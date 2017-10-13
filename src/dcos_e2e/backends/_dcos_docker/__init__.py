"""
Helpers for interacting with DC/OS Docker.
"""

import inspect
import os
import socket
import uuid
from copy import deepcopy
from ipaddress import IPv4Address
from pathlib import Path
from shutil import copyfile, copytree, ignore_patterns, rmtree
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Set, Type, Union

import docker
import yaml
from passlib.hash import sha512_crypt

from dcos_e2e._common import run_subprocess
from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.node import Node


def _get_open_port() -> int:
    """
    Return a free port.
    """
    host = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new_socket:
        new_socket.bind((host, 0))
        new_socket.listen(1)
        return int(new_socket.getsockname()[1])


class DCOS_Docker(ClusterBackend):  # pylint: disable=invalid-name
    """
    A record of a DC/OS Docker backend which can be used to create clusters.
    """

    def __init__(self, workspace_dir: Optional[Path] = None) -> None:
        """
        Create a configuration for a DC/OS Docker cluster backend.

        Args:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
                This is equivalent to `dir` in
                https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory  # noqa

        Attributes:
            dcos_docker_path: The path to a clone of DC/OS Docker.
                This clone will be used to create the cluster.
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
        """
        current_file = inspect.stack()[0][1]
        current_parent = Path(os.path.abspath(current_file)).parent
        self.dcos_docker_path = current_parent / 'dcos_docker'
        self.workspace_dir = workspace_dir

    @property
    def cluster_cls(self) -> Type['DCOS_Docker_Cluster']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return DCOS_Docker_Cluster

    @property
    def supports_destruction(self) -> bool:
        """
        DC/OS Docker clusters can be destroyed.
        """
        return True


class DCOS_Docker_Cluster(ClusterManager):  # pylint: disable=invalid-name
    """
    A record of a DC/OS Docker cluster.
    """

    def __init__(  # noqa: E501 pylint: disable=super-init-not-called,too-many-statements,too-many-branches,wrong-spelling-in-comment
        self,
        generate_config_path: Optional[Path],
        masters: int,
        agents: int,
        public_agents: int,
        extra_config: Dict[str, Any],
        log_output_live: bool,
        files_to_copy_to_installer: Dict[Path, Path],
        files_to_copy_to_masters: Dict[Path, Path],
        cluster_backend: DCOS_Docker,
    ) -> None:
        """
        Create a DC/OS Docker cluster.

        Args:
            generate_config_path: The path to a build artifact to install.
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            extra_config: DC/OS Docker comes with a "base" configuration.
                This dictionary can contain extra installation configuration
                variables.
            log_output_live: If `True`, log output of subprocesses live.
                If `True`, stderr is merged into stdout in the return value.
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS. Currently on DC/OS
                Docker the only supported paths on the installer are in the
                `/genconf` directory.
            files_to_copy_to_masters: A mapping of host paths to paths on the
                master nodes. These are files to copy from the host to
                the master nodes before installing DC/OS. On DC/OS Docker the
                files are mounted, read only, to the masters.
            cluster_backend: Details of the specific DC/OS Docker backend to
                use.

        Raises:
            ValueError: There is no file at `generate_config_path`.
            CalledProcessError: The step to create and install containers
                exited with a non-zero code.
        """
        if generate_config_path is None or not generate_config_path.exists():
            raise ValueError()

        self.log_output_live = log_output_live

        # To avoid conflicts, we use random container names.
        # We use the same random string for each container in a cluster so
        # that they can be associated easily.
        #
        # Starting with "dcos-e2e" allows `make clean` to remove these and
        # only these containers.
        unique = 'dcos-e2e-{random}'.format(random=uuid.uuid4())

        # We create a new instance of DC/OS Docker and we work in this
        # directory.
        # This helps running tests in parallel without conflicts and it
        # reduces the chance of side-effects affecting sequential tests.
        self._path = Path(
            TemporaryDirectory(
                suffix=unique,
                dir=(
                    str(cluster_backend.workspace_dir)
                    if cluster_backend.workspace_dir else None
                ),
            ).name
        )

        copytree(
            src=str(cluster_backend.dcos_docker_path),
            dst=str(self._path),
            # If there is already a config, we do not copy it as it will be
            # overwritten and therefore copying it is wasteful.
            ignore=ignore_patterns('dcos_generate_config.sh'),
        )

        # Files in the DC/OS Docker directory's `genconf` directory are mounted
        # to the installer at `/genconf`.
        # Therefore, every file which we want to copy to `/genconf` on the
        # installer is put into the genconf directory in DC/OS Docker.
        # The way to fix this if we want to be able to put files anywhere is
        # to add an variable to `dcos_generate_config.sh.in` which allows
        # `-v` mounts.
        # Then `INSTALLER_MOUNTS` can be added to DC/OS Docker.
        genconf_dir = self._path / 'genconf'
        # We wrap these in `Path` to work around
        # https://github.com/PyCQA/pylint/issues/224.
        Path(genconf_dir).mkdir(exist_ok=True)
        genconf_dir = Path(genconf_dir).resolve()

        for host_path, installer_path in files_to_copy_to_installer.items():
            relative_installer_path = installer_path.relative_to('/genconf')
            destination_path = genconf_dir / relative_installer_path
            copyfile(src=str(host_path), dst=str(destination_path))

        extra_genconf_config = ''
        if extra_config:
            extra_genconf_config = yaml.dump(
                data=extra_config,
                default_flow_style=False,
            )

        # Only overlay, overlay2, and aufs storage drivers are supported.
        # This chooses the overlay2 driver if the host's driver is not
        # supported for speed reasons.
        client = docker.from_env(version='auto')
        host_driver = client.info()['Driver']
        storage_driver = host_driver if host_driver in (
            'overlay', 'overlay2', 'aufs'
        ) else 'overlay2'

        self._master_prefix = '{unique}-master-'.format(unique=unique)
        self._agent_prefix = '{unique}-agent-'.format(unique=unique)
        self._public_agent_prefix = '{unique}-pub-agent-'.format(unique=unique)

        include_dir = self._path / 'include'
        certs_dir = include_dir / 'certs'
        certs_dir.mkdir(parents=True)

        bootstrap_genconf_path = genconf_dir / 'serve'
        # We wrap this in `Path` to work around
        # https://github.com/PyCQA/pylint/issues/224.
        Path(bootstrap_genconf_path).mkdir()
        bootstrap_tmp_path = Path('/opt/dcos_install_tmp')

        # See https://success.docker.com/KBase/Different_Types_of_Volumes
        # for a definition of different types of volumes.
        agent_mounts = {
            str(certs_dir.resolve()): {
                'bind': '/etc/docker/certs.d',
                'mode': 'rw'
            },
            'var_lib_docker': {
                'bind': '/var/lib/docker',
                'mode': 'rw'
            },
            'opt': {
                'bind': '/opt',
                'mode': 'rw'
            },
            str(bootstrap_genconf_path): {
                'bind': str(bootstrap_tmp_path),
                'mode': 'rw'
            }
        }

        master_mounts = deepcopy(agent_mounts)

        for host_path, master_path in files_to_copy_to_masters.items():
            # The volume is mounted `read-write` because certain processes
            # change the content or permission of the files on the volume.
            master_mounts[str(host_path)] = {
                'bind': str(master_path),
                'mode': 'rw',
            }

        node_tmpfs_mounts = {
            '/run': 'rw,exec,nosuid,size=2097152k',
            '/tmp': 'rw,exec,nosuid,size=2097152k',
        }

        installer_ctr = '{unique}-installer'.format(unique=unique)
        installer_port = _get_open_port()

        variables = {
            # This version of Docker supports `overlay2`.
            'DOCKER_VERSION': '1.13.1',
            'DOCKER_STORAGEDRIVER': storage_driver,
            # Number of nodes.
            'MASTERS': str(masters),
            'AGENTS': str(agents),
            'PUBLIC_AGENTS': str(public_agents),
            # Container names.
            'MASTER_CTR': self._master_prefix,
            'AGENT_CTR': self._agent_prefix,
            'PUBLIC_AGENT_CTR': self._public_agent_prefix,
            'INSTALLER_CTR': installer_ctr,
            'INSTALLER_PORT': str(installer_port),
            'EXTRA_GENCONF_CONFIG': extra_genconf_config,
            'DCOS_GENERATE_CONFIG_PATH': str(generate_config_path),
        }  # type: Dict[str, str]

        make_args = []
        for key, value in variables.items():
            # See https://stackoverflow.com/a/7860705 for details on escaping
            # Make variables.
            escaped_value = value.replace('$', '$$')
            escaped_value = escaped_value.replace('#', '\\#')
            set_variable = '{key}={value}'.format(key=key, value=escaped_value)
            make_args.append(set_variable)

        run_subprocess(
            args=['make'] + make_args + ['build'],
            cwd=str(self._path),
            log_output_live=self.log_output_live,
        )

        for master_number in range(1, masters + 1):
            self._start_dcos_container(
                container_base_name=self._master_prefix,
                container_number=master_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes=master_mounts,
                tmpfs=node_tmpfs_mounts,
            )

        for agent_number in range(1, agents + 1):
            self._start_dcos_container(
                container_base_name=self._agent_prefix,
                container_number=agent_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes=agent_mounts,
                tmpfs=node_tmpfs_mounts,
            )

        for public_agent_number in range(1, public_agents + 1):
            self._start_dcos_container(
                container_base_name=self._public_agent_prefix,
                container_number=public_agent_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes=agent_mounts,
                tmpfs=node_tmpfs_mounts,
            )

        assert len(self.agents) == agents
        assert len(self.public_agents) == public_agents
        assert len(self.masters) == masters

        superuser_password = 'admin'
        superuser_password_hash = sha512_crypt.hash(superuser_password)
        config_file_path = genconf_dir / 'config.yaml'
        config_body_dict = {
            'agent_list': [str(agent.ip_address) for agent in self.agents],
            'public_agent_list': [
                str(public_agent.ip_address)
                for public_agent in self.public_agents
            ],
            'bootstrap_url':
            'file://' + str(bootstrap_tmp_path),
            'cluster_name':
            'DCOS',
            'exhibitor_storage_backend':
            'static',
            'master_discovery':
            'static',
            'master_list': [str(master.ip_address) for master in self.masters],
            'process_timeout':
            10000,
            'resolvers': ['8.8.8.8'],
            'ssh_port':
            22,
            'ssh_user':
            'root',
            'superuser_password_hash':
            superuser_password_hash,
            'superuser_username':
            'admin',
            'platform':
            'docker',
            'check_time':
            'false',
        }

        config_body_dict.update(extra_config)
        config_body = yaml.dump(
            data=config_body_dict,
            default_flow_style=False,
        )

        Path(config_file_path).write_text(config_body)

        genconf_args = [
            'bash',
            str(generate_config_path),
            '--offline',
            '-v',
            '--genconf',
        ]

        run_subprocess(
            args=genconf_args,
            env={
                'PORT': str(installer_port),
                'DCOS_INSTALLER_CONTAINER_NAME': installer_ctr,
            },
            log_output_live=self.log_output_live,
            cwd=str(self._path),
        )

        for master_number in range(1, masters + 1):
            self._run_dcos_install_in_container(
                container_base_name=self._master_prefix,
                container_number=master_number,
                role='master',
            )

        for agent_number in range(1, agents + 1):
            self._run_dcos_install_in_container(
                container_base_name=self._agent_prefix,
                container_number=agent_number,
                role='slave',
            )

        for public_agent_number in range(1, public_agents + 1):
            self._run_dcos_install_in_container(
                container_base_name=self._public_agent_prefix,
                container_number=public_agent_number,
                role='slave_public',
            )

        for node in {*self.masters, *self.agents, *self.public_agents}:
            # Remove stray file that prevents non-root SSH.
            # https://ubuntuforums.org/showthread.php?t=2327330
            node.run_as_root(args=['rm', '-f', '/run/nologin'])

    def _run_dcos_install_in_container(
        self,
        container_base_name: str,
        container_number: int,
        role: str,
    ) -> None:
        """
        Run ``dcos_install.sh`` in a container.

        Args:
            container_base_name: The start of the container name.
            container_number: The end of the container name.
            role: One of 'master', 'slave', 'slave_public'.
        """
        client = docker.from_env(version='auto')
        container_name = container_base_name + str(container_number)
        container = client.containers.get(container_name)
        bootstrap_tmp_path = Path('/opt/dcos_install_tmp')
        dcos_install_path = bootstrap_tmp_path / 'dcos_install.sh'
        cmd = [
            '/bin/bash',
            str(dcos_install_path),
            '--no-block-dcos-setup',
            role,
        ]
        container.exec_run(cmd=cmd)

    def _start_dcos_container(
        self,
        container_base_name: str,
        container_number: int,
        volumes: Union[Dict[str, Dict[str, str]], List[str]],
        tmpfs: Dict[str, str],
        dcos_num_masters: int,
        dcos_num_agents: int,
    ) -> None:
        """
        Start a master, agent or public agent container.
        In this container, start Docker and `sshd`.

        Run Mesos without `systemd` support. This is not supported by DC/OS.
        See https://jira.mesosphere.com/browse/DCOS_OSS-1131.

        Args:
            container_base_name: The start of the container name.
            container_number: The end of the container name.
            volumes: See `volumes` on
                http://docker-py.readthedocs.io/en/latest/containers.html.
            tmpfs: See `tmpfs` on
                http://docker-py.readthedocs.io/en/latest/containers.html.
            dcos_num_masters: The number of master nodes expected to be in the
                cluster once it has been created.
            dcos_num_agents: The number of agent nodes (agent and public
                agents) expected to be in the cluster once it has been created.
        """
        docker_image = 'mesosphere/dcos-docker'
        registry_host = 'registry.local'
        if self.masters:
            first_master = next(iter(self.masters))
            extra_host_ip_address = str(first_master.ip_address)
        else:
            extra_host_ip_address = '127.0.0.1'
        hostname = container_base_name + str(container_number)
        environment = {
            'container': hostname,
            'DCOS_NUM_MASTERS': dcos_num_masters,
            'DCOS_NUM_AGENTS': dcos_num_agents,
        }
        extra_hosts = {registry_host: extra_host_ip_address}

        client = docker.from_env(version='auto')
        container = client.containers.run(
            name=hostname,
            privileged=True,
            detach=True,
            tty=True,
            environment=environment,
            hostname=hostname,
            extra_hosts=extra_hosts,
            image=docker_image,
            volumes=volumes,
            tmpfs=tmpfs,
        )

        disable_systemd_support_cmd = (
            "echo 'MESOS_SYSTEMD_ENABLE_SUPPORT=false' >> "
            '/var/lib/dcos/mesos-slave-common'
        )

        for cmd in [
            ['mkdir', '-p', '/var/lib/dcos'],
            ['/bin/bash', '-c', disable_systemd_support_cmd],
            ['systemctl', 'start', 'sshd.service'],
        ]:
            container.exec_run(cmd=cmd)

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        client = docker.from_env(version='auto')
        for prefix in (
            self._master_prefix,
            self._agent_prefix,
            self._public_agent_prefix,
        ):
            containers = client.containers.list(filters={'name': prefix})
            for container in containers:
                container.remove(v=True, force=True)

        rmtree(path=str(self._path), ignore_errors=True)

    def _nodes(self, container_base_name: str) -> Set[Node]:
        """
        Args:
            container_base_name: The start of the container names.

        Returns: ``Node``s corresponding to containers with names starting
            with ``container_base_name``.
        """
        client = docker.from_env(version='auto')
        filters = {'name': container_base_name}
        containers = client.containers.list(filters=filters)

        return set(
            Node(
                ip_address=IPv4Address(
                    container.attrs['NetworkSettings']['IPAddress']
                ),
                ssh_key_path=self._path / 'include' / 'ssh' / 'id_rsa',
            ) for container in containers
        )

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master ``Node``s.
        """
        return self._nodes(container_base_name=self._master_prefix)

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """
        return self._nodes(container_base_name=self._agent_prefix)

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent ``Node``s.
        """
        return self._nodes(container_base_name=self._public_agent_prefix)

"""
Helpers for interacting with DC/OS Docker.
"""

import inspect
import os
import socket
import stat
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import copyfile, copytree, ignore_patterns, rmtree
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any, Dict, List, Optional, Set, Type, Union

import docker
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
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

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
    ) -> None:
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
            custom_master_mounts: The XXX
        """
        current_file = inspect.stack()[0][1]
        current_parent = Path(os.path.abspath(current_file)).parent
        self.dcos_docker_path = current_parent / 'dcos_docker'
        self.workspace_dir = workspace_dir
        self.custom_master_mounts = custom_master_mounts

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

    def __init__(  # pylint: disable=super-init-not-called,too-many-statements
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
            CalledProcessError: The step to create and install containers
                exited with a non-zero code.
        """
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

        self._path = self._path.resolve()

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
        genconf_dir_src = self._path / 'genconf.src'
        include_dir = self._path / 'include'
        include_dir_src = self._path / 'include.src'
        certs_dir = include_dir / 'certs'
        certs_dir.mkdir(parents=True)
        ssh_dir = include_dir / 'ssh'
        ssh_dir.mkdir(parents=True)
        sbin_dir_src = include_dir_src / 'sbin'
        sbin_dir = include_dir / 'sbin'
        sbin_dir.mkdir(parents=True)
        service_dir_src = include_dir_src / 'systemd'
        service_dir = include_dir / 'systemd'
        service_dir.mkdir(parents=True)

        ip_detect = Path(genconf_dir / 'ip-detect')

        copyfile(
            src=str(genconf_dir_src / 'ip-detect'),
            dst=str(ip_detect),
        )
        ip_detect.chmod(mode=ip_detect.stat().st_mode | stat.S_IEXEC)

        dcos_postflight = sbin_dir / 'dcos-postflight'

        copyfile(
            src=str(sbin_dir_src / 'dcos-postflight'),
            dst=str(dcos_postflight),
        )
        dcos_postflight.chmod(
            mode=dcos_postflight.stat().st_mode | stat.S_IEXEC,
        )

        copyfile(
            src=str(service_dir_src / 'systemd-journald-init.service'),
            dst=str(service_dir / 'systemd-journald-init.service'),
        )

        rsa_key_pair = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048,
        )

        public_key = rsa_key_pair.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH,
        )

        private_key = rsa_key_pair.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_key_file = ssh_dir / 'id_rsa.pub'
        private_key_file = ssh_dir / 'id_rsa'
        public_key_file.write_bytes(data=public_key)
        private_key_file.write_bytes(data=private_key)
        private_key_file.chmod(mode=stat.S_IRUSR)

        for host_path, installer_path in files_to_copy_to_installer.items():
            relative_installer_path = installer_path.relative_to('/genconf')
            destination_path = genconf_dir / relative_installer_path
            copyfile(src=str(host_path), dst=str(destination_path))

        # Only overlay, overlay2, and aufs storage drivers are supported.
        # This chooses the overlay2 driver if the host's driver is not
        # supported for speed reasons.
        client = docker.from_env(version='auto')
        host_driver = client.info()['Driver']
        storage_driver = host_driver if host_driver in (
            'overlay', 'overlay2', 'aufs'
        ) else 'overlay2'

        docker_service_body = dedent(
            """\
            [Unit]
            Description=Docker Application Container Engine
            Documentation=https://docs.docker.com
            After=dbus.service

            [Service]
            ExecStart=/usr/bin/docker daemon -D -s {docker_storage_driver} \
            --disable-legacy-registry=true \
            --exec-opt=native.cgroupdriver=cgroupfs
            LimitNOFILE=1048576
            LimitNPROC=1048576
            LimitCORE=infinity
            Delegate=yes
            TimeoutStartSec=0

            [Install]
            WantedBy=default.target
            """.format(docker_storage_driver=storage_driver)
        )

        self._master_prefix = '{unique}-master-'.format(unique=unique)
        self._agent_prefix = '{unique}-agent-'.format(unique=unique)
        self._public_agent_prefix = '{unique}-pub-agent-'.format(unique=unique)

        bootstrap_genconf_path = genconf_dir / 'serve'
        # We wrap this in `Path` to work around
        # https://github.com/PyCQA/pylint/issues/224.
        Path(bootstrap_genconf_path).mkdir()
        bootstrap_tmp_path = Path('/opt/dcos_install_tmp')

        # See https://success.docker.com/KBase/Different_Types_of_Volumes
        # for a definition of different types of volumes.
        node_tmpfs_mounts = {
            '/run': 'rw,exec,nosuid,size=2097152k',
            '/tmp': 'rw,exec,nosuid,size=2097152k',
        }

        installer_ctr = '{unique}-installer'.format(unique=unique)
        installer_port = _get_open_port()

        (service_dir / 'docker.service').write_text(docker_service_body)

        docker_image_tag = 'mesosphere/dcos-docker'
        base_tag = docker_image_tag + ':base'
        base_docker_tag = base_tag + '-docker'
        # This version of Docker supports `overlay2`.
        docker_version = '1.13.1'
        distro = 'centos-7'

        client.images.build(
            path=str(self._path),
            rm=True,
            forcerm=True,
            tag=base_tag,
            dockerfile=str(Path('build') / 'base' / distro / 'Dockerfile'),
        )

        client.images.build(
            path=str(self._path),
            rm=True,
            forcerm=True,
            tag=base_docker_tag,
            dockerfile=str(
                Path('build') / 'base-docker' / docker_version / 'Dockerfile'
            ),
        )

        client.images.build(
            path=str(self._path),
            rm=True,
            forcerm=True,
            tag=docker_image_tag,
        )

        common_mounts = {
            str(certs_dir.resolve()): {
                'bind': '/etc/docker/certs.d',
                'mode': 'rw',
            },
            str(bootstrap_genconf_path): {
                'bind': str(bootstrap_tmp_path),
                'mode': 'ro',
            },
        }

        agent_mounts = {
            '/sys/fs/cgroup': {'bind': '/sys/fs/cgroup', 'mode': 'ro'},
            **common_mounts,
        }

        for master_number in range(1, masters + 1):
            unique_mounts = {
                str(uuid.uuid4()): {
                    'bind': '/var/lib/docker',
                    'mode': 'rw'
                },
                str(uuid.uuid4()): {
                    'bind': '/opt',
                    'mode': 'rw'
                },
            }

            self._start_dcos_container(
                container_base_name=self._master_prefix,
                container_number=master_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes={
                    **common_mounts,
                    **cluster_backend.custom_master_mounts,
                    **unique_mounts,
                },
                tmpfs=node_tmpfs_mounts,
            )

        for agent_number in range(1, agents + 1):
            unique_mounts = {
                str(uuid.uuid4()): {
                    'bind': '/var/lib/docker',
                    'mode': 'rw'
                },
                str(uuid.uuid4()): {
                    'bind': '/opt',
                    'mode': 'rw'
                },
                str(uuid.uuid4()): {
                    'bind': '/var/lib/mesos/slave',
                    'mode': 'rw'
                },
            }

            self._start_dcos_container(
                container_base_name=self._agent_prefix,
                container_number=agent_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes={**agent_mounts, **unique_mounts},
                tmpfs=node_tmpfs_mounts,
            )

        for public_agent_number in range(1, public_agents + 1):
            unique_mounts = {
                str(uuid.uuid4()): {
                    'bind': '/var/lib/docker',
                    'mode': 'rw'
                },
                str(uuid.uuid4()): {
                    'bind': '/opt',
                    'mode': 'rw'
                },
                str(uuid.uuid4()): {
                    'bind': '/var/lib/mesos/slave',
                    'mode': 'rw'
                },
            }

            self._start_dcos_container(
                container_base_name=self._public_agent_prefix,
                container_number=public_agent_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes={**agent_mounts, **unique_mounts},
                tmpfs=node_tmpfs_mounts,
            )

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

        config_body = yaml.dump(data={**config_body_dict, **extra_config})
        Path(config_file_path).write_text(data=config_body)

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

        for role, nodes in [
            ('master', self.masters),
            ('slave', self.agents),
            ('slave_public', self.public_agents),
        ]:
            dcos_install_args = [
                '/bin/bash',
                str(bootstrap_tmp_path / 'dcos_install.sh'),
                '--no-block-dcos-setup',
                role,
            ]

            for node in nodes:
                node.run_as_root(args=dcos_install_args)

        for node in {*self.masters, *self.agents, *self.public_agents}:
            # Remove stray file that prevents non-root SSH.
            # https://ubuntuforums.org/showthread.php?t=2327330
            node.run_as_root(args=['rm', '-f', '/run/nologin'])

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

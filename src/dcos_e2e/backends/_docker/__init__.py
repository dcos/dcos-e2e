"""
Helpers for creating and interacting with clusters on Docker.
"""

import inspect
import logging
import os
import socket
import subprocess
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import copyfile, copytree, rmtree
from tempfile import gettempdir
from typing import Any, Dict, List, Optional, Set, Tuple, Type

import docker
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from dcos_e2e._common import run_subprocess
from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Node

from ._containers import start_dcos_container
from ._docker_build import build_docker_image

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


def _write_key_pair(public_key_path: Path, private_key_path: Path) -> None:
    """
    Write an RSA key pair for connecting to nodes via SSH.

    Args:
        public_key_path: Path to write public key to.
        private_key_path: Path to a private key file to write.
    """
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

    public_key_path.write_bytes(data=public_key)
    private_key_path.write_bytes(data=private_key)


def _get_open_port() -> int:
    """
    Return a free port.
    """
    host = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new_socket:
        new_socket.bind((host, 0))
        new_socket.listen(1)
        return int(new_socket.getsockname()[1])


def _get_fallback_storage_driver() -> DockerStorageDriver:
    """
    Return the Docker storage driver to use if one is not given.
    """
    storage_drivers = {
        'aufs': DockerStorageDriver.AUFS,
        'overlay': DockerStorageDriver.OVERLAY,
        'overlay2': DockerStorageDriver.OVERLAY_2,
    }

    client = docker.from_env(version='auto')
    host_driver = client.info()['Driver']

    try:
        return storage_drivers[host_driver]
    except KeyError:
        # This chooses the aufs driver if the host's driver is not
        # supported because this is widely supported.
        #
        # This is encoded in a `dcos-docker doctor` check.
        return DockerStorageDriver.AUFS


class Docker(ClusterBackend):
    """
    A record of a Docker backend which can be used to create clusters.
    """

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        custom_master_mounts: Optional[Dict[str, Dict[str, str]]] = None,
        custom_agent_mounts: Optional[Dict[str, Dict[str, str]]] = None,
        custom_public_agent_mounts: Optional[Dict[str, Dict[str, str]]] = None,
        linux_distribution: Distribution = Distribution.CENTOS_7,
        docker_version: DockerVersion = DockerVersion.v1_13_1,
        storage_driver: Optional[DockerStorageDriver] = None,
        docker_container_labels: Optional[Dict[str, str]] = None,
        docker_master_labels: Optional[Dict[str, str]] = None,
        docker_agent_labels: Optional[Dict[str, str]] = None,
        docker_public_agent_labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Create a configuration for a Docker cluster backend.

        Args:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
                This is equivalent to `dir` in
                :py:func:`tempfile.mkstemp`.
            custom_master_mounts: Custom mounts add to master node containers.
                See `volumes` in `Containers.run`_.
            custom_agent_mounts: Custom mounts add to agent node containers.
                See `volumes` in `Containers.run`_.
            custom_public_agent_mounts: Custom mounts add to public agent node
                containers. See `volumes` in `Containers.run`_.
            linux_distribution: The Linux distribution to boot DC/OS on.
            docker_version: The Docker version to install on the cluster nodes.
            storage_driver: The storage driver to use for Docker on the
                cluster nodes. By default, this is the host's storage driver.
                If this is not one of ``aufs``, ``overlay`` or ``overlay2``,
                ``aufs`` is used.
            docker_container_labels: Docker labels to add to the cluster node
                containers. Akin to the dictionary option in `Containers.run`_.
            docker_master_labels: Docker labels to add to the cluster master
                node containers. Akin to the dictionary option in
                `Containers.run`_.
            docker_agent_labels: Docker labels to add to the cluster agent node
                containers. Akin to the dictionary option in `Containers.run`_.
            docker_public_agent_labels: Docker labels to add to the cluster
                public agent node containers. Akin to the dictionary option in
                `Containers.run`_.

        Attributes:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
            custom_master_mounts: Custom mounts add to master node containers.
                See `volumes` in `Containers.run`_.
            custom_agent_mounts: Custom mounts add to agent node containers.
                See `volumes` in `Containers.run`_.
            custom_public_agent_mounts: Custom mounts add to public agent node
                containers. See `volumes` in `Containers.run`_.
            linux_distribution: The Linux distribution to boot DC/OS on.
            docker_version: The Docker version to install on the cluster nodes.
            docker_storage_driver: The storage driver to use for Docker on the
                cluster nodes.
            docker_master_labels: Docker labels to add to the cluster master
                node containers. Akin to the dictionary option in
                `Containers.run`_.
            docker_agent_labels: Docker labels to add to the cluster agent node
                containers. Akin to the dictionary option in `Containers.run`_.
            docker_public_agent_labels: Docker labels to add to the cluster
                public agent node containers. Akin to the dictionary option in
                `Containers.run`_.

        .. _Containers.run:
            http://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run
        """
        self.docker_version = docker_version
        self.workspace_dir = workspace_dir or Path(gettempdir())
        self.custom_master_mounts = custom_master_mounts or {}
        self.custom_agent_mounts = custom_agent_mounts or {}
        self.custom_public_agent_mounts = custom_public_agent_mounts or {}
        self.linux_distribution = linux_distribution
        fallback_driver = _get_fallback_storage_driver()
        self.docker_storage_driver = storage_driver or fallback_driver
        self.docker_container_labels = docker_container_labels or {}
        self.docker_master_labels = docker_master_labels or {}
        self.docker_agent_labels = docker_agent_labels or {}
        self.docker_public_agent_labels = docker_public_agent_labels or {}

    @property
    def cluster_cls(self) -> Type['DockerCluster']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return DockerCluster


class DockerCluster(ClusterManager):
    """
    A record of a Docker cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
        files_to_copy_to_installer: List[Tuple[Path, Path]],
        cluster_backend: Docker,
    ) -> None:
        """
        Create a Docker cluster.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            files_to_copy_to_installer: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
                Currently on DC/OS Docker the only supported paths on the
                installer are in the ``/genconf`` directory.
            cluster_backend: Details of the specific Docker backend to use.
        """
        self._default_ssh_user = 'root'

        # To avoid conflicts, we use random container names.
        # We use the same random string for each container in a cluster so
        # that they can be associated easily.
        #
        # Starting with "dcos-e2e" allows `make clean` to remove these and
        # only these containers.
        self._cluster_id = 'dcos-e2e-{random}'.format(random=uuid.uuid4())

        # We work in a new directory.
        # This helps running tests in parallel without conflicts and it
        # reduces the chance of side-effects affecting sequential tests.
        workspace_dir = cluster_backend.workspace_dir
        self._path = Path(workspace_dir) / uuid.uuid4().hex / self._cluster_id
        self._path.mkdir(exist_ok=True, parents=True)
        self._path = self._path.resolve()

        # Files in the `genconf` directory are mounted to the installer at
        # `/genconf`.
        # Therefore, every file which we want to copy to `/genconf` on the
        # installer is put into the `genconf` directory.
        # The way to fix this if we want to be able to put files anywhere is
        # to add an variable to `dcos_generate_config.sh.in` which allows
        # `-v` mounts.
        self._genconf_dir = self._path / 'genconf'
        # We wrap these in `Path` to work around
        # https://github.com/PyCQA/pylint/issues/224.
        Path(self._genconf_dir).mkdir(exist_ok=True, parents=True)
        self._genconf_dir = Path(self._genconf_dir).resolve()
        include_dir = self._path / 'include'
        certs_dir = include_dir / 'certs'
        certs_dir.mkdir(parents=True)
        ssh_dir = include_dir / 'ssh'
        ssh_dir.mkdir(parents=True)

        current_file = inspect.stack()[0][1]
        current_parent = Path(os.path.abspath(current_file)).parent
        ip_detect_src = current_parent / 'resources' / 'ip-detect'
        ip_detect_dst = Path('/genconf/ip-detect')
        files_to_copy_to_installer.append((ip_detect_src, ip_detect_dst))

        public_key_path = ssh_dir / 'id_rsa.pub'
        _write_key_pair(
            public_key_path=public_key_path,
            private_key_path=ssh_dir / 'id_rsa',
        )

        for host_path, installer_path in files_to_copy_to_installer:
            relative_installer_path = installer_path.relative_to('/genconf')
            destination_path = self._genconf_dir / relative_installer_path
            if host_path.is_dir():
                destination_path = destination_path / host_path.stem
                copytree(src=str(host_path), dst=str(destination_path))
            else:
                copyfile(src=str(host_path), dst=str(destination_path))

        self._master_prefix = self._cluster_id + '-master-'
        self._agent_prefix = self._cluster_id + '-agent-'
        self._public_agent_prefix = self._cluster_id + '-public-agent-'

        bootstrap_genconf_path = self._genconf_dir / 'serve'
        # We wrap this in `Path` to work around
        # https://github.com/PyCQA/pylint/issues/224.
        Path(bootstrap_genconf_path).mkdir()
        self._bootstrap_tmp_path = Path('/opt/dcos_install_tmp')

        # See https://success.docker.com/KBase/Different_Types_of_Volumes
        # for a definition of different types of volumes.
        node_tmpfs_mounts = {
            '/run': 'rw,exec,nosuid,size=2097152k',
            '/tmp': 'rw,exec,nosuid,size=2097152k',
        }

        docker_image_tag = 'mesosphere/dcos-docker'
        build_docker_image(
            tag=docker_image_tag,
            linux_distribution=cluster_backend.linux_distribution,
            docker_version=cluster_backend.docker_version,
        )

        common_mounts = {
            str(certs_dir.resolve()): {
                'bind': '/etc/docker/certs.d',
                'mode': 'rw',
            },
            str(bootstrap_genconf_path): {
                'bind': str(self._bootstrap_tmp_path),
                'mode': 'ro',
            },
        }

        agent_mounts = {
            '/sys/fs/cgroup': {
                'bind': '/sys/fs/cgroup',
                'mode': 'ro',
            },
            **common_mounts,
        }

        for master_number in range(1, masters + 1):
            unique_mounts = {
                str(uuid.uuid4()): {
                    'bind': '/var/lib/docker',
                    'mode': 'rw',
                },
                str(uuid.uuid4()): {
                    'bind': '/opt',
                    'mode': 'rw',
                },
            }

            start_dcos_container(
                existing_masters=self.masters,
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
                docker_image=docker_image_tag,
                labels={
                    **cluster_backend.docker_container_labels,
                    **cluster_backend.docker_master_labels,
                },
                public_key_path=public_key_path,
                docker_storage_driver=cluster_backend.docker_storage_driver,
                docker_version=cluster_backend.docker_version,
            )

        for agent_number in range(1, agents + 1):
            unique_mounts = {
                str(uuid.uuid4()): {
                    'bind': '/var/lib/docker',
                    'mode': 'rw',
                },
                str(uuid.uuid4()): {
                    'bind': '/opt',
                    'mode': 'rw',
                },
                str(uuid.uuid4()): {
                    'bind': '/var/lib/mesos/slave',
                    'mode': 'rw',
                },
            }

            start_dcos_container(
                existing_masters=self.masters,
                container_base_name=self._agent_prefix,
                container_number=agent_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes={
                    **agent_mounts,
                    **cluster_backend.custom_agent_mounts,
                    **unique_mounts,
                },
                tmpfs=node_tmpfs_mounts,
                docker_image=docker_image_tag,
                labels={
                    **cluster_backend.docker_container_labels,
                    **cluster_backend.docker_agent_labels,
                },
                public_key_path=public_key_path,
                docker_storage_driver=cluster_backend.docker_storage_driver,
                docker_version=cluster_backend.docker_version,
            )

        for public_agent_number in range(1, public_agents + 1):
            unique_mounts = {
                str(uuid.uuid4()): {
                    'bind': '/var/lib/docker',
                    'mode': 'rw',
                },
                str(uuid.uuid4()): {
                    'bind': '/opt',
                    'mode': 'rw',
                },
                str(uuid.uuid4()): {
                    'bind': '/var/lib/mesos/slave',
                    'mode': 'rw',
                },
            }

            start_dcos_container(
                existing_masters=self.masters,
                container_base_name=self._public_agent_prefix,
                container_number=public_agent_number,
                dcos_num_masters=masters,
                dcos_num_agents=agents + public_agents,
                volumes={
                    **agent_mounts,
                    **cluster_backend.custom_public_agent_mounts,
                    **unique_mounts,
                },
                tmpfs=node_tmpfs_mounts,
                docker_image=docker_image_tag,
                labels={
                    **cluster_backend.docker_container_labels,
                    **cluster_backend.docker_public_agent_labels,
                },
                public_key_path=public_key_path,
                docker_storage_driver=cluster_backend.docker_storage_driver,
                docker_version=cluster_backend.docker_version,
            )

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a URL. This is not supported and simply raises a
        ``NotImplementedError``.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            extra_config: This may contain extra installation configuration
                variables that are applied on top of the default DC/OS
                configuration of the Docker backend.
            log_output_live: If ``True``, log output of the installation live.

        Raises:
            NotImplementedError: ``NotImplementedError`` because the Docker
                backend does not support the DC/OS advanced installation
                method.
        """
        message = (
            'The Docker backend does not support the installation of DC/OS '
            'by build artifacts passed via URL string. This is because a more '
            'efficient installation method exists in `install_dcos_from_path`.'
        )
        raise NotImplementedError(message)

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a given build artifact.

        Args:
            build_artifact: The ``Path`` to a build artifact to install DC/OS
                from.
            extra_config: May contain extra installation configuration
                variables that are applied on top of the default DC/OS
                configuration of the Docker backend.
            log_output_live: If ``True``, log output of the installation live.

        Raises:
            CalledProcessError: There was an error installing DC/OS on a node.
        """
        ssh_user = self._default_ssh_user

        def ip_list(nodes: Set[Node]) -> List[str]:
            return list(map(lambda node: str(node.public_ip_address), nodes))

        config = {
            'agent_list': ip_list(nodes=self.agents),
            'bootstrap_url': 'file://' + str(self._bootstrap_tmp_path),
            # Without this, we see errors like:
            # "Time is not synchronized / marked as bad by the kernel.".
            # Adam saw this on Docker for Mac 17.09.0-ce-mac35.
            #
            # In that case this was fixable with:
            #   $ docker run --rm --privileged alpine hwclock -s
            'check_time': 'false',
            'cluster_name': 'DCOS',
            'exhibitor_storage_backend': 'static',
            'master_discovery': 'static',
            'master_list': ip_list(nodes=self.masters),
            'process_timeout': 10000,
            'public_agent_list': ip_list(nodes=self.public_agents),
            'resolvers': ['8.8.8.8'],
            'ssh_port': 22,
            'ssh_user': ssh_user,
        }

        config_data = {**config, **extra_config}
        config_yaml = yaml.dump(data=config_data)  # type: ignore
        config_file_path = self._genconf_dir / 'config.yaml'
        config_file_path.write_text(data=config_yaml)

        genconf_args = [
            'bash',
            str(build_artifact),
            '--offline',
            '-v',
            '--genconf',
        ]

        installer_ctr = '{cluster_id}-installer'.format(
            cluster_id=self._cluster_id,
        )
        installer_port = _get_open_port()

        run_subprocess(
            args=genconf_args,
            env={
                'PORT': str(installer_port),
                'DCOS_INSTALLER_CONTAINER_NAME': installer_ctr,
            },
            log_output_live=log_output_live,
            cwd=str(self._path),
        )

        for role, nodes in [
            ('master', self.masters),
            ('slave', self.agents),
            ('slave_public', self.public_agents),
        ]:
            dcos_install_args = [
                '/bin/bash',
                str(self._bootstrap_tmp_path / 'dcos_install.sh'),
                '--no-block-dcos-setup',
                role,
            ]

            for node in nodes:
                try:
                    node.run(args=dcos_install_args)
                except subprocess.CalledProcessError as ex:  # pragma: no cover
                    LOGGER.error(ex.stdout)
                    LOGGER.error(ex.stderr)
                    raise

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
                container.stop()
                container.remove(v=True)

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

        nodes = set([])
        for container in containers:
            container_ip_address = IPv4Address(
                container.attrs['NetworkSettings']['IPAddress'],
            )
            nodes.add(
                Node(
                    public_ip_address=container_ip_address,
                    private_ip_address=container_ip_address,
                    default_ssh_user=self._default_ssh_user,
                    ssh_key_path=self._path / 'include' / 'ssh' / 'id_rsa',
                ),
            )
        return nodes

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master :class:`.node.Node` s.
        """
        return self._nodes(container_base_name=self._master_prefix)

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent :class:`.node.Node` s.
        """
        return self._nodes(container_base_name=self._agent_prefix)

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent :class:`.node.Node` s.
        """
        return self._nodes(container_base_name=self._public_agent_prefix)

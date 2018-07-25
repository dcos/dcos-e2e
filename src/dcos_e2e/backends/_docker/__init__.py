"""
Helpers for creating and interacting with clusters on Docker.
"""

import inspect
import os
import socket
import subprocess
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import copyfile, copytree, rmtree
from tempfile import gettempdir
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Type

import docker
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docker.types import Mount

from dcos_e2e._common import get_logger, run_subprocess
from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Node, Transport

from ._containers import start_dcos_container
from ._docker_build import build_docker_image

LOGGER = get_logger(__name__)


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
        custom_container_mounts: Optional[List[Mount]] = None,
        custom_master_mounts: Optional[List[Mount]] = None,
        custom_agent_mounts: Optional[List[Mount]] = None,
        custom_public_agent_mounts: Optional[List[Mount]] = None,
        linux_distribution: Distribution = Distribution.CENTOS_7,
        docker_version: DockerVersion = DockerVersion.v1_13_1,
        storage_driver: Optional[DockerStorageDriver] = None,
        docker_container_labels: Optional[Dict[str, str]] = None,
        docker_master_labels: Optional[Dict[str, str]] = None,
        docker_agent_labels: Optional[Dict[str, str]] = None,
        docker_public_agent_labels: Optional[Dict[str, str]] = None,
        transport: Transport = Transport.DOCKER_EXEC,
        network: Optional[docker.models.networks.Network] = None,
        one_master_host_port_map: Optional[Dict[str, int]] = None,
    ) -> None:
        """
        Create a configuration for a Docker cluster backend.

        Args:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
                This is equivalent to `dir` in
                :py:func:`tempfile.mkstemp`.
            custom_container_mounts: Custom mounts add to all node containers.
                See `mounts` in `Containers.run`_.
            custom_master_mounts: Custom mounts add to master node containers.
                See `mounts` in `Containers.run`_.
            custom_agent_mounts: Custom mounts add to agent node containers.
                See `mounts` in `Containers.run`_.
            custom_public_agent_mounts: Custom mounts add to public agent node
                containers. See `mounts` in `Containers.run`_.
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
            transport: The transport to use for communicating with nodes.
            network: The Docker network containers will be connected to. If no
                network is specified the ``docker0`` bridge network is used.
                It may not be possible to SSH to containers on a
                custom network on macOS.
            one_master_host_port_map: The exposed host ports for one of the
                master nodes. This is useful on macOS on which the container IP
                is not directly accessible from the host. By exposing the host
                ports, the user can reach the services on the master node using
                the mapped host ports. The host port map will be applied to one
                master only if there are multiple master nodes. See `ports` in
                `Containers.run`_. Currently, only Transmission Control
                Protocol is supported.

        Attributes:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
            custom_container_mounts: Custom mounts add to all node containers.
                See `mounts` in `Containers.run`_.
            custom_master_mounts: Custom mounts add to master node containers.
                See `mounts` in `Containers.run`_.
            custom_agent_mounts: Custom mounts add to agent node containers.
                See `mounts` in `Containers.run`_.
            custom_public_agent_mounts: Custom mounts add to public agent node
                containers. See `mounts` in `Containers.run`_.
            linux_distribution: The Linux distribution to boot DC/OS on.
            docker_version: The Docker version to install on the cluster nodes.
            docker_storage_driver: The storage driver to use for Docker on the
                cluster nodes.
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
            transport: The transport to use for communicating with nodes.
            network: The Docker network containers will be connected to. If no
                network is specified the ``docker0`` bridge network is used.
                It may not be possible to SSH to containers on a
                custom network on macOS.
            one_master_host_port_map: The exposed host ports for one of the
                master nodes. This is useful on macOS on which the container IP
                is not directly accessible from the host. By exposing the host
                ports, the user can reach the services on the master node using
                the mapped host ports. The host port map will be applied to one
                master only if there are multiple master nodes. See `ports` in
                `Containers.run`_. Currently, only Transmission Control
                Protocol is supported.

        .. _Containers.run:
            http://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run
        """
        self.docker_version = docker_version
        self.workspace_dir = workspace_dir or Path(gettempdir())
        self.custom_container_mounts = custom_container_mounts or []
        self.custom_master_mounts = custom_master_mounts or []
        self.custom_agent_mounts = custom_agent_mounts or []
        self.custom_public_agent_mounts = custom_public_agent_mounts or []
        self.linux_distribution = linux_distribution
        fallback_driver = _get_fallback_storage_driver()
        self.docker_storage_driver = storage_driver or fallback_driver
        self.docker_container_labels = docker_container_labels or {}
        self.docker_master_labels = docker_master_labels or {}
        self.docker_agent_labels = docker_agent_labels or {}
        self.docker_public_agent_labels = docker_public_agent_labels or {}
        self.transport = transport
        self.network = network
        self.one_master_host_port_map = one_master_host_port_map or {}

    @property
    def cluster_cls(self) -> Type['DockerCluster']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return DockerCluster

    @property
    def ip_detect_path(self) -> Path:
        """
        Return the path to the Docker specific ``ip-detect`` script.
        """
        current_file = inspect.stack()[0][1]
        current_parent = Path(os.path.abspath(current_file)).parent
        return current_parent / 'resources' / 'ip-detect'


class DockerCluster(ClusterManager):
    """
    A record of a Docker cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
        cluster_backend: Docker,
    ) -> None:
        """
        Create a Docker cluster.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            cluster_backend: Details of the specific Docker backend to use.
        """
        self._default_user = 'root'
        self._default_transport = cluster_backend.transport

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
        self._genconf_dir.mkdir(exist_ok=True, parents=True)
        self._genconf_dir = self._genconf_dir.resolve()
        include_dir = self._path / 'include'
        certs_dir = include_dir / 'certs'
        certs_dir.mkdir(parents=True)
        ssh_dir = include_dir / 'ssh'
        ssh_dir.mkdir(parents=True)

        public_key_path = ssh_dir / 'id_rsa.pub'
        _write_key_pair(
            public_key_path=public_key_path,
            private_key_path=ssh_dir / 'id_rsa',
        )

        self._master_prefix = self._cluster_id + '-master-'
        self._agent_prefix = self._cluster_id + '-agent-'
        self._public_agent_prefix = self._cluster_id + '-public-agent-'

        bootstrap_genconf_path = self._genconf_dir / 'serve'
        bootstrap_genconf_path.mkdir()
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

        certs_mount = Mount(
            source=str(certs_dir.resolve()),
            target='/etc/docker/certs.d',
            read_only=False,
            type='bind',
        )

        bootstrap_genconf_mount = Mount(
            source=str(bootstrap_genconf_path),
            target=str(self._bootstrap_tmp_path),
            read_only=True,
            type='bind',
        )

        # Mount cgroups into agents for Mesos DRF.
        cgroup_mount = Mount(
            source='/sys/fs/cgroup',
            target='/sys/fs/cgroup',
            read_only=True,
            type='bind',
        )

        var_lib_docker_mount = Mount(
            source=None,
            target='/var/lib/docker',
        )

        opt_mount = Mount(
            source=None,
            target='/opt',
        )

        mesos_slave_mount = Mount(
            source=None,
            target='/var/lib/mesos/slave',
        )

        agent_mounts = [
            certs_mount,
            bootstrap_genconf_mount,
            cgroup_mount,
            var_lib_docker_mount,
            opt_mount,
            mesos_slave_mount,
            *cluster_backend.custom_container_mounts,
        ]

        master_mounts = [
            certs_mount,
            bootstrap_genconf_mount,
            var_lib_docker_mount,
            opt_mount,
            *cluster_backend.custom_container_mounts,
            *cluster_backend.custom_master_mounts,
        ]

        for master_container_number in range(masters):
            ports = {}  # type: Dict[str, int]
            if master_container_number == 0:
                ports = cluster_backend.one_master_host_port_map
            start_dcos_container(
                container_base_name=self._master_prefix,
                container_number=master_container_number,
                mounts=master_mounts,
                tmpfs=node_tmpfs_mounts,
                docker_image=docker_image_tag,
                labels={
                    **cluster_backend.docker_container_labels,
                    **cluster_backend.docker_master_labels,
                },
                public_key_path=public_key_path,
                docker_storage_driver=(cluster_backend.docker_storage_driver),
                docker_version=cluster_backend.docker_version,
                network=cluster_backend.network,
                ports=ports,
            )

        for nodes, prefix, labels, mounts in (
            (
                agents,
                self._agent_prefix,
                cluster_backend.docker_agent_labels,
                agent_mounts + cluster_backend.custom_agent_mounts,
            ),
            (
                public_agents,
                self._public_agent_prefix,
                cluster_backend.docker_public_agent_labels,
                agent_mounts + cluster_backend.custom_public_agent_mounts,
            ),
        ):
            for agent_container_number in range(nodes):
                start_dcos_container(
                    container_base_name=prefix,
                    container_number=agent_container_number,
                    mounts=mounts,
                    tmpfs=node_tmpfs_mounts,
                    docker_image=docker_image_tag,
                    labels={
                        **cluster_backend.docker_container_labels,
                        **labels,
                    },
                    public_key_path=public_key_path,
                    docker_storage_driver=(
                        cluster_backend.docker_storage_driver
                    ),
                    docker_version=cluster_backend.docker_version,
                    network=cluster_backend.network,
                )

    def install_dcos_from_url_with_bootstrap_node(
        self,
        build_artifact: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        log_output_live: bool,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from a URL with a bootstrap node.
        This is not supported and simply raises a ``NotImplementedError``.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script that is used for
                installing DC/OS.
            log_output_live: If ``True``, log output of the installation live.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.

        Raises:
            NotImplementedError: ``NotImplementedError`` because the Docker
                backend does not support the DC/OS advanced installation
                method with a bootstrap node.
        """
        raise NotImplementedError

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS, not including the
        list of nodes.
        """
        ssh_user = self._default_user
        return {
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
            'process_timeout': 10000,
            'resolvers': ['8.8.8.8'],
            'ssh_port': 22,
            'ssh_user': ssh_user,
        }

    def install_dcos_from_path_with_bootstrap_node(
        self,
        build_artifact: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        log_output_live: bool,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from a given build artifact.

        Args:
            build_artifact: The ``Path`` to a build artifact to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script that is used for
                installing DC/OS.
            log_output_live: If ``True``, log output of the installation live.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.

        Raises:
            CalledProcessError: There was an error installing DC/OS on a node.
        """
        copyfile(
            src=str(ip_detect_path),
            dst=str(self._genconf_dir / 'ip-detect'),
        )

        config_yaml = yaml.dump(data=dcos_config)
        config_file_path = self._genconf_dir / 'config.yaml'
        config_file_path.write_text(data=config_yaml)

        for host_path, installer_path in files_to_copy_to_genconf_dir:
            relative_installer_path = installer_path.relative_to('/genconf')
            destination_path = self._genconf_dir / relative_installer_path
            if host_path.is_dir():
                destination_path = destination_path / host_path.stem
                copytree(src=str(host_path), dst=str(destination_path))
            else:
                copyfile(src=str(host_path), dst=str(destination_path))

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

    def destroy_node(self, node: Node) -> None:
        """
        Destroy a node in the cluster.
        """
        client = docker.from_env(version='auto')
        containers = client.containers.list()
        for container in containers:
            networks = container.attrs['NetworkSettings']['Networks']
            for net in networks:
                if networks[net]['IPAddress'] == str(node.public_ip_address):
                    container.stop()
                    container.remove(v=True)

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        for node in {*self.masters, *self.agents, *self.public_agents}:
            self.destroy_node(node=node)

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
            networks = container.attrs['NetworkSettings']['Networks']
            network_name = 'bridge'
            if len(networks) != 1:
                [network_name] = list(networks.keys() - set(['bridge']))
            container_ip_address = IPv4Address(
                networks[network_name]['IPAddress'],
            )
            nodes.add(
                Node(
                    public_ip_address=container_ip_address,
                    private_ip_address=container_ip_address,
                    default_user=self._default_user,
                    ssh_key_path=self._path / 'include' / 'ssh' / 'id_rsa',
                    default_transport=self._default_transport,
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

"""
Helpers for interacting with DC/OS Docker.
"""

import socket
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import copyfile, copytree, ignore_patterns, rmtree
from typing import Any, Dict, Set, Type

import docker
import yaml

from .._common import Node, run_subprocess
from ._base_classes import ClusterBackend, ClusterManager


def _get_open_port() -> int:
    """
    Return a free port.
    """
    host = ''
    # We ignore type hinting to avoid a bug in `typeshed`.
    # See https://github.com/python/typeshed/issues/1391.
    with socket.socket(  # type: ignore
        socket.AF_INET, socket.SOCK_STREAM
    ) as new_socket:
        new_socket.bind((host, 0))
        new_socket.listen(1)
        return new_socket.getsockname()[1]


class DCOS_Docker(ClusterBackend):  # pylint: disable=invalid-name
    """
    A record of a DC/OS Docker backend which can be used to create clusters.
    """

    def __init__(
        self,
        workspace_path: Path,
        generate_config_path: Path,
        dcos_docker_path: Path
    ) -> None:
        """
        Create a configuration for a DC/OS Docker cluster backend.

        Args:
            generate_config_path: The path to a build artifact to install.
            dcos_docker_path: The path to a clone of DC/OS Docker.
                This clone will be used to create the cluster.
            workspace_path: The directory to create large temporary files in.
                The files are cleaned up when the cluster is destroyed.

        Attributes:
            generate_config_path: The path to a build artifact to install.
            dcos_docker_path: The path to a clone of DC/OS Docker.
                This clone will be used to create the cluster.
            workspace_path: The directory to create large temporary files in.
                The files are cleaned up when the cluster is destroyed.
        """
        self.workspace_path = workspace_path
        self.generate_config_path = generate_config_path
        self.dcos_docker_path = dcos_docker_path

    @property
    def cluster_cls(self) -> Type['DCOS_Docker_Cluster']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return DCOS_Docker_Cluster


class DCOS_Docker_Cluster(ClusterManager):  # pylint: disable=invalid-name
    """
    A record of a DC/OS Docker cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
        extra_config: Dict[str, Any],
        log_output_live: bool,
        files_to_copy_to_installer: Dict[Path, Path],
        files_to_copy_to_masters: Dict[Path, Path],
        cluster_backend: DCOS_Docker,
        superuser_username: str,
        superuser_password: str,
    ) -> None:
        """
        Create a DC/OS Docker cluster.

        Args:
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
            superuser_username: The username of the cluster superuser.
            superuser_password: The password of the cluster superuser.
                Currently DC/OS Docker only supports "admin".

        Raises:
            ValueError: The given superuser password is not "admin".
        """
        if superuser_password != 'admin':
            raise ValueError(
                "The only superuser password which is supported by DC/OS "
                "Docker is 'admin'. "
                "See https://jira.mesosphere.com/browse/DCOS-16035."
            )
        self.log_output_live = log_output_live

        # To avoid conflicts, we use random container names.
        # We use the same random string for each container in a cluster so
        # that they can be associated easily.
        random = uuid.uuid4()

        # We create a new instance of DC/OS Docker and we work in this
        # directory.
        # This helps running tests in parallel without conflicts and it
        # reduces the chance of side-effects affecting sequential tests.
        workspace = cluster_backend.workspace_path
        self._path = workspace / 'dcos-docker-{random}'.format(random=random)

        copytree(
            src=str(cluster_backend.dcos_docker_path),
            dst=str(self._path),
            # If there is already a config, we do not copy it as it will be
            # overwritten and therefore copying it is wasteful.
            ignore=ignore_patterns('dcos_generate_config.sh'),
        )

        copyfile(
            src=str(cluster_backend.generate_config_path),
            dst=str(self._path / 'dcos_generate_config.sh'),
        )

        master_ctr = 'dcos-master-{random}-'.format(random=random)
        agent_ctr = 'dcos-agent-{random}-'.format(random=random)
        public_agent_ctr = 'dcos-public-agent-{random}-'.format(random=random)
        # Only overlay and aufs storage drivers are supported.
        # This chooses the aufs driver if the host's driver is not supported.
        # aufs was chosen as it is supported on the version of Docker on
        # Travis CI.
        client = docker.from_env(version='auto')
        host_driver = client.info()['Driver']
        storage_driver = host_driver if host_driver in (
            'overlay', 'aufs'
        ) else 'aufs'
        self._variables = {
            'DOCKER_STORAGEDRIVER': storage_driver,
            # Some platforms support systemd and some do not.
            # Disabling support makes all platforms consistent in this aspect.
            'MESOS_SYSTEMD_ENABLE_SUPPORT': 'false',
            # Number of nodes.
            'MASTERS': str(masters),
            'AGENTS': str(agents),
            'PUBLIC_AGENTS': str(public_agents),
            # Container names.
            'MASTER_CTR': master_ctr,
            'AGENT_CTR': agent_ctr,
            'PUBLIC_AGENT_CTR': public_agent_ctr,
            'MASTER_MOUNTS': '',
            # This is a workaround for an error which occurs with DC/OS Docker
            # when "$HOME" is not set.
            # See https://jira.mesosphere.com/browse/DCOS_OSS-1193.
            'HOME_MOUNTS': '',
            'SUPERUSER_USERNAME': superuser_username,
            'SUPERUSER_PASSWORD': superuser_password,
            'INSTALLER_PORT': str(_get_open_port()),
        }  # type: Dict[str, str]

        if extra_config:
            self._variables['EXTRA_GENCONF_CONFIG'] = yaml.dump(
                data=extra_config,
                default_flow_style=False,
            )

        # Files in the DC/OS Docker directory's genconf directory are mounted
        # to the installer at `/genconf`.
        # Therefore, every file which we want to copy to `/genconf` on the
        # installer is put into the genconf directory in DC/OS Docker.
        for host_path, installer_path in files_to_copy_to_installer.items():
            relative_installer_path = installer_path.relative_to('/genconf')
            destination_path = self._path / 'genconf' / relative_installer_path
            copyfile(src=str(host_path), dst=str(destination_path))

        master_mounts = []
        for host_path, master_path in files_to_copy_to_masters.items():
            mount = '-v {host_path}:{master_path}:ro'.format(
                host_path=host_path,
                master_path=master_path,
            )
            master_mounts.append(mount)

        self._variables['MASTER_MOUNTS'] = ' '.join(master_mounts)
        self._make(target='all')

    def _make(self, target: str) -> None:
        """
        Run `make` in the DC/OS Docker directory using variables associated
        with this instance.

        Args:
            target: `make` target to run.

        Raises:
            CalledProcessError: The process exited with a non-zero code.
        """
        args = ['make'] + [
            '{key}={value}'.format(key=key, value=value)
            for key, value in self._variables.items()
        ] + [target]

        run_subprocess(
            args=args,
            cwd=str(self._path),
            log_output_live=self.log_output_live
        )

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        self._make(target='clean')
        rmtree(
            path=str(self._path),
            # Some files may be created in the container that we cannot clean
            # up.
            ignore_errors=True,
        )

    def _nodes(self, container_base_name: str, num_nodes: int) -> Set[Node]:
        """
        Args:
            container_base_name: The start of the container names.
            num_nodes: The number of nodes.

        Returns: ``Node``s corresponding to containers with names starting
            with ``container_base_name``.
        """
        client = docker.from_env(version='auto')
        nodes = set([])  # type: Set[Node]

        while len(nodes) < num_nodes:
            container_name = '{container_base_name}{number}'.format(
                container_base_name=container_base_name,
                number=len(nodes) + 1,
            )
            container = client.containers.get(container_name)
            ip_address = container.attrs['NetworkSettings']['IPAddress']
            node = Node(
                ip_address=IPv4Address(ip_address),
                ssh_key_path=self._path / 'include' / 'ssh' / 'id_rsa',
            )
            nodes.add(node)

        return nodes

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master ``Node``s.
        """
        return self._nodes(
            container_base_name=self._variables['MASTER_CTR'],
            num_nodes=int(self._variables['MASTERS']),
        )

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """
        return self._nodes(
            container_base_name=self._variables['AGENT_CTR'],
            num_nodes=int(self._variables['AGENTS']),
        )

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent ``Node``s.
        """
        return self._nodes(
            container_base_name=self._variables['PUBLIC_AGENT_CTR'],
            num_nodes=int(self._variables['PUBLIC_AGENTS']),
        )

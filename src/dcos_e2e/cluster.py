"""
DC/OS Cluster management tools. Independent of back ends.
"""

import logging
import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from retry import retry

from . import _wait_for_dcos
from ._existing_cluster import ExistingCluster as _ExistingCluster
from .base_classes import ClusterManager  # noqa: F401
from .base_classes import ClusterBackend
from .node import Node, Output, Role, Transport

LOGGER = logging.getLogger(__name__)


@retry(
    exceptions=(subprocess.CalledProcessError),
    tries=5,
    delay=2,
)
def _wait_for_ssh(node: Node) -> None:
    """
    Retry up to five times (arbitrary) until SSH is available on the given
    node.
    """
    # In theory we could just use any args and specify the transport as SSH.
    # However, this would not work on macOS without a special network set up.
    args = [
        'systemctl',
        'status',
        'sshd.socket',
        '||',
        'systemctl',
        'status',
        'sshd',
    ]
    node.run(
        args=args,
        output=Output.LOG_AND_CAPTURE,
        shell=True,
    )


class Cluster(ContextDecorator):
    """
    A record of a DC/OS cluster.

    This is intended to be used as context manager.
    """

    def __init__(
        self,
        cluster_backend: ClusterBackend,
        masters: int = 1,
        agents: int = 1,
        public_agents: int = 1,
    ) -> None:
        """
        Create a DC/OS cluster.

        Args:
            cluster_backend: The backend to use for the cluster.
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
        """
        self._cluster = cluster_backend.cluster_cls(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            cluster_backend=cluster_backend,
        )  # type: ClusterManager
        self._base_config = cluster_backend.base_config

        for node in {
            *self.masters,
            *self.agents,
            *self.public_agents,
        }:
            _wait_for_ssh(node=node)

    @classmethod
    def from_nodes(
        cls,
        masters: Set[Node],
        agents: Set[Node],
        public_agents: Set[Node],
    ) -> 'Cluster':
        """
        Create a cluster from existing nodes.

        Args:
            masters: The master nodes in an existing cluster.
            agents: The agent nodes in an existing cluster.
            public_agents: The public agent nodes in an existing cluster.

        Returns:
            A cluster object with the nodes of an existing cluster.
        """
        backend = _ExistingCluster(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        )

        return cls(
            masters=len(masters),
            agents=len(agents),
            public_agents=len(public_agents),
            cluster_backend=backend,
        )

    def wait_for_dcos_oss(
        self,
        http_checks: bool = True,
    ) -> None:
        """
        Wait until the DC/OS OSS boot process has completed.

        Args:
            http_checks: Whether or not to wait for checks which involve HTTP.
                If this is `False`, this function may return before DC/OS is
                fully ready. This is useful in cases where an HTTP connection
                cannot be made to the cluster. For example, this is useful on
                macOS without a VPN set up.

        Raises:
            dcos_e2e.exceptions.DCOSTimeoutError: Raised if cluster components
                did not become ready within one hour.
        """
        _wait_for_dcos.wait_for_dcos_oss(
            masters=self.masters,
            agents=self.agents,
            public_agents=self.public_agents,
            http_checks=http_checks,
        )

    def wait_for_dcos_ee(
        self,
        superuser_username: str,
        superuser_password: str,
        http_checks: bool = True,
    ) -> None:
        """
        Wait until the DC/OS Enterprise boot process has completed.

        Args:
            superuser_username: Username of a user with superuser privileges.
            superuser_password: Password of a user with superuser privileges.
            http_checks: Whether or not to wait for checks which involve HTTP.
                If this is `False`, this function may return before DC/OS is
                fully ready. This is useful in cases where an HTTP connection
                cannot be made to the cluster. For example, this is useful on
                macOS without a VPN set up.

        Raises:
            dcos_e2e.exceptions.DCOSTimeoutError: Raised if cluster components
                did not become ready within one hour.
        """
        _wait_for_dcos.wait_for_dcos_ee(
            masters=self.masters,
            agents=self.agents,
            public_agents=self.public_agents,
            superuser_username=superuser_username,
            superuser_password=superuser_password,
            http_checks=http_checks,
        )

    def install_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output = Output.CAPTURE,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
    ) -> None:
        """
        Installs DC/OS using the DC/OS advanced installation method.

        Args:
            dcos_installer: A URL pointing to an installer to install DC/OS
                from.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            ip_detect_path: The path to a ``ip-detect`` script that will be
                used when installing DC/OS.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            output: What happens with stdout and stderr.
        """
        self._cluster.install_dcos_from_url(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=output,
        )

    def install_dcos_from_path(
        self,
        dcos_installer: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output = Output.CAPTURE,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
    ) -> None:
        """
        Installs DC/OS using the DC/OS advanced installation method.

        Args:
            dcos_installer: The ``Path`` to a local installer to install DC/OS
                from.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            ip_detect_path: The path to a ``ip-detect`` script that will be
                used when installing DC/OS.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            output: What happens with stdout and stderr.
        """
        self._cluster.install_dcos_from_path(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=output,
        )

    def upgrade_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output = Output.CAPTURE,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
    ) -> None:
        """
        Upgrade DC/OS.

        Args:
            dcos_installer: A URL pointing to an installer to upgrade DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The path to a ``ip-detect`` script that will be
                used when installing DC/OS.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            output: What happens with stdout and stderr.
        """
        for nodes, role in (
            (self.masters, Role.MASTER),
            (self.agents, Role.AGENT),
            (self.public_agents, Role.PUBLIC_AGENT),
        ):
            for node in nodes:
                node.upgrade_dcos_from_url(
                    dcos_installer=dcos_installer,
                    dcos_config=dcos_config,
                    ip_detect_path=ip_detect_path,
                    role=role,
                    files_to_copy_to_genconf_dir=(
                        files_to_copy_to_genconf_dir
                    ),
                    output=output,
                )

    def upgrade_dcos_from_path(
        self,
        dcos_installer: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output = Output.CAPTURE,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
    ) -> None:
        """
        Upgrade DC/OS.

        Args:
            dcos_installer: The ``Path`` to a local installer or a ``str`` to
                which is a URL pointing to an installer to install DC/OS from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The path to a ``ip-detect`` script that will be
                used when installing DC/OS.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            output: What happens with stdout and stderr.
        """
        for nodes, role in (
            (self.masters, Role.MASTER),
            (self.agents, Role.AGENT),
            (self.public_agents, Role.PUBLIC_AGENT),
        ):
            for node in nodes:
                node.upgrade_dcos_from_path(
                    dcos_installer=dcos_installer,
                    dcos_config=dcos_config,
                    ip_detect_path=ip_detect_path,
                    role=role,
                    files_to_copy_to_genconf_dir=(
                        files_to_copy_to_genconf_dir
                    ),
                    output=output,
                )

    def __enter__(self) -> 'Cluster':
        """
        Enter a context manager.
        The context manager receives this ``Cluster`` instance.
        """
        return self

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master :class:`.node.Node` s.
        """
        return self._cluster.masters

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent :class:`.node.Node` s.
        """
        return self._cluster.agents

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent :class:`.node.Node` s.
        """
        return self._cluster.public_agents

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """

        def ip_list(nodes: Set[Node]) -> List[str]:
            return list(map(lambda node: str(node.private_ip_address), nodes))

        config = {
            'agent_list': ip_list(nodes=self.agents),
            'master_list': ip_list(nodes=self.masters),
            'public_agent_list': ip_list(nodes=self.public_agents),
        }
        return {
            **config,
            **self._base_config,
        }

    def run_with_test_environment(
        self,
        args: List[str],
        env: Optional[Dict[str, Any]] = None,
        output: Output = Output.CAPTURE,
        tty: bool = False,
        node: Optional[Node] = None,
        transport: Optional[Transport] = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a command on a node using the Mesosphere test environment.

        Args:
            args: The command to run on the node.
            env: Environment variables to be set on the node before running
                the command. On enterprise clusters, ``DCOS_LOGIN_UNAME`` and
                ``DCOS_LOGIN_PW`` must be set.
            output: What happens with stdout and stderr.
            node: The node to run the given command on. if not given, an
                arbitrary master node is used.
            tty: If ``True``, allocate a pseudo-tty. This means that the users
                terminal is attached to the streams of the process.
                This means that the values of stdout and stderr will not be in
                the returned ``subprocess.CompletedProcess``.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.

        Returns:
            The result of the given command.

        Raises:
            subprocess.CalledProcessError: If the command fails.
        """
        args = [
            '.',
            '/opt/mesosphere/environment.export',
            '&&',
            'cd',
            '/opt/mesosphere/active/dcos-integration-test/',
            '&&',
            *args,
        ]

        env = env or {}

        def ip_addresses(nodes: Iterable[Node]) -> str:
            return ','.join(
                map(lambda node: str(node.private_ip_address), nodes),
            )

        # Tests are run on a random master node if no node is given.
        node = node or next(iter(self.masters))

        environment_variables = {
            # This is needed for 1.9 (and below?)
            'PUBLIC_MASTER_HOSTS': ip_addresses(self.masters),
            'MASTER_HOSTS': ip_addresses(self.masters),
            'SLAVE_HOSTS': ip_addresses(self.agents),
            'PUBLIC_SLAVE_HOSTS': ip_addresses(self.public_agents),
            'DCOS_DNS_ADDRESS': 'http://' + str(node.private_ip_address),
            # This is only used by DC/OS 1.9 integration tests
            'DCOS_NUM_MASTERS': len(self.masters),
            'DCOS_NUM_AGENTS': len(self.agents) + len(self.public_agents),
            **env,
        }

        return node.run(
            args=args,
            output=output,
            env=environment_variables,
            tty=tty,
            shell=True,
            transport=transport,
        )

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        self._cluster.destroy()

    def destroy_node(self, node: Node) -> None:
        """
        Destroy a node in the cluster.
        """
        self._cluster.destroy_node(node=node)

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Any,
    ) -> bool:
        """
        On exiting, destroy all nodes in the cluster if the backend supports
        it.
        """
        # This is a hack to make Vulture not think that these are unused
        # arguments. We have to receive them to be a valid context manager.
        for _ in (exc_type, exc_value, traceback):
            pass

        try:
            self.destroy()
        except NotImplementedError:
            pass

        return False

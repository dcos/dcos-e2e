"""
DC/OS Cluster management tools. Independent of back ends.
"""

import json
import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from retry import retry

from ._vendor.dcos_test_utils.dcos_api import DcosApiSession, DcosUser
from ._vendor.dcos_test_utils.enterprise import EnterpriseApiSession
from ._vendor.dcos_test_utils.helpers import CI_CREDENTIALS
# Ignore a spurious error - this import is used in a type hint.
from .backends import ClusterManager  # noqa: F401
from .backends import ClusterBackend, _ExistingCluster
from .node import Node, Role, Transport


@retry(
    exceptions=(subprocess.CalledProcessError),
    tries=5,
    delay=1,
)
def _wait_for_ssh(node: Node) -> None:
    """
    Retry up to five times (arbitrary) until SSH is available on the given
    node.
    """
    node.run(args=['systemctl', 'status', 'sshd'])


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

    @retry(
        exceptions=(subprocess.CalledProcessError),
        tries=500,
        delay=10,
    )
    def _wait_for_node_poststart(self) -> None:
        """
        Wait until all DC/OS node-poststart checks are healthy.

        The execution will differ for different version of DC/OS.
        ``dcos-check-runner`` only exists on DC/OS 1.12+. ``dcos-diagnostics
        check node-poststart`` only works on DC/OS 1.10 and 1.11. ``3dt`` only
        exists on DC/OS 1.9. ``node-poststart`` requires ``sudo`` to allow
        reading the CA certificate used by certain checks.
        """
        for node in self.masters:
            node.run(
                args=[
                    'sudo',
                    '/opt/mesosphere/bin/dcos-check-runner',
                    'check',
                    'node-poststart',
                    '||',
                    'sudo',
                    '/opt/mesosphere/bin/dcos-diagnostics',
                    'check',
                    'node-poststart',
                    '||',
                    '/opt/mesosphere/bin/3dt',
                    '--diag',
                ],
                # Keep in mind this must be run as privileged user.
                log_output_live=True,
                shell=True,
            )

    def wait_for_dcos_oss(self, http_checks: bool = True) -> None:
        """
        Wait until the DC/OS OSS boot process has completed.

        Args:
            http_checks: Whether or not to wait for checks which involve HTTP.
                If this is `False`, this function may return before DC/OS is
                fully ready. This is useful in cases where an HTTP connection
                cannot be made to the cluster. For example, this is useful on
                macOS without a VPN set up.

        Raises:
            RetryError: Raised if any cluster component did not become
                healthy in time.
        """

        self._wait_for_node_poststart()
        if not http_checks:
            return

        # The dcos-diagnostics check is not yet sufficient to determine
        # when a CLI login would be possible with DC/OS OSS. It only
        # checks the healthy state of the systemd units, not reachability
        # of services through HTTP.

        # Since DC/OS uses a Single-Sign-On flow with Identity Providers
        # outside the cluster for the login and Admin Router only rewrites
        # requests to them, the login endpoint does not provide anything.

        # Current solution to guarantee the security CLI login:

        # Try until one can login successfully with a long lived token
        # (dirty hack in dcos-test-utils wait_for_dcos). This is to avoid
        # having to simulate a browser that does the SSO flow.

        # Suggestion for replacing this with a DC/OS check for CLI login:

        # Determine and wait for all dependencies of the SSO OAuth login
        # inside of DC/OS. This should include Admin Router, ZooKeeper and
        # the DC/OS OAuth login service. Note that this may only guarantee
        # that the login could work, however not that is actually works.

        # In order to fully replace this method one would need to have
        # DC/OS checks for every HTTP endpoint exposed by Admin Router.

        any_master = next(iter(self.masters))

        api_session = DcosApiSession(
            dcos_url='http://{ip}'.format(ip=any_master.public_ip_address),
            masters=[str(n.public_ip_address) for n in self.masters],
            slaves=[str(n.public_ip_address) for n in self.agents],
            public_slaves=[
                str(n.public_ip_address) for n in self.public_agents
            ],
            auth_user=DcosUser(credentials=CI_CREDENTIALS),
        )

        api_session.wait_for_dcos()  # type: ignore

    def wait_for_dcos_ee(
        self,
        superuser_username: str,
        superuser_password: str,
        http_checks: bool = True,
    ) -> None:
        """
        Wait until the DC/OS Enterprise boot process has completed.

        Args:
            superuser_username: Username of the default superuser.
            superuser_password: Password of the default superuser.
            http_checks: Whether or not to wait for checks which involve HTTP.
                If this is `False`, this function may return before DC/OS is
                fully ready. This is useful in cases where an HTTP connection
                cannot be made to the cluster. For example, this is useful on
                macOS without a VPN set up.

        Raises:
            RetryError: Raised if any cluster component did not become
                healthy in time.
        """

        self._wait_for_node_poststart()
        if not http_checks:
            return

        # The dcos-diagnostics check is not yet sufficient to determine
        # when a CLI login would be possible with Enterprise DC/OS. It only
        # checks the healthy state of the systemd units, not reachability
        # of services through HTTP.

        # In the case of Enterprise DC/OS this method uses dcos-test-utils
        # and superuser credentials to perform a superuser login that
        # assure authenticating via CLI is working.

        # Suggestion for replacing this with a DC/OS check for CLI login:

        # In Enterprise DC/OS this could be replace by polling the login
        # endpoint with random login credentials until it returns 401. In
        # that case the guarantees would be the same as with the OSS
        # suggestion.

        # The progress on a partial replacement can be followed here:
        # https://jira.mesosphere.com/browse/DCOS_OSS-1313

        # In order to fully replace this method one would need to have
        # DC/OS checks for every HTTP endpoint exposed by Admin Router.

        credentials = {
            'uid': superuser_username,
            'password': superuser_password,
        }

        any_master = next(iter(self.masters))
        config_result = any_master.run(
            args=['cat', '/opt/mesosphere/etc/bootstrap-config.json'],
        )
        config = json.loads(config_result.stdout.decode())
        ssl_enabled = config['ssl_enabled']

        scheme = 'https://' if ssl_enabled else 'http://'
        dcos_url = scheme + str(any_master.public_ip_address)
        enterprise_session = EnterpriseApiSession(  # type: ignore
            dcos_url=dcos_url,
            masters=[str(n.public_ip_address) for n in self.masters],
            slaves=[str(n.public_ip_address) for n in self.agents],
            public_slaves=[
                str(n.public_ip_address) for n in self.public_agents
            ],
            auth_user=DcosUser(credentials=credentials),
        )

        if ssl_enabled:
            response = enterprise_session.get(
                # We wait for 10 minutes which is arbitrary but should
                # be more than enough after all systemd units are healthy.
                '/ca/dcos-ca.crt',
                retry_timeout=60 * 10,
                verify=False,
            )
            response.raise_for_status()
            enterprise_session.set_ca_cert()

        enterprise_session.wait_for_dcos()

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
            **self._cluster.base_config,
        }

    def install_dcos_from_url(
        self,
        build_artifact: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        log_output_live: bool = False,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
    ) -> None:
        """
        Installs DC/OS using the DC/OS advanced installation method.

        If supported by the cluster backend, this method spins up a persistent
        bootstrap host that supplies all dedicated DC/OS hosts with the
        necessary installation files.

        Since the bootstrap host is different from the host initiating the
        cluster creation passing the ``build_artifact`` via URL string
        saves the time of copying the ``build_artifact`` to the bootstrap host.

        However, some backends may not support using a bootstrap node. For
        these backends, each node will download and extract the build
        artifact. This may be very slow, as the build artifact is downloaded to
        and extracted on each node, one at a time.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            ip_detect_path: The path to a ``ip-detect`` script that will be
                used when installing DC/OS.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            log_output_live: If `True`, log output of the installation live.
                If `True`, stderr is merged into stdout in the return value.
        """
        try:
            self._cluster.install_dcos_from_url_with_bootstrap_node(
                build_artifact=build_artifact,
                dcos_config=dcos_config,
                ip_detect_path=ip_detect_path,
                files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
                log_output_live=log_output_live,
            )
        except NotImplementedError:
            for nodes, role in (
                (self.masters, Role.MASTER),
                (self.agents, Role.AGENT),
                (self.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    node.install_dcos_from_url(
                        build_artifact=build_artifact,
                        dcos_config=dcos_config,
                        ip_detect_path=ip_detect_path,
                        files_to_copy_to_genconf_dir=(
                            files_to_copy_to_genconf_dir
                        ),
                        role=role,
                        log_output_live=log_output_live,
                    )

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
        log_output_live: bool = False,
    ) -> None:
        """
        Args:
            build_artifact: The `Path` to a build artifact to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The path to a ``ip-detect`` script that will be
                used when installing DC/OS.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            log_output_live: If `True`, log output of the installation live.
                If `True`, stderr is merged into stdout in the return value.

        Raises:
            NotImplementedError: `NotImplementedError` because it is more
                efficient for the given backend to use the DC/OS advanced
                installation method that takes build artifacts by URL string.
        """
        try:
            self._cluster.install_dcos_from_path_with_bootstrap_node(
                build_artifact=build_artifact,
                dcos_config=dcos_config,
                ip_detect_path=ip_detect_path,
                files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
                log_output_live=log_output_live,
            )
        except NotImplementedError:
            for nodes, role in (
                (self.masters, Role.MASTER),
                (self.agents, Role.AGENT),
                (self.public_agents, Role.PUBLIC_AGENT),
            ):
                for node in nodes:
                    node.install_dcos_from_path(
                        build_artifact=build_artifact,
                        dcos_config=dcos_config,
                        ip_detect_path=ip_detect_path,
                        role=role,
                        files_to_copy_to_genconf_dir=(
                            files_to_copy_to_genconf_dir
                        ),
                        log_output_live=log_output_live,
                    )

    def run_integration_tests(
        self,
        pytest_command: List[str],
        env: Optional[Dict[str, Any]] = None,
        log_output_live: bool = False,
        tty: bool = False,
        test_host: Optional[Node] = None,
        transport: Optional[Transport] = None,
    ) -> subprocess.CompletedProcess:
        """
        Run integration tests on a random master node.

        Args:
            pytest_command: The ``pytest`` command to run on the node.
            env: Environment variables to be set on the node before running
                the `pytest_command`. On enterprise clusters,
                ``DCOS_LOGIN_UNAME`` and ``DCOS_LOGIN_PW`` must be set.
            log_output_live: If ``True``, log output of the ``pytest_command``
                live. If ``True``, ``stderr`` is merged into ``stdout`` in the
                return value.
            test_host: The node to run the given command on. if not given, an
                arbitrary master node is used.
            tty: If ``True``, allocate a pseudo-tty. This means that the users
                terminal is attached to the streams of the process.
                This means that the values of stdout and stderr will not be in
                the returned ``subprocess.CompletedProcess``.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.

        Returns:
            The result of the ``pytest`` command.

        Raises:
            subprocess.CalledProcessError: If the ``pytest`` command fails.
        """
        args = [
            'source',
            '/opt/mesosphere/environment.export',
            '&&',
            'cd',
            '/opt/mesosphere/active/dcos-integration-test/',
            '&&',
            *pytest_command,
        ]

        env = env or {}

        def ip_addresses(nodes: Iterable[Node]) -> str:
            return ','.join(
                map(lambda node: str(node.private_ip_address), nodes),
            )

        # Tests are run on a random master node if no node is given.
        test_host = test_host or next(iter(self.masters))

        environment_variables = {
            # This is needed for 1.9 (and below?)
            'PUBLIC_MASTER_HOSTS': ip_addresses(self.masters),
            'MASTER_HOSTS': ip_addresses(self.masters),
            'SLAVE_HOSTS': ip_addresses(self.agents),
            'PUBLIC_SLAVE_HOSTS': ip_addresses(self.public_agents),
            'DCOS_DNS_ADDRESS': 'http://' + str(test_host.private_ip_address),
            # This is only used by DC/OS 1.9 integration tests
            'DCOS_NUM_MASTERS': len(self.masters),
            'DCOS_NUM_AGENTS': len(self.agents) + len(self.public_agents),
            **env,
        }

        return test_host.run(
            args=args,
            log_output_live=log_output_live,
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

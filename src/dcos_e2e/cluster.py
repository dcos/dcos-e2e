"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
import warnings
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from dcos_test_utils.dcos_api import DcosApiSession, DcosUser
from dcos_test_utils.helpers import CI_CREDENTIALS, session_tempfile
from urllib3.exceptions import InsecureRequestWarning

# Ignore a spurious error - this import is used in a type hint.
from .backends import ClusterManager  # noqa: F401
from .backends import ClusterBackend, _ExistingCluster
from .node import Node


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
        files_to_copy_to_installer: Optional[Dict[Path, Path]] = None,
    ) -> None:
        """
        Create a DC/OS cluster.

        Args:
            cluster_backend: The backend to use for the cluster.
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        self._default_ssh_user = cluster_backend.default_ssh_user
        self._cluster = cluster_backend.cluster_cls(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            files_to_copy_to_installer=dict(files_to_copy_to_installer or {}),
            cluster_backend=cluster_backend,
        )  # type: ClusterManager

    @classmethod
    def from_nodes(
        cls,
        masters: Set[Node],
        agents: Set[Node],
        public_agents: Set[Node],
        default_ssh_user: str,
    ) -> 'Cluster':
        """
        Create a cluster from existing nodes.

        Args:
            masters: The master nodes in an existing cluster.
            agents: The agent nodes in an existing cluster.
            public_agents: The public agent nodes in an existing cluster.
            default_ssh_user: The SSH user name which can be connected to with
                the SSH keys associated with all nodes.

        Returns:
            A cluster object with the nodes of an existing cluster.
        """
        backend = _ExistingCluster(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            default_ssh_user=default_ssh_user,
        )

        return cls(
            masters=len(masters),
            agents=len(agents),
            public_agents=len(public_agents),
            files_to_copy_to_installer=None,
            cluster_backend=backend,
        )

    def wait_for_dcos_oss(self) -> None:
        """
        Wait until the DC/OS OSS boot process has completed.

        Raises:
            RetryError: Raised if any cluster component did not become
                healthy in time.
        """
        any_master = next(iter(self.masters))

        api_session = DcosApiSession(
            dcos_url='http://{ip}'.format(ip=any_master.ip_address),
            masters=[str(n.ip_address) for n in self.masters],
            slaves=[str(n.ip_address) for n in self.agents],
            public_slaves=[str(n.ip_address) for n in self.public_agents],
            auth_user=DcosUser(credentials=CI_CREDENTIALS),
        )

        api_session.wait_for_dcos()

    def wait_for_dcos_ee(
        self,
        superuser_username: str,
        superuser_password: str,
    ) -> None:
        """
        Wait until the DC/OS Enterprise boot process has completed.

        Args:
            superuser_username: Username of the default superuser.
            superuser_password: Password of the default superuser.

        Raises:
            RetryError: Raised if any cluster component did not become
                healthy in time.
        """

        credentials = {
            'uid': superuser_username,
            'password': superuser_password,
        }

        any_master = next(iter(self.masters))

        api_session = DcosApiSession(
            dcos_url='https://{ip}'.format(ip=any_master.ip_address),
            masters=[str(n.ip_address) for n in self.masters],
            slaves=[str(n.ip_address) for n in self.agents],
            public_slaves=[str(n.ip_address) for n in self.public_agents],
            auth_user=DcosUser(credentials=credentials),
        )

        warnings.simplefilter('ignore', InsecureRequestWarning)

        ca_cert = api_session.get(
            # We wait up to 10 minutes which is arbitrary but has worked
            # in testing at the time of writing.
            '/ca/dcos-ca.crt',
            retry_timeout=60 * 10,
            verify=False
        )
        ca_cert.raise_for_status()
        api_session.session.verify = session_tempfile(ca_cert.content)

        warnings.simplefilter('default', InsecureRequestWarning)

        api_session.wait_for_dcos()

    def __enter__(self) -> 'Cluster':
        """
        Enter a context manager.
        The context manager receives this ``Cluster`` instance.
        """
        return self

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master ``Node``s.
        """
        return self._cluster.masters

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """
        return self._cluster.agents

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public_agent ``Node``s.
        """
        return self._cluster.public_agents

    @property
    def default_ssh_user(self) -> str:
        """
        Return the default SSH user for accessing a node.
        """
        return self._default_ssh_user

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any] = None,
        log_output_live: bool = False,
    ) -> None:
        """
        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            extra_config: Implementations may come with a "base"
                configuration. This dictionary can contain extra installation
                configuration variables.
            log_output_live: If `True`, log output of the installation live.
                If `True`, stderr is merged into stdout in the return value.

        Raises:
            NotImplementedError: `NotImplementedError` because the given
                backend provides a more efficient installation method than
                the DC/OS advanced installation method.
        """
        self._cluster.install_dcos_from_url(
            build_artifact=build_artifact,
            extra_config=extra_config if extra_config else {},
            log_output_live=log_output_live,
        )

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        extra_config: Dict[str, Any] = None,
        log_output_live: bool = False,
    ) -> None:
        """
        Args:
            build_artifact: The `Path` to a build artifact to install DC/OS
                from.
            extra_config: Implementations may come with a "base"
                configuration. This dictionary can contain extra installation
                configuration variables.
            log_output_live: If `True`, log output of the installation live.
                If `True`, stderr is merged into stdout in the return value.

        Raises:
            NotImplementedError: `NotImplementedError` because it is more
                efficient for the given backend to use the DC/OS advanced
                installation method that takes build artifacts by URL string.
        """
        self._cluster.install_dcos_from_path(
            build_artifact=build_artifact,
            extra_config=extra_config if extra_config else {},
            log_output_live=log_output_live,
        )

    def run_integration_tests(
        self,
        pytest_command: List[str],
        env: Optional[Dict] = None,
        log_output_live: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Run integration tests on a random master node.

        Args:
            pytest_command: The ``pytest`` command to run on the node.
            env: Environment variables to be set on the node before running
                the `pytest_command`. On enterprise
                clusters, `DCOS_LOGIN_UNAME` and `DCOS_LOGIN_PW` must be set.
            log_output_live: If `True`, log output of the `pytest_command`
                live. If `True`, stderr is merged into stdout in the return
                value.

        Returns:
            The result of the ``pytest`` command.

        Raises:
            ``subprocess.CalledProcessError`` if the ``pytest`` command fails.
        """

        args = [
            'source',
            '/opt/mesosphere/environment.export',
            '&&',
            'cd',
            '/opt/mesosphere/active/dcos-integration-test/',
            '&&',
        ]

        env = env or {}

        def ip_addresses(nodes: Iterable[Node]) -> str:
            return ','.join(map(lambda node: str(node.ip_address), nodes))

        environment_variables = {
            'MASTER_HOSTS': ip_addresses(self.masters),
            'SLAVE_HOSTS': ip_addresses(self.agents),
            'PUBLIC_SLAVE_HOSTS': ip_addresses(self.public_agents),
            **env,
        }

        args += pytest_command

        # Tests are run on a random master node.
        test_host = next(iter(self.masters))

        return test_host.run(
            args=args,
            user=self.default_ssh_user,
            log_output_live=log_output_live,
            env=environment_variables,
        )

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        self._cluster.destroy()

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

"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from time import sleep
from threading import Thread
from typing import Any, Dict, Iterable, List, Optional, Set

import requests
from requests import codes
from retry import retry

# Ignore a spurious error - this import is used in a type hint.
from .backends import ClusterManager  # noqa: F401
from .backends import ClusterBackend
from .node import Node
from dcos_test_utils.enterprise import EnterpriseApiSession, EnterpriseUser


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



    # @retry(
    #     exceptions=(
    #         subprocess.CalledProcessError,
    #         ValueError,
    #         requests.exceptions.ConnectionError,
    #     ),
    #     tries=500,
    #     delay=5,
    # )

    def wait_for_diagnostics(self, log_output_live: bool = False) -> None:
        """
        Determine the point in time where all systemd units are running.
        """
        # Ping Marathon UI for 200
        diagnostics_args = [
            '/opt/mesosphere/bin/dcos-diagnostics',
            '--diag',
            '||',
            '/opt/mesosphere/bin/3dt',
            '--diag',
        ]

        for node in self.masters:
            node.run(
                args=diagnostics_args,
                # Keep in mind this must be run as privileged user.
                user=self.default_ssh_user,
                log_output_live=log_output_live,
                env={
                    'LC_ALL': 'en_US.UTF-8',
                    'LANG': 'en_US.UTF-8',
                },
            )

    def wait_for_zookeeper(self, log_output_live: bool = False) -> None:
        """
        Await the launch of Zookeeper.
        """
        # 1. Wait for ZK up
        # check GET :8181 STATUS 200

        # 2. Wait for ZK ensemble
        # check GET :8181/exhibitor/v1/cluster/state json['leader'] == 'true'
        pass

    def wait_for_mesos(self, log_output_live: bool = False) -> None:
        """
        Enable Mesos framework registration through HTTP.
        """
        # Wait until Mesos is up on all master nodes.
        for master in self.masters:
            _dcos_wait.mesos_up(master)

        # Wait for Mesos consensus.
        _dcos_wait.mesos_consensus(self.masters)

        any_master = next(iter(self.masters))

        # Wait for MesosDNS Mesos leader update on any Mesos master.
        _dcos_wait.dns_mesos_leader(any_master, self.default_ssh_user)

        # Wait until Mesos serves HTTP on the leader (we use all masters)
        for master in self.masters:
            _dcos_wait.mesos_http_serving(master)

        # Wait 25 seconds for Adminrouter cache expiration + refresh.
        sleep(25 + 5)

    def wait_for_marathon(self, log_output_live: bool = False) -> None:
        """
        Enable Marathon application deployment through HTTP.
        """
        # 1. Wait until Marathon is up on all master nodes.
        for master in self.masters:
            _dcos_wait.marathon_up(master)

        # 2. Wait for Marathon consensus.
        _dcos_wait.marathon_consensus(self.masters)

        any_master = next(iter(self.masters))

        # 3. Wait for MesosDNS Mesos leader update on any Marathon master.
        _dcos_wait.dns_marathon_leader(any_master, self.default_ssh_user)

        # Wait until Marathon serves HTTP on the leader (we use all masters)
        for master in self.masters:
            _dcos_wait.marathon_http_serving(master)

        # Wait 25 seconds for Adminrouter cache expiration + refresh.
        sleep(25 + 5)

    @retry(
        exceptions=(
            subprocess.CalledProcessError,
            ValueError,
            requests.exceptions.ConnectionError,
        ),
        tries=500,
        delay=5,
    )
    def wait_for_cli(self, log_output_live: bool = False) -> None:

        # 1. Wait for IAM up
        # check GET :8101 STATUS 200

        # 2. Wait for Adminrouter up
        # check GET / STATUS 200

        any_master = next(iter(self.masters))

        # 3. Download CA crt
        url = 'http://{ip_address}/ca/dcos-ca.crt'.format(
            ip_address=any_master.ip_address,
        )
        resp = requests.get(url, verify=False)
        if resp.status_code not in (codes.OK):  # noqa: E501 pragma: no cover pylint: disable=no-member
            message = 'Status code is: {status_code}'.format(
                status_code=resp.status_code,
            )
            raise ValueError(message)

    def wait_for_dcos(
        self,
        superuser_username,
        superuser_password,
        log_output_live: bool = False
    ) -> None:
        """
        Wait until DC/OS has started and all nodes have joined the cluster.

        Args:
            log_output_live: If `True`, log output of the diagnostics check
                live. If `True`, stderr is merged into stdout in the return
                value.

        Raises:
            RetryError: Raised if any cluster component did not become
            healthy in time.
        """
        any_master = next(iter(self.masters))

        # Hack, should work with DC/OS EE for the purpose of waiting
        auth_user = EnterpriseUser(superuser_username, superuser_password)

        session = EnterpriseApiSession(
            dcos_url='https://{ip}'.format(ip=any_master.ip_address),
            masters=[str(n.ip_address) for n in self.masters],
            agents=[str(n.ip_address) for n in self.agents],
            public_agents=[str(n.ip_address) for n in self.public_agents],
            auth_user=auth_user,
        )

        session.wait_for_dcos()

        # Wait 25 seconds for Adminrouter cache expiration + refresh.
        sleep(25 + 5)

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
        self.wait_for_dcos()

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
        try:
            self.destroy()
        except NotImplementedError:
            pass

        return False

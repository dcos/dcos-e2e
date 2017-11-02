"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from time import sleep
from typing import Any, Dict, Iterable, List, Optional, Set

import requests
from requests import codes
from retry import retry

# Ignore a spurious error - this import is used in a type hint.
from .backends import ClusterManager  # noqa: F401
from .backends import ClusterBackend
from .node import Node


class Cluster(ContextDecorator):
    """
    A record of a DC/OS cluster.

    This is intended to be used as context manager.
    """

    def __init__(
        self,
        cluster_backend: ClusterBackend,
        generate_config_path: Path = None,
        extra_config: Optional[Dict[str, Any]] = None,
        masters: int = 1,
        agents: int = 1,
        public_agents: int = 1,
        log_output_live: bool = False,
        destroy_on_error: bool = True,
        destroy_on_success: bool = True,
        files_to_copy_to_installer: Optional[Dict[Path, Path]] = None,
    ) -> None:
        """
        Create a DC/OS cluster.

        Args:
            cluster_backend: The backend to use for the cluster.
            generate_config_path: The path to a build artifact to install.
            extra_config: This dictionary can contain extra installation
                configuration variables to add to base configurations.
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            log_output_live: If `True`, log output of subprocesses live.
                If `True`, stderr is merged into stdout in the return value.
            destroy_on_error: If `False`, the cluster will not be destroyed
                if there is an exception raised in the context of this object.
            destroy_on_success: If `False`, the cluster will not be destroyed
                if there is no exception raised in the context of this object.
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.

        Raises:
            ValueError: `destroy_on_error` or `destroy_on_success` is `True`
                and the `cluster_backend` does not support being destroyed.
        """
        if destroy_on_error and not cluster_backend.supports_destruction:
            message = (
                'The given cluster backend does not support being destroyed.'
                ' Therefore, `destroy_on_error` must be set to `False`.'
            )
            raise ValueError(message)

        if destroy_on_success and not cluster_backend.supports_destruction:
            message = (
                'The given cluster backend does not support being destroyed.'
                ' Therefore, `destroy_on_success` must be set to `False`.'
            )
            raise ValueError(message)

        self._destroy_on_error = destroy_on_error
        self._destroy_on_success = destroy_on_success
        self._log_output_live = log_output_live
        extra_config = dict(extra_config or {})

        self._cluster = cluster_backend.cluster_cls(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=extra_config,
            log_output_live=self._log_output_live,
            files_to_copy_to_installer=dict(files_to_copy_to_installer or {}),
            cluster_backend=cluster_backend,
            generate_config_path=generate_config_path,
        )  # type: ClusterManager

    @retry(
        exceptions=(
            subprocess.CalledProcessError,
            ValueError,
            requests.exceptions.ConnectionError,
        ),
        tries=500,
        delay=5,
    )
    def wait_for_dcos(self) -> None:
        """
        Wait until DC/OS has started and all nodes have joined the cluster.
        """
        diagnostics_args = [
            '/opt/mesosphere/bin/dcos-diagnostics',
            '--diag',
            '||',
            '/opt/mesosphere/bin/3dt',
            '--diag',
        ]

        for node in self.masters:
            node.run_as_root(
                args=diagnostics_args,
                log_output_live=self._log_output_live,
                env={
                    'LC_ALL': 'en_US.UTF-8',
                    'LANG': 'en_US.UTF-8',
                },
            )

            url = 'http://{ip_address}/ca/dcos-ca.crt'.format(
                ip_address=node.ip_address,
            )
            resp = requests.get(url, verify=False)
            if resp.status_code not in (codes.OK, codes.NOT_FOUND):  # noqa: E501 pragma: no cover pylint: disable=no-member
                message = 'Status code is: {status_code}'.format(
                    status_code=resp.status_code,
                )
                raise ValueError(message)

        # Ideally we would use diagnostics checks as per
        # https://jira.mesosphere.com/browse/DCOS_OSS-1276
        # and these would wait long enough.
        #
        # However, until then, there is a race condition with the cluster.
        # This is not always caught by the tests.
        #
        # For now we sleep for 5 minutes as this has been shown to be enough.
        sleep(60 * 5)

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

    def run_integration_tests(
        self,
        pytest_command: List[str],
        env: Optional[Dict] = None,
    ) -> subprocess.CompletedProcess:
        """
        Run integration tests on a random master node.

        Args:
            pytest_command: The ``pytest`` command to run on the node.
            env: Environment variables to be set on the node before running
                the `pytest_command`. On enterprise
                clusters, `DCOS_LOGIN_UNAME` and `DCOS_LOGIN_PW` must be set.

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

        return test_host.run_as_root(
            args=args,
            log_output_live=self._log_output_live,
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
        On exiting, destroy all nodes in the cluster.
        """
        if exc_type is None and self._destroy_on_success:
            self.destroy()

        if exc_type is not None and self._destroy_on_error:
            self.destroy()

        return False

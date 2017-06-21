"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from requests import codes
from retry import retry

from ._common import Node
# Ignore a spurious error - this import is used in a type hint.
from .backends import ClusterManager  # noqa: F401
from .backends import ClusterBackend


class Cluster(ContextDecorator):
    """
    A record of a DC/OS cluster.

    This is intended to be used as context manager.
    """

    def __init__(
        self,
        cluster_backend: ClusterBackend,
        generate_config_path: Path,
        extra_config: Optional[Dict[str, Any]]=None,
        masters: int=1,
        agents: int=1,
        public_agents: int=1,
        log_output_live: bool=False,
        destroy_on_error: bool=True,
        files_to_copy_to_installer: Optional[Dict[Path, Path]]=None,
        files_to_copy_to_masters: Optional[Dict[Path, Path]]=None,
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
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            files_to_copy_to_masters: A mapping of host paths to paths on the
                master nodes. These are files to copy from the host to
                the master nodes before installing DC/OS.

        Raises:
            ValueError: There is no file at `generate_config_path`.
        """
        if not generate_config_path.exists():
            raise ValueError()

        self._destroy_on_error = destroy_on_error
        self._log_output_live = log_output_live
        extra_config = dict(extra_config or {})

        self._cluster = cluster_backend.cluster_cls(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=extra_config,
            log_output_live=self._log_output_live,
            files_to_copy_to_installer=dict(files_to_copy_to_installer or {}),
            files_to_copy_to_masters=dict(files_to_copy_to_masters or {}),
            cluster_backend=cluster_backend,
            generate_config_path=generate_config_path,
        )  # type: ClusterManager

    @retry(
        exceptions=(
            subprocess.CalledProcessError, ValueError,
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
            '3dt',
            'check',
            'node-poststart',
            '&&',
            '3dt',
            'check',
            'cluster',
        ]

        for node in self.masters:
            node.run_as_root(
                args=diagnostics_args,
                log_output_live=self._log_output_live,
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
        env: Optional[Dict]=None,
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

        args += pytest_command

        # Tests are run on a random master node.
        test_host = next(iter(self.masters))

        return test_host.run_as_root(
            args=args,
            log_output_live=self._log_output_live,
            env=env,
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
        if exc_type is None or self._destroy_on_error:
            self.destroy()
        return False

"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from retry import retry

from ._common import Node
from .backends import ClusterBackend


class _ClusterNotReady(Exception):
    """
    Raised when a cluster is not ready.
    """


class Cluster(ContextDecorator):
    """
    A record of a DC/OS cluster.

    This is intended to be used as context manager.
    """

    def __init__(
        self,
        cluster_backend: ClusterBackend,
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
        """
        self._destroy_on_error = destroy_on_error
        self._log_output_live = log_output_live

        self._superuser_username = 'admin'
        self._superuser_password = 'admin'

        self._cluster = cluster_backend.cluster_cls(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=dict(extra_config or {}),
            log_output_live=self._log_output_live,
            files_to_copy_to_installer=dict(files_to_copy_to_installer or {}),
            files_to_copy_to_masters=dict(files_to_copy_to_masters or {}),
            cluster_backend=cluster_backend,
            superuser_username=self._superuser_username,
            superuser_password=self._superuser_password,
        )

    @retry(
        exceptions=(_ClusterNotReady),
        delay=10,
        tries=60,
    )
    def wait(self) -> None:
        """
        Wait for the cluster to be ready.
        """
        pytest_command = ['pytest', 'test_no_such_file.py']
        environment_variables = {
            'DCOS_LOGIN_UNAME': self._superuser_username,
            'DCOS_LOGIN_PW': self._superuser_password,
            'DCOS_NUM_AGENTS': len(self.agents) + len(self.public_agents),
            'DCOS_NUM_MASTERS': len(self.masters),
            'DCOS_PYTEST_CMD': ' '.join(pytest_command),
        }

        args = []
        for key, value in environment_variables.items():
            export = "export {key}='{value}'".format(key=key, value=value)
            args.append(export)
            args.append('&&')

        args += [
            '/bin/bash',
            '/opt/mesosphere/active/dcos-integration-test/util/run_integration_test.sh',  # noqa E501
        ]
        # Tests are run on a random master node.
        test_host = next(iter(self.masters))

        try:
            test_host.run_as_root(
                args=args,
                log_output_live=self._log_output_live,
            )
        except subprocess.CalledProcessError as exc:
            # The command results in an exit code of 127 if the test file is
            # not available.
            if exc.returncode == 127:
                raise _ClusterNotReady()
            raise

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
    ) -> subprocess.CompletedProcess:
        """
        Run integration tests on a random master node.

        Args:
            pytest_command: The ``pytest`` command to run on the node.

        Returns:
            The result of the ``pytest`` command.

        Raises:
            ``subprocess.CalledProcessError`` if the ``pytest`` command fails.
        """
        self.wait()
        environment_variables = {
            'DCOS_LOGIN_UNAME': self._superuser_username,
            'DCOS_LOGIN_PW': self._superuser_password,
        }

        args = []

        for key, value in environment_variables.items():
            export = "export {key}='{value}'".format(key=key, value=value)
            args.append(export)
            args.append('&&')

        args += [
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
            args=args, log_output_live=self._log_output_live
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

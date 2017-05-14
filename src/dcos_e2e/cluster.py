"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ._common import Node
from ._dcos_docker import DCOS_Docker


class Cluster(ContextDecorator):
    """
    A record of a DC/OS Cluster.

    This is intended to be used as context manager.
    """

    def __init__(
        self,
        extra_config: Optional[Dict[str, Any]]=None,
        masters: int=1,
        agents: int=1,
        public_agents: int=1,
        log_output_live: bool=False,
    ) -> None:
        """
        Args:
            extra_config: This dictionary can contain extra installation
                configuration variables to add to base configurations.
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            log_output_live: If `True`, log output of subprocesses live.
                If `True`, stderr is merged into stdout in the return value.
        """
        self._backend = DCOS_Docker(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=dict(extra_config or {}),
            generate_config_path=Path('/tmp/dcos_generate_config.sh'),
            dcos_docker_path=Path('/tmp/dcos-docker'),
            log_output_live=log_output_live,
        )
        self._backend.postflight()

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
        return self._backend.masters

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """
        return self._backend.agents

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public_agent ``Node``s.
        """
        return self._backend.public_agents

    def run_integration_tests(self, pytest_command: List[str]
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
        agent_hosts = [str(node.ip_address) for node in self.agents]
        public_agent_hosts = [
            str(node.ip_address) for node in self.public_agents
        ]

        environment_variables = {
            # Used by `run_integration_tests.sh`.
            'DCOS_PYTEST_CMD': ' '.join(pytest_command),
            'DCOS_NUM_MASTERS': len(self.masters),
            'DCOS_NUM_AGENTS': len(self.public_agents) + len(self.agents),
            # `run_integration_tests.sh` does not provide all necessary
            # environment variables.
            # See https://jira.mesosphere.com/browse/DCOS-15759.
            'DCOS_LOGIN_UNAME': 'admin',
            'DCOS_LOGIN_PW': 'admin',
            'TEST_DCOS_RESILIENCY': 'admin',
            'SLAVE_HOSTS': ','.join(agent_hosts),
            'PUBLIC_SLAVE_HOSTS': ','.join(public_agent_hosts),
        }

        set_env_variables = [
            "{key}='{value}'".format(key=key, value=value)
            for key, value in environment_variables.items()
        ]

        test_dir = '/opt/mesosphere/active/dcos-integration-test/util'
        change_to_test_dir = ['cd', test_dir]

        and_cmd = ['&&']

        # We exit at the first failure in the script, else the return code
        # would be the return code of the commands after the `pytest` run.
        run_test_script = ['/bin/bash', '-e', './run_integration_test.sh']

        args = (
            change_to_test_dir + and_cmd + set_env_variables + run_test_script
        )

        # Tests are run on a random master node.
        test_host = next(iter(self.masters))

        return test_host.run_as_root(args=args)

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Any,
    ) -> bool:
        """
        On exiting, destroy all nodes in the cluster.
        """
        if exc_type is not None:
            self._backend.destroy()
        return False

"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ._common import Node
from ._dcos_docker import DCOS_Docker


class Cluster(ContextDecorator):
    """
    A record of a DC/OS Cluster.

    This is intended to be used as context manager.
    """

    def __init__(
        self,
        extra_config: Optional[Dict[str, str]]=None,
        masters: int=1,
        agents: int=1,
        public_agents: int=1,
    ) -> None:
        """
        Args:
            extra_config: This can contain extra installation
                configuration variables to add to base configurations.
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
        """
        if extra_config is None:
            extra_config = {}

        self._backend = DCOS_Docker(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=extra_config,
            generate_config_path=Path('/tmp/dcos_generate_config.sh'),
            dcos_docker_path=Path('/tmp/dcos-docker'),
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
        X
        """
        # Tests are run on a random master node
        test_host = next(iter(self.masters))

        environment_variables = {
            'DCOS_PYTEST_CMD': ' '.join(pytest_command),
            'DCOS_NUM_MASTERS': len(self.masters),
            'DCOS_NUM_AGENTS': len(self.public_agents) + len(self.agents),
            # `run_integration_tests.sh` does not provide all necessary
            # environment variables.
            'DCOS_LOGIN_UNAME': 'admin',
        }

        set_env_variables = [
            "{key}='{value}'".format(key=key, value=value)
            for key, value in environment_variables.items()
        ]

        and_cmd = ['&&']
        test_dir = '/opt/mesosphere/active/dcos-integration-test/util'
        change_to_test_dir = ['cd', test_dir]
        run_test_script = ['/bin/bash'] + ['./run_integration_test.sh']
        args = (
            change_to_test_dir + and_cmd + set_env_variables + run_test_script
        )

        try:
            return test_host.run_as_root(args=args)
        except subprocess.CalledProcessError as exc:
            # print(repr(exc.stdout))
            # print(repr(exc.stderr))
            import pdb
            pdb.set_trace()
            raise

    def __exit__(self, *exc: Tuple[None, None, None]) -> bool:
        """
        On exiting, destroy all nodes in the cluster.
        """
        self._backend.destroy()
        return False

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
        agents: int=0,
        public_agents: int=0,
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

        # dcos_dns_address = 'http://{ip_address}'.format(
        #     ip_address=test_host._ip_address
        # )
        # master_hosts = ','.join([node._ip_address for node in self.masters])
        # slave_hosts = ','.join([node._ip_address for node in self.agents])
        # public_slave_hosts = ','.join(
        #     [node._ip_address for node in self.public_agents]
        # )
        #
        # environment_variables = {
        #     'DCOS_DNS_ADDRESS': dcos_dns_address,
        #     'MASTER_HOSTS': master_hosts,
        #     'PUBLIC_MASTER_HOSTS': master_hosts,
        #     'SLAVE_HOSTS': slave_hosts,
        #     'PUBLIC_SLAVE_HOSTS': public_slave_hosts,
        #     'DCOS_PROVIDER': 'onprem',
        #     'DNS_SEARCH': 'false',
        #     'DCOS_LOGIN_PW': 'admin',
        #     'PYTHONUNBUFFERED': 'true',
        #     'PYTHONDONTWRITEBYTECODE': 'true',
        #     'DCOS_LOGIN_UNAME': 'admin',
        #     'TEST_DCOS_RESILIENCY': 'false',
        # }
        environment_variables = {
            'DCOS_PYTEST'
        }

        variable_settings = [
            '{key}={value}'.format(key=key, value=value)
            for key, value in environment_variables.items()
        ]

        # TODO use /util run_integration_test helper
        # pytest_command = variable_settings + pytest_command
        #
        # test_dir = '/opt/mesosphere/active/dcos-integration-test/'
        # change_to_test_dir = ['cd', test_dir]
        # source_environment = ['source', '/opt/mesosphere/environment.export']
        and_cmd = ['&&']
        #
        # args = (
        #     change_to_test_dir + and_cmd + source_environment + and_cmd +
        #     pytest_command
        # )
        test_dir = '/opt/mesosphere/active/dcos-integration-test/util'
        change_to_test_dir = ['cd', test_dir]
        run_test_script = ['/bin/bash'] + variable_settings + ['./run_integration_test.sh']
        args = (change_to_test_dir + and_cmd + run_test_script)

        try:
            return test_host.run_as_root(args=args)
        except subprocess.CalledProcessError as exc:
            print(repr(exc.stdout))
            print(repr(exc.stderr))
            raise

    def __exit__(self, *exc: Tuple[None, None, None]) -> bool:
        """
        On exiting, destroy all nodes in the cluster.
        """
        self._backend.destroy()
        return False

"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from dcos_test_utils.dcos_api_session import DcosApiSession, DcosUser
from dcos_test_utils.helpers import CI_CREDENTIALS

from ._common import Node
from .backends import ClusterBackend


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

    def wait_for_dcos(self) -> None:
        """
        Wait until the cluster is ready and all nodes have joined.

        Temporarily, this is a sleep which waits longer than DC/OS Docker has
        shown to require.

        See https://github.com/dcos/dcos/pull/1609/files for a probably more
        suitable approach.
        """
        web_host = next(iter(self.masters))
        masters_ip_addresses = [
            str(master.ip_address) for master in self.masters
        ]
        agents_ip_addresses = [str(agent.ip_address) for agent in self.agents]
        public_agent_ip_addresses = [
            str(public_agent.ip_address) for public_agent in self.public_agents
        ]

        dcos_url = 'http://' + str(web_host.ip_address)
        auth_user = DcosUser(credentials=CI_CREDENTIALS)
        api_session = DcosApiSession(
            dcos_url=dcos_url,
            masters=masters_ip_addresses,
            slaves=agents_ip_addresses,
            public_slaves=public_agent_ip_addresses,
            default_os_user=self._superuser_username,
            auth_user=auth_user,
        )
        # Without the following line, if we use a CA certificate, e.g. in a
        # permissive or strict security mode, requests made by `wait_for_dcos`
        # will fail.
        #
        # A proper fix would be to download and use the root CA certificate.
        # See: https://github.com/mesosphere/dcos-enterprise/blob/master/packages/dcos-integration-test/extra/api_session_fixture.py#L54-L91  # noqa: E501
        api_session.session.verify = False
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
        self.wait_for_dcos()
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

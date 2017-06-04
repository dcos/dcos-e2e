"""
DC/OS Cluster management tools. Independent of back ends.
"""

import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from time import sleep
from typing import Any, Dict, List, Optional, Set

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

        self._cluster = cluster_backend.cluster_cls(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=dict(extra_config or {}),
            log_output_live=self._log_output_live,
            files_to_copy_to_installer=dict(files_to_copy_to_installer or {}),
            files_to_copy_to_masters=dict(files_to_copy_to_masters or {}),
            cluster_backend=cluster_backend,
        )

        self._wait()

    def _wait(self) -> None:
        """
        XXX
        """
        master = next(iter(self.masters))
        # TODO Maybe you need to just check with requests from the host?
        poll_web_server_args = [
            'curl',
            '--insecure',
            '--fail',
            '--location',
            '--silent',
            'http://127.0.0.1/',
        ]
        while True:
            try:
                master.run_as_root(args=poll_web_server_args)
                break
            except subprocess.CalledProcessError:
                sleep(5)

        config_3dt_ls_args = [
            'ls',
            '/opt/mesosphere/packages/3dt*/endpoints_config.json',
        ]

        while True:
            try:
                ls_output = master.run_as_root(args=config_3dt_ls_args)
                break
            except subprocess.CalledProcessError:
                sleep(5)

        config_files = ls_output.stdout.split('\n')
        for config_file in config_files:
            component_status_args = [
                '/opt/mesosphere/bin/3dt',
                '-diag',
                '-endpoint-config={config_file}'.format(
                    config_file=config_file,
                ),
            ]
            while True:
                try:
                    master.run_as_root(args=component_status_args)
                    break
                except subprocess.CalledProcessError:
                    sleep(5)

        # Wait for nodes to join cluster
        agents_joined_cluster_args = ['dig', 'slave.mesos', '+short']
        while True:
            dig_resp = master.run_as_root(args=agents_joined_cluster_args)
            num_agents = len(dig_resp.stdout.split('\n'))
            if num_agents > len(self.agents) + len(self.public_agents):
                raise Exception()
            if num_agents == len(self.agents) + len(self.public_agents):
                break

        masters_joined_cluster_args = ['dig', 'master.mesos', '+short']
        while True:
            dig_resp = master.run_as_root(args=masters_joined_cluster_args)
            num_masters = len(dig_resp.stdout.split('\n'))
            if num_masters > len(self.masters):
                raise Exception()
            if num_agents == len(self.masters):
                break

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
        environment_variables = {
            'DCOS_LOGIN_UNAME': self._cluster.superuser_username,
            'DCOS_LOGIN_PW': self._cluster.superuser_password,
        }

        exports = [
            "export {key}='{value}'".format(key=key, value=value)
            for key, value in environment_variables.items()
        ]

        set_env_variables = []
        for export in exports:
            set_env_variables.append(export)
            set_env_variables.append('&&')

        set_env_variables += ['source', '/opt/mesosphere/environment.export']

        test_dir = '/opt/mesosphere/active/dcos-integration-test/'
        change_to_test_dir = ['cd', test_dir]
        and_cmd = ['&&']
        args = (
            change_to_test_dir + and_cmd + set_env_variables + and_cmd +
            pytest_command
        )

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

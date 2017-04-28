import subprocess
from contextlib import ContextDecorator
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml
from _dcos_docker import DCOS_Docker


class _Node:
    """
    A record of a DC/OS cluster node.
    """

    def __init__(self, ip_address: str, ssh_key_path: Path) -> None:
        """
        Args:
            ip_address: The IP address of the node.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the `root` user.
        """
        self._ip_address = ip_address
        self._ssh_key_path = ssh_key_path

    def run_as_root(self, args: List[str]) -> subprocess.CompletedProcess:
        """
        Run a command on this node as ``root``.

        Args:
            args: The command to run on the node.

        Returns:
            The representation of the finished process.

        Raises:
            CalledProcessError: The process exited with a non-zero code.
        """
        ssh_args = [
            'ssh',
            # Suppress warnings.
            # In particular, we don't care about remote host identification
            # changes.
            "-q",
            # The node may be an unknown host.
            "-o",
            "StrictHostKeyChecking=no",
            # Use an SSH key which is authorized.
            "-i",
            str(self._ssh_key_path),
            # Run commands as the root user.
            "-l",
            "root",
            # Bypass password checking.
            "-o",
            "PreferredAuthentications=publickey",
            self._ip_address,
        ] + args

        return subprocess.run(args=ssh_args, check=True)


class Cluster(ContextDecorator):
    """
    A record of a DC/OS Cluster.

    This is intended to be used as context manager.
    """

    def __init__(
        self,
        extra_config: Dict,
        masters: int=1,
        agents: int=0,
        public_agents: int=0,
    ) -> None:
        """
        Args:
            extra_config: This dictionary can contain extra installation
                configuration variables to add to base configurations.
            masters: The number of master nodes to create.
            agents: The number of master nodes to create.
            public_agents: The number of master nodes to create.
        """
        # See README.md for information on the required configuration.
        with open(str(Path.home() / '.dcos-e2e.yaml')) as configuration:
            tests_config = yaml.load(configuration)

        generate_config_path = Path(tests_config['dcos_generate_config_path'])
        self._backend = DCOS_Docker(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=extra_config,
            generate_config_path=generate_config_path,
            dcos_docker_path=Path(tests_config['dcos_docker_path']),
        )
        self._backend.postflight()

    def __enter__(self) -> 'Cluster':
        """
        A context manager receives this ``Cluster`` instance.
        """
        return self

    @property
    def masters(self) -> Set[_Node]:
        """
        Return all DC/OS master ``_Node``s.
        """
        return self._backend.masters

    def __exit__(self, *exc: Tuple[None, None, None]) -> bool:
        """
        On exiting, destroy all nodes in the cluster.
        """
        self._backend.destroy()
        return False

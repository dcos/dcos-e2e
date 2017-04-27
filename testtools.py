import subprocess
import uuid
from contextlib import ContextDecorator
from pathlib import Path
from shutil import copyfile, copytree, rmtree
from typing import Dict, List, Set, Tuple

import yaml
from docker import Client


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


class _DCOS_Docker:
    """
    A record of a DC/OS Docker cluster.
    """

    def __init__(
        self,
        masters: int,
        agents: int,
        public_agents: int,
        extra_config: Dict,
        generate_config_path: Path,
        dcos_docker_path: Path,
    ) -> None:
        """
        Create a DC/OS Docker cluster.

        Args:
            masters: The number of master nodes to create.
            agents: The number of master nodes to create.
            public_agents: The number of master nodes to create.
            extra_config: DC/OS Docker comes with a "base" configuration.
                This dictionary can contain extra installation configuration
                variables.
            generate_config_path: The path to a build artifact to install.
            dcos_docker_path: The path to a clone of DC/OS Docker.
        """
        # To avoid conflicts, we use random container names.
        # We use the same random string for each container in a cluster so
        # that they can be associated easily.
        random = uuid.uuid4()

        # We create a new instance of DC/OS Docker and we work in this
        # directory.
        # This reduces the chance of conflicts.
        # We put this in the `/tmp` directory because that is writeable on
        # the Vagrant VM.
        self._path = Path('/tmp') / 'dcos-docker-{random}'.format(
            random=random)
        copytree(src=str(dcos_docker_path), dst=str(self._path))

        copyfile(
            src=str(generate_config_path),
            dst=str(self._path / 'dcos_generate_config.sh'),
        )

        self._variables = {
            # Number of nodes.
            'MASTERS': str(masters),
            'AGENTS': str(agents),
            'PUBLIC_AGENTS': str(public_agents),
            # Container names.
            'MASTER_CTR': 'dcos-master-{random}-'.format(random=random),
            'AGENT_CTR': 'dcos-agent-{random}-'.format(random=random),
            'PUBLIC_AGENT_CTR': 'dcos-public-agent-{random}-'.format(
                random=random),
        }  # type: Dict[str, str]

        if extra_config:
            self._variables['EXTRA_GENCONF_CONFIG'] = yaml.dump(
                data=extra_config,
                default_flow_style=False,
            )

        self._wait_for_installers()
        self._make(target='all')

    # @retry()
    def _wait_for_installers(self) -> None:

        def genconf_container_running() -> bool:
            client = Client()
            for container in client.containers():
                image = container['Image']
                if image.startswith('mesosphere/dcos-genconf'):
                    return True
            return False

        while genconf_container_running():
            from time import sleep
            sleep(1)

    def _make(self, target: str) -> None:
        """
        Run `make` in the DC/OS Docker directory using variables associated
        with this instance.

        Args:
            target: `make` target to run.

        Raises:
            CalledProcessError: The process exited with a non-zero code.
        """
        args = ['make'] + [
            '{key}={value}'.format(key=key, value=value)
            for key, value in self._variables.items()
        ] + [target]

        subprocess.run(
            args=args,
            cwd=str(self._path),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def postflight(self) -> None:
        """
        Wait for nodes to be ready to run tests against.
        """
        self._make(target='postflight')

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        self._make(target='clean')
        rmtree(path=str(self._path))

    def _nodes(self, container_base_name: str, num_nodes: int) -> Set[_Node]:
        """
        Args:
            container_base_name: The start of the container names.
            num_nodes: The number of nodes.

        Returns: ``_Node``s corresponding to containers with names starting
            with ``container_base_name``.
        """
        client = Client()
        nodes = set([])  # type: Set[_Node]

        while len(nodes) < num_nodes:
            container_name = '{container_base_name}{number}'.format(
                container_base_name=container_base_name,
                number=len(nodes) + 1,
            )
            details = client.inspect_container(container=container_name)
            ip_address = details['NetworkSettings']['IPAddress']
            node = _Node(
                ip_address=ip_address,
                ssh_key_path=self._path / 'include' / 'ssh' / 'id_rsa',
            )
            nodes.add(node)

        return nodes

    @property
    def masters(self) -> Set[_Node]:
        """
        Return all DC/OS master ``_Node``s.
        """
        return self._nodes(
            container_base_name=self._variables['MASTER_CTR'],
            num_nodes=int(self._variables['MASTERS']),
        )


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
        with open('configuration.yaml') as configuration:
            tests_config = yaml.load(configuration)

        self._backend = _DCOS_Docker(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            extra_config=extra_config,
            generate_config_path=Path(
                tests_config['dcos_generate_config_path']),
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

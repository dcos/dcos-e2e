"""
Helpers for interacting with DC/OS Docker.
"""

import subprocess
import uuid
from pathlib import Path
from shutil import copy2, copyfile, copytree, rmtree
from typing import Dict, Optional, Set

import yaml

from docker import Client
from retry import retry

from ._common import Node


class _ConflictingContainerError(Exception):
    """
    Raised when an existing container conflicts with a container which will be
    created.
    """
    pass


class DCOS_Docker:
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
        custom_ca_key: Optional[Path],
        # Dir containing files which get added to genconf
        genconf_extra_dir: Optional[Path],
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
        tmp = Path('/tmp')
        self._path = tmp / 'dcos-docker-{random}'.format(random=random)
        copytree(
            src=str(dcos_docker_path),
            dst=str(self._path),
            symlinks=True,
        )

        if genconf_extra_dir is not None:
            for path in genconf_extra_dir.glob('*'):
                if path.is_dir():
                    copytree(src=str(path), dst=str(self._path / 'genconf'))
                else:
                    copy2(src=str(path), dst=str(self._path / 'genconf'))

        copyfile(
            src=str(generate_config_path),
            dst=str(self._path / 'dcos_generate_config.sh'),
        )

        master_ctr = 'dcos-master-{random}-'.format(random=random)
        agent_ctr = 'dcos-agent-{random}-'.format(random=random)
        public_agent_ctr = 'dcos-public-agent-{random}-'.format(random=random)
        self._variables = {
            # Number of nodes.
            'MASTERS': str(masters),
            'AGENTS': str(agents),
            'PUBLIC_AGENTS': str(public_agents),
            # Container names.
            'MASTER_CTR': master_ctr,
            'AGENT_CTR': agent_ctr,
            'PUBLIC_AGENT_CTR': public_agent_ctr,
        }  # type: Dict[str, str]

        if extra_config:
            self._variables['EXTRA_GENCONF_CONFIG'] = yaml.dump(
                data=extra_config,
                default_flow_style=False,
            )

        if custom_ca_key is not None:
            self._variables['CUSTOM_CA_KEY_PATH'] = str(custom_ca_key)

        self._create_containers()

    @retry(exceptions=_ConflictingContainerError, delay=10, tries=10)
    def _create_containers(self) -> None:
        """
        Create containers for the cluster.

        Creating clusters involves creating temporary installer containers.
        These containers can conflict in name.
        If a conflict occurs, retry.
        """
        conflict_error_substring = (
            'Conflict. The container name "/dcos-genconf.'
        )

        try:
            self._make(target='all')
        except subprocess.CalledProcessError as e:
            if conflict_error_substring in str(e.stderr):
                raise _ConflictingContainerError()
            raise

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
        rmtree(
            path=str(self._path),
            # Some files may be created in the container that we cannot clean
            # up.
            ignore_errors=True,
        )

    def _nodes(self, container_base_name: str, num_nodes: int) -> Set[Node]:
        """
        Args:
            container_base_name: The start of the container names.
            num_nodes: The number of nodes.

        Returns: ``Node``s corresponding to containers with names starting
            with ``container_base_name``.
        """
        client = Client()
        nodes = set([])  # type: Set[Node]

        while len(nodes) < num_nodes:
            container_name = '{container_base_name}{number}'.format(
                container_base_name=container_base_name,
                number=len(nodes) + 1,
            )
            details = client.inspect_container(container=container_name)
            ip_address = details['NetworkSettings']['IPAddress']
            node = Node(
                ip_address=ip_address,
                ssh_key_path=self._path / 'include' / 'ssh' / 'id_rsa',
            )
            nodes.add(node)

        return nodes

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master ``Node``s.
        """
        return self._nodes(
            container_base_name=self._variables['MASTER_CTR'],
            num_nodes=int(self._variables['MASTERS']),
        )

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """
        return self._nodes(
            container_base_name=self._variables['AGENT_CTR'],
            num_nodes=int(self._variables['AGENTS']),
        )

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent ``Node``s.
        """
        return self._nodes(
            container_base_name=self._variables['PUBLIC_AGENT_CTR'],
            num_nodes=int(self._variables['PUBLIC_AGENTS']),
        )

from contextlib import ContextDecorator
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import yaml

from ._common import Node
from ._dcos_docker import DCOS_Docker


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
        custom_ca_key: Optional[Path]=None,
        genconf_extra_dir: Optional[Path]=None,
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
            custom_ca_key=custom_ca_key,
            genconf_extra_dir=genconf_extra_dir,
        )
        self._backend.postflight()

    def __enter__(self) -> 'Cluster':
        """
        A context manager receives this ``Cluster`` instance.
        """
        return self

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master ``Node``s.
        """
        return self._backend.masters

    def __exit__(self, *exc: Tuple[None, None, None]) -> bool:
        """
        On exiting, destroy all nodes in the cluster.
        """
        self._backend.destroy()
        return False

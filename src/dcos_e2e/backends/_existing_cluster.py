"""
Helpers for interacting with existing clusters.
"""

from pathlib import Path
from typing import Any, Dict

from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager


class Existing_Cluster(ClusterBackend):
    """
    A record of an existing DC/OS cluster.
    """


class Existing_Cluster_Manager(ClusterManager):
    """
    A record of a DC/OS cluster.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        generate_config_path: Path,
        masters: int,
        agents: int,
        public_agents: int,
        extra_config: Dict[str, Any],
        log_output_live: bool,
        files_to_copy_to_installer: Dict[Path, Path],
        files_to_copy_to_masters: Dict[Path, Path],
        cluster_backend: Existing_Cluster,
    ) -> None:
        """
        XXX
        """
        self.masters = masters
        self.agents = agents
        self.public_agents = public_agents

        if not 1 == 2:
            pass

"""
Classes to allow backend-specific configuration for cluster backend types.
"""

from pathlib import Path
from ._dcos_docker import DCOS_Docker_Cluster


class DCOS_Docker_Configuration:  # pylint: disable=invalid-name
    """
    DC/OS Docker specific configuration.
    """

    def __init__(self) -> None:
        """
        Create a configuration for a DC/OS Docker cluster backend.

        Attributes:
            cluster_backend_cls: The class to use as a cluster backend.
            generate_config_path: The path to a build artifact to install.
            dcos_docker_path: The path to a clone of DC/OS Docker.
                This clone will be used to create the cluster.
            workspace_path: The directory to create large temporary files in.
                The files are cleaned up when the cluster is destroyed.
        """
        self.cluster_backend_cls = DCOS_Docker_Cluster
        # We put this files in the `/tmp` directory because that is writable on
        # the Vagrant VM.
        self.workspace_path = Path('/tmp')
        self.generate_config_path = Path('/tmp/dcos_generate_config.sh')
        self.dcos_docker_path = Path('/tmp/dcos-docker')

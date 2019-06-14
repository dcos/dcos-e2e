"""
Credentials used when making CLIs.
"""

from pathlib import Path

from dcos_e2e.cluster import Cluster

DEFAULT_SUPERUSER_USERNAME = 'bootstrapuser'
DEFAULT_SUPERUSER_PASSWORD = 'deleteme'


def add_authorized_key(cluster: Cluster, public_key_path: Path) -> None:
    """
    Add an authorized key to all nodes in the given cluster.
    """
    nodes = {
        *cluster.masters,
        *cluster.agents,
        *cluster.public_agents,
    }

    for node in nodes:
        node.run(
            args=['echo', '', '>>', '/root/.ssh/authorized_keys'],
            shell=True,
        )
        node.run(
            args=[
                'echo',
                public_key_path.read_text(),
                '>>',
                '/root/.ssh/authorized_keys',
            ],
            shell=True,
        )

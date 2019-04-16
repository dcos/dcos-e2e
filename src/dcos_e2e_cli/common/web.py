"""
Helpers for opening the Web UI of a cluster.
"""

import click

from dcos_e2e.cluster import Cluster


def launch_web_ui(cluster: Cluster) -> None:
    """
    Launch the web UI for a cluster.

    Args:
        cluster: The cluster to launch a web UI for.
    """
    master = next(iter(cluster.masters))
    web_ui = 'http://' + str(master.public_ip_address)
    click.launch(web_ui)

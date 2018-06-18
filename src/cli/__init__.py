"""
A CLI for controlling DC/OS clusters on Docker.
"""

import logging
from typing import Optional, Union

import click

from dcos_e2e.node import Transport

from ._common import ClusterContainers
from ._options import existing_cluster_id_option
from .commands.create import create
from .commands.destroy import destroy, destroy_list
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.list_clusters import list_clusters
from .commands.mac_network import destroy_mac_network, setup_mac_network
from .commands.run_command import run
from .commands.sync import sync_code
from .commands.wait import wait


def _set_logging(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> None:
    """
    Set logging level depending on the chosen verbosity.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    value = min(value, 3)
    value = max(value, 0)
    verbosity_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.NOTSET,
    }
    # Disable logging calls of the given severity level or below.
    logging.disable(verbosity_map[int(value or 0)])


@click.option(
    '-v',
    '--verbose',
    count=True,
    callback=_set_logging,
)
@click.group(name='dcos-docker')
@click.version_option()
def dcos_docker(verbose: None) -> None:
    """
    Manage DC/OS clusters on Docker.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (verbose, ):
        pass


@dcos_docker.command('web')
@existing_cluster_id_option
def web(cluster_id: str) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``dcos-docker wait`` before running this command.
    """
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        # The transport is not used so does not matter.
        transport=Transport.DOCKER_EXEC,
    )
    cluster = cluster_containers.cluster
    master = next(iter(cluster.masters))
    web_ui = 'http://' + str(master.public_ip_address)
    click.launch(web_ui)


dcos_docker.add_command(create)
dcos_docker.add_command(destroy)
dcos_docker.add_command(destroy_list)
dcos_docker.add_command(destroy_mac_network)
dcos_docker.add_command(doctor)
dcos_docker.add_command(inspect_cluster)
dcos_docker.add_command(list_clusters)
dcos_docker.add_command(run)
dcos_docker.add_command(setup_mac_network)
dcos_docker.add_command(sync_code)
dcos_docker.add_command(wait)

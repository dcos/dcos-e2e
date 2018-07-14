"""
A CLI for controlling DC/OS clusters on Docker.
"""

import logging
from typing import Optional, Union

import click

from cli.common.commands import list_clusters_command_factory

from .commands._common import existing_cluster_ids
from .commands.create import create
from .commands.destroy import destroy, destroy_list
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.mac_network import destroy_mac_network, setup_mac_network
from .commands.run_command import run
from .commands.sync import sync_code
from .commands.wait import wait
from .commands.web import web


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


LIST_CLUSTERS = list_clusters_command_factory(
    existing_cluster_ids_func=existing_cluster_ids,
)
dcos_docker.add_command(create)
dcos_docker.add_command(destroy)
dcos_docker.add_command(destroy_list)
dcos_docker.add_command(destroy_mac_network)
dcos_docker.add_command(doctor)
dcos_docker.add_command(inspect_cluster)
dcos_docker.add_command(LIST_CLUSTERS)
dcos_docker.add_command(run)
dcos_docker.add_command(setup_mac_network)
dcos_docker.add_command(sync_code)
dcos_docker.add_command(wait)
dcos_docker.add_command(web)

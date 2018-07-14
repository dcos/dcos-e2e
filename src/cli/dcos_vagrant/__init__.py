"""
A CLI for controlling DC/OS clusters on Vagrant.
"""

import logging
from typing import Optional, Union

import click

from cli.common.commands import list_clusters_command_factory

from .commands._common import existing_cluster_ids
from .commands.create import create
from .commands.destroy import destroy, destroy_list
from .commands.doctor import doctor


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
@click.group(name='dcos-vagrant')
@click.version_option()
def dcos_vagrant(verbose: None) -> None:
    """
    Manage DC/OS clusters on Vagrant.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (verbose, ):
        pass


LIST_CLUSTERS = list_clusters_command_factory(
    existing_cluster_ids_func=existing_cluster_ids,
)
dcos_vagrant.add_command(create)
dcos_vagrant.add_command(destroy)
dcos_vagrant.add_command(destroy_list)
dcos_vagrant.add_command(doctor)
dcos_vagrant.add_command(LIST_CLUSTERS)

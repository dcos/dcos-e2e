"""
Tools for inspecting existing clusters.
"""

import json
from typing import Any  # noqa: F401
from typing import Dict  # noqa: F401

import click

from dcos_e2e.node import Transport
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging
from dcos_e2e_cli.common.inspect_cluster import show_cluster_details

from ._common import ClusterContainers, existing_cluster_ids


@click.command('inspect')
@existing_cluster_id_option
@verbosity_option
def inspect_cluster(cluster_id: str, verbose: int) -> None:
    """
    Show cluster details.
    """
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        # The transport here is not relevant as we do not make calls to the
        # cluster.
        transport=Transport.DOCKER_EXEC,
    )

    show_cluster_details(
        cluster_id=cluster_id,
        cluster_representation=cluster_containers,
    )

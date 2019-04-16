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
from dcos_e2e_cli.common.variants import get_cluster_variant

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
    master = next(iter(cluster_containers.masters))
    web_ui = 'http://' + master.attrs['NetworkSettings']['IPAddress']

    keys = {
        'masters': cluster_containers.masters,
        'agents': cluster_containers.agents,
        'public_agents': cluster_containers.public_agents,
    }

    nodes = {
        key: [
            cluster_containers.to_dict(node_representation=container)
            for container in containers
        ]
        for key, containers in keys.items()
    }

    cluster = cluster_containers.cluster
    dcos_variant = get_cluster_variant(cluster=cluster)
    variant_name = str(dcos_variant if dcos_variant else None)

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
        'SSH Default User': cluster_containers.ssh_default_user,
        'SSH key': str(cluster_containers.ssh_key_path),
        'DC/OS Variant': variant_name,
    }  # type: Dict[str, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )

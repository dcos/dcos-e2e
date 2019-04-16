"""
Tools for inspecting existing clusters.
"""

import json
from typing import Any  # noqa: F401
from typing import Dict  # noqa: F401

import click

from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging
from dcos_e2e_cli.common.variants import get_cluster_variant

from ._common import ClusterInstances, existing_cluster_ids
from ._options import aws_region_option


@click.command('inspect')
@existing_cluster_id_option
@aws_region_option
@verbosity_option
def inspect_cluster(cluster_id: str, aws_region: str, verbose: int) -> None:
    """
    Show cluster details.
    """
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )
    keys = {
        'masters': cluster_instances.masters,
        'agents': cluster_instances.agents,
        'public_agents': cluster_instances.public_agents,
    }
    master = next(iter(cluster_instances.cluster.masters))
    web_ui = 'http://' + str(master.public_ip_address)
    nodes = {
        key: [
            cluster_instances.to_dict(node_representation=instance)
            for instance in instances
        ]
        for key, instances in keys.items()
    }

    cluster = cluster_instances.cluster
    dcos_variant = get_cluster_variant(cluster=cluster)
    variant_name = str(dcos_variant if dcos_variant else None)

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
        'SSH Default User': cluster_instances.ssh_default_user,
        'SSH key': str(cluster_instances.ssh_key_path),
        'DC/OS Variant': variant_name,
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )

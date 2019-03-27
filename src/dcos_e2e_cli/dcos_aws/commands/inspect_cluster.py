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

from ._common import (
    ClusterInstances,
    InstanceInspectView,
    existing_cluster_ids,
)
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
            InstanceInspectView(
                instance=instance,
                aws_region=aws_region,
            ).to_dict() for instance in instances
        ]
        for key, instances in keys.items()
    }

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
        'DC/OS Variant': cluster_instances.dcos_variant.name,
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )

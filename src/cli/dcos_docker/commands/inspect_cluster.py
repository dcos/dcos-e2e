"""
Tools for inspecting existing clusters.
"""

import json
from typing import Any, Dict  # noqa: F401

import click

from cli.common.options import existing_cluster_id_option, verbosity_option
from cli.common.utils import check_cluster_id_exists, set_logging
from dcos_e2e.node import Transport

from ._common import (
    ClusterContainers,
    ContainerInspectView,
    existing_cluster_ids,
)


@click.command('inspect')
@existing_cluster_id_option
@click.option(
    '--env',
    is_flag=True,
    help='Show details in an environment variable format to eval.',
)
@verbosity_option
def inspect_cluster(cluster_id: str, env: bool, verbose: int) -> None:
    """
    Show cluster details.

    To quickly get environment variables to use with Docker tooling, use the
    ``--env`` flag.

    Run ``eval $(dcos-docker inspect <CLUSTER_ID> --env)``, then run
    ``docker exec -it $MASTER_0`` to enter the first master, for example.
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
    ssh_key = cluster_containers.workspace_dir / 'ssh' / 'id_rsa'

    keys = {
        'masters': cluster_containers.masters,
        'agents': cluster_containers.agents,
        'public_agents': cluster_containers.public_agents,
    }

    if env:
        env_dict = {}
        for _, containers in keys.items():
            for container in containers:
                inspect_view = ContainerInspectView(container=container)
                inspect_data = inspect_view.to_dict()
                reference = inspect_data['e2e_reference'].upper()
                env_dict[reference] = container.id
                node_ip_key = reference + '_IP'
                node_ip = container.attrs['NetworkSettings']['IPAddress']
                env_dict[node_ip_key] = node_ip
        env_dict['WEB_UI'] = web_ui
        env_dict['SSH_KEY'] = ssh_key
        for key, value in env_dict.items():
            click.echo('export {key}={value}'.format(key=key, value=value))
        return

    nodes = {
        key: [
            ContainerInspectView(container).to_dict()
            for container in containers
        ]
        for key, containers in keys.items()
    }

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
        'SSH key': str(ssh_key),
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )

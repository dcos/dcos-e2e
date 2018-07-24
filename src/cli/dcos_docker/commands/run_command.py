"""
Tools for running arbitrary commands on cluster nodes.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

import click

from cli.common.arguments import node_args_argument
from cli.common.options import (
    dcos_login_pw_option,
    dcos_login_uname_option,
    environment_variables_option,
    existing_cluster_id_option,
    no_test_env_run_option,
    sync_dir_run_option,
)
from cli.common.run_command import run_command
from cli.common.sync import sync_code_to_masters
from cli.common.utils import check_cluster_id_exists
from dcos_e2e.node import Node, Transport

from ._common import (
    ClusterContainers,
    ContainerInspectView,
    existing_cluster_ids,
)
from ._options import node_transport_option


def _get_node(cluster_id: str, node_reference: str) -> Node:
    """
    Get a node from a "reference".

    Args:
        cluster_id: The ID of a cluster.
        node_reference: One of:
            * A node's IP address
            * A node's Docker container name
            * A node's Docker container ID
            * A reference in the format "<role>_<number>"

    Returns:
        The ``Node`` from the given cluster with the given ID.

    Raises:
        click.BadParameter: There is no such node.
    """
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=Transport.DOCKER_EXEC,
    )

    containers = {
        *cluster_containers.masters,
        *cluster_containers.agents,
        *cluster_containers.public_agents,
    }

    for container in containers:
        inspect_data = ContainerInspectView(container=container).to_dict()
        reference = inspect_data['e2e_reference']
        ip_address = inspect_data['ip_address']
        container_name = inspect_data['docker_container_name']
        container_id = inspect_data['docker_container_id']
        accepted = (
            reference,
            reference.upper(),
            ip_address,
            container_name,
            container_id,
        )

        if node_reference in accepted:
            return cluster_containers.to_node(container=container)

    message = (
        'No such node in cluster "{cluster_id}" with IP address, Docker '
        'container ID or node reference "{node_reference}". '
        'Node references can be seen with ``dcos_docker inspect``.'
    ).format(
        cluster_id=cluster_id,
        node_reference=node_reference,
    )
    raise click.BadParameter(message=message)


@click.command('run', context_settings=dict(ignore_unknown_options=True))
@existing_cluster_id_option
@node_args_argument
@dcos_login_uname_option
@dcos_login_pw_option
@sync_dir_run_option
@no_test_env_run_option
@click.option(
    '--node',
    type=str,
    default='master_0',
    help=(
        'A reference to a particular node to run the command on. '
        'This can be one of: '
        'The node\'s IP address, '
        'the node\'s Docker container name, '
        'the node\'s Docker container ID, '
        'a reference in the format "<role>_<number>". '
        'These details be seen with ``dcos-docker inspect``.'
    ),
)
@environment_variables_option
@node_transport_option
def run(
    cluster_id: str,
    node_args: Tuple[str],
    sync_dir: Optional[Path],
    dcos_login_uname: str,
    dcos_login_pw: str,
    no_test_env: bool,
    node: str,
    env: Dict[str, str],
    transport: Transport,
) -> None:
    """
    Run an arbitrary command on a node.

    This command sets up the environment so that ``pytest`` can be run.

    For example, run
    ``dcos-docker run --cluster-id 1231599 pytest -k test_tls.py``.

    Or, with sync:
    ``dcos-docker run --sync-dir . --cluster-id 1231599 pytest -k test_tls.py``.

    To use special characters such as single quotes in your command, wrap the
    whole command in double quotes.
    """  # noqa: E501
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    host = _get_node(cluster_id=cluster_id, node_reference=node)

    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster = cluster_containers.cluster

    if sync_dir is not None:
        sync_code_to_masters(
            cluster=cluster,
            dcos_checkout_dir=sync_dir,
        )

    run_command(
        args=list(node_args),
        cluster=cluster,
        host=host,
        use_test_env=not no_test_env,
        dcos_login_uname=dcos_login_uname,
        dcos_login_pw=dcos_login_pw,
        env=env,
        transport=transport,
    )

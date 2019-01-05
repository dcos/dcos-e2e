"""
Tools for running arbitrary commands on cluster nodes.
"""

from pathlib import Path
from typing import Dict, Tuple

import click

from dcos_e2e.node import Node, Transport
from dcos_e2e_cli.common.arguments import node_args_argument
from dcos_e2e_cli.common.options import (
    dcos_login_pw_option,
    dcos_login_uname_option,
    environment_variables_option,
    existing_cluster_id_option,
    sync_dir_run_option,
    test_env_run_option,
    verbosity_option,
)
from dcos_e2e_cli.common.run_command import run_command
from dcos_e2e_cli.common.sync import sync_code_to_masters
from dcos_e2e_cli.common.utils import check_cluster_id_exists, set_logging

from ._common import ClusterVMs, VMInspectView, existing_cluster_ids


def _get_node(cluster_id: str, node_reference: str) -> Node:
    """
    Get a node from a "reference".

    Args:
        cluster_id: The ID of a cluster.
        node_reference: One of:
            * A node's IP address
            * A node's VM name
            * A reference in the format "<role>_<number>"

    Returns:
        The ``Node`` from the given cluster with the given ID.

    Raises:
        click.BadParameter: There is no such node.
    """
    cluster_vms = ClusterVMs(cluster_id=cluster_id)

    vm_names = {
        *cluster_vms.masters,
        *cluster_vms.agents,
        *cluster_vms.public_agents,
    }

    for vm_name in vm_names:
        inspect_data = VMInspectView(vm_name=vm_name).to_dict()
        reference = inspect_data['e2e_reference']
        ip_address = inspect_data['ip_address']
        accepted = (
            reference,
            reference.upper(),
            ip_address,
            vm_name,
        )

        if node_reference in accepted:
            return cluster_vms.to_node(vm_name=vm_name)

    message = (
        'No such node in cluster "{cluster_id}" with IP address, VM name or '
        'node reference "{node_reference}". '
        'Node references can be seen with ``minidcos vagrant inspect``.'
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
@test_env_run_option
@environment_variables_option
@click.option(
    '--node',
    type=str,
    default='master_0',
    help=(
        'A reference to a particular node to run the command on. '
        'This can be one of: '
        'The node\'s IP address, '
        'the node\'s VM name, '
        'a reference in the format "<role>_<number>". '
        'These details be seen with ``minidcos vagrant inspect``.'
    ),
)
@verbosity_option
def run(
    cluster_id: str,
    node_args: Tuple[str],
    sync_dir: Tuple[Path],
    dcos_login_uname: str,
    dcos_login_pw: str,
    test_env: bool,
    node: str,
    env: Dict[str, str],
    verbose: int,
) -> None:
    """
    Run an arbitrary command on a node.

    To use special characters such as single quotes in your command, wrap the
    whole command in double quotes.
    """  # noqa: E501
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    host = _get_node(cluster_id=cluster_id, node_reference=node)
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    cluster = cluster_vms.cluster
    for dcos_checkout_dir in sync_dir:
        sync_code_to_masters(
            cluster=cluster,
            dcos_checkout_dir=dcos_checkout_dir,
            dcos_variant=cluster_vms.dcos_variant,
        )

    run_command(
        args=list(node_args),
        cluster=cluster,
        host=host,
        use_test_env=test_env,
        dcos_login_uname=dcos_login_uname,
        dcos_login_pw=dcos_login_pw,
        env=env,
        transport=Transport.SSH,
    )

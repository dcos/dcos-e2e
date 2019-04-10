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
from ._nodes import get_node, node_option


@click.command('run', context_settings=dict(ignore_unknown_options=True))
@existing_cluster_id_option
@node_args_argument
@dcos_login_uname_option
@dcos_login_pw_option
@sync_dir_run_option
@test_env_run_option
@environment_variables_option
@node_option
@verbosity_option
def run(
    cluster_id: str,
    node_args: Tuple[str],
    sync_dir: Tuple[Path],
    dcos_login_uname: str,
    dcos_login_pw: str,
    test_env: bool,
    node: Tuple[str],
    env: Dict[str, str],
    verbose: int,
) -> None:
    """
    Run an arbitrary command on a node or multiple nodes.

    To use special characters such as single quotes in your command, wrap the
    whole command in double quotes.
    """
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    cluster = cluster_vms.cluster
    for dcos_checkout_dir in sync_dir:
        sync_code_to_masters(
            cluster=cluster,
            dcos_checkout_dir=dcos_checkout_dir,
            dcos_variant=cluster_vms.dcos_variant,
            sudo=True,
        )

    hosts = set([])
    for node_reference in node:
        host = get_node(
            cluster_vms=cluster_vms,
            node_reference=node_reference,
        )
        if host is None:
            message = (
                'No such node in cluster "{cluster_id}" with IP address, VM '
                'name or node reference "{node_reference}". Node '
                'references can be seen with ``minidcos vagrant inspect``.'
            ).format(
                cluster_id=cluster_id,
                node_reference=node_reference,
            )
            raise click.BadParameter(message=message)

        hosts.add(host)

    for host in hosts:
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

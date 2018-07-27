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
    verbosity_option,
)
from cli.common.run_command import run_command
from cli.common.sync import sync_code_to_masters
from cli.common.utils import check_cluster_id_exists, set_logging
from dcos_e2e.node import Node, Transport

from ._common import (
    ClusterInstances,
    InstanceInspectView,
    existing_cluster_ids,
)
from ._options import aws_region_option


def _get_node(cluster_id: str, node_reference: str, aws_region: str) -> Node:
    """
    Get a node from a "reference".

    Args:
        cluster_id: The ID of a cluster.
        node_reference: One of:
            * A node's public IP address
            * A node's private IP address
            * A node's EC2 instance ID
            * A reference in the format "<role>_<number>"
        aws_region: The AWS region the cluster is in.

    Returns:
        The ``Node`` from the given cluster with the given ID.

    Raises:
        click.BadParameter: There is no such node.
    """
    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )

    instances = {
        *cluster_instances.masters,
        *cluster_instances.agents,
        *cluster_instances.public_agents,
    }

    for instance in instances:
        inspect_data = InstanceInspectView(
            instance=instance,
            aws_region=aws_region,
        ).to_dict()
        reference = inspect_data['e2e_reference']
        instance_id = inspect_data['ec2_instance_id']
        public_ip_address = inspect_data['public_ip_address']
        private_ip_address = inspect_data['private_ip_address']
        accepted = (
            reference,
            reference.upper(),
            instance_id,
            public_ip_address,
            private_ip_address,
        )

        if node_reference in accepted:
            return cluster_instances.to_node(instance=instance)

    message = (
        'No such node in cluster "{cluster_id}" with IP address, VM name or '
        'node reference "{node_reference}". '
        'Node references can be seen with ``dcos-vagrant inspect``.'
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
@environment_variables_option
@aws_region_option
@verbosity_option
@click.option(
    '--node',
    type=str,
    default='master_0',
    help=(
        'A reference to a particular node to run the command on. '
        'This can be one of: '
        'The node\'s public IP address, '
        'The node\'s private IP address, '
        'the node\'s EC2 instance ID, '
        'a reference in the format "<role>_<number>". '
        'These details be seen with ``dcos-aws inspect``.'
    ),
)
def run(
    cluster_id: str,
    node_args: Tuple[str],
    sync_dir: Optional[Path],
    dcos_login_uname: str,
    dcos_login_pw: str,
    no_test_env: bool,
    env: Dict[str, str],
    aws_region: str,
    verbose: int,
    node: str,
) -> None:
    """
    Run an arbitrary command on a node.

    This command sets up the environment so that ``pytest`` can be run.

    For example, run
    ``dcos-aws run --cluster-id 1231599 pytest -k test_tls.py``.

    Or, with sync:
    ``dcos-aws run --sync-dir . --cluster-id 1231599 pytest -k test_tls.py``.

    To use special characters such as single quotes in your command, wrap the
    whole command in double quotes.
    """  # noqa: E501
    set_logging(verbosity_level=verbose)
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(aws_region=aws_region),
    )
    cluster_instances = ClusterInstances(
        cluster_id=cluster_id,
        aws_region=aws_region,
    )
    cluster = cluster_instances.cluster
    host = _get_node(
        cluster_id=cluster_id,
        node_reference=node,
        aws_region=aws_region,
    )

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
        transport=Transport.SSH,
    )

"""
Tools for running arbitrary commands on cluster nodes.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import click

from cli.common.sync import sync_code_to_masters
from cli.common.validators import validate_path_is_directory
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Transport

from ._common import ClusterContainers, ContainerInspectView
from ._options import existing_cluster_id_option, node_transport_option


def _validate_environment_variable(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
) -> Dict[str, str]:
    """
    Validate that environment variables are set as expected.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (param, ctx):
        pass

    env = {}
    for definition in value:
        try:
            key, val = definition.split(sep='=', maxsplit=1)
        except ValueError:
            message = (
                '"{definition}" does not match the format "<KEY>=<VALUE>".'
            ).format(definition=definition)
            raise click.BadParameter(message=message)
        env[key] = val
    return env


def _get_node(cluster_id: str, node_reference: str) -> Node:
    """
    Get a node from a "reference".

    Args:
        cluster_id: The ID of a cluster.
        node_reference: One of:
            * A node's IP address
            * A node's Docker container
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


def _run_command(
    args: List[str],
    cluster: Cluster,
    host: Node,
    transport: Transport,
    use_test_env: bool,
    dcos_login_uname: str,
    dcos_login_pw: str,
    env: Dict[str, str],
) -> None:
    """
    Run a command on a given cluster / host.

    Args:
        args: The arguments to run on a node.
        cluster: The cluster to run a command on.
        host: the node to run a command on.
        transport: The transport to use to communicate with the cluster.
        use_test_env: Whether to use the DC/OS integration test environment to
            run the command in.
        dcos_login_uname: The DC/OS login username. This is only used if using
            the test environment and DC/OS Enterprise.
        dcos_login_pw: The DC/OS login password. This is only used if using
            the test environment and DC/OS Enterprise.
        env: Environment variables to set before running the command.
    """
    columns, rows = click.get_terminal_size()

    env = {
        # LINES and COLUMNS are needed if using the ``DOCKER_EXEC`` transport.
        # See https://github.com/moby/moby/issues/35407.
        'COLUMNS': str(columns),
        'LINES': str(rows),
        'DCOS_LOGIN_UNAME': dcos_login_uname,
        'DCOS_LOGIN_PW': dcos_login_pw,
        **env,
    }

    if not use_test_env:
        try:
            host.run(
                args=args,
                log_output_live=False,
                tty=True,
                shell=True,
                env=env,
                transport=transport,
            )
        except subprocess.CalledProcessError as exc:
            sys.exit(exc.returncode)

        return

    try:
        cluster.run_integration_tests(
            pytest_command=args,
            tty=True,
            env=env,
            test_host=host,
            transport=transport,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


@click.command('run', context_settings=dict(ignore_unknown_options=True))
@existing_cluster_id_option
@click.option(
    '--dcos-login-uname',
    type=str,
    default='admin',
    help=(
        'The username to set the ``DCOS_LOGIN_UNAME`` environment variable to.'
    ),
)
@click.option(
    '--dcos-login-pw',
    type=str,
    default='admin',
    help=(
        'The password to set the ``DCOS_LOGIN_PW`` environment variable to.'
    ),
)
@click.argument('node_args', type=str, nargs=-1, required=True)
@click.option(
    '--sync-dir',
    type=click.Path(exists=True),
    help=(
        'The path to a DC/OS checkout. '
        'Part of this checkout will be synced to all master nodes before the '
        'command is run.'
    ),
    callback=validate_path_is_directory,
)
@click.option(
    '--no-test-env',
    is_flag=True,
    help=(
        'With this flag set, no environment variables are set and the command '
        'is run in the home directory. '
    ),
)
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
        'These details be seen with ``dcos_docker inspect``.'
    ),
)
@click.option(
    '--env',
    type=str,
    callback=_validate_environment_variable,
    multiple=True,
    help='Set environment variables in the format "<KEY>=<VALUE>"',
)
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

    _run_command(
        args=list(node_args),
        cluster=cluster,
        host=host,
        use_test_env=not no_test_env,
        dcos_login_uname=dcos_login_uname,
        dcos_login_pw=dcos_login_pw,
        env=env,
        transport=transport,
    )

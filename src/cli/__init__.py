"""
A CLI for controlling DC/OS clusters on Docker.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import click

from dcos_e2e.node import Node, Transport

from ._common import ClusterContainers, ContainerInspectView
from ._options import existing_cluster_id_option, node_transport_option
from ._validators import (
    validate_environment_variable,
    validate_path_is_directory,
)
from .commands.create import create
from .commands.destroy import destroy, destroy_list
from .commands.doctor import doctor
from .commands.inspect_cluster import inspect_cluster
from .commands.list_clusters import list_clusters
from .commands.mac_network import destroy_mac_network, setup_mac_network
from .commands.sync import sync_code
from .commands.wait import wait


def _set_logging(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> None:
    """
    Set logging level depending on the chosen verbosity.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    value = min(value, 3)
    value = max(value, 0)
    verbosity_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.NOTSET,
    }
    # Disable logging calls of the given severity level or below.
    logging.disable(verbosity_map[int(value or 0)])


@click.option(
    '-v',
    '--verbose',
    count=True,
    callback=_set_logging,
)
@click.group(name='dcos-docker')
@click.version_option()
def dcos_docker(verbose: None) -> None:
    """
    Manage DC/OS clusters on Docker.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (verbose, ):
        pass


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


@dcos_docker.command('run', context_settings=dict(ignore_unknown_options=True))
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
    callback=validate_environment_variable,
    multiple=True,
    help='Set environment variables in the format "<KEY>=<VALUE>"',
)
@node_transport_option
@click.pass_context
def run(
    ctx: click.core.Context,
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

    if sync_dir is not None:
        ctx.invoke(
            sync_code,
            cluster_id=cluster_id,
            dcos_checkout_dir=str(sync_dir),
            transport=transport,
        )

    if transport == Transport.DOCKER_EXEC:
        columns, rows = click.get_terminal_size()
        # See https://github.com/moby/moby/issues/35407.
        env = {
            'COLUMNS': str(columns),
            'LINES': str(rows),
            **env,
        }

    if no_test_env:
        try:
            host.run(
                args=list(node_args),
                log_output_live=False,
                tty=True,
                shell=True,
                env=env,
                transport=transport,
            )
        except subprocess.CalledProcessError as exc:
            sys.exit(exc.returncode)

        return

    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster = cluster_containers.cluster

    env = {
        'DCOS_LOGIN_UNAME': dcos_login_uname,
        'DCOS_LOGIN_PW': dcos_login_pw,
        **env,
    }

    try:
        cluster.run_integration_tests(
            pytest_command=list(node_args),
            tty=True,
            env=env,
            test_host=host,
            transport=transport,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


@dcos_docker.command('web')
@existing_cluster_id_option
def web(cluster_id: str) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``dcos-docker wait`` before running this command.
    """
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        # The transport is not used so does not matter.
        transport=Transport.DOCKER_EXEC,
    )
    cluster = cluster_containers.cluster
    master = next(iter(cluster.masters))
    web_ui = 'http://' + str(master.public_ip_address)
    click.launch(web_ui)


dcos_docker.add_command(create)
dcos_docker.add_command(destroy)
dcos_docker.add_command(destroy_list)
dcos_docker.add_command(destroy_mac_network)
dcos_docker.add_command(doctor)
dcos_docker.add_command(inspect_cluster)
dcos_docker.add_command(list_clusters)
dcos_docker.add_command(setup_mac_network)
dcos_docker.add_command(sync_code)
dcos_docker.add_command(wait)

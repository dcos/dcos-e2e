"""
Tools for running arbitrary commands on cluster nodes.
"""

import subprocess
import sys
from typing import Dict, List

import click

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Output, Transport


def run_command(
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
    tty = sys.stdout.isatty()

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
                output=Output.NO_CAPTURE,
                tty=tty,
                shell=True,
                env=env,
                transport=transport,
            )
        except subprocess.CalledProcessError as exc:
            sys.exit(exc.returncode)

        return

    try:
        cluster.run_with_test_environment(
            args=args,
            tty=tty,
            env=env,
            node=host,
            transport=transport,
            output=Output.NO_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)

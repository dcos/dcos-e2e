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
    no_test_env_run_option,
    sync_dir_run_option,
)
from cli.common.run_command import run_command
from cli.common.sync import sync_code_to_masters
from dcos_e2e.node import Transport

from ._common import ClusterVMs
from ._options import existing_cluster_id_option


@click.command('run', context_settings=dict(ignore_unknown_options=True))
@existing_cluster_id_option
@node_args_argument
@dcos_login_uname_option
@dcos_login_pw_option
@sync_dir_run_option
@no_test_env_run_option
@environment_variables_option
def run(
    cluster_id: str,
    node_args: Tuple[str],
    sync_dir: Optional[Path],
    dcos_login_uname: str,
    dcos_login_pw: str,
    no_test_env: bool,
    env: Dict[str, str],
) -> None:
    """
    Run an arbitrary command on a node.

    This command sets up the environment so that ``pytest`` can be run.

    For example, run
    ``dcos-vagrant run --cluster-id 1231599 pytest -k test_tls.py``.

    Or, with sync:
    ``dcos-vagrant run --sync-dir . --cluster-id 1231599 pytest -k test_tls.py``.

    To use special characters such as single quotes in your command, wrap the
    whole command in double quotes.
    """  # noqa: E501
    cluster_vms = ClusterVMs(cluster_id=cluster_id)
    cluster = cluster_vms.cluster
    host = next(iter(cluster.masters))

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

"""
Tools for waiting for DC/OS.
"""

import sys

import click
import click_spinner
import urllib3

from dcos_e2e.cluster import Cluster
from dcos_e2e.exceptions import DCOSTimeoutError
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant

from .utils import command_path


def wait_for_dcos(
    dcos_variant: DCOSVariant,
    cluster: Cluster,
    superuser_username: str,
    superuser_password: str,
    http_checks: bool,
    sibling_ctx: click.core.Context,
    doctor_command: click.core.Command,
) -> None:
    """
    Wait for DC/OS to start.

    Args:
        dcos_variant: The DC/OS variant of the cluster.
        cluster: The cluster to wait for.
        superuser_username: If the cluster is a DC/OS Enterprise cluster, use
            this username to wait for DC/OS.
        superuser_password: If the cluster is a DC/OS Enterprise cluster, use
            this password to wait for DC/OS.
        http_checks: Whether or not to wait for checks which require an HTTP
            connection to the cluster.
        doctor_command: A ``doctor`` command to advise a user to use.
        sibling_ctx: A context associated with a call to a sibling of
            ``doctor_command``.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    doctor_command_name = command_path(
        sibling_ctx=sibling_ctx,
        command=doctor_command,
    )
    message = (
        'A cluster may take some time to be ready.\n'
        'The amount of time it takes to start a cluster depends on a variety '
        'of factors.\n'
        'If you are concerned that this is hanging, try '
        '"{doctor_command_name}" to diagnose common issues.'
    ).format(doctor_command_name=doctor_command_name)
    click.echo(message)

    no_login_message = (
        'If you cancel this command while it is running, '
        'you may not be able to log in. '
        'To resolve that, run this command again.'
    )

    if not dcos_variant == DCOSVariant.ENTERPRISE:
        click.echo(no_login_message)

    with click_spinner.spinner():
        try:
            if dcos_variant == DCOSVariant.ENTERPRISE:
                cluster.wait_for_dcos_ee(
                    superuser_username=superuser_username,
                    superuser_password=superuser_password,
                    http_checks=http_checks,
                )
                return

            cluster.wait_for_dcos_oss(http_checks=http_checks)
        except DCOSTimeoutError:
            click.echo('Waiting for DC/OS to start timed out.', err=True)
            sys.exit(1)

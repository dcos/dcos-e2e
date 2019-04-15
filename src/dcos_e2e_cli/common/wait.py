"""
Tools for waiting for DC/OS.
"""

import sys

import click
import urllib3
from halo import Halo
from retry import retry

from dcos_e2e.cluster import Cluster
from dcos_e2e.exceptions import DCOSTimeoutError
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant
from dcos_e2e_cli.common.variants import (
    cluster_variant_available,
    get_cluster_variant,
)


@retry(
    exceptions=(DCOSTimeoutError),
    tries=60 * 60,
    delay=1,
)
def _wait_for_variant(cluster: Cluster) -> None:
    """
    Wait for a particular file to be available on the cluster.
    This means that the cluster variant can be determined.
    """
    if not cluster_variant_available(cluster=cluster):
        raise DCOSTimeoutError


def wait_for_dcos(
    cluster: Cluster,
    superuser_username: str,
    superuser_password: str,
    http_checks: bool,
    doctor_command_name: str,
) -> None:
    """
    Wait for DC/OS to start.

    Args:
        cluster: The cluster to wait for.
        superuser_username: If the cluster is a DC/OS Enterprise cluster, use
            this username to wait for DC/OS.
        superuser_password: If the cluster is a DC/OS Enterprise cluster, use
            this password to wait for DC/OS.
        http_checks: Whether or not to wait for checks which require an HTTP
            connection to the cluster.
        doctor_command_name: A ``doctor`` command to advise a user to use.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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

    spinner = Halo(enabled=sys.stdout.isatty())
    spinner.start(text='Waiting for DC/OS variant')
    _wait_for_variant(cluster=cluster)
    dcos_variant = get_cluster_variant(cluster=cluster)
    spinner.succeed()
    if dcos_variant == DCOSVariant.OSS:
        click.echo(no_login_message)
    spinner.start(text='Waiting for DC/OS to start')
    try:
        if dcos_variant == DCOSVariant.ENTERPRISE:
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
                http_checks=http_checks,
            )
        else:
            cluster.wait_for_dcos_oss(http_checks=http_checks)
    except DCOSTimeoutError:
        spinner.fail(text='Waiting for DC/OS to start timed out.')
        sys.exit(1)

    spinner.succeed()

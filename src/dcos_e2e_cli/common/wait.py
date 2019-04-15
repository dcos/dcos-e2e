"""
Tools for waiting for DC/OS.
"""

import sys

import click
import urllib3
from retry import retry
from halo import Halo
import subprocess
import textwrap

from dcos_e2e.cluster import Cluster
from dcos_e2e.exceptions import DCOSTimeoutError
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant
from dcos_e2e_cli.common.variants import get_cluster_variant


@retry(
    exceptions=(DCOSTimeoutError),
    tries=60 * 60,
    delay=1,
)
def _wait_for_variant(cluster: Cluster) -> None:
    """
    XXX
    """
    (master, ) = cluster.masters
    script = textwrap.dedent(
        """
        #!/bin/bash
        if [ -e /opt/mesosphere/etc/dcos-version.json ]
        then
            echo "True"
        else
            echo "False"
        fi
        """,
    )
    version_file_exists = master.run(args=[script], shell=True)
    if version_file_exists.stdout.strip().decode() != 'True':
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
        dcos_variant: The DC/OS variant of the cluster.
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
    spinner.start(text='Waiting for DC/OS variant')
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

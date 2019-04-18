"""
Helpers for managing DC/OS Variants.
"""

import json
import subprocess
import sys
import textwrap
from pathlib import Path
from shutil import rmtree
from typing import Optional

import click
from halo import Halo

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Output
from dcos_e2e_cli._vendor.dcos_installer_tools import (
    DCOSVariant,
    get_dcos_installer_details,
)


def get_install_variant(
    given_variant: str,
    installer_path: Optional[Path],
    doctor_message: str,
    workspace_dir: Path,
) -> DCOSVariant:
    """
    Get the variant of DC/OS to install.

    Args:
        given_variant: The variant string given by the user to the
            ``variant_option``. One of "auto", "enterprise" and "oss". If
            "auto" is given, use the DC/OS installer to find the variant.
        installer_path: The path to a DC/OS installer, if available.
        workspace_dir: A directory to work in, given that this function uses
            large files.
        doctor_message: The message to show if something goes wrong.

    Returns:
        The variant of DC/OS to install.

    Raises:
        CalledProcessError: There was an error unpacking the installer.
    """
    if given_variant == 'auto':
        assert installer_path is not None
        spinner = Halo(enabled=sys.stdout.isatty())
        spinner.start(text='Determining DC/OS variant')
        try:
            details = get_dcos_installer_details(
                installer=installer_path,
                workspace_dir=workspace_dir,
            )
        except subprocess.CalledProcessError as exc:
            rmtree(path=str(workspace_dir), ignore_errors=True)
            spinner.stop()
            click.echo(doctor_message)
            click.echo()
            click.echo('Original error:', err=True)
            click.echo(exc.stderr, err=True)
            raise
        except ValueError as exc:
            click.echo(str(exc), err=True)
            sys.exit(1)

        spinner.succeed()
        return details.variant

    return {
        'oss': DCOSVariant.OSS,
        'enterprise': DCOSVariant.ENTERPRISE,
    }[given_variant]


def cluster_variant_available(cluster: Cluster) -> bool:
    """
    Check whether a cluster's variant can be retrieved.

    Args:
        cluster: The cluster to check.

    Returns:
        Whether the cluster variant is available.
    """
    master = next(iter(cluster.masters))
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
    output = version_file_exists.stdout.strip().decode()
    return {'True': True, 'False': False}[output]


def get_cluster_variant(cluster: Cluster) -> Optional[DCOSVariant]:
    """
    Get the variant of DC/OS running on a cluster.

    Args:
        cluster: The cluster running DC/OS.

    Returns:
        The variant of DC/OS installed on the given cluster or ``None`` if the
        file required for us to know is not ready.
    """
    if not cluster_variant_available(cluster=cluster):
        return None

    master = next(iter(cluster.masters))
    get_version_json_args = ['cat', '/opt/mesosphere/etc/dcos-version.json']
    result = master.run(args=get_version_json_args, output=Output.CAPTURE)
    dcos_version = json.loads(result.stdout.decode())
    given_variant = dcos_version['dcos-variant']
    return {
        'open': DCOSVariant.OSS,
        'enterprise': DCOSVariant.ENTERPRISE,
    }[given_variant]

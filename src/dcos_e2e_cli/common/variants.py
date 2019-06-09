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
from dcos_e2e.exceptions import DCOSNotInstalledError
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


def get_cluster_variant(cluster: Cluster) -> Optional[DCOSVariant]:
    """
    Get the variant of DC/OS running on a cluster.

    Args:
        cluster: The cluster running DC/OS.

    Returns:
        The variant of DC/OS installed on the given cluster or ``None`` if the
        file required for us to know is not ready.
    """
    master = next(iter(cluster.masters))
    try:
        variant = master.dcos_build_info().variant
        variant_retrieved = True
    except DCOSNotInstalledError:
        variant_retrieved = False

    return variant if variant_retrieved else None

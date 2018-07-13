"""
Common utilities for making DC/OS E2E CLIs.
"""

import json
import subprocess
import sys
from pathlib import Path
from shutil import rmtree

import click
import click_spinner

from cli.common.options import (
    agents_option,
    artifact_argument,
    extra_config_option,
    masters_option,
    public_agents_option,
    workspace_dir_option,
)
from cli.common.utils import get_variant


def _is_enterprise(build_artifact: Path, workspace_dir: Path) -> bool:
    """
    Return whether the build artifact is an Enterprise artifact.

    Raises:
        ValueError: A space is in the build artifact path.
    """
    if ' ' in str(build_artifact):
        raise ValueError('No spaces allowed in path to the build artifact.')

    result = subprocess.check_output(
        args=['bash', str(build_artifact), '--version'],
        cwd=str(workspace_dir),
        stderr=subprocess.PIPE,
    )

    result = result.decode()
    result = ' '.join(
        [
            line for line in result.splitlines()
            if not line.startswith('Extracting image')
            and not line.startswith('Loaded image') and '.tar' not in line
        ],
    )

    version_info = json.loads(result)
    variant = version_info['variant']
    return bool(variant == 'ee')


def get_variant(
    artifact_path: Path,
    doctor_message: str,
    workspace_dir: Path,
) -> str:
    """
    Get the variant of a DC/OS artifact.

    Args:
        artifact_path: The path to an artifact to get the DC/OS variant of.
        workspace_dir: A directory to work in, given that this function uses
            large files.
        doctor_message: The message to show if something goes wrong.

    Returns:
        "oss" or "enterprise" as appropriate.

    Raises:
        CalledProcessError: There was an error unpacking the artifact.
    """
    try:
        with click_spinner.spinner():
            enterprise = _is_enterprise(
                build_artifact=artifact_path,
                workspace_dir=workspace_dir,
            )
    except subprocess.CalledProcessError as exc:
        rmtree(path=str(workspace_dir), ignore_errors=True)
        click.echo(doctor_message)
        click.echo()
        click.echo('Original error:', err=True)
        click.echo(exc.stderr, err=True)
        raise
    except ValueError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    return 'enterprise' if enterprise else 'oss'

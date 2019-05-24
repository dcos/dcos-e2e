"""
Helpers for installing DC/OS.
"""

import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional

import click

import dcos_e2e_cli.common.wait
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Output
from dcos_e2e_cli._vendor.halo import Halo

from .base_classes import ClusterRepresentation
from .credentials import DEFAULT_SUPERUSER_PASSWORD, DEFAULT_SUPERUSER_USERNAME


def install_dcos_from_path(
    cluster: Cluster,
    cluster_representation: ClusterRepresentation,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    local_genconf_dir: Optional[Path],
    dcos_installer: Path,
    doctor_message: str,
) -> None:
    """
    Install DC/OS on a cluster from a path.

    Args:
        cluster: The cluster to install DC/OS on.
        cluster_representation: A representation of the cluster.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        local_genconf_dir: A directory of files to copy from the host to the
            installer node before installing DC/OS.
        dcos_config: The DC/OS configuration to use.
        dcos_installer: The path to a DC/OS installer.
        doctor_message: A message which instructs the user on which command to
            use if installation fails.
    """
    files_to_copy_to_genconf_dir = []
    if local_genconf_dir is not None:
        node_genconf_path = Path('/genconf')
        for genconf_file in local_genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(local_genconf_dir)
            relative_path = node_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))

    spinner = Halo(enabled=sys.stdout.isatty())  # type: ignore
    spinner.start('Installing DC/OS')

    # We allow a cluster to be passed in rather than just inferring it from
    # ``cluster_representation`` in case the ``cluster`` has a more efficient
    # installation method than a ``Cluster.from_nodes``.
    # However, if the cluster is a ``Cluster.from_nodes``, ``destroy`` will not
    # work and therefore we use ``cluster_representation.destroy`` instead.
    #
    # We do not always use ``cluster_representation.destroy`` because the AWS
    # backend does not support this.
    try:
        cluster.install_dcos_from_path(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=Output.LOG_AND_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        spinner.stop()
        click.echo('Error installing DC/OS.', err=True)
        click.echo(click.style('Full error:', fg='yellow'))
        click.echo(click.style(textwrap.indent(str(exc), '  '), fg='yellow'))
        stderr = exc.stderr.decode()
        click.echo(click.style(textwrap.indent(stderr, '  '), fg='red'))
        click.echo(doctor_message)
        try:
            cluster.destroy()
        except NotImplementedError:
            cluster_representation.destroy()
        sys.exit(exc.returncode)

    spinner.succeed()


def install_dcos_from_url(
    cluster: Cluster,
    cluster_representation: ClusterRepresentation,
    ip_detect_path: Path,
    dcos_config: Dict[str, Any],
    local_genconf_dir: Optional[Path],
    dcos_installer_url: str,
    doctor_message: str,
) -> None:
    """
    Install DC/OS on a cluster from a url.

    Args:
        cluster: The cluster to install DC/OS on.
        cluster_representation: A representation of the cluster.
        ip_detect_path: The ``ip-detect`` script to use for installing DC/OS.
        local_genconf_dir: A directory of files to copy from the host to the
            installer node before installing DC/OS.
        dcos_config: The DC/OS configuration to use.
        dcos_installer_url: A URL pointing to a DC/OS installer.
        doctor_message: A message which instructs the user on which command to
            use if installation fails.
    """
    files_to_copy_to_genconf_dir = []
    if local_genconf_dir is not None:
        node_genconf_path = Path('/genconf')
        for genconf_file in local_genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(local_genconf_dir)
            relative_path = node_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))

    spinner = Halo(enabled=sys.stdout.isatty())  # type: ignore
    spinner.start('Installing DC/OS')

    # We allow a cluster to be passed in rather than just inferring it from
    # ``cluster_representation`` in case the ``cluster`` has a more efficient
    # installation method than a ``Cluster.from_nodes``.
    # However, if the cluster is a ``Cluster.from_nodes``, ``destroy`` will not
    # work and therefore we use ``cluster_representation.destroy`` instead.
    #
    # We do not always use ``cluster_representation.destroy`` because the AWS
    # backend does not support this.
    try:
        cluster.install_dcos_from_url(
            dcos_installer=dcos_installer_url,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=Output.LOG_AND_CAPTURE,
        )
    except subprocess.CalledProcessError as exc:
        spinner.stop()
        click.echo('Error installing DC/OS.', err=True)
        click.echo(click.style('Full error:', fg='yellow'))
        click.echo(click.style(textwrap.indent(str(exc), '  '), fg='yellow'))
        stderr = exc.stderr.decode()
        click.echo(click.style(textwrap.indent(stderr, '  '), fg='red'))
        click.echo(doctor_message)
        try:
            cluster.destroy()
        except NotImplementedError:
            cluster_representation.destroy()
        sys.exit(exc.returncode)

    spinner.succeed()


def run_post_install_steps(
    cluster: Cluster,
    cluster_id: str,
    dcos_config: Dict[str, Any],
    doctor_command_name: str,
    http_checks: bool,
    wait_command_name: str,
    wait_for_dcos: bool,
) -> None:
    """
    Wait for DC/OS if wanted, else print a message stating that next you should
    wait.

    Args:
        cluster: A DC/OS cluster to run steps against.
        cluster_id: The ID of the cluster.
        dcos_config: The config that DC/OS was installed with.
        doctor_command_name: The name of a ``doctor`` command to use if things
            go wrong.
        http_checks: Whether to run HTTP checks when waiting for DC/OS.
        wait_command_name: The name of a ``wait`` command to use after the
            cluster is installed.
        wait_for_dcos: Whether to wait for DC/OS to be installed.
    """
    superuser_username = dcos_config.get(
        'superuser_username',
        DEFAULT_SUPERUSER_USERNAME,
    )

    superuser_password = dcos_config.get(
        'superuser_password',
        DEFAULT_SUPERUSER_PASSWORD,
    )

    if wait_for_dcos:
        dcos_e2e_cli.common.wait.wait_for_dcos(
            cluster=cluster,
            superuser_username=superuser_username,
            superuser_password=superuser_password,
            http_checks=http_checks,
            doctor_command_name=doctor_command_name,
        )

        return

    cluster_started_message = (
        'Cluster "{cluster_id}" has started. '
        'Run "{wait_command_name} --cluster-id {cluster_id}" to wait for '
        'DC/OS to become ready.'
    ).format(
        cluster_id=cluster_id,
        wait_command_name=wait_command_name,
    )
    click.echo(cluster_started_message, err=True)

    click.echo(cluster_id)

"""
Tools for creating DC/OS clusters.
"""

import sys
import textwrap
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, Optional

import click
from passlib.hash import sha512_crypt

from dcos_e2e.base_classes import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant

from .utils import get_doctor_message


def create_cluster(
    cluster_backend: ClusterBackend,
    masters: int,
    agents: int,
    public_agents: int,
    sibling_ctx: click.core.Context,
    doctor_command: click.core.Command,
) -> Cluster:
    """
    Create a cluster.
    """
    doctor_message = get_doctor_message(
        sibling_ctx=sibling_ctx,
        doctor_command=doctor_command,
    )
    try:
        return Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(click.style('Full error:', fg='yellow'))
        click.echo(click.style(textwrap.indent(str(exc), '  '), fg='yellow'))
        click.echo(doctor_message, err=True)

        sys.exit(exc.returncode)


def get_config(
    cluster: Cluster,
    extra_config: Dict[str, Any],
    dcos_variant: DCOSVariant,
    security_mode: Optional[str],
    license_key: Optional[str],
) -> Dict[str, Any]:
    """
    Get a DC/OS configuration to use for the given cluster.
    """
    is_enterprise = bool(dcos_variant == DCOSVariant.ENTERPRISE)

    if is_enterprise:
        superuser_username = 'admin'
        superuser_password = 'admin'

        enterprise_extra_config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
        }
        if license_key is not None:
            key_contents = Path(license_key).read_text()
            enterprise_extra_config['license_key_contents'] = key_contents

        extra_config = {**enterprise_extra_config, **extra_config}
        if security_mode is not None:
            extra_config['security'] = security_mode

    dcos_config = {
        **cluster.base_config,
        **extra_config,
    }

    return dcos_config

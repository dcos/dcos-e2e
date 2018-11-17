"""
Tools for creating DC/OS clusters.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
from passlib.hash import sha512_crypt

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster

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
    XXX
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
        click.echo(doctor_message)
        sys.exit(exc.returncode)


def get_config(
    cluster: Cluster,
    extra_config: Dict[str, Any],
    is_enterprise: bool,
    security_mode: Optional[str],
    license_key: Optional[str],
) -> Dict[str, Any]:
    """
    Get a DC/OS configuration to use for the given cluster.
    """
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

"""
Tools for creating DC/OS clusters.
"""

import sys
import textwrap
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, Optional

import click
import halo
from passlib.hash import sha512_crypt

from dcos_e2e.base_classes import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import DCOSVariant

from .base_classes import ClusterRepresentation
from .credentials import DEFAULT_SUPERUSER_PASSWORD, DEFAULT_SUPERUSER_USERNAME

# yapf breaks multi-line noqa, see
# https://github.com/google/yapf/issues/524.
# yapf: disable
CREATE_HELP = (
    """
    Create a DC/OS cluster.

        DC/OS Enterprise

            \b
            DC/OS Enterprise clusters require different configuration variables to DC/OS OSS.
            For example, enterprise clusters require the following configuration parameters:

            ``superuser_username``, ``superuser_password_hash``, ``fault_domain_enabled``, ``license_key_contents``

            \b
            These can all be set in ``--extra-config``.
            However, some defaults are provided for all but the license key.

            \b
            The default superuser username is ``{default_superuser_username}``.
            The default superuser password is ``{default_superuser_password}``.
            The default ``fault_domain_enabled`` is ``false``.

            \b
            ``license_key_contents`` must be set for DC/OS Enterprise 1.11 and above.
            This is set to one of the following, in order:

            \b
            * The ``license_key_contents`` set in ``--extra-config``.
            * The contents of the path given with ``--license-key``.
            * The contents of the path set in the ``DCOS_LICENSE_KEY_PATH`` environment variable.

            \b
            If none of these are set, ``license_key_contents`` is not given.
    """# noqa: E501,E261
).format(
    default_superuser_username=DEFAULT_SUPERUSER_USERNAME,
    default_superuser_password=DEFAULT_SUPERUSER_PASSWORD,
)
# yapf: enable


def create_cluster(
    cluster_backend: ClusterBackend,
    masters: int,
    agents: int,
    public_agents: int,
    doctor_message: str,
    enable_spinner: bool,
) -> Cluster:
    """
    Create a cluster.

    Args:
        cluster_backend: The cluster backend to use.
        masters: The number of master nodes to create.
        agents: The number of agent nodes to create.
        public_agents: The number of public agent nodes to create.
        doctor_message: A message to show pointing users to a doctor command.
        enable_spinner: Whether to enable the spinner animation.

    Returns:
        A new cluster.
    """
    spinner = halo.Halo(enabled=enable_spinner)
    spinner.start(text='Creating cluster')
    try:
        cluster = Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        )
    except CalledProcessError as exc:
        spinner.stop()
        click.echo('Error creating cluster.', err=True)
        click.echo(click.style('Full error:', fg='yellow'))
        click.echo(click.style(textwrap.indent(str(exc), '  '), fg='yellow'))
        click.echo(doctor_message, err=True)

        sys.exit(exc.returncode)

    spinner.succeed()
    return cluster


def get_config(
    cluster_representation: ClusterRepresentation,
    extra_config: Dict[str, Any],
    dcos_variant: DCOSVariant,
    security_mode: Optional[str],
    license_key: Optional[Path],
) -> Dict[str, Any]:
    """
    Get a DC/OS configuration to use for the given cluster.
    """
    is_enterprise = bool(dcos_variant == DCOSVariant.ENTERPRISE)

    if is_enterprise:
        superuser_username = DEFAULT_SUPERUSER_USERNAME
        superuser_password = DEFAULT_SUPERUSER_PASSWORD

        enterprise_extra_config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
        }
        if license_key is not None:
            key_contents = license_key.read_text()
            enterprise_extra_config['license_key_contents'] = key_contents

        extra_config = {**enterprise_extra_config, **extra_config}
        if security_mode is not None:
            extra_config['security'] = security_mode

    dcos_config = {
        **cluster_representation.base_config,
        **extra_config,
    }

    return dcos_config

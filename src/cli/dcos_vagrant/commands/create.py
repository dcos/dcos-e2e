"""
Tools for creating a DC/OS cluster.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import click

@click.command('create')
@click.argument('artifact', type=click.Path(exists=True))
@click.option(
    '--masters',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of master nodes.',
)
@click.option(
    '--agents',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of agent nodes.',
)
@click.option(
    '--public-agents',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of public agent nodes.',
)
@click.option(
    '--extra-config',
    type=click.Path(exists=True),
    callback=_validate_dcos_configuration,
    help=(
        'The path to a file including DC/OS configuration YAML. '
        'The contents of this file will be added to add to a default '
        'configuration.'
    ),
)
@click.option(
    '--security-mode',
    type=click.Choice(['disabled', 'permissive', 'strict']),
    help=(
        'The security mode to use for a DC/OS Enterprise cluster. '
        'This overrides any security mode set in ``--extra-config``.'
    ),
)
@click.option(
    '--workspace-dir',
    type=click.Path(exists=True),
    callback=validate_path_is_directory,
    help=(
        'Creating a cluster can use approximately 2 GB of temporary storage. '
        'Set this option to use a custom "workspace" for this temporary '
        'storage. '
        'See '
        'https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir '
        'for details on the temporary directory location if this option is '
        'not set.'
    ),
)
@click.pass_context
def create(
    ctx: click.core.Context,
    agents: int,
    artifact: str,
    extra_config: Dict[str, Any],
    masters: int,
    public_agents: int,
    license_key: Optional[str],
    security_mode: Optional[str],
    workspace_dir: Optional[Path],
    variant: str,
    wait_for_dcos: bool,
) -> None:
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
            The default superuser username is ``admin``.
            The default superuser password is ``admin``.
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
    """  # noqa: E501
    pass

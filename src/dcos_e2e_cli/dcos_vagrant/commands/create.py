"""
Tools for creating a DC/OS cluster.
"""

import json
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from halo import Halo

import dcos_e2e_cli.common.wait
from dcos_e2e.backends import Vagrant
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant
from dcos_e2e_cli.common.arguments import installer_argument
from dcos_e2e_cli.common.create import create_cluster, get_config
from dcos_e2e_cli.common.options import (
    agents_option,
    cluster_id_option,
    copy_to_master_option,
    enable_selinux_enforcing_option,
    extra_config_option,
    genconf_dir_option,
    license_key_option,
    masters_option,
    public_agents_option,
    security_mode_option,
    variant_option,
    verbosity_option,
    workspace_dir_option,
)
from dcos_e2e_cli.common.utils import (
    check_cluster_id_unique,
    command_path,
    get_doctor_message,
    get_variant,
    install_dcos_from_path,
    set_logging,
    show_cluster_started_message,
)
from dcos_e2e_cli.common.credentials import (
    DEFAULT_SUPERUSER_USERNAME,
    DEFAULT_SUPERUSER_PASSWORD,
)

from ._common import (
    CLUSTER_ID_DESCRIPTION_KEY,
    VARIANT_DESCRIPTION_KEY,
    VARIANT_ENTERPRISE_DESCRIPTION_VALUE,
    VARIANT_OSS_DESCRIPTION_VALUE,
    WORKSPACE_DIR_DESCRIPTION_KEY,
    existing_cluster_ids,
)
from .doctor import doctor
from .wait import wait


@click.command('create')
@installer_argument
@masters_option
@agents_option
@extra_config_option
@public_agents_option
@workspace_dir_option
@variant_option
@license_key_option
@genconf_dir_option
@security_mode_option
@copy_to_master_option
@cluster_id_option
@verbosity_option
@enable_selinux_enforcing_option
@click.option(
    '--wait-for-dcos',
    is_flag=True,
    help=(
        'Wait for DC/OS after creating the cluster. '
        'This is equivalent to using "minidcos vagrant wait" after this '
        'command.'
    ),
)
@click.pass_context
@Halo(enabled=sys.stdout.isatty())
def create(
    ctx: click.core.Context,
    agents: int,
    installer: str,
    extra_config: Dict[str, Any],
    masters: int,
    public_agents: int,
    variant: str,
    workspace_dir: Optional[Path],
    license_key: Optional[str],
    security_mode: Optional[str],
    copy_to_master: List[Tuple[Path, Path]],
    cluster_id: str,
    verbose: int,
    enable_selinux_enforcing: bool,
    genconf_dir: Optional[Path],
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
    set_logging(verbosity_level=verbose)
    check_cluster_id_unique(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    base_workspace_dir = workspace_dir or Path(tempfile.gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex
    workspace_dir.mkdir(parents=True)

    doctor_message = get_doctor_message(sibling_ctx=ctx, doctor_command=doctor)
    installer_path = Path(installer).resolve()

    dcos_variant = get_variant(
        given_variant=variant,
        installer_path=installer_path,
        workspace_dir=workspace_dir,
        doctor_message=doctor_message,
    )

    variant_label_value = {
        DCOSVariant.OSS: VARIANT_OSS_DESCRIPTION_VALUE,
        DCOSVariant.ENTERPRISE: VARIANT_ENTERPRISE_DESCRIPTION_VALUE,
    }[dcos_variant]

    description = {
        CLUSTER_ID_DESCRIPTION_KEY: cluster_id,
        WORKSPACE_DIR_DESCRIPTION_KEY: str(workspace_dir),
        VARIANT_DESCRIPTION_KEY: variant_label_value,
    }
    cluster_backend = Vagrant(
        workspace_dir=workspace_dir,
        virtualbox_description=json.dumps(obj=description),
    )

    cluster = create_cluster(
        cluster_backend=cluster_backend,
        masters=masters,
        agents=agents,
        public_agents=public_agents,
        doctor_message=doctor_message,
    )

    nodes = {*cluster.masters, *cluster.agents, *cluster.public_agents}
    for node in nodes:
        if enable_selinux_enforcing:
            node.run(args=['setenforce', '1'], sudo=True)

    for node in cluster.masters:
        for path_pair in copy_to_master:
            local_path, remote_path = path_pair
            node.send_file(
                local_path=local_path,
                remote_path=remote_path,
            )

    files_to_copy_to_genconf_dir = []
    if genconf_dir is not None:
        container_genconf_path = Path('/genconf')
        for genconf_file in genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(genconf_dir)
            relative_path = container_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))

    dcos_config = get_config(
        cluster=cluster,
        extra_config=extra_config,
        dcos_variant=dcos_variant,
        security_mode=security_mode,
        license_key=license_key,
    )

    install_dcos_from_path(
        cluster=cluster,
        dcos_config=dcos_config,
        ip_detect_path=cluster_backend.ip_detect_path,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        doctor_message=doctor_message,
        installer=installer_path,
    )

    superuser_username = dcos_config.get(
        'superuser_username',
        DEFAULT_SUPERUSER_USERNAME,
    )

    superuser_password = dcos_config.get(
        'superuser_password',
        DEFAULT_SUPERUSER_PASSWORD,
    )

    doctor_command_name = command_path(sibling_ctx=ctx, command=doctor)
    if wait_for_dcos:
        dcos_e2e_cli.common.wait.wait_for_dcos(
            dcos_variant=dcos_variant,
            cluster=cluster,
            superuser_username=superuser_username,
            superuser_password=superuser_password,
            http_checks=True,
            doctor_command_name=doctor_command_name,
        )

        return

    wait_command_name = command_path(sibling_ctx=ctx, command=wait)
    show_cluster_started_message(
        wait_command_name=wait_command_name,
        cluster_id=cluster_id,
    )

    click.echo(cluster_id)

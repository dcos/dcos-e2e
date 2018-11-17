"""
Tools for creating a DC/OS cluster.
"""

import json
import sys
import tempfile
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Tuple

import click
from passlib.hash import sha512_crypt

from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster
from dcos_e2e_cli._vendor.dcos_installer_tools import DCOSVariant
from dcos_e2e_cli.common.arguments import artifact_argument
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
    get_variant,
    install_dcos_from_path,
    set_logging,
    show_cluster_started_message,
)

from ._common import (
    CLUSTER_ID_DESCRIPTION_KEY,
    VARIANT_DESCRIPTION_KEY,
    VARIANT_ENTERPRISE_DESCRIPTION_VALUE,
    VARIANT_OSS_DESCRIPTION_VALUE,
    WORKSPACE_DIR_DESCRIPTION_KEY,
    existing_cluster_ids,
)
from .wait import wait


@click.command('create')
@artifact_argument
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
@click.pass_context
def create(
    ctx: click.core.Context,
    agents: int,
    artifact: str,
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

    doctor_message = 'Try `minidcos vagrant doctor` for troubleshooting help.'

    artifact_path = Path(artifact).resolve()

    dcos_variant = {
        'auto':
        get_variant(
            artifact_path=artifact_path,
            workspace_dir=workspace_dir,
            doctor_message=doctor_message,
        ),
        'oss':
        DCOSVariant.OSS,
        'enterprise':
        DCOSVariant.ENTERPRISE,
    }[variant]

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
    if dcos_variant == DCOSVariant.ENTERPRISE:
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

    try:
        cluster = Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(doctor_message)
        sys.exit(exc.returncode)

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

    install_dcos_from_path(
        cluster=cluster,
        dcos_config={
            **cluster.base_config,
            **extra_config,
        },
        ip_detect_path=ip_detect_path,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
    )

    show_cluster_started_message(
        # We work on the assumption that the ``wait`` command is a sibling
        # command of this one.
        sibling_ctx=ctx,
        wait_command=wait,
        cluster_id=cluster_id,
    )

    click.echo(cluster_id)

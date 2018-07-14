"""
Tools for creating a DC/OS cluster.
"""

import json
import sys
import tempfile
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict, List, Optional, Set, Tuple

import click
import click_spinner
from passlib.hash import sha512_crypt

from cli._vendor import vertigo_py
from cli.common.options import (
    agents_option,
    artifact_argument,
    copy_to_master_option,
    extra_config_option,
    license_key_option,
    make_cluster_id_option,
    masters_option,
    public_agents_option,
    security_mode_option,
    variant_option,
    workspace_dir_option,
)
from cli.common.utils import get_variant
from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster

CLUSTER_ID_DESCRIPTION_KEY = 'dcos_e2e.cluster_id'


def _description_from_vm_name(vm_name: str) -> str:
    """
    Given the name of a VirtualBox VM, return its description.
    """
    virtualbox_vm = vertigo_py.VM(name=vm_name)  # type: ignore
    info = virtualbox_vm.parse_info()  # type: Dict[str, str]
    escaped_description = info.get('description', '')
    description = escaped_description.encode().decode('unicode_escape')
    return description


def existing_cluster_ids() -> Set[str]:
    ls_output = vertigo_py.ls()  # type: ignore
    vm_ls_output = ls_output['vms']
    lines = vm_ls_output.decode().strip().split('\n')
    lines = [line for line in lines if line]
    cluster_ids = set()
    for line in lines:
        vm_name_in_quotes, _ = line.split(' ')
        vm_name = vm_name_in_quotes[1:-1]
        description = _description_from_vm_name(vm_name=vm_name)
        try:
            data = json.loads(s=description)
        except json.decoder.JSONDecodeError:
            continue

        cluster_id = data.get(CLUSTER_ID_DESCRIPTION_KEY)
        cluster_ids.add(cluster_id)

    return cluster_ids - set([None])


@click.command('create')
@artifact_argument
@masters_option
@agents_option
@extra_config_option
@public_agents_option
@workspace_dir_option
@variant_option
@license_key_option
@security_mode_option
@copy_to_master_option
@make_cluster_id_option(existing_cluster_ids_func=existing_cluster_ids)
def create(
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
    base_workspace_dir = workspace_dir or Path(tempfile.gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex
    workspace_dir.mkdir(parents=True)

    description = {
        CLUSTER_ID_DESCRIPTION_KEY: cluster_id,
    }
    cluster_backend = Vagrant(
        workspace_dir=workspace_dir,
        virtualbox_description=json.dumps(obj=description),
    )
    doctor_message = 'Try `dcos-vagrant doctor` for troubleshooting help.'

    artifact_path = Path(artifact).resolve()

    if variant == 'auto':
        variant = get_variant(
            artifact_path=artifact_path,
            workspace_dir=workspace_dir,
            doctor_message=doctor_message,
        )

    enterprise = bool(variant == 'enterprise')
    if enterprise:
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
            files_to_copy_to_installer=[],
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(doctor_message)
        sys.exit(exc.returncode)

    for node in cluster.masters:
        for path_pair in copy_to_master:
            local_path, remote_path = path_pair
            node.send_file(
                local_path=local_path,
                remote_path=remote_path,
            )

    try:
        with click_spinner.spinner():
            cluster.install_dcos_from_path(
                build_artifact=artifact_path,
                dcos_config={
                    **cluster.base_config,
                    **extra_config,
                },
            )
    except CalledProcessError as exc:
        click.echo('Error installing DC/OS.', err=True)
        click.echo(doctor_message)
        cluster.destroy()
        sys.exit(exc.returncode)

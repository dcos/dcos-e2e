"""
A CLI for controlling DC/OS clusters on Docker.
"""

import json
import logging
import re
import subprocess
import uuid
from pathlib import Path
from shutil import rmtree
from subprocess import CalledProcessError
from tempfile import gettempdir
from typing import Any, Dict, List, Optional, Set, Union  # noqa: F401

import click
import docker
import yaml
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docker.models.containers import Container
from passlib.hash import sha512_crypt

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion

logging.disable(logging.WARNING)

_LINUX_DISTRIBUTIONS = {
    'centos-7': Distribution.CENTOS_7,
    'ubuntu-16.04': Distribution.UBUNTU_16_04,
    'coreos': Distribution.COREOS,
    'fedora-23': Distribution.FEDORA_23,
    'debian-8': Distribution.DEBIAN_8,
}

_DOCKER_VERSIONS = {
    '1.13.1': DockerVersion.v1_13_1,
    '1.11.2': DockerVersion.v1_11_2,
}

_DOCKER_STORAGE_DRIVERS = {
    'aufs': DockerStorageDriver.AUFS,
    'overlay': DockerStorageDriver.OVERLAY,
    'overlay2': DockerStorageDriver.OVERLAY_2,
}

_CLUSTER_ID_LABEL_KEY = 'dcos_e2e.cluster_id'
_WORKSPACE_DIR_LABEL_KEY = 'dcos_e2e.workspace_dir'
_VARIANT_LABEL_KEY = 'dcos_e2e.variant'


def _write_key_pair(public_key_path: Path, private_key_path: Path) -> None:
    """
    Write an RSA key pair for connecting to nodes via SSH.

    Args:
        public_key_path: Path to write public key to.
        private_key_path: Path to a private key file to write.
    """
    # TODO move this function to dcos_e2e.common
    rsa_key_pair = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048,
    )

    public_key = rsa_key_pair.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH,
    )

    private_key = rsa_key_pair.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_path.write_bytes(data=public_key)
    private_key_path.write_bytes(data=private_key)


class _InspectView:
    def __init__(self, container: Container) -> None:
        self._container = container

    def to_dict(self) -> Dict[str, str]:
        return {'docker_container_name': self._container.name}


def _existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    client = docker.from_env(version='auto')
    filters = {'label': _CLUSTER_ID_LABEL_KEY}
    containers = client.containers.list(filters=filters)
    return set(
        [container.labels[_CLUSTER_ID_LABEL_KEY] for container in containers]
    )


def _validate_dcos_configuration(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Union[int, bool, str],
) -> Dict[str, Any]:
    """
    Validate that a given value is a YAML map.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    try:
        return dict(yaml.load(str(value)) or {})
    except ValueError:
        message = '"{value}" is not a valid DC/OS configuration'.format(
            value=value,
        )
    except yaml.YAMLError:
        message = '"{value}" is not valid YAML'.format(value=value)

    raise click.BadParameter(message=message)


def _validate_cluster_id(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Union[int, bool, str],
) -> str:
    """
    Validate that a given value is a YAML map.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value in _existing_cluster_ids():
        message = 'A cluster with the id "{value}" already exists'.format(
            value=value,
        )
        raise click.BadParameter(message=message)

    # This matches the Docker ID regular expression.
    # This regular expression can be seen by running:
    # > docker run -it --rm --id=' WAT ? I DUNNO ! ' alpine
    if not re.fullmatch('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', str(value)):
        message = (
            'Invalid cluster id "{value}", only [a-zA-Z0-9][a-zA-Z0-9_.-] '
            'are allowed and the cluster id cannoy be empty'
        ).format(value=value)
        raise click.BadParameter(message)

    return str(value)


def _validate_cluster_exists(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Union[int, bool, str],
) -> str:
    """
    Validate that a cluster exists with the given name.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    cluster_id = str(value)
    if cluster_id not in _existing_cluster_ids():
        message = 'Cluster "{value}" does not exist'.format(value=value)
        raise click.BadParameter(message)

    return cluster_id


def _is_enterprise(build_artifact: Path) -> bool:
    """
    Return whether the build artifact is an Enterprise artifact.
    """
    get_version_args = [
        'bash',
        str(build_artifact),
        '--version',
    ]
    result = subprocess.check_output(args=get_version_args)
    version_info = json.loads(result)
    variant = version_info['variant']
    return bool(variant == 'ee')


@click.group()
def dcos_docker() -> None:
    """
    Manage DC/OS clusters on Docker.
    """


@dcos_docker.command('create')
@click.argument('artifact', type=click.Path(exists=True))
@click.option(
    '--docker-version',
    type=click.Choice(_DOCKER_VERSIONS.keys()),
    default='1.13.1',
    show_default=True,
    help='The Docker version to install on the nodes.',
)
@click.option(
    '--linux-distribution',
    type=click.Choice(_LINUX_DISTRIBUTIONS.keys()),
    default='centos-7',
    show_default=True,
    help='The Linux distribution to use on the nodes.',
)
@click.option(
    '--docker-storage-driver',
    type=click.Choice(_DOCKER_STORAGE_DRIVERS.keys()),
    default=None,
    show_default=False,
    help=(
        'The storage driver to use for Docker in Docker. '
        'By default this uses the host\'s driver.'
    ),
)
@click.option(
    '--masters',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of master nodes.'
)
@click.option(
    '--agents',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of agent nodes.'
)
@click.option(
    '--public-agents',
    type=click.INT,
    default=1,
    show_default=True,
    help='The number of public agent nodes.'
)
@click.option(
    '--extra-config',
    type=str,
    default='{}',
    callback=_validate_dcos_configuration,
    help='Extra DC/OS configuration YAML to add to a default configuration.'
)
@click.option(
    '--cluster-id',
    type=str,
    default=uuid.uuid4().hex,
    callback=_validate_cluster_id,
    help='A unique identifier for the cluster. Defaults to a random value.',
)
@click.option(
    '--license-key-path',
    type=click.Path(exists=True),
    envvar='DCOS_LICENSE_KEY_PATH',
    help='If using DC/OS Enterprise, this defaults',
)
def create(
    agents: int,
    artifact: str,
    cluster_id: str,
    docker_storage_driver: str,
    docker_version: str,
    extra_config: Dict[str, Any],
    linux_distribution: str,
    masters: int,
    public_agents: int,
    license_key_path: str,
) -> None:
    """
    Create a DC/OS cluster.

        DC/OS Enterprise

            DC/OS Enterprise clusters require different configuration variables to DC/OS OSS.
            For example, enterprise clusters require the following configuration parameters:

            * `superuser_username`
            * `superuser_password_hash`
            * `fault_domain_enabled`
            * `license_key_contents`

            These can all be set in `extra_config`.
            However, some defaults are provided for all but the license key.

            The default superuser username is `admin`.
            The default superuser password is `admin`.

            The default `fault_domain_enabled` is `false`.

            `license_key_contents` must be set for DC/OS Enterprise 1.11 and above.
            This is set to one of the following, in order:

            * The `license_key_contents` set in `extra_config`.
            * The contents of the path given with `--license-key-path`.
            * The contents of the path set in the `DCOS_LICENSE_KEY_PATH` environment variable.

            If none of these are set, `license_key_contents` is not given.
    """
    custom_master_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_agent_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_public_agent_mounts = {}  # type: Dict[str, Dict[str, str]]

    workspace_dir = Path(gettempdir()) / uuid.uuid4().hex
    ssh_keypair_dir = workspace_dir / 'ssh'
    ssh_keypair_dir.mkdir(parents=True)
    _write_key_pair(
        public_key_path=ssh_keypair_dir / 'id_rsa.pub',
        private_key_path=ssh_keypair_dir / 'id_rsa',
    )

    enterprise = _is_enterprise(build_artifact=Path(artifact))

    if enterprise:
        superuser_username = 'admin'
        superuser_password = 'admin'

        enterprise_extra_config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
        }

        if license_key_path is not None:
            key_contents = Path(license_key_path).read_text()
            enterprise_extra_config['license_key_contents'] = key_contents

        extra_config = {**enterprise_extra_config, **extra_config}

    cluster_backend = Docker(
        custom_master_mounts=custom_master_mounts,
        custom_agent_mounts=custom_agent_mounts,
        custom_public_agent_mounts=custom_public_agent_mounts,
        linux_distribution=_LINUX_DISTRIBUTIONS[linux_distribution],
        docker_version=_DOCKER_VERSIONS[docker_version],
        ssh_keypair_dir=ssh_keypair_dir,
        storage_driver=_DOCKER_STORAGE_DRIVERS.get(docker_storage_driver),
        docker_container_labels={
            _CLUSTER_ID_LABEL_KEY: cluster_id,
            _WORKSPACE_DIR_LABEL_KEY: str(workspace_dir),
            _VARIANT_LABEL_KEY: 'ee' if enterprise else '',
        },
        workspace_dir=workspace_dir,
    )

    cluster = Cluster(
        cluster_backend=cluster_backend,
        masters=masters,
        agents=agents,
        public_agents=public_agents,
    )

    try:
        cluster.install_dcos_from_path(
            build_artifact=Path(artifact),
            extra_config=extra_config,
        )
    except CalledProcessError:
        cluster.destroy()
        return

    click.echo(cluster_id)


@dcos_docker.command('list')
def list_clusters() -> None:
    """
    List all clusters.
    """
    for cluster_id in _existing_cluster_ids():
        click.echo(cluster_id)


@dcos_docker.command('destroy')
@click.argument(
    'cluster_ids',
    nargs=-1,
    type=str,
)
def destroy(cluster_ids: List[str]) -> None:
    """
    Destroy clusters.

    This takes >= 1 cluster IDs.
    To destroy all clusters, run:

    dcos_docker destroy $(dcos_docker list)
    """
    client = docker.from_env(version='auto')

    for cluster_id in cluster_ids:
        if cluster_id not in _existing_cluster_ids():
            warning = 'Cluster "{cluster_id}" does not exist'.format(
                cluster_id=cluster_id,
            )
            click.echo(warning, err=True)
            continue

        cluster_containers = _ClusterContainers(cluster_id=cluster_id)
        containers = {
            *cluster_containers.masters,
            *cluster_containers.agents,
            *cluster_containers.public_agents,
        }
        containers = client.containers.list(filters=filters)
        rmtree(path=str(cluster_containers.workspace_dir), ignore_errors=True)
        for container in containers:
            container.remove(v=True, force=True)

        click.echo(cluster_id)


class _ClusterContainers:
    """
    XXX
    """

    def __init__(self, cluster_id: str) -> None:
        self._cluster_id_label = _CLUSTER_ID_LABEL_KEY + '=' + cluster_id

    def _containers_by_node_type(
        self,
        node_type: str,
    ) -> Set[Container]:
        """
        XXX
        """
        client = docker.from_env(version='auto')
        filters = {
            'label': [
                self._cluster_id_label,
                'node_type={node_type}'.format(node_type=node_type),
            ],
        }
        return set(client.containers.list(filters=filters))

    @property
    def masters(self) -> Set[Container]:
        """
        XXX
        """
        return self._containers_by_node_type(node_type='master')

    @property
    def agents(self) -> Set[Container]:
        """
        XXX
        """
        return self._containers_by_node_type(node_type='agent')

    @property
    def public_agents(self) -> Set[Container]:
        """
        XXX
        """
        return self._containers_by_node_type(node_type='public_agent')

    @property
    def is_ee(self) -> bool:
        """
        XXXX
        """
        master_container = next(iter(self.masters))
        return bool(master_container.labels[_VARIANT_LABEL_KEY] == 'ee')

    @property
    def cluster(self) -> Cluster:
        workspace_dir / 'ssh'

    @property
    def workspace_dir(self) -> Path:
        container = next(iter(self.masters))
        workspace_dir = container.labels[_WORKSPACE_DIR_LABEL_KEY]
        return Path(workspace_dir)


@dcos_docker.command('wait')
@click.argument('cluster_id', type=str, callback=_validate_cluster_exists)
@click.option('--superuser-username', type=str)
@click.option('--superuser-password', type=str)
def wait(
    cluster_id: str,
    superuser_username: Optional[str],
    superuser_password: Optional[str],
) -> None:
    """
    If Enterprise, uses admin admin like the default...
    """
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)

    if not cluster_containers.is_ee:
        if superuser_username or superuser_password:
            message = (
                '`--superuser-username` and `--superuser-password` must not '
                'be set for an open source DC/OS cluster.'
            )
            raise click.BadOptionUsage(message=message)

        cluster_containers.cluster.wait_for_dcos_oss()

    superuser_username = superuser_username or 'admin'
    superuser_password = superuser_password or 'admin'

    if cluster_containers.is_ee:
        cluster_containers.cluster.wait_for_dcos_ee(
            superuser_username=superuser_username or 'admin',
            superuser_password=superuser_password or 'admin',
        )


@dcos_docker.command('inspect')
@click.argument('cluster_id', type=str, callback=_validate_cluster_exists)
@click.option(
    '--env',
    is_flag=True,
    help='Show details in an environment variable format to eval.',
)
def inspect_cluster(cluster_id: str, env: bool) -> None:
    """
    Show cluster details.
    """
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)

    if env:
        prefixes = {
            'MASTER': cluster_containers.masters,
            'AGENT': cluster_containers.agents,
            'PUBLIC_AGENT': cluster_containers.public_agents,
        }
        for prefix, containers in prefixes.items():
            for index, container in enumerate(containers):
                message = 'export {prefix}_{index}={container_id}'.format(
                    prefix=prefix,
                    index=index,
                    container_id=container.id,
                )
                click.echo(message)
        return

    keys = {
        'masters': cluster_containers.masters,
        'agents': cluster_containers.agents,
        'public_agents': cluster_containers.public_agents,
    }

    nodes = {
        key: [_InspectView(container).to_dict() for container in containers]
        for key, containers in keys.items()
    }

    # DC/OS version (e.g. Enterprise 1.11)?
    master = next(iter(cluster_containers.masters))
    web_ui = 'http://' + master.attrs['NetworkSettings']['IPAddress']

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True)
    )


if __name__ == '__main__':
    dcos_docker()

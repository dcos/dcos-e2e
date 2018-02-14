"""
A CLI for controlling DC/OS clusters on Docker.

Ideas for improvements
----------------------

$ dcos_docker doctor
Not enough RAM allocated to Docker
Docker for Mac network not set up

* Sync bootstrap dir in sync
* Handle Custom CA Cert case, with mounts
* Customizable logging system
* Create a cluster, destroy a cluster, there are dangling volumes, why?
* Does wait for OSS work?
* Use a `default` name if there exist no cluster IDs?
* Describe this in README
* Genconf in checkout

* Add --sync flag to run which uses env var for checkout location
* Add sync to docs
* Add tests for sync
* Run - use username and password from options
* Idea for default - if you use the word "default" this returns the one and only one cluster
    - or maybe if no Cluster ID uses the one cluster, if there is only one
* Default checkout dir = .
"""

import io
import json
import logging
import os
import re
import subprocess
import tarfile
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from subprocess import CalledProcessError
from tempfile import gettempdir
from typing import (  # noqa: F401
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import click
import click_spinner
import docker
import urllib3
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
from dcos_e2e.node import Node

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
    help=(
        'This is ignored if using open source DC/OS. '
        'If using DC/OS Enterprise, this defaults to the value of the '
        '`DCOS_LICENSE_KEY_PATH` environment variable.'
    ),
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

            \b
            DC/OS Enterprise clusters require different configuration variables to DC/OS OSS.
            For example, enterprise clusters require the following configuration parameters:

            ``superuser_username``, ``superuser_password_hash``, ``fault_domain_enabled``, ``license_key_contents``

            \b
            These can all be set in ``extra_config``.
            However, some defaults are provided for all but the license key.

            \b
            The default superuser username is ``admin``.
            The default superuser password is ``admin``.
            The default ``fault_domain_enabled`` is ``false``.

            \b
            ``license_key_contents`` must be set for DC/OS Enterprise 1.11 and above.
            This is set to one of the following, in order:

            \b
            * The ``license_key_contents`` set in ``extra_config``.
            * The contents of the path given with ``--license-key-path``.
            * The contents of the path set in the ``DCOS_LICENSE_KEY_PATH`` environment variable.

            \b
            If none of these are set, ``license_key_contents`` is not given.
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
        with click_spinner.spinner():
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

    To destroy all clusters, run ``dcos_docker destroy $(dcos_docker list)``.
    """
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
        rmtree(path=str(cluster_containers.workspace_dir), ignore_errors=True)
        for container in containers:
            container.stop()
            container.remove(v=True)

        click.echo(cluster_id)


class _ClusterContainers:
    """
    A representation of a cluster constructed from Docker nodes.
    """

    def __init__(self, cluster_id: str) -> None:
        """
        Args:
            cluster_id: The ID of the cluster.
        """
        self._cluster_id_label = _CLUSTER_ID_LABEL_KEY + '=' + cluster_id

    def _containers_by_node_type(
        self,
        node_type: str,
    ) -> Set[Container]:
        """
        Return all containers in this cluster of a particular node type.
        """
        client = docker.from_env(version='auto')
        filters = {
            'label': [
                self._cluster_id_label,
                'node_type={node_type}'.format(node_type=node_type),
            ],
        }
        return set(client.containers.list(filters=filters))

    def _to_node(self, container: Container) -> Node:
        address = IPv4Address(container.attrs['NetworkSettings']['IPAddress'])
        ssh_key_path = self.workspace_dir / 'ssh' / 'id_rsa'
        return Node(
            public_ip_address=address,
            private_ip_address=address,
            ssh_key_path=ssh_key_path,
        )

    @property
    def masters(self) -> Set[Container]:
        """
        Docker containers which represent master nodes.
        """
        return self._containers_by_node_type(node_type='master')

    @property
    def agents(self) -> Set[Container]:
        """
        Docker containers which represent agent nodes.
        """
        return self._containers_by_node_type(node_type='agent')

    @property
    def public_agents(self) -> Set[Container]:
        """
        Docker containers which represent public agent nodes.
        """
        return self._containers_by_node_type(node_type='public_agent')

    @property
    def is_enterprise(self) -> bool:
        """
        Return whether the cluster is a DC/OS Enterprise cluster.
        """
        master_container = next(iter(self.masters))
        return bool(master_container.labels[_VARIANT_LABEL_KEY] == 'ee')

    @property
    def cluster(self) -> Cluster:
        """
        Return a ``Cluster`` constructed from the containers.
        """
        return Cluster.from_nodes(
            masters=set(map(self._to_node, self.masters)),
            agents=set(map(self._to_node, self.agents)),
            public_agents=set(map(self._to_node, self.public_agents)),
            default_ssh_user='root',
        )

    @property
    def workspace_dir(self) -> Path:
        container = next(iter(self.masters))
        workspace_dir = container.labels[_WORKSPACE_DIR_LABEL_KEY]
        return Path(workspace_dir)


@dcos_docker.command('wait')
@click.argument('cluster_id', type=str, callback=_validate_cluster_exists)
@click.option(
    '--superuser-username',
    type=str,
    help=(
        'The superuser username is needed only on DC/OS Enterprise clusters. '
        'By default, on a DC/OS Enterprise cluster, `admin` is used.'
    ),
)
@click.option(
    '--superuser-password',
    type=str,
    help=(
        'The superuser password is needed only on DC/OS Enterprise clusters. '
        'By default, on a DC/OS Enterprise cluster, `admin` is used.'
    ),
)
def wait(
    cluster_id: str,
    superuser_username: Optional[str],
    superuser_password: Optional[str],
) -> None:
    """
    Wait for DC/OS to start.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)

    if not cluster_containers.is_enterprise:
        if superuser_username or superuser_password:
            message = (
                '`--superuser-username` and `--superuser-password` must not '
                'be set for an open source DC/OS cluster.'
            )
            raise click.BadOptionUsage(message=message)

        with click_spinner.spinner():
            cluster_containers.cluster.wait_for_dcos_oss()

    superuser_username = superuser_username or 'admin'
    superuser_password = superuser_password or 'admin'

    if cluster_containers.is_enterprise:
        with click_spinner.spinner():
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

    To quickly get environment variables to use with Docker tooling, use the
    ``--env`` flag.

    Run ``eval (dcos_docker inspect <CLUSTER_ID> --env)``, then run
    ``docker exec -it $MASTER_0`` to enter the first master, for example.
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


@dcos_docker.command('run', context_settings=dict(ignore_unknown_options=True))
@click.argument('cluster_id', type=str, callback=_validate_cluster_exists)
@click.argument('node_args', type=str, nargs=-1)
@click.option(
    '--sync',
    is_flag=True,
    help='XXX',
)
@click.pass_context
def run(
    ctx: click.core.Context, cluster_id: str, node_args: Tuple[str],
    sync: Optional[str],
) -> None:
    """
    Run an arbitrary command on a node.

    This command sets up the environment so that ``pytest`` can be run.

    For example, run ``dcos_docker run 1231599 pytest -k test_tls.py``.
    """
    if sync is not None:
        checkout = os.environ['DCOS_CHECKOUT_PATH']
        ctx.invoke(sync_code, cluster_id=cluster_id, checkout=checkout)

    args = [
        'source',
        '/opt/mesosphere/environment.export',
        '&&',
        'cd',
        '/opt/mesosphere/active/dcos-integration-test/',
        '&&',
    ] + list(node_args)

    def ip_addresses(nodes: Iterable[Node]) -> str:
        return ','.join(map(lambda node: str(node.public_ip_address), nodes))

    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    cluster = cluster_containers.cluster

    environment = {
        'MASTER_HOSTS': ip_addresses(cluster.masters),
        'SLAVE_HOSTS': ip_addresses(cluster.agents),
        'PUBLIC_SLAVE_HOSTS': ip_addresses(cluster.public_agents),
        'DCOS_LOGIN_UNAME': 'admin',
        'DCOS_LOGIN_PW': 'admin',
    }

    docker_env_vars = []
    for key, value in environment.items():
        docker_env_vars.append('-e')
        docker_env_vars.append('{key}={value}'.format(key=key, value=value))

    master = next(iter(cluster_containers.masters))
    system_cmd = [
        'docker',
        'exec',
        '-it',
    ] + docker_env_vars + [
        master.id,
        '/bin/bash',
        '-c',
        '"{args}"'.format(args=' '.join(args)),
    ]

    joined = ' '.join(system_cmd)
    os.system(joined)


def tar_with_filter(
    path: Path,
    filter: Callable[[tarfile.TarInfo], Optional[tarfile.TarInfo]],
) -> io.BytesIO:

    tarstream = io.BytesIO()
    with tarfile.TarFile(fileobj=tarstream, mode='w') as tar:
        tar.add(name=str(path), arcname='/', filter=filter)
    tarstream.seek(0)

    return tarstream


def cache_filter(tar_info: tarfile.TarInfo) -> Optional[tarfile.TarInfo]:
    if '__pycache__' in tar_info.name:
        return None
    if tar_info.name.endswith('.pyc'):
        return None
    return tar_info


@dcos_docker.command('sync')
@click.argument('cluster_id', type=str, callback=_validate_cluster_exists)
@click.argument(
    'checkout',
    type=click.Path(exists=True),
    envvar='DCOS_CHECKOUT_PATH',
)
def sync_code(cluster_id: str, checkout: str) -> None:
    """
    Sync files from a DC/OS checkout to master nodes.

    This syncs integration test files and bootstrap files.

    ``checkout`` should be set to the path of clone of an open source DC/OS
    or DC/OS Enterprise repository.

    By default the ``checkout`` argument is set to the value of the
    ``DCOS_CHECKOUT_PATH`` environment variable.
    """
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    cluster = cluster_containers.cluster
    node_active_dir = Path('/opt/mesosphere/active')
    node_test_dir = node_active_dir / 'dcos-integration-test'
    node_bootstrap_dir = (
        node_active_dir / 'bootstrap' / 'lib' /
        'python3.6/site-packages/dcos_internal_utils/'
    )

    local_packages = Path(checkout) / 'packages'
    local_test_dir = local_packages / 'dcos-integration-test' / 'extra'
    local_bootstrap_dir = local_packages / 'bootstrap' / 'extra' / 'dcos_internal_utils'

    node_test_py_pattern = node_test_dir / '*.py'
    for master in cluster.masters:
        master.run(
            args=['rm', '-rf', str(node_test_py_pattern)],
            user=cluster.default_ssh_user,
            shell=True,
        )

    test_tarstream = tar_with_filter(
        path=local_test_dir,
        filter=cache_filter,
    )
    bootstrap_tarstream = tar_with_filter(
        path=local_bootstrap_dir,
        filter=cache_filter,
    )
    for master_container in cluster_containers.masters:
        master_container.put_archive(
            path=str(node_test_dir),
            data=test_tarstream,
        )

        master_container.put_archive(
            path=str(node_bootstrap_dir),
            data=bootstrap_tarstream,
        )


if __name__ == '__main__':
    dcos_docker()

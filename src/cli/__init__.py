"""
A CLI for controlling DC/OS clusters on Docker.

Ideas for improvements
----------------------

* Handle Custom CA Cert case, with mounts (and copy to installer)
* brew install
* Windows support
* Refactor (key creation common)
* Check if this works you're on old Docker machine - if not, add to requirements
* Make sync_code use send_file and then untar
"""

import io
import json
import logging
import os
import re
import shutil
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
    """
    Details of a node to show in the inspect view.
    """

    def __init__(self, container: Container) -> None:
        """
        Args:
            container: The Docker container which represents the node.
        """
        self._container = container

    def to_dict(self) -> Dict[str, str]:
        """
        Return dictionary with information to be shown to users.
        """
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
    Validate that a given value is a file containing a YAML map.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value is None:
        return {}

    content = Path(str(value)).read_text()

    try:
        return dict(yaml.load(content) or {})
    except ValueError:
        message = '"{content}" is not a valid DC/OS configuration'.format(
            content=content,
        )
    except yaml.YAMLError:
        message = '"{content}" is not valid YAML'.format(content=content)

    raise click.BadParameter(message=message)


def _validate_cluster_id(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
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
            'are allowed and the cluster ID cannot be empty.'
        ).format(value=value)
        raise click.BadParameter(message)

    return str(value)


def _validate_cluster_exists(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> str:
    """
    Validate that a cluster exists with the given name.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value is None:
        if 'default' in _existing_cluster_ids():
            return 'default'
        message = '--cluster-id was not given and no cluster "default" exists'
        raise click.BadParameter(message)

    cluster_id = str(value)
    if cluster_id not in _existing_cluster_ids():
        message = 'Cluster "{value}" does not exist'.format(value=value)
        raise click.BadParameter(message)

    return cluster_id


def _is_enterprise(build_artifact: Path, workspace_dir: Path) -> bool:
    """
    Return whether the build artifact is an Enterprise artifact.
    """
    get_version_args = [
        'bash',
        str(build_artifact),
        '--version',
    ]
    result = subprocess.check_output(
        args=get_version_args,
        cwd=str(workspace_dir),
    )
    version_info = json.loads(result.decode())
    variant = version_info['variant']
    return bool(variant == 'ee')


def _set_logging(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> None:
    """
    Set logging level depending on the chosen verbosity.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    value = min(value, 2)
    value = max(value, 0)
    verbosity_map = {
        0: logging.WARNING,
        1: logging.DEBUG,
        2: logging.INFO,
    }
    logging.disable(verbosity_map[int(value or 0)])


@click.option(
    '-v',
    '--verbose',
    count=True,
    callback=_set_logging,
)
@click.group()
def dcos_docker(verbose: None) -> None:
    """
    Manage DC/OS clusters on Docker.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (verbose, ):
        pass


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
    '-c',
    '--cluster-id',
    type=str,
    default=uuid.uuid4().hex,
    callback=_validate_cluster_id,
    help=(
        'A unique identifier for the cluster. '
        'Defaults to a random value. '
        'Use the value "default" to use this cluster for other'
    ),
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
    license_key_path: Optional[str],
    security_mode: Optional[str],
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
    public_key_path = ssh_keypair_dir / 'id_rsa.pub'
    private_key_path = ssh_keypair_dir / 'id_rsa'
    _write_key_pair(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
    )

    enterprise = _is_enterprise(
        build_artifact=Path(artifact),
        workspace_dir=workspace_dir,
    )

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
        if security_mode is not None:
            extra_config['security'] = security_mode

    cluster_backend = Docker(
        custom_master_mounts=custom_master_mounts,
        custom_agent_mounts=custom_agent_mounts,
        custom_public_agent_mounts=custom_public_agent_mounts,
        linux_distribution=_LINUX_DISTRIBUTIONS[linux_distribution],
        docker_version=_DOCKER_VERSIONS[docker_version],
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

    nodes = {
        *cluster.masters,
        *cluster.agents,
        *cluster.public_agents,
    }

    for node in nodes:
        node.run(
            args=['echo', '', '>>', '/root/.ssh/authorized_keys'],
            user=cluster.default_ssh_user,
            shell=True,
        )
        node.run(
            args=[
                'echo',
                public_key_path.read_text(),
                '>>',
                '/root/.ssh/authorized_keys',
            ],
            user=cluster.default_ssh_user,
            shell=True,
        )

    try:
        with click_spinner.spinner():
            cluster.install_dcos_from_path(
                build_artifact=Path(artifact),
                extra_config=extra_config,
            )
    except CalledProcessError as exc:
        click.echo('Error creating cluster:', err=True)
        click.echo(str(exc), err=True)
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

        client = docker.from_env(version='auto')
        client.volumes.prune()
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
@click.option(
    '-c',
    '--cluster-id',
    type=str,
    callback=_validate_cluster_exists,
    default=None,
    help='If not given, "default" is used.',
)
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
@click.option(
    '-c',
    '--cluster-id',
    type=str,
    callback=_validate_cluster_exists,
    default=None,
    help='If not given, "default" is used.',
)
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

    Run ``eval $(dcos_docker inspect <CLUSTER_ID> --env)``, then run
    ``docker exec -it $MASTER_0`` to enter the first master, for example.
    """
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    master = next(iter(cluster_containers.masters))
    web_ui = 'http://' + master.attrs['NetworkSettings']['IPAddress']

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
        click.echo('export WEB_UI={web_ui}'.format(web_ui=web_ui))
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

    data = {
        'Cluster ID': cluster_id,
        'Web UI': web_ui,
        'Nodes': nodes,
    }  # type: Dict[Any, Any]
    click.echo(
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True)
    )


@dcos_docker.command('run', context_settings=dict(ignore_unknown_options=True))
@click.option(
    '-c',
    '--cluster-id',
    type=str,
    callback=_validate_cluster_exists,
    default=None,
    help='If not given, "default" is used.',
)
@click.option(
    '--dcos-login-uname',
    type=str,
    default='admin',
    help='The username to set the ``DCOS_LOGIN_UNAME`` as.'
)
@click.option(
    '--dcos-login-pw',
    type=str,
    default='admin',
    help='The password to set the ``DCOS_LOGIN_PW`` as.'
)
@click.argument('node_args', type=str, nargs=-1)
@click.option(
    '--sync',
    is_flag=True,
    help=(
        'Syncs to DC/OS checkout specified in the ``DCOS_CHECKOUT_PATH`` '
        'environment variable before running the command. '
        'If the environment variable is not set, the current working '
        'directory is used.'
    ),
)
@click.pass_context
def run(
    ctx: click.core.Context,
    cluster_id: str,
    node_args: Tuple[str],
    sync: bool,
    dcos_login_uname: str,
    dcos_login_pw: str,
) -> None:
    """
    Run an arbitrary command on a node.

    This command sets up the environment so that ``pytest`` can be run.

    For example, run
    ``dcos_docker run --cluster-id 1231599 pytest -k test_tls.py``.

    Or, with sync:
    ``dcos_docker run --sync --cluster-id 1231599 pytest -k test_tls.py``.
    """
    if sync:
        checkout = os.environ.get('DCOS_CHECKOUT_PATH', '.')
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

    terminal_size = shutil.get_terminal_size()

    environment = {
        'MASTER_HOSTS': ip_addresses(cluster.masters),
        'SLAVE_HOSTS': ip_addresses(cluster.agents),
        'PUBLIC_SLAVE_HOSTS': ip_addresses(cluster.public_agents),
        'DCOS_LOGIN_UNAME': dcos_login_uname,
        'DCOS_LOGIN_PW': dcos_login_pw,
        # Without this we have display errors.
        # See https://github.com/moby/moby/issues/25450.
        'COLUMNS': terminal_size.columns,
        'LINES': terminal_size.lines,
        'TERM': os.environ['TERM'],
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


def _tar_with_filter(
    path: Path,
    tar_filter: Callable[[tarfile.TarInfo], Optional[tarfile.TarInfo]],
) -> io.BytesIO:
    """
    Return a tar of a files in a given directory, which are not filtered out
    by the ``filter``.
    """
    tarstream = io.BytesIO()
    with tarfile.TarFile(fileobj=tarstream, mode='w') as tar:
        tar.add(name=str(path), arcname='/', filter=tar_filter)
    tarstream.seek(0)

    return tarstream


def _cache_filter(tar_info: tarfile.TarInfo) -> Optional[tarfile.TarInfo]:
    """
    Filter for ``tarfile.TarFile.add`` which removes Python and pytest cache
    files.
    """
    if '__pycache__' in tar_info.name:
        return None
    if tar_info.name.endswith('.pyc'):
        return None
    return tar_info


@dcos_docker.command('web')
@click.option(
    '-c',
    '--cluster-id',
    type=str,
    callback=_validate_cluster_exists,
    default=None,
    help='If not given, "default" is used.',
)
def web(cluster_id: str) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``dcos_docker wait`` before running this command.
    """
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    master = next(iter(cluster_containers.masters))
    web_ui = 'http://' + master.attrs['NetworkSettings']['IPAddress']
    click.launch(web_ui)


@dcos_docker.command('sync')
@click.option(
    '-c',
    '--cluster-id',
    type=str,
    callback=_validate_cluster_exists,
    default=None,
    help='If not given, "default" is used.',
)
@click.argument(
    'checkout',
    type=click.Path(exists=True),
    envvar='DCOS_CHECKOUT_PATH',
    default='.',
)
def sync_code(cluster_id: str, checkout: str) -> None:
    """
    Sync files from a DC/OS checkout to master nodes.

    This syncs integration test files and bootstrap files.

    ``CHECKOUT`` should be set to the path of clone of an open source DC/OS
    or DC/OS Enterprise repository.

    By default the ``CHECKOUT`` argument is set to the value of the
    ``DCOS_CHECKOUT_PATH`` environment variable.

    If no ``CHECKOUT`` is given, the current working directory is used.
    """
    local_packages = Path(checkout) / 'packages'
    local_test_dir = local_packages / 'dcos-integration-test' / 'extra'
    if not local_test_dir.exists():
        message = (
            'CHECKOUT must be set to the checkout of a DC/OS repository.\n'
            '"{local_test_dir}" does not exist.'
        ).format(local_test_dir=local_test_dir)
        raise click.BadArgumentUsage(message=message)

    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    cluster = cluster_containers.cluster
    node_active_dir = Path('/opt/mesosphere/active')
    node_test_dir = node_active_dir / 'dcos-integration-test'
    node_lib_dir = node_active_dir / 'bootstrap' / 'lib'
    # Different versions of DC/OS have different versions of Python.
    master = next(iter(cluster.masters))
    ls_result = master.run(
        args=['ls', str(node_lib_dir)],
        user=cluster.default_ssh_user,
    )
    python_version = ls_result.stdout.decode().strip()
    node_python_dir = node_lib_dir / python_version
    node_bootstrap_dir = (
        node_python_dir / 'site-packages' / 'dcos_internal_utils'
    )

    local_bootstrap_dir = (
        local_packages / 'bootstrap' / 'extra' / 'dcos_internal_utils'
    )

    node_test_py_pattern = node_test_dir / '*.py'
    for master in cluster.masters:
        master.run(
            args=['rm', '-rf', str(node_test_py_pattern)],
            user=cluster.default_ssh_user,
            # We use a wildcard character, `*`, so we need shell expansion.
            shell=True,
        )

    test_tarstream = _tar_with_filter(
        path=local_test_dir,
        tar_filter=_cache_filter,
    )
    bootstrap_tarstream = _tar_with_filter(
        path=local_bootstrap_dir,
        tar_filter=_cache_filter,
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


def _info(message: str) -> None:
    """
    Show a warning message.
    """
    click.echo()
    click.echo(click.style('Note: ', fg='blue'), nl=False)
    click.echo(message)


def _warn(message: str) -> None:
    """
    Show a warning message.
    """
    click.echo()
    click.echo(click.style('Warning: ', fg='yellow'), nl=False)
    click.echo(message)


def _error(message: str) -> None:
    """
    Show an error message.
    """
    click.echo()
    click.echo(click.style('Error: ', fg='red'), nl=False)
    click.echo(message)


@dcos_docker.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    client = docker.from_env(version='auto')
    host_driver = client.info()['Driver']
    docker_for_mac = bool(client.info()['OperatingSystem'] == 'Docker for Mac')
    storage_driver_url = (
        'https://docs.docker.com/storage/storagedriver/select-storage-driver/'
    )
    if host_driver not in _DOCKER_STORAGE_DRIVERS:
        message = (
            "The host's Docker storage driver is \"{host_driver}\". "
            'We recommend that you use one of: {supported_drivers}. '
            'See {help_url}.'
        ).format(
            host_driver=host_driver,
            supported_drivers=', '.join(_DOCKER_STORAGE_DRIVERS.keys()),
            help_url=storage_driver_url,
        )
        _warn(message)

    if shutil.which('ssh') is None:
        _error(message='`ssh` must be available on your path.')

    ping_container = client.containers.run(
        image='alpine',
        tty=True,
        detach=True,
    )

    ping_container.reload()
    ip_address = ping_container.attrs['NetworkSettings']['IPAddress']

    try:
        subprocess.check_call(
            args=['ping', ip_address, '-c', '1', '-t', '1'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        message = 'Cannot connect to a Docker container by its IP address.'
        if docker_for_mac:
            message += (
                ' We recommend using '
                'https://github.com/wojas/docker-mac-network. '
            )
        _error(message=message)

    ping_container.stop()
    ping_container.remove(v=True)

    tmp_path = Path('/tmp').resolve()

    try:
        private_mount_container = client.containers.run(
            image='alpine',
            tty=True,
            detach=True,
            volumes={
                str(tmp_path): {
                    'bind': '/test',
                },
            },
        )
    except docker.errors.APIError as exc:
        message = (
            'There was an error mounting a the temporary directory path '
            '"{tmp_path}" in container: \n\n'
            '{exception_detail}'
        ).format(
            tmp_path=tmp_path,
            exception_detail=exc.explanation.decode(
                'ascii',
                'backslashreplace',
            ),
        )
        _error(message=message)
    else:
        private_mount_container.stop()
        private_mount_container.remove(v=True)

    docker_memory = client.info()['MemTotal']
    message = (
        'Docker has approximately {memory:.1f} GB of memory available. '
        'The amount of memory required depends on the workload. '
        'For example, creating large clusters or multiple clusters requires '
        'a lot of memory.\n'
        'A four node cluster seems to work well on a machine with 9 GB '
        'of memory available to Docker.'
    ).format(
        memory=docker_memory / 1024 / 1024 / 1024,
    )
    mac_message = (
        '\n'
        'To dedicate more memory to Docker for Mac, go to '
        'Docker > Preferences > Advanced.'
    )
    if docker_for_mac:
        message += mac_message

    _info(message=message)


if __name__ == '__main__':
    dcos_docker()

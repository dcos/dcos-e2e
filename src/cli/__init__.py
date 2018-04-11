"""
A CLI for controlling DC/OS clusters on Docker.
"""

import io
import json
import logging
import subprocess
import sys
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
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docker.models.containers import Container
from passlib.hash import sha512_crypt

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node

from ._common import (
    CLUSTER_ID_LABEL_KEY,
    DOCKER_STORAGE_DRIVERS,
    DOCKER_VERSIONS,
    LINUX_DISTRIBUTIONS,
    VARIANT_LABEL_KEY,
    WORKSPACE_DIR_LABEL_KEY,
    existing_cluster_ids,
)
from ._doctor_checks import (
    CheckLevels,
    check_1_9_sed,
    check_docker_root_free_space,
    check_memory,
    check_mount_tmp,
    check_networking,
    check_ssh,
    check_storage_driver,
    check_tmp_free_space,
    link_to_troubleshooting,
)
from ._utils import is_enterprise
from ._validators import (
    validate_cluster_exists,
    validate_cluster_id,
    validate_dcos_configuration,
    validate_path_is_directory,
    validate_path_pair,
)


def _existing_cluster_id_option(command: Callable[..., None],
                                ) -> Callable[..., None]:
    """
    An option decorator for one Cluster ID.
    """
    function = click.option(
        '-c',
        '--cluster-id',
        type=str,
        callback=validate_cluster_exists,
        default=None,
        help='If not given, "default" is used.',
    )(command)  # type: Callable[..., None]
    return function


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
@click.group(name='dcos-docker')
@click.version_option()
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
    type=click.Choice(sorted(DOCKER_VERSIONS.keys())),
    default='1.13.1',
    show_default=True,
    help='The Docker version to install on the nodes.',
)
@click.option(
    '--linux-distribution',
    type=click.Choice(sorted(LINUX_DISTRIBUTIONS.keys())),
    default='centos-7',
    show_default=True,
    help='The Linux distribution to use on the nodes.',
)
@click.option(
    '--docker-storage-driver',
    type=click.Choice(sorted(DOCKER_STORAGE_DRIVERS.keys())),
    default=None,
    show_default=False,
    help=(
        'The storage driver to use for Docker in Docker. '
        "By default this uses the host's driver."
    ),
)
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
    callback=validate_dcos_configuration,
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
    callback=validate_cluster_id,
    help=(
        'A unique identifier for the cluster. '
        'Defaults to a random value. '
        'Use the value "default" to use this cluster for other'
    ),
)
@click.option(
    '--license-key',
    type=click.Path(exists=True),
    envvar='DCOS_LICENSE_KEY_PATH',
    help=(
        'This is ignored if using open source DC/OS. '
        'If using DC/OS Enterprise, this defaults to the value of the '
        '`DCOS_LICENSE_KEY_PATH` environment variable.'
    ),
)
@click.option(
    '--genconf-dir',
    type=click.Path(exists=True),
    callback=validate_path_is_directory,
    help=(
        'Path to a directory that contains additional files for '
        'DC/OS installer. All files from this directory will be copied to the '
        '`genconf` directory before running DC/OS installer.'
    ),
)
@click.option(
    '--copy-to-master',
    type=str,
    callback=validate_path_pair,
    multiple=True,
    help=(
        'Files to copy to master nodes before installing DC/OS. '
        'This option can be given multiple times. '
        'Each option should be in the format '
        '/absolute/local/path:/remote/path.'
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
    license_key: Optional[str],
    security_mode: Optional[str],
    copy_to_master: List[Tuple[Path, Path]],
    genconf_dir: Optional[Path],
    workspace_dir: Optional[Path],
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
    custom_master_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_agent_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_public_agent_mounts = {}  # type: Dict[str, Dict[str, str]]

    base_workspace_dir = workspace_dir or Path(gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex

    doctor_message = 'Try `dcos-docker doctor` for troubleshooting help.'
    ssh_keypair_dir = workspace_dir / 'ssh'
    ssh_keypair_dir.mkdir(parents=True)
    public_key_path = ssh_keypair_dir / 'id_rsa.pub'
    private_key_path = ssh_keypair_dir / 'id_rsa'
    _write_key_pair(
        public_key_path=public_key_path,
        private_key_path=private_key_path,
    )

    artifact_path = Path(artifact).resolve()
    try:
        enterprise = is_enterprise(
            build_artifact=artifact_path,
            workspace_dir=workspace_dir,
        )
    except subprocess.CalledProcessError as exc:
        rmtree(path=str(workspace_dir), ignore_errors=True)
        click.echo(doctor_message)
        click.echo()
        click.echo('Original error:')
        click.echo(exc.stderr)
        raise

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

    files_to_copy_to_installer = []
    if genconf_dir is not None:
        container_genconf_path = Path('/genconf')
        for genconf_file in genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(genconf_dir)
            relative_path = container_genconf_path / genconf_relative
            files_to_copy_to_installer.append((genconf_file, relative_path))

    cluster_backend = Docker(
        custom_master_mounts=custom_master_mounts,
        custom_agent_mounts=custom_agent_mounts,
        custom_public_agent_mounts=custom_public_agent_mounts,
        linux_distribution=LINUX_DISTRIBUTIONS[linux_distribution],
        docker_version=DOCKER_VERSIONS[docker_version],
        storage_driver=DOCKER_STORAGE_DRIVERS.get(docker_storage_driver),
        docker_container_labels={
            CLUSTER_ID_LABEL_KEY: cluster_id,
            WORKSPACE_DIR_LABEL_KEY: str(workspace_dir),
            VARIANT_LABEL_KEY: 'ee' if enterprise else '',
        },
        docker_master_labels={'node_type': 'master'},
        docker_agent_labels={'node_type': 'agent'},
        docker_public_agent_labels={'node_type': 'public_agent'},
        workspace_dir=workspace_dir,
    )

    try:
        cluster = Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
            files_to_copy_to_installer=files_to_copy_to_installer,
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(doctor_message)
        sys.exit(exc.returncode)

    nodes = {
        *cluster.masters,
        *cluster.agents,
        *cluster.public_agents,
    }

    for node in nodes:
        node.run(
            args=['echo', '', '>>', '/root/.ssh/authorized_keys'],
            shell=True,
        )
        node.run(
            args=[
                'echo',
                public_key_path.read_text(),
                '>>',
                '/root/.ssh/authorized_keys',
            ],
            shell=True,
        )

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
                extra_config=extra_config,
            )
    except CalledProcessError as exc:
        click.echo('Error installing DC/OS.', err=True)
        click.echo(doctor_message)
        cluster.destroy()
        sys.exit(exc.returncode)

    click.echo(cluster_id)


@dcos_docker.command('list')
def list_clusters() -> None:
    """
    List all clusters.
    """
    for cluster_id in existing_cluster_ids():
        click.echo(cluster_id)


@dcos_docker.command('destroy-list')
@click.argument(
    'cluster_ids',
    nargs=-1,
    type=str,
)
@click.pass_context
def destroy_list(
    ctx: click.core.Context,
    cluster_ids: List[str],
) -> None:
    """
    Destroy clusters.

    To destroy all clusters, run ``dcos-docker destroy $(dcos-docker list)``.
    """
    for cluster_id in cluster_ids:
        if cluster_id not in existing_cluster_ids():
            warning = 'Cluster "{cluster_id}" does not exist'.format(
                cluster_id=cluster_id,
            )
            click.echo(warning, err=True)
            continue

        ctx.invoke(
            destroy,
            cluster_id=cluster_id,
        )


@dcos_docker.command('destroy')
@_existing_cluster_id_option
def destroy(cluster_id: str) -> None:
    """
    Destroy a cluster.
    """
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
        self._cluster_id_label = CLUSTER_ID_LABEL_KEY + '=' + cluster_id

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
            default_ssh_user='root',
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
        return bool(master_container.labels[VARIANT_LABEL_KEY] == 'ee')

    @property
    def cluster(self) -> Cluster:
        """
        Return a ``Cluster`` constructed from the containers.
        """
        return Cluster.from_nodes(
            masters=set(map(self._to_node, self.masters)),
            agents=set(map(self._to_node, self.agents)),
            public_agents=set(map(self._to_node, self.public_agents)),
        )

    @property
    def workspace_dir(self) -> Path:
        container = next(iter(self.masters))
        workspace_dir = container.labels[WORKSPACE_DIR_LABEL_KEY]
        return Path(workspace_dir)


@dcos_docker.command('wait')
@_existing_cluster_id_option
@click.option(
    '--superuser-username',
    type=str,
    default='admin',
    help=(
        'The superuser username is needed only on DC/OS Enterprise clusters. '
        'By default, on a DC/OS Enterprise cluster, `admin` is used.'
    ),
)
@click.option(
    '--superuser-password',
    type=str,
    default='admin',
    help=(
        'The superuser password is needed only on DC/OS Enterprise clusters. '
        'By default, on a DC/OS Enterprise cluster, `admin` is used.'
    ),
)
def wait(
    cluster_id: str,
    superuser_username: str,
    superuser_password: str,
) -> None:
    """
    Wait for DC/OS to start.
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    with click_spinner.spinner():
        if cluster_containers.is_enterprise:
            cluster_containers.cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )
            return

        cluster_containers.cluster.wait_for_dcos_oss()


@dcos_docker.command('inspect')
@_existing_cluster_id_option
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

    Run ``eval $(dcos-docker inspect <CLUSTER_ID> --env)``, then run
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
        json.dumps(data, indent=4, separators=(',', ': '), sort_keys=True),
    )


@dcos_docker.command('run', context_settings=dict(ignore_unknown_options=True))
@_existing_cluster_id_option
@click.option(
    '--dcos-login-uname',
    type=str,
    default='admin',
    help=(
        'The username to set the ``DCOS_LOGIN_UNAME`` environment variable to.'
    ),
)
@click.option(
    '--dcos-login-pw',
    type=str,
    default='admin',
    help=(
        'The password to set the ``DCOS_LOGIN_PW`` environment variable to.'
    ),
)
@click.argument('node_args', type=str, nargs=-1, required=True)
@click.option(
    '--sync-dir',
    type=click.Path(exists=True),
    help=(
        'The path to a DC/OS checkout. '
        'Part of this checkout will be synced before the command is run.'
    ),
    callback=validate_path_is_directory,
)
@click.option(
    '--no-test-env',
    is_flag=True,
    help=(
        'With this flag set, no environment variables are set and the command '
        'is run in the home directory. '
    ),
)
@click.pass_context
def run(
    ctx: click.core.Context,
    cluster_id: str,
    node_args: Tuple[str],
    sync_dir: Optional[Path],
    dcos_login_uname: str,
    dcos_login_pw: str,
    no_test_env: bool,
) -> None:
    """
    Run an arbitrary command on a node.

    This command sets up the environment so that ``pytest`` can be run.

    For example, run
    ``dcos-docker run --cluster-id 1231599 pytest -k test_tls.py``.

    Or, with sync:
    ``dcos-docker run --sync-dir . --cluster-id 1231599 pytest -k test_tls.py``.
    """  # noqa: E501
    if sync_dir is not None:
        ctx.invoke(
            sync_code,
            cluster_id=cluster_id,
            dcos_checkout_dir=str(sync_dir),
        )

    env = {
        'DCOS_LOGIN_UNAME': dcos_login_uname,
        'DCOS_LOGIN_PW': dcos_login_pw,
    }

    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    cluster = cluster_containers.cluster

    if no_test_env:
        try:
            test_host = next(iter(cluster.masters))

            test_host.run(
                args=list(node_args),
                log_output_live=False,
                tty=True,
                shell=True,
            )
        except subprocess.CalledProcessError as exc:
            sys.exit(exc.returncode)

        return

    try:
        cluster.run_integration_tests(
            pytest_command=list(node_args),
            tty=True,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


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
@_existing_cluster_id_option
def web(cluster_id: str) -> None:
    """
    Open the browser at the web UI.

    Note that the web UI may not be available at first.
    Consider using ``dcos-docker wait`` before running this command.
    """
    cluster_containers = _ClusterContainers(cluster_id=cluster_id)
    master = next(iter(cluster_containers.masters))
    web_ui = 'http://' + master.attrs['NetworkSettings']['IPAddress']
    click.launch(web_ui)


@dcos_docker.command('sync')
@_existing_cluster_id_option
@click.argument(
    'dcos_checkout_dir',
    type=click.Path(exists=True),
    envvar='DCOS_CHECKOUT_DIR',
    default='.',
)
def sync_code(cluster_id: str, dcos_checkout_dir: str) -> None:
    """
    Sync files from a DC/OS checkout to master nodes.

    This syncs integration test files and bootstrap files.

    ``DCOS_CHECKOUT_DIR`` should be set to the path of clone of an open source
    DC/OS or DC/OS Enterprise repository.

    By default the ``DCOS_CHECKOUT_DIR`` argument is set to the value of the
    ``DCOS_CHECKOUT_DIR`` environment variable.

    If no ``DCOS_CHECKOUT_DIR`` is given, the current working directory is
    used.
    """
    local_packages = Path(dcos_checkout_dir) / 'packages'
    local_test_dir = local_packages / 'dcos-integration-test' / 'extra'
    if not Path(local_test_dir).exists():
        message = (
            'DCOS_CHECKOUT_DIR must be set to the checkout of a DC/OS '
            'repository.\n'
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
    ls_result = master.run(args=['ls', str(node_lib_dir)])
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


@dcos_docker.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    check_functions = [
        check_1_9_sed,
        check_docker_root_free_space,
        check_memory,
        check_mount_tmp,
        check_networking,
        check_ssh,
        check_storage_driver,
        check_tmp_free_space,
    ]

    highest_level = max(function() for function in check_functions)

    link_to_troubleshooting()
    if highest_level == CheckLevels.ERROR:
        sys.exit(1)

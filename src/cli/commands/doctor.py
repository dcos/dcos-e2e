"""
Checks for showing up common sources of errors with the Docker backend.
"""

import shutil
import subprocess
import sys
import tempfile
from enum import IntEnum
from pathlib import Path
from tempfile import gettempdir, gettempprefix

import click
import docker

from cli._common import DOCKER_STORAGE_DRIVERS, docker_client
from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.docker_versions import DockerVersion


class _CheckLevels(IntEnum):
    """
    Levels of issues that a check can raise.
    """

    NONE = 1
    WARNING = 2
    ERROR = 3


def _info(message: str) -> None:
    """
    Show an info message.
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


def _check_tmp_free_space() -> _CheckLevels:
    """
    Warn if there is not enough free space in the default temporary directory.
    """
    free_space = shutil.disk_usage(gettempdir()).free
    free_space_gb = free_space / 1024 / 1024 / 1024

    low_space_message = (
        'The default temporary directory ("{tmp_prefix}") has '
        '{free_space:.1f} GB of free space available. '
        'Creating a cluster typically takes approximately 2 GB of temporary '
        'storage. '
        'If you encounter problems with disk space usage, set the ``TMPDIR`` '
        'environment variable to a suitable temporary directory or use the '
        '``--workspace-dir`` option on the ``dcos-docker create`` command.'
    ).format(
        tmp_prefix=Path('/') / gettempprefix(),
        free_space=free_space_gb,
    )

    if free_space_gb < 5:
        _warn(message=low_space_message)
        return _CheckLevels.WARNING

    return _CheckLevels.NONE


def _check_docker_root_free_space() -> _CheckLevels:
    """
    Warn if there is not enough free space in the Docker root directory.
    """
    # Any image will do, we use this for another test so using it here saves
    # pulling another image.
    tiny_image = 'luca3m/sleep'
    client = docker_client()
    container = client.containers.run(
        image=tiny_image,
        tty=True,
        detach=True,
        privileged=True,
    )

    cmd = ['df', '/']
    _, output = container.exec_run(cmd=cmd)
    container.stop()
    container.remove(v=True)

    output_lines = output.decode().strip().split('\n')
    # We skip the first line which is headers.
    # Sometimes the information is split across multiple lines.
    information = ' '.join(line for line in output_lines[1:])
    _, _, _, avail, _, _ = information.split()
    available_bytes = int(avail)
    available_gigabytes = available_bytes / 1024 / 1024
    low_space_message = (
        'The Docker root directory is at "{docker_root_dir}". '
        'On macOS this location is on a hidden virtual machine. '
        'This directory has {free_space:.1f} GB of free space available. '
        'If you encounter problems try running ``docker volume prune``.'
    ).format(
        docker_root_dir=client.info()['DockerRootDir'],
        free_space=available_gigabytes,
    )

    # The choice of 5 GB is arbitrary. Let's see how it goes in practice and
    # potentially adjust later.
    if available_gigabytes < 5:
        _warn(message=low_space_message)
        return _CheckLevels.WARNING

    return _CheckLevels.NONE


def _check_storage_driver() -> _CheckLevels:
    """
    Warn if the Docker storage driver is not a recommended driver.
    """
    client = docker_client()
    host_driver = client.info()['Driver']
    storage_driver_url = (
        'https://docs.docker.com/storage/storagedriver/select-storage-driver/'
    )
    # Any image will do, we use this for another test so using it here saves
    # pulling another image.
    tiny_image = 'luca3m/sleep'
    container = client.containers.run(
        image=tiny_image,
        tty=True,
        detach=True,
        privileged=True,
        volumes={'/proc': {
            'bind': '/host/proc',
            'mode': 'rw',
        }},
    )

    cmd = ['cat', '/host/proc/filesystems']
    _, output = container.exec_run(cmd=cmd)
    container.stop()
    container.remove(v=True)
    aufs_supported = bool(b'aufs' in output.split())
    supported_host_driver = bool(host_driver in DOCKER_STORAGE_DRIVERS)
    can_work = bool(aufs_supported or supported_host_driver)

    if not can_work:
        message = (
            "The host's Docker storage driver is \"{host_driver}\". "
            'aufs is not available. '
            'Change your storage driver to one of: {supported_drivers}. '
            'Alternatively try using the `--docker-storage-driver` option '
            'with `overlay` or `overlay2`. '
            'See {help_url}.'
        ).format(
            host_driver=host_driver,
            supported_drivers=', '.join(sorted(DOCKER_STORAGE_DRIVERS.keys())),
            help_url=storage_driver_url,
        )
        _error(message=message)
        return _CheckLevels.ERROR

    if not supported_host_driver:
        message = (
            "The host's Docker storage driver is \"{host_driver}\". "
            'We recommend that you use one of: {supported_drivers}. '
            'See {help_url}.'
        ).format(
            host_driver=host_driver,
            supported_drivers=', '.join(sorted(DOCKER_STORAGE_DRIVERS.keys())),
            help_url=storage_driver_url,
        )
        _warn(message=message)
        return _CheckLevels.WARNING

    return _CheckLevels.NONE


def _check_ssh() -> _CheckLevels:
    """
    Error if `ssh` is not available on the path.
    """
    if shutil.which('ssh') is None:
        _error(message='`ssh` must be available on your path.')
        return _CheckLevels.ERROR
    return _CheckLevels.NONE


def _check_networking() -> _CheckLevels:
    """
    Error if the Docker network is not set up correctly.
    """
    highest_level = _CheckLevels.NONE
    # Image for a container which sleeps for a long time.
    tiny_image = 'luca3m/sleep'
    client = docker_client()
    docker_for_mac = bool(client.info()['OperatingSystem'] == 'Docker for Mac')

    ping_container = client.containers.run(
        image=tiny_image,
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
        message = (
            'Cannot connect to a Docker container by its IP address. '
            'This is needed for features such as connecting to the web UI and '
            'using the DC/OS CLI. '
            'To use some parts of this CLI without resolving this issue, use '
            'the "--transport docker-exec" option on many of the available '
            'commands, and the --skip-http-checks flag on the "wait" command.'
        )
        if docker_for_mac:
            message += (
                ' '
                'We recommend using "dcos-docker setup-mac-network" to '
                'resolve this issue.'
            )
        _error(message=message)
        highest_level = _CheckLevels.ERROR

    ping_container.stop()
    ping_container.remove(v=True)
    return highest_level


def _check_mount_tmp() -> _CheckLevels:
    """
    Error if it is not possible to mount the temporary directory.
    """
    highest_level = _CheckLevels.NONE
    # Any image will do, we use this for another test so using it here saves
    # pulling another image.
    tiny_image = 'luca3m/sleep'
    client = docker_client()

    tmp_path = Path('/tmp').resolve()

    try:
        private_mount_container = client.containers.run(
            image=tiny_image,
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
            'There was an error mounting the temporary directory path '
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
        highest_level = _CheckLevels.ERROR

    private_mount_container.stop()
    private_mount_container.remove(v=True)
    return highest_level


def _check_memory() -> _CheckLevels:
    """
    Show information about the memory available to Docker.
    """
    client = docker_client()
    docker_memory = client.info()['MemTotal']
    docker_for_mac = bool(client.info()['OperatingSystem'] == 'Docker for Mac')
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
    return _CheckLevels.NONE


def _link_to_troubleshooting() -> _CheckLevels:
    """
    Link to documentation for further troubleshooting.
    """
    message = (
        'If you continue to experience problems, more information is '
        'available at '
        'http://dcos-e2e.readthedocs.io/en/latest/docker-backend.html#troubleshooting'  # noqa: E501
        '.'
    )

    _info(message=message)
    return _CheckLevels.NONE


def _check_1_9_sed() -> _CheckLevels:
    """
    Warn if the system's version of ``sed`` is incompatible with legacy DC/OS
    installers.
    """
    temp = tempfile.NamedTemporaryFile()
    Path(temp.name).write_text('a\na')
    sed_args = "sed '0,/a/ s/a/b/' " + temp.name
    result = subprocess.check_output(args=sed_args, shell=True)

    if result != b'b\na':
        message = (
            'The version of ``sed`` is not compatible with installers for '
            'DC/OS 1.9 and below. '
            'See '
            'http://dcos-e2e.readthedocs.io/en/latest/versioning-and-api-stability.html#dc-os-1-9-and-below'  # noqa: E501
            '.'
        )
        _warn(message=message)
        return _CheckLevels.WARNING

    return _CheckLevels.NONE


def _check_selinux() -> _CheckLevels:
    """
    Error if SELinux is enabled.
    This can cause problems such as mount problems for the installer.
    """
    if shutil.which('getenforce') is None:
        return _CheckLevels.NONE

    result = subprocess.check_output(args=['getenforce'])
    if result == b'Enforcing':
        message = (
            'SELinux is in "Enforcing" mode. '
            'SELinux must be in "Permissive" or "Disabled" mode.'
        )
        _error(message=message)
        return _CheckLevels.ERROR

    return _CheckLevels.NONE


def _check_docker_supports_mounts() -> _CheckLevels:
    """
    This is to avoid:

    docker.errors.InvalidVersion: mounts param is not supported in API versions
    < 1.30
    """
    client = docker_client()
    mount = docker.types.Mount(source=None, target='/etc')
    # Any image will do, we use this for another test so using it here saves
    # pulling another image.
    tiny_image = 'luca3m/sleep'

    try:
        container = client.containers.run(
            image=tiny_image,
            mounts=[mount],
            detach=True,
        )
    except docker.errors.InvalidVersion as exc:
        if 'mounts param is not supported' in str(exc):
            message = (
                'The Docker API version must be >= 1.30. '
                'This is because DC/OS E2E uses the ``mounts`` parameter.'
            )
            _error(message=message)
            return _CheckLevels.ERROR
        raise

    container.stop()
    container.remove(v=True)

    return _CheckLevels.NONE


def _check_can_mount_in_docker() -> _CheckLevels:
    """
    Check for an incompatibility between some systemd versions and some
    versions of Docker.
    """
    docker_client()

    cluster_backend = Docker(docker_version=DockerVersion.v1_13_1)
    args = ['docker', 'run', '-v', '/foo', 'alpine']

    error_message_substring = 'no subsystem for mount'
    with Cluster(cluster_backend=cluster_backend) as cluster:
        (public_agent, ) = cluster.public_agents
        try:
            public_agent.run(args=args)
        except subprocess.CalledProcessError as exc:
            if error_message_substring not in exc.stderr.decode():
                raise

            message = (
                'An issue has been detected which means that, for some '
                'versions of Docker inside DC/OS nodes, it will not be '
                'possible to create containers with mounts. '
                'Some functionality may be affected by this, for example '
                'extracting the DC/OS installer on a node.'
                '\n'
                'This issue is likely because the host\'s version of systemd '
                'is greater than version 232, which causes the following '
                'known issue: '
                'https://github.com/opencontainers/runc/issues/1175.'
                '\n'
                'Newer versions of Docker, work well with new versions of '
                'systemd. '
                'To avoid issues caused by this incompatibility, do one of '
                'the following:'
                '\n* Set ``systemd.legacy_systemd_cgroup_controller=yes`` as '
                'a kernel parameter on your host.'
                '\n* Use versions of Docker newer than 1.13.1 inside the '
                'DC/OS nodes.'
                ' To do this in the ``dcos-docker`` CLI, use the '
                '``--docker-version`` option on ``dcos-docker create``.'
                ' To do this in the Python library, pass a '
                '``docker_version`` parameter to the ``Docker`` backend class.'
            )
            _warn(message=message)
            return _CheckLevels.WARNING

    return _CheckLevels.NONE


@click.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    check_functions = [
        _check_1_9_sed,
        _check_docker_root_free_space,
        _check_docker_supports_mounts,
        _check_memory,
        _check_mount_tmp,
        _check_networking,
        _check_selinux,
        _check_ssh,
        _check_storage_driver,
        _check_tmp_free_space,
        _check_can_mount_in_docker,
    ]

    highest_level = max(function() for function in check_functions)

    _link_to_troubleshooting()
    if highest_level == _CheckLevels.ERROR:
        sys.exit(1)

"""
Checks for showing up common sources of errors with the Docker backend.
"""

import shutil
import subprocess
import tempfile
from enum import IntEnum
from pathlib import Path
from tempfile import gettempdir, gettempprefix

import click
import docker

from ._common import DOCKER_STORAGE_DRIVERS


class CheckLevels(IntEnum):
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


def check_tmp_free_space() -> CheckLevels:
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
        return CheckLevels.WARNING

    return CheckLevels.NONE


def check_docker_root_free_space() -> CheckLevels:
    """
    Warn if there is not enough free space in the Docker root directory.
    """
    # Any image will do, we use this for another test so using it here saves
    # pulling another image.
    tiny_image = 'luca3m/sleep'
    client = docker.from_env(version='auto')
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

    _, information = output.decode().strip().split('\n')
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
        return CheckLevels.WARNING

    return CheckLevels.NONE


def check_storage_driver() -> CheckLevels:
    """
    Warn if the Docker storage driver is not a recommended driver.
    """
    client = docker.from_env(version='auto')
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
            'See {help_url}.'
        ).format(
            host_driver=host_driver,
            supported_drivers=', '.join(sorted(DOCKER_STORAGE_DRIVERS.keys())),
            help_url=storage_driver_url,
        )
        _error(message=message)
        return CheckLevels.ERROR

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
        return CheckLevels.WARNING

    return CheckLevels.NONE


def check_ssh() -> CheckLevels:
    """
    Error if `ssh` is not available on the path.
    """
    if shutil.which('ssh') is None:
        _error(message='`ssh` must be available on your path.')
        return CheckLevels.ERROR
    return CheckLevels.NONE


def check_networking() -> CheckLevels:
    """
    Error if the Docker network is not set up correctly.
    """
    highest_level = CheckLevels.NONE
    # Image for a container which sleeps for a long time.
    tiny_image = 'luca3m/sleep'
    client = docker.from_env(version='auto')
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
        message = 'Cannot connect to a Docker container by its IP address.'
        if docker_for_mac:
            message += (
                ' We recommend using '
                'https://github.com/wojas/docker-mac-network. '
            )
        _error(message=message)
        highest_level = CheckLevels.ERROR

    ping_container.stop()
    ping_container.remove(v=True)
    return highest_level


def check_mount_tmp() -> CheckLevels:
    """
    Error if it is not possible to mount the temporary directory.
    """
    highest_level = CheckLevels.NONE
    # Any image will do, we use this for another test so using it here saves
    # pulling another image.
    tiny_image = 'luca3m/sleep'
    client = docker.from_env(version='auto')

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
        highest_level = CheckLevels.ERROR

    private_mount_container.stop()
    private_mount_container.remove(v=True)
    return highest_level


def check_memory() -> CheckLevels:
    """
    Show information about the memory available to Docker.
    """
    client = docker.from_env(version='auto')
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
    return CheckLevels.NONE


def link_to_troubleshooting() -> CheckLevels:
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
    return CheckLevels.NONE


def check_1_9_sed() -> CheckLevels:
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
        return CheckLevels.WARNING

    return CheckLevels.NONE

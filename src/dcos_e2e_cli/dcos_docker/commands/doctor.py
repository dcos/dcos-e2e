"""
Checks for showing up common sources of errors with the Docker backend.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import gettempdir, gettempprefix

import click
import docker

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e_cli.common.doctor import (
    CheckLevels,
    check_1_9_sed,
    check_ssh,
    error,
    info,
    run_doctor_commands,
    warn,
)
from dcos_e2e_cli.common.options import verbosity_option

from ._common import docker_client
from ._docker_storage_driver import DOCKER_STORAGE_DRIVERS


def _check_tmp_free_space() -> CheckLevels:
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
        '``--workspace-dir`` option on the ``minidcos docker create`` command.'
    ).format(
        tmp_prefix=Path('/') / gettempprefix(),
        free_space=free_space_gb,
    )

    if free_space_gb < 5:
        warn(message=low_space_message)
        return CheckLevels.WARNING

    return CheckLevels.NONE


def _check_docker_root_free_space() -> CheckLevels:
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
        'If you encounter problems try running ``docker volume prune`` to free'
        'space. '
        'This will remove all local volumes not used by at least one '
        'container. '
        'However, space may be used by volumes used by stopped containers. '
        'To remove stopped containers, use ``docker container prune``.'
    ).format(
        docker_root_dir=client.info()['DockerRootDir'],
        free_space=available_gigabytes,
    )

    # The choice of 5 GB is arbitrary. Let's see how it goes in practice and
    # potentially adjust later.
    if available_gigabytes < 5:
        warn(message=low_space_message)
        return CheckLevels.WARNING

    return CheckLevels.NONE


def _check_storage_driver() -> CheckLevels:
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
        error(message=message)
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
        warn(message=message)
        return CheckLevels.WARNING

    return CheckLevels.NONE


def _check_networking() -> CheckLevels:
    """
    Error if the Docker network is not set up correctly.
    """
    highest_level = CheckLevels.NONE
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
            'To use the "wait" command without resolving this issue, use the '
            '"--skip-http-checks" flag on the "wait" command.'
        )
        if docker_for_mac:
            message += (
                ' '
                'We recommend using "minidcos docker setup-mac-network" to '
                'resolve this issue.'
            )
        warn(message=message)
        highest_level = CheckLevels.WARNING

    ping_container.stop()
    ping_container.remove(v=True)
    return highest_level


def _check_mount_tmp() -> CheckLevels:
    """
    Error if it is not possible to mount the temporary directory.
    """
    highest_level = CheckLevels.NONE
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
        error(message=message)
        highest_level = CheckLevels.ERROR

    private_mount_container.stop()
    private_mount_container.remove(v=True)
    return highest_level


def _check_memory() -> CheckLevels:
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
    ).format(memory=docker_memory / 1024 / 1024 / 1024)
    mac_message = (
        '\n'
        'To dedicate more memory to Docker for Mac, go to '
        'Docker > Preferences > Advanced.'
    )
    if docker_for_mac:
        message += mac_message

    info(message=message)
    return CheckLevels.NONE


def _link_to_troubleshooting() -> None:
    """
    Link to documentation for further troubleshooting.
    """
    message = (
        'If you continue to experience problems, more information is '
        'available at '
        'http://dcos-e2e.readthedocs.io/en/latest/docker-backend.html#troubleshooting'  # noqa: E501
        '.'
    )

    info(message=message)


def _check_selinux() -> CheckLevels:
    """
    Error if SELinux is enabled.
    This can cause problems such as mount problems for the installer.
    """
    if shutil.which('getenforce') is None:
        return CheckLevels.NONE

    result = subprocess.check_output(args=['getenforce'])
    if result == b'Enforcing':
        message = (
            'SELinux is in "Enforcing" mode. '
            'SELinux must be in "Permissive" or "Disabled" mode.'
        )
        error(message=message)
        return CheckLevels.ERROR

    return CheckLevels.NONE


def _check_docker_supports_mounts() -> CheckLevels:
    """
    Check to is to avoid:

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
                'This is because this tool uses the ``mounts`` parameter.'
            )
            error(message=message)
            return CheckLevels.ERROR
        raise

    container.stop()
    container.remove(v=True)

    return CheckLevels.NONE


def _check_systemd() -> CheckLevels:
    """
    Check that the host supports systemd.

    See https://jira.d2iq.com/browse/DCOS_OSS-4475 for removing the need
    for this.
    """
    client = docker_client()
    tiny_image = 'luca3m/sleep'
    cgroup_mount = docker.types.Mount(
        source='/sys/fs/cgroup/systemd',
        target='/sys/fs/cgroup/systemd',
        read_only=True,
        type='bind',
    )
    try:
        container = client.containers.run(
            image=tiny_image,
            mounts=[cgroup_mount],
            detach=True,
        )
    except docker.errors.APIError as exc:
        expected = (
            'bind mount source path does not exist: /sys/fs/cgroup/systemd"'
        )
        expected_docker_machine = (
            'bind source path does not exist: /sys/fs/cgroup/systemd"'
        )
        if expected in str(exc) or expected_docker_machine in str(exc):
            message = (
                'Launching various applications requires ``/sys/fs/cgroup`` '
                'to be mounted from the host. '
                'This is because UCR applications require cgroup isolation. '
                'Therefore, by default, ``/sys/fs/cgroup`` is mounted from '
                'the host. '
                'It appears that this is not available on the host. '
                'Therefore, to launch a cluster you must use '
                '``--no-mount-sys-fs-cgroup``. '
                'Some applications will not work on the launched cluster.'
            )
            warn(message=message)
            return CheckLevels.WARNING
        raise

    container.stop()
    container.remove(v=True)

    return CheckLevels.NONE


def _check_mount_var() -> CheckLevels:
    """
    Check that `/var/folders` can be mounted.
    """
    source = Path('/var').resolve()
    client = docker_client()
    tiny_image = 'luca3m/sleep'
    var_mount = docker.types.Mount(
        source=str(source),
        target='/var',
        read_only=True,
        type='bind',
    )
    try:
        container = client.containers.run(
            image=tiny_image,
            mounts=[var_mount],
            detach=True,
        )
    except docker.errors.APIError as exc:
        expected = 'bind mount source path does not exist: {source}'.format(
            source=source,
        )
        expected_docker_machine = (
            'bind source path does not exist: {source}'
        ).format(source=source)
        if expected in str(exc) or expected_docker_machine in str(exc):
            message = (
                'There was an error mounting "{source}" '
                'from the host into a Docker container. '
                'This is required for multiple operations.'
            ).format(source=source)

            operating_system_info = client.info()['OperatingSystem']
            boot2docker = bool('Boot2Docker' in operating_system_info)
            if boot2docker:
                message += (
                    '\n'
                    'It appears that you are using Boot2Docker or '
                    'docker-machine and this might be the cause of the '
                    'problem. '
                    'These are known to be incompatible with DC/OS E2E and '
                    'minidcos.'
                )
            if sys.platform == 'darwin':
                message += (
                    '\n'
                    'Consider upgrading to Docker for Mac. '
                    'See https://docs.docker.com/docker-for-mac/install/.'
                )
            error(message=message)
            return CheckLevels.ERROR
        raise

    container.stop()
    container.remove(v=True)

    return CheckLevels.NONE


def _check_can_build() -> CheckLevels:
    """
    Check that the default cluster images can be built.
    """
    cluster_backend = Docker(docker_version=DockerVersion.v1_13_1)
    try:
        with Cluster(cluster_backend=cluster_backend):
            pass
    except docker.errors.BuildError as exc:
        message = (
            'There was an error building a Docker image. '
            'The Docker logs follow.\n'
            '\n'
        )
        for item in exc.build_log:
            if 'stream' in item:
                message += '\t' + item['stream']
        error(message=message)
        return CheckLevels.ERROR

    return CheckLevels.NONE


def _check_can_mount_in_docker() -> CheckLevels:
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
                "This issue is likely because the host's version of systemd "
                'is greater than version 232, which causes the following '
                'known the issue described at '
                'https://github.com/opencontainers/runc/issues/1175 .'
                '\n'
                'Newer versions of Docker, work well with new versions of '
                'systemd. '
                'To avoid issues caused by this incompatibility, do one of '
                'the following:'
                '\n'
                '* Set ``systemd.legacy_systemd_cgroup_controller=yes`` as '
                'a kernel parameter on your host.'
                '\n'
                '* Avoid using the ``--docker-version`` option to choose '
                'Docker version 1.13.1.'
            )
            warn(message=message)
            return CheckLevels.WARNING

    return CheckLevels.NONE


@click.command('doctor')
@verbosity_option
def doctor() -> None:
    """
    Diagnose common issues which stop this CLI from working correctly.
    """
    check_functions_no_cluster = [
        _check_docker_root_free_space,
        _check_docker_supports_mounts,
        _check_mount_var,
        _check_memory,
        _check_mount_tmp,
        _check_networking,
        _check_selinux,
        check_ssh,
        _check_storage_driver,
        _check_tmp_free_space,
        check_1_9_sed,
        _check_systemd,
    ]

    # Ideally no checks would create ``Cluster``s.
    # Checks which do risk showing issues unrelated to what they mean to.
    # We therefore run these last.
    check_functions_cluster_needed = [
        _check_can_build,
        # This comes last because it depends on ``_check_can_build``.
        _check_can_mount_in_docker,
    ]

    check_functions = (
        check_functions_no_cluster + check_functions_cluster_needed
    )

    run_doctor_commands(check_functions=check_functions)
    _link_to_troubleshooting()

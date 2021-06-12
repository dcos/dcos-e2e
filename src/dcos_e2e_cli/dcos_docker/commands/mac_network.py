"""
Tools for managing networking for Docker for Mac.
"""

import sys
import tarfile
import time
from io import BytesIO
from pathlib import Path
from shutil import copy, copytree, rmtree
from tempfile import TemporaryDirectory
from typing import Union

import click
import click_pathlib
import docker
from halo import Halo

from dcos_e2e.backends import Docker
from dcos_e2e_cli.common.options import enable_spinner_option

from ._common import docker_client

# These names cannot include the standard container name prefix else they
# conflict with "minidcos docker clean".
_PROXY_CONTAINER_NAME = 'vpn-proxy'
_OPENVPN_CONTAINER_NAME = 'vpn-openvpn'


def _get_ovpn_file_destination(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Path,
) -> Path:
    """
    Get OVPN file destination.
    """
    for _ in (ctx, param):
        pass

    path = value.expanduser()
    if path.is_dir():
        path = path / 'docker-for-mac.ovpn'

    if path.suffix != '.ovpn':
        message = '"{value}" does not have the suffix ".ovpn".'.format(
            value=value,
        )
        raise click.BadParameter(message=message)

    return path


def _create_mac_network(configuration_dst: Path, enable_spinner: bool) -> None:
    """
    Set up a network to connect to nodes on macOS.

    This creates an OpenVPN configuration file and describes how to use it.
    """
    with Halo(enabled=enable_spinner):
        client = docker_client()
        restart_policy = {'Name': 'always', 'MaximumRetryCount': 0}

        clone_name = 'docker-mac-network-master'
        docker_mac_network_clone = Path(__file__).parent / clone_name
        openvpn_dockerfile = Path(__file__).parent / 'openvpn'

        tmpdir = TemporaryDirectory()
        openvpn_build_path = Path(tmpdir.name).resolve()
        # Use a copy of the clone so that the clone cannot be corrupted for the
        # next run.
        rmtree(path=tmpdir.name)
        copytree(src=str(openvpn_dockerfile), dst=str(openvpn_build_path))
        docker_mac_network = openvpn_build_path / 'docker-mac-network-master'
        copytree(
            src=str(docker_mac_network_clone),
            dst=str(docker_mac_network),
        )

        proxy_image_tag = '{prefix}/proxy'.format(
            prefix=Docker().container_name_prefix,
        )
        client.images.build(
            path=str(docker_mac_network),
            rm=True,
            forcerm=True,
            tag=proxy_image_tag,
        )

        openvpn_image_tag = '{prefix}/openvpn'.format(
            prefix=Docker().container_name_prefix,
        )
        client.images.build(
            path=str(openvpn_build_path),
            rm=True,
            forcerm=True,
            tag=openvpn_image_tag,
        )

        proxy_command = 'TCP-LISTEN:13194,fork TCP:172.17.0.1:1194'
        proxy_ports = {'13194/tcp': ('127.0.0.1', '13194')}

        client.containers.run(
            image=proxy_image_tag,
            command=proxy_command,
            ports=proxy_ports,
            detach=True,
            restart_policy=restart_policy,
            name=_PROXY_CONTAINER_NAME,
        )

        openvpn_container = client.containers.run(
            image=openvpn_image_tag,
            restart_policy=restart_policy,
            cap_add=['NET_ADMIN'],
            environment={
                'dest': 'docker-for-mac.ovpn',
                'DEBUG': 1,
            },
            command='/local/helpers/run.sh',
            network_mode='host',
            detach=True,
            name=_OPENVPN_CONTAINER_NAME,
        )

        while True:
            try:
                raw_stream, _ = openvpn_container.get_archive(
                    path='/local/docker-for-mac.ovpn',
                )
            except docker.errors.NotFound:
                time.sleep(1)
            else:
                break

        temporary_extract_dst = Path(TemporaryDirectory().name).resolve()
        tar_archive = BytesIO(b''.join((i for i in raw_stream)))
        open_tar = tarfile.open(mode='r:', fileobj=tar_archive)
        open_tar.extractall(path=str(temporary_extract_dst))
        configuration_src = temporary_extract_dst / 'docker-for-mac.ovpn'
        copy(src=str(configuration_src), dst=str(configuration_dst))


def _destroy_mac_network_containers(enable_spinner: bool) -> None:
    """
    Destroy containers created by ``minidcos docker setup-mac-network``.
    """
    with Halo(enabled=enable_spinner):
        client = docker_client()
        for name in (_PROXY_CONTAINER_NAME, _OPENVPN_CONTAINER_NAME):
            try:
                container = client.containers.get(container_id=name)
            except docker.errors.NotFound:
                pass
            else:
                container.remove(v=True, force=True)


@click.command('setup-mac-network')
@click.option(
    '--configuration-dst',
    type=click_pathlib.Path(exists=False),
    default='~/Documents/docker-for-mac.ovpn',
    callback=_get_ovpn_file_destination,
    show_default=True,
    help='The location to create an OpenVPN configuration file.',
)
@click.option(
    '--force',
    is_flag=True,
    help=(
        'Overwrite any files and destroy conflicting containers from previous '
        'uses of this command.'
    ),
)
@enable_spinner_option
def setup_mac_network(
    configuration_dst: Path,
    enable_spinner: bool,
    force: bool,
) -> None:
    """
    Set up a network to connect to nodes on macOS.

    This creates an OpenVPN configuration file and describes how to use it.
    """
    profile_name = configuration_dst.with_suffix('').name

    configuration_instructions = (
        '1. Install an OpenVPN client such as Tunnelblick '
        '(https://tunnelblick.net/downloads.html) '
        'or Shimo (https://www.shimovpn.com).'
        '\n'
        '2. Run "open {configuration_dst}".'
        '\n'
        '3. If your OpenVPN client is Shimo, edit the new "{profile_name}" '
        'profile\'s Advanced settings to deselect "Send all traffic over VPN".'
        '\n'
        '4. In your OpenVPN client, connect to the new "{profile_name}" '
        'profile.'
        '\n'
        '5. Run "minidcos docker doctor" to confirm that everything is '
        'working.'
    ).format(
        configuration_dst=configuration_dst,
        profile_name=profile_name,
    )

    if configuration_dst.exists() and not force:
        already_exists_message = (
            '"{configuration_dst}" already exists so no new OpenVPN '
            'configuration was created.'
            '\n'
            '\n'
            'To use {configuration_dst}:'
            '\n'
        ).format(
            configuration_dst=configuration_dst,
        ) + configuration_instructions
        raise click.BadParameter(message=already_exists_message)

    if force:
        _destroy_mac_network_containers(enable_spinner=enable_spinner)

    try:
        _create_mac_network(
            configuration_dst=configuration_dst,
            enable_spinner=enable_spinner,
        )
    except docker.errors.APIError as exc:
        if exc.status_code == 409:
            message = (
                'Error: A custom macOS network container is already running. '
                'Use --force to destroy conflicting containers.'
            )
            click.echo(message, err=True)
            sys.exit(1)
        raise
    except docker.errors.BuildError as exc:
        message = 'Error: There was a problem building a Docker image:\n'
        click.echo(message, err=True)
        for line in exc.build_log:
            if 'stream' in line:
                click.echo('   ' + line['stream'].strip(), err=True)
        sys.exit(1)

    click.echo(message=configuration_instructions)


@click.command('destroy-mac-network')
@enable_spinner_option
def destroy_mac_network(enable_spinner: bool) -> None:
    """
    Destroy containers created by "minidcos docker setup-mac-network".
    """
    _destroy_mac_network_containers(enable_spinner=enable_spinner)
    message = (
        "The containers used to allow access to Docker for Mac's internal "
        'networks have been removed.'
        '\n'
        '\n'
        'It may be the case that the "docker-for-mac" profile still exists in '
        'your OpenVPN client.'
    )

    click.echo(message=message)

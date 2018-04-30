"""
Tools for managing networking for Docker for Mac.
"""

import sys
import time
from pathlib import Path
from shutil import copy, copytree
from tempfile import TemporaryDirectory
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


def create_mac_network(configuration_dst: Path) -> None:
    """
    Set up a network to connect to nodes on macOS.

    This creates an OpenVPN configuration file and describes how to use it.
    """
    client = docker.from_env(version='auto')
    restart_policy = {'Name': 'always', 'MaximumRetryCount': 0}

    clone_name = 'docker-mac-network-master'
    docker_mac_network_clone = Path(__file__).parent / clone_name
    docker_mac_network = Path(TemporaryDirectory().name).resolve()
    # Use a copy of the clone so that the clone cannot be corrupted for the
    # next run.
    copytree(src=str(docker_mac_network_clone), dst=str(docker_mac_network))

    docker_image_tag = 'dcos-e2e/proxy'
    client.images.build(
        path=str(docker_mac_network),
        rm=True,
        forcerm=True,
        tag=docker_image_tag,
    )

    proxy_command = 'TCP-LISTEN:13194,fork TCP:172.17.0.1:1194'
    proxy_ports = {'13194/tcp': ('127.0.0.1', '13194')}
    proxy_container_name = 'dcos_e2e-proxy'

    try:
        client.containers.run(
            image=docker_image_tag,
            command=proxy_command,
            ports=proxy_ports,
            detach=True,
            restart_policy=restart_policy,
            name=proxy_container_name,
        )
    except docker.errors.APIError as exc:
        if exc.status_code == 409:
            message = (
                'Error: A proxy container is already running. '
                'To remove this container, run: '
                '"docker rm -f {proxy_container_name}"'
            ).format(proxy_container_name=proxy_container_name)
            click.echo(message, err=True)
            sys.exit(1)
        raise

    client.containers.run(
        image='kylemanna/openvpn',
        restart_policy=restart_policy,
        cap_add=['NET_ADMIN'],
        environment={
            'dest': 'docker-for-mac.ovpn',
            'DEBUG': 1
        },
        command='/local/helpers/run.sh',
        network_mode='host',
        detach=True,
        volumes={
            str(docker_mac_network): {
                'bind': '/local',
                'mode': 'rw',
            },
            str(docker_mac_network / 'config'): {
                'bind': '/etc/openvpn',
                'mode': 'rw',
            },
        },
    )

    configuration_src = Path(docker_mac_network / 'docker-for-mac.ovpn')

    with click_spinner.spinner():
        while True:
            if configuration_src.exists():
                break
            time.sleep(1)

    copy(src=str(configuration_src), dst=str(configuration_dst))

    message = (
        '1. Install an OpenVPN client such as Tunnelblick '
        '(https://tunnelblick.net/downloads.html) '
        'or Shimo (https://www.shimovpn.com).'
        '\n'
        '2. Run "open {configuration_dst}".'
        '\n'
        '3. If your OpenVPN client is Shimo, edit the new "docker-for-mac" '
        'profile\'s Advanced settings to deselect "Send all traffic over VPN".'
        '\n'
        '4. In your OpenVPN client, connect to the new "docker-for-mac" '
        'profile.'
        '\n'
        '5. Run "dcos-docker doctor" to confirm that everything is working.'
    ).format(configuration_dst=configuration_dst)

    click.echo(message=message)

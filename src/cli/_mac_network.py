"""
Tools for managing networking for Docker for Mac.
"""

import tarfile
import time
from io import BytesIO
from pathlib import Path
from shutil import copy, copytree, rmtree
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

import docker

# We start these names with "e2e" rather than "dcos-e2e" to avoid a conflict
# with "make clean".
_PROXY_CONTAINER_NAME = 'e2e-proxy'
_OPENVPN_CONTAINER_NAME = 'e2e-openvpn'


def create_mac_network(configuration_dst: Path) -> None:
    """
    Set up a network to connect to nodes on macOS.

    This creates an OpenVPN configuration file and describes how to use it.
    """
    client = docker.from_env(version='auto')
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
    copytree(src=str(docker_mac_network_clone), dst=str(docker_mac_network))

    proxy_image_tag = 'dcos-e2e/proxy'
    client.images.build(
        path=str(docker_mac_network),
        rm=True,
        forcerm=True,
        tag=proxy_image_tag,
    )

    openvpn_image_tag = 'dcos-e2e/openvpn'
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


def destroy_mac_network_containers() -> None:
    """
    Destroy containers created by ``dcos-docker setup-mac-network``.
    """
    client = docker.from_env(version='auto')
    for name in (_PROXY_CONTAINER_NAME, _OPENVPN_CONTAINER_NAME):
        try:
            container = client.containers.get(container_id=name)
        except docker.errors.NotFound:
            pass
        else:
            container.remove(v=True, force=True)

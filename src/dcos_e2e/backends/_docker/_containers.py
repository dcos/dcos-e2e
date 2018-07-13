"""
Helpers for starting DC/OS containers.
"""

import configparser
import io
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional

import docker

from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion


def _docker_service_file(
    storage_driver: DockerStorageDriver,
    docker_version: DockerVersion,
) -> str:
    """
    Return the contents of a systemd unit file for a Docker service.

    Args:
        storage_driver: The Docker storage driver to use.
        docker_version: The version of Docker to start.
    """
    storage_driver_name = {
        DockerStorageDriver.AUFS: 'aufs',
        DockerStorageDriver.OVERLAY: 'overlay',
        DockerStorageDriver.OVERLAY_2: 'overlay2',
    }[storage_driver]

    daemon = {
        DockerVersion.v1_11_2: '/usr/bin/docker daemon',
        DockerVersion.v1_13_1: '/usr/bin/docker daemon',
        DockerVersion.v17_12_1_ce: '/usr/bin/dockerd',
    }[docker_version]

    docker_cmd = (
        '{daemon} '
        '-D '
        '-s {storage_driver_name} '
        '--exec-opt=native.cgroupdriver=cgroupfs'
    ).format(
        storage_driver_name=storage_driver_name,
        daemon=daemon,
    )

    docker_service_contents = {
        'Unit': {
            'Description': 'Docker Application Container Engine',
            'Documentation': 'https://docs.docker.com',
            'After': 'dbus.service',
        },
        'Service': {
            'ExecStart': docker_cmd,
            'LimitNOFILE': '1048576',
            'LimitNPROC': '1048576',
            'LimitCORE': 'infinity',
            'Delegate': 'yes',
            'TimeoutStartSec': '0',
        },
        'Install': {
            'WantedBy': 'default.target',
        },
    }
    config = configparser.ConfigParser()
    # Ignore erroneous error https://github.com/python/typeshed/issues/1857.
    config.optionxform = str  # type: ignore
    config.read_dict(docker_service_contents)
    config_string = io.StringIO()
    config.write(config_string)
    config_string.seek(0)
    return config_string.read()


def start_dcos_container(
    container_base_name: str,
    container_number: int,
    mounts: List[docker.types.Mount],
    tmpfs: Dict[str, str],
    docker_image: str,
    labels: Dict[str, str],
    public_key_path: Path,
    docker_storage_driver: DockerStorageDriver,
    docker_version: DockerVersion,
    network: Optional[docker.models.networks.Network] = None,
    ports: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Start a master, agent or public agent container.
    In this container, start Docker and `sshd`.

    Run Mesos without `systemd` support. This is not supported by DC/OS.
    See https://jira.mesosphere.com/browse/DCOS_OSS-1131.

    Args:
        container_base_name: The start of the container name.
        container_number: The end of the container name.
        mounts: See `mounts` on
            http://docker-py.readthedocs.io/en/latest/containers.html.
        tmpfs: See `tmpfs` on
            http://docker-py.readthedocs.io/en/latest/containers.html.
        docker_image: The name of the Docker image to use.
        labels: Docker labels to add to the cluster node containers. Akin to
            the dictionary option in
            http://docker-py.readthedocs.io/en/stable/containers.html.
        public_key_path: The path to an SSH public key to put on the node.
        docker_version: The Docker version to use on the node.
        docker_storage_driver: The storage driver to use for Docker on the
            node.
        network: The network to connect the container to other than the default
        ``docker0`` bridge network.
        ports: The ports to expose on the host.
    """
    hostname = container_base_name + str(container_number)
    environment = {'container': hostname}

    client = docker.from_env(version='auto')
    container = client.containers.create(
        name=hostname,
        privileged=True,
        detach=True,
        tty=True,
        environment=environment,
        hostname=hostname,
        image=docker_image,
        mounts=mounts,
        tmpfs=tmpfs,
        labels=labels,
        stop_signal='SIGRTMIN+3',
        command=['/sbin/init'],
        ports=ports or {},
    )
    if network:
        network.connect(container)
    container.start()

    disable_systemd_support_cmd = (
        "echo 'MESOS_SYSTEMD_ENABLE_SUPPORT=false' >> "
        '/var/lib/dcos/mesos-slave-common'
    )

    docker_service_name = 'docker.service'
    docker_service_text = _docker_service_file(
        storage_driver=docker_storage_driver,
        docker_version=docker_version,
    )
    docker_service_dst = '/lib/systemd/system/' + docker_service_name
    echo_docker = [
        'echo',
        '-e',
        shlex.quote(docker_service_text),
        '>',
        docker_service_dst,
    ]

    public_key = public_key_path.read_text()
    echo_key = ['echo', public_key, '>>', '/root/.ssh/authorized_keys']

    for cmd in [
        ['mkdir', '-p', '/var/lib/dcos'],
        ['mkdir', '-p', '/lib/systemd/system'],
        '/bin/bash -c "{cmd}"'.format(cmd=' '.join(echo_docker)),
        ['systemctl', 'enable', docker_service_name],
        ['systemctl', 'start', docker_service_name],
        ['/bin/bash', '-c', disable_systemd_support_cmd],
        ['mkdir', '--parents', '/root/.ssh'],
        '/bin/bash -c "{cmd}"'.format(cmd=' '.join(echo_key)),
        ['rm', '-f', '/run/nologin', '||', 'true'],
        ['systemctl', 'start', 'sshd'],
        # Work around https://jira.mesosphere.com/browse/DCOS_OSS-1361.
        ['systemd-tmpfiles', '--create', '--prefix', '/run/log/journal'],
    ]:
        exit_code, output = container.exec_run(cmd=cmd)
        assert exit_code == 0, ' '.join(cmd) + ': ' + output.decode()

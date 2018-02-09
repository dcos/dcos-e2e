"""

"""

import re
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Dict  # noqa: F401
from typing import Optional, Union
import logging
import uuid

import click
import yaml
import docker

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.docker_storage_drivers import DockerStorageDriver

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


def _validate_dcos_configuration(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Union[int, bool, str],
) -> Dict[str, Any]:
    """
    XXX
    """
    try:
        return dict(yaml.load(value) or {})
    except ValueError:
        message = '"{value}" is not a valid DC/OS configuration'.format(
            value=value,
        )
    except Exception as exc:
        message = '"{value}" is not valid YAML'.format(value=value)

    raise click.BadParameter(message=message)


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
    help='foo',
)
@click.option(
    '--linux-distribution',
    type=click.Choice(_LINUX_DISTRIBUTIONS.keys()),
    default='centos-7',
    show_default=True,
    help='foo',
)
@click.option(
    '--docker-storage-driver',
    type=click.Choice(_DOCKER_STORAGE_DRIVERS.keys()),
    default=None,
    show_default=False,
    help='by default uses host driver',
)
@click.option(
    '--num-masters',
    type=click.INT,
    default=1,
    show_default=True,
)
@click.option(
    '--num-agents',
    type=click.INT,
    default=1,
    show_default=True,
)
@click.option(
    '--num-public-agents',
    type=click.INT,
    default=1,
    show_default=True,
)
@click.option(
    '--extra-config',
    type=str,
    default='{}',
    callback=_validate_dcos_configuration,
)
def create(
    artifact: str,
    linux_distribution: str,
    docker_version: str,
    num_masters: int,
    num_agents: int,
    num_public_agents: int,
    docker_storage_driver: str,
    extra_config: Dict[str, Any],
) -> None:
    """
    Create a DC/OS cluster.
    """
    custom_master_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_agent_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_public_agent_mounts = {}  # type: Dict[str, Dict[str, str]]
    cluster_id = uuid.uuid4().hex

    logging.disable(logging.WARNING)

    cluster_backend = Docker(
        custom_master_mounts=custom_master_mounts,
        custom_agent_mounts=custom_agent_mounts,
        custom_public_agent_mounts=custom_public_agent_mounts,
        linux_distribution=_LINUX_DISTRIBUTIONS[linux_distribution],
        docker_version=_DOCKER_VERSIONS[docker_version],
        storage_driver=_DOCKER_STORAGE_DRIVERS.get(docker_storage_driver),
        docker_container_labels={
            'dcos_e2e.cluster_id': cluster_id,
        },
    )

    cluster = Cluster(
        cluster_backend=cluster_backend,
        masters=num_masters,
        agents=num_agents,
        public_agents=num_public_agents,
    )

    try:
        cluster.install_dcos_from_path(
            build_artifact=Path(artifact),
            extra_config=extra_config,
        )
    except CalledProcessError as exc:
        cluster.destroy()
        return

    click.echo(cluster_id)


@dcos_docker.command('list')
# TODO quiet vs verbose
def list():
    logging.disable(logging.WARNING)
    client = docker.from_env(version='auto')
    filters = {'label': 'dcos_e2e.cluster_id'}
    containers = client.containers.list(filters=filters)
    # TODO constant for dcos_e2e.cluster_id
    cluster_ids = set([container.labels['dcos_e2e.cluster_id'] for container in containers])
    for cluster_id in cluster_ids:
        click.echo(cluster_id)

if __name__ == '__main__':
    dcos_docker()

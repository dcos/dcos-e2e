"""

"""

from pathlib import Path
from typing import Any, Dict  # noqa: F401

import click

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_versions import DockerVersion

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
)
@click.option(
    '--linux-distribution',
    type=click.Choice(_LINUX_DISTRIBUTIONS.keys()),
    default='centos-7',
    show_default=True,
)
def create(
    artifact: str,
    linux_distribution: str,
    docker_version: str,
) -> None:
    """
    Create a DC/OS cluster.
    """
    # Everything in this block should be a CLI option.
    custom_master_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_agent_mounts = {}  # type: Dict[str, Dict[str, str]]
    custom_public_agent_mounts = {}  # type: Dict[str, Dict[str, str]]
    linux_distribution = _LINUX_DISTRIBUTIONS[linux_distribution]
    docker_version = _DOCKER_VERSIONS[docker_version]
    docker_storage_driver = None
    # If someone wants to see no output, they can pipe stdout/stderr somewhere
    log_output_live = True
    extra_config = {}  # type: Dict[str, Any]
    masters = 1
    agents = 1
    public_agents = 1

    cluster_backend = Docker(
        custom_master_mounts=custom_master_mounts,
        custom_agent_mounts=custom_agent_mounts,
        custom_public_agent_mounts=custom_public_agent_mounts,
        linux_distribution=linux_distribution,
        docker_version=docker_version,
        storage_driver=docker_storage_driver,
    )

    cluster = Cluster(
        cluster_backend=cluster_backend,
        masters=masters,
        agents=agents,
        public_agents=public_agents,
    )

    cluster.install_dcos_from_path(
        build_artifact=Path(artifact),
        extra_config=extra_config,
        log_output_live=log_output_live,
    )


if __name__ == '__main__':
    dcos_docker()

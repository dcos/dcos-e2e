"""
Common code for CLI modules.
"""

from typing import Dict, Set

import docker
from docker.models.containers import Container

from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion

LINUX_DISTRIBUTIONS = {
    'centos-7': Distribution.CENTOS_7,
    'coreos': Distribution.COREOS,
    'ubuntu-16.04': Distribution.UBUNTU_16_04,
}

DOCKER_VERSIONS = {
    '1.11.2': DockerVersion.v1_11_2,
    '1.13.1': DockerVersion.v1_13_1,
    '17.12.1-ce': DockerVersion.v17_12_1_ce,
}

DOCKER_STORAGE_DRIVERS = {
    'aufs': DockerStorageDriver.AUFS,
    'overlay': DockerStorageDriver.OVERLAY,
    'overlay2': DockerStorageDriver.OVERLAY_2,
}

CLUSTER_ID_LABEL_KEY = 'dcos_e2e.cluster_id'
WORKSPACE_DIR_LABEL_KEY = 'dcos_e2e.workspace_dir'
VARIANT_LABEL_KEY = 'dcos_e2e.variant'


def existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    client = docker.from_env(version='auto')
    filters = {'label': CLUSTER_ID_LABEL_KEY}
    containers = client.containers.list(filters=filters)
    return set(
        [container.labels[CLUSTER_ID_LABEL_KEY] for container in containers],
    )


class ContainerInspectView:
    """
    Details of a node from a container.
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
        container = self._container
        index = container.name.split('-')[-1]
        name_without_index = container.name[:-len('-' + index)]
        if name_without_index.endswith('public-agent'):
            role = 'public_agent'
        elif name_without_index.endswith('agent'):
            role = 'agent'
        elif name_without_index.endswith('master'):
            role = 'master'

        return {
            'e2e_reference': '{role}_{index}'.format(role=role, index=index),
            'docker_container_name': container.name,
            'ip_address': container.attrs['NetworkSettings']['IPAddress'],
        }

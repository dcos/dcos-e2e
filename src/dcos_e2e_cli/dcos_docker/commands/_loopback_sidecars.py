"""
Helpers for interacting with loopback sidecars.
"""

from typing import List

from docker.models.containers import Container

from ._common import (
    NODE_TYPE_LABEL_KEY,
    NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
    SIDECAR_NAME_LABEL_KEY,
    docker_client,
)


def loopback_sidecars_by_name(name: str) -> List[Container]:
    """
    Return all loopback sidecar containers with the given sidecar ``name``.
    """
    client = docker_client()
    filters = {
        'label': [
            '{key}={value}'.format(
                key=NODE_TYPE_LABEL_KEY,
                value=NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
            ),
            '{key}={value}'.format(
                key=SIDECAR_NAME_LABEL_KEY,
                value=name,
            ),
        ],
    }
    return list(client.containers.list(filters=filters))

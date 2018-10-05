"""
Tests for creating binaries.
"""

import logging
from pathlib import Path

import docker
from docker.types import Mount

from admin.binaries import make_linux_binaries

LOGGER = logging.getLogger(__name__)


def test_linux_binaries() -> None:
    """
    ``make_linux_binaries`` creates binaries which can be run on Linux.
    """

    binary_paths = make_linux_binaries(
        repo_root=Path(__file__).parent.parent.parent,
    )
    binary_path_names = set(path.name for path in binary_paths)
    assert binary_path_names == {'dcos-docker', 'dcos-aws', 'dcos-vagrant'}

    mounts = []
    remote_binaries_dir = Path('/binaries')
    remote_paths = []
    for path in binary_paths:
        remote_path = remote_binaries_dir / path.name
        mounts.append(
            Mount(
                source=str(path.absolute()),
                target=str(remote_path),
                type='bind',
            ),
        )
        remote_paths.append(remote_path)

    for remote_path in remote_paths:
        cmd_in_container = [
            'chmod',
            '+x',
            str(remote_path),
            '&&',
            str(remote_path),
            '--help',
        ]
        cmd = 'bash -c "{cmd}"'.format(cmd=' '.join(cmd_in_container))
        client = docker.from_env(version='auto')
        container = client.containers.run(
            image='python:3.6',
            mounts=mounts,
            command=cmd,
            remove=True,
            detach=True,
        )
        for line in container.logs(stream=True):
            line = line.decode().strip()
            LOGGER.info(line)

"""
Tests for creating binaries.
"""

import logging
import os
from pathlib import Path

import docker
from docker.types import Mount

from admin.binaries import make_linux_binaries

LOGGER = logging.getLogger(__name__)


def test_linux_binaries() -> None:
    """
    ``make_linux_binaries`` creates a binary which can be run on Linux.
    """
    repo_root = Path(__file__).parent.parent.parent
    binary_paths = make_linux_binaries(repo_root=repo_root)
    binary_path_names = set(path.name for path in binary_paths)
    assert binary_path_names == {'minidcos'}

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

    client = docker.from_env(version='auto')

    for remote_path in remote_paths:
        # Unset LANG and LC_ALL to show that these are not necessary for the
        # CLI to run.
        # This was a problem when the binaries were built with Python < 3.7.
        cmd_in_container = [
            'unset',
            'LANG',
            '&&',
            'unset',
            'LC_ALL',
            '&&',
            'chmod',
            '+x',
            str(remote_path),
            '&&',
            str(remote_path),
            '--version',
        ]
        command = 'bash -c "{cmd}"'.format(cmd=' '.join(cmd_in_container))
        container = client.containers.create(
            image='python:3.7',
            mounts=mounts,
            command=command,
        )

        container.start()
        for line in container.logs(stream=True):
            line = line.decode().strip()
            LOGGER.info(line)

        status_code = container.wait()['StatusCode']
        assert status_code == 0
        container.remove(force=True)

    for binary_path in binary_paths:
        os.remove(str(binary_path.resolve()))

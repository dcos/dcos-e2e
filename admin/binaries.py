"""
Create binaries for the CLIs.
"""

import logging
import shutil
from pathlib import Path
from typing import Set

import docker
from docker.types import Mount

LOGGER = logging.getLogger(__name__)


def make_linux_binaries(repo_root: Path) -> Set[Path]:
    """
    Create binaries for Linux in a Docker container.

    Args:
        repo_root: The path to the root of the repository.

    Returns:
        A set of paths to the built binaries.
    """

    shutil.rmtree(str(repo_root / 'dist'))
    for path in repo_root.glob('dcos-*.spec'):
        shutil.rmtree(str(path))

    target_dir = '/e2e'
    code_mount = Mount(
        source=str(repo_root.absolute()),
        target=target_dir,
        type='bind',
    )

    bin_dir = repo_root / 'bin'
    binaries = list(bin_dir.iterdir())

    cmd_in_container = ['pip3', 'install', '-e', '.[packaging]']
    for binary in binaries:
        cmd_in_container += [
            '&&',
            'pyinstaller',
            './bin/{binary}'.format(binary=binary),
            '--onefile',
        ]
    cmd = 'bash -c "{cmd}"'.format(cmd=' '.join(cmd_in_container))

    client = docker.from_env(version='auto')
    container = client.containers.run(
        image='python:3.6',
        mounts=[code_mount],
        command=cmd,
        working_dir=target_dir,
        remove=True,
        detach=True,
    )
    for line in container.logs(stream=True):
        line = line.decode().strip()
        LOGGER.info(line)

    return set(repo_root / 'dist' / binary for binary in binaries)

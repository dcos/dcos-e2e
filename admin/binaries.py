"""
Create binaries for the CLIs.
"""

import logging
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
    client = docker.from_env(version='auto')
    dist_dir = repo_root / 'dist'
    assert not dist_dir.exists() or not set(dist_dir.iterdir())

    target_dir = '/e2e'
    code_mount = Mount(
        source=str(repo_root.absolute()),
        target=target_dir,
        type='bind',
    )

    cmd_in_container = [
        # This includes a few hacks.
        # Those work around linked issues.
        # When those issues are resolved, we can use:
        # pip install .[packaging]
        #
        # We use an unreleased PyInstaller version.
        # This is so that we can get a fix which should be in the next
        # PyInstaller release after PyInstaller 3.4.
        # See https://github.com/pyinstaller/pyinstaller/issues/3507.
        'pip3',
        'install',
        'git+https://github.com/pyinstaller/pyinstaller',
        '&&',
        'pip',
        'install',
        '.',
        '&&',
        # PyInstaller is not compatible with enum34.
        # We have one requirement which depends on enum34 -
        # py_log_symbols 0.0.12.
        # We use an unreleased version of py_log_symbols which does not
        # require enum34 and then we uninstall enum34.
        'pip',
        'install',
        'git+https://github.com/manrajgrover/py-log-symbols',
        '&&',
        'pip',
        'uninstall',
        '--yes',
        'enum34',
        '&&',
        'python',
        'admin/create_pyinstaller_binaries.py',
    ]
    command = 'bash -c "{cmd}"'.format(cmd=' '.join(cmd_in_container))

    container = client.containers.run(
        image='python:3.7',
        mounts=[code_mount],
        command=command,
        working_dir=target_dir,
        remove=True,
        detach=True,
    )
    for line in container.logs(stream=True):
        line = line.strip()
        LOGGER.info(line)

    status_code = container.wait()['StatusCode']
    assert status_code == 0
    return set(dist_dir.iterdir())

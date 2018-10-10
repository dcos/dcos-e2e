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

    target_dir = '/e2e'
    code_mount = Mount(
        source=str(repo_root.absolute()),
        target=target_dir,
        type='bind',
    )

    # MANIFEST.in describes files that must be available which are not
    # necessarily Python files.
    # These include e.g. Dockerfiles.
    # We still need to include these in the binary.
    datas = []
    with open('MANIFEST.in') as manifest_file:
        for line in manifest_file.readlines():
            if line.startswith('recursive-include'):
                _, manifest_path, _ = line.split()
            else:
                _, manifest_path = line.split()
            if manifest_path.startswith('src/'):
                if Path(manifest_path).is_file():
                    parent = Path(manifest_path).parent
                    manifest_path = str(parent)

                path_without_src = manifest_path[len('src/'):]
                datas.append((manifest_path, path_without_src))

    dist_dir = repo_root / 'dist'
    for path in list(repo_root.glob('dcos-*.spec')) + [dist_dir]:
        container_path = Path(target_dir) / str(path.relative_to(repo_root))
        container = client.containers.run(
            image='python:3.6',
            mounts=[code_mount],
            command=['rm', '-rf', str(container_path)],
            working_dir=target_dir,
            remove=True,
            detach=True,
        )
        for line in container.logs(stream=True):
            line = line.strip()
            LOGGER.info(line)

    bin_dir = repo_root / 'bin'
    binaries = list(bin_dir.iterdir())

    # We explicitly do not use ``-e / --editable``.
    # This is because ``versioneer`` replaces the dynamic ``_version.py`` file
    # with a static one only when creating a non-editable Python EGG.  This is
    # required for the PyInstaller binary to determine the version string
    # because the git tags used by the dynamic ``_version.py`` are not
    # included.
    cmd_in_container = ['pip3', 'install', '.[packaging]']
    for binary in binaries:
        cmd_in_container += [
            '&&',
            'pyinstaller',
            './bin/{binary}'.format(binary=binary.name),
            '--onefile',
        ]
        for data in datas:
            source, destination = data
            data_str = '{source}:{destination}'.format(
                source=source,
                destination=destination,
            )
            add_data_command = ['--add-data', data_str]
            cmd_in_container += add_data_command
    cmd = 'bash -c "{cmd}"'.format(cmd=' '.join(cmd_in_container))

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

    return set(repo_root / 'dist' / binary.name for binary in binaries)

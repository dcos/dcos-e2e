"""
"""

import subprocess
from pathlib import Path

import docker
from docker.types import Mount
from dulwich.repo import Repo
from py.path import local  # pylint: disable=no-name-in-module, import-error

from admin.homebrew import get_homebrew_formula


def test_brew(tmpdir: local) -> None:
    """
    It is possible to create a Homebrew formula and to install this with
    Linuxbrew.
    """
    local_repository = Repo('.')
    archive_file = Path(str(tmpdir.join('1.tar.gz')))
    archive_file.touch()
    # We do not use ``dulwich.porcelain.archive`` because it has no option to
    # use a gzip format.
    args = [
        'git',
        'archive',
        '--format',
        'tar.gz',
        '-o',
        str(archive_file),
        '--prefix',
        '1/',
        'HEAD',
    ]
    subprocess.run(args=args, check=True)

    client = docker.from_env(version='auto')
    linuxbrew_image = 'linuxbrew/linuxbrew'
    # The path needs to look like a versioned artifact to Linuxbrew.
    container_archive_path = '/1.tar.gz'
    archive_url = 'file://' + container_archive_path
    head_url = 'file://' + str(Path(local_repository.path).absolute())

    homebrew_formula_contents = get_homebrew_formula(
        archive_url=archive_url,
        head_url=head_url,
    )

    homebrew_filename = 'dcose2e.rb'
    homebrew_file = Path(str(tmpdir.join(homebrew_filename)))
    homebrew_file.write_text(homebrew_formula_contents)
    container_homebrew_file_path = '/' + homebrew_filename

    archive_mount = Mount(
        source=str(archive_file.absolute()),
        target=container_archive_path,
        type='bind',
    )

    homebrew_file_mount = Mount(
        source=str(homebrew_file.absolute()),
        target=container_homebrew_file_path,
        type='bind',
    )

    mounts = [archive_mount, homebrew_file_mount]
    command_list = [
        'brew',
        'install',
        container_homebrew_file_path,
        '&&',
        'dcos-docker',
        '--help',
        '&&',
        'dcos-aws',
        '--help',
        '&&',
        'dcos-vagrant',
        '--help',
    ]

    command = '/bin/bash -c "{command}"'.format(
        command=' '.join(command_list),
    )

    client.containers.run(
        image=linuxbrew_image,
        mounts=mounts,
        command=command,
        environment={'HOMEBREW_NO_AUTO_UPDATE': 1},
    )

"""
"""

from pathlib import Path

import docker
from docker.types import Mount
from dulwich.porcelain import archive
from dulwich.repo import Repo
from py.path import local  # pylint: disable=no-name-in-module, import-error

from admin.homebrew import get_homebrew_formula


def test_brew(tmpdir: local) -> None:
    """
    XXX
    """
    local_repository = Repo('.')
    committish = b'HEAD'
    archive_file = Path(str(tmpdir.join('archive.tar.gz')))
    archive_file.touch()

    with archive_file.open('wb') as outstream:
        archive(
            repo=local_repository,
            committish=committish,
            outstream=outstream,
        )

    client = docker.from_env(version='auto')
    linuxbrew_image = 'linuxbrew/linuxbrew'
    container_archive_path = '/archive.tar.gz'
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
    command = [
        'brew',
        'install',
        container_homebrew_file_path,
        '&&',
        'dcos-docker',
        '--help',
        '&&fsa',
    ]

    container = client.containers.run(
        image=linuxbrew_image,
        mounts=mounts,
        command=command,
        environment={'HOMEBREW_NO_AUTO_UPDATE': 1},
    )

    container.wait()
    import pdb; pdb.set_trace()
    container.stop()
    container.remove(v=True)

    # TODO make archive - test can you do archive from file:///
    # git archive --format=tar.gz -o /tmp/my-repo.tar.gz --prefix=my-repo/ master
    # If so, this probably needs to be in the container
    # TODO admin/homebrew
    # TODO write file
    # TODO start container
    # docker run -it linuxbrew/linuxbrew
    # TODO send file to container
    # TODO install from Linuxbrew
    # TODO also for Vagrant and AWS
    # dcos-docker help

    # TODO move this to tests/

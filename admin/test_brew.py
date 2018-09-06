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

    homebrew_formula_contents = get_homebrew_formula(
        repository=local_repository,
        archive_url=archive_url,
    )

    homebrew_file = Path(str(tmpdir.join('dcose2e.rb')))
    homebrew_file.write(homebrew_formula_contents)

    archive_mount = Mount(
        source=str(archive_file),
        target=container_archive_path,
    )

    homebrew_file_mount = Mount(
        source=str(homebrew_file),
        target=container_archive_path,
    )

    container = client.containers.run(
        image=linuxbrew_image,
        detach=True,
        mounts=mounts,
    )
    import pdb; pdb.set_trace()

    # TODO make archive - test can you do archive from file:///
    # git archive --format=tar.gz -o /tmp/my-repo.tar.gz --prefix=my-repo/ master
    # If so, this probably needs to be in the container
    # TODO admin/homebrew
    # TODO write file
    # TODO start container
    # docker run -it linuxbrew/linuxbrew
    # TODO send file to container
    # TODO install from Linuxbrew
    # dcos-docker help

    # TODO move this to tests/

"""
Release the next version.
"""

import datetime
import logging
import re
from pathlib import Path
from typing import List

import click
from dulwich.client import HttpGitClient
from dulwich.porcelain import add, commit, push, tag_list
from dulwich.repo import Repo
from github import Github, Repository, UnknownObjectException

from admin.binaries import make_linux_binaries
from admin.homebrew import get_homebrew_formula


def get_version() -> str:
    """
    Return the next version.
    This is today’s date in the format ``YYYY.MM.DD.MICRO``.
    ``MICRO`` refers to the number of releases created on this date,
    starting from ``0``.
    """
    utc_now = datetime.datetime.utcnow()
    date_format = '%Y.%m.%d'
    date_str = utc_now.strftime(date_format)
    local_repository = Repo('.')
    tag_labels = tag_list(repo=local_repository)
    tag_labels = [item.decode() for item in tag_labels]
    today_tag_labels = [
        item for item in tag_labels if item.startswith(date_str)
    ]
    micro = int(len(today_tag_labels))
    return '{date}.{micro}'.format(date=date_str, micro=micro)


def update_changelog(version: str, changelog: Path) -> None:
    """
    Add a version title to the changelog.
    """
    changelog_contents = changelog.read_text()
    new_changelog_contents = changelog_contents.replace(
        'Next\n----',
        'Next\n----\n\n{version}\n------------'.format(version=version),
    )
    changelog.write_text(new_changelog_contents)


def create_github_release(
    repository: Repository,
    version: str,
) -> None:
    """
    Create a tag and release on GitHub.
    """
    changelog_url = 'https://dcos-e2e.readthedocs.io/en/latest/changelog.html'
    release_name = 'Release ' + version
    release_message = 'See ' + changelog_url
    github_release = repository.create_git_tag_and_release(
        tag=version,
        tag_message='Release ' + version,
        release_name=release_name,
        release_message=release_message,
        type='commit',
        object=repository.get_commits()[0].sha,
        draft=False,
    )

    # The artifacts we build must be built from the tag we just created.
    # This tag is created remotely on GitHub using the GitHub HTTP API.
    #
    # We fetch all tags from GitHub and set our local HEAD to the latest master
    # from GitHub.
    #
    # One symptom of this is that ``minidcos --version`` from the PyInstaller
    # binary shows the correct version.
    local_repository = Repo('.')
    client = HttpGitClient(repository.owner.html_url)
    remote_refs = client.fetch(repository.name + '.git', local_repository)

    # Update the local tags and references with the remote ones.
    for key, value in remote_refs.items():
        local_repository.refs[key] = value

    # Advance local HEAD to remote master HEAD.
    local_repository[b'HEAD'] = remote_refs[b'refs/heads/master']

    # We need to make the artifacts just after creating a tag so that the
    # --version output is exactly the one of the tag.
    # No tag exists when the GitHub release is a draft.
    # This means that temporarily we have a release without binaries.
    linux_artifacts = make_linux_binaries(repo_root=Path('.'))
    for installer_path in linux_artifacts:
        github_release.upload_asset(
            path=str(installer_path),
            label=installer_path.name,
        )


def commit_and_push(
    version: str,
    repository: Repository,
    paths: List[Path],
) -> None:
    """
    Commit and push all changes.
    """
    local_repository = Repo('.')
    _, ignored = add(paths=[str(path) for path in paths])
    assert not ignored
    message = b'Update for release ' + version.encode('utf-8')
    commit(message=message)
    branch_name = 'master'
    push(
        repo=local_repository,
        remote_location=repository.ssh_url,
        refspecs=branch_name.encode('utf-8'),
    )


def update_homebrew(
    homebrew_file: Path,
    version_str: str,
    repository: Repository,
) -> None:
    """
    Update the Homebrew file.
    """
    archive_url = repository.get_archive_link(
        archive_format='tarball',
        ref=version_str,
    )

    homebrew_formula_contents = get_homebrew_formula(
        archive_url=archive_url,
        head_url=repository.clone_url,
        homebrew_recipe_filename=homebrew_file.name,
    )
    homebrew_file.write_text(homebrew_formula_contents)


def update_vagrantfile(version: str, vagrantfile: Path) -> None:
    """
    Update the Vagrantfile.
    """
    vagrantfile_contents = vagrantfile.read_text()
    updated = re.sub(
        r"DEFAULT_DCOS_E2E_REF\s*=\s*'[^']+'",
        "DEFAULT_DCOS_E2E_REF = '{}'".format(version),
        vagrantfile_contents,
        count=1,
    )
    vagrantfile.write_text(updated)


def get_repo(github_token: str, github_owner: str) -> Repository:
    """
    Get a GitHub repository.
    """
    github_client = Github(github_token)
    try:
        github_user_or_org = github_client.get_organization(github_owner)
    except UnknownObjectException:
        github_user_or_org = github_client.get_user(github_owner)

    return github_user_or_org.get_repo('dcos-e2e')


@click.command('release')
@click.argument('github_token')
@click.argument('github_owner')
def release(github_token: str, github_owner: str) -> None:
    """
    Perform a release.
    """
    logging.basicConfig(level=logging.DEBUG)
    repository = get_repo(github_token=github_token, github_owner=github_owner)
    version_str = get_version()
    homebrew_file = Path('minidcos.rb')
    vagrantfile = Path('vagrant/Vagrantfile')
    changelog = Path('CHANGELOG.rst')
    update_changelog(version=version_str, changelog=changelog)
    update_homebrew(
        homebrew_file=homebrew_file,
        version_str=version_str,
        repository=repository,
    )
    update_vagrantfile(vagrantfile=vagrantfile, version=version_str)
    paths = [homebrew_file, changelog, vagrantfile]
    commit_and_push(version=version_str, repository=repository, paths=paths)
    create_github_release(repository=repository, version=version_str)


if __name__ == '__main__':
    release()

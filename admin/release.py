"""
Release the next version of DC/OS E2E.
"""

import datetime
import re
from pathlib import Path
from typing import Set

import click
from dulwich.porcelain import add, commit, push, tag_list
from dulwich.repo import Repo
from github import Github, Repository, UnknownObjectException

from binaries import make_linux_binaries
from homebrew import get_homebrew_formula


def get_version() -> str:
    """
    Return the next version of DC/OS E2E.
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


def update_changelog(version: str) -> None:
    """
    Add a version title to the changelog.
    """
    changelog = Path('CHANGELOG.rst')
    changelog_contents = changelog.read_text()
    new_changelog_contents = changelog_contents.replace(
        'Next\n----',
        'Next\n----\n\n{version}\n------------'.format(version=version),
    )
    changelog.write_text(new_changelog_contents)


def create_github_release(
    repository: Repository,
    version: str,
    artifacts: Set[Path],
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
        draft=True,
    )
    for artifact_path in artifacts:
        github_release.upload_asset(
            path=str(artifact_path),
            label=artifact_path.name,
        )
    github_release.update_release(
        name=release_name,
        message=release_message,
        draft=False,
    )


def commit_and_push(version: str, repository: Repository) -> None:
    """
    Commit and push all changes.
    """
    local_repository = Repo('.')
    paths = ['dcose2e.rb', 'CHANGELOG.rst', 'vagrant/Vagrantfile']
    _, ignored = add(paths=paths)
    assert not ignored
    message = b'Update for release ' + version.encode('utf-8')
    commit(message=message)
    branch_name = 'master'
    push(
        repo=local_repository,
        remote_location=repository.ssh_url,
        refspecs=branch_name.encode('utf-8'),
    )


def update_homebrew(version_str: str, repository: Repository) -> None:
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
    )
    homebrew_file = Path('dcose2e.rb')
    homebrew_file.write_text(homebrew_formula_contents)


def update_vagrantfile(version: str) -> None:
    """
    Update the Vagrantfile.
    """
    vagrantfile = Path('vagrant/Vagrantfile')
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
    repository = get_repo(github_token=github_token, github_owner=github_owner)
    version_str = get_version()
    update_changelog(version=version_str)
    update_homebrew(
        version_str=version_str,
        repository=repository,
    )
    update_vagrantfile(version=version_str)
    linux_artifacts = make_linux_binaries(repo_root=Path('.'))
    commit_and_push(version=version_str, repository=repository)
    create_github_release(
        repository=repository,
        version=version_str,
        artifacts=linux_artifacts,
    )


if __name__ == '__main__':
    release()

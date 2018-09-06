"""
Release the next version of DC/OS E2E.
"""

import datetime
import os
import re
import subprocess
from pathlib import Path
from textwrap import dedent

from dulwich.porcelain import add, commit, push, tag_list
from dulwich.repo import Repo
from github import Github, Repository, UnknownObjectException


def get_homebrew_formula(version: str, repository: Repository) -> str:
    """
    Return the contents of a Homebrew formula for the DC/OS E2E CLI.
    """
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    lines = requirements_file.read_text().strip().split('\n')
    requirements = [line for line in lines if not line.startswith('#')]
    # At the time of writing, with the latest versions of the DC/OS E2E direct
    # dependencies, there is a version conflict for ``msrestazure``, an
    # indirect dependency.
    # Therefore, we pin a particular version which satisfies all requirements.
    # See DCOS-40131.
    requirements.append('msrestazure==0.4.34')

    # Without the following, some users get:
    # The 'secretstorage' distribution was not found and is required by keyring
    requirements.append('secretstorage')

    first = requirements[0]

    args = ['poet', first]
    for requirement in requirements[1:]:
        args.append('--also')
        args.append(requirement)

    result = subprocess.run(args=args, stdout=subprocess.PIPE, check=True)
    resource_stanzas = str(result.stdout.decode())

    # We could use:
    # ```
    # repository.get_archive_link(archive_format='tarball', version=version)
    # ```
    #
    # However, this is broken in PyGitHub 1.40, and will be fixed in the next
    # release to PyPI.
    archive_url = '{html_url}/archive/{version}.tar.gz'.format(
        html_url=repository.html_url,
        version=version,
    )
    pattern = dedent(
        """\
        class Dcose2e < Formula
          include Language::Python::Virtualenv

          url "{archive_url}"
          head "{clone_url}"
          homepage "http://dcos-e2e.readthedocs.io/en/latest/cli.html"
          depends_on "python3"
          depends_on "pkg-config"

        {resource_stanzas}

          def install
            virtualenv_install_with_resources
          end

          test do
              ENV["LC_ALL"] = "en_US.utf-8"
              ENV["LANG"] = "en_US.utf-8"
              system "#{{bin}}/dcos_docker", "--help"
          end
        end
        """,
    )

    return pattern.format(
        resource_stanzas=resource_stanzas,
        archive_url=archive_url,
        version=version,
        clone_url=repository.clone_url,
    )


def get_version() -> str:
    """
    Returns the next version of DC/OS E2E.
    This is today’s date in the format ``YYYY.MM.DD.MICRO``.
    ``MICRO`` refers to the number of releases created on this date,
    starting from ``0``.
    """
    utc_now = datetime.datetime.utcnow()
    date_format = '%Y.%m.%d'
    date_str = utc_now.strftime(date_format)
    repo = Repo('.')
    tag_labels = tag_list(repo)
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
) -> None:
    """
    Create a tag and release on GitHub.
    """
    changelog_url = 'https://dcos-e2e.readthedocs.io/en/latest/changelog.html'
    repository.create_git_tag_and_release(
        tag=version,
        tag_message='Release ' + version,
        release_name='Release ' + version,
        release_message='See ' + changelog_url,
        type='commit',
        object=repository.get_commits()[0].sha,
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
    homebrew_formula_contents = get_homebrew_formula(
        version=version_str,
        repository=repository,
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


def main() -> None:
    github_token = os.environ['GITHUB_TOKEN']
    github_owner = os.environ['GITHUB_OWNER']
    repository = get_repo(github_token=github_token, github_owner=github_owner)
    version_str = get_version()
    update_changelog(version=version_str)
    update_homebrew(
        version_str=version_str,
        repository=repository,
    )
    update_vagrantfile(version=version_str)
    commit_and_push(version=version_str, repository=repository)
    create_github_release(
        repository=repository,
        version=version_str,
    )


if __name__ == '__main__':
    main()

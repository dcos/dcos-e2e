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
from github import Github


def get_homebrew_formula(version: str) -> str:
    """
    Return the contents of a Homebrew formula for the DC/OS E2E CLI.
    """
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    lines = requirements_file.read_text().strip().split('\n')
    requirements = [line for line in lines if not line.startswith('#')]
    first = requirements[0]

    args = ['poet', first]
    for requirement in requirements[1:]:
        args.append('--also')
        args.append(requirement)

    result = subprocess.run(args=args, stdout=subprocess.PIPE)
    resource_stanzas = str(result.stdout.decode())

    pattern = dedent(
        """\
        class Dcosdocker < Formula
          include Language::Python::Virtualenv

          url "https://github.com/mesosphere/dcos-e2e/archive/{version}.tar.gz"
          head "https://github.com/mesosphere/dcos-e2e.git"
          homepage "http://dcos-e2e.readthedocs.io/en/latest/cli.html"
          depends_on "python3"

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

    return pattern.format(resource_stanzas=resource_stanzas, version=version)


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
    github_token: str,
    version: str,
) -> None:
    """
    Create a tag and release on GitHub.
    """
    github_client = Github(github_token)
    org = github_client.get_organization('mesosphere')
    repository = org.get_repo('dcos-e2e')
    changelog_url = 'https://dcos-e2e.readthedocs.io/en/latest/changelog.html'
    repository.create_git_tag_and_release(
        tag=version,
        tag_message='Release ' + version,
        release_name='Release ' + version,
        release_message='See ' + changelog_url,
        type='commit',
        object=repository.get_commits()[0].sha,
    )


def commit_and_push(version: str) -> None:
    """
    Commit and push all changes.
    """
    repo = Repo('.')
    paths = ['dcosdocker.rb', 'CHANGELOG.rst', 'vagrant/Vagrantfile']
    _, ignored = add(paths=paths)
    assert not ignored
    message = b'Update for release ' + version.encode('utf-8')
    commit(message=message)
    branch_name = 'master'
    push(
        repo=repo,
        remote_location='git@github.com:mesosphere/dcos-e2e.git',
        refspecs=branch_name.encode('utf-8'),
    )


def update_homebrew(version_str: str) -> None:
    """
    Update the Homebrew file.
    """
    homebrew_formula_contents = get_homebrew_formula(version=version_str)
    homebrew_file = Path('dcosdocker.rb')
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


def main() -> None:
    github_token = os.environ['GITHUB_TOKEN']
    version_str = get_version()
    update_changelog(version=version_str)
    update_homebrew(version_str=version_str)
    update_vagrantfile(version=version_str)
    commit_and_push(version=version_str)
    create_github_release(
        github_token=github_token,
        version=version_str,
    )


if __name__ == '__main__':
    main()

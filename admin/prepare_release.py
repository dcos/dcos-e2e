"""
Switch to a release branch for the next version of DC/OS E2E.
"""

import datetime
import os
import uuid
import subprocess
from pathlib import Path
from textwrap import dedent

import docutils
import docutils.parsers.rst
from dulwich.porcelain import branch_create, tag_list
from dulwich.repo import Repo


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

          url "https://github.com/mesosphere/dcos-e2e.git#{version}"
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
        """
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


def checkout_new_branch(branch_name: str) -> None:
    """"
    Create and checkout a branch.
    """
    branch_create(repo='.', name=branch_name.encode('utf-8'))
    repo = Repo('.')
    repo.refs.set_symbolic_ref(
        b'HEAD',
        b'refs/heads/' + branch_name.encode('utf-8'),
    )


def get_changelog_text() -> str:
    """
    XXX
    """
    changelog = Path('CHANGELOG.rst')
    source = changelog.read_text()
    document_name = uuid.uuid4().hex
    settings = docutils.frontend.OptionParser(
        components=(docutils.parsers.rst.Parser,)
    ).get_default_values()
    document = docutils.utils.new_document(document_name, settings)

    parser = docutils.parsers.rst.Parser()
    parser.parse(source, document)
    children = document.traverse()
    for item in children:
        try:
            [item_id] = item['ids']
        except (ValueError, TypeError):
            continue
        if item_id == 'next':
            bullet_list_index = item.first_child_matching_class(
                childclass=docutils.nodes.bullet_list,
            )
            bullet_list = item[bullet_list_index]
            return bullet_list.astext()
    return ''

def create_github_release(
    changelog_contents: str,
    github_username: str,
    github_password: str,
    version: str,
) -> None:
    """
    XXX
    """
        # if 'Next' in item.__repr__() and not item.children:
        #     print(item.__repr__())
        #     import pdb; pdb.set_trace()
        #     pass
        # if item.text == '
        # # import pdb; pdb.set_trace()
        # pass


def update_homebrew() -> None:
    """
    Update the Homebrew file.
    """
    homebrew_formula_contents = get_homebrew_formula(version=version_str)
    homebrew_file = Path('dcosdocker.rb')
    homebrew_file.write_text(homebrew_formula_contents)


def main() -> None:
    github_username = os.environ['GITHUB_USERNAME']
    github_password = os.environ['GITHUB_PASSWORD']
    version_str = get_version()
    # branch_name = 'release-' + version_str
    # checkout_new_branch(branch_name=branch_name)
    # update_homebrew()
    # update_changelog(version=version_str)
    # Commit
    # Push
    # Create PR
    # Merge into master
    create_github_release(
        github_username=github_username,
        github_password=github_password,
        version=version_str,
    )


if __name__ == '__main__':
    main()

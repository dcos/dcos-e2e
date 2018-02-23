"""
Switch to a release branch for the next version of DC/OS E2E.
"""

import datetime
import os
import subprocess
import uuid
from pathlib import Path
from textwrap import dedent

import docutils
import docutils.parsers.rst
from dulwich.porcelain import add, branch_create, commit, push, tag_list
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


def get_changelog_contents() -> str:
    """
    XXX
    """
    changelog = Path('CHANGELOG.rst')
    source = changelog.read_text()
    document_name = uuid.uuid4().hex
    settings = docutils.frontend.OptionParser(
        components=(docutils.parsers.rst.Parser, )
    ).get_default_values()
    document = docutils.utils.new_document(document_name, settings)

    parser = docutils.parsers.rst.Parser()
    parser.parse(source, document)
    try:
        [next_section] = [
            item for item in document.traverse()
            if 'ids' in item and item['ids'] == ['next']
        ]
    except ValueError:
        raise ValueError('Expecting section titled "Next" in CHANGELOG.rst')

    bullet_list_index = next_section.first_child_matching_class(
        childclass=docutils.nodes.bullet_list,
    )

    if bullet_list_index is None:
        # There are no items in the "Next" section.
        return ''

    bullet_list = next_section[bullet_list_index]
    list_items = [bullet.astext() for bullet in bullet_list]
    result = ''
    for item in list_items:
        result += '* ' + item + '\n\n'
    return result.strip()


def create_github_release(
    changelog_contents: str,
    github_username: str,
    github_password: str,
    version: str,
) -> None:
    """
    XXX
    """


def commit_and_push(version: str, branch_name: str) -> None:
    repo = Repo('.')
    add()
    commit_ref = commit(message=b'Update for release')
    ref_name = 'refs/heads/{branch_name}'.format(branch_name=branch_name)
    repo.refs[ref_name.encode('utf-8')] = commit_ref
    # import pdb; pdb.set_trace()
    push(
        repo=repo,
        remote_location='git@github.com:mesosphere/dcos-e2e.git',
        # refspecs=ref_name.encode('utf-8'),
        refspecs=branch_name.encode('utf-8'),
    )
    import pdb; pdb.set_trace()

    pass


def update_homebrew(version_str: str) -> None:
    """
    Update the Homebrew file.
    """
    homebrew_formula_contents = get_homebrew_formula(version=version_str)
    homebrew_file = Path('dcosdocker.rb')
    homebrew_file.write_text(homebrew_formula_contents)


def main() -> None:
    github_username = os.environ['GITHUB_USERNAME']
    github_password = os.environ['GITHUB_PASSWORD']
    changelog_contents = get_changelog_contents()
    version_str = get_version()
    branch_name = 'release-' + version_str
    commit_and_push(version=version_str, branch_name=branch_name)
    return
    # checkout_new_branch(branch_name=branch_name)
    # update_homebrew(version_str=version_str)
    update_changelog(version=version_str)
    commit_and_push()
    # Commit
    # Push
    # Create PR
    # Merge into master
    print(changelog_contents)
    create_github_release(
        changelog_contents=changelog_contents,
        github_username=github_username,
        github_password=github_password,
        version=version_str,
    )


if __name__ == '__main__':
    main()

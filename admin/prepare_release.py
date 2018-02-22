"""
Switch to a release branch for the next version of DC/OS E2E.
"""

import datetime
import subprocess
from pathlib import Path
from textwrap import dedent

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


def update_changelog() -> None:
    pass


def main() -> None:
    version_str = get_version()
    branch_name = 'release-' + version_str
    branch_create(repo='.', name=branch_name.encode('utf-8'))
    repo = Repo('.')
    repo.refs.set_symbolic_ref(
        b'HEAD',
        b'refs/heads/' + branch_name.encode('utf-8'),
    )
    homebrew_formula_contents = get_homebrew_formula(version=version_str)
    homebrew_file = Path('dcosdocker.rb')
    homebrew_file.write_text(homebrew_formula_contents)


if __name__ == '__main__':
    main()

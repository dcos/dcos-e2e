"""
Tools for creating Homebrew recipes.
"""

import subprocess
from pathlib import Path
from textwrap import dedent


def get_homebrew_formula(archive_url: str, head_url: str) -> str:
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

    pattern = dedent(
        """\
        class Dcose2e < Formula
          include Language::Python::Virtualenv

          url "{archive_url}"
          head "{head_url}"
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
        head_url=head_url,
    )

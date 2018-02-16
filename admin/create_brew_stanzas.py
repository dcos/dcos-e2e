import subprocess
from pathlib import Path
from textwrap import dedent
from typing import List


def get_requirements(requirements_file: Path) -> List[str]:
    lines = requirements_file.read_text().strip().split('\n')
    return [line for line in lines if not line.startswith('#')]


def get_resource_stanzas(requirements: List[str]) -> str:
    first = requirements[0]

    args = ['poet', first]
    for requirement in requirements[1:]:
        args.append('--also')
        args.append(requirement)

    result = subprocess.run(args=args, stdout=subprocess.PIPE)
    return str(result.stdout.decode())


def get_formula(resource_stanzas: str) -> str:

    pattern = dedent(
        """\
        class Dcosdocker < Formula
          include Language::Python::Virtualenv

          url "https://github.com/mesosphere/dcos-e2e.git"
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

    return pattern.format(resource_stanzas=resource_stanzas)


def main() -> str:
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    requirements = get_requirements(requirements_file=requirements_file)
    resource_stanzas = get_resource_stanzas(requirements=requirements)
    return get_formula(resource_stanzas=resource_stanzas)


if __name__ == '__main__':
    print(main())

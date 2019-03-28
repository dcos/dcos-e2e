"""
Tools for creating Homebrew recipes.
"""

import subprocess
from pathlib import Path
from textwrap import dedent
from typing import List


def _get_dependencies(requirements_file: Path) -> List[str]:
    """
    Return requirements from a requirements file.

    This expects a requirements file with no ``--find-links`` lines.
    """
    lines = requirements_file.read_text().strip().split('\n')
    return [line for line in lines if not line.startswith('#')]


def _get_class_name(homebrew_recipe_filename: str) -> str:
    """
    The Ruby class name depends on the file name.

    The first character is capitalized.
    Some characters are removed, and if a character is removed, the next
    character is capitalized.

    Returns:
        The Ruby class name to use, given a file name.
    """
    stem = Path(homebrew_recipe_filename).stem
    disallowed_characters = {'-', '.', '+'}
    class_name = ''
    for index, character in enumerate(list(stem)):
        if character not in disallowed_characters:
            if index == 0:
                class_name += character.upper()
            elif list(stem)[index - 1] in disallowed_characters:
                class_name += character.upper()
            else:
                class_name += character

    return class_name


def get_homebrew_formula(
    archive_url: str,
    head_url: str,
    homebrew_recipe_filename: str,
) -> str:
    """
    Return the contents of a Homebrew formula for the CLIs.
    """
    repository_root = Path(__file__).parent.parent
    indirect_requires = _get_dependencies(
        requirements_file=repository_root / 'indirect-requirements.txt',
    )

    direct_requires = _get_dependencies(
        requirements_file=repository_root / 'requirements.txt',
    )

    requirements = indirect_requires + direct_requires

    first = requirements[0]

    args = ['poet', first]
    for requirement in requirements[1:]:
        args.append('--also')
        args.append(requirement)

    result = subprocess.run(args=args, stdout=subprocess.PIPE, check=True)
    resource_stanzas = str(result.stdout.decode())
    homepage_url = 'http://minidcos.readthedocs.io/en/latest/'

    pattern = dedent(
        """\
        class {class_name} < Formula
          include Language::Python::Virtualenv

          url "{archive_url}"
          head "{head_url}"
          homepage "{homepage_url}"
          depends_on "python3"
          depends_on "pkg-config"

        {resource_stanzas}

          def install
            # Without this we hit various issues including
            # https://github.com/takluyver/flit/issues/245.
            # All of these issues are caught by CI so it is safe to remove this
            # and then run CI.
            ENV["PIP_USE_PEP517"] = "false"
            virtualenv_install_with_resources
          end

          test do
              system "#{{bin}}/dcos_docker", "--help"
          end
        end
        """,
    )

    class_name = _get_class_name(
        homebrew_recipe_filename=homebrew_recipe_filename,
    )
    return pattern.format(
        class_name=class_name,
        resource_stanzas=resource_stanzas,
        archive_url=archive_url,
        head_url=head_url,
        homepage_url=homepage_url,
    )

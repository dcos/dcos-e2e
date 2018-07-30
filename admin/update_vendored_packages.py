"""
Vendor some requirements.
"""

import subprocess
import sys
from pathlib import Path

import vendorize


class _Requirement:
    """
    A requirement to vendor.
    """

    def __init__(
        self,
        target_directory: Path,
        package_name: str,
        https_address: str,
        git_reference: str,
    ) -> None:
        """
        Details of a requirement to vendor.
        """
        self.target_directory = target_directory
        self.package_name = package_name
        self.https_address = https_address
        self.git_reference = git_reference


def main() -> None:
    """
    We vendor some requirements.

    We use our own script as we want the vendored ``dcos_launch`` to use the
    vendored ``dcos_test_utils``.
    """
    dcos_e2e_target_directory = Path('src/dcos_e2e/_vendor')
    dcos_cli_target_directory = Path('src/cli/_vendor')

    dcos_launch = _Requirement(
        target_directory=dcos_e2e_target_directory,
        package_name='dcos_launch',
        https_address='https://github.com/dcos/dcos-launch',
        git_reference='339f61828ab239726ae923b55b8a5fb9d12f4abb',
    )

    test_utils = _Requirement(
        target_directory=dcos_e2e_target_directory,
        package_name='dcos_test_utils',
        https_address='https://github.com/dcos/dcos-test-utils',
        git_reference='3ebfc18ff9c5a1aa382311474a9192a68c98b0a7',
    )

    # We have a fix at https://github.com/click-contrib/sphinx-click/pull/27
    # that we require.
    sphinx_click = _Requirement(
        target_directory=dcos_e2e_target_directory,
        package_name='sphinx_click',
        https_address='https://github.com/adamtheturtle/sphinx-click',
        git_reference='fix-envvar-duplicates',
    )

    vertigo_e2e = _Requirement(
        target_directory=dcos_e2e_target_directory,
        package_name='vertigo',
        https_address='https://github.com/adamtheturtle/vertigo',
        git_reference='77d7aa5d994e2650ece9e8aded6e9bffda21a2ac',
    )

    vertigo_cli = _Requirement(
        target_directory=dcos_cli_target_directory,
        package_name='vertigo',
        https_address='https://github.com/adamtheturtle/vertigo',
        git_reference='77d7aa5d994e2650ece9e8aded6e9bffda21a2ac',
    )

    requirements = [
        dcos_launch,
        test_utils,
        sphinx_click,
        vertigo_e2e,
        vertigo_cli,
    ]
    target_directories = set(
        requirement.target_directory for requirement in requirements
    )

    for target_directory in target_directories:
        try:
            target_directory.mkdir(exist_ok=False)
        except FileExistsError:
            message = (
                'Error: {target_directory} exists. '
                'Run the following commands before running this script again:'
                '\n\n'
                'git rm -rf {target_directory}\n'
                'rm -rf {target_directory}'
            )

            print(message.format(target_directory=target_directory))
            sys.exit(1)

        init_file = Path(target_directory) / '__init__.py'
        Path(init_file).touch()

    for requirement in requirements:
        uri = 'git+{https_address}@{reference}'.format(
            https_address=requirement.https_address,
            reference=requirement.git_reference,
        )

        subprocess.check_call(
            [
                'pip',
                'install',
                '--no-dependencies',
                '--target',
                str(requirement.target_directory),
                uri,
            ],
        )

    for target_directory in target_directories:
        # Ideally we would not use a protected function, however, this
        # trade-off has been considered - we want to use the vendored
        # ``dcos_test_utils`` from the vendored ``dcos_launch``.
        package_names = [
            requirement.package_name for requirement in requirements
            if requirement.target_directory == target_directory
        ]
        vendorize._rewrite_imports(  # pylint: disable=protected-access
            target_directory=target_directory,
            top_level_names=package_names,
        )


if __name__ == '__main__':
    main()

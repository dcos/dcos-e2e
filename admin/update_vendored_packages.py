"""
Vendor some requirements.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List

import vendorize
from dulwich.porcelain import add, commit, ls_files, remove


class _Requirement:
    """
    A requirement to vendor.
    """

    def __init__(
        self,
        target_directory: Path,
        package_name: str,
        install_directories: List[str],
        https_address: str,
        git_reference: str,
    ) -> None:
        """
        Details of a requirement to vendor.
        """
        self.target_directory = target_directory
        self.package_name = package_name
        self.install_directories = install_directories
        self.https_address = https_address
        self.git_reference = git_reference


def _get_requirements() -> List[_Requirement]:
    """
    Return all requirements to vendor.
    """
    dcos_e2e_target_directory = Path('src/dcos_e2e/_vendor')
    dcos_cli_target_directory = Path('src/dcos_e2e_cli/_vendor')

    dcos_launch = _Requirement(
        target_directory=dcos_e2e_target_directory,
        package_name='dcos_launch',
        install_directories=['dcos_launch'],
        https_address='https://github.com/dcos/dcos-launch',
        git_reference='5df9c68a5a5f41a5bf201b961eb54140ac324635',
    )

    test_utils = _Requirement(
        target_directory=dcos_e2e_target_directory,
        package_name='dcos_test_utils',
        install_directories=['dcos_test_utils', 'pytest_dcos'],
        https_address='https://github.com/dcos/dcos-test-utils',
        git_reference='0957dc87e05d8b14c42e188de6a9e926839716c6',
    )

    dcos_launch_cli = _Requirement(
        target_directory=dcos_cli_target_directory,
        package_name='dcos_launch',
        install_directories=['dcos_launch'],
        https_address='https://github.com/dcos/dcos-launch',
        git_reference='5df9c68a5a5f41a5bf201b961eb54140ac324635',
    )

    test_utils_cli = _Requirement(
        target_directory=dcos_cli_target_directory,
        package_name='dcos_test_utils',
        install_directories=['dcos_test_utils', 'pytest_dcos'],
        https_address='https://github.com/dcos/dcos-test-utils',
        git_reference='0957dc87e05d8b14c42e188de6a9e926839716c6',
    )

    vertigo_e2e = _Requirement(
        target_directory=dcos_e2e_target_directory,
        package_name='vertigo',
        install_directories=['vertigo_py'],
        https_address='https://github.com/adamtheturtle/vertigo',
        git_reference='77d7aa5d994e2650ece9e8aded6e9bffda21a2ac',
    )

    vertigo_cli = _Requirement(
        target_directory=dcos_cli_target_directory,
        package_name='vertigo',
        install_directories=['vertigo_py'],
        https_address='https://github.com/adamtheturtle/vertigo',
        git_reference='77d7aa5d994e2650ece9e8aded6e9bffda21a2ac',
    )

    dcos_installer_tools = _Requirement(
        target_directory=dcos_cli_target_directory,
        package_name='dcos_installer_tools',
        install_directories=['dcos_installer_tools'],
        https_address='https://github.com/adamtheturtle/dcos-installer-tools',
        git_reference='8550cf77f0f8e9878ad4d6ec9980f675b656d966',
    )

    requirements = [
        dcos_installer_tools,
        dcos_launch,
        test_utils,
        dcos_launch_cli,
        test_utils_cli,
        vertigo_e2e,
        vertigo_cli,
    ]

    return requirements


def _remove_existing_files(requirements: List[_Requirement]) -> None:
    """
    Remove existing files in vendored target directories.
    """
    target_directories = set(
        requirement.target_directory for requirement in requirements
    )

    repo_files = ls_files(repo='.')
    for target_directory in target_directories:
        git_paths = [
            item.decode() for item in repo_files
            if item.decode().startswith(str(target_directory))
        ]
        remove(paths=git_paths)
        try:
            shutil.rmtree(path=str(target_directory))
        except FileNotFoundError:
            pass


def _vendor_requirements(requirements: List[_Requirement]) -> None:
    """
    Clone vendored requirements.
    """
    target_directories = set(
        requirement.target_directory for requirement in requirements
    )

    for target_directory in target_directories:
        target_directory.mkdir(exist_ok=True)
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
                '--no-binary',
                ':all:',
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


def _commit_vendored(requirements: List[_Requirement]) -> None:
    """
    Commit files for vendored requirements.
    """
    for requirement in requirements:
        add(paths=[str(requirement.target_directory / '__init__.py')])
        for install_directory in requirement.install_directories:
            directory = requirement.target_directory / install_directory
            for item in directory.glob('**/*'):
                add(paths=[str(item)])
    commit(message='Update vendored packages')


def _remove_untracked_files(requirements: List[_Requirement]) -> None:
    """
    Remove files downloaded by pip which are not tracked by git.
    """
    target_directories = set(
        requirement.target_directory for requirement in requirements
    )
    repo_files = ls_files(repo='.')
    for target_directory in target_directories:
        git_paths = [
            item.decode() for item in repo_files
            if item.decode().startswith(str(target_directory))
        ]

        for item in target_directory.iterdir():
            if not [path for path in git_paths if path.startswith(str(item))]:
                shutil.rmtree(path=str(item))


def main() -> None:
    """
    We vendor some requirements.

    We use our own script as we want the vendored ``dcos_launch`` to use the
    vendored ``dcos_test_utils``.
    """
    requirements = _get_requirements()
    _remove_existing_files(requirements=requirements)
    _vendor_requirements(requirements=requirements)
    _commit_vendored(requirements=requirements)
    _remove_untracked_files(requirements=requirements)


if __name__ == '__main__':
    main()

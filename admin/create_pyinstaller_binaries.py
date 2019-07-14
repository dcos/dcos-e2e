"""
Make PyInstaller binaries for the platform that this is being run on.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import Set

import click
import pkg_resources

import dcos_e2e


def is_editable() -> bool:
    """
    Return whether this project is an editable package.

    See https://stackoverflow.com/a/40835950.
    """
    package_name = dcos_e2e.__name__
    # Normalize as per https://www.python.org/dev/peps/pep-0440/.
    normalized_package_name = package_name.replace('_', '-').lower()
    distributions = {v.key: v for v in set(pkg_resources.working_set)}
    distribution = distributions[normalized_package_name]
    project_name = distribution.project_name
    for path_item in sys.path:
        egg_link = Path(path_item) / (project_name + '.egg-link')
        if egg_link.exists():
            return True
    return False


def require_not_editable(editable: bool) -> None:
    """
    Require the package to have been installed not in editable mode.
    """

    message = dedent(
        """\
        We explicitly require the package to have been installed without the
        use of ``-e / --editable``.

        This is because ``versioneer`` replaces the dynamic ``_version.py``
        file with a static one only when creating a non-editable Python EGG.

        This is required for the PyInstaller binary to determine the version
        string because the git tags used by the dynamic ``_version.py`` are not
        included.

        Use --accept-editable to ignore this error.
        """,
    )
    if editable:
        raise Exception(message)


def remove_existing_files(scripts: Set[Path]) -> None:
    """
    Remove files created when building binaries.

    This is to stop interference with future builds.
    """
    dist_dir = Path('.') / 'dist'
    build_dir = Path('.') / 'build'
    try:
        shutil.rmtree(path=str(dist_dir))
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(path=str(build_dir))
    except FileNotFoundError:
        pass

    for script in scripts:
        path = Path(script.name + '.spec')
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def create_binary(script: Path, repo_root: Path) -> None:
    """
    Use PyInstaller to create a binary from a script.

    Args:
        script: The script to create a binary for.
        repo_root: The path to the root of the repository.
    """
    # MANIFEST.in describes files that must be available which are not
    # necessarily Python files.
    # These include e.g. Dockerfiles.
    # We still need to include these in the binary.
    datas = []
    manifest = repo_root / 'MANIFEST.in'
    with manifest.open() as manifest_file:
        for line in manifest_file.readlines():
            if line.startswith('recursive-include'):
                _, manifest_path, _ = line.split()
            else:
                _, manifest_path = line.split()
            if manifest_path.startswith('src/'):
                if Path(manifest_path).is_file():
                    parent = Path(manifest_path).parent
                    manifest_path = str(parent)

                path_without_src = manifest_path[len('src/'):]
                data_item = (str(repo_root / manifest_path), path_without_src)
                datas.append(data_item)

    pyinstaller_command = ['pyinstaller', str(script.resolve()), '--onefile']
    for data in datas:
        source, destination = data
        data_str = '{source}:{destination}'.format(
            source=source,
            destination=destination,
        )
        add_data_command = ['--add-data', data_str]
        pyinstaller_command += add_data_command

    subprocess.check_output(args=pyinstaller_command)


@click.command('create_binaries')
@click.option(
    '--accept-editable',
    is_flag=True,
    help=(
        'For --version to work appropriately on the binary, we require the '
        'package to be installed not in --editable mode. '
        'Use this flag to override that requirement.'
    ),
)
def create_binaries(accept_editable: bool) -> None:
    """
    Make PyInstaller binaries for the platform that this is being run on.

    All binaries will be created in ``./dist``.
    """
    editable = is_editable()
    if not accept_editable:
        require_not_editable(editable=editable)
    repo_root = Path(__file__).resolve().parent.parent
    script_dir = repo_root / 'bin'
    scripts = set(script_dir.iterdir())
    remove_existing_files(scripts=scripts)
    for script in scripts:
        create_binary(script=script, repo_root=repo_root)


if __name__ == '__main__':
    create_binaries()

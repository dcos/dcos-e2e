"""
Make PyInstaller binaries for the platform that this is being run on.

For this to work as expected, we expect that NOT EDITABLE.
"""

import dcos_e2e

import pkg_resources
import shutil
import subprocess
import sys
from pathlib import Path

def is_editable() -> bool:
    """
    Return whether this project is an editable package.

    See https://stackoverflow.com/a/40835950.
    """
    package_name = dcos_e2e.__name__
    # Normalize as per https://www.python.org/dev/peps/pep-0440/.
    normalized_package_name = package_name.replace('_', '-').lower()
    distributions = {v.key: v for v in pkg_resources.working_set}
    distribution = distributions[normalized_package_name]
    project_name = distribution.project_name
    for path_item in sys.path:
        egg_link = Path(path_item) / (project_name + '.egg-link')
        if egg_link.exists():
            return True
    return False

def remove_existing_files(repo_root: Path) -> None:
    dist_dir = repo_root / 'dist'
    build_dir = repo_root / 'build'
    try:
        shutil.rmtree(path=dist_dir)
    except FileNotFoundError:
        pass

    try:
        shutil.rmtree(path=build_dir)
    except FileNotFoundError:
        pass

    for path in repo_root.glob('dcos-*.spec'):
        path.unlink()


def create_binary(script: Path) -> None:
    # MANIFEST.in describes files that must be available which are not
    # necessarily Python files.
    # These include e.g. Dockerfiles.
    # We still need to include these in the binary.
    datas = []
    with open('MANIFEST.in') as manifest_file:
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
                datas.append((manifest_path, path_without_src))

    pyinstaller_command = ['pyinstaller', script.resolve(), '--onefile']
    for data in datas:
        source, destination = data
        data_str = '{source}:{destination}'.format(
            source=source,
            destination=destination,
        )
        add_data_command = ['--add-data', data_str]
        pyinstaller_command += add_data_command

    subprocess.check_output(args=pyinstaller_command)


if __name__ == '__main__':
    print(is_editable())
    # TODO Check if version file exists
    # repo_root = Path(__file__).parent.parent
    # remove_existing_files(repo_root=repo_root)
    # script_dir = repo_root / 'bin'
    # for script in script_dir.iterdir():
    #     create_binary(script=script)

"""
Make PyInstaller binaries for the platform that this is being run on.

For this to work as expected, we expect that NOT EDITABLE.
"""

import shutil
import subprocess
from pathlib import Path


def remove_existing_files(repo_root: Path) -> None:
    dist_dir = repo_root / 'dist'
    build_dir = repo_root / 'build'
    shutil.rmtree(path=dist_dir)
    shutil.rmtree(path=build_dir)
    if dist_dir.exists():
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
    repo_root = Path(__file__).parent.parent
    remove_existing_files(repo_root=repo_root)
    script_dir = repo_root / 'bin'
    for script in script_dir.iterdir():
        create_binary(script=script)

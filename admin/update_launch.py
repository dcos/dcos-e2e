"""
Vendor some requirements.
"""

import subprocess
import sys
from pathlib import Path

import vendorize


def main() -> None:
    """
    We vendor some requirements.

    We use our own script as we want the vendored ``dcos_launch`` to use the
    vendored ``dcos_test_utils``.
    """
    vendored_launch_sha = 'fad6d70caf282f7260d2d7af88f044ccfd64f8c7'
    vendored_test_utils_sha = 'a4cd8815fde6624a645c83eef85abde88b73a38f'

    launch = 'git+https://github.com/dcos/dcos-launch@{sha}'.format(
        sha=vendored_launch_sha,
    )

    test_utils = 'git+https://github.com/dcos/dcos-test-utils@{sha}'.format(
        sha=vendored_test_utils_sha,
    )

    package_name_to_uri = {
        'dcos_launch': launch,
        'dcos_test_utils': test_utils,
    }

    target_directory = Path('src/dcos_e2e/_vendor')
    try:
        target_directory.mkdir(exist_ok=False)
    except FileExistsError:
        message = (
            'Error: {target_directory} exists. '
            'Run the following commands before running this script again:'
            '\n\n'
            'git rm -rf {target_directory}\n'
            'rm -rf src/dcos_e2e/_vendor'
        )

        print(message.format(target_directory=target_directory))
        sys.exit(1)

    init_file = Path(target_directory) / '__init__.py'
    Path(init_file).touch()

    for _, requirement in package_name_to_uri.items():
        subprocess.check_call(
            [
                'pip',
                'install',
                '--no-dependencies',
                '--target',
                str(target_directory),
                requirement,
            ],
        )

    # Ideally we would not use a protected function, however, this trade-off
    # has been considered - we want to use the vendored ``dcos_test_utils``
    # from the vendored ``dcos_launch``.
    vendorize._rewrite_imports(  # pylint: disable=protected-access
        target_directory=target_directory,
        top_level_names=list(package_name_to_uri.keys()),
    )


if __name__ == '__main__':
    main()

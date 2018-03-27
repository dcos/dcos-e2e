"""
Vendor some requirements.
"""

import vendorize
import os
import subprocess
from pathlib import Path


def main() -> None:
    launch_url = 'git+https://github.com/dcos/dcos-launch@fad6d70caf282f7260d2d7af88f044ccfd64f8c7'  # noqa: E501
    test_utils_url = 'git+https://github.com/dcos/dcos-test-utils@a4cd8815fde6624a645c83eef85abde88b73a38f'  # noqa: E501
    target_directory = 'src/dcos_e2e/_vendor'
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    init_file = Path(target_directory) / '__init__.py'
    Path(init_file).touch()

    for requirement in [launch_url, test_utils_url]:
        subprocess.check_call(
            [
                'pip',
                'install',
                '--no-dependencies',
                '--target',
                target_directory,
                requirement,
            ],
        )

    top_level_names = ['dcos_launch', 'dcos_test_utils']

    # Ideally we would not use a protected function, however, this trade-off
    # has been considered - we want to use the vendored ``dcos_test_utils``
    # from the vendored ``dcos_launch``.
    vendorize._rewrite_imports(  # pylint: disable=protected-access
        target_directory=target_directory,
        top_level_names=top_level_names,
    )


if __name__ == '__main__':
    main()

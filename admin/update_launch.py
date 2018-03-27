"""
Vendor some requirements.
"""

import vendorize
import subprocess
from pathlib import Path


def main() -> None:
    package_name_to_url = {
        'dcos_launch': 'git+https://github.com/dcos/dcos-launch@fad6d70caf282f7260d2d7af88f044ccfd64f8c7',  # noqa: E501
        'dcos_test_utils': 'git+https://github.com/dcos/dcos-test-utils@a4cd8815fde6624a645c83eef85abde88b73a38f',  # noqa: E501
    }
    target_directory = 'src/dcos_e2e/_vendor'
    init_file = Path(target_directory) / '__init__.py'
    Path(init_file).touch()

    for _, requirement in package_name_to_url.items():
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

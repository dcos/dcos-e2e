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
    launch = (
        'dcos_launch',
        'git+https://github.com/dcos/dcos-launch',
        '09c1d53652d8e91aad5f1c246ef24646de2eb4c1',
    )

    test_utils = (
        'dcos_test_utils',
        'git+https://github.com/dcos/dcos-test-utils',
        '00f1a62ef673ebc34e29d9db488dd06b0c1ae4ec',
    )

    # We have a fix at https://github.com/click-contrib/sphinx-click/pull/27
    # that we require.
    sphinx_click = (
        'sphinx_click',
        'git+https://github.com/adamtheturtle/sphinx-click',
        'fix-envvar-duplicates',
    )

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

    package_names = set()
    for requirement in [launch, test_utils, sphinx_click]:
        package_name, uri, reference = requirement
        package_names.add(package_name)

        subprocess.check_call(
            [
                'pip',
                'install',
                '--no-dependencies',
                '--target',
                str(target_directory),
                uri + '@' + reference,
            ],
        )

    # Ideally we would not use a protected function, however, this trade-off
    # has been considered - we want to use the vendored ``dcos_test_utils``
    # from the vendored ``dcos_launch``.
    vendorize._rewrite_imports(  # pylint: disable=protected-access
        target_directory=target_directory,
        top_level_names=list(package_names),
    )


if __name__ == '__main__':
    main()

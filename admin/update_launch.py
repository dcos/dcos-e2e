'''
Try to get the following to work:

python -c 'import dcos_e2e._vendor.dcos_launch'
'''

import vendorize
import os
import subprocess
from pathlib import Path


def test_main():
    # package_path = 'src/dcos_e2e/_vendor/dcos_launch'
    # top_level_names = ['dcos_test_utils']
    # vendorize._rewrite_imports_in_package(package_path, top_level_names, depth=1)
    #
    launch_url = 'git+https://github.com/dcos/dcos-launch@fad6d70caf282f7260d2d7af88f044ccfd64f8c7'
    test_utils_url = 'git+https://github.com/dcos/dcos-test-utils@a4cd8815fde6624a645c83eef85abde88b73a38f'
    target_directory = 'src/dcos_e2e/_vendor'
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)

    init_file = Path(target_directory) / '__init__.py'
    init_file.touch()

    for requirement in [launch_url, test_utils_url]:
        subprocess.check_call(
            ['pip', 'install', '--no-dependencies', '--target', target_directory, requirement])

    top_level_names = ['dcos_launch', 'dcos_test_utils']
    vendorize._rewrite_imports(target_directory, top_level_names)

    # module_path = 'src/dcos_e2e/_vendor/dcos_launch/util.py'
    # top_level_names = ['dcos_test_utils']
    # vendorize._rewrite_imports_in_module(module_path, top_level_names, depth=1)

#
#
# if __name__ == '__main__':
#     main()

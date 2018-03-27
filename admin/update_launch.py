"""
Try to get the following to work:

python -c 'import dcos_e2e._vendor.dcos_launch'
"""

import vendorize


def main():
    package_path = 'src/dcos_e2e/_vendor/dcos_launch'
    top_level_names = ['dcos_test_utils']
    vendorize._rewrite_imports_in_package(package_path, top_level_names, depth=1)
    #
    # module_path = 'src/dcos_e2e/_vendor/dcos_launch/util.py'
    # top_level_names = ['dcos_test_utils']
    # vendorize._rewrite_imports_in_module(module_path, top_level_names, depth=1)



if __name__ == '__main__':
    main()

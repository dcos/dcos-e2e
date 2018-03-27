"""
Try to get the following to work:

python -c 'import dcos_e2e._vendor.dcos_launch'
"""

import vendorize


def main():
    package_path = 'src/dcos_e2e/_vendor/dcos_launch'
    top_level_names = ['dcos_test_utils']
    # import pdb; pdb.set_trace()
    # top_level = vendorize._read_top_level_names(target_directory)
    # top_level_names = ['dcos_launch', 'dcos_test_utils']
    import pdb; pdb.set_trace()
    vendorize._rewrite_imports_in_package(package_path, top_level_names, depth=1)
    # vendorize.vendorize_requirement(
    # )
    # target_directory = 1
    # top_level_names = 1
    # vendorize._rewrite_imports(
    #     target_directory=target_directory,
    #     top_level_names=top_level_names,
    # )
    # pass



if __name__ == '__main__':
    main()

import vendorize


def main():
    target_directory = 'src/dcos_e2e/_vendor/dcos_launch'
    top_level_names = ['dcos_test_utils']
    vendorize._rewrite_imports(target_directory, top_level_names)
    # top_level = vendorize._read_top_level_names(target_directory)
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

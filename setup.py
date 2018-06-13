"""
Setup script for DC/OS End to End tests.
"""

import versioneer
from setuptools import find_packages, setup

# Avoid dependency links because they are not supported by Read The Docs.
#
# Also, they require users to use ``--process-dependency-links``.
DEPENDENCY_LINKS = []

with open('requirements.txt') as requirements:
    INSTALL_REQUIRES = []
    # Keyring is not a direct dependency but without it some users get:
    #
    # Cannot load 'keyring' on your system (either not installed, or not
    # configured correctly): No module named 'keyring'
    INSTALL_REQUIRES.append('keyring')
    # Similarly, without the following, some users get:
    # The 'secretstorage' distribution was not found and is required by keyring
    INSTALL_REQUIRES.append('secretstorage')
    for line in requirements.readlines():
        if line.startswith('#'):
            continue
        if line.startswith('--find-links'):
            _, link = line.split('--find-links ')
            DEPENDENCY_LINKS.append(link)
        else:
            INSTALL_REQUIRES.append(line)

with open('dev-requirements.txt') as dev_requirements:
    DEV_REQUIRES = []
    for line in dev_requirements.readlines():
        if not line.startswith('#'):
            DEV_REQUIRES.append(line)

with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='DCOS E2E',
    version=versioneer.get_version(),  # type: ignore
    cmdclass=versioneer.get_cmdclass(),  # type: ignore
    author='Adam Dangoor',
    author_email='adangoor@mesosphere.com',
    description='Test helpers for testing DC/OS end to end.',
    long_description=LONG_DESCRIPTION,
    packages=find_packages(where='src'),
    zip_safe=False,
    package_dir={'': 'src'},
    install_requires=INSTALL_REQUIRES,
    include_package_data=True,
    license='Apache License 2.0',
    keywords='dcos mesos docker',
    url='https://github.com/dcos/dcos-e2e',
    extras_require={
        'dev': DEV_REQUIRES,
    },
    classifiers=[
        'Operating System :: POSIX',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: Apache License 2.0',
    ],
    # Avoid dependency links because they are not supported by Read The Docs.
    #
    # Also, they require users to use ``--process-dependency-links``.
    dependency_links=DEPENDENCY_LINKS,
    entry_points="""
        [console_scripts]
        dcos-docker=cli:dcos_docker
    """,
)

"""
Setup script for DC/OS End to End tests.
"""

from setuptools import find_packages, setup

VERSION = '2017.11.29.0'

DEPENDENCY_LINKS = []

with open('requirements.txt') as requirements:
    INSTALL_REQUIRES = []
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

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='DCOS E2E',
    version=VERSION,
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
    url='https://github.com/mesosphere/dcos-e2e',
    extras_require={
        'dev': DEV_REQUIRES,
    },
    classifiers=[
        'Operating System :: POSIX',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: Apache License 2.0',
    ],
    dependency_links=DEPENDENCY_LINKS,
)

"""Setup script for DC/OS End to End tests."""

from setuptools import find_packages, setup

DEPENDENCY_LINKS = []
VERSION = '2017.06.15.0'

with open("requirements.txt") as requirements:
    INSTALL_REQUIRES = []
    for line in requirements.readlines():
        if line.startswith('#'):
            continue
        if line.startswith('--find-links '):
            _, link = line.split('--find-links ')
            DEPENDENCY_LINKS.append(link)
        else:
            INSTALL_REQUIRES.append(line)

with open("dev-requirements.txt") as dev_requirements:
    DEV_REQUIRES = []
    for line in dev_requirements.readlines():
        if line.startswith('#'):
            continue
        if line.startswith('--find-links '):
            _, link = line.split('--find-links ')
            DEPENDENCY_LINKS.append(link)
        else:
            DEV_REQUIRES.append(line)

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="DC/OS E2E",
    version=VERSION,
    author="Adam Dangoor",
    author_email='adangoor@mesosphere.com',
    description="Test helpers for testing DC/OS end to end.",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(where='src'),
    zip_safe=False,
    package_dir={'': 'src'},
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": DEV_REQUIRES,
    },
    classifiers=[
        'Operating System :: POSIX',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3.5',
    ],
    dependency_links=DEPENDENCY_LINKS,
)

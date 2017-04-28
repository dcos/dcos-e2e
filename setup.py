"""Setup script for DC/OS End to End tests."""

from setuptools import find_packages, setup

with open("requirements.txt") as requirements:
    install_requires = requirements.readlines()

with open("dev-requirements.txt") as dev_requirements:
    dev_requires = dev_requirements.readlines()

with open('README.md') as f:
    long_description = f.read()

setup(
    name="DC/OS E2E",
    version="0.1",
    author="Adam Dangoor",
    author_email='adangoor@mesosphere.com',
    description="Test helpers for testing DC/OS end to end.",
    long_description=long_description,
    packages=find_packages(where='src'),
    zip_safe=False,
    package_dir={'': 'src'},
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
    },
    classifiers=[
        'Operating System :: POSIX',
        'Environment :: Web Environment',
        'Programming Language :: Python :: 3.5',
    ],
)

"""Setup script for DC/OS End to End tests."""

from setuptools import find_packages, setup

dependency_links = []

with open("requirements.txt") as requirements:
    install_requires_lines = requirements.readlines()
    install_requires = []
    for line in install_requires_lines:
        if line.startswith('#'):
            continue
        if line.startswith('--find-links '):
            _, link = line.split('--find-links ')
            dependency_links.append(link)
        else:
            install_requires.append(line)

with open("dev-requirements.txt") as dev_requirements:
    dev_requires_lines = dev_requirements.readlines()
    dev_requires = []
    for line in dev_requires_lines:
        if line.startswith('#'):
            continue
        if line.startswith('--find-links '):
            _, link = line.split('--find-links ')
            dependency_links.append(link)
        else:
            dev_requires.append(line)

with open('README.md') as f:
    long_description = f.read()

test_utils_sha = '97131812adb6f2bfe33ba89c71eae6a868e1f6de'

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
    dependency_links=dependency_links,
)

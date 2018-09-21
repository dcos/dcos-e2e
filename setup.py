"""
Setup script for DC/OS End to End tests.
"""

from pathlib import Path
import versioneer
from setuptools import find_packages, setup

# Avoid dependency links because they are not supported by Read The Docs.
#
# Also, they require users to use ``--process-dependency-links``.
DEPENDENCY_LINKS = []


def _dependencies_from_requirements_file(requirements_file: Path):
    """
    Return requirements from a requirements file.

    This expects a requirements file with no ``--find-links`` lines.
    """
    lines = requirements_file.read_text().split('\n')
    return [line for line in lines if not line.startswith('#')]


INSTALL_REQUIRES = _dependencies_from_requirements_file(
    requirements_file=Path('requirements.txt'),
)
DEV_REQUIRES = _dependencies_from_requirements_file(
    requirements_file=Path('dev-requirements.txt'),
)
PACKAGING_REQUIRES = _dependencies_from_requirements_file(
    requirements_file=Path('packaging-requirements.txt'),
)

LONG_DESCRIPTION = Path('README.rst').read_text()

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
        'packaging': PACKAGING_REQUIRES,
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
        dcos-docker=cli.dcos_docker:dcos_docker
        dcos-vagrant=cli.dcos_vagrant:dcos_vagrant
        dcos-aws=cli.dcos_aws:dcos_aws
    """,
)

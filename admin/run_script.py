"""
Run tests and linters on Travis CI.
"""

import os
import subprocess
import sys

import pytest

from .travis_download_requirements import download_artifacts


def run_test(test_pattern: str) -> None:
    """
    Run pytest with a given test pattern.
    """
    result = pytest.main(
        [
            '-vvv',
            '--exitfirst',
            '--capture',
            'no',
            test_pattern,
            '--cov',
            'src/dcos_e2e',
            '--cov',
            'tests',
        ],
    )
    sys.exit(result)


if __name__ == '__main__':
    CI_PATTERN = os.environ.get('CI_PATTERN')
    if CI_PATTERN:
        download_artifacts(test_pattern=CI_PATTERN)
        run_test(test_pattern=CI_PATTERN)
    else:
        subprocess.check_call(['make', 'lint'])
        subprocess.check_call(['dcos-docker', 'doctor'])
        subprocess.check_call(['make', 'docs'])

"""
Run tests and linters on CI.
"""

import os
import sys
from typing import Dict  # noqa: F401

import pytest


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
            '--cov=src/dcos_e2e',
            '--cov=tests',
        ],
    )
    sys.exit(result)


if __name__ == '__main__':
    CI_PATTERN = os.environ['CI_PATTERN']
    run_test(test_pattern=CI_PATTERN)

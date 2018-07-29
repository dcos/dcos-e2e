"""
Custom lint tests for DC/OS E2E.
"""

import subprocess
from pathlib import Path
from typing import Dict  # noqa: F401
from typing import Set

import pytest
import yaml

from run_script import PATTERNS


def _travis_ci_patterns() -> Set[str]:
    """
    Return the CI patterns given in the ``.travis.yml`` file.
    """
    travis_file = Path(__file__).parent.parent / '.travis.yml'
    travis_contents = travis_file.read_text()
    travis_dict = yaml.load(travis_contents)
    travis_matrix = travis_dict['env']['matrix']

    ci_patterns = set()  # type: Set[str]
    for matrix_item in travis_matrix:
        key, value = matrix_item.split('=')
        assert key == 'CI_PATTERN'
        assert value not in ci_patterns
        # Special case for running no tests.
        if value != "''":
            ci_patterns.add(value)

    return ci_patterns


def _tests_from_pattern(ci_pattern: str) -> Set[str]:
    """
    From a CI pattern, get all tests ``pytest`` would collect.
    """
    tests = set([])  # type: Set[str]
    args = ['pytest', '--collect-only', ci_pattern, '-q']
    result = subprocess.run(args=args, stdout=subprocess.PIPE)
    output = result.stdout
    for line in output.splitlines():
        if line and not line.startswith(b'no tests ran in'):
            tests.add(line.decode())

    return tests


def test_ci_patterns_match() -> None:
    """
    The patterns in ``.travis.yml`` must match the patterns in
    ``admin/run_script.py``.
    """
    ci_patterns = _travis_ci_patterns()
    assert ci_patterns - PATTERNS.keys() == set()
    assert PATTERNS.keys() - ci_patterns == set()


def test_ci_patterns_valid() -> None:
    """
    All of the CI patterns in ``.travis.yml`` match at least one test in the
    test suite.
    """
    ci_patterns = _travis_ci_patterns()

    for ci_pattern in ci_patterns:
        collect_only_result = pytest.main(['--collect-only', ci_pattern])

        message = '"{ci_pattern}" does not match any tests.'.format(
            ci_pattern=ci_pattern,
        )
        assert collect_only_result == 0, message


def test_tests_collected_once() -> None:
    """
    Each test in the test suite is collected exactly once.

    This does not necessarily mean that they are run - they may be skipped.
    """
    ci_patterns = _travis_ci_patterns()
    tests_to_patterns = {}  # type: Dict[str, Set[str]]
    for pattern in ci_patterns:
        tests = _tests_from_pattern(ci_pattern=pattern)
        for test in tests:
            if test in tests_to_patterns:
                tests_to_patterns[test].add(pattern)
            else:
                tests_to_patterns[test] = set([pattern])

    for test_name, patterns in tests_to_patterns.items():
        message = (
            'Test "{test_name}" will be run once for each pattern in '
            '{patterns}. '
            'Each test should be run only once.'
        ).format(
            test_name=test_name,
            patterns=patterns,
        )
        assert len(patterns) == 1, message

    all_tests = _tests_from_pattern(ci_pattern='tests/')
    assert tests_to_patterns.keys() - all_tests == set()
    assert all_tests - tests_to_patterns.keys() == set()


def test_init_files() -> None:
    """
    ``__init__`` files exist where they should do.

    If ``__init__`` files are missing, linters may not run on all files that
    they should run on.
    """
    directories = (Path('src'), Path('tests'))

    for directory in directories:
        files = directory.glob('**/*.py')
        for python_file in files:
            parent = python_file.parent
            expected_init = parent / '__init__.py'
            assert expected_init.exists()

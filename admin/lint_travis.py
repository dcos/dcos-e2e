"""
Every test pattern we run on CI must also be specified in
``admin/run_script.py``.

This allows us to download only the required DC/OS artifacts.
However, this is prone to error.

The tests here help show some errors early.
"""

import os
import sys
from pathlib import Path
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
        if value in ci_patterns:
            raise Exception(
                '"{pattern}" is duplicated in ".travis.yml".'.format(
                    pattern=value,
                ),
            )
        # Special case for running no tests.
        if value != "''":
            ci_patterns.add(value)

    return ci_patterns


def test_ci_patterns_match() -> None:
    """
    The patterns in ``.travis.yml`` must match the patterns in
    ``admin/run_script.py``.
    """
    ci_patterns = _travis_ci_patterns()
    assert ci_patterns - PATTERNS.keys() == {}
    assert PATTERNS.keys() - ci_patterns == {}


def test_ci_patterns_valid() -> None:
    ci_patterns = _travis_ci_patterns()

    for ci_pattern in ci_patterns:
        old_out = sys.stdout
        old_err = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        collect_only_result = pytest.main(['--collect-only', ci_pattern])
        sys.stdout = old_out
        sys.stderr = old_err

        assert collect_only_result > 0


# TODO are there tests duplicated across patterns
# TODO are there tests missing

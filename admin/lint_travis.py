"""
Every test pattern we run on CI must also be specified in
``admin/run_script.py``.

This allows us to download only the required DC/OS artifacts.
However, this is prone to error.

This script attempts to help with that by telling test authors if they have
missed adding an item to ``admin/run_script.py``.
"""

import os
import sys
from pathlib import Path
from typing import Set  # noqa: F401

import pytest
import yaml

from run_script import PATTERNS

def travis_ci_patterns() -> None:
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

if CI_PATTERNS != PATTERNS.keys():
    sys.stderr.write(
        'The test patterns in ``.travis.yml`` and ``admin/run_script.py`` '
        'differ:\n',
    )

    TRAVIS_ONLY = CI_PATTERNS - PATTERNS.keys()
    if TRAVIS_ONLY:
        for TRAVIS_ONLY_ITEM in TRAVIS_ONLY:
            sys.stderr.write(
                '    Only ``.travis.yml`` includes "{item}".\n'.format(
                    item=TRAVIS_ONLY_ITEM,
                ),
            )

    RUN_SCRIPT_ONLY = PATTERNS.keys() - CI_PATTERNS
    if RUN_SCRIPT_ONLY:
        for RUN_SCRIPT_ONLY_ITEM in RUN_SCRIPT_ONLY:
            sys.stderr.write(
                '    Only ``admin/run_script.py`` includes "{item}."\n'.format(
                    item=RUN_SCRIPT_ONLY_ITEM,
                ),
            )

COLLECT_ONLY_ERROR_RESULTS = set()
for CI_PATTERN in CI_PATTERNS:
    OLD_OUT = sys.stdout
    OLD_ERR = sys.stderr
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    COLLECT_ONLY_RESULT = pytest.main(['--collect-only', CI_PATTERN])
    sys.stdout = OLD_OUT
    sys.stderr = OLD_ERR

    if COLLECT_ONLY_RESULT != 0:
        COLLECT_ONLY_ERROR_RESULTS.add(CI_PATTERN)

for ERROR_PATTERN in COLLECT_ONLY_ERROR_RESULTS:
    sys.stderr.write(
        'Error finding tests with pattern "{pattern}".\n'.format(
            pattern=ERROR_PATTERN,
        ),
    )

if CI_PATTERNS != PATTERNS.keys() or COLLECT_ONLY_ERROR_RESULTS:
    sys.exit(1)

# TODO are there tests duplicated across patterns
# TODO are there tests missing

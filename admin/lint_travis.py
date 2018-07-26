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

TRAVIS_FILE = Path(__file__).parent.parent / '.travis.yml'
TRAVIS_CONTENTS = TRAVIS_FILE.read_text()
TRAVIS_DICT = yaml.load(TRAVIS_CONTENTS)
TRAVIS_MATRIX = TRAVIS_DICT['env']['matrix']

CI_PATTERNS = set()  # type: Set[str]
for MATRIX_ITEM in TRAVIS_MATRIX:
    KEY, VALUE = MATRIX_ITEM.split('=')
    assert KEY == 'CI_PATTERN'
    if VALUE in CI_PATTERNS:
        raise Exception(
            '"{pattern}" is duplicated in ".travis.yml".'.format(
                pattern=VALUE,
            ),
        )
    # Special case for running no tests.
    if VALUE != "''":
        CI_PATTERNS.add(VALUE)

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

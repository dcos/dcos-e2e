"""
Every test pattern we run on CI must also be specified in
``admin/run_script.py``.

This allows us to download only the required DC/OS artifacts.
However, this is prone to error.

This script attempts to help with that by telling test authors if they have
missed adding an item to ``admin/run_script.py``.
"""

import sys
from pathlib import Path

import yaml

from run_script import PATTERNS

TRAVIS_FILE = Path(__file__).parent.parent / '.travis.yml'
TRAVIS_CONTENTS = TRAVIS_FILE.read_text()
TRAVIS_DICT = yaml.load(TRAVIS_CONTENTS)
TRAVIS_MATRIX = TRAVIS_DICT['env']['matrix']

CI_PATTERNS = set()
for MATRIX_ITEM in TRAVIS_MATRIX:
    KEY, VALUE = MATRIX_ITEM.split('=')
    assert KEY == 'CI_PATTERN'
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
    sys.exit(1)

from pathlib import Path
from run_script import PATTERNS
import yaml

travis_file = Path(__file__).parent.parent / '.travis.yml'
travis_contents = travis_file.read_text()
travis_dict = yaml.load(travis_contents)
travis_matrix = travis_dict['env']['matrix']

ci_patterns = set()
for matrix_item in travis_matrix:
    key, value = matrix_item.split('=')
    assert key == 'CI_PATTERN'
    # Special case for running no tests.
    if value != "''":
        ci_patterns.add(value)

assert ci_patterns == PATTERNS.keys()

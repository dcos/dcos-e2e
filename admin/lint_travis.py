from pathlib import Path
travis_file = Path(__file__).parent.parent / '.travis.yml'
travis_contents = travis_file.read_text()
import yaml
travis_dict = yaml.load(travis_contents)

from run_script import PATTERNS



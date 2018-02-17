"""
Run `mypy`, ignoring relevant errors.
"""

import subprocess
import sys

def main() -> None:
    args = ['mypy', 'src/', 'tests/']
    ignore_paths = {
        'src/dcos_e2e/vendor',
    }
    result = subprocess.run(args=args, stdout=subprocess.PIPE)
    print(result.stdout.decode())
    if len(result.stdout):
        sys.exit(1)


if __name__ == '__main__':
    main()
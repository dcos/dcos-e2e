"""
Run `mypy`, ignoring relevant errors.
"""

import subprocess
import sys


def main() -> None:
    args = ['mypy', 'src/', 'tests/']
    ignore_paths = {
        'src/dcos_e2e/_vendor',
    }
    result = subprocess.run(args=args, stdout=subprocess.PIPE)
    result_lines = result.stdout.decode().strip().split('\n')
    error_lines = [
        line for line in result_lines
        if not any(line.startswith(path) for path in ignore_paths)
    ]
    print('\n'.join(error_lines))
    sys.exit(int(bool(error_lines)))


if __name__ == '__main__':
    main()

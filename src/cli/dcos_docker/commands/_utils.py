"""
Utilities for the CLI.
"""

import json
import subprocess
from pathlib import Path


def is_enterprise(build_artifact: Path, workspace_dir: Path) -> bool:
    """
    Return whether the build artifact is an Enterprise artifact.

    Raises:
        ValueError: A space is in the build artifact path.
    """
    if ' ' in str(build_artifact):
        raise ValueError('No spaces allowed in path to the build artifact.')

    result = subprocess.check_output(
        args=['bash', str(build_artifact), '--version'],
        cwd=str(workspace_dir),
        stderr=subprocess.PIPE,
    )

    result = result.decode()
    result = ' '.join(
        [
            line for line in result.splitlines()
            if not line.startswith('Extracting image')
            and not line.startswith('Loaded image') and '.tar' not in line
        ],
    )

    version_info = json.loads(result)
    variant = version_info['variant']
    return bool(variant == 'ee')

"""
Utilities for the CLI.
"""

import json
import subprocess
from pathlib import Path


def is_enterprise(build_artifact: Path, workspace_dir: Path) -> bool:
    """
    Return whether the build artifact is an Enterprise artifact.
    """
    get_version_args = [
        'bash',
        str(build_artifact),
        '--version',
    ]
    result = subprocess.check_output(
        args=get_version_args,
        cwd=str(workspace_dir),
        stderr=subprocess.PIPE,
    )

    # In some cases, the name of the generated file is included in the output.
    result = result.decode()
    if '.tar\n' in result:
        result = result.split('.tar\n')[1]
    version_info = json.loads(result)
    variant = version_info['variant']
    return bool(variant == 'ee')

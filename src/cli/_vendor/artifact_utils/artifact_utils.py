"""
Tools for getting details from DC/OS installer artifacts.
"""

import json
import shutil
import subprocess
import uuid
from enum import Enum
from pathlib import Path
from tempfile import gettempdir
from typing import Optional


class DCOSVariant(Enum):
    """
    Variants of DC/OS.
    """

    OSS = 1
    ENTERPRISE = 2


class _DCOSInstallerDetails:
    """
    Details of a DC/OS installer.

    Attributes:
        variant: The DC/OS variant which can be installed by a particular
            installer.
        version: The version of DC/OS which can be installed by a particular
            installer.
    """

    def __init__(self, variant: DCOSVariant, version: str) -> None:
        """
        Details of a DC/OS installer.

        Args:
            variant: The DC/OS variant which can be installed by a particular
                installer.
            version: The version of DC/OS which can be installed by a
                particular installer.
        """
        self.variant = variant
        self.version = version


def get_dcos_installer_details(
    installer: Path,
    workspace_dir: Optional[Path] = None,
    keep_extracted: bool = False,
) -> _DCOSInstallerDetails:
    """
    Get details from a DC/OS artifact.

    Args:
        installer: The path to a DC/OS installer. This cannot include a
            space.
        workspace_dir: The directory in which large temporary files will be
            created.
            This is equivalent to `dir` in :py:func:`tempfile.mkstemp`.
        keep_extracted: Whether to keep the extracted artifact.

    Raises:
        ValueError: A space is in the installer path.
        CalledProcessError: There was an error extracting the given installer.
    """
    if ' ' in str(installer):
        message = 'No spaces allowed in path to the installer.'
        raise ValueError(message)

    workspace_dir = workspace_dir or Path(gettempdir())
    if not keep_extracted:
        workspace_dir = Path(workspace_dir) / uuid.uuid4().hex

    workspace_dir.mkdir(exist_ok=True, parents=True)

    result = subprocess.check_output(
        args=['bash', str(installer), '--version'],
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

    version = version_info['version']
    variant = {
        'ee': DCOSVariant.ENTERPRISE,
        '': DCOSVariant.OSS,
    }[version_info['variant']]

    if not keep_extracted:
        shutil.rmtree(path=str(workspace_dir))

    return _DCOSInstallerDetails(version=version, variant=variant)

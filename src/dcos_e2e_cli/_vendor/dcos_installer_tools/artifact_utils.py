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

    # The installer interface is as follows:
    #
    # ```
    # $ bash dcos_generate_config.sh --version
    # Extracting image from this script and loading into docker daemon, this \
    # step can take a few minutes
    # x dcos-genconf.75af9b2571de95e074-c74aa914537fa9f81b.tar
    # Loaded image: mesosphere/dcos-genconf: \
    # 75af9b2571de95e074-c74aa914537fa9f81b
    # {
    #     "variant": "",
    #     "version": "1.12.0-rc3"
    # }
    # $ bash dcos_generate_config.sh --version
    # {
    #     "variant": "",
    #     "version": "1.12.0-rc3"
    # }
    # ```
    #
    # Therefore we use the installer twice to eliminate all non-JSON text.

    version_args = ['bash', str(installer), '--version']

    subprocess.check_output(
        args=version_args,
        cwd=str(workspace_dir),
        stderr=subprocess.PIPE,
    )

    result = subprocess.check_output(
        args=version_args,
        cwd=str(workspace_dir),
        stderr=subprocess.PIPE,
    )

    version_info = json.loads(result.decode())

    version = version_info['version']
    variant = {
        'ee': DCOSVariant.ENTERPRISE,
        '': DCOSVariant.OSS,
    }[version_info['variant']]

    if not keep_extracted:
        shutil.rmtree(path=str(workspace_dir))

    return _DCOSInstallerDetails(version=version, variant=variant)

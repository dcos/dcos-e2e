"""
Tools for managing a cluster given a ``ClusterManager``.
"""

from functools import singledispatch
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple, Union

from .base_classes import ClusterManager
from .node import Output


@singledispatch
def cluster_manager_install_dcos(
    cluster_manager: ClusterManager,
    dcos_installer: Union[str, Path],
    dcos_config: Dict[str, Any],
    ip_detect_path: Path,
    output: Output,
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
) -> None:
    """
    Installs DC/OS using the DC/OS advanced installation method.

    Args:
        dcos_installer: The ``Path`` to a local installer or a ``str`` to
            which is a URL pointing to an installer to install DC/OS from.
        dcos_config: The contents of the DC/OS ``config.yaml``.
        cluster_manager: The cluster manager to install DC/OS with.
        ip_detect_path: The path to a ``ip-detect`` script that will be
            used when installing DC/OS.
        files_to_copy_to_genconf_dir: Pairs of host paths to paths on
            the installer node. These are files to copy from the host to
            the installer node before installing DC/OS.
        output: What happens with stdout and stderr.
    """
    assert isinstance(dcos_installer, Path)
    cluster_manager.install_dcos_from_path(
        dcos_installer=dcos_installer,
        dcos_config=dcos_config,
        ip_detect_path=ip_detect_path,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        output=output,
    )


@cluster_manager_install_dcos.register
def _install_dcos_from_url(
    cluster_manager: ClusterManager,
    dcos_installer: str,
    dcos_config: Dict[str, Any],
    ip_detect_path: Path,
    output: Output,
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
) -> None:
    """
    Installs DC/OS using the DC/OS advanced installation method.

    Args:
        dcos_installer: The URL string to an installer to install DC/OS
            from.
        cluster_manager: The cluster manager to install DC/OS with.
        dcos_config: The contents of the DC/OS ``config.yaml``.
        ip_detect_path: The path to a ``ip-detect`` script that will be
            used when installing DC/OS.
        files_to_copy_to_genconf_dir: Pairs of host paths to paths on
            the installer node. These are files to copy from the host to
            the installer node before installing DC/OS.
        output: What happens with stdout and stderr.
    """
    cluster_manager.install_dcos_from_url(
        dcos_installer=dcos_installer,
        dcos_config=dcos_config,
        ip_detect_path=ip_detect_path,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        output=output,
    )

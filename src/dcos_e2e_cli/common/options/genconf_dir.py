"""
Options for working with a ``genconf`` directory.
"""

from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

import click
import click_pathlib


def get_files_to_copy_to_genconf_dir(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Path],
) -> List[Tuple[Path, Path]]:
    """
    Get a list of pairs of paths and where to put them on a node.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    local_genconf_dir = value
    files_to_copy_to_genconf_dir = []
    if local_genconf_dir is not None:
        node_genconf_path = Path('/genconf')
        for genconf_file in local_genconf_dir.glob('*'):
            genconf_relative = genconf_file.relative_to(local_genconf_dir)
            relative_path = node_genconf_path / genconf_relative
            files_to_copy_to_genconf_dir.append((genconf_file, relative_path))
    return files_to_copy_to_genconf_dir


def genconf_dir_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for a custom "genconf" directory.
    """
    click_option_function = click.option(
        '--genconf-dir',
        'files_to_copy_to_genconf_dir',
        type=click_pathlib.Path(
            exists=True,
            dir_okay=True,
            file_okay=False,
            resolve_path=True,
        ),
        callback=get_files_to_copy_to_genconf_dir,
        help=(
            'Path to a directory that contains additional files for the DC/OS '
            'installer. '
            'All files from this directory will be copied to the "genconf" '
            'directory before running the DC/OS installer.'
        ),
    )  # type: Callable[[Callable[..., None]], Callable[..., None]]
    function = click_option_function(command)  # type: Callable[..., None]
    return function

"""
Tools for managing workspaces.
"""

import tempfile
import uuid
from pathlib import Path
from typing import Callable, Optional, Union

import click

from .validators import validate_path_is_directory


def get_workspace_dir(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> Optional[Path]:
    """
    Validate that a path is a directory.
    """
    optional_base_path = validate_path_is_directory(
        ctx=ctx,
        param=param,
        value=value,
    )
    base_workspace_dir = optional_base_path or Path(tempfile.gettempdir())
    workspace_dir = base_workspace_dir / uuid.uuid4().hex
    workspace_dir.mkdir(parents=True)
    return workspace_dir


def workspace_dir_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the workspace directory.
    """
    help_text = (
        'Creating a cluster can use approximately 2 GB of temporary storage. '
        'Set this option to use a custom "workspace" for this temporary '
        'storage. '
        'See '
        'https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir '
        'for details on the temporary directory location if this option is '
        'not set.'
    )
    function = click.option(
        '--workspace-dir',
        type=click.Path(exists=True),
        callback=get_workspace_dir,
        help=help_text,
    )(command)  # type: Callable[..., None]
    return function

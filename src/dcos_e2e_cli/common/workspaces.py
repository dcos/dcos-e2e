"""
Tools for managing workspaces.
"""

import tempfile
import uuid
from pathlib import Path
from typing import Callable, Optional, Union

import click
import click_pathlib


def get_workspace_dir(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Path],
) -> Path:
    """
    Get a new workspace directory, within the given directory if one is given.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    base_workspace_dir = value or Path(tempfile.gettempdir())
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
        type=click_pathlib.Path(
            exists=True,
            dir_okay=True,
            file_okay=False,
            resolve_path=True,
        ),
        callback=get_workspace_dir,
        help=help_text,
    )(command)  # type: Callable[..., None]
    return function

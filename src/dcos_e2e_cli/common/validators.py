"""
Validators for CLI options.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union

import click


def validate_path_pair(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Tuple[str]],
) -> List[Tuple[Path, Path]]:
    """
    Validate a pair of paths expected to be in the format:
    /absolute/local/path:/remote/path.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    result = []  # type: List[Tuple[Path, Path]]

    if value is None:
        return result

    for path_pair in value:
        try:
            [local_path, remote_path] = list(map(Path, path_pair.split(':')))
        except ValueError:
            message = (
                '"{path_pair}" is not in the format '
                '/absolute/local/path:/remote/path.'
            ).format(path_pair=path_pair)
            raise click.BadParameter(message=message)

        if not local_path.exists():
            message = '"{local_path}" does not exist.'.format(
                local_path=local_path,
            )
            raise click.BadParameter(message=message)

        if not remote_path.is_absolute():
            message = '"{remote_path} is not an absolute path.'.format(
                remote_path=remote_path,
            )
            raise click.BadParameter(message=message)

        result.append((local_path, remote_path))

    return result

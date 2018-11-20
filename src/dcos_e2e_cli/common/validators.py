"""
Validators for CLI options.
"""

from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import click


def validate_path_is_directory(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> Optional[Path]:
    """
    Validate that a path is a directory.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value is None:
        return None

    path = Path(str(value))
    if not path.is_dir():
        message = '"{path}" is not a directory.'.format(path=str(path))
        raise click.BadParameter(message=message)

    return path


def validate_paths_are_directories(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    # ``value`` is set to "Any" as the typeshed stub is wrong:
    # https://github.com/python/typeshed/issues/2615.
    value: Any,
) -> Tuple[Path, ...]:
    """
    Validate that all paths are directories.
    """
    paths = []
    for item in value:
        validate_path_is_directory(ctx=ctx, param=param, value=item)
        paths.append(Path(item))
    return_value = tuple(item for item in paths)
    return return_value


def validate_path_pair(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
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

"""
Validators for CLI options.
"""

import re
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Tuple, Union

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


def validate_path_pair(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
) -> List[Tuple[Path, Path]]:
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


def make_validate_cluster_id(
    existing_cluster_ids_func: Callable[[], Set[str]],
) -> Callable[[
    click.core.Context,
    Union[click.core.Option, click.core.Parameter],
    Optional[Union[int, bool, str]],
], str]:
    """
    Return a Click validator for a new cluster ID.

    Args:
        existing_cluster_ids_func: A function which returns existing cluster
            IDs.
    """

    def _validate_cluster_id(
        ctx: click.core.Context,
        param: Union[click.core.Option, click.core.Parameter],
        value: Optional[Union[int, bool, str]],
    ) -> str:
        """
        Validate that a value is a valid cluster ID.
        """
        # We "use" variables to satisfy linting tools.
        for _ in (ctx, param):
            pass

        if value in existing_cluster_ids_func():
            message = 'A cluster with the id "{value}" already exists.'.format(
                value=value,
            )
            raise click.BadParameter(message=message)

        # This matches the Docker ID regular expression.
        # This regular expression can be seen by running:
        # > docker run -it --rm --id=' WHAT ? I DUNNO ! ' alpine
        if not re.fullmatch('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', str(value)):
            message = (
                'Invalid cluster id "{value}", only [a-zA-Z0-9][a-zA-Z0-9_.-] '
                'are allowed and the cluster ID cannot be empty.'
            ).format(value=value)
            raise click.BadParameter(message)

        return str(value)

    return _validate_cluster_id

"""
Validators for CLI options.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import click
import yaml

from ._common import existing_cluster_ids


def validate_dcos_configuration(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Union[int, bool, str],
) -> Dict[str, Any]:
    """
    Validate that a given value is a file containing a YAML map.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value is None:
        return {}

    content = Path(str(value)).read_text()

    try:
        return dict(yaml.load(content) or {})
    except ValueError:
        message = '"{content}" is not a valid DC/OS configuration'.format(
            content=content,
        )
    except yaml.YAMLError:
        message = '"{content}" is not valid YAML'.format(content=content)

    raise click.BadParameter(message=message)


def validate_cluster_id(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> str:
    """
    Validate that a given value is a YAML map.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value in existing_cluster_ids():
        message = 'A cluster with the id "{value}" already exists'.format(
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


def validate_cluster_exists(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> str:
    """
    Validate that a cluster exists with the given name.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value is None:
        if 'default' in existing_cluster_ids():
            return 'default'
        message = '--cluster-id was not given and no cluster "default" exists'
        raise click.BadParameter(message)

    cluster_id = str(value)
    if cluster_id not in existing_cluster_ids():
        message = 'Cluster "{value}" does not exist'.format(value=value)
        raise click.BadParameter(message)

    return cluster_id


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


def validate_volumes(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
) -> Dict[str, Dict[str, str]]:
    for _ in (ctx, param, value):
        pass
    return {}

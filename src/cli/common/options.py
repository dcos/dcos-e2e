"""
Click options which are common across CLI tools.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Union

import click
import yaml


def _validate_dcos_configuration(
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


def masters_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of masters.
    """
    function = click.option(
        '--masters',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of master nodes.',
    )(command)  # type: Callable[..., None]
    return function


def agents_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of agents.
    """
    function = click.option(
        '--agents',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of agent nodes.',
    )(command)  # type: Callable[..., None]
    return function


def public_agents_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of agents.
    """
    function = click.option(
        '--public-agents',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of public agent nodes.',
    )(command)  # type: Callable[..., None]
    return function


def extra_config_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for supplying extra DC/OS configuration options.
    """
    function = click.option(
        '--extra-config',
        type=click.Path(exists=True),
        callback=_validate_dcos_configuration,
        help=(
            'The path to a file including DC/OS configuration YAML. '
            'The contents of this file will be added to add to a default '
            'configuration.'
        ),
    )(command)  # type: Callable[..., None]
    return function

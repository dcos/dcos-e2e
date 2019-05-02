"""
Options for passing environment variables.
"""

from typing import Callable, Dict, Tuple, Union

import click


def _validate_environment_variable(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Tuple[str],
) -> Dict[str, str]:
    """
    Validate that environment variables are set as expected.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (param, ctx):
        pass

    env = {}
    for definition in value:
        try:
            key, val = definition.split(sep='=', maxsplit=1)
        except ValueError:
            message = (
                '"{definition}" does not match the format "<KEY>=<VALUE>".'
            ).format(definition=definition)
            raise click.BadParameter(message=message)
        env[key] = val
    return env


def environment_variables_option(command: Callable[..., None],
                                 ) -> Callable[..., None]:
    """
    An option decorator for setting environment variables.
    """
    function = click.option(
        '--env',
        type=str,
        callback=_validate_environment_variable,
        multiple=True,
        help='Set environment variables in the format "<KEY>=<VALUE>"',
    )(command)  # type: Callable[..., None]
    return function

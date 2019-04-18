"""
AWS Custom Tag Option
"""

from typing import Callable, Dict, Tuple, Union

import click


def _validate_tags(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Tuple[str],
) -> Dict[str, str]:
    """
    Turn tag strings into a Dict.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    tags = {}  # type: Dict[str, str]
    for tag_definition in value:
        parts = tag_definition.split(':')

        if len(parts) != 2:
            message = (
                '"{tag_definition}" is not a valid tag. '
                'Please follow this syntax: <TAG_KEY>:<TAG_VALUE>.'
            ).format(tag_definition=tag_definition)
            raise click.BadParameter(message=message)

        tag_key, tag_value = parts
        if tag_key in tags:
            message = 'Tag key "{tag_key}" specified multiple times.'.format(
                tag_key=tag_key,
            )
            raise click.BadParameter(message=message)

        tags[tag_key] = tag_value
    return tags


def custom_tag_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    Option to choose the DC/OS variant for installation.
    """
    function = click.option(
        '--custom-tag',
        type=str,
        callback=_validate_tags,
        help=(
            'Add tags to EC2 instances in the format '
            '"<TAG_KEY>:<TAG_VALUE>".'
        ),
        multiple=True,
    )(command)  # type: Callable[..., None]
    return function

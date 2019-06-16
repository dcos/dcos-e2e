"""
Options for using Docker volumes.
"""

from typing import Callable, List, Union

import click
import docker


def _validate_volumes(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: str,
) -> List[docker.types.Mount]:
    """
    Turn volume definition strings into ``Mount``s that ``docker-py`` can use.
    """
    for _ in (ctx, param):
        pass
    mounts = []
    for volume_definition in value:
        parts = volume_definition.split(':')

        if len(parts) == 1:
            host_src = None
            [container_dst] = parts
            read_only = False
        elif len(parts) == 2:
            host_src, container_dst = parts
            read_only = False
        elif len(parts) == 3:
            host_src, container_dst, mode = parts
            if mode == 'ro':
                read_only = True
            elif mode == 'rw':
                read_only = False
            else:
                message = (
                    'Mode in "{volume_definition}" is "{mode}". '
                    'If given, the mode must be one of "ro", "rw".'
                ).format(
                    volume_definition=volume_definition,
                    mode=mode,
                )
                raise click.BadParameter(message=message)
        else:
            message = (
                '"{volume_definition}" is not a valid volume definition. '
                'See '
                'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
                'for the syntax to use.'
            ).format(volume_definition=volume_definition)
            raise click.BadParameter(message=message)

        mount = docker.types.Mount(
            source=host_src,
            target=container_dst,
            type='bind',
            read_only=read_only,
        )
        mounts.append(mount)
    return mounts


def _volume_option_factory(
    name: str,
    container_type: str,
) -> Callable[[Callable[..., None]], Callable[..., None]]:
    """
    An option decorator for setting Docker bind mounts.
    """

    def new_volume_option(command: Callable[..., None]) -> Callable[..., None]:
        function = click.option(
            name,
            type=str,
            callback=_validate_volumes,
            help=(
                'Bind mount a volume on all {container_type} node containers. '
                'See '
                'https://docs.docker.com/engine/reference/run/#volume-shared-filesystems '  # noqa: E501
                'for the syntax to use.'
            ).format(container_type=container_type),
            multiple=True,
        )(command)  # type: Callable[..., None]
        return function

    return new_volume_option


VOLUME_OPTION = _volume_option_factory(
    name='--custom-volume',
    container_type='cluster',
)

MASTER_VOLUME_OPTION = _volume_option_factory(
    name='--custom-master-volume',
    container_type='cluster master',
)

AGENT_VOLUME_OPTION = _volume_option_factory(
    name='--custom-agent-volume',
    container_type='cluster agent',
)

PUBLIC_AGENT_VOLUME_OPTION = _volume_option_factory(
    name='--custom-public-agent-volume',
    container_type='cluster public agent',
)

from typing import Callable, Optional, Union

import click


def _validate_cluster_exists(
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

    cluster_id = str(value)
    if cluster_id not in existing_cluster_ids():
        message = 'Cluster "{value}" does not exist'.format(value=value)
        raise click.BadParameter(message)

    return cluster_id


def existing_cluster_id_option(command: Callable[..., None],
                               ) -> Callable[..., None]:
    """
    An option decorator for one Cluster ID.
    """
    function = click.option(
        '-c',
        '--cluster-id',
        type=str,
        callback=_validate_cluster_exists,
        default='default',
        show_default=True,
        help='The ID of the cluster to use.',
    )(command)  # type: Callable[..., None]
    return function

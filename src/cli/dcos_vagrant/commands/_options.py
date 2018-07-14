"""
Common options for ``dcos-vagrant`` commands.
"""

from typing import Callable

from cli.common.options import make_existing_cluster_id_option

from ._common import existing_cluster_ids


def existing_cluster_id_option(command: Callable[..., None],
                               ) -> Callable[..., None]:
    """
    An option decorator for one Cluster ID.
    """
    existing_id_option = make_existing_cluster_id_option(
        existing_cluster_ids_func=existing_cluster_ids,
    )

    return existing_id_option(command)

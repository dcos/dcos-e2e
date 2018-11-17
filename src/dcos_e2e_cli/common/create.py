"""
Tools for creating DC/OS clusters.
"""

import sys
import click

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster

from .utils import get_doctor_message


def create_cluster(
    cluster_backend: ClusterBackend,
    masters: int,
    agents: int,
    public_agents: int,
    sibling_ctx: click.core.Context,
    doctor_command: click.core.Command,
) -> Cluster:
    """
    XXX
    """
    doctor_message = get_doctor_message(
        sibling_ctx=sibling_ctx,
        doctor_command=doctor_command,
    )
    try:
        return Cluster(
            cluster_backend=cluster_backend,
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        )
    except CalledProcessError as exc:
        click.echo('Error creating cluster.', err=True)
        click.echo(doctor_message)
        sys.exit(exc.returncode)

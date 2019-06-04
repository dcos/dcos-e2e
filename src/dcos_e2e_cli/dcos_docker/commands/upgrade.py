from pathlib import Path

import click

from dcos_e2e.backends import Docker
from dcos_e2e.node import Output, Role, Transport
from dcos_e2e_cli.common.arguments import installer_argument
from dcos_e2e_cli.common.options import (
    existing_cluster_id_option,
    verbosity_option,
)
from dcos_e2e_cli.common.utils import check_cluster_id_exists

from ._common import ClusterContainers, existing_cluster_ids
from ._options import node_transport_option


@click.command('upgrade')
@existing_cluster_id_option
@verbosity_option
@node_transport_option
@installer_argument
def upgrade(cluster_id: str, transport: Transport, installer: Path) -> None:
    """
    XXX
    """
    check_cluster_id_exists(
        new_cluster_id=cluster_id,
        existing_cluster_ids=existing_cluster_ids(),
    )
    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster_backend = Docker()
    cluster = cluster_containers.cluster
    for nodes, role in (
        (cluster.masters, Role.MASTER),
        (cluster.agents, Role.AGENT),
        (cluster.public_agents, Role.PUBLIC_AGENT),
    ):
        for node in nodes:
            node.upgrade_dcos_from_path(
                dcos_installer=installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                role=role,
                output=Output.LOG_AND_CAPTURE,
            )

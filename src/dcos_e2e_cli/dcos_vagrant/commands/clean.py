"""
Clean all Docker containers, volumes etc. from using the Docker backend.
"""

import click

from dcos_e2e_cli._vendor import vertigo_py
from dcos_e2e_cli.common.options import enable_spinner_option, verbosity_option
from dcos_e2e_cli.dcos_vagrant.commands.destroy import destroy_cluster

from ._common import vm_names_by_cluster


@click.command('clean')
@click.option(
    '--destroy-running-clusters',
    is_flag=True,
    default=False,
    show_default=True,
    help='Destroy running clusters.',
)
@enable_spinner_option
@verbosity_option
def clean(destroy_running_clusters: bool, enable_spinner: bool) -> None:
    """
    Remove VMs created by this tool.

    This is useful in removing paused and aborted VMs.
    VMs are aborted when the host is shut down.
    """
    running_clusters = vm_names_by_cluster(running_only=True)
    all_clusters = vm_names_by_cluster(running_only=False)
    not_running_cluster_names = set(
        all_clusters.keys() - running_clusters.keys(),
    )

    if destroy_running_clusters:
        for cluster_id in running_clusters.keys():
            destroy_cluster(
                cluster_id=cluster_id,
                enable_spinner=enable_spinner,
            )

    for cluster_id in not_running_cluster_names:
        for vm_name in all_clusters[cluster_id]:
            virtualbox_vm = vertigo_py.VM(name=vm_name)  # type: ignore
            virtualbox_vm.unregistervm(delete=True)
            print('not running ', vm_name)

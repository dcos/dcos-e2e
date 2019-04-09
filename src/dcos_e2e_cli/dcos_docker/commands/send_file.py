
@click.command('destroy')
@existing_cluster_id_option
def destroy(cluster_id: str) -> None:
    """
    Destroy a cluster.
    """
    _destroy_cluster(cluster_id=cluster_id)
    click.echo(cluster_id)

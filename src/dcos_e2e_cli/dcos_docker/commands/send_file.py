
@click.command('destroy')
@existing_cluster_id_option
@node_transport_option
@verbosity_option
def send_file(cluster_id: str, node: Tuple[str], transport: Transport, verbose: int) -> None:
    """
    Send a file to a node.
    """
    _destroy_cluster(cluster_id=cluster_id)
    click.echo(cluster_id)

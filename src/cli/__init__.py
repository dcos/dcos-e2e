import click


@click.group()
def dcos_docker():
    """
    Manage DC/OS clusters on Docker.
    """


@dcos_docker.command('create')
@click.argument('artifact', type=click.Path(exists=True))
def create(artifact):
    """
    Create a DC/OS cluster.
    """


if __name__ == '__main__':
    dcos_docker()

import click


@click.group()
def dcos_docker():
    """
    Manage DC/OS clusters on Docker.
    """
    pass

@dcos_docker.command('create')
def create():
    """
    Create a DC/OS cluster.
    """
    pass

if __name__ == '__main__':
    dcos_docker()

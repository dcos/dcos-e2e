import click


@click.group()
def dcos_docker():
    """
    Manage DC/OS clusters on Docker.
    """

@click.command()
def create():
    """
    Create a DC/OS cluster.
    """

if __name__ == '__main__':
    dcos_docker()

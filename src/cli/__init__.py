import click


@click.group()
def dcos_docker():
    """
    Manage DC/OS clusters on Docker.
    """

"""
A CLI for controlling DC/OS clusters on Docker.
"""

import click

import dcos_e2e

from ..dcos_aws import dcos_aws
from ..dcos_docker import dcos_docker
from ..dcos_vagrant import dcos_vagrant

_CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(name='minidcos', context_settings=_CONTEXT_SETTINGS)
# We set the ``version`` parameter because in PyInstaller binaries,
# ``pkg_resources`` is not available.
#
# Click uses ``pkg_resources`` to determine the version if it is not given.
@click.version_option(version=dcos_e2e.__version__)
def minidcos() -> None:
    """
    Manage DC/OS clusters.
    """


minidcos.add_command(dcos_docker)
minidcos.add_command(dcos_vagrant)
minidcos.add_command(dcos_aws)

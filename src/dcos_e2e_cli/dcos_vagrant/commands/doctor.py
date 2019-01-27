"""
Checks for showing up common sources of errors with the Vagrant backend.
"""

import shutil

import click
import docker

from dcos_e2e_cli.common.doctor import (
    CheckLevels,
    check_1_9_sed,
    check_ssh,
    error,
    run_doctor_commands,
    warn,
)
from dcos_e2e_cli.common.options import verbosity_option
from dcos_e2e_cli.common.utils import set_logging


def check_docker() -> CheckLevels:
    """
    Error if Docker is not running.
    """
    try:
        docker.from_env(version='auto')
    except docker.errors.DockerException:
        message = (
            'Docker is not running. '
            'Docker is required for the "create" command to determine the '
            'DC/OS variant of the given DC/OS installer. '
            'Use the "--variant" option when using the "create" command or '
            'install and run Docker.'
        )
        warn(message=message)
        return CheckLevels.WARNING
    return CheckLevels.NONE


def check_vagrant() -> CheckLevels:
    """
    Error if `vagrant` is not available on the path.
    """
    if shutil.which('vagrant') is None:
        error(message='`vagrant` must be available on the PATH.')
        return CheckLevels.ERROR
    return CheckLevels.NONE


def check_vagrant_plugins() -> CheckLevels:
    """
    Error if `vagrant-vbguest` is not installed.
    """
    # We import Vagrant here instead of at the top of the file because, if
    # the Vagrant executable is not found, a warning is logged.
    #
    # We want to avoid that warning for users of other backends who do not
    # have the Vagrant executable.
    import vagrant

    client = vagrant.Vagrant()
    plugin_list = client.plugin_list()
    if 'vagrant-vbguest' in set(plugin.name for plugin in plugin_list):
        return CheckLevels.NONE

    error(message='The `vagrant-vbguest` plugin must be installed.')
    return CheckLevels.ERROR


@click.command('doctor')
@verbosity_option
def doctor(verbose: int) -> None:
    """
    Diagnose common issues which stop this CLI from working correctly.
    """
    set_logging(verbosity_level=verbose)
    check_functions = [
        check_docker,
        check_1_9_sed,
        check_ssh,
        check_vagrant,
        check_vagrant_plugins,
    ]

    run_doctor_commands(check_functions=check_functions)

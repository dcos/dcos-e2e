"""
Checks for showing up common sources of errors with the Vagrant backend.
"""

import shutil
import sys

import click

from cli.common.doctor import CheckLevels, check_1_9_sed, check_ssh, error


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
    if 'vagrant-vbguest' in set(
        plugin.name for plugin in client.plugin_list()
    ):
        return CheckLevels.NONE

    error(message='The `vagrant-vbguest` plugin must be installed.')
    return CheckLevels.ERROR


@click.command('doctor')
def doctor() -> None:
    """
    Diagnose common issues which stop DC/OS E2E from working correctly.
    """
    check_functions = [
        check_1_9_sed,
        check_ssh,
        check_vagrant,
        check_vagrant_plugins,
    ]

    highest_level = max(function() for function in check_functions)

    if highest_level == CheckLevels.ERROR:
        sys.exit(1)

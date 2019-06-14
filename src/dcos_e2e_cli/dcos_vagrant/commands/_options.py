"""
Common options for ``minidcos vagrant ``.
"""

from typing import Callable

import click

from dcos_e2e.backends import Vagrant


def vm_memory_mb_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the amount of memory given to each VM.
    """
    backend = Vagrant()
    function = click.option(
        '--vm-memory-mb',
        type=click.INT,
        default=backend.vm_memory_mb,
        show_default=True,
        help='The amount of memory to give each VM.',
    )(command)  # type: Callable[..., None]
    return function


def vagrant_box_url_option(command: Callable[..., None],
                           ) -> Callable[..., None]:
    """
    An option decorator for the Vagrant Box URL to use.
    """
    backend = Vagrant()
    function = click.option(
        '--vagrant-box-url',
        type=click.STRING,
        default=backend.vagrant_box_url,
        show_default=True,
        help='The URL of the Vagrant box to use.',
    )(command)  # type: Callable[..., None]
    return function


def vagrant_box_version_option(command: Callable[..., None],
                               ) -> Callable[..., None]:
    """
    An option decorator for the Vagrant Box version to use.
    """
    backend = Vagrant()
    version_constraint_url = (
        'https://www.vagrantup.com/docs/boxes/versioning.html'
        '#version-constraints'
    )
    function = click.option(
        '--vagrant-box-version',
        type=click.STRING,
        default=backend.vagrant_box_version,
        show_default=True,
        help=(
            'The version of the Vagrant box to use. '
            'See {version_constraint_url} for details.'
        ).format(version_constraint_url=version_constraint_url),
    )(command)  # type: Callable[..., None]
    return function

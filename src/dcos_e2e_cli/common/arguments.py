"""
Click arguments which are common across CLI tools.
"""

from typing import Callable

import click
import click_pathlib


def dcos_checkout_dir_argument(command: Callable[..., None],
                               ) -> Callable[..., None]:
    """
    Decorate a function to allow choosing a DC/OS checkout directory.
    """
    function = click.argument(
        'dcos_checkout_dir',
        type=click_pathlib.Path(exists=True),
        envvar='DCOS_CHECKOUT_DIR',
        default='.',
    )(command)  # type: Callable[..., None]
    return function


def node_args_argument(command: Callable[..., None]) -> Callable[..., None]:
    """
    Decorate a function to allow choosing arguments to run on a node.
    """
    function = click.argument(
        'node_args',
        type=str,
        nargs=-1,
        required=True,
    )(command)  # type: Callable[..., None]
    return function


def installer_argument(command: Callable[..., None]) -> Callable[..., None]:
    """
    Decorate a function to allow choosing a DC/OS installer.
    """
    function = click.argument(
        'installer',
        type=click_pathlib.Path(
            exists=True,
            dir_okay=False,
            file_okay=True,
            resolve_path=True,
        ),
    )(command)  # type: Callable[..., None]
    return function

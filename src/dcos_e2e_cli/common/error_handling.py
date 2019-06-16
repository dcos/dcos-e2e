"""
Tools for handling errors.
"""

import subprocess
import textwrap

import click


def show_calledprocess_error(exc: subprocess.CalledProcessError) -> None:
    """
    Given a ``subprocess.CalledProcessError``, show the full error message and
    stderr in yellow and red.
    """
    click.echo(click.style('Full error:', fg='yellow'))
    click.echo(click.style(textwrap.indent(str(exc), '  '), fg='yellow'))
    stderr = exc.stderr.decode()
    click.echo(click.style(textwrap.indent(stderr, '  '), fg='red'))

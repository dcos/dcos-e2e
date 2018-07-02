"""
Tools for creating a DC/OS cluster.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import click

@click.command('create')
@click.argument('artifact', type=click.Path(exists=True))
@click.pass_context
def create(
    ctx: click.core.Context,
    artifact: str,
) -> None:
    """
    Create a DC/OS cluster.
    """  # noqa: E501
    pass

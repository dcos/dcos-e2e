import click
import logging
import io
import json
import logging
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path
from shutil import rmtree
from subprocess import CalledProcessError
from typing import (  # noqa: F401
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

import click
import click_spinner
import urllib3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docker.types import Mount
from passlib.hash import sha512_crypt

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Transport

def _set_logging(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> None:
    """
    Set logging level depending on the chosen verbosity.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    value = min(value, 3)
    value = max(value, 0)
    verbosity_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
        3: logging.NOTSET,
    }
    # Disable logging calls of the given severity level or below.
    logging.disable(verbosity_map[int(value or 0)])


@click.option(
    '-v',
    '--verbose',
    count=True,
    callback=_set_logging,
)
@click.group(name='dcos-docker')
@click.version_option()
def dcos_docker(verbose: None) -> None:
    """
    Manage DC/OS clusters on Docker.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (verbose, ):
        pass

"""
Tools for managing networking for Docker for Mac.
"""

import io
import json
import logging
import subprocess
import sys
import tarfile
import time
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import copy, rmtree, copytree
from subprocess import CalledProcessError
from tempfile import gettempdir, TemporaryDirectory
from typing import (  # noqa: F401
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import click
import click_spinner
import docker
import urllib3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docker.models.containers import Container
from passlib.hash import sha512_crypt

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node

def setup_mac_network(configuration_dst: Path) -> None:
    """
    Set up a network to connect to nodes on macOS.

    This creates an OpenVPN configuration file and describes how to use it.
    """
    pass

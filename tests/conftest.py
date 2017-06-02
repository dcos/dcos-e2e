"""
Helpers for running tests with `pytest`.
"""

from pathlib import Path

import pytest

from dcos_e2e.backends import DCOS_Docker


@pytest.fixture()
def cluster_backend() -> DCOS_Docker:
    """
    Return a cluster backend to use.

    For now only DC/OS Docker is supported, but in the future this may support
    multiple backends. Potentially, tests using this fixture could be run with
    all backends.
    """
    return DCOS_Docker(
        # We put this files in the `/tmp` directory because that is
        # writable on the Vagrant VM.
        workspace_path=Path('/tmp'),
        generate_config_path=Path('/tmp/dcos_generate_config.sh'),
        dcos_docker_path=Path('/tmp/dcos-docker'),
    )

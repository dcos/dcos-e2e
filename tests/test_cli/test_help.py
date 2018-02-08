
"""
XXX
"""

from pathlib import Path
from textwrap import dedent

import pytest

import cli
from cli import dcos_docker
from click.testing import CliRunner


@pytest.mark.parametrize('arguments', [
    [],
    ['--help'],
])
def test_help(arguments):
    """
    XXX
    """
    runner = CliRunner()
    result = runner.invoke(dcos_docker, arguments)
    assert result.exit_code == 0
    expected_help = dedent(
        """\
        Usage: dcos_docker [OPTIONS] COMMAND [ARGS]...

          Manage DC/OS clusters on Docker.

        Options:
          --help  Show this message and exit.
        """
    )
    assert result.output == expected_help

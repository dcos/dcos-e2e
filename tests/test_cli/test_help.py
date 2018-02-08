"""
XXX
"""

from textwrap import dedent
from typing import List

import pytest
from click.testing import CliRunner

from cli import dcos_docker


@pytest.mark.parametrize('arguments', [
    [],
    ['--help'],
])
def test_help(arguments: List[str]) -> None:
    """
    Help test is shown with `dcos_docker` and `dcos_docker --hlp`.
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

        Commands:
          create  Create a DC/OS cluster.
        """
    )
    assert result.output == expected_help

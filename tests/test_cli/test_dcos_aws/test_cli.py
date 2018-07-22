"""
Tests for the AWS CLI.

This mostly provides error case coverage.
We rely mostly on manual testing.
This is because automated tests for this would be very slow.

For developing help texts, it is useful to add a breakpoint on failure and then
to capture what the help text actually is with:

  .. code: python

       import pyperclip; pyperclip.copy(result.output)
"""

from textwrap import dedent
from typing import List

import pytest
from click.testing import CliRunner

from cli import dcos_aws


class TestDcosAWS:
    """
    Tests for the top level `dcos-aws` command.
    """

    def test_version(self) -> None:
        """
        The CLI version is shown with ``dcos-aws --version``.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_aws,
            ['--version'],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        expected = 'dcos-aws, version'
        assert expected in result.output

    @pytest.mark.parametrize('arguments', [
        [],
        ['--help'],
    ])
    def test_help(self, arguments: List[str]) -> None:
        """
        Help test is shown with `dcos-aws` and `dcos-aws --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_aws, arguments, catch_exceptions=False)
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-aws [OPTIONS] COMMAND [ARGS]...

              Manage DC/OS clusters on AWS.

            Options:
              --version  Show the version and exit.
              --help     Show this message and exit.

            Commands:
              create  Create a DC/OS cluster.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

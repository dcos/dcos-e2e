"""
XXX
"""

from pathlib import Path
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
    Help test is shown with `dcos_docker` and `dcos_docker --help`.
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


class TestCreate:
    def test_help(self) -> None:
        """
        Help test is shown with `dcos_docker create --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['create', '--help'])
        assert result.exit_code == 0
        # yapf breaks multiline noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos_docker create [OPTIONS] ARTIFACT

              Create a DC/OS cluster.

            Options:
              --docker-version [1.13.1|1.11.2]
                                              foo  [default: 1.13.1]
              --linux-distribution [centos-7|ubuntu-16.04|coreos|fedora-23|debian-8]
                                              foo  [default: centos-7]
              --docker-storage-driver [aufs|overlay|overlay2]
                                              by default uses host driver
              --num-masters INTEGER           [default: 1]
              --num-agents INTEGER            [default: 1]
              --num-public-agents INTEGER     [default: 1]
              --extra-config TEXT
              --help                          Show this message and exit.
            """# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

    def test_invalid_artifact_path(self) -> None:
        """
        An error is shown if an invalid artifact path is given.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['create', '/not/a/path'])
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "artifact": '
            'Path "/not/a/path" does not exist.'
        )
        assert expected_error in result.output

    def test_invalid_yaml(self, oss_artifact: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--extra-config',
                '@',
            ],
        )
        assert result.exit_code == 2
        expected_message = dedent(
            """\
           Usage: dcos_docker create [OPTIONS] ARTIFACT

           Error: Invalid value for "--extra-config": "@" is not valid YAML
           """
        )
        assert result.output == expected_message

    def test_not_key_value(self, oss_artifact: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--extra-config',
                'some_key',
            ],
        )
        assert result.exit_code == 2
        # yapf breaks multiline noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
           """\
           Usage: dcos_docker create [OPTIONS] ARTIFACT

           Error: Invalid value for "--extra-config": "some_key" is not a valid DC/OS configuration
            """# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

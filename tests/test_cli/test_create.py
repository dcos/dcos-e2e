"""
XXX
"""

from pathlib import Path

from click.testing import CliRunner

from cli import dcos_docker


def test_invalid_artifact_path() -> None:
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


def test_create(oss_artifact: Path) -> None:
    """
    XXX
    """
    runner = CliRunner()
    result = runner.invoke(dcos_docker, ['create', str(oss_artifact)])
    assert result.exit_code == 0
    assert result.output == ''

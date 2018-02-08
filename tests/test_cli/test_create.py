"""
XXX
"""

from pathlib import Path

from click.testing import CliRunner

from cli import dcos_docker


def test_invalid_artifact_path():
    """
    XXX
    """
    runner = CliRunner()
    result = runner.invoke(dcos_docker, ['create', '/not/a/path'])
    assert result.exit_code == 0
    assert result.output == 'XXX\n'


def test_create(oss_artifact: Path):
    """
    XXX
    """
    runner = CliRunner()
    result = runner.invoke(dcos_docker, ['create', str(oss_artifact)])
    assert result.exit_code == 0
    assert result.output == 'Hello Peter!\n'

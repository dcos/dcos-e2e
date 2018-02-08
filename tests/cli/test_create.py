"""
XXX
"""

from pathlib import Path

from cli import create
from click.testing import CliRunner


def test_invalid_artifact_path():
    """
    XXX
    """
    runner = CliRunner()
    result = runner.invoke(create, ['/not/a/path'])
    assert result.exit_code == 0
    assert result.output == 'XXX\n'


def test_create(oss_artifact: Path):
    """
    XXX
    """
    runner = CliRunner()
    result = runner.invoke(create, [str(oss_artifact)])
    assert result.exit_code == 0
    assert result.output == 'Hello Peter!\n'

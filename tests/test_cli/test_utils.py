"""
Tests for utilities for the CLI.
"""

import uuid
from pathlib import Path

from _pytest.tmpdir import TempdirFactory

from cli._utils import is_enterprise


class TestIsEnterprise:
    """
    Tests for ``is_enterprise``.
    """

    def test_oss(
        self,
        oss_artifact: Path,
        oss_1_11_artifact: Path,
        oss_1_10_artifact: Path,
        tmpdir_factory: TempdirFactory,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS artifact.
        """
        artifacts = [
            oss_artifact,
            oss_1_11_artifact,
            oss_1_10_artifact,
        ]

        for artifact in artifacts:
            random = uuid.uuid4().hex
            workspace_dir = Path(str(tmpdir_factory.mktemp(random)))
            assert not is_enterprise(
                build_artifact=artifact,
                workspace_dir=workspace_dir,
            )

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        enterprise_1_11_artifact: Path,
        enterprise_1_10_artifact: Path,
        tmpdir_factory: TempdirFactory,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise artifact.
        """
        artifacts = [
            enterprise_artifact,
            enterprise_1_11_artifact,
            enterprise_1_10_artifact,
        ]

        for artifact in artifacts:
            random = uuid.uuid4().hex
            workspace_dir = Path(str(tmpdir_factory.mktemp(random)))
            assert is_enterprise(
                build_artifact=artifact,
                workspace_dir=workspace_dir,
            )

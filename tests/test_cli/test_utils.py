"""
Tests for utilities for the CLI.
"""

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
        tmpdir: local,
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
            assert not is_enterprise(
                build_artifact=artifact,
                workspace_dir=workspace_dir,
            )

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        enterprise_1_11_artifact: Path,
        enterprise_1_10_artifact: Path,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise artifact.
        """
        artifacts = []
        pass

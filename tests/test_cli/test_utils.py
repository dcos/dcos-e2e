"""
Tests for utilities for the CLI.
"""


class TestIsEnterprise:
    """
    Tests for ``is_enterprise``.
    """

    def test_oss(
        self,
        oss_artifact: Path,
        oss_1_11_artifact: Path,
        oss_1_10_artifact: Path,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS artifact.
        """
        pass

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        enterprise_1_11_artifact: Path,
        enterprise_1_10_artifact: Path,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise artifact.
        """
        pass

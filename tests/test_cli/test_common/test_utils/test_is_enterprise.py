"""
Tests for ``_is_enterprise``.
"""

from pathlib import Path

# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from cli.common.utils import _is_enterprise


class TestOSS:
    """
    Tests for giving OSS artifacts to ``_is_enterprise``.

    We could use pytest parameterization to consolidate these tests, but then
    we would have to store all artifacts and Travis builders run out of space.
    """

    def test_master(
        self,
        oss_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS master artifact.
        """
        assert not _is_enterprise(
            build_artifact=oss_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_12(
        self,
        oss_1_12_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS 1.12 artifact.
        """
        assert not _is_enterprise(
            build_artifact=oss_1_12_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_11(
        self,
        oss_1_11_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS 1.11 artifact.
        """
        assert not _is_enterprise(
            build_artifact=oss_1_11_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_10(
        self,
        oss_1_10_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS 1.10 artifact.
        """
        assert not _is_enterprise(
            build_artifact=oss_1_10_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_9(
        self,
        oss_1_9_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS 1.9 artifact.
        """
        assert not _is_enterprise(
            build_artifact=oss_1_9_artifact,
            workspace_dir=Path(str(tmpdir)),
        )


class TestEnterprise:
    """
    Tests for giving Enterprise artifacts to ``_is_enterprise``.

    We could use pytest parameterization to consolidate these tests, but then
    we would have to store all artifacts and Travis builders run out of space.
    """

    def test_master(
        self,
        enterprise_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise master artifact.
        """
        assert _is_enterprise(
            build_artifact=enterprise_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_12(
        self,
        enterprise_1_12_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise 1.12 artifact.
        """
        assert _is_enterprise(
            build_artifact=enterprise_1_12_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_11(
        self,
        enterprise_1_11_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise 1.11 artifact.
        """
        assert _is_enterprise(
            build_artifact=enterprise_1_11_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_10(
        self,
        enterprise_1_10_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise 1.10 artifact.
        """
        assert _is_enterprise(
            build_artifact=enterprise_1_10_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

    def test_1_9(
        self,
        enterprise_1_9_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise 1.9 artifact.
        """
        assert _is_enterprise(
            build_artifact=enterprise_1_9_artifact,
            workspace_dir=Path(str(tmpdir)),
        )

"""
Tests for utilities for the CLI.
"""

import shutil
import uuid
from pathlib import Path

from _pytest.tmpdir import TempdirFactory

from cli.common.utils import _is_enterprise

def _oss_test(artifact: Path, workspace_dir: Path):
    """
    ``False`` is returned when given a DC/OS OSS artifact.
    """
    assert not _is_enterprise(
        build_artifact=artifact,
        workspace_dir=workspace_dir,
    )


class TestIsEnterprise:
    """
    Tests for ``_is_enterprise``.
    """

    def test_master(
        self,
        oss_artifact: Path,
        enterprise_artifact: Path,
    ) -> None:
        """
        ``False`` is returned when given a DC/OS OSS artifact.
        """
        artifacts = [
            oss_artifact,
            oss_1_11_artifact,
            oss_1_10_artifact,
            oss_1_9_artifact,
        ]

        for artifact in artifacts:
            random = uuid.uuid4().hex
            workspace_dir = Path(str(tmpdir_factory.mktemp(random)))
            assert not _is_enterprise(
                build_artifact=artifact,
                workspace_dir=workspace_dir,
            )
            # We delete the workspace during the test so as not to use too much
            # space for the test.
            shutil.rmtree(path=str(workspace_dir))

    def test_enterprise(
        self,
        enterprise_artifact: Path,
        enterprise_1_11_artifact: Path,
        enterprise_1_10_artifact: Path,
        enterprise_1_9_artifact: Path,
        tmpdir_factory: TempdirFactory,
    ) -> None:
        """
        ``True`` is returned when given a DC/OS Enterprise artifact.
        """
        artifacts = [
            enterprise_artifact,
            enterprise_1_11_artifact,
            enterprise_1_10_artifact,
            enterprise_1_9_artifact,
        ]

        for artifact in artifacts:
            random = uuid.uuid4().hex
            workspace_dir = Path(str(tmpdir_factory.mktemp(random)))
            assert _is_enterprise(
                build_artifact=artifact,
                workspace_dir=workspace_dir,
            )
            # We delete the workspace during the test so as not to use too much
            # space for the test.
            shutil.rmtree(path=str(workspace_dir))

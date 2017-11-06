"""
Tests for the Docker backend.
"""

import uuid
from pathlib import Path

# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
import pytest
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster


class TestCustomMasterMounts:
    """
    Tests for adding mounts to master nodes.
    """

    def test_custom_master_mounts(
        self,
        tmpdir: local,
        oss_artifact: str,
    ) -> None:
        """
        It is possible to mount local files to master nodes.
        """
        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_path = Path('/etc/on_master_nodes.txt')
        custom_master_mounts = {
            str(local_file): {
                'bind': str(master_path),
                'mode': 'rw',
            },
        }
        backend = Docker(custom_master_mounts=custom_master_mounts)

        with Cluster(
            cluster_backend=backend,
            generate_config_url=oss_artifact,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            args = ['cat', str(master_path)]
            result = master.run_as_root(args=args)
            assert result.stdout.decode() == content

            new_content = str(uuid.uuid4())
            local_file.write(new_content)
            result = master.run_as_root(args=args)
            assert result.stdout.decode() == new_content


class TestArtifactUrl:
    """
    Tests for build artifacts in different locations.
    """

    def test_no_artifact_url(self, tmpdir: local) -> None:

        with Cluster(
            cluster_backend=Docker(workspace_dir=tmpdir),
            generate_config_url=None,
            masters=1,
            agents=0,
            public_agents=0,
        ):
            with pytest.raises(ValueError):
                pass

    def test_unsupported_artifact_url(self, tmpdir: local) -> None:

        unsupported_url = 'scheme://{}'.format(uuid.uuid4())

        with Cluster(
            cluster_backend=Docker(workspace_dir=tmpdir),
            generate_config_url=unsupported_url,
            masters=1,
            agents=0,
            public_agents=0,
        ):
            with pytest.raises(ValueError):
                pass

    def test_local_artifact_url(
        self, tmpdir: local, oss_artifact: str
    ) -> None:

        with Cluster(
            cluster_backend=Docker(workspace_dir=tmpdir),
            generate_config_url=oss_artifact,
            masters=1,
            agents=0,
            public_agents=0,
        ):
            pass

    def test_remote_artifact_url(
        self, tmpdir: local, oss_artifact_url: str
    ) -> None:

        with Cluster(
            cluster_backend=Docker(workspace_dir=tmpdir),
            generate_config_url=oss_artifact_url,
            masters=1,
            agents=0,
            public_agents=0,
        ):
            pass

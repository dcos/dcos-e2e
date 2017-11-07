"""
Tests for the Docker backend.
"""

import uuid
from pathlib import Path
from subprocess import CalledProcessError

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
        oss_artifact: Path,
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
            build_artifact=oss_artifact,
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


class TestBadParameters:
    """
    Tests for bad parameters passed to Docker clusters.
    """

    def test_no_build_artifact(self, tmpdir: local) -> None:
        """
        The docker backend requires a build artifact in order
        to launch a DC/OS cluster.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=Docker(workspace_dir=tmpdir),
                build_artifact=None,
                masters=1,
                agents=0,
                public_agents=0,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The Docker backend only supports creating new clusters. '
            'Therefore the given cluster backend must receive a build '
            'artifact.'
        )

        assert str(excinfo.value) == expected_error

    def test_unsupported_build_artifact(
        self, tmpdir: local, oss_artifact_url: str
    ) -> None:
        """
        If the given build artifact is not a Path
        the Docker backend will not accept it.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            with Cluster(
                cluster_backend=Docker(workspace_dir=tmpdir),
                build_artifact=oss_artifact_url,
                masters=1,
                agents=0,
                public_agents=0,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The Docker backend only supports creating clusters from '
            'build artifacts specified by Path.'
        )

        assert str(excinfo.value) == expected_error

    def test_invalid_build_artifact(self, tmpdir: local) -> None:
        """
        If the given Path does not point to a valid build artifact
        the subprocess for calling DC/OS Docker will fail.
        """
        invalid_build_artifact = Path('/{}'.format(uuid.uuid4()))

        with pytest.raises(CalledProcessError):
            with Cluster(
                cluster_backend=Docker(workspace_dir=tmpdir),
                build_artifact=invalid_build_artifact,
                masters=1,
                agents=0,
                public_agents=0,
            ):
                pass  # pragma: no cover

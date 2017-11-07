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


class TestBadParameters:
    """
    Tests for bad parameters passed to Docker clusters.
    """

    def test_no_artifact_url(self, tmpdir: local) -> None:
        """
        The docker backend requires an artifact url in order
        to launch a DC/OS cluster.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=Docker(workspace_dir=tmpdir),
                generate_config_url=None,
                masters=1,
                agents=0,
                public_agents=0,
            ):
                pass

        expected_error = (
            'The Docker backend only supports creating new clusters. '
            'Therefore the given cluster backend must receive a build '
            'artifact url.'
        )

        assert str(excinfo.value) == expected_error

    def test_unsupported_artifact_url(self, tmpdir: local) -> None:
        """
        The Docker backend supports file | HTTP | HTTPS schemes.
        If a different url scheme is given a ValueError is raised.
        """
        unsupported_url = 'scheme://{}'.format(uuid.uuid4())

        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=Docker(workspace_dir=tmpdir),
                generate_config_url=unsupported_url,
                masters=1,
                agents=0,
                public_agents=0,
            ):
                pass

        expected_error = (
            'The given artifact url scheme is not supported '
            'by the Docker cluster backend.'
        )

        assert str(excinfo.value) == expected_error

    def test_not_an_artifact_url(self, tmpdir: local) -> None:
        """
        If the given url does not point to a valid build artifact
        the subprocess for calling DC/OS Docker will fail.
        """
        invalid_artifact_url = 'https://google.com'

        with pytest.raises(CalledProcessError):
            with Cluster(
                cluster_backend=Docker(workspace_dir=tmpdir),
                generate_config_url=invalid_artifact_url,
                masters=1,
                agents=0,
                public_agents=0,
            ):
                pass

    def test_local_artifact_url(
        self, tmpdir: local, oss_artifact: str
    ) -> None:
        """
        Asserts whether a cluster is successfully created from
        an artifact url that points to the local file system.
        """
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
        """
        Asserts whether a cluster is successfully created
        from an artifact url that point to a HTTPS server.
        """
        with Cluster(
            cluster_backend=Docker(workspace_dir=tmpdir),
            generate_config_url=oss_artifact_url,
            masters=1,
            agents=0,
            public_agents=0,
        ):
            pass

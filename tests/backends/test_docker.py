"""
Tests for the Docker backend.
"""

import uuid
from pathlib import Path
from typing import Iterator

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
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster.install_dcos_from_path(oss_artifact)
            (master, ) = cluster.masters
            args = ['cat', str(master_path)]
            result = master.run(args=args, user=cluster.default_ssh_user)
            assert result.stdout.decode() == content

            new_content = str(uuid.uuid4())
            local_file.write(new_content)
            result = master.run(args=args, user=cluster.default_ssh_user)
            assert result.stdout.decode() == new_content


class TestUnsupportedInstallationMethods:
    """
    Tests for unsupported installation methods on Docker clusters.
    """

    @pytest.fixture(scope='module')
    def dcos_cluster(self) -> Iterator[Cluster]:
        """
        Return a `Cluster`.

        This is module scoped as we do not intend to modify the cluster.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            yield cluster

    def test_install_dcos_from_url(
        self,
        dcos_cluster: Cluster,
        oss_artifact_url: str,
    ) -> None:
        """
        The Docker backend requires a build artifact in order
        to launch a DC/OS cluster.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            dcos_cluster.install_dcos_from_url(oss_artifact_url)

        expected_error = (
            'The Docker backend does not support the installation of DC/OS '
            'by build artifacts passed via URL string. This is because a more '
            'efficient installation method exists in `install_dcos_from_path`.'
        )

        assert str(excinfo.value) == expected_error

"""
Tests for the DC/OS Docker backend.
"""

import uuid
from pathlib import Path

import pytest
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import DCOS_Docker
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
        If no file exists at the given `generate_config_path`, a `ValueError`
        is raised.
        """
        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_path = Path('/etc/on_master_nodes.txt')
        custom_master_mounts = {
            str(local_file): {'bind': str(master_path), 'mode': 'rw'},
        }
        backend = DCOS_Docker(custom_master_mounts=custom_master_mounts)

        with Cluster(
            cluster_backend=backend,
            generate_config_path=oss_artifact,
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

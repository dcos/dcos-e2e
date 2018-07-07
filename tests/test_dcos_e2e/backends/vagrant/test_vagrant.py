"""
Tests for the Vagrant backend.
"""

import uuid
from pathlib import Path

from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster


# We skip these tests because VirtualBox is not available on Travis CI.
class TestRunIntegrationTest:  # pragma: nocover
    """
    Tests for functionality specific to the Vagrant backend.
    """

    def test_run_integration_test(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        It is possible to run DC/OS integration tests on Vagrant.
        This test module only requires a single master node.
        """
        with Cluster(
            cluster_backend=Vagrant(),
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
                log_output_live=True,
            )

            cluster.wait_for_dcos_oss()

            # No error is raised with a successful command.
            cluster.run_integration_tests(
                pytest_command=['pytest', '-vvv', '-s', '-x', 'test_units.py'],
                log_output_live=True,
            )

# TODO pragma ignore
class TestVMNameSuffix:
    # TODO create with a suffix
    # Assert with Virtualbox CLI the structure of the VM name

    def test_default(self):
        with Cluster(
            cluster_backend=Vagrant(),
            masters=1,
            agents=0,
            public_agents=0,
        ):
            pass

    def test_custom(self):
        suffix = uuid.uuid4().hex
        with Cluster(
            cluster_backend=Vagrant(vm_name_suffix=suffix),
            masters=1,
            agents=0,
            public_agents=0,
        ):
            pass

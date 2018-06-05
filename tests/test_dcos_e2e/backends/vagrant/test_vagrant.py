"""
Tests for the Vagrant backend.
"""

import uuid
from pathlib import Path

import pytest
from passlib.hash import sha512_crypt

from dcos_e2e.backends import Vagrant
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution


class TestRunIntegrationTest:
    """
    Tests for functionality specific to the Vagrant backend.
    """

    def test_run_enterprise_integration_test(
        self,
        ee_artifact_path: Path,
        license_key_contents: str,
    ) -> None:
        """
        It is possible to run DC/OS integration tests on Vagrant.
        This test module only requires a single master node.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
            'security': 'strict',
        }

        with Cluster(
            cluster_backend=Vagrant(),
            masters=1,
        ) as cluster:

            cluster.install_dcos_from_path(
                build_artifact=ee_artifact_path,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                log_output_live=True,
            )

            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

            # No error is raised with a successful command.
            cluster.run_integration_tests(
                pytest_command=['pytest', '-vvv', '-s', '-x', 'test_tls.py'],
                env={
                    'DCOS_LOGIN_UNAME': superuser_username,
                    'DCOS_LOGIN_PW': superuser_password,
                },
                log_output_live=True,
            )

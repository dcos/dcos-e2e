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
        enterprise_artifact: Path,
        oss_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        It is possible to run DC/OS integration tests on Vagrant.
        This test module only requires a single master node.
        """
        superuser_username = 'admin'
        superuser_password = 'admin'

        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
            'security': 'strict',
        }

        config = {}

        with Cluster(
            cluster_backend=Vagrant(),
            masters=1,
        ) as cluster:

            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                log_output_live=True,
            )

            cluster.wait_for_dcos()

            # No error is raised with a successful command.
            cluster.run_integration_tests(
                pytest_command=['pytest', '-vvv', '-s', '-x', 'test_units.py'],
                env={
                    'DCOS_LOGIN_UNAME': superuser_username,
                    'DCOS_LOGIN_PW': superuser_password,
                },
                log_output_live=True,
            )

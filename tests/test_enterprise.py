"""
Tests for using the test harness with a DC/OS Enterprise cluster.
"""

import subprocess
import uuid
from pathlib import Path

import pytest
from passlib.hash import sha512_crypt
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestEnterpriseIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        extra_config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
        }

        with Cluster(
            generate_config_path=enterprise_artifact,
            cluster_backend=cluster_backend,
            extra_config=extra_config,
            log_output_live=True,
        ) as cluster:
            # No error is raised with a successful command.
            cluster.run_integration_tests(
                pytest_command=['pytest', '-vvv', '-s', '-x', 'test_tls.py'],
                env={
                    'DCOS_LOGIN_UNAME': superuser_username,
                    'DCOS_LOGIN_PW': superuser_password,
                },
            )


class TestCopyFiles:
    """
    Tests for copying files to nodes.
    """

    def test_copy_files_to_installers(
        self,
        cluster_backend: ClusterBackend,
        tmpdir: local,
        enterprise_artifact: Path,
    ) -> None:
        """
        Files can be copied from the host to the installer nodes at creation
        time.
        """
        files_to_copy_to_installer = {
            source_path: Path('/genconf/on_installer.txt'),
        }
        with Cluster(
            cluster_backend=cluster_backend,
            generate_config_path=enterprise_artifact,
            files_to_copy_to_installer=files_to_copy_to_installer,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster.wait_for_dcos()


class TestWaitForDCOS:
    """
    Tests for `Cluster.wait_for_dcos`.
    """

    @pytest.mark.xfail(
        reason='See https://jira.mesosphere.com/browse/DCOS_OSS-1313',
        raises=AssertionError,
    )
    def test_auth_with_cli(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
    ) -> None:
        """
        After `Cluster.wait_for_dcos`, the cluster can communicate with the
        CLI.

        Unfortunately this test is prone to flakiness as it depends on races.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        extra_config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
        }

        with Cluster(
            generate_config_path=enterprise_artifact,
            cluster_backend=cluster_backend,
            extra_config=extra_config,
            log_output_live=True,
        ) as cluster:
            (master, ) = cluster.masters
            cluster.wait_for_dcos()
            setup_args = [
                'dcos',
                'cluster',
                'setup',
                'https://' + str(master.ip_address),
                '--no-check',
                '--username={username}'.format(username=superuser_username),
                '--password={password}'.format(password=superuser_password),
            ]

            setup = subprocess.run(
                args=setup_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            assert setup.returncode == 0
            # Do not cover the following line - see the xfail marker.
            assert setup.stderr == b''  # pragma: no cover

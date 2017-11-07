"""
Tests for using the test harness with a DC/OS Enterprise cluster.
"""

import subprocess
import uuid
from pathlib import Path

import pytest
import requests
from passlib.hash import sha512_crypt

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestEnterpriseIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: str,
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
            build_artifact=enterprise_artifact,
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

    def test_copy_files_to_installer(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: str,
    ) -> None:
        """
        Files can be copied from the host to the installer node at creation
        time.

        The installer container is removed shortly after creation by DC/OS
        Docker. Therefore, we inspect the symptoms - we can use custom CA
        certificates.

        See CA certificate tests in Enterprise DC/OS for more details.
        """
        cert_filename = 'dcos-ca-certificate.crt'
        key_filename = 'dcos-ca-certificate-key.key'

        genconf = Path('/genconf')
        installer_cert_path = genconf / cert_filename
        installer_key_path = genconf / key_filename

        cert_dir_on_host = Path('tests/certificates').resolve()
        cert_path = cert_dir_on_host / cert_filename
        ca_key_path = cert_dir_on_host / key_filename

        master_key_path = Path(
            '/var/lib/dcos/pki/tls/CA/private/custom_ca.key'
        )

        config = {
            'superuser_username': str(uuid.uuid4()),
            'superuser_password_hash': sha512_crypt.hash(str(uuid.uuid4())),
            'security': 'strict',
            'ca_certificate_path': str(installer_cert_path),
            'ca_certificate_key_path': str(installer_key_path),
        }

        files_to_copy_to_installer = {
            cert_path: installer_cert_path,
            ca_key_path: installer_key_path,
        }

        with Cluster(
            cluster_backend=cluster_backend,
            extra_config=config,
            build_artifact=enterprise_artifact,
            files_to_copy_to_installer=files_to_copy_to_installer,
            log_output_live=True,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            master.send_file(
                local_path=ca_key_path,
                remote_path=master_key_path,
            )

            cluster.wait_for_dcos()
            master_url = 'https://' + str(master.ip_address)
            response = requests.get(master_url, verify=str(cert_path))
            response.raise_for_status()


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
        enterprise_artifact: str,
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
            build_artifact=enterprise_artifact,
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

"""
Tests for using the test harness with a DC/OS Enterprise cluster.
"""

import json
import subprocess
import uuid
from pathlib import Path

import requests
from passlib.hash import sha512_crypt

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Role


class TestEnterpriseIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=enterprise_artifact,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                ip_detect_path=cluster_backend.ip_detect_path,
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


class TestCopyFiles:
    """
    Tests for copying files to nodes.
    """

    def test_copy_files_to_installer(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
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

        cert_dir_on_host = Path('tests/test_dcos_e2e/certificates').resolve()
        cert_path = cert_dir_on_host / cert_filename
        ca_key_path = cert_dir_on_host / key_filename

        master_key_path = Path(
            '/var/lib/dcos/pki/tls/CA/private/custom_ca.key',
        )

        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())

        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'security': 'strict',
            'ca_certificate_path': str(installer_cert_path),
            'ca_certificate_key_path': str(installer_key_path),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        files_to_copy_to_genconf_dir = [
            (cert_path, installer_cert_path),
            (ca_key_path, installer_key_path),
        ]

        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            master.send_file(
                local_path=ca_key_path,
                remote_path=master_key_path,
            )

            cluster.install_dcos_from_path(
                build_artifact=enterprise_artifact,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                log_output_live=True,
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            )

            # We exercise the "http_checks=False" code here but we do not test
            # its functionality. It is a temporary measure while we wait for
            # more thorough dcos-checks.
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
                http_checks=False,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )
            master_url = 'https://' + str(master.public_ip_address)
            response = requests.get(master_url, verify=str(cert_path))
            response.raise_for_status()

    def test_copy_directory_to_installer(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        Directories can be copied from the host to the installer node at
        creation time.

        The installer container is removed shortly after creation by DC/OS
        Docker. Therefore, we inspect the symptoms - we can use custom CA
        certificates.

        See CA certificate tests in Enterprise DC/OS for more details.
        """
        cert_filename = 'dcos-ca-certificate.crt'
        key_filename = 'dcos-ca-certificate-key.key'

        genconf = Path('/genconf')
        installer_cert_path = genconf / 'certificates' / cert_filename
        installer_key_path = genconf / 'certificates' / key_filename

        cert_dir_on_host = Path('tests/test_dcos_e2e/certificates').resolve()
        cert_path = cert_dir_on_host / cert_filename
        ca_key_path = cert_dir_on_host / key_filename

        master_key_path = Path(
            '/var/lib/dcos/pki/tls/CA/private/custom_ca.key',
        )

        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())

        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'security': 'strict',
            'ca_certificate_path': str(installer_cert_path),
            'ca_certificate_key_path': str(installer_key_path),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        files_to_copy_to_genconf_dir = ((cert_dir_on_host, genconf), )

        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            master.send_file(
                local_path=ca_key_path,
                remote_path=master_key_path,
            )

            cluster.install_dcos_from_path(
                build_artifact=enterprise_artifact,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                log_output_live=True,
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            )

            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )
            master_url = 'https://' + str(master.public_ip_address)
            response = requests.get(master_url, verify=str(cert_path))
            response.raise_for_status()

    def test_copy_directory_to_node_installer_genconf_dir(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        Directories can be copied to the ``genconf`` directory from the host
        to the installing node when installing DC/OS.

        Supplying a custom CA certificate directory is a good example for this
        capability. See CA certificate tests in Enterprise DC/OS for more
        details.
        """
        cert_filename = 'dcos-ca-certificate.crt'
        key_filename = 'dcos-ca-certificate-key.key'

        genconf = Path('/genconf')
        installer_cert_path = genconf / 'certificates' / cert_filename
        installer_key_path = genconf / 'certificates' / key_filename

        cert_dir_on_host = Path('tests/test_dcos_e2e/certificates').resolve()
        cert_path = cert_dir_on_host / cert_filename
        ca_key_path = cert_dir_on_host / key_filename

        master_key_path = Path(
            '/var/lib/dcos/pki/tls/CA/private/custom_ca.key',
        )

        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())

        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'security': 'strict',
            'ca_certificate_path': str(installer_cert_path),
            'ca_certificate_key_path': str(installer_key_path),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            master.send_file(
                local_path=ca_key_path,
                remote_path=master_key_path,
            )
            master.install_dcos_from_path(
                build_artifact=enterprise_artifact,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                ip_detect_path=cluster_backend.ip_detect_path,
                role=Role.MASTER,
                files_to_copy_to_genconf_dir=[(cert_dir_on_host, genconf)],
                log_output_live=True,
            )

            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )
            master_url = 'https://' + str(master.public_ip_address)
            response = requests.get(master_url, verify=str(cert_path))
            response.raise_for_status()


class TestSSLDisabled:
    """
    Tests for clusters with SSL disabled.
    """

    def test_wait_for_dcos_ee(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_11_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        A cluster can start up with SSL disabled.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
            'security': 'disabled',
        }

        with Cluster(
            cluster_backend=cluster_backend,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=enterprise_1_11_artifact,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                log_output_live=True,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

            # On 1.11 with security mode disabled, SSL is disabled.
            any_master = next(iter(cluster.masters))
            config_result = any_master.run(
                args=['cat', '/opt/mesosphere/etc/bootstrap-config.json'],
            )
            config = json.loads(config_result.stdout.decode())
            ssl_enabled = config['ssl_enabled']
            assert not ssl_enabled


class TestWaitForDCOS:
    """
    Tests for `Cluster.wait_for_dcos_ee`.
    """

    def test_auth_with_cli(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        After `Cluster.wait_for_dcos_ee`, the DC/OS Enterprise cluster can
        communicate with the CLI.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=enterprise_artifact,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                log_output_live=True,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            (master, ) = cluster.masters
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

            setup_args = [
                'dcos',
                'cluster',
                'setup',
                'https://' + str(master.public_ip_address),
                '--no-check',
                '--username',
                superuser_username,
                '--password',
                superuser_password,
            ]

            setup = subprocess.run(
                args=setup_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            assert setup.returncode == 0
            assert setup.stderr == b''

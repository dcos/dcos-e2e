"""
Tests for the Docker backend.
"""

import uuid
from pathlib import Path

import boto3
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from passlib.hash import sha512_crypt
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import AWS
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node


class TestDefaults:
    """
    Tests for default values of the AWS backend.
    """

    def test_admin_location(self) -> None:
        """
        The default ``admin_location`` is correct.
        """
        assert AWS().admin_location == '0.0.0.0/0'

    def test_aws_region(self) -> None:
        """
        The default ``aws_region`` is correct.
        """
        assert AWS().aws_region == 'us-west-2'

    def test_linux_distribution(self) -> None:
        """
        The default ``linux_distribution`` is correct.
        """
        assert AWS().linux_distribution == Distribution.CENTOS_7


class TestUnsupported:
    """
    Tests for unsupported functionality specific to the AWS backend.
    """

    def test_linux_distribution_coreos(self) -> None:
        """
        The AWS backend does not support the COREOS Linux distribution.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            AWS(linux_distribution=Distribution.COREOS)

        expected_error = (
            'The COREOS Linux distribution is currently not supported by '
            'the AWS backend.'
        )

        assert str(excinfo.value) == expected_error

    def test_linux_distribution_ubuntu(self) -> None:
        """
        The AWS backend does not support the COREOS Linux distribution.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            AWS(linux_distribution=Distribution.UBUNTU_16_04)

        expected_error = (
            'The UBUNTU_16_04 Linux distribution is currently not supported '
            'by the AWS backend.'
        )

        assert str(excinfo.value) == expected_error

    def test_copy_to_installer_not_supported(self) -> None:
        """
        The AWS backend does not support copying files to the installer.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            Cluster(
                cluster_backend=AWS(),
                files_to_copy_to_installer={Path('/'): Path('/')},
            )

        expected_error = (
            'Copying files to the installer is currently not supported by the '
            'AWS backend.'
        )

        assert str(excinfo.value) == expected_error

    def test_destroy_node(self):
        """
        Destroying a particular node is not supported on the AWS backend.
        """
        with Cluster(cluster_backend=AWS()) as cluster:
            (agent, ) = cluster.agents
            with pytest.raises(NotImplementedError):
                cluster.destroy_node(node=agent)


class TestRunIntegrationTest:
    """
    Tests for functionality specific to the AWS backend.
    """

    @pytest.mark.parametrize('linux_distribution', [Distribution.CENTOS_7])
    def test_run_enterprise_integration_test(
        self,
        ee_artifact_url: str,
        license_key_contents: str,
        linux_distribution: Distribution,
    ) -> None:
        """
        It is possible to run DC/OS integration tests on AWS.
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
            cluster_backend=AWS(linux_distribution=linux_distribution),
            masters=1,
        ) as cluster:

            cluster.install_dcos_from_url(
                build_artifact=ee_artifact_url,
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


def _write_key_pair(public_key_path: Path, private_key_path: Path) -> None:
    """
    Write an RSA key pair for connecting to nodes via SSH.

    Args:
        public_key_path: Path to write public key to.
        private_key_path: Path to a private key file to write.
    """
    rsa_key_pair = rsa.generate_private_key(
        backend=default_backend(),
        public_exponent=65537,
        key_size=2048,
    )

    public_key = rsa_key_pair.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH,
    )

    private_key = rsa_key_pair.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_path.write_bytes(data=public_key)
    private_key_path.write_bytes(data=private_key)


class TestCustomKeyPair:
    """
    Tests for passing a custom key pair to the AWS backend.
    """

    def test_custom_key_pair(self, tmpdir: local):
        """
        It is possible to pass a custom key pair to the AWS backend.
        """
        key_name = 'e2e-test-{random}'.format(random=uuid.uuid4().hex)
        private_key_path = Path(str(tmpdir.join('private_key')))
        public_key_path = Path(str(tmpdir.join('public_key')))
        _write_key_pair(
            public_key_path=public_key_path,
            private_key_path=private_key_path,
        )
        backend = AWS(aws_key_pair=(key_name, private_key_path))
        region_name = backend.aws_region
        ec2 = boto3.client('ec2', region_name=region_name)
        ec2.import_key_pair(
            KeyName=key_name,
            PublicKeyMaterial=public_key_path.read_bytes(),
        )

        try:
            with Cluster(
                cluster_backend=backend,
                agents=0,
                public_agents=0,
            ) as cluster:
                (master, ) = cluster.masters
                node = Node(
                    public_ip_address=master.public_ip_address,
                    private_ip_address=master.private_ip_address,
                    default_user=master.default_user,
                    ssh_key_path=private_key_path,
                )

                node.run(args=['echo', '1'])
        finally:
            ec2.delete_key_pair(KeyName=key_name)


class TestDCOSInstallation:
    """
    Test the platform-independent DC/OS installation on AWS.
    """

    def test_install_dcos_from_path(self, oss_artifact: Path) -> None:
        """
        The AWS backend requires a build artifact path in order to launch
        a DC/OS cluster.
        """
        with Cluster(
            cluster_backend=AWS(),
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
            )

            cluster.wait_for_dcos_oss()

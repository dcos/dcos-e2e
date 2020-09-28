"""
Tests for the AWS backend.
"""

import stat
import uuid
from pathlib import Path
from textwrap import dedent
from typing import Dict

import boto3
import pytest
from boto3.resources.base import ServiceResource
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from passlib.hash import sha512_crypt

from dcos_e2e.backends import AWS
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node, Output, Role


class TestDefaults:
    """
    Tests for default values of the AWS backend.
    """

    def test_admin_location(self) -> None:
        """
        The default ``admin_location`` is correct.
        """
        assert AWS().admin_location == '0.0.0.0/0'

    def test_aws_instance_type(self) -> None:
        """
        The default ``aws_instance_type`` is correct.
        """
        assert AWS().aws_instance_type == 'm4.large'

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

    def test_linux_distribution_ubuntu(self) -> None:
        """
        The AWS backend does not support the Ubuntu Linux distribution.
        """
        with pytest.raises(NotImplementedError) as excinfo:
            AWS(linux_distribution=Distribution.UBUNTU_16_04)

        expected_error = (
            'The UBUNTU_16_04 Linux distribution is currently not supported '
            'by the AWS backend.'
        )

        assert str(excinfo.value) == expected_error

    def test_destroy_node(self) -> None:
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
        ee_installer_url: str,
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

        cluster_backend = AWS(linux_distribution=linux_distribution)

        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
        ) as cluster:

            cluster.install_dcos_from_url(
                dcos_installer=ee_installer_url,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                output=Output.LOG_AND_CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )

            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

            # No error is raised with a successful command.
            # We choose a test file which runs very quickly.
            fast_test_file = 'test_marathon_authn_authz.py'
            cluster.run_with_test_environment(
                args=['pytest', '-vvv', '-s', '-x', fast_test_file],
                env={
                    'DCOS_LOGIN_UNAME': superuser_username,
                    'DCOS_LOGIN_PW': superuser_password,
                },
                output=Output.LOG_AND_CAPTURE,
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

    private_key_path.chmod(mode=stat.S_IRUSR)


class TestCustomKeyPair:
    """
    Tests for passing a custom key pair to the AWS backend.
    """

    def test_custom_key_pair(self, tmp_path: Path) -> None:
        """
        It is possible to pass a custom key pair to the AWS backend.
        """
        key_name = 'e2e-test-{random}'.format(random=uuid.uuid4().hex)
        private_key_path = tmp_path / 'private_key'
        public_key_path = tmp_path / 'public_key'
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
    Test installing DC/OS.
    """

    def test_install_dcos_from_path(self, oss_installer: Path) -> None:
        """
        It is possible to install DC/OS on an AWS cluster from a local path.
        """
        cluster_backend = AWS()
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                output=Output.LOG_AND_CAPTURE,
            )
            cluster.wait_for_dcos_oss()

    def test_install_dcos_from_node(
        self,
        oss_installer_url: str,
    ) -> None:
        """
        It is possible to install DC/OS on an AWS cluster node by node.
        """
        cluster_backend = AWS()
        with Cluster(
            cluster_backend=cluster_backend,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            master.install_dcos_from_url(
                dcos_installer=oss_installer_url,
                dcos_config=cluster.base_config,
                role=Role.MASTER,
                output=Output.LOG_AND_CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()

    def test_install_dcos_with_custom_ip_detect(
        self,
        oss_installer_url: str,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to install DC/OS on an AWS with a custom IP detect
        script.
        """
        cluster_backend = AWS()
        with Cluster(
            cluster_backend=cluster_backend,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            ip_detect_file = tmp_path / 'ip-detect'
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write_text(ip_detect_contents)

            cluster.install_dcos_from_url(
                dcos_installer=oss_installer_url,
                dcos_config=cluster.base_config,
                output=Output.LOG_AND_CAPTURE,
                ip_detect_path=ip_detect_file,
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/detect_ip'],
            )
            node_script_contents = cat_result.stdout.decode()
            assert node_script_contents == ip_detect_contents
            backend_script_path = cluster_backend.ip_detect_path
            backend_script_contents = backend_script_path.read_text()
            assert node_script_contents != backend_script_contents

    def test_install_dcos_with_custom_genconf(
        self,
        oss_installer_url: str,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to install DC/OS on an AWS including
        custom files in the ``genconf`` directory.
        """
        cluster_backend = AWS()
        with Cluster(
            cluster_backend=cluster_backend,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            ip_detect_file = tmp_path / 'ip-detect'
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write_text(ip_detect_contents)

            cluster.install_dcos_from_url(
                dcos_installer=oss_installer_url,
                dcos_config=cluster.base_config,
                output=Output.LOG_AND_CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=[
                    (ip_detect_file, Path('/genconf/ip-detect')),
                ],
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/detect_ip'],
            )
            node_script_contents = cat_result.stdout.decode()
            assert node_script_contents == ip_detect_contents
            backend_script_path = cluster_backend.ip_detect_path
            backend_script_contents = backend_script_path.read_text()
            assert node_script_contents != backend_script_contents


def _tag_dict(instance: ServiceResource) -> Dict[str, str]:
    """
    Return an EC2 instance's tags as a dictionary.
    """
    tag_dict = dict()  # type: Dict[str, str]
    tags = instance.tags or {}

    for tag in tags:
        key = tag['Key']
        value = tag['Value']
        tag_dict[key] = value

    return tag_dict


def _get_ec2_instance_from_node(
    node: Node,
    aws_region: str,
) -> ServiceResource:
    """
    Return the EC2 instance which matches the given ``node`` on the given
    ``aws_region``.
    """
    ec2 = boto3.resource('ec2', region_name=aws_region)
    [instance] = list(
        ec2.instances.filter(
            Filters=[
                {
                    'Name': 'ip-address',
                    'Values': [str(node.public_ip_address)],
                },
            ],
        ),
    )

    return instance


class TestTags:
    """
    Tests for setting tags on EC2 instances.
    """

    def test_custom(self) -> None:
        """
        It is possible to set node EC2 instance tags.
        """
        cluster_key = uuid.uuid4().hex
        cluster_value = uuid.uuid4().hex
        cluster_tags = {cluster_key: cluster_value}

        master_key = uuid.uuid4().hex
        master_value = uuid.uuid4().hex
        master_tags = {master_key: master_value}

        agent_key = uuid.uuid4().hex
        agent_value = uuid.uuid4().hex
        agent_tags = {agent_key: agent_value}

        public_agent_key = uuid.uuid4().hex
        public_agent_value = uuid.uuid4().hex
        public_agent_tags = {public_agent_key: public_agent_value}

        cluster_backend = AWS(
            ec2_instance_tags=cluster_tags,
            master_ec2_instance_tags=master_tags,
            agent_ec2_instance_tags=agent_tags,
            public_agent_ec2_instance_tags=public_agent_tags,
        )

        with Cluster(cluster_backend=cluster_backend) as cluster:
            for node in cluster.masters:
                node_instance = _get_ec2_instance_from_node(
                    node=node,
                    aws_region=cluster_backend.aws_region,
                )
                node_tags = _tag_dict(instance=node_instance)
                assert node_tags[cluster_key] == cluster_value
                assert node_tags[master_key] == master_value
                assert agent_key not in node_tags
                assert public_agent_key not in node_tags

            for node in cluster.agents:
                node_instance = _get_ec2_instance_from_node(
                    node=node,
                    aws_region=cluster_backend.aws_region,
                )
                node_tags = _tag_dict(instance=node_instance)
                assert node_tags[cluster_key] == cluster_value
                assert node_tags[agent_key] == agent_value
                assert master_key not in node_tags
                assert public_agent_key not in node_tags

            for node in cluster.public_agents:
                node_instance = _get_ec2_instance_from_node(
                    node=node,
                    aws_region=cluster_backend.aws_region,
                )
                node_tags = _tag_dict(instance=node_instance)
                assert node_tags[cluster_key] == cluster_value
                assert node_tags[public_agent_key] == public_agent_value
                assert master_key not in node_tags
                assert agent_key not in node_tags

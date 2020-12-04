"""
Tests for support of legacy versions of DC/OS.

We do not test the whole matrix of support, such as each version with each
Docker version or base operating system, for cost reasons.
"""

import uuid
from pathlib import Path

from passlib.hash import sha512_crypt

from dcos_e2e.base_classes import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import DCOSVariant, Output


class Test113:
    """
    Tests for running DC/OS 1.13.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_1_13_installer: Path,
    ) -> None:
        """
        An open source DC/OS 1.13 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_1_13_installer,
                dcos_config=cluster.base_config,
                output=Output.LOG_AND_CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('1.13')
                assert build.commit
                assert build.variant == DCOSVariant.OSS

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_13_installer: Path,
        license_key_contents: str,
    ) -> None:
        """
        A DC/OS Enterprise 1.13 cluster can be started.
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
                dcos_installer=enterprise_1_13_installer,
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
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('1.13')
                assert build.commit
                assert build.variant == DCOSVariant.ENTERPRISE


class Test20:
    """
    Tests for running DC/OS 2.0.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_2_0_installer: Path,
    ) -> None:
        """
        An open source DC/OS 2.0 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_2_0_installer,
                dcos_config=cluster.base_config,
                output=Output.LOG_AND_CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.0')
                assert build.commit
                assert build.variant == DCOSVariant.OSS

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_2_0_installer: Path,
        license_key_contents: str,
    ) -> None:
        """
        A DC/OS Enterprise 2.0 cluster can be started.
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
                dcos_installer=enterprise_2_0_installer,
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
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.0')
                assert build.commit
                assert build.variant == DCOSVariant.ENTERPRISE


class Test21:
    """
    Tests for running DC/OS 2.1.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_2_1_installer: Path,
    ) -> None:
        """
        An open source DC/OS 2.1 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_2_1_installer,
                dcos_config=cluster.base_config,
                output=Output.LOG_AND_CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.1')
                assert build.commit
                assert build.variant == DCOSVariant.OSS

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_2_1_installer: Path,
        license_key_contents: str,
    ) -> None:
        """
        A DC/OS Enterprise 2.1 cluster can be started.
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
                dcos_installer=enterprise_2_1_installer,
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
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.1')
                assert build.commit
                assert build.variant == DCOSVariant.ENTERPRISE

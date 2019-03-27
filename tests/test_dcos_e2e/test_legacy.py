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
from dcos_e2e.node import Output


class Test19:
    """
    Tests for running DC/OS 1.9.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_1_9_installer: Path,
    ) -> None:
        """
        An open source DC/OS 1.9 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_1_9_installer,
                dcos_config=cluster.base_config,
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_9_installer: Path,
    ) -> None:
        """
        A DC/OS Enterprise 1.9 cluster can be started.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
        }

        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=enterprise_1_9_installer,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )


class Test110:
    """
    Tests for running DC/OS 1.10.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_1_10_installer: Path,
    ) -> None:
        """
        An open source DC/OS 1.10 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_1_10_installer,
                dcos_config=cluster.base_config,
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_10_installer: Path,
        license_key_contents: str,
    ) -> None:
        """
        A DC/OS Enterprise 1.10 cluster can be started.
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
                dcos_installer=enterprise_1_10_installer,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )


class Test111:
    """
    Tests for running DC/OS 1.11.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_1_11_installer: Path,
    ) -> None:
        """
        An open source DC/OS 1.11 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_1_11_installer,
                dcos_config=cluster.base_config,
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_11_installer: Path,
        license_key_contents: str,
    ) -> None:
        """
        A DC/OS Enterprise 1.11 cluster can be started.
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
                dcos_installer=enterprise_1_11_installer,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )


class Test112:
    """
    Tests for running DC/OS 1.12.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_1_12_installer: Path,
    ) -> None:
        """
        An open source DC/OS 1.12 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_1_12_installer,
                dcos_config=cluster.base_config,
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_12_installer: Path,
        license_key_contents: str,
    ) -> None:
        """
        A DC/OS Enterprise 1.12 cluster can be started.
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
                dcos_installer=enterprise_1_12_installer,
                dcos_config={
                    **cluster.base_config,
                    **config,
                },
                output=Output.CAPTURE,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

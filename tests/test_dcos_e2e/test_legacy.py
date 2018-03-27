"""
Tests for support of legacy versions of DC/OS.

We do not test the whole matrix of support, such as each version with each
Docker version or base operating system, for cost reasons.
"""

import uuid
from pathlib import Path

from passlib.hash import sha512_crypt

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class Test19:
    """
    Tests for running DC/OS 1.9.
    """

    def test_oss(
        self,
        cluster_backend: ClusterBackend,
        oss_1_9_artifact: Path,
    ) -> None:
        """
        An open source DC/OS 1.9 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_1_9_artifact,
                log_output_live=True,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_9_artifact: Path,
    ) -> None:
        """
        A DC/OS Enterprise 1.9 cluster can be started.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
        }

        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=enterprise_1_9_artifact,
                extra_config=config,
                log_output_live=True,
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
        oss_1_10_artifact: Path,
    ) -> None:
        """
        An open source DC/OS 1.10 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_1_10_artifact,
                log_output_live=True,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_10_artifact: Path,
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
                build_artifact=enterprise_1_10_artifact,
                extra_config=config,
                log_output_live=True,
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
        oss_1_11_artifact: Path,
    ) -> None:
        """
        An open source DC/OS 1.11 cluster can be started.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_1_11_artifact,
                log_output_live=True,
            )
            cluster.wait_for_dcos_oss()

    def test_enterprise(
        self,
        cluster_backend: ClusterBackend,
        enterprise_1_11_artifact: Path,
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
                build_artifact=enterprise_1_11_artifact,
                extra_config=config,
                log_output_live=True,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

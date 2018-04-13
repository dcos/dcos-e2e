"""
Tests for using the test harness with a DC/OS Enterprise cluster.
"""

import subprocess
import uuid
from pathlib import Path

import requests
from passlib.hash import sha512_crypt

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestExperiment:
    """
    Tests for running integration tests on a node.
    """

    def test_1(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        helper(cluster_backend, enterprise_artifact, license_key_contents)

    def test_2(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        helper(cluster_backend, enterprise_artifact, license_key_contents)

    def test_3(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        helper(cluster_backend, enterprise_artifact, license_key_contents)

    def test_4(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        helper(cluster_backend, enterprise_artifact, license_key_contents)

    def test_5(
        self,
        cluster_backend: ClusterBackend,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        helper(cluster_backend, enterprise_artifact, license_key_contents)


def helper(cluster_backend, enterprise_artifact, license_key_contents):
    superuser_username = 'bootstrapuser'
    superuser_password = 'deleteme'
    superuser_hashed_password = sha512_crypt.hash(superuser_password)

    print('EXPECTED CREDENTIALS')
    print('SUPERUSER_USERNAME: ' + superuser_username)
    print('SUPERUSER_PASSWORD: ' + superuser_password)
    print('SUPERUSER_PASSWORD_HASH: ' + superuser_hashed_password)

    config = {
        'superuser_username': superuser_username,
        'superuser_password_hash': superuser_hashed_password,
        'fault_domain_enabled': False,
        'license_key_contents': license_key_contents,
    }

    with Cluster(cluster_backend=cluster_backend) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=enterprise_artifact,
            extra_config=config,
            log_output_live=False,
        )
        cluster.wait_for_dcos_ee(
            superuser_username=superuser_username,
            superuser_password=superuser_password,
        )

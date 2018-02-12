"""
Tests for the Docker backend.
"""

import os
import uuid
from pathlib import Path

from passlib.hash import sha512_crypt

from dcos_e2e.backends import AWS
from dcos_e2e.cluster import Cluster


class TestAWSBackend:
    """
    Tests for functionality specific to the Docker backend.
    """

    def test_cluster(self, license_key_contents: str) -> None:

        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        aws_backend = AWS(
            aws_key_name='default',
            ssh_key_path=Path('/Users/tim/.ssh/default'),
        )

        with Cluster(
            cluster_backend=aws_backend,
            masters=1,
        ) as cluster:
            cluster.install_dcos_from_url(
                build_artifact=os.environ['INSTALLER_URL'],
                extra_config=config,
                log_output_live=True,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

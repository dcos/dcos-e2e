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

    def test_distribution_not_supported(
        self,
        license_key_contents: str,
    ) -> None:
        pass

    def test_run_integration_test(self, license_key_contents: str) -> None:

        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
            'security': 'strict',
        }

        aws_backend = AWS(workspace_dir=Path('/tmp'))

        with Cluster(
            cluster_backend=aws_backend,
            masters=1,
        ) as cluster:

            (master, ) = cluster.masters

            result = master.run(
                args=['echo', '$USER'],
                shell=True,
            )

            result.stdout.decode() == 'centos\n'

            cluster.install_dcos_from_url(
                build_artifact=os.environ['INSTALLER_URL'],
                extra_config=config,
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

            # TODO: Defintely to do before shipping
            # #. Test running on Travis
            #   - 100% test coverage
            #   - Add keys to Travis
            #   - Test install from Path
            # #. Initial documentation - document that this does not work on
            #    Windows, or how to get it to work with WSL

            # TODO: Nice to have
            # Get Bilal to use it
            # Get it to work with Windows

            # TODO: Vendoring
            # Change DC/OS Launch as there is an error on import after
            # vendoring:
            # pkg_resource('dcos_launch') -> ('dcos_e2e._vendor.dcos_launch')
            # config.py, util.py, platform/aws.py
            #Idea is for it do use inspect rather than pkg_resource

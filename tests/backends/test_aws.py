"""
Tests for the AWS backend.
"""
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestAWSBackend:
    """
    Test running integration using the AWS backend.
    """

    def test_run_pytest(
        self, aws_backend: ClusterBackend, oss_artifact_url: str
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=aws_backend) as cluster:
            cluster.install_dcos_from_url(
                build_artifact=oss_artifact_url, log_output_live=True
            )
            cluster.wait_for_dcos_oss()
            # No error is raised with a successful command.
            pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_auth.py']
            cluster.run_integration_tests(
                pytest_command=pytest_command,
                log_output_live=True,
            )

            # An error is raised with an unsuccessful command.
            with pytest.raises(CalledProcessError) as excinfo:
                pytest_command = ['pytest', 'test_no_such_file.py']
                result = cluster.run_integration_tests(
                    pytest_command=pytest_command,
                    log_output_live=True,
                )
                # This result will not be printed if the test passes, but it
                # may provide useful debugging information.
                print(result)  # pragma: no cover

            # `pytest` results in an exit code of 4 when no tests are
            # collected.
            # See https://docs.pytest.org/en/latest/usage.html.
            assert excinfo.value.returncode == 4

    def test_install_dcos_from_path(
        self,
        aws_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        The Docker backend requires a build artifact in order
        to launch a DC/OS cluster.
        """
        with Cluster(cluster_backend=aws_backend) as cluster:
            with pytest.raises(NotImplementedError) as excinfo:
                cluster.install_dcos_from_path(oss_artifact)

        expected_error = (
            'The AWS backend does not support the installing DC/OS from '
            'a build artifact on the file system. This is due a more '
            'efficient method existing in `install_dcos_from_url`.'
        )

        assert str(excinfo.value) == expected_error

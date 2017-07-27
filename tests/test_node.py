"""
Tests for managing DC/OS cluster nodes.
"""

import logging
from pathlib import Path
from subprocess import CalledProcessError

import pytest
from pytest_capturelog import CaptureLogFuncArg

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    def test_run(
        self,
        caplog: CaptureLogFuncArg,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        It is possible to run commands as a given user and see their output.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
            generate_config_path=oss_artifact,
        ) as cluster:
            (master, ) = cluster.masters
            result = master.run(args=['echo', '$USER'], user='root')
            assert result.returncode == 0
            assert result.stdout.strip() == b'root'
            assert result.stderr == b''

            # The user is configurable.
            # Create a user.
            result = master.run(args=['adduser', 'testuser'], user='root')
            assert result.returncode == 0
            # Prepare the user account for public key SSH access from the test
            result = master.run(
                args=['cp', '-a', '/root/.ssh', '/home/adduser/.ssh'],
                user='root'
            )
            assert result.returncode == 0
            result = master.run(
                args=['chown', '-R', 'adduser', '/home/adduser/.ssh'],
                user='root'
            )
            assert result.returncode == 0
            # Confirm that commands can be run as the new user.
            result = master.run(args=['echo', '$USER'], user='testuser')
            assert result.returncode == 0
            assert result.stdout.strip() == b'testuser'
            assert result.stderr == b''

            # Commands which return a non-0 code raise a
            # ``CalledProcessError``.
            with pytest.raises(CalledProcessError) as excinfo:
                master.run(args=['unset_command'], user='root')

            exception = excinfo.value
            assert exception.returncode == 127
            assert exception.stdout == b''
            assert b'command not found' in exception.stderr
            for record in caplog.records():
                # The error which caused this exception is not in the debug
                # log output.
                if record.levelno == logging.DEBUG:
                    assert 'unset_command' not in record.getMessage()

            # With `log_output_live`, output is logged and stderr is merged
            # into stdout.
            with pytest.raises(CalledProcessError) as excinfo:
                master.run(
                    args=['unset_command'], user='root', log_output_live=True
                )

            exception = excinfo.value
            assert exception.stderr == b''
            assert b'command not found' in exception.stdout
            expected_error_substring = 'unset_command'
            found_expected_error = False
            for record in caplog.records():
                if expected_error_substring in record.getMessage():
                    if record.levelno == logging.DEBUG:
                        found_expected_error = True
            assert found_expected_error

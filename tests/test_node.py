"""
Tests for managing DC/OS cluster nodes.
"""

import logging
from pathlib import Path
from subprocess import CalledProcessError

import pytest
from pytest_catchlog import CompatLogCaptureFixture

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    def test_run_as_root(
        self,
        caplog: CompatLogCaptureFixture,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        It is possible to run commands as root and see their output.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
            generate_config_path=oss_artifact,
        ) as cluster:
            (master, ) = cluster.masters
            result = master.run_as_root(args=['echo', '$USER'])
            assert result.returncode == 0
            assert result.stdout.strip() == b'root'
            assert result.stderr == b''

            # Commands which return a non-0 code raise a
            # ``CalledProcessError``.
            with pytest.raises(CalledProcessError) as excinfo:
                master.run_as_root(args=['unset_command'])

            exception = excinfo.value
            assert exception.returncode == 127
            assert exception.stdout == b''
            assert b'command not found' in exception.stderr
            for record in caplog.records:
                # The error which caused this exception is not in the debug
                # log output.
                if record.levelno == logging.DEBUG:
                    assert 'unset_command' not in record.getMessage()

            # With `log_output_live`, output is logged and stderr is merged
            # into stdout.
            with pytest.raises(CalledProcessError) as excinfo:
                master.run_as_root(
                    args=['unset_command'], log_output_live=True
                )

            exception = excinfo.value
            assert exception.stderr == b''
            assert b'command not found' in exception.stdout
            expected_error_substring = 'unset_command'
            found_expected_error = False
            for record in caplog.records:
                if expected_error_substring in record.getMessage():
                    if record.levelno == logging.DEBUG:
                        found_expected_error = True
            assert found_expected_error

    # An arbitrary time slice that is longer than it takes to spin up a cluster
    # but avoids bash infinite loops.
    @pytest.mark.timeout(60 * 15)
    def test_popen_as_root(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        It is possible to run commands as root asynchronously.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
            generate_config_path=oss_artifact,
        ) as cluster:
            (master, ) = cluster.masters
            popen_1 = master.popen_as_root(
                args=[
                    '(mkfifo', '/tmp/pipe', '|', 'true)'
                    '&&', '(cat', '/tmp/pipe)'
                ]
            )

            popen_2 = master.popen_as_root(
                args=[
                    '(mkfifo', '/tmp/pipe', '|', 'true)'
                    '&&', '(echo', 'foo', '>', '/tmp/pipe)'
                ]
            )

            stdout, _ = popen_1.communicate()
            return_code_1 = popen_1.poll()

            # Needed to cleanly terminate second subprocess
            popen_2.communicate()
            return_code_2 = popen_2.poll()

            assert stdout == b'foo\n'
            assert return_code_1 == 0
            assert return_code_2 == 0

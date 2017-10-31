"""
Tests for managing DC/OS cluster nodes.
"""

import logging
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Iterator

import pytest
from pytest_catchlog import CompatLogCaptureFixture

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    @pytest.fixture(scope='module')
    def dcos_cluster(
        self,
        oss_artifact: Path,
        cluster_backend: ClusterBackend,
    ) -> Iterator[Cluster]:
        """
        Return a `Cluster`.

        This is module scoped as we do not intend to modify the cluster.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            generate_config_path=oss_artifact,
            masters=1,
            agents=0,
            public_agents=0,
            log_output_live=True,
        ) as cluster:
            yield cluster

    def test_run(
        self,
        dcos_cluster: Cluster,
        caplog: CompatLogCaptureFixture,
    ) -> None:
        """
        It is possible to run commands as the given user and see their output.
        """
        (master, ) = dcos_cluster.masters
        echo_result = master.run(args=['echo', '$USER'], user='root')
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'root'
        assert echo_result.stderr == b''

        new_user_name = str(uuid.uuid4())
        home_path = Path('/home') / new_user_name
        ssh_path = home_path / '.ssh'

        # Create a new user which can be we can SSH into.
        commands = [
            ['adduser', new_user_name],
            ['mkdir', '-p', str(home_path)],
            ['cp', '-a', '/root/.ssh', str(ssh_path)],
            ['chown', '-R', new_user_name,
             str(ssh_path)],
        ]

        for command in commands:
            result = master.run_as_root(args=command)
            assert result.returncode == 0

        new_user_echo = master.run(args=['echo', '$USER'], user=new_user_name)
        assert new_user_echo.returncode == 0
        assert new_user_echo.stdout.strip().decode() == new_user_name
        assert new_user_echo.stderr == b''

        # Commands which return a non-0 code raise a
        # ``CalledProcessError``.
        with pytest.raises(CalledProcessError) as excinfo:
            master.run(args=['unset_command'], user='root')

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
            master.run(
                args=['unset_command'],
                user='root',
                log_output_live=True,
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

    def test_run_as_root(
        self,
        caplog: CompatLogCaptureFixture,
        dcos_cluster: Cluster,
    ) -> None:
        """
        It is possible to run commands as root and see their output.
        """
        (master, ) = dcos_cluster.masters
        echo_result = master.run_as_root(args=['echo', '$USER'])
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'root'
        assert echo_result.stderr == b''

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
            master.run_as_root(args=['unset_command'], log_output_live=True)

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

    # We time out after an arbitrary amount of time to avoid infinite loops.
    @pytest.mark.timeout(60 * 15)
    def test_popen(self, dcos_cluster: Cluster) -> None:
        """
        It is possible to run commands asynchronously.
        """
        (master, ) = dcos_cluster.masters

        popen_1 = master.popen(
            args=[
                '(mkfifo /tmp/pipe | true)',
                '&&',
                '(cat /tmp/pipe)',
            ],
            user='root',
        )

        popen_2 = master.popen(
            args=[
                '(mkfifo /tmp/pipe | true)',
                '&&',
                '(echo foo > /tmp/pipe)',
            ],
            user='root',
        )

        stdout, _ = popen_1.communicate()
        return_code_1 = popen_1.poll()

        # Needed to cleanly terminate second subprocess.
        popen_2.communicate()
        return_code_2 = popen_2.poll()

        assert stdout == b'foo\n'
        assert return_code_1 == 0
        assert return_code_2 == 0

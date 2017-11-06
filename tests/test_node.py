"""
Tests for managing DC/OS cluster nodes.
"""

import logging
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Iterator

import pytest
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error
from pytest_catchlog import CompatLogCaptureFixture

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster

# We ignore this error because it conflicts with `pytest` standard usage.
# pylint: disable=redefined-outer-name


@pytest.fixture(scope='module')
def dcos_cluster(
    oss_artifact: str,
    cluster_backend: ClusterBackend,
) -> Iterator[Cluster]:
    """
    Return a `Cluster`.

    This is module scoped as we do not intend to modify the cluster in ways
    that make tests interfere with one another.
    """
    with Cluster(
        cluster_backend=cluster_backend,
        generate_config_url=oss_artifact,
        masters=1,
        agents=0,
        public_agents=0,
        log_output_live=True,
    ) as cluster:
        yield cluster


def _create_user(cluster: Cluster, username: str) -> None:
    """
    Create a user which one can SSH into.

    Args:
        cluster: The cluster to create a user on.
        username: The name of the user to create.
    """
    (master, ) = cluster.masters
    home_path = Path('/home') / username
    ssh_path = home_path / '.ssh'

    commands = [
        ['adduser', username],
        ['mkdir', '-p', str(home_path)],
        ['cp', '-a', '/root/.ssh', str(ssh_path)],
        ['chown', '-R', username, str(ssh_path)],
    ]

    for command in commands:
        result = master.run_as_root(args=command)
        assert result.returncode == 0


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    def test_run(
        self,
        caplog: CompatLogCaptureFixture,
        dcos_cluster: Cluster,
    ) -> None:
        """
        It is possible to run commands as the given user and see their output.
        """
        (master, ) = dcos_cluster.masters
        echo_result = master.run(args=['echo', '$USER'], user='root')
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'root'
        assert echo_result.stderr == b''

        username = uuid.uuid4().hex
        _create_user(cluster=dcos_cluster, username=username)

        new_user_echo = master.run(args=['echo', '$USER'], user=username)
        assert new_user_echo.returncode == 0
        assert new_user_echo.stdout.strip().decode() == username
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

    # An arbitrary time limit to avoid infinite wait times.
    @pytest.mark.timeout(60)
    def test_popen(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        It is possible to run commands as the given user asynchronously.
        """
        (master, ) = dcos_cluster.masters
        username = uuid.uuid4().hex
        _create_user(cluster=dcos_cluster, username=username)

        popen_1 = master.popen(
            args=['(mkfifo /tmp/pipe | true)', '&&', '(cat /tmp/pipe)'],
            user=username,
        )

        popen_2 = master.popen(
            args=[
                '(mkfifo /tmp/pipe | true)',
                '&&',
                '(echo $USER > /tmp/pipe)',
            ],
            user=username,
        )

        stdout, _ = popen_1.communicate()
        return_code_1 = popen_1.poll()

        # Needed to cleanly terminate second subprocess
        popen_2.communicate()
        return_code_2 = popen_2.poll()

        assert stdout.strip().decode() == username
        assert return_code_1 == 0
        assert return_code_2 == 0

    def test_send_file(
        self,
        dcos_cluster: Cluster,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a file to a cluster node.
        """
        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_destination_path = Path('/etc/new_dir/on_master_node.txt')
        (master, ) = dcos_cluster.masters
        master.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path)]
        result = master.run_as_root(args=args)
        assert result.stdout.decode() == content

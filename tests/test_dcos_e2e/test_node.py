"""
Tests for managing DC/OS cluster nodes.
"""

import logging
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import Iterator

import pytest
from _pytest.logging import LogCaptureFixture
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster

# We ignore this error because it conflicts with `pytest` standard usage.
# pylint: disable=redefined-outer-name


@pytest.fixture(scope='module')
def dcos_cluster(
    oss_artifact: Path,
    cluster_backend: ClusterBackend,
) -> Iterator[Cluster]:
    """
    Return a `Cluster`.

    This is module scoped as we do not intend to modify the cluster in ways
    that make tests interfere with one another.
    """
    with Cluster(
        cluster_backend=cluster_backend,
        masters=1,
        agents=0,
        public_agents=0,
    ) as cluster:
        cluster.install_dcos_from_path(oss_artifact, log_output_live=True)
        yield cluster


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    def test_run_literal(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        When shell=False, preserve arguments as literal values.
        """
        (master, ) = dcos_cluster.masters

        echo_result = master.run(
            args=['echo', 'Hello, ', '&&', 'echo', 'World!']
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'Hello,  && echo World!'
        assert echo_result.stderr == b''

    def test_run_shell(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        When shell=True, interpret spaces and special characters.
        """
        (master, ) = dcos_cluster.masters

        echo_result = master.run(
            args=['echo', 'Hello, ', '&&', 'echo', 'World!'],
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'Hello,\nWorld!'
        assert echo_result.stderr == b''

    def test_run_remote_env(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        Remote environment variables are available.
        """
        (master, ) = dcos_cluster.masters

        echo_result = master.run(args=['echo', '$USER'], shell=True)
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'root'
        assert echo_result.stderr == b''

    def test_run_custom_user(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        Commands can be run as a custom user.
        """
        (master, ) = dcos_cluster.masters

        testuser = str(uuid.uuid4().hex)
        master.run(args=['useradd', testuser])
        master.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        echo_result = master.run(
            args=['echo', '$USER'],
            user=testuser,
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip().decode() == testuser
        assert echo_result.stderr == b''

        master.run(args=['userdel', '-r', testuser])

    def test_run_pass_env(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        Environment variables can be passed to the remote execution
        """
        (master, ) = dcos_cluster.masters

        echo_result = master.run(
            args=['echo', '$MYVAR'],
            env={'MYVAR': 'hello, world'},
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'hello, world'
        assert echo_result.stderr == b''

    def test_run_error(
        self,
        caplog: LogCaptureFixture,
        dcos_cluster: Cluster,
    ) -> None:
        """
        Commands which return a non-0 code raise a ``CalledProcessError``.
        """
        (master, ) = dcos_cluster.masters

        with pytest.raises(CalledProcessError) as excinfo:
            master.run(args=['unset_command'])

        exception = excinfo.value
        assert exception.returncode == 127
        assert exception.stdout == b''
        assert b'command not found' in exception.stderr
        # The error which caused this exception is not in the debug log output.
        error_message = 'unset_command'
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG, caplog.records
            )
        )
        matching_messages = set(
            filter(
                lambda record: error_message in record.getMessage(),
                caplog.records
            )
        )
        assert not bool(len(debug_messages & matching_messages))

    def test_run_error_shell(
        self,
        caplog: LogCaptureFixture,
        dcos_cluster: Cluster,
    ) -> None:
        """
        Commands which return a non-0 code raise a ``CalledProcessError``.
        """
        (master, ) = dcos_cluster.masters

        with pytest.raises(CalledProcessError) as excinfo:
            master.run(args=['unset_command'], shell=True)

        exception = excinfo.value
        assert exception.returncode == 127
        assert exception.stdout == b''
        assert b'command not found' in exception.stderr
        error_message = 'unset_command'
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG, caplog.records
            )
        )
        matching_messages = set(
            filter(
                lambda record: error_message in record.getMessage(),
                caplog.records
            )
        )
        assert not bool(len(debug_messages & matching_messages))

    def test_run_log_output_live(
        self,
        caplog: LogCaptureFixture,
        dcos_cluster: Cluster,
    ) -> None:
        """
        With `log_output_live`, stdout and stderr are merged and logged.
        """
        (master, ) = dcos_cluster.masters

        # With `log_output_live`, output is logged and stderr is merged
        # into stdout.
        with pytest.raises(CalledProcessError) as excinfo:
            master.run(
                args=['unset_command'],
                log_output_live=True,
            )

        exception = excinfo.value
        assert exception.stderr == b''
        assert b'command not found' in exception.stdout
        error_message = 'unset_command'
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG, caplog.records
            )
        )
        matching_messages = set(
            filter(
                lambda record: error_message in record.getMessage(),
                caplog.records
            )
        )
        assert bool(len(debug_messages & matching_messages))

    def test_log_output_live_and_tty(self, dcos_cluster: Cluster) -> None:
        """
        A ``ValueError`` is raised if ``tty`` is ``True`` and
    ``log_output_live`` is ``True``.
        """
        (master, ) = dcos_cluster.masters

        with pytest.raises(ValueError) as excinfo:
            master.run(
                args=['echo', '1'],
                log_output_live=True,
                tty=True,
            )

        expected_message = (
            '`log_output_live` cannot be `True` if `pipe_output` is `False`.'
        )
        assert str(excinfo.value) == expected_message

    # An arbitrary time limit to avoid infinite wait times.
    @pytest.mark.timeout(60)
    def test_popen(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        It is possible to run commands as the default user asynchronously.
        """
        (master, ) = dcos_cluster.masters

        popen_1 = master.popen(
            args=['(mkfifo /tmp/pipe | true)', '&&', '(cat /tmp/pipe)'],
            shell=True,
        )

        popen_2 = master.popen(
            args=[
                '(mkfifo /tmp/pipe | true)',
                '&&',
                '(echo $USER > /tmp/pipe)',
            ],
            shell=True,
        )

        stdout, _ = popen_1.communicate()
        return_code_1 = popen_1.poll()

        # Needed to cleanly terminate second subprocess
        popen_2.communicate()
        return_code_2 = popen_2.poll()

        assert stdout.strip().decode() == master.default_ssh_user
        assert return_code_1 == 0
        assert return_code_2 == 0

    # An arbitrary time limit to avoid infinite wait times.
    @pytest.mark.timeout(60)
    def test_popen_custom_user(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        It is possible to run commands as a custom user asynchronously.
        """
        (master, ) = dcos_cluster.masters

        testuser = str(uuid.uuid4().hex)
        master.run(args=['useradd', testuser])
        master.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        popen_1 = master.popen(
            args=['(mkfifo /tmp/pipe | true)', '&&', '(cat /tmp/pipe)'],
            user=testuser,
            shell=True,
        )

        popen_2 = master.popen(
            args=[
                '(mkfifo /tmp/pipe | true)',
                '&&',
                '(echo $USER > /tmp/pipe)',
            ],
            user=testuser,
            shell=True,
        )

        stdout, _ = popen_1.communicate()
        return_code_1 = popen_1.poll()

        # Needed to cleanly terminate second subprocess
        popen_2.communicate()
        return_code_2 = popen_2.poll()

        assert stdout.strip().decode() == testuser
        assert return_code_1 == 0
        assert return_code_2 == 0

        master.run(args=['userdel', '-r', testuser])

    def test_send_file(
        self,
        dcos_cluster: Cluster,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a file to a cluster node as the default user.
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
        result = master.run(args=args)
        assert result.stdout.decode() == content

    def test_send_file_custom_user(
        self,
        dcos_cluster: Cluster,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a file to a cluster node as a custom user.
        """
        (master, ) = dcos_cluster.masters

        testuser = str(uuid.uuid4().hex)
        master.run(args=['useradd', testuser])
        master.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_destination_path = Path(
            '/home/{}/on_master_node.txt'.format(testuser)
        )
        (master, ) = dcos_cluster.masters
        master.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
            user=testuser,
        )
        args = ['cat', str(master_destination_path)]
        result = master.run(args=args, user=testuser)
        assert result.stdout.decode() == content

        # Implicitly asserts SSH connection closed by ``send_file``.
        master.run(args=['userdel', '-r', testuser])

    def test_string_representation(
        self,
        dcos_cluster: Cluster,
    ) -> None:
        """
        The string representation has the expected format.
        """
        (master, ) = dcos_cluster.masters
        string = 'Node(public_ip={public_ip}, private_ip={private_ip})'.format(
            public_ip=master.public_ip_address,
            private_ip=master.private_ip_address,
        )
        assert string == str(master)

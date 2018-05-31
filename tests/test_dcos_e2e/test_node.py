"""
Tests for managing DC/OS cluster nodes.
"""

import logging
import uuid
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired
from typing import Iterator

import pytest
from _pytest.logging import LogCaptureFixture
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node

# We ignore this error because it conflicts with `pytest` standard usage.
# pylint: disable=redefined-outer-name


@pytest.fixture(scope='module')
def dcos_node(
    oss_artifact: Path,
    cluster_backend: ClusterBackend,
) -> Iterator[Node]:
    """
    Return a ``Node``.

    This is module scoped as we do not intend to modify the cluster in ways
    that make tests interfere with one another.
    """
    with Cluster(
        cluster_backend=cluster_backend,
        masters=1,
        agents=0,
        public_agents=0,
    ) as cluster:
        (master, ) = cluster.masters
        yield master


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    def test_run_literal(
        self,
        dcos_node: Node,
    ) -> None:
        """
        When shell=False, preserve arguments as literal values.
        """
        echo_result = dcos_node.run(
            args=['echo', 'Hello, ', '&&', 'echo', 'World!'],
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'Hello,  && echo World!'
        assert echo_result.stderr == b''

    def test_run_shell(
        self,
        dcos_node: Node,
    ) -> None:
        """
        When shell=True, interpret spaces and special characters.
        """
        echo_result = dcos_node.run(
            args=['echo', 'Hello, ', '&&', 'echo', 'World!'],
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'Hello,\nWorld!'
        assert echo_result.stderr == b''

    def test_run_remote_env(
        self,
        dcos_node: Node,
    ) -> None:
        """
        Remote environment variables are available.
        """
        echo_result = dcos_node.run(args=['echo', '$USER'], shell=True)
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'root'
        assert echo_result.stderr == b''

    def test_run_custom_user(
        self,
        dcos_node: Node,
    ) -> None:
        """
        Commands can be run as a custom user.
        """
        testuser = str(uuid.uuid4().hex)
        dcos_node.run(args=['useradd', testuser])
        dcos_node.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        echo_result = dcos_node.run(
            args=['echo', '$USER'],
            user=testuser,
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip().decode() == testuser
        assert echo_result.stderr == b''

        dcos_node.run(args=['userdel', '-r', testuser])

    def test_run_pass_env(
        self,
        dcos_node: Node,
    ) -> None:
        """
        Environment variables can be passed to the remote execution
        """
        echo_result = dcos_node.run(
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
        dcos_node: Node,
    ) -> None:
        """
        Commands which return a non-0 code raise a ``CalledProcessError``.
        """
        with pytest.raises(CalledProcessError) as excinfo:
            dcos_node.run(args=['unset_command'])

        exception = excinfo.value
        assert exception.returncode == 127
        assert exception.stdout == b''
        assert b'command not found' in exception.stderr
        # The error which caused this exception is not in the debug log output.
        error_message = 'unset_command'
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG,
                caplog.records,
            ),
        )
        matching_messages = set(
            filter(
                lambda record: error_message in record.getMessage(),
                caplog.records,
            ),
        )
        assert not bool(len(debug_messages & matching_messages))

    def test_run_error_shell(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
    ) -> None:
        """
        Commands which return a non-0 code raise a ``CalledProcessError``.
        """
        with pytest.raises(CalledProcessError) as excinfo:
            dcos_node.run(args=['unset_command'], shell=True)

        exception = excinfo.value
        assert exception.returncode == 127
        assert exception.stdout == b''
        assert b'command not found' in exception.stderr
        error_message = 'unset_command'
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG,
                caplog.records,
            ),
        )
        matching_messages = set(
            filter(
                lambda record: error_message in record.getMessage(),
                caplog.records,
            ),
        )
        assert not bool(len(debug_messages & matching_messages))

    def test_run_log_output_live(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
    ) -> None:
        """
        With `log_output_live`, stdout and stderr are merged and logged.
        """
        # With `log_output_live`, output is logged and stderr is merged
        # into stdout.
        with pytest.raises(CalledProcessError) as excinfo:
            dcos_node.run(
                args=['unset_command'],
                log_output_live=True,
            )

        exception = excinfo.value
        assert exception.stderr == b''
        assert b'command not found' in exception.stdout
        error_message = 'unset_command'
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG,
                caplog.records,
            ),
        )
        matching_messages = set(
            filter(
                lambda record: error_message in record.getMessage(),
                caplog.records,
            ),
        )
        assert bool(len(debug_messages & matching_messages))

    def test_log_output_live_and_tty(self, dcos_node: Node) -> None:
        """
        A ``ValueError`` is raised if ``tty`` is ``True`` and
    ``log_output_live`` is ``True``.
        """
        with pytest.raises(ValueError) as excinfo:
            dcos_node.run(
                args=['echo', '1'],
                log_output_live=True,
                tty=True,
            )

        expected_message = (
            '`log_output_live` cannot be `True` if `pipe_output` is `False`.'
        )
        assert str(excinfo.value) == expected_message

    def test_popen(
        self,
        dcos_node: Node,
    ) -> None:
        """
        It is possible to run commands as the default user asynchronously.
        """
        proc_1 = dcos_node.popen(
            args=['(mkfifo /tmp/pipe | true)', '&&', '(cat /tmp/pipe)'],
            shell=True,
        )

        proc_2 = dcos_node.popen(
            args=[
                '(mkfifo /tmp/pipe | true)',
                '&&',
                '(echo $USER > /tmp/pipe)',
            ],
            shell=True,
        )

        try:
            # An arbitrary timeout to avoid infinite wait times.
            stdout, _ = proc_1.communicate(timeout=15)
        except TimeoutExpired:  # pragma: no cover
            proc_1.kill()
            stdout, _ = proc_1.communicate()

        return_code_1 = proc_1.poll()

        # Needed to cleanly terminate second subprocess
        try:
            # An arbitrary timeout to avoid infinite wait times.
            proc_2.communicate(timeout=15)
        except TimeoutExpired:  # pragma: no cover
            proc_2.kill()
            proc_2.communicate()
            raise

        return_code_2 = proc_2.poll()

        assert stdout.strip().decode() == dcos_node.default_user
        assert return_code_1 == 0
        assert return_code_2 == 0

        dcos_node.run(['rm', '-f', '/tmp/pipe'])

    def test_popen_custom_user(
        self,
        dcos_node: Node,
    ) -> None:
        """
        It is possible to run commands as a custom user asynchronously.
        """
        testuser = str(uuid.uuid4().hex)
        dcos_node.run(args=['useradd', testuser])
        dcos_node.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        proc_1 = dcos_node.popen(
            args=['(mkfifo /tmp/pipe | true)', '&&', '(cat /tmp/pipe)'],
            user=testuser,
            shell=True,
        )

        proc_2 = dcos_node.popen(
            args=[
                '(mkfifo /tmp/pipe | true)',
                '&&',
                '(echo $USER > /tmp/pipe)',
            ],
            user=testuser,
            shell=True,
        )

        try:
            # An arbitrary timeout to avoid infinite wait times.
            stdout, _ = proc_1.communicate(timeout=15)
        except TimeoutExpired:  # pragma: no cover
            proc_1.kill()
            stdout, _ = proc_1.communicate()

        return_code_1 = proc_1.poll()

        # Needed to cleanly terminate second subprocess
        try:
            # An arbitrary timeout to avoid infinite wait times.
            proc_2.communicate(timeout=15)
        except TimeoutExpired:  # pragma: no cover
            proc_2.kill()
            proc_2.communicate()
            raise

        return_code_2 = proc_2.poll()

        assert stdout.strip().decode() == testuser
        assert return_code_1 == 0
        assert return_code_2 == 0

        dcos_node.run(['rm', '-f', '/tmp/pipe'], user=testuser)
        dcos_node.run(args=['userdel', '-r', testuser])

    def test_send_file(
        self,
        dcos_node: Node,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a file to a cluster node as the default user.
        """
        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_destination_path = Path('/etc/new_dir/on_master_node.txt')
        dcos_node.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == content

    def test_send_file_custom_user(
        self,
        dcos_node: Node,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a file to a cluster node as a custom user.
        """
        testuser = str(uuid.uuid4().hex)
        dcos_node.run(args=['useradd', testuser])
        dcos_node.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_destination = '/home/{user}/on_master_node.txt'.format(
            user=testuser,
        )
        master_destination_path = Path(master_destination)

        dcos_node.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
            user=testuser,
        )
        args = ['cat', str(master_destination_path)]
        result = dcos_node.run(args=args, user=testuser)
        assert result.stdout.decode() == content

        # Implicitly asserts SSH connection closed by ``send_file``.
        dcos_node.run(args=['userdel', '-r', testuser])

    def test_string_representation(
        self,
        dcos_node: Node,
    ) -> None:
        """
        The string representation has the expected format.
        """
        string = 'Node(public_ip={public_ip}, private_ip={private_ip})'.format(
            public_ip=dcos_node.public_ip_address,
            private_ip=dcos_node.private_ip_address,
        )
        assert string == str(dcos_node)

"""
Tests for managing DC/OS cluster nodes.
"""

import logging
import uuid
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired
from typing import Iterator

import pytest
from _pytest.fixtures import SubRequest
from _pytest.logging import LogCaptureFixture
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Transport

# We ignore this error because it conflicts with `pytest` standard usage.
# pylint: disable=redefined-outer-name


# @pytest.fixture(scope='module', params=list(Transport))
@pytest.fixture(scope='module', params=[Transport.DOCKER_EXEC])
def dcos_node(request: SubRequest) -> Iterator[Node]:
    """
    Return a ``Node``.

    This is module scoped as we do not intend to modify the cluster in ways
    that make tests interfere with one another.
    """
    # We use the Docker backend because it is currently the only one which
    # supports all transports.
    cluster_backend = Docker(transport=request.param)
    with Cluster(
        cluster_backend=cluster_backend,
        masters=1,
        agents=0,
        public_agents=0,
    ) as cluster:
        (master, ) = cluster.masters
        yield master


class TestStringRepresentation:
    """
    Tests for the string representation of a ``Node``.
    """

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


class TestSendFile:
    """
    Tests for ``Node.send_file``.
    """

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


class TestPopen:
    """
    Tests for ``Node.popen``.
    """

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
                '(echo $HOME > /tmp/pipe)',
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

        assert stdout.strip().decode() == '/' + dcos_node.default_user
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
                '(echo $HOME > /tmp/pipe)',
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

        assert stdout.strip().decode() == '/home/' + testuser
        assert return_code_1 == 0
        assert return_code_2 == 0

        dcos_node.run(['rm', '-f', '/tmp/pipe'], user=testuser)
        dcos_node.run(args=['userdel', '-r', testuser])


class TestRun:
    """
    Tests for ``Node.run``.
    """

    def test_literal(
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

    def test_shell(
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
        assert echo_result.stderr.strip() == b''

    def test_stderr(self, dcos_node: Node) -> None:
        """
        ``stderr`` is send to the result's ``stderr`` property.
        """
        echo_result = dcos_node.run(args=['echo', '1', '1>&2'], shell=True)
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b''
        assert echo_result.stderr.strip() == b'1'

    def test_remote_env(
        self,
        dcos_node: Node,
    ) -> None:
        """
        Remote environment variables are available.
        """
        echo_result = dcos_node.run(args=['echo', '$HOME'], shell=True)
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip() == b'/root'
        assert echo_result.stderr == b''

    def test_custom_user(
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
            args=['echo', '$HOME'],
            user=testuser,
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip().decode() == '/home/' + testuser
        assert echo_result.stderr == b''

        dcos_node.run(args=['userdel', '-r', testuser])

    def test_pass_env(
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

    @pytest.mark.parametrize('shell', [True, False])
    @pytest.mark.parametrize('log_output_live', [True, False])
    def test_error(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
        shell: bool,
        log_output_live: bool,
    ) -> None:
        """
        Commands which return a non-0 code raise a ``CalledProcessError``.
        """
        with pytest.raises(CalledProcessError) as excinfo:
            dcos_node.run(
                args=['rm', 'does_not_exist'],
                shell=shell,
                log_output_live=log_output_live,
            )

        exception = excinfo.value
        assert exception.returncode == 1
        error_message = (
            'rm: cannot remove ‘does_not_exist’: No such file or directory'
        )
        if log_output_live:
            assert exception.stderr.strip() == b''
            assert exception.stdout.decode().strip() == error_message
        else:
            assert exception.stdout.strip() == b''
            assert exception.stderr.decode().strip() == error_message
        # The stderr output is not in the debug log output.
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG,
                caplog.records,
            ),
        )
        matching_messages = set(
            filter(
                lambda record: 'No such file' in record.getMessage(),
                caplog.records,
            ),
        )
        assert bool(len(debug_messages & matching_messages)) is log_output_live

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

        expected_message = '`log_output_live` and `tty` cannot both be `True`.'
        assert str(excinfo.value) == expected_message

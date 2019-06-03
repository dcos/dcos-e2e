"""
Tests for managing DC/OS cluster nodes.

See ``test_node_install.py`` for more, related tests.
"""

import logging
import os
import subprocess
import sys
import textwrap
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from subprocess import CalledProcessError, TimeoutExpired
from typing import Iterator

import pytest
from _pytest.capture import CaptureFixture
from _pytest.fixtures import SubRequest
from _pytest.logging import LogCaptureFixture

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.exceptions import DCOSNotInstalledError
from dcos_e2e.node import Node, Output, Transport

# We ignore this error because it conflicts with `pytest` standard usage.
# pylint: disable=redefined-outer-name

# Set TEST_ONE_TRANSPORT=1 to run these tests with just one transport.
# This can be useful during development for transport-agnostic testing.
_TRANSPORTS = [
    Transport.DOCKER_EXEC,
] if os.getenv('TEST_ONE_TRANSPORT') == '1' else list(Transport)


@pytest.fixture(scope='module', params=_TRANSPORTS)
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


class TestEquality:
    """
    Tests for Node.__eq__
    """

    def test_eq(self, tmp_path: Path) -> None:
        """
        Two nodes are equal iff their IP addresses are equal.
        """

        content = str(uuid.uuid4())
        node_ssh_key_filename = 'foo.key'
        node_ssh_key = tmp_path / node_ssh_key_filename
        node_ssh_key.write_text(content)
        other_ssh_key_filename = 'bar.key'
        other_ssh_key = tmp_path / other_ssh_key_filename
        other_ssh_key.write_text(content)

        node_public_ip_address = IPv4Address('172.0.0.1')
        node_private_ip_address = IPv4Address('172.0.0.3')
        other_ip_address = IPv4Address('172.0.0.4')
        node_user = 'a'
        other_user = 'b'
        node_transport = Transport.DOCKER_EXEC
        other_transport = Transport.SSH
        node = Node(
            public_ip_address=node_public_ip_address,
            private_ip_address=node_private_ip_address,
            ssh_key_path=node_ssh_key,
            default_user=node_user,
            default_transport=node_transport,
        )
        for transport in (node_transport, other_transport):
            for public_ip_address in (
                node_public_ip_address,
                other_ip_address,
            ):
                for private_ip_address in (
                    node_private_ip_address,
                    other_ip_address,
                ):
                    for ssh_key_path in (node_ssh_key, other_ssh_key):
                        for user in (node_user, other_user):
                            other_node = Node(
                                public_ip_address=public_ip_address,
                                private_ip_address=private_ip_address,
                                ssh_key_path=ssh_key_path,
                                default_user=user,
                                default_transport=transport,
                            )

                            should_match = bool(
                                (public_ip_address, private_ip_address) == (
                                    node_public_ip_address,
                                    node_private_ip_address,
                                ),
                            )

                            do_match = bool(node == other_node)
                            assert should_match == do_match


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


class TestDownloadFile:
    """
    Tests for ``Node.download_file``.
    """

    def test_file_to_directory(
        self,
        dcos_node: Node,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to download a file from a node to a directory path.
        """
        content = str(uuid.uuid4())
        random = uuid.uuid4().hex
        local_file_name = 'local_file_{random}.txt'.format(random=random)
        remote_file_name = 'remote_file_{random}.txt'.format(random=random)
        remote_file_path = Path('/etc/') / remote_file_name
        local_file = tmp_path / local_file_name
        local_file.write_text(content)
        dcos_node.send_file(
            local_path=local_file,
            remote_path=remote_file_path,
        )
        dcos_node.download_file(
            remote_path=remote_file_path,
            local_path=tmp_path,
        )
        downloaded_file = tmp_path / remote_file_name
        assert downloaded_file.read_text() == content

    def test_file_to_file(
        self,
        dcos_node: Node,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to download a file from a node to a file path.
        """
        content = str(uuid.uuid4())
        random = uuid.uuid4().hex
        local_file_name = 'local_file_{random}.txt'.format(random=random)
        remote_file_name = 'remote_file_{random}.txt'.format(random=random)
        remote_file_path = Path('/etc/') / remote_file_name
        downloaded_file_name = 'downloaded_file_{random}.txt'.format(
            random=random,
        )
        downloaded_file_path = tmp_path / downloaded_file_name
        local_file = tmp_path / local_file_name
        local_file.write_text(content)
        dcos_node.send_file(
            local_path=local_file,
            remote_path=remote_file_path,
        )
        dcos_node.download_file(
            remote_path=remote_file_path,
            local_path=downloaded_file_path,
        )
        assert downloaded_file_path.read_text() == content

    def test_remote_file_does_not_exist(
        self,
        dcos_node: Node,
    ) -> None:
        """
        Downloading a file raises a ``ValueError`` if the remote file path does
        not exist.
        """
        random = uuid.uuid4().hex
        remote_file_path = Path('/etc/') / random
        message = (
            'Failed to download file from remote location "{location}". '
            'File does not exist.'
        ).format(location=remote_file_path)
        with pytest.raises(ValueError) as exc:
            dcos_node.download_file(
                remote_path=remote_file_path,
                local_path=Path('./blub'),
            )
        assert str(exc.value) == message

    def test_local_file_already_exists(
        self,
        dcos_node: Node,
        tmp_path: Path,
    ) -> None:
        """
        Downloading a file raises a ``ValueError`` if the local file path
        already exists.
        """
        content = str(uuid.uuid4())
        random = uuid.uuid4().hex
        local_file_name = 'local_file_{random}.txt'.format(random=random)
        local_file_path = tmp_path / local_file_name
        local_file_path.write_text(content)
        remote_file_name = 'remote_file_{random}.txt'.format(random=random)
        remote_file_path = Path('/etc/') / remote_file_name
        dcos_node.send_file(
            local_path=local_file_path,
            remote_path=remote_file_path,
        )
        message = (
            'Failed to download a file to "{file}". '
            'A file already exists in that location.'
        ).format(file=local_file_path)
        with pytest.raises(ValueError) as exc:
            dcos_node.download_file(
                remote_path=remote_file_path,
                local_path=local_file_path,
            )
        assert str(exc.value) == message


class TestSendFile:
    """
    Tests for ``Node.send_file``.
    """

    def test_send_file(
        self,
        dcos_node: Node,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to send a file to a cluster node as the default user.
        """
        content = str(uuid.uuid4())
        local_file = tmp_path / 'example_file.txt'
        local_file.write_text(content)
        random = uuid.uuid4().hex
        master_destination_dir = '/etc/{random}'.format(random=random)
        master_destination_path = Path(master_destination_dir) / 'file.txt'
        dcos_node.send_file(
            local_path=local_file,
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == content

    def test_send_directory(
        self,
        dcos_node: Node,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to send a directory to a cluster node as the default
        user.
        """
        original_content = str(uuid.uuid4())
        dir_name = 'directory'
        file_name = 'example_file.txt'
        dir_path = tmp_path / dir_name
        dir_path.mkdir()
        local_file_path = dir_path / file_name
        local_file_path.write_text(original_content)

        random = uuid.uuid4().hex
        master_base_dir = '/etc/{random}'.format(random=random)
        master_destination_dir = Path(master_base_dir)

        dcos_node.send_file(
            local_path=local_file_path,
            remote_path=master_destination_dir / dir_name / file_name,
        )

        args = ['cat', str(master_destination_dir / dir_name / file_name)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == original_content

        new_content = str(uuid.uuid4())
        local_file_path.write_text(new_content)

        dcos_node.send_file(
            local_path=dir_path,
            remote_path=master_destination_dir,
        )
        args = ['cat', str(master_destination_dir / dir_name / file_name)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == new_content

    def test_send_file_to_directory(
        self,
        dcos_node: Node,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to send a file to a cluster node to a directory that
        is mounted as tmpfs.
        See ``DockerExecTransport.send_file`` for details.
        """
        content = str(uuid.uuid4())
        file_name = 'example_file.txt'
        local_file = tmp_path / file_name
        local_file.write_text(content)

        master_destination_path = Path(
            '/etc/{random}'.format(random=uuid.uuid4().hex),
        )
        dcos_node.run(args=['mkdir', '--parent', str(master_destination_path)])
        dcos_node.send_file(
            local_path=local_file,
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path / file_name)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == content

    def test_send_file_to_tmp_directory(
        self,
        dcos_node: Node,
        tmp_path: Path,
    ) -> None:
        """
        It is possible to send a file to a cluster node to a directory that
        is mounted as tmpfs.
        See ``DockerExecTransport.send_file`` for details.
        """
        content = str(uuid.uuid4())
        local_file = tmp_path / 'example_file.txt'
        local_file.write_text(content)
        master_destination_path = Path('/tmp/mydir/on_master_node.txt')
        dcos_node.send_file(
            local_path=local_file,
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == content

    def test_custom_user(
        self,
        dcos_node: Node,
        tmp_path: Path,
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

        random = str(uuid.uuid4())
        local_file = tmp_path / 'example_file.txt'
        local_file.write_text(random)
        master_destination_dir = '/home/{testuser}/{random}'.format(
            testuser=testuser,
            random=random,
        )
        master_destination_path = Path(master_destination_dir) / 'file.txt'
        dcos_node.send_file(
            local_path=local_file,
            remote_path=master_destination_path,
            user=testuser,
        )
        args = ['stat', '-c', '"%U"', str(master_destination_path)]
        result = dcos_node.run(args=args, shell=True)
        assert result.stdout.decode().strip() == testuser

        # Implicitly asserts SSH connection closed by ``send_file``.
        dcos_node.run(args=['userdel', '-r', testuser])

    def test_sudo(self, dcos_node: Node, tmp_path: Path) -> None:
        """
        It is possible to use sudo to send a file to a directory which the
        user does not have access to.
        """
        testuser = str(uuid.uuid4().hex)
        dcos_node.run(args=['useradd', testuser])
        dcos_node.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        sudoers_line = '{user} ALL=(ALL) NOPASSWD: ALL'.format(user=testuser)
        dcos_node.run(
            args=['echo "' + sudoers_line + '">> /etc/sudoers'],
            shell=True,
        )

        random = str(uuid.uuid4())
        local_file = tmp_path / 'example_file.txt'
        local_file.write_text(random)
        master_destination_dir = '/etc/{testuser}/{random}'.format(
            testuser=testuser,
            random=random,
        )
        master_destination_path = Path(master_destination_dir) / 'file.txt'
        with pytest.raises(CalledProcessError):
            dcos_node.send_file(
                local_path=local_file,
                remote_path=master_destination_path,
                user=testuser,
            )
        dcos_node.send_file(
            local_path=local_file,
            remote_path=master_destination_path,
            user=testuser,
            sudo=True,
        )

        args = ['stat', '-c', '"%U"', str(master_destination_path)]
        result = dcos_node.run(args=args, shell=True)
        assert result.stdout.decode().strip() == testuser

        # Implicitly asserts SSH connection closed by ``send_file``.
        dcos_node.run(args=['userdel', '-r', testuser])

    def test_send_symlink(self, dcos_node: Node, tmp_path: Path) -> None:
        """
        If sending the path to a symbolic link, the link's target is sent.
        """
        random = str(uuid.uuid4())
        dir_containing_real_file = tmp_path / uuid.uuid4().hex
        dir_containing_real_file.mkdir()
        dir_containing_symlink = tmp_path / uuid.uuid4().hex
        dir_containing_symlink.mkdir()
        local_file = dir_containing_real_file / 'example_file.txt'
        local_file.write_text(random)
        symlink_file_path = dir_containing_symlink / 'symlink.txt'
        symlink_file_path.symlink_to(target=local_file)
        master_destination_dir = '/etc/{random}'.format(random=random)
        master_destination_path = Path(master_destination_dir) / 'file.txt'
        dcos_node.send_file(
            local_path=symlink_file_path,
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == random


class TestPopen:
    """
    Tests for ``Node.popen``.
    """

    def test_literal(
        self,
        dcos_node: Node,
    ) -> None:
        """
        When shell=False, preserve arguments as literal values.
        """
        echo_result = dcos_node.popen(
            args=['echo', 'Hello, ', '&&', 'echo', 'World!'],
        )
        stdout, stderr = echo_result.communicate()
        assert echo_result.returncode == 0
        assert stdout.strip() == b'Hello,  && echo World!'
        assert stderr == b''

    def test_stderr(self, dcos_node: Node) -> None:
        """
        ``stderr`` is send to the result's ``stderr`` property.
        """
        echo_result = dcos_node.popen(args=['echo', '1', '1>&2'], shell=True)
        stdout, stderr = echo_result.communicate()
        assert echo_result.returncode == 0
        assert stdout.strip().decode() == ''
        assert stderr.strip().decode() == '1'

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

        echo_result = dcos_node.popen(
            args=['echo', '$HOME'],
            user=testuser,
            shell=True,
        )
        stdout, stderr = echo_result.communicate()
        assert echo_result.returncode == 0
        assert stdout.strip().decode() == '/home/' + testuser
        assert stderr.strip().decode() == ''

        dcos_node.run(args=['userdel', '-r', testuser])

    def test_shell(
        self,
        dcos_node: Node,
    ) -> None:
        """
        When shell=True, interpret spaces and special characters.
        """
        echo_result = dcos_node.popen(
            args=['echo', 'Hello, ', '&&', 'echo', 'World!'],
            shell=True,
        )
        stdout, stderr = echo_result.communicate()
        assert echo_result.returncode == 0
        assert stdout.strip().decode() == 'Hello,\nWorld!'
        assert stderr.strip().decode() == ''

    def test_pass_env(
        self,
        dcos_node: Node,
    ) -> None:
        """
        Environment variables can be passed to the remote execution
        """
        echo_result = dcos_node.popen(
            args=['echo', '$MYVAR'],
            env={'MYVAR': 'hello, world'},
            shell=True,
        )
        stdout, stderr = echo_result.communicate()
        assert echo_result.returncode == 0
        assert stdout.strip().decode() == 'hello, world'
        assert stderr.strip().decode() == ''

    def test_async(self, dcos_node: Node) -> None:
        """
        It is possible to run commands asynchronously.
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

    def test_sudo(
        self,
        dcos_node: Node,
    ) -> None:
        """
        When sudo is given as ``True``, the given command has sudo prefixed.
        """
        testuser = str(uuid.uuid4().hex)
        dcos_node.run(args=['useradd', testuser])
        dcos_node.run(
            args=['cp', '-R', '$HOME/.ssh', '/home/{}/'.format(testuser)],
            shell=True,
        )

        sudoers_line = '{user} ALL=(ALL) NOPASSWD: ALL'.format(user=testuser)

        echo_result = dcos_node.run(
            args=['echo "' + sudoers_line + '">> /etc/sudoers'],
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip().decode() == ''
        assert echo_result.stderr.strip().decode() == ''

        echo_result = dcos_node.run(
            args=['echo', '$(whoami)'],
            user=testuser,
            shell=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip().decode() == testuser
        assert echo_result.stderr.strip().decode() == ''

        echo_result = dcos_node.run(
            args=['echo', '$(whoami)'],
            user=testuser,
            shell=True,
            sudo=True,
        )
        assert echo_result.returncode == 0
        assert echo_result.stdout.strip().decode() == 'root'
        assert echo_result.stderr.strip().decode() == ''

        dcos_node.run(args=['userdel', '-r', testuser])

    # We skip coverage on this test because CI may not be a TTY.
    # However, we do not skip the whole test so we at least cover more code in
    # the implementation.
    @pytest.mark.parametrize('tty', [True, False])
    def test_tty(
        self,
        dcos_node: Node,
        tty: bool,
    ) -> None:
        """
        If the ``tty`` parameter is set to ``True``, a TTY is created.
        """
        filename = uuid.uuid4().hex
        script = textwrap.dedent(
            """
            if [ -t 1 ]
            then
            echo True
            else
            echo False
            fi
            """,
        ).format(filename=filename)
        echo_result = dcos_node.run(
            args=[script],
            tty=tty,
            shell=True,
        )

        if not sys.stdout.isatty():  # pragma: no cover
            reason = (
                'For this test to be valid, stdout must be a TTY. '
                'Use ``--capture=no / -s`` to run this test.'
            )
            pytest.skip(reason)
        else:  # pragma: no cover
            assert echo_result.returncode == 0
            assert echo_result.stdout.strip().decode() == str(tty)

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
        assert echo_result.stderr.strip().decode() == ''

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
        assert echo_result.stdout.strip().decode() == 'hello, world'
        assert echo_result.stderr.strip().decode() == ''

    def test_error(self, dcos_node: Node) -> None:
        """
        Commands which return a non-0 code raise a ``CalledProcessError``.
        """
        with pytest.raises(CalledProcessError) as excinfo:
            dcos_node.run(args=['rm', 'does_not_exist'])

        exception = excinfo.value
        assert exception.returncode == 1


class TestOutput:
    """
    Tests for the ``output`` parameter of ``Node.run``.
    """

    @pytest.fixture(autouse=True)
    def configure_logging(self, caplog: LogCaptureFixture) -> None:
        """
        Set the ``caplog`` logging level to ``DEBUG`` so it captures any log
        messages produced by ``dcos_e2e`` library.
        """
        caplog.set_level(logging.DEBUG, logger='dcos_e2e')

    def test_default(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
    ) -> None:
        """
        By default, stderr and stdout are captured in the output.

        stderr is logged.
        """
        stdout_message = uuid.uuid4().hex
        stderr_message = uuid.uuid4().hex
        args = ['echo', stdout_message, '&&', '>&2', 'echo', stderr_message]
        result = dcos_node.run(args=args, shell=True)
        assert result.stdout.strip().decode() == stdout_message
        assert result.stderr.strip().decode() == stderr_message

        assert caplog.records == []

    @pytest.mark.parametrize(
        'stdout_message',
        [uuid.uuid4().hex, 'å'],
        ids=['ascii', 'unicode'],
    )
    @pytest.mark.parametrize(
        'stderr_message',
        [uuid.uuid4().hex, 'å'],
        ids=['ascii', 'unicode'],
    )
    def test_capture(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
        stdout_message: str,
        stderr_message: str,
    ) -> None:
        """
        When given ``Output.CAPTURE``, stderr and stdout are captured in the
        output.

        stderr is logged.
        """
        args = ['echo', stdout_message, '&&', '>&2', 'echo', stderr_message]
        result = dcos_node.run(args=args, output=Output.CAPTURE, shell=True)
        assert result.stdout.strip().decode() == stdout_message
        assert result.stderr.strip().decode() == stderr_message

        assert caplog.records == []

    @pytest.mark.parametrize(
        'message',
        [uuid.uuid4().hex, 'å'],
        ids=['ascii', 'unicode'],
    )
    def test_log_and_capture_stdout(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
        message: str,
    ) -> None:
        """
        When using ``Output.LOG_AND_CAPTURE``, stdout is logged and captured.
        """
        args = ['echo', message]
        result = dcos_node.run(
            args=args,
            shell=True,
            output=Output.LOG_AND_CAPTURE,
        )

        expected_command = (
            'Running command `/bin/sh -c echo {message}` on a node `{node}`'
        ).format(
            message=message,
            node=str(dcos_node),
        )

        assert result.stdout.strip().decode() == message

        command_log, first_log = caplog.records
        assert first_log.levelno == logging.DEBUG

        assert command_log.message == expected_command
        assert message == first_log.message

    @pytest.mark.parametrize(
        'message',
        [uuid.uuid4().hex, 'å'],
        ids=['ascii', 'unicode'],
    )
    def test_log_and_capture_stderr(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
        message: str,
    ) -> None:
        """
        When using ``Output.LOG_AND_CAPTURE``, stderr is logged and captured.
        """
        args = ['>&2', 'echo', message]
        result = dcos_node.run(
            args=args,
            shell=True,
            output=Output.LOG_AND_CAPTURE,
        )

        expected_command = (
            'Running command `/bin/sh -c >&2 echo {message}` on a node '
            '`{node}`'
        ).format(
            message=message,
            node=str(dcos_node),
        )

        assert result.stderr.strip().decode() == message

        command_log, first_log = caplog.records
        assert first_log.levelno == logging.WARN

        assert command_log.message == expected_command
        assert message == first_log.message

    def test_not_utf_8_log_and_capture(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
    ) -> None:
        """
        It is possible to see output of commands which output non-utf-8
        bytes using ``output.LOG_AND_CAPTURE``.
        """
        # We expect that this will trigger a UnicodeDecodeError when run on a
        # node, if the result is meant to be decoded with utf-8.
        # It also is not so long that it will kill our terminal.
        args = ['head', '-c', '100', '/bin/cat']
        dcos_node.run(args=args, output=Output.LOG_AND_CAPTURE)
        # We do not test the output, but we at least test its length for now.
        [command_log, log] = caplog.records
        assert len(log.message) >= 100

        expected_command = (
            'Running command `head -c 100 /bin/cat` on a node `{node}`'.format(
                node=str(dcos_node),
            )
        )
        assert command_log.message == expected_command

    def test_not_utf_8_capture(
        self,
        caplog: LogCaptureFixture,
        dcos_node: Node,
    ) -> None:
        """
        It is possible to capture output of commands which output non-utf-8
        bytes using ``output.CAPTURE``.
        """
        # We expect that this will trigger a UnicodeDecodeError when run on a
        # node, if the result is meant to be decoded with utf-8.
        # It also is not so long that it will kill our terminal.
        args = ['head', '-c', '100', '/bin/cat']
        args = ['>&2'] + args
        result = dcos_node.run(args=args, output=Output.CAPTURE, shell=True)
        assert caplog.records == []
        assert len(result.stderr) >= 100

    def test_no_capture(
        self,
        capfd: CaptureFixture,
        dcos_node: Node,
    ) -> None:
        """
        When given ``Output.NO_CAPTURE``, no output is captured.
        """
        stdout_message = uuid.uuid4().hex
        stderr_message = uuid.uuid4().hex
        args = ['echo', stdout_message, '&&', '>&2', 'echo', stderr_message]
        result = dcos_node.run(args=args, shell=True, output=Output.NO_CAPTURE)
        assert result.stdout is None
        assert result.stderr is None

        captured = capfd.readouterr()
        assert captured.out.strip() == stdout_message
        assert captured.err.strip() == stderr_message

    @pytest.mark.parametrize(
        'output',
        [Output.LOG_AND_CAPTURE, Output.CAPTURE],
    )
    def test_errors(self, dcos_node: Node, output: Output) -> None:
        """
        The ``stderr`` of a failed command is available in the raised
        ``subprocess.CalledProcessError``.
        """
        args = ['rm', 'does_not_exist']
        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            dcos_node.run(args=args, shell=True, output=output)
        expected_message = b'No such file or directory'
        assert expected_message in excinfo.value.stderr


class TestDcosBuildInfo:
    """
    Tests for ``Node.dcos_build_info``.

    The tests here assume that DC/OS is not already installed.
    In order to save CI run time, the tests for this method are in
    ``test_legacy.py``.
    This allows us to check that the build information is correct for all
    supported versions of DC/OS.
    """

    def test_not_installed(self, dcos_node: Node) -> None:
        """
        When trying to retrieve the DC/OS version of a cluster which does not
        have DC/OS installed, a ``DCOSNotInstalledError`` is raised.
        """
        with pytest.raises(DCOSNotInstalledError):
            dcos_node.dcos_build_info()

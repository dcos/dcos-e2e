"""
Tests for managing DC/OS cluster nodes.

See ``test_node_install.py`` for more, related tests.
"""

import logging
import textwrap
import uuid
from ipaddress import IPv4Address
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


@pytest.fixture(scope='module', params=list(Transport))
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

    def test_eq(self, tmpdir: local) -> None:
        """
        Two nodes are equal iff their IP addresses are equal.
        """

        content = str(uuid.uuid4())
        key1_filename = 'foo.key'
        key1_file = tmpdir.join(key1_filename)
        key1_file.write(content)
        key2_filename = 'bar.key'
        key2_file = tmpdir.join(key2_filename)
        key2_file.write(content)

        node_public_ip_address = IPv4Address('172.0.0.1')
        node_private_ip_address = IPv4Address('172.0.0.3')
        other_ip_address = IPv4Address('172.0.0.4')
        node_ssh_key_path = Path(str(key1_file))
        other_ssh_key_path = Path(str(key2_file))
        node_user = 'a'
        other_user = 'b'
        node_transport = Transport.DOCKER_EXEC
        other_transport = Transport.SSH
        node = Node(
            public_ip_address=node_public_ip_address,
            private_ip_address=node_private_ip_address,
            ssh_key_path=node_ssh_key_path,
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
                    for ssh_key_path in (
                        node_ssh_key_path,
                        other_ssh_key_path,
                    ):
                        for user in (node_user, other_user):
                            other_node = Node(
                                public_ip_address=public_ip_address,
                                private_ip_address=private_ip_address,
                                ssh_key_path=ssh_key_path,
                                default_user=user,
                                default_transport=transport,
                            )

                            should_match = bool(
                                public_ip_address == node_public_ip_address and
                                private_ip_address == node_private_ip_address,
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
        random = uuid.uuid4().hex
        master_destination_dir = '/etc/{random}'.format(random=random)
        master_destination_path = Path(master_destination_dir) / 'file.txt'
        dcos_node.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == content

    def test_send_directory(
        self,
        dcos_node: Node,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a directory to a cluster node as the default
        user.
        """
        original_content = str(uuid.uuid4())
        dir_name = 'directory'
        file_name = 'example_file.txt'
        dir_path = tmpdir.mkdir(dir_name)
        local_file_path = dir_path.join(file_name)
        local_file_path.write(original_content)

        random = uuid.uuid4().hex
        master_base_dir = '/etc/{random}'.format(random=random)
        master_destination_dir = Path(master_base_dir)

        dcos_node.send_file(
            local_path=Path(str(local_file_path)),
            remote_path=master_destination_dir / dir_name / file_name,
        )

        args = ['cat', str(master_destination_dir / dir_name / file_name)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == original_content

        new_content = str(uuid.uuid4())
        local_file_path.write(new_content)

        dcos_node.send_file(
            local_path=Path(str(dir_path)),
            remote_path=master_destination_dir,
        )
        args = ['cat', str(master_destination_dir / dir_name / file_name)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == new_content

    def test_send_file_to_directory(
        self,
        dcos_node: Node,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a file to a cluster node to a directory that
        is mounted as tmpfs.
        See ``DockerExecTransport.send_file`` for details.
        """
        content = str(uuid.uuid4())
        file_name = 'example_file.txt'
        local_file = tmpdir.join(file_name)
        local_file.write(content)

        master_destination_path = Path(
            '/etc/{random}'.format(random=uuid.uuid4().hex),
        )
        dcos_node.run(args=['mkdir', '--parent', str(master_destination_path)])
        dcos_node.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path / file_name)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == content

    def test_send_file_to_tmp_directory(
        self,
        dcos_node: Node,
        tmpdir: local,
    ) -> None:
        """
        It is possible to send a file to a cluster node to a directory that
        is mounted as tmpfs.
        See ``DockerExecTransport.send_file`` for details.
        """
        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_destination_path = Path('/tmp/mydir/on_master_node.txt')
        dcos_node.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
        )
        args = ['cat', str(master_destination_path)]
        result = dcos_node.run(args=args)
        assert result.stdout.decode() == content

    def test_custom_user(
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

        random = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(random)
        master_destination_dir = '/home/{testuser}/{random}'.format(
            testuser=testuser,
            random=random,
        )
        master_destination_path = Path(master_destination_dir) / 'file.txt'
        dcos_node.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
            user=testuser,
        )
        args = ['stat', '-c', '"%U"', str(master_destination_path)]
        result = dcos_node.run(args=args, shell=True)
        assert result.stdout.decode().strip() == testuser

        # Implicitly asserts SSH connection closed by ``send_file``.
        dcos_node.run(args=['userdel', '-r', testuser])

    def test_sudo(
        self,
        dcos_node: Node,
        tmpdir: local,
    ) -> None:
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
        local_file = tmpdir.join('example_file.txt')
        local_file.write(random)
        master_destination_dir = '/etc/{testuser}/{random}'.format(
            testuser=testuser,
            random=random,
        )
        master_destination_path = Path(master_destination_dir) / 'file.txt'
        with pytest.raises(CalledProcessError):
            dcos_node.send_file(
                local_path=Path(str(local_file)),
                remote_path=master_destination_path,
                user=testuser,
            )
        dcos_node.send_file(
            local_path=Path(str(local_file)),
            remote_path=master_destination_path,
            user=testuser,
            sudo=True,
        )

        args = ['stat', '-c', '"%U"', str(master_destination_path)]
        result = dcos_node.run(args=args, shell=True)
        assert result.stdout.decode().strip() == 'root'

        # Implicitly asserts SSH connection closed by ``send_file``.
        dcos_node.run(args=['userdel', '-r', testuser])

    def test_send_symlink(self, dcos_node: Node, tmpdir: local) -> None:
        """
        If sending the path to a symbolic link, the link's target is sent.
        """
        random = str(uuid.uuid4())
        dir_containing_real_file = tmpdir.mkdir(uuid.uuid4().hex)
        dir_containing_symlink = tmpdir.mkdir(uuid.uuid4().hex)
        local_file = dir_containing_real_file.join('example_file.txt')
        local_file.write(random)
        symlink_file = dir_containing_symlink.join('symlink.txt')
        symlink_file_path = Path(str(symlink_file))
        symlink_file_path.symlink_to(target=Path(str(local_file)))
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
            echo True > {filename}
            else
            echo False > {filename}
            fi
            """,
        ).format(filename=filename)
        echo_result = dcos_node.run(
            args=[script],
            tty=tty,
            shell=True,
        )

        assert echo_result.returncode == 0
        run_result = dcos_node.run(args=['cat', filename])
        assert run_result.stdout.strip().decode() == str(tty)

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

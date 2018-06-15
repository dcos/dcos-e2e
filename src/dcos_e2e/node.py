"""
Tools for managing DC/OS cluster nodes.
"""

import stat
import subprocess
from enum import Enum
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict, List, Optional

import yaml

from ._node_transports import DockerExecTransport, NodeTransport, SSHTransport


class Transport(Enum):
    """
    Transports for communicating with nodes.
    """

    SSH = 1
    DOCKER_EXEC = 2


class Node:
    """
    A record of a DC/OS cluster node.
    """

    def __init__(
        self,
        public_ip_address: IPv4Address,
        private_ip_address: IPv4Address,
        default_user: str,
        ssh_key_path: Path,
        default_transport: Transport = Transport.SSH,
    ) -> None:
        """
        Args:
            public_ip_address: The public IP address of the node.
            private_ip_address: The IP address used by the DC/OS component
                running on this node.
            default_user: The default username to use for connections.
            ssh_key_path: The path to an SSH key which can be used to SSH to
                the node as the ``default_user`` user.
            default_transport: The transport to use for communicating with
                nodes.

        Attributes:
            public_ip_address: The public IP address of the node.
            private_ip_address: The IP address used by the DC/OS component
                running on this node.
            default_user: The default username to use for connections.
            default_transport: The transport used to communicate with the node.
        """
        self.public_ip_address = public_ip_address
        self.private_ip_address = private_ip_address
        self.default_user = default_user
        ssh_key_path.chmod(mode=stat.S_IRUSR)
        self._ssh_key_path = ssh_key_path
        self.default_transport = default_transport

    def __str__(self) -> str:
        """
        Convert a `Node` object to string listing only its IP addresses.

        Returns the custom string representation of a `Node` object.
        """
        return 'Node(public_ip={public_ip}, private_ip={private_ip})'.format(
            public_ip=self.public_ip_address,
            private_ip=self.private_ip_address,
        )

    def _get_node_transport(self, transport: Transport) -> NodeTransport:
        """
        Return an instance of a node transport class which correlates to the
        given transport.
        """
        transport_dict = {
            Transport.SSH: SSHTransport,
            Transport.DOCKER_EXEC: DockerExecTransport,
        }

        transport_cls = transport_dict[transport]
        # See https://github.com/python/mypy/issues/5135.
        return transport_cls()  # type: ignore

    def install_dcos(
        self,
        build_artifact: str,
        dcos_config: Dict[str, Any],
        role: str,
    ) -> None:
        # TODO Transport option
        # TODO use default transport
        # TODO log output live option
        node_build_artifact = '/dcos_generate_config.sh'
        self.run(
            args=['curl', '-f', build_artifact, '-o', node_build_artifact],
        )

        # TODO add bootstrap URL location as /genconf/serve
        tempdir = Path(gettempdir())
        dcos_config = {
            **dcos_config,
            **{'bootstrap_url': 'file:///genconf/serve'}
        }
        config_yaml = yaml.dump(data=dcos_config)
        config_file_path = tempdir / 'config.yaml'
        Path(config_file_path).write_text(data=config_yaml)

        remote_genconf_dir = 'genconf'
        remote_genconf_path = Path('/') / remote_genconf_dir

        self.send_file(
            local_path=config_file_path,
            remote_path=remote_genconf_path / 'config.yaml',
        )

        genconf_args = [
            'cd',
            '/',
            '&&',
            'bash',
            node_build_artifact,
            '--offline',
            '-v',
            '--genconf',
        ]

        self.run(
            args=genconf_args,
            log_output_live=True,
            shell=True,
        )

        self.run(args=['rm', node_build_artifact])

        setup_args = [
            'cd',
            '/',
            '&&',
            'bash',
            'genconf/serve/dcos_install.sh',
            '--no-block-dcos-setup',
            role,
        ]
        self.run(args=setup_args, shell=True)

    def run(
        self,
        args: List[str],
        user: Optional[str] = None,
        log_output_live: bool = False,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
        tty: bool = False,
        transport: Optional[Transport] = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a command on this node the given user.

        Args:
            args: The command to run on the node.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            log_output_live: If ``True``, log output live. If ``True``, stderr
                is merged into stdout in the return value.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.
            shell: If ``False`` (the default), each argument is passed as a
                literal value to the command.  If True, the command line is
                interpreted as a shell command, with a special meaning applied
                to some characters (e.g. $, &&, >). This means the caller must
                quote arguments if they may contain these special characters,
                including whitespace.
            tty: If ``True``, allocate a pseudo-tty. This means that the users
                terminal is attached to the streams of the process.
                This means that the values of stdout and stderr will not be in
                the returned ``subprocess.CompletedProcess``.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.

        Returns:
            The representation of the finished process.

        Raises:
            subprocess.CalledProcessError: The process exited with a non-zero
                code.
            ValueError: ``log_output_live`` and ``tty`` are both set to
                ``True``.
        """
        env = dict(env or {})
        if shell:
            args = ['/bin/sh', '-c', ' '.join(args)]

        if user is None:
            user = self.default_user

        if log_output_live and tty:
            message = '`log_output_live` and `tty` cannot both be `True`.'
            raise ValueError(message)

        transport = transport or self.default_transport
        node_transport = self._get_node_transport(transport=transport)
        return node_transport.run(
            args=args,
            user=user,
            log_output_live=log_output_live,
            env=env,
            tty=tty,
            ssh_key_path=self._ssh_key_path,
            public_ip_address=self.public_ip_address,
        )

    def popen(
        self,
        args: List[str],
        user: Optional[str] = None,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
        transport: Optional[Transport] = None,
    ) -> subprocess.Popen:
        """
        Open a pipe to a command run on a node as the given user.

        Args:
            args: The command to run on the node.
            user: The user to open a pipe for a command for over.
                If `None` the ``default_user`` is used instead.
            env: Environment variables to be set on the node before running
                the command. A mapping of environment variable names to
                values.
            shell: If False (the default), each argument is passed as a
                literal value to the command.  If True, the command line is
                interpreted as a shell command, with a special meaning applied
                to some characters (e.g. $, &&, >). This means the caller must
                quote arguments if they may contain these special characters,
                including whitespace.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.

        Returns:
            The pipe object attached to the specified process.
        """
        env = dict(env or {})
        if shell:
            args = ['/bin/sh', '-c', ' '.join(args)]

        if user is None:
            user = self.default_user

        transport = transport or self.default_transport
        node_transport = self._get_node_transport(transport=transport)
        return node_transport.popen(
            args=args,
            user=user,
            env=env,
            ssh_key_path=self._ssh_key_path,
            public_ip_address=self.public_ip_address,
        )

    def send_file(
        self,
        local_path: Path,
        remote_path: Path,
        user: Optional[str] = None,
        transport: Optional[Transport] = None,
    ) -> None:
        """
        Copy a file to this node.

        Args:
            local_path: The path on the host of the file to send.
            remote_path: The path on the node to place the file.
            user: The name of the remote user to send the file. If ``None``,
                the ``default_user`` is used instead.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
        """
        if user is None:
            user = self.default_user

        transport = transport or self.default_transport
        node_transport = self._get_node_transport(transport=transport)
        self.run(
            args=['mkdir', '--parents',
                  str(remote_path.parent)],
            user=user,
            transport=transport,
        )

        return node_transport.send_file(
            local_path=local_path,
            remote_path=remote_path,
            user=user,
            ssh_key_path=self._ssh_key_path,
            public_ip_address=self.public_ip_address,
        )

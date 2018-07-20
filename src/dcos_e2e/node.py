"""
Tools for managing DC/OS cluster nodes.
"""

import stat
import subprocess
import uuid
from enum import Enum
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

from ._node_transports import DockerExecTransport, NodeTransport, SSHTransport


class Role(Enum):
    """
    Roles of DC/OS nodes.
    """

    MASTER = 'master'
    AGENT = 'slave'
    PUBLIC_AGENT = 'slave_public'


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

    def __eq__(self, other: Any) -> bool:
        """
        Compare a ``Node`` object against another one based on its attributes,
        namely the ``public_ip_address`` and ``private_ip_address``.
        """
        return bool(hash(self) == hash(other))

    def __hash__(self) -> int:
        return hash((self.public_ip_address, self.private_ip_address))

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

    def _install_dcos_from_node_path(
        self,
        remote_build_artifact: Path,
        dcos_config: Dict[str, Any],
        role: Role,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
        user: Optional[str] = None,
        log_output_live: bool = False,
        transport: Optional[Transport] = None,
    ) -> None:
        """
        Install DC/OS in a platform-independent way by using
        the advanced installation method as described at
        https://docs.mesosphere.com/1.11/installing/oss/custom/advanced/.

        The documentation describes using a "bootstrap" node, so that only
        one node downloads and extracts the artifact.
        This method is less efficient on a multi-node cluster,
        as it does not use a bootstrap node.
        Instead, the artifact is extracted on this node, and then DC/OS is
        installed.

        Args:
            remote_build_artifact: The path on the node to a build artifact to
                be installed on the node.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            role: The desired DC/OS role for the installation.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            log_output_live: If ``True``, log output live.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.

        """
        tempdir = Path(gettempdir())

        remote_genconf_dir = 'genconf'
        remote_genconf_path = remote_build_artifact.parent / remote_genconf_dir

        for host_path, installer_path in files_to_copy_to_genconf_dir:
            # This is a hack that only works because backends are abusing
            # the bug of being able to supply ``ip_detect_contents`` in the
            # DC/OS configuration file ``config.yaml``.
            # As long as a ``Node`` is not aware of its backend this is the
            # only way to select the backend-specific ``ip-detect`` script.
            if installer_path == Path('/genconf/ip-detect'):
                try:
                    del dcos_config['ip_detect_contents']
                except KeyError:
                    pass
            # This part only exists because of the AWS backend workaround
            # for ip-detect-public-filename in 1.9. It can be removed in a
            # follow-up after changing the backend to respect that parameter.
            if installer_path == Path('/genconf/ip-detect-public'):
                try:
                    del dcos_config['ip_detect_public_contents']
                except KeyError:
                    pass

            relative_installer_path = installer_path.relative_to('/genconf')

            self.send_file(
                local_path=host_path,
                remote_path=remote_genconf_path / relative_installer_path,
                transport=transport,
                user=user,
                sudo=True,
            )

        serve_dir_path = remote_genconf_path / 'serve'
        dcos_config = {
            **dcos_config,
            **{
                'bootstrap_url':
                'file://{serve_dir_path}'.format(
                    serve_dir_path=serve_dir_path,
                ),
            },
        }
        config_yaml = yaml.dump(data=dcos_config)
        config_file_path = tempdir / 'config.yaml'
        Path(config_file_path).write_text(data=config_yaml)

        self.send_file(
            local_path=config_file_path,
            remote_path=remote_genconf_path / 'config.yaml',
            transport=transport,
            user=user,
            sudo=True,
        )

        genconf_args = [
            'cd',
            str(remote_build_artifact.parent),
            '&&',
            'bash',
            str(remote_build_artifact),
            '--offline',
            '-v',
            '--genconf',
        ]

        self.run(
            args=genconf_args,
            log_output_live=True,
            shell=True,
            transport=transport,
            user=user,
            sudo=True,
        )

        self.run(
            args=['rm', str(remote_build_artifact)],
            log_output_live=log_output_live,
            transport=transport,
            user=user,
            sudo=True,
        )

        setup_args = [
            'cd',
            str(remote_build_artifact.parent),
            '&&',
            'bash',
            'genconf/serve/dcos_install.sh',
            '--no-block-dcos-setup',
            role.value,
        ]

        self.run(
            args=setup_args,
            shell=True,
            log_output_live=log_output_live,
            transport=transport,
            user=user,
            sudo=True,
        )

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        dcos_config: Dict[str, Any],
        role: Role,
        user: Optional[str] = None,
        log_output_live: bool = False,
        transport: Optional[Transport] = None,
        files_to_copy_to_genconf_dir: Optional[Iterable[Tuple[Path, Path]]
                                               ] = (),
    ) -> None:
        """
        Install DC/OS in a platform-independent way by using
        the advanced installation method as described at
        https://docs.mesosphere.com/1.11/installing/oss/custom/advanced/.

        The documentation describes using a "bootstrap" node, so that only
        one node downloads and extracts the artifact.
        This method is less efficient on a multi-node cluster,
        as it does not use a bootstrap node.
        Instead, the artifact is sent to this node and then extracted on this
        node, and then DC/OS is installed.

        This creates a folder in ``/dcos-e2e`` on this node which contains the
        DC/OS installation files that can be removed safely after the DC/OS
        installation has finished.

        Run ``dcos-docker doctor`` to see if your host is incompatible with
        this method.

        Args:
            build_artifact: The path to a build artifact to be installed on the
                node.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            role: The desired DC/OS role for the installation.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            log_output_live: If ``True``, log output live.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        workspace_dir = Path('/dcos-e2e')
        node_artifact_parent = workspace_dir / uuid.uuid4().hex
        mkdir_args = ['mkdir', '--parents', str(node_artifact_parent)]
        self.run(
            args=mkdir_args,
            user=user,
            transport=transport,
            sudo=True,
        )
        node_build_artifact = node_artifact_parent / 'dcos_generate_config.sh'
        self.send_file(
            local_path=build_artifact,
            remote_path=node_build_artifact,
            transport=transport,
            user=user,
            sudo=True,
        )
        self._install_dcos_from_node_path(
            remote_build_artifact=node_build_artifact,
            dcos_config=dcos_config,
            user=user,
            role=role,
            log_output_live=log_output_live,
            transport=transport,
            files_to_copy_to_genconf_dir=list(
                files_to_copy_to_genconf_dir or (),
            ),
        )

    def install_dcos_from_url(
        self,
        build_artifact: str,
        dcos_config: Dict[str, Any],
        role: Role,
        user: Optional[str] = None,
        log_output_live: bool = False,
        transport: Optional[Transport] = None,
        files_to_copy_to_genconf_dir: Optional[Iterable[Tuple[Path, Path]]
                                               ] = (),
    ) -> None:
        """
        Install DC/OS in a platform-independent way by using
        the advanced installation method as described at
        https://docs.mesosphere.com/1.11/installing/oss/custom/advanced/.

        The documentation describes using a "bootstrap" node, so that only
        one node downloads and extracts the artifact.
        This method is less efficient on a multi-node cluster,
        as it does not use a bootstrap node.
        Instead, the artifact is downloaded to this node and then extracted on
        this node, and then DC/OS is installed.

        Run ``dcos-docker doctor`` to see if your host is incompatible with
        this method.

        This creates a folder in ``/dcos-e2e`` on this node which contains the
        DC/OS installation files that can be removed safely after the DC/OS
        installation has finished.

        Args:
            build_artifact: The URL to a build artifact to be installed on the
                node.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            role: The desired DC/OS role for the installation.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            log_output_live: If ``True``, log output live.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.

        """
        workspace_dir = Path('/dcos-e2e')
        node_artifact_parent = workspace_dir / uuid.uuid4().hex
        mkdir_args = ['mkdir', '--parents', str(node_artifact_parent)]
        self.run(
            args=mkdir_args,
            user=user,
            transport=transport,
            sudo=True,
        )
        node_build_artifact = node_artifact_parent / 'dcos_generate_config.sh'
        self.run(
            args=[
                'curl',
                '-f',
                build_artifact,
                '-o',
                str(node_build_artifact),
            ],
            log_output_live=log_output_live,
            transport=transport,
            user=user,
            sudo=True,
        )
        self._install_dcos_from_node_path(
            remote_build_artifact=node_build_artifact,
            dcos_config=dcos_config,
            files_to_copy_to_genconf_dir=list(
                files_to_copy_to_genconf_dir or (),
            ),
            user=user,
            role=role,
            log_output_live=log_output_live,
            transport=transport,
        )

    def run(
        self,
        args: List[str],
        user: Optional[str] = None,
        log_output_live: bool = False,
        env: Optional[Dict[str, Any]] = None,
        shell: bool = False,
        tty: bool = False,
        transport: Optional[Transport] = None,
        sudo: bool = False,
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
            sudo: Whether to use "sudo" to run commands.

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

        if sudo:
            args = ['sudo'] + args

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
        sudo: bool = False,
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
            sudo: Whether to use sudo to create the directory which holds the
                remote file.
        """
        if user is None:
            user = self.default_user

        transport = transport or self.default_transport
        node_transport = self._get_node_transport(transport=transport)
        mkdir_args = ['mkdir', '--parents', str(remote_path.parent)]
        self.run(
            args=mkdir_args,
            user=user,
            transport=transport,
            sudo=sudo,
        )

        stat_cmd = ['stat', '-c', '"%U"', str(remote_path.parent)]
        stat_result = self.run(
            args=stat_cmd,
            shell=True,
            user=user,
            transport=transport,
            sudo=sudo,
        )

        original_parent = stat_result.stdout.decode().strip()

        chown_args = ['chown', '-R', user, str(remote_path.parent)]
        self.run(
            args=chown_args,
            transport=transport,
            sudo=True,
        )

        node_transport.send_file(
            local_path=local_path,
            remote_path=remote_path,
            user=user,
            ssh_key_path=self._ssh_key_path,
            public_ip_address=self.public_ip_address,
        )

        chown_args = ['chown', '-R', original_parent, str(remote_path.parent)]
        self.run(
            args=chown_args,
            transport=transport,
            sudo=True,
        )

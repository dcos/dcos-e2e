"""
Tools for managing DC/OS cluster nodes.
"""

import json
import logging
import shlex
import subprocess
import tarfile
import uuid
from enum import Enum
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from textwrap import dedent
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

from ._node_transports import DockerExecTransport, NodeTransport, SSHTransport
from .exceptions import DCOSNotInstalledError

LOGGER = logging.getLogger(__name__)


class Role(Enum):
    """
    Roles of DC/OS nodes.
    """

    MASTER = 'master'
    AGENT = 'slave'
    PUBLIC_AGENT = 'slave_public'


class DCOSVariant(Enum):
    """
    Variant of DC/OS.
    """

    OSS = 1
    ENTERPRISE = 2


class DCOSBuildInfo:
    """
    Build information of DC/OS nodes.
    """

    def __init__(
        self,
        version: str,
        commit: str,
        variant: DCOSVariant,
    ) -> None:
        """
        DC/OS build info object.

        Args:
            version: A version of DC/OS.
            commit: A commit hash of DC/OS.
            variant: A DC/OS variant.

        Attributes:
            version: A version of DC/OS.
            commit: A commit hash of DC/OS.
            variant: A DC/OS variant.
        """
        self.version = version
        self.commit = commit
        self.variant = variant


class Transport(Enum):
    """
    Transports for communicating with nodes.
    """

    SSH = 1
    DOCKER_EXEC = 2


class Output(Enum):
    """
    Output capture options for running commands.

    When using :py:class:`~dcos_e2e.node.Output.LOG_AND_CAPTURE`,
    stdout and stderr are merged into stdout.

    Attributes:
        LOG_AND_CAPTURE: Log output at the debug level. If the code returns a
            ``subprocess.CompletedProcess``, the stdout and stderr will be
            contained in the return value. However, they will be merged into
            stdout.
        CAPTURE: Capture stdout and stderr. If the code returns a
            ``subprocess.CompletedProcess``, the stdout and stderr will be
            contained in the return value.
        NO_CAPTURE: Do not capture stdout or stderr.
    """

    LOG_AND_CAPTURE = 1
    CAPTURE = 2
    NO_CAPTURE = 3


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
                the node as the ``default_user`` user. The file must only have
                permissions to be read by (and optionally written to) the
                owner.
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
        self._ssh_key_path = ssh_key_path
        self.default_transport = default_transport

    def __eq__(self, other: Any) -> bool:
        """
        Compare a ``Node`` object against another one based on its attributes,
        namely the ``public_ip_address`` and ``private_ip_address``.
        """
        return bool(hash(self) == hash(other))

    def __hash__(self) -> int:
        """
        Return a hash which is unique for this node.
        """
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

    def install_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        role: Role,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
        user: Optional[str] = None,
        output: Output = Output.CAPTURE,
        transport: Optional[Transport] = None,
    ) -> None:
        """
        Install DC/OS in a platform-independent way by using
        the advanced installation method as described at
        https://docs.d2iq.com/mesosphere/dcos/2.1/installing/production/deploying-dcos/installation/.

        The documentation describes using a "bootstrap" node, so that only
        one node downloads and extracts the installer.
        This method is less efficient on a multi-node cluster,
        as it does not use a bootstrap node.
        Instead, the installer is put on this node and then extracted on this
        node, and then DC/OS is installed.

        This creates a folder in ``/dcos-install-dir`` on this node which
        contains the DC/OS installation files that can be removed safely after
        the DC/OS installation has finished.

        Args:
            dcos_installer: A URL pointing to an installer to install DC/OS
                from.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            ip_detect_path: The path to the ``ip-detect`` script to use for
                installing DC/OS.
            role: The desired DC/OS role for the installation.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            output: What happens with stdout and stderr.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        node_dcos_installer = _node_installer_path(
            node=self,
            user=user,
            transport=transport,
            output=output,
        )
        _download_installer_to_node(
            node=self,
            dcos_installer_url=dcos_installer,
            output=output,
            transport=transport,
            user=user,
            node_path=node_dcos_installer,
        )
        _install_dcos_from_node_path(
            node=self,
            remote_dcos_installer=node_dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            user=user,
            role=role,
            output=output,
            transport=transport,
        )

    def install_dcos_from_path(
        self,
        dcos_installer: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        role: Role,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
        user: Optional[str] = None,
        output: Output = Output.CAPTURE,
        transport: Optional[Transport] = None,
    ) -> None:
        """
        Install DC/OS in a platform-independent way by using
        the advanced installation method as described at
        https://docs.d2iq.com/mesosphere/dcos/2.1/installing/production/deploying-dcos/installation/.

        The documentation describes using a "bootstrap" node, so that only
        one node downloads and extracts the installer.
        This method is less efficient on a multi-node cluster,
        as it does not use a bootstrap node.
        Instead, the installer is put on this node and then extracted on this
        node, and then DC/OS is installed.

        This creates a folder in ``/dcos-install-dir`` on this node which
        contains the DC/OS installation files that can be removed safely after
        the DC/OS installation has finished.

        Args:
            dcos_installer: The ``Path`` to a local installer to install DC/OS
                from.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            ip_detect_path: The path to the ``ip-detect`` script to use for
                installing DC/OS.
            role: The desired DC/OS role for the installation.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            output: What happens with stdout and stderr.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        node_dcos_installer = _node_installer_path(
            node=self,
            user=user,
            transport=transport,
            output=output,
        )
        self.send_file(
            local_path=dcos_installer,
            remote_path=node_dcos_installer,
            transport=transport,
            user=user,
            sudo=True,
        )
        _install_dcos_from_node_path(
            node=self,
            remote_dcos_installer=node_dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            user=user,
            role=role,
            output=output,
            transport=transport,
        )

    def upgrade_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        role: Role,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
        user: Optional[str] = None,
        output: Output = Output.CAPTURE,
        transport: Optional[Transport] = None,
    ) -> None:
        """
        Upgrade DC/OS on this node.
        This follows the steps in
        https://docs.d2iq.com/mesosphere/dcos/2.1/installing/production/upgrading/.

        Args:
            dcos_installer: A URL pointing to an installer to install DC/OS
                from.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            ip_detect_path: The path to the ``ip-detect`` script to use for
                installing DC/OS.
            role: The desired DC/OS role for the installation.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            output: What happens with stdout and stderr.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        node_dcos_installer = _node_installer_path(
            node=self,
            user=user,
            transport=transport,
            output=output,
        )
        _download_installer_to_node(
            node=self,
            dcos_installer_url=dcos_installer,
            output=output,
            transport=transport,
            user=user,
            node_path=node_dcos_installer,
        )
        _upgrade_dcos_from_node_path(
            node=self,
            remote_dcos_installer=node_dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            user=user,
            role=role,
            output=output,
            transport=transport,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        )

    def upgrade_dcos_from_path(
        self,
        dcos_installer: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        role: Role,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
        user: Optional[str] = None,
        output: Output = Output.CAPTURE,
        transport: Optional[Transport] = None,
    ) -> None:
        """
        Upgrade DC/OS on this node.
        This follows the steps in
        https://docs.d2iq.com/mesosphere/dcos/2.1/installing/production/upgrading/.

        Args:
            dcos_installer: The ``Path`` to a local installer to upgrade DC/OS
                from.
            dcos_config: The contents of the DC/OS ``config.yaml``.
            ip_detect_path: The path to the ``ip-detect`` script to use for
                installing DC/OS.
            role: The desired DC/OS role for the installation.
            user: The username to communicate as. If ``None`` then the
                ``default_user`` is used instead.
            output: What happens with stdout and stderr.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        node_dcos_installer = _node_installer_path(
            node=self,
            user=user,
            transport=transport,
            output=output,
        )
        self.send_file(
            local_path=dcos_installer,
            remote_path=node_dcos_installer,
            transport=transport,
            user=user,
            sudo=True,
        )
        _upgrade_dcos_from_node_path(
            node=self,
            remote_dcos_installer=node_dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            user=user,
            role=role,
            output=output,
            transport=transport,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        )

    def run(
        self,
        args: List[str],
        user: Optional[str] = None,
        output: Output = Output.CAPTURE,
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
            output: What happens with stdout and stderr.
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
                When using a TTY, different transports may use different line
                endings.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.
            sudo: Whether to use "sudo" to run commands.

        Returns:
            The representation of the finished process.

        Raises:
            subprocess.CalledProcessError: The process exited with a non-zero
                code.
        """

        env = dict(env or {})

        if shell:
            args = ['/bin/sh', '-c', ' '.join(args)]

        if sudo:
            args = ['sudo'] + args

        if user is None:
            user = self.default_user

        transport = transport or self.default_transport
        node_transport = self._get_node_transport(transport=transport)

        capture_output = {
            Output.CAPTURE: True,
            Output.LOG_AND_CAPTURE: True,
            Output.NO_CAPTURE: False,
        }[output]

        log_output_live = {
            Output.CAPTURE: False,
            Output.LOG_AND_CAPTURE: True,
            Output.NO_CAPTURE: False,
        }[output]

        if log_output_live:
            log_msg = 'Running command `{cmd}` on a node `{node}`'.format(
                cmd=' '.join(args),
                node=str(self),
            )
            LOGGER.debug(log_msg)

        return node_transport.run(
            args=args,
            user=user,
            log_output_live=log_output_live,
            env=env,
            tty=tty,
            ssh_key_path=self._ssh_key_path,
            public_ip_address=self.public_ip_address,
            capture_output=capture_output,
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

        chown_args = ['chown', user, str(remote_path.parent)]
        self.run(
            args=chown_args,
            user=user,
            transport=transport,
            sudo=sudo,
        )

        tempdir = Path(gettempdir())
        tar_name = '{unique}.tar'.format(unique=uuid.uuid4().hex)
        local_tar_path = tempdir / tar_name

        is_dir = self.run(
            args=[
                'python',
                '-c',
                '"import os; print(os.path.isdir(\'{remote_path}\'))"'.format(
                    remote_path=remote_path,
                ),
            ],
            shell=True,
        ).stdout.decode().strip()

        with tarfile.open(str(local_tar_path), 'w', dereference=True) as tar:
            arcname = Path(remote_path.name)
            if is_dir == 'True':
                arcname = arcname / local_path.name
            tar.add(str(local_path), arcname=str(arcname), recursive=True)

        # `remote_path` may be a tmpfs mount.
        # At the time of writing, for example, `/tmp` is a tmpfs mount
        # on the Docker backend.
        # Copying files to tmpfs mounts fails silently.
        # See https://github.com/moby/moby/issues/22020.
        home_path = self.run(
            args=['echo', '$HOME'],
            user=user,
            transport=transport,
            sudo=False,
            shell=True,
        ).stdout.strip().decode()
        # Therefore, we create a temporary file within our home directory.
        # We then remove the temporary file at the end of this function.

        remote_tar_path = Path(home_path) / tar_name

        node_transport.send_file(
            local_path=local_tar_path,
            remote_path=remote_tar_path,
            user=user,
            ssh_key_path=self._ssh_key_path,
            public_ip_address=self.public_ip_address,
        )

        Path(local_tar_path).unlink()

        tar_args = [
            'tar',
            '-C',
            str(remote_path.parent),
            '-xvf',
            str(remote_tar_path),
        ]
        self.run(
            args=tar_args,
            user=user,
            transport=transport,
            sudo=False,
        )

        chown_args = ['chown', original_parent, str(remote_path.parent)]
        self.run(
            args=chown_args,
            user=user,
            transport=transport,
            sudo=sudo,
        )

        self.run(
            args=['rm', str(remote_tar_path)],
            user=user,
            transport=transport,
            sudo=sudo,
        )

    def download_file(
        self,
        remote_path: Path,
        local_path: Path,
        transport: Optional[Transport] = None,
    ) -> None:
        """
        Download a file from this node.

        Args:
            remote_path: The path on the node to download the file from.
            local_path: The path on the host to download the file to.
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.

        Raises:
            ValueError: The ``remote_path`` does not exist. The ``local_path``
                is an existing file.
        """
        transport = transport or self.default_transport
        user = self.default_user
        transport = self.default_transport
        try:
            self.run(
                args=['test', '-e', str(remote_path)],
                user=user,
                transport=transport,
                sudo=False,
            )
        except subprocess.CalledProcessError:
            message = (
                'Failed to download file from remote location "{location}". '
                'File does not exist.'
            ).format(location=remote_path)
            raise ValueError(message)

        if local_path.exists() and local_path.is_file():
            message = (
                'Failed to download a file to "{file}". '
                'A file already exists in that location.'
            ).format(file=local_path)
            raise ValueError(message)

        if local_path.exists() and local_path.is_dir():
            download_file_path = local_path / remote_path.name
        else:
            download_file_path = local_path

        node_transport = self._get_node_transport(transport=transport)
        node_transport.download_file(
            remote_path=remote_path,
            local_path=download_file_path,
            user=user,
            ssh_key_path=self._ssh_key_path,
            public_ip_address=self.public_ip_address,
        )

    def dcos_build_info(
        self,
        transport: Optional[Transport] = None,
    ) -> DCOSBuildInfo:
        """
        Download a file from this node.

        Args:
            transport: The transport to use for communicating with nodes. If
                ``None``, the ``Node``'s ``default_transport`` is used.

        Raises:
            DCOSNotInstalledError: The DC/OS build information is not available
                because DC/OS is not installed on the ``Node``.
        """
        build_info_remote_path = Path('/opt/mesosphere/etc/dcos-version.json')

        try:
            self.run(
                args=['test', '-e', str(build_info_remote_path)],
                transport=transport,
            )
        except subprocess.CalledProcessError:
            raise DCOSNotInstalledError

        get_build_info_args = ['cat', str(build_info_remote_path)]
        result = self.run(
            args=get_build_info_args,
            transport=transport,
        )
        build_info = json.loads(result.stdout.decode())

        # Work around ``dcos-variant`` missing before DC/OS 1.12.
        if 'dcos-variant' not in build_info:
            full_config_remote_path = Path(
                '/opt/mesosphere/etc/expanded.config.full.json',
            )
            get_bootstrap_config_args = [
                'cat',
                str(full_config_remote_path),
            ]
            result = self.run(
                args=get_bootstrap_config_args,
                transport=transport,
            )
            full_config = json.loads(result.stdout.decode())
            if 'security' in full_config:
                build_info['dcos-variant'] = 'enterprise'
            else:
                build_info['dcos-variant'] = 'open'

        variant_map = {
            'open': DCOSVariant.OSS,
            'enterprise': DCOSVariant.ENTERPRISE,
        }
        return DCOSBuildInfo(
            version=build_info['version'],
            commit=build_info['dcos-image-commit'],
            variant=variant_map[build_info['dcos-variant']],
        )


def _prepare_installer(
    node: Node,
    remote_dcos_installer: Path,
    dcos_config: Dict[str, Any],
    ip_detect_path: Path,
    transport: Optional[Transport],
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    user: Optional[str],
) -> None:
    """
    Put files in place for DC/OS to be installed or upgraded.
    """
    tempdir = Path(gettempdir())

    remote_genconf_dir = 'genconf'
    remote_genconf_path = remote_dcos_installer.parent / remote_genconf_dir

    node.send_file(
        local_path=ip_detect_path,
        remote_path=remote_genconf_path / 'ip-detect',
        transport=transport,
        user=user,
        sudo=True,
    )

    serve_dir_path = remote_genconf_path / 'serve'
    bootstrap_url = 'file://{serve_dir_path}'.format(
        serve_dir_path=serve_dir_path,
    )
    extra_config = {'bootstrap_url': bootstrap_url}
    dcos_config = {**dcos_config, **extra_config}
    config_yaml = yaml.dump(data=dcos_config)
    config_file_path = tempdir / 'config.yaml'
    Path(config_file_path).write_text(data=config_yaml)

    node.send_file(
        local_path=config_file_path,
        remote_path=remote_genconf_path / 'config.yaml',
        transport=transport,
        user=user,
        sudo=True,
    )

    for host_path, installer_path in files_to_copy_to_genconf_dir:
        relative_installer_path = installer_path.relative_to('/genconf')
        destination_path = remote_genconf_path / relative_installer_path
        node.send_file(
            local_path=host_path,
            remote_path=destination_path,
            transport=transport,
            user=user,
            sudo=True,
        )


def _install_dcos_from_node_path(
    node: Node,
    remote_dcos_installer: Path,
    dcos_config: Dict[str, Any],
    ip_detect_path: Path,
    role: Role,
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    user: Optional[str],
    output: Output,
    transport: Optional[Transport],
) -> None:
    """
    Install DC/OS in a platform-independent way by using
    the advanced installation method as described at
    https://docs.d2iq.com/mesosphere/dcos/2.1/installing/production/.

    The documentation describes using a "bootstrap" node, so that only
    one node downloads and extracts the installer.
    This method is less efficient on a multi-node cluster,
    as it does not use a bootstrap node.
    Instead, the installer is extracted on this node, and then DC/OS is
    installed.

    Args:
        remote_dcos_installer: The path on the node to an installer to
            be installed on the node.
        node: The node to install DC/OS on.
        dcos_config: The contents of the DC/OS ``config.yaml``.
        ip_detect_path: The path to the ``ip-detect`` script to use for
            installing DC/OS.
        role: The desired DC/OS role for the installation.
        user: The username to communicate as. If ``None`` then the
            ``default_user`` is used instead.
        output: What happens with stdout and stderr.
        transport: The transport to use for communicating with nodes. If
            ``None``, the ``Node``'s ``default_transport`` is used.
        files_to_copy_to_genconf_dir: Pairs of host paths to paths on
            the installer node. These are files to copy from the host to
            the installer node before installing DC/OS.
    """
    _prepare_installer(
        node=node,
        dcos_config=dcos_config,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        ip_detect_path=ip_detect_path,
        remote_dcos_installer=remote_dcos_installer,
        transport=transport,
        user=user,
    )

    genconf_args = [
        'cd',
        str(remote_dcos_installer.parent),
        '&&',
        'bash',
        str(remote_dcos_installer),
        '-v',
        '--genconf',
    ]

    node.run(
        args=genconf_args,
        output=output,
        shell=True,
        transport=transport,
        user=user,
        sudo=True,
    )

    node.run(
        args=['rm', str(remote_dcos_installer)],
        output=output,
        transport=transport,
        user=user,
        sudo=True,
    )

    setup_args = [
        'cd',
        str(remote_dcos_installer.parent),
        '&&',
        'bash',
        'genconf/serve/dcos_install.sh',
        '--no-block-dcos-setup',
        role.value,
    ]

    node.run(
        args=setup_args,
        shell=True,
        output=output,
        transport=transport,
        user=user,
        sudo=True,
    )


def _node_installer_path(
    node: Node,
    user: Optional[str],
    transport: Optional[Transport],
    output: Output,
) -> Path:
    """
    Create a workspace directory on a node to use for installers and related
    files.

    These are unfortunately kept around, wasting space on the node because
    they can only be removed when the install or upgrade is finished, and we do
    not block on this.

    Args:
        node: The node to create a directory on.
        user: The username to communicate as. If ``None`` then the
            ``default_user`` is used instead.
        output: What happens with stdout and stderr.
        transport: The transport to use for communicating with nodes. If
            ``None``, the ``Node``'s ``default_transport`` is used.

    Returns:
        A path to put a new DC/OS installer in on the node.
    """
    workspace_dir = Path('/dcos-install-dir') / uuid.uuid4().hex
    mkdir_args = ['mkdir', '--parents', str(workspace_dir)]
    node.run(
        args=mkdir_args,
        user=user,
        transport=transport,
        sudo=True,
        output=output,
    )

    return workspace_dir / 'dcos_generate_config.sh'


def _download_installer_to_node(
    node: Node,
    dcos_installer_url: str,
    output: Output,
    transport: Optional[Transport],
    node_path: Path,
    user: Optional[str],
) -> None:
    """
    Download a DC/OS installer to a node.
    """
    curl_args = [
        'curl',
        '-f',
        dcos_installer_url,
        '-o',
        str(node_path),
    ]
    node.run(
        args=curl_args,
        output=output,
        transport=transport,
        user=user,
        sudo=True,
    )


def _upgrade_dcos_from_node_path(
    remote_dcos_installer: Path,
    node: Node,
    dcos_config: Dict[str, Any],
    ip_detect_path: Path,
    role: Role,
    files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    user: Optional[str],
    output: Output,
    transport: Optional[Transport],
) -> None:
    """
    Upgrade DC/OS on this node.
    This follows the steps in
    https://docs.d2iq.com/mesosphere/dcos/2.1/installing/production/upgrading/.

    Args:
        remote_dcos_installer: The path on the node to an installer to
            be installed on the node.
        node: The node to upgrade DC/OS on.
        dcos_config: The contents of the DC/OS ``config.yaml``.
        ip_detect_path: The path to the ``ip-detect`` script to use for
            installing DC/OS.
        role: The desired DC/OS role for the installation.
        user: The username to communicate as. If ``None`` then the
            ``default_user`` is used instead.
        output: What happens with stdout and stderr.
        transport: The transport to use for communicating with nodes. If
            ``None``, the ``Node``'s ``default_transport`` is used.
        files_to_copy_to_genconf_dir: Pairs of host paths to paths on
            the installer node. These are files to copy from the host to
            the installer node before installing DC/OS.

    Raises:
        subprocess.CalledProcessError: One of the upgrade process steps
            exited with a non-zero code.
    """
    _prepare_installer(
        node=node,
        dcos_config=dcos_config,
        files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        ip_detect_path=ip_detect_path,
        remote_dcos_installer=remote_dcos_installer,
        transport=transport,
        user=user,
    )

    python_to_find_open_port = dedent(
        """\
        import socket

        host = ''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new:
            new.bind((host, 0))
            new.listen(1)
            print(int(new.getsockname()[1]))
        """,
    )

    try:
        open_port_result = node.run(
            args=[
                # We source this file to guarantee that we have Python 3 on
                # our path as ``python``.
                '.',
                '/opt/mesosphere/environment.export',
                '&&',
                'python',
                '-c',
                shlex.quote(python_to_find_open_port),
            ],
            shell=True,
            output=Output.CAPTURE,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        # We do not have coverage here - we do not expect to hit it unless
        # we have made a mistake.
        LOGGER.error(exc.stderr.decode())
        raise

    open_port_number = int(open_port_result.stdout.decode())

    genconf_args = [
        'cd',
        str(remote_dcos_installer.parent),
        '&&',
        'PORT={open_port}'.format(open_port=open_port_number),
        'bash',
        str(remote_dcos_installer),
        '-v',
        '--generate-node-upgrade-script',
        node.dcos_build_info().version,
    ]

    # We do not respect ``output`` here because we need to capture output
    # for the result.
    # We cannot just use ``Output.CAPTURE`` because then we will have
    # silence in the test output and Travis CI will error.
    output_map = {
        Output.CAPTURE: Output.CAPTURE,
        Output.LOG_AND_CAPTURE: Output.LOG_AND_CAPTURE,
        Output.NO_CAPTURE: Output.LOG_AND_CAPTURE,
    }
    result = node.run(
        args=genconf_args,
        output=output_map[output],
        shell=True,
        transport=transport,
        user=user,
        sudo=True,
    )

    last_line = result.stdout.decode().split()[-1]
    upgrade_script_path = Path(last_line.split('file://')[-1])

    node.run(
        args=['rm', str(remote_dcos_installer)],
        output=output,
        transport=transport,
        user=user,
        sudo=True,
    )

    if role in (Role.AGENT, Role.PUBLIC_AGENT):
        node.run(
            args=['rm', '-f', '/opt/mesosphere/lib/libltdl.so.7'],
            sudo=True,
            output=output,
        )

    setup_args = [
        'cd',
        str(remote_dcos_installer.parent),
        '&&',
        'bash',
        str(upgrade_script_path),
    ]

    node.run(
        args=setup_args,
        shell=True,
        output=output,
        transport=transport,
        user=user,
        sudo=True,
    )

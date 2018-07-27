"""
Vagrant backend.
"""

import inspect
import os
import shutil
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Type

from dcos_e2e.node import Node

from .._base_classes import ClusterBackend, ClusterManager


class Vagrant(ClusterBackend):
    """
    Vagrant cluster backend base class.
    """

    def __init__(
        self,
        virtualbox_description: str = '',
        workspace_dir: Optional[Path] = None,
    ) -> None:
        """
        Create a configuration for a Vagrant cluster backend.

        Args:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
                This is equivalent to `dir` in
                :py:func:`tempfile.mkstemp`.
            virtualbox_description: A description string to add to VirtualBox
                VMs.

        Attributes:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
            virtualbox_description: A description string to add to VirtualBox
                VMs.
        """
        self.workspace_dir = workspace_dir or Path(gettempdir())
        self.virtualbox_description = virtualbox_description

    @property
    def cluster_cls(self) -> Type['VagrantCluster']:
        """
        Return the :class:`ClusterManager` class to use to create and manage a
        cluster.
        """
        return VagrantCluster

    @property
    def ip_detect_path(self) -> Path:
        """
        Return the path to the Vagrant specific ``ip-detect`` script.
        """
        current_file = inspect.stack()[0][1]
        current_parent = Path(os.path.abspath(current_file)).parent
        return current_parent / 'resources' / 'ip-detect'


class VagrantCluster(ClusterManager):
    """
    Vagrant cluster manager.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
        files_to_copy_to_installer: List[Tuple[Path, Path]],
        cluster_backend: Vagrant,
    ) -> None:
        """
        Create a DC/OS cluster with the given ``cluster_backend``.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            files_to_copy_to_installer: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
            cluster_backend: Details of the specific Docker backend to use.

        Raises:
            NotImplementedError: ``files_to_copy_to_installer`` includes files
                to copy to the installer.
        """
        if files_to_copy_to_installer:
            message = (
                'Copying files to the installer is currently not supported by '
                'the Vagrant backend.'
            )
            raise NotImplementedError(message)

        cluster_id = 'dcos-e2e-{random}'.format(random=uuid.uuid4())
        self._master_prefix = cluster_id + '-master-'
        self._agent_prefix = cluster_id + '-agent-'
        self._public_agent_prefix = cluster_id + '-public-agent-'

        # We work in a new directory.
        # This helps running tests in parallel without conflicts and it
        # reduces the chance of side-effects affecting sequential tests.
        workspace_dir = cluster_backend.workspace_dir
        path = Path(workspace_dir) / uuid.uuid4().hex / cluster_id
        Path(path).mkdir(exist_ok=True, parents=True)
        path = Path(path).resolve()
        vagrantfile_path = Path(__file__).parent / 'resources' / 'Vagrantfile'
        shutil.copy(src=str(vagrantfile_path), dst=str(path))

        vm_names = []
        for nodes, prefix in (
            (masters, self._master_prefix),
            (agents, self._agent_prefix),
            (public_agents, self._public_agent_prefix),
        ):
            for vm_number in range(nodes):
                name = prefix + str(vm_number)
                vm_names.append(name)

        vagrant_env = {
            'PATH': os.environ['PATH'],
            'VM_NAMES': ','.join(vm_names),
            'VM_DESCRIPTION': cluster_backend.virtualbox_description,
        }

        # We import Vagrant here instead of at the top of the file because, if
        # the Vagrant executable is not found, a warning is logged.
        #
        # We want to avoid that warning for users of other backends who do not
        # have the Vagrant executable.
        import vagrant
        self._vagrant_client = vagrant.Vagrant(
            root=str(path),
            env=vagrant_env,
            quiet_stdout=False,
            quiet_stderr=True,
        )

        self._vagrant_client.up()

    def install_dcos_from_url_with_bootstrap_node(
        self,
        build_artifact: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        log_output_live: bool,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from a build artifact passed as an URL string.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script that is used for
                installing DC/OS.
            log_output_live: If ``True``, log output of the installation live.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on the
                installer node. This must be empty as it is not currently
                supported.
        """
        raise NotImplementedError

    def install_dcos_from_path_with_bootstrap_node(
        self,
        build_artifact: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        log_output_live: bool,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from a build artifact passed as a file system `Path`.

        Args:
            build_artifact: The path to a build artifact to install DC/OS from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script that is used for
                installing DC/OS.
            log_output_live: If ``True``, log output of the installation live.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on the
                installer node. This must be empty as it is not currently
                supported.
        """
        raise NotImplementedError

    def destroy_node(self, node: Node) -> None:
        """
        Destroy a node in the cluster.
        """
        client = self._vagrant_client
        hostname_command = "hostname -I | cut -d' ' -f2"
        virtual_machines = [
            vm for vm in client.status() if vm.state == 'running'
        ]
        for virtual_machine in virtual_machines:
            vm_ip_str = client.ssh(
                vm_name=virtual_machine.name,
                command=hostname_command,
            ).strip()

            vm_ip_address = IPv4Address(vm_ip_str)
            if vm_ip_address == node.private_ip_address:
                client.destroy(vm_name=virtual_machine.name)

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        client = self._vagrant_client
        for node in {*self.masters, *self.agents, *self.public_agents}:
            self.destroy_node(node=node)

        shutil.rmtree(path=client.root, ignore_errors=True)

    def _nodes(self, node_base_name: str) -> Set[Node]:
        """
        Args:
            node_base_name: The start of node names.

        Returns: ``Node``s corresponding to VMs with names starting with
            ``node_base_name``.
        """
        client = self._vagrant_client
        vagrant_nodes = [
            vm for vm in client.status()
            if vm.name.startswith(node_base_name) and vm.state == 'running'
        ]
        hostname_command = "hostname -I | cut -d' ' -f2"
        nodes = set([])
        for node in vagrant_nodes:
            default_user = client.user(vm_name=node.name)
            ssh_key_path = Path(client.keyfile(vm_name=node.name))

            not_ip_chars = ['{', '}', '^', '[', ']']

            node_ip_str = client.ssh(
                vm_name=node.name,
                command=hostname_command,
            ).strip()

            for char in not_ip_chars:
                node_ip_str = node_ip_str.replace(char, '')

            node_ip_address = IPv4Address(node_ip_str)

            nodes.add(
                Node(
                    public_ip_address=node_ip_address,
                    private_ip_address=node_ip_address,
                    default_user=default_user,
                    ssh_key_path=ssh_key_path,
                ),
            )
        return nodes

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master :class:`.node.Node` s.
        """
        return self._nodes(node_base_name=self._master_prefix)

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent :class:`.node.Node` s.
        """
        return self._nodes(node_base_name=self._agent_prefix)

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent :class:`.node.Node` s.
        """
        return self._nodes(node_base_name=self._public_agent_prefix)

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        return {
            'check_time': 'false',
            'cluster_name': 'DCOS',
            'exhibitor_storage_backend': 'static',
            'master_discovery': 'static',
            'resolvers': ['8.8.8.8'],
            'ssh_port': 22,
            'ssh_user': 'vagrant',
        }

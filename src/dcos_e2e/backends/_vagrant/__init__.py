"""
Vagrant backend.
"""

import os
import shutil
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict, Iterable, Optional, Set, Tuple, Type

from dcos_e2e.base_classes import ClusterBackend, ClusterManager
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node, Output


class Vagrant(ClusterBackend):
    """
    Vagrant cluster backend base class.
    """

    def __init__(
        self,
        virtualbox_description: str = '',
        workspace_dir: Optional[Path] = None,
        vm_memory_mb: int = 2048,
        vagrant_box_version: str = '~> 0.10',
        vagrant_box_url: str = (
            'https://downloads.dcos.io/dcos-vagrant/metadata.json'
        ),
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
            vm_memory_mb: The amount of memory in megabytes allocated to each
                VM.
            vagrant_box_version: The Vagrant box version to use. See
                https://www.vagrantup.com/docs/boxes/versioning.html#version-constraints
                for version details.
            vagrant_box_url: The URL of the Vagrant box to use.

        Attributes:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
            virtualbox_description: A description string to add to VirtualBox
                VMs.
            vm_memory_mb: The amount of memory in megabytes allocated to each
                VM.
            vagrant_box_version: The Vagrant box version to use. See
                https://www.vagrantup.com/docs/boxes/versioning.html#version-constraints
                for version details.
            vagrant_box_url: The URL of the Vagrant box to use.
        """
        self.workspace_dir = workspace_dir or Path(gettempdir())
        self.virtualbox_description = virtualbox_description
        self.vm_memory_mb = vm_memory_mb
        self.vagrant_box_version = vagrant_box_version
        self.vagrant_box_url = vagrant_box_url

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
        current_parent = Path(__file__).parent.resolve()
        return current_parent / 'resources' / 'ip-detect'

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        # See https://jira.d2iq.com/browse/DCOS_OSS-2501
        # for removing "check_time: 'false'".
        return {
            'check_time': 'false',
            'cluster_name': 'DCOS',
            'exhibitor_storage_backend': 'static',
            'master_discovery': 'static',
            'resolvers': ['8.8.8.8'],
            'ssh_port': 22,
            'ssh_user': 'vagrant',
        }


class VagrantCluster(ClusterManager):
    """
    Vagrant cluster manager.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        masters: int,
        agents: int,
        public_agents: int,
        cluster_backend: Vagrant,
    ) -> None:
        """
        Create a DC/OS cluster with the given ``cluster_backend``.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            cluster_backend: Details of the specific Docker backend to use.
        """
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
            'HOME': os.environ['HOME'],
            'PATH': os.environ['PATH'],
            'VM_NAMES': ','.join(vm_names),
            'VM_DESCRIPTION': cluster_backend.virtualbox_description,
            'VM_MEMORY': str(cluster_backend.vm_memory_mb),
            'VAGRANT_BOX_VERSION': str(cluster_backend.vagrant_box_version),
            'VAGRANT_BOX_URL': cluster_backend.vagrant_box_url,
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
            quiet_stderr=False,
        )

        self._vagrant_client.up()

    def install_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from an installer passed as an URL string.

        Args:
            dcos_installer: The URL string to an installer to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script that is used for
                installing DC/OS.
            output: What happens with stdout and stderr.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on the
                installer node. This must be empty as it is not currently
                supported.
        """
        cluster = Cluster.from_nodes(
            masters=self.masters,
            agents=self.agents,
            public_agents=self.public_agents,
        )

        cluster.install_dcos_from_url(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            output=output,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        )

    def install_dcos_from_path(
        self,
        dcos_installer: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from an installer passed as a file system `Path`.

        Args:
            dcos_installer: The path to an installer to install DC/OS from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The ``ip-detect`` script that is used for
                installing DC/OS.
            output: What happens with stdout and stderr.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on the
                installer node. This must be empty as it is not currently
                supported.
        """
        cluster = Cluster.from_nodes(
            masters=self.masters,
            agents=self.agents,
            public_agents=self.public_agents,
        )

        cluster.install_dcos_from_path(
            dcos_installer=dcos_installer,
            dcos_config=dcos_config,
            ip_detect_path=ip_detect_path,
            output=output,
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
        )

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

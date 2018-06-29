"""
Vagrant backend.
"""

import os
import shutil
import textwrap
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from typing import Any, Dict, List, Optional, Set, Tuple, Type

import vagrant
import yaml

from dcos_e2e.node import Node

from .._base_classes import ClusterBackend, ClusterManager


class Vagrant(ClusterBackend):
    """
    Vagrant cluster backend base class.
    """

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
    ) -> None:
        """
        Create a configuration for a Vagrant cluster backend.

        Args:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
                This is equivalent to `dir` in
                :py:func:`tempfile.mkstemp`.

        Attributes:
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
        """
        self.workspace_dir = workspace_dir or Path(gettempdir())

    @property
    def cluster_cls(self) -> Type['VagrantCluster']:
        """
        Return the :class:`ClusterManager` class to use to create and manage a
        cluster.
        """
        return VagrantCluster


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

        # Plan for dcos-vagrant doctor:
        # * Check we have the VirtualBox guest additions plugin,
        # using client.plugin_list
        # * Check that have a viable version of VirtualBox - figure this out
        # from the DC/OS Vagrant documentation. 5.1.18 seems to work. The
        # latest version of VirtualBox does not work.

        # Plan:
        # * Ignore coverage on the new Vagrant files
        # * Raise NotImplementedError for files_to_copy_to_installer
        # * Write documentation
        # * Follow-up - make CLI (JIRA) with dcos-vagrant doctor
        # * Remove DC/OS Vagrant


        cluster_id = 'dcos-e2e-{random}'.format(random=uuid.uuid4())
        self._master_prefix = cluster_id + '-master-'
        self._agent_prefix = cluster_id + '-agent-'
        self._public_agent_prefix = cluster_id + '-public-agent-'

        # We work in a new directory.
        # This helps running tests in parallel without conflicts and it
        # reduces the chance of side-effects affecting sequential tests.
        workspace_dir = cluster_backend.workspace_dir
        path = Path(workspace_dir) / uuid.uuid4().hex / cluster_id
        path.mkdir(exist_ok=True, parents=True)
        path = path.resolve()
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
        }
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
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a build artifact passed as an URL string.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            log_output_live: If ``True``, log output of the installation live.
        """
        raise NotImplementedError

    def install_dcos_from_path_with_bootstrap_node(
        self,
        build_artifact: Path,
        dcos_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a build artifact passed as a file system `Path`.

        Args:
            build_artifact: The path to a build artifact to install DC/OS from.
            dcos_config: The DC/OS configuration to use.
            log_output_live: If ``True``, log output of the installation live.
        """
        raise NotImplementedError

    def destroy_node(self, node: Node) -> None:
        """
        Destroy a node in the cluster.
        """
        client = self._vagrant_client
        hostname_command = "hostname -I | cut -d' ' -f2"
        for virtual_machine in client.status():
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
            vm for vm in client.status() if vm.name.startswith(node_base_name)
        ]
        hostname_command = "hostname -I | cut -d' ' -f2"
        nodes = set([])
        for node in vagrant_nodes:
            default_user = client.user(vm_name=node.name)
            ssh_key_path = Path(client.keyfile(vm_name=node.name))

            node_ip_str = client.ssh(
                vm_name=node.name,
                command=hostname_command,
            ).strip()

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
        master = next(iter(self.masters))

        # pylint: disable=anomalous-backslash-in-string
        ip_detect_contents = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            echo $(/usr/sbin/ip route show to match {master_ip}
            | grep -Eo '[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}'
            | tail -1)
            """.format(master_ip=master.private_ip_address),
        )
        # pylint: enable=anomalous-backslash-in-string

        config = {
            'check_time': 'false',
            'cluster_name': 'DCOS',
            'exhibitor_storage_backend': 'static',
            'master_discovery': 'static',
            'resolvers': ['8.8.8.8'],
            'ssh_port': 22,
            'ssh_user': 'vagrant',
            # This is not a documented option.
            # Users are instructed to instead provide a filename with
            # 'ip_detect_contents_filename'.
            'ip_detect_contents': yaml.dump(ip_detect_contents),
        }

        return config

"""
Vagrant backend.
"""

import os
import textwrap
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Type

import vagrant
import yaml

from dcos_e2e.node import Node

from .._base_classes import ClusterBackend, ClusterManager


class Vagrant(ClusterBackend):
    """
    Vagrant cluster backend base class.
    """

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

    def __init__(
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
            cluster_backend: Details of the specific DC/OS Docker backend to
                use.
        """
        # Document that we need Virtualbox guest additions
        # Write a configuration file
        # TODO Doctor command with client.plugin_list
        #
        # Works with Virtualbox 5.1.18
        # Does not work with Virtualbox latest version
        # TODO: submit a bug report to DC/OS Vagrant

        # Plan:
        # * Create nodes separate from installing DC/OS
        # * Use environment variables for e.g. number of nodes, cluster ID
        # * Fill in methods like Destroy
        # * Copy the file to a workspace dir like Docker
        cluster_id = 'dcos-e2e-{random}'.format(random=uuid.uuid4())
        self._master_prefix = cluster_id + '-master-'
        self._agent_prefix = cluster_id + '-agent-'
        self._public_agent_prefix = cluster_id + '-public-agent-'

        vm_names = []
        for nodes, prefix in (
            (masters, self._master_prefix),
            (agents, self._agent_prefix),
            (public_agents, self._public_agent_prefix),
        ):
            for vm_number in range(nodes):
                name = prefix + str(vm_number)
                vm_names.append(name)

        path = Path(__file__).parent / 'resources' / 'dcos-vagrant'
        vagrant_env = {
            'PATH': os.environ['PATH'],
            # TODO Instead maybe just run Vagrant up multiple times
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
        raise NotImplementedError

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        raise NotImplementedError

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
        # TODO get IP with vagrant ssh -c "hostname -I | cut -d' ' -f2" 2>/dev/null
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

        ip_detect_contents = textwrap.dedent(
            """\
            #!/usr/bin/env bash

            set -o errexit
            set -o nounset
            set -o pipefail

            echo $(/usr/sbin/ip route show to match {master_ip} | grep -Eo '[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}\.[0-9]{{1,3}}' | tail -1)
            """.format(master_ip=master.private_ip_address),
        )
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

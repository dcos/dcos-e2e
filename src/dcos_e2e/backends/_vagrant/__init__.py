"""
Vagrant backend.
"""

from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Type

import vagrant

from .._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.node import Node, Transport
from dcos_e2e._common import run_subprocess


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
        self._default_transport = Transport.SSH

        # Document that we need Virtualbox guest additions
        # Write a configuration file
        #
        # Works with Virtualbox 5.1.18
        # Does not work with Virtualbox latest version
        # TODO: submit a bug report to DC/OS Vagrant

        # Plan:
        # * Create nodes separate from installing DC/OS
        # * Fill in methods like Destroy
        # * Look at why we have things like m1.dcos - can we just use IP addresses?
        # * Removing junk from the installation
        # * Using a custom DC/OS config file
        # * Customise size of cluster (generate YAML)
        # * Passwordless
        dcos_vagrant_path = Path(__file__).parent / 'resources' / 'dcos-vagrant'
        config_file_path = dcos_vagrant_path / 'VagrantConfig-1m-1a-1p.yaml'
        artifact_path = dcos_vagrant_path / 'dcos_generate_config.oss.sh'
        dcos_config_path = dcos_vagrant_path / 'etc' / 'config-1.11.0.yaml'
        license_key_path = Path('/tmp/license-key.txt')
        return
        import os
        run_subprocess(
            args=['/usr/local/bin/vagrant', 'up', '--provider=virtualbox'],
            cwd=str(dcos_vagrant_path),
            env={
                'PATH': os.environ['PATH'],
            },
            log_output_live=True,
        )

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

    def install_dcos_from_path(
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


    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        dcos_vagrant_path = Path(__file__).parent / 'resources' / 'dcos-vagrant'
        client = vagrant.Vagrant(root=str(dcos_vagrant_path))

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master :class:`.node.Node` s.
        """
        dcos_vagrant_path = Path(__file__).parent / 'resources' / 'dcos-vagrant'
        client = vagrant.Vagrant(root=str(dcos_vagrant_path))

        ip_addresses = [IPv4Address('192.168.65.90')]

        nodes = set([])
        for ip_address in ip_addresses:
            nodes.add(
                Node(
                    public_ip_address=ip_address,
                    private_ip_address=ip_address,
                    default_user='vagrant',
                    ssh_key_path=Path(client.keyfile()),
                    default_transport=self._default_transport,
                ),
            )

        return nodes

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent :class:`.node.Node` s.
        """
        dcos_vagrant_path = Path(__file__).parent / 'resources' / 'dcos-vagrant'
        client = vagrant.Vagrant(root=str(dcos_vagrant_path))

        ip_addresses = [IPv4Address('192.168.65.111')]

        nodes = set([])
        for ip_address in ip_addresses:
            nodes.add(
                Node(
                    public_ip_address=ip_address,
                    private_ip_address=ip_address,
                    default_user='vagrant',
                    ssh_key_path=Path(client.keyfile()),
                    default_transport=self._default_transport,
                ),
            )

        return nodes

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent :class:`.node.Node` s.
        """
        dcos_vagrant_path = Path(__file__).parent / 'resources' / 'dcos-vagrant'
        client = vagrant.Vagrant(root=str(dcos_vagrant_path))

        ip_addresses = [IPv4Address('192.168.65.60')]

        nodes = set([])
        for ip_address in ip_addresses:
            nodes.add(
                Node(
                    public_ip_address=ip_address,
                    private_ip_address=ip_address,
                    default_user='vagrant',
                    ssh_key_path=Path(client.keyfile()),
                    default_transport=self._default_transport,
                ),
            )

        return nodes

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        return {}

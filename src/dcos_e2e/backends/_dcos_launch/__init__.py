"""
A DC/OS Launch backend for DC/OS E2E.
"""
import uuid
import sys

from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Dict, Set

from dcos_e2e.backends import ClusterBackend, ClusterManager
from dcos_e2e.node import Node
try:
    from dcos_launch import config, get_launcher
except ImportError:
    # Fail silently on Windows, otherwise it would trigger :
    #   "ImportError: No module named 'termios'"
    assert sys.platform == 'win32'


class DCOSLaunch(ClusterBackend):

    def __init__(
            self,
            ssh_private_key_filename: str,
    ) -> None:
        self.ssh_private_key_filename = ssh_private_key_filename

    @property
    def cluster_cls(self):
        return DCOSLaunchCluster

    @property
    def default_ssh_user(self) -> str:
        return 'centos'


class DCOSLaunchCluster(ClusterManager):
    # pylint: disable=too-many-arguments,super-init-not-called
    def __init__(
            self,
            masters: int,
            agents: int,
            public_agents: int,
            files_to_copy_to_installer: Dict[Path, Path],
            cluster_backend: DCOSLaunch,
    ) -> None:
        self.num_masters = masters
        self.num_agents = agents
        self.num_public_agents = public_agents
        self.cluster_backend = cluster_backend
        self.dcos_launcher = None
        self.cluster_info = {}
    # pylint: enable=too-many-arguments,super-init-not-called

    def install_dcos_from_url(
            self,
            build_artifact: str,
            extra_config: Dict[str, Any],
            log_output_live: bool,
    ) -> None:

        dcos_launch_config = get_dcos_launch_config(
            installer_url=build_artifact,
            num_masters=self.num_masters,
            num_agents=self.num_agents,
            num_public_agents=self.num_public_agents,
            ssh_private_key=self.cluster_backend.ssh_private_key_filename,
            extra_config=extra_config,
        )

        dcos_launch_config = config.get_validated_config(
            dcos_launch_config, '/tmp')

        launcher = get_launcher(dcos_launch_config)

        cluster_info = launcher.create()

        self.dcos_launcher = get_launcher(cluster_info)
        self.dcos_launcher.wait()
        self.cluster_info = self.dcos_launcher.describe()

    def install_dcos_from_path(
            self,
            build_artifact: Path,
            extra_config: Dict[str, Any],
            log_output_live: bool,
    ) -> None:
        message = (
            'The DC/OS Launch backend does not support the installation of '
            ' build artifacts passed via a path. This is because a more '
            'efficient installation method exists in `install_dcos_from_url`.'
        )
        raise NotImplementedError(message)

    def destroy(self) -> None:
        if self.dcos_launcher:
            self.dcos_launcher.delete()

    @property
    def masters(self) -> Set[Node]:
        nodes = set([])
        for master in self.cluster_info.get('masters'):
            node = Node(
                public_ip_address=IPv4Address(master.get('public_ip')),
                private_ip_address=IPv4Address(master.get('private_ip')),
                ssh_key_path=self.cluster_backend.ssh_private_key_filename,
            )
            nodes.add(node)

        return nodes

    @property
    def agents(self) -> Set[Node]:
        nodes = set([])
        for priv_agent in self.cluster_info.get('private_agents'):
            node = Node(
                public_ip_address=IPv4Address(priv_agent.get('public_ip')),
                private_ip_address=IPv4Address(priv_agent.get('private_ip')),
                ssh_key_path=self.cluster_backend.ssh_private_key_filename,
            )
            nodes.add(node)

        return nodes

    @property
    def public_agents(self) -> Set[Node]:
        nodes = set([])
        for pub_agent in self.cluster_info.get('public_agents'):
            node = Node(
                public_ip_address=IPv4Address(pub_agent.get('public_ip')),
                private_ip_address=IPv4Address(pub_agent.get('private_ip')),
                ssh_key_path=self.cluster_backend.ssh_private_key_filename,
            )
            nodes.add(node)

        return nodes


# pylint: disable=too-many-arguments
def get_dcos_launch_config(
        installer_url,
        num_masters,
        num_agents,
        num_public_agents,
        ssh_private_key,
        extra_config,
):
    dcos_config = {
        'cluster_name': 'DC/OS Licensing CLI Integration Tests',
        'resolvers': ['10.10.0.2'],
        'dns_search': 'us-west-2.compute.internal',
        'master_discovery': 'static',
        'exhibitor_storage_backend': 'static',
    }

    deployment_name = "dcos-licensing-cli-e2e-tests-" + uuid.uuid4().hex

    return {
        'launch_config_version': 1,
        'deployment_name': deployment_name,
        'installer_url': installer_url,
        'platform': 'aws',
        'provider': 'onprem',
        'aws_region': 'us-west-2',
        'aws_key_name': 'default',
        'ssh_private_key_filename': ssh_private_key,
        'os_name': 'cent-os-7-dcos-prereqs',
        'instance_type': 'm4.large',
        'num_masters': num_masters,
        'num_private_agents': num_agents,
        'num_public_agents': num_public_agents,
        'dcos_config': {**dcos_config, **extra_config},
    }

"""
A DC/OS Launch backend for DC/OS E2E.
"""
import uuid
# import sys

from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Dict, Set, Type
from typing import Optional  # noqa: F401

from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node
from dcos_launch.util import AbstractLauncher  # noqa: F401
from dcos_launch import config, get_launcher
# try:
#     from dcos_launch import config, get_launcher
# except ImportError:
#     # Fail silently on Windows, otherwise it would trigger :
#     #   "ImportError: No module named 'termios'"
#     assert sys.platform == 'win32'


class AWS(ClusterBackend):
    """
    A record of an AWS backend which can be used to create clusters.
    """

    def __init__(
        self,
        aws_key_name: str,
        ssh_key_path: Path,
        aws_region: str = 'us-west-2',
        instance_type: str = 'm4.large',
    ) -> None:
        """
        Create a configuration for a Docker cluster backend.

        """
        self.config = {
            'platform': 'aws',
            'provider': 'onprem',
            'aws_region': aws_region,
            'aws_key_name': aws_key_name,
            'instance_type': instance_type,
            'ssh_private_key_filename': str(ssh_key_path),
        }

    @property
    def cluster_cls(self) -> Type['AWSCluster']:
        return AWSCluster

    @property
    def default_ssh_user(self) -> str:
        return 'centos'

    @property
    def default_linux_distribution(self) -> Distribution:
        return Distribution.CENTOS_7


class AWSCluster(ClusterManager):
    # pylint: disable=too-many-arguments,super-init-not-called
    """
    A record of an AWS cluster.
    """

    def __init__(
        self,
        masters: int,
        agents: int,
        public_agents: int,
        files_to_copy_to_installer: Dict[Path, Path],
        cluster_backend: AWS,
        linux_distribution: Distribution,
    ) -> None:
        self.cluster_backend = cluster_backend
        self.dcos_launcher = None  # type: Optional[AbstractLauncher]
        self.cluster_info = {}  # type: Dict[str, Any]

        aws_distros = {
            Distribution.CENTOS_7: 'cent-os-7-dcos-prereqs',
        }

        cluster_config = {
            'launch_config_version': 1,
            'deployment_name': 'dcos-e2e-{}'.format(str(uuid.uuid4())),
            'num_masters': masters,
            'num_private_agents': agents,
            'num_public_agents': public_agents,
            'os_name': aws_distros[linux_distribution],
        }

        self.ssh_key_path = Path(
            cluster_backend.config['ssh_private_key_filename'])

        self.launch_config = {**cluster_config, **cluster_backend.config}

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:

        self.launch_config['installer_url'] = build_artifact

        dcos_config = {
            'cluster_name': self.launch_config['deployment_name'],
            'resolvers': ['10.10.0.2'],
            'master_discovery': 'static',
            'exhibitor_storage_backend': 'static',
        }

        self.launch_config['dcos_config'] = {**dcos_config, **extra_config}

        validated_launch_config = config.get_validated_config(
            self.launch_config, '/tmp'
        )

        launcher = get_launcher(validated_launch_config)

        cluster_info = launcher.create()

        self.dcos_launcher = get_launcher(
            cluster_info)
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
            'build artifacts passed via a path. This is because a more '
            'efficient installation method exists in `install_dcos_from_url`.'
        )
        raise NotImplementedError(message)

    def destroy(self) -> None:
        if self.dcos_launcher:
            self.dcos_launcher.delete()

    @property
    def masters(self) -> Set[Node]:
        nodes = set([])
        cluster_masters = list(self.cluster_info['masters'])
        for master in cluster_masters:
            node = Node(
                public_ip_address=IPv4Address(master.get('public_ip')),
                private_ip_address=IPv4Address(master.get('private_ip')),
                ssh_key_path=self.ssh_key_path,
            )
            nodes.add(node)

        return nodes

    @property
    def agents(self) -> Set[Node]:
        nodes = set([])
        cluster_agents = list(self.cluster_info['private_agents'])
        for priv_agent in cluster_agents:
            node = Node(
                public_ip_address=IPv4Address(priv_agent.get('public_ip')),
                private_ip_address=IPv4Address(priv_agent.get('private_ip')),
                ssh_key_path=self.ssh_key_path,
            )
            nodes.add(node)

        return nodes

    @property
    def public_agents(self) -> Set[Node]:
        nodes = set([])
        cluster_public_agents = list(self.cluster_info['public_agents'])
        for pub_agent in cluster_public_agents:
            node = Node(
                public_ip_address=IPv4Address(pub_agent.get('public_ip')),
                private_ip_address=IPv4Address(pub_agent.get('private_ip')),
                ssh_key_path=self.ssh_key_path,
            )
            nodes.add(node)

        return nodes

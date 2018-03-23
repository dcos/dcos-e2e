"""
A DC/OS Launch backend for DC/OS E2E.
"""
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from tempfile import gettempdir
from typing import Optional  # noqa: F401
from typing import Any, Dict, Set, Type

from dcos_launch import config, get_launcher
from dcos_launch.aws import DcosCloudformationLauncher
from dcos_launch.onprem import AbstractOnpremLauncher
from dcos_launch.util import AbstractLauncher  # noqa: F401

from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node


class AWS(ClusterBackend):
    """
    A record of an AWS backend which can be used to create clusters.
    """

    def __init__(
        self,
        aws_region: str = 'us-west-2',
        instance_type: str = 'm4.large',
        admin_location: str = '0.0.0.0/0',
        linux_distribution: Distribution = Distribution.CENTOS_7,
        workspace_dir: Optional[Path] = None,
    ) -> None:
        """
        Create a configuration for a Docker cluster backend.

        """
        supported_distributions = {Distribution.CENTOS_7, Distribution.COREOS}
        if linux_distribution not in supported_distributions:
            raise NotImplementedError

        aws_ssh_user = {
            Distribution.CENTOS_7: 'centos',
            Distribution.COREOS: 'core',
        }

        self._default_ssh_user = aws_ssh_user[linux_distribution]
        self.workspace_dir = workspace_dir or Path(gettempdir())
        self.linux_distribution = linux_distribution

        self.config = {
            'platform': 'aws',
            'provider': 'onprem',
            'aws_region': aws_region,
            'instance_type': instance_type,
            'admin_location': admin_location,
        }

    @property
    def cluster_cls(self) -> Type['AWSCluster']:
        return AWSCluster

    @property
    def default_ssh_user(self) -> str:
        return self._default_ssh_user


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
    ) -> None:

        unique = 'dcos-e2e-{}'.format(str(uuid.uuid4()))

        self._path = Path(cluster_backend.workspace_dir) / uuid.uuid4().hex
        Path(self._path).mkdir(exist_ok=True)
        self._path = Path(self._path).resolve()
        self._path = Path(self._path) / unique
        Path(self._path).mkdir(exist_ok=True)

        self._default_ssh_user = cluster_backend.default_ssh_user
        self.cluster_backend = cluster_backend
        self.dcos_launcher = None  # type: Optional[AbstractLauncher]
        self.cluster_info = {}  # type: Dict[str, Any]

        aws_distros = {
            Distribution.CENTOS_7: 'cent-os-7-dcos-prereqs',
            Distribution.COREOS: 'coreos',
        }

        cluster_config = {
            'launch_config_version': 1,
            'deployment_name': unique,
            'num_masters': masters,
            'num_private_agents': agents,
            'num_public_agents': public_agents,
            'os_name': aws_distros[cluster_backend.linux_distribution],
            'key_helper': True,
        }

        launch_config = {**cluster_config, **cluster_backend.config}

        # Fake url to pass config validation
        launch_config['installer_url'] = 'https://google.com'

        # Preliminary DC/OS config to pass config validation
        dcos_config = {
            'cluster_name': unique,
            'resolvers': ['10.10.0.2', '8.8.8.8'],
            'master_discovery': 'static',
            'exhibitor_storage_backend': 'static',
        }

        launch_config['dcos_config'] = dcos_config

        validated_launch_config = config.get_validated_config(
            launch_config, str(self._path)
        )

        # Returns a DcosCloudformationLauncher
        self.launcher = get_launcher(validated_launch_config)

        # Creates the AWS stack
        self.cluster_info = self.launcher.create()

        # Waits for stack setup completion
        DcosCloudformationLauncher.wait(self.launcher)

        # Store the generated AWS SSH key
        self._ssh_key_path = self._path / 'id_rsa'
        private_key = self.cluster_info['ssh_private_key']
        self._ssh_key_path.write_bytes(private_key.encode())

        # Update the cluster_info with post-install DC/OS information
        self.cluster_info = self.launcher.describe()

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:

        # Returns an AbstractOnpremLauncher
        # self.launcher = get_launcher(self.cluster_info)

        # Overwrite the installer_url
        self.launcher.config['installer_url'] = build_artifact

        # Get the fake validated config
        dcos_config = self.launcher.config['dcos_config']

        # Write back the real config plus exta parameters
        self.launcher.config['dcos_config'] = {**dcos_config, **extra_config}

        # Start the actual DC/OS installation process
        AbstractOnpremLauncher.wait(self.launcher)

        # Update the cluster_info with post-install DC/OS information
        self.cluster_info = self.launcher.describe()

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
        if self.launcher:
            self.launcher.delete()

    @property
    def masters(self) -> Set[Node]:
        nodes = set([])
        cluster_masters = list(self.cluster_info['masters'])
        for master in cluster_masters:
            node = Node(
                public_ip_address=IPv4Address(master.get('public_ip')),
                private_ip_address=IPv4Address(master.get('private_ip')),
                default_ssh_user=self._default_ssh_user,
                ssh_key_path=self._ssh_key_path,
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
                default_ssh_user=self._default_ssh_user,
                ssh_key_path=self._ssh_key_path,
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
                default_ssh_user=self._default_ssh_user,
                ssh_key_path=self._ssh_key_path,
            )
            nodes.add(node)

        return nodes

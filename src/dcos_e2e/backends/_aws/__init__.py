"""
Helpers for creating and interacting with clusters on AWS.
"""

import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir
from typing import Optional  # noqa: F401
from typing import Any, Dict, Set, Type

from dcos_e2e._vendor.dcos_launch import config, get_launcher
from dcos_e2e._vendor.dcos_launch.aws import DcosCloudformationLauncher
from dcos_e2e._vendor.dcos_launch.onprem import AbstractOnpremLauncher
from dcos_e2e._vendor.dcos_launch.util import AbstractLauncher  # noqa: F401
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
        admin_location: str = '0.0.0.0/0',
        linux_distribution: Distribution = Distribution.CENTOS_7,
        workspace_dir: Optional[Path] = None,
    ) -> None:
        """
        Create a configuration for an AWS cluster backend.

        Args:
            admin_location: The IP address range from which the AWS nodes can
                be accessed.
            aws_region: The AWS location to create nodes in. See
                `Regions and Availability Zones`_.
            linux_distribution: The Linux distribution to boot DC/OS on.
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
                This is equivalent to `dir` in
                :py:func:`tempfile.mkstemp`.

        Attributes:
            admin_location: The IP address range from which the AWS nodes can
                be accessed.
            aws_region: The AWS location to create nodes in. See
                `Regions and Availability Zones`_.
            linux_distribution: The Linux distribution to boot DC/OS on.
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.

        Raises:
            NotImplementedError: In case an unsupported Linux distribution has
                been passed in at backend creation.

        .. _Regions and Availability Zones:
            https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html
        """
        supported_distributions = set(
            [
                Distribution.CENTOS_7,
                # Progress on COREOS support is tracked in JIRA:
                # https://jira.mesosphere.com/browse/DCOS-21954
            ],
        )

        if linux_distribution not in supported_distributions:
            message = (
                'The {distribution_name} Linux distribution is currently not '
                'supported by the AWS backend.'
            ).format(distribution_name=linux_distribution.name)
            raise NotImplementedError(message)

        self.workspace_dir = workspace_dir or Path(gettempdir())
        self.linux_distribution = linux_distribution
        self.aws_region = aws_region
        self.admin_location = admin_location

    @property
    def cluster_cls(self) -> Type['AWSCluster']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return AWSCluster


class AWSCluster(ClusterManager):
    # pylint: disable=super-init-not-called
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
        """
        Create an AWS cluster.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            files_to_copy_to_installer: Pairs of host paths to paths on the
                installer node. This must be empty as it is not currently
                supported.
            cluster_backend: Details of the specific AWS backend to use.

        Raises:
            NotImplementedError: ``files_to_copy_to_installer`` includes files
                to copy to the installer.
        """
        if files_to_copy_to_installer:
            # Copying files to the installer is not yet supported.
            # https://jira.mesosphere.com/browse/DCOS-21894
            message = (
                'Copying files to the installer is currently not supported by '
                'the AWS backend.'
            )
            raise NotImplementedError(message)

        unique = 'dcos-e2e-{}'.format(str(uuid.uuid4()))

        self._path = Path(cluster_backend.workspace_dir) / unique
        Path(self._path).mkdir(exist_ok=True)
        self._path = Path(self._path).resolve()
        self._path = Path(self._path) / unique
        Path(self._path).mkdir(exist_ok=True)

        ssh_user = {
            Distribution.CENTOS_7: 'centos',
            Distribution.COREOS: 'core',
        }
        self._default_ssh_user = ssh_user[cluster_backend.linux_distribution]

        self.cluster_backend = cluster_backend
        self.dcos_launcher = None  # type: Optional[AbstractLauncher]
        self.cluster_info = {}  # type: Dict[str, Any]

        aws_distros = {
            Distribution.CENTOS_7: 'cent-os-7-dcos-prereqs',
            Distribution.COREOS: 'coreos',
        }

        launch_config = {
            'admin_location': cluster_backend.admin_location,
            'aws_region': cluster_backend.aws_region,
            'deployment_name': unique,
            # Supply a valid URL to the preliminary config.
            # This is replaced later before the DC/OS installation.
            'installer_url': 'https://example.com',
            'instance_type': 'm4.large',
            'key_helper': True,
            'launch_config_version': 1,
            'num_masters': masters,
            'num_private_agents': agents,
            'num_public_agents': public_agents,
            'os_name': aws_distros[cluster_backend.linux_distribution],
            'platform': 'aws',
            'provider': 'onprem',
        }

        # Workaround for 1.9 as it will not work with ip_detect_public_filename
        # https://jira.mesosphere.com/browse/DCOS-21960
        detect_ip_public = '#!/bin/bash\ncurl fsSL http://169.254.169.254/latest/meta-data/public-ipv4'

        # First we create a preliminary dcos-config inside the
        # dcos-launch config to pass the config validation step.
        launch_config['dcos_config'] = {
            'cluster_name': unique,
            'resolvers': ['8.8.4.4', '8.8.8.8'],
            'master_discovery': 'static',
            'dns_search': 'mesos',
            'exhibitor_storage_backend': 'static',
            'ip_detect_public_contents': detect_ip_public.encode(),
        }

        # Validate the preliminary dcos-launch config.
        # This also fills in blanks in the dcos-launch config.
        validated_launch_config = config.get_validated_config(
            user_config=launch_config,
            config_dir=str(self._path),
        )

        # Get a OnpremLauncher object
        self.launcher = get_launcher(  # type: ignore
            config=validated_launch_config,
        )

        # Create the AWS stack from the DcosCloudformationLauncher.
        # Update ``cluster_info`` with the AWS SSH key information.
        self.cluster_info = self.launcher.create()

        # Store the generated AWS SSH key to the file system.
        self._ssh_key_path = self._path / 'id_rsa'
        private_key = self.cluster_info['ssh_private_key']
        Path(self._ssh_key_path).write_bytes(private_key.encode())

        # Wait for the AWS stack setup completion.
        DcosCloudformationLauncher.wait(self.launcher)  # type: ignore

        # Update the cluster_info with AWS stack information:
        # ``describe`` fetches the latest information for the stack.
        # This makes node IP addresses available to ``cluster_info``.
        # This also inserts bootstrap node information into ``cluster_info``.
        self.cluster_info = AbstractOnpremLauncher.describe(  # type: ignore
            self.launcher,
        )

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a URL.

        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            extra_config: This may contain extra installation configuration
                variables that are applied on top of the default DC/OS
                configuration of the AWS backend.
            log_output_live: If ``True``, log output of the installation live.
        """

        # In order to install DC/OS with the preliminary dcos-launch
        # config the ``build_artifact`` URL is overwritten.
        self.launcher.config['installer_url'] = build_artifact

        # The DC/OS config parameters from ``extra_config`` are applied
        # on top of the preliminary DC/OS config.
        dcos_config = self.launcher.config['dcos_config']
        self.launcher.config['dcos_config'] = {**dcos_config, **extra_config}

        # The ``wait`` method starts the actual DC/OS installation process.
        # We do not use ``self.launcher.wait()`` here because at the time of
        # writing it does both, waiting for the AWS stack and installing
        # DC/OS. This is desired to be changed by the dcos-launch team.
        # https://jira.mesosphere.com/browse/DCOS-21660
        AbstractOnpremLauncher.wait(self.launcher)  # type: ignore

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Install DC/OS from a given build artifact. This is not supported and
        simply raises a his is not supported and simply raises a
        ``NotImplementedError``.

        Args:
            build_artifact: The ``Path`` to a build artifact to install DC/OS
                from.
            extra_config: May contain extra installation configuration
                variables that are applied on top of the default DC/OS
                configuration of the AWS backend.
            log_output_live: If ``True``, log output of the installation live.

        Raises:
            NotImplementedError: ``NotImplementedError`` because the AWS
                backend does not support the DC/OS advanced installation
                method.
        """
        message = (
            'The AWS backend does not support the installation of build '
            'artifacts passed via path. This is because a more efficient'
            'installation method exists in ``install_dcos_from_url``.'
        )
        raise NotImplementedError(message)

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        # Deletion only works if valid AWS credentials are present. This
        # a problem if temporary credentials become invalid before
        # destroying a cluster because the generated AWS KeyPair persists.
        # https://jira.mesosphere.com/browse/DCOS-21893
        self.launcher.delete()

        rmtree(path=str(self._path), ignore_errors=True)

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master :class:`.node.Node` s.
        """
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
        """
        Return all DC/OS agent :class:`.node.Node` s.
        """
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
        """
        Return all DC/OS public agent :class:`.node.Node` s.
        """
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

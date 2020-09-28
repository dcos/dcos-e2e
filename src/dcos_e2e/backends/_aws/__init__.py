"""
Helpers for creating and interacting with clusters on AWS.
"""

import stat
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir
from typing import Any, Dict, Iterable, Optional, Set, Tuple, Type

import boto3

from dcos_e2e._vendor.dcos_launch import config, get_launcher
from dcos_e2e._vendor.dcos_launch.util import AbstractLauncher  # noqa: F401
from dcos_e2e.base_classes import ClusterBackend, ClusterManager
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.node import Node, Output


class AWS(ClusterBackend):
    """
    A record of an AWS backend which can be used to create clusters.
    """

    def __init__(
        self,
        aws_instance_type: str = 'm4.large',
        aws_region: str = 'us-west-2',
        admin_location: str = '0.0.0.0/0',
        linux_distribution: Distribution = Distribution.CENTOS_7,
        workspace_dir: Optional[Path] = None,
        aws_key_pair: Optional[Tuple[str, Path]] = None,
        aws_cloudformation_stack_name: Optional[str] = None,
        ec2_instance_tags: Optional[Dict[str, str]] = None,
        master_ec2_instance_tags: Optional[Dict[str, str]] = None,
        agent_ec2_instance_tags: Optional[Dict[str, str]] = None,
        public_agent_ec2_instance_tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Create a configuration for an AWS cluster backend.

        Args:
            admin_location: The IP address range from which the AWS nodes can
                be accessed.
            aws_instance_type: The AWS instance type to use.
                See `Instance types`_.
            aws_region: The AWS location to create nodes in. See
                `Regions and Availability Zones`_.
            linux_distribution: The Linux distribution to boot DC/OS on.
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
                This is equivalent to `dir` in
                :py:func:`tempfile.mkstemp`.
            aws_key_pair: An optional tuple of (name, path) where the name is
                the identifier of an existing SSH public key on AWS KeyPairs
                and the path is the local path to the corresponding private
                key. The private key can then be used to connect to the
                cluster. If this is not given, a new key pair will be
                generated.
            aws_cloudformation_stack_name: The name of the CloudFormation stack
                to create. If this is not given, a random string is used.
            ec2_instance_tags: Tags to add to the cluster node EC2 instances.
            master_ec2_instance_tags: Tags to add to the cluster master node
                EC2 instances.
            agent_ec2_instance_tags: EC2 tags to add to the cluster agent node
                EC2 instances.
            public_agent_ec2_instance_tags: EC2 tags to add to the cluster
                public agent node EC2 instances.

        Attributes:
            admin_location: The IP address range from which the AWS nodes can
                be accessed.
            aws_instance_type: The AWS instance type to use.
                See `Instance types`_.
            aws_region: The AWS location to create nodes in. See
                `Regions and Availability Zones`_.
            linux_distribution: The Linux distribution to boot DC/OS on.
            workspace_dir: The directory in which large temporary files will be
                created. These files will be deleted at the end of a test run.
            aws_key_pair: An optional tuple of (name, path) where the name is
                the identifier of an existing SSH public key on AWS KeyPairs
                and the path is the local path to the corresponding private
                key. The private key can then be used to connect to the
                cluster.
            aws_cloudformation_stack_name: The name of the CloudFormation stack
                to create.
            ec2_instance_tags: Tags to add to the cluster node EC2 instances.
            master_ec2_instance_tags: Tags to add to the cluster master node
                EC2 instances.
            agent_ec2_instance_tags: EC2 tags to add to the cluster agent node
                EC2 instances.
            public_agent_ec2_instance_tags: EC2 tags to add to the cluster
                public agent node EC2 instances.

        Raises:
            NotImplementedError: In case an unsupported Linux distribution has
                been passed in at backend creation.

        .. _Regions and Availability Zones:
            https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html
        .. _Instance types:
            https://aws.amazon.com/ec2/instance-types
        """
        supported_distributions = set(
            [
                Distribution.CENTOS_7,
                Distribution.RHEL_7,
                # Support for Ubuntu is blocked on
                # https://jira.d2iq.com/browse/DCOS_OSS-3876.
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
        self.aws_instance_type = aws_instance_type
        self.admin_location = admin_location
        self.aws_key_pair = aws_key_pair
        self.aws_cloudformation_stack_name = aws_cloudformation_stack_name
        self.ec2_instance_tags = ec2_instance_tags or {}
        self.master_ec2_instance_tags = master_ec2_instance_tags or {}
        self.agent_ec2_instance_tags = agent_ec2_instance_tags or {}
        self.public_agent_ec2_instance_tags = (
            public_agent_ec2_instance_tags or {}
        )

    @property
    def cluster_cls(self) -> Type['AWSCluster']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return AWSCluster

    @property
    def ip_detect_path(self) -> Path:
        """
        Return the path to the AWS specific ``ip-detect`` script.
        """
        current_parent = Path(__file__).parent.resolve()
        return current_parent / 'resources' / 'ip-detect'

    @property
    def base_config(self) -> Dict[str, Any]:
        """
        Return a base configuration for installing DC/OS OSS.
        """
        return {
            'cluster_name': 'DCOS',
            'exhibitor_storage_backend': 'static',
            'master_discovery': 'static',
            'platform': 'aws',
            'resolvers': ['10.10.0.2', '8.8.8.8'],
            'rexray_config_preset': 'aws',
        }


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
        cluster_backend: AWS,
    ) -> None:
        """
        Create an AWS cluster.

        Args:
            masters: The number of master nodes to create.
            agents: The number of agent nodes to create.
            public_agents: The number of public agent nodes to create.
            cluster_backend: Details of the specific AWS backend to use.

        """
        unique = 'dcos-e2e-{random}'.format(random=str(uuid.uuid4()))

        self._path = cluster_backend.workspace_dir / unique
        self._path.mkdir(exist_ok=True)
        self._path = self._path.resolve() / unique
        self._path.mkdir(exist_ok=True)
        self._ip_detect_path = cluster_backend.ip_detect_path

        ssh_user = {
            Distribution.CENTOS_7: 'centos',
            Distribution.RHEL_7: 'ec2-user',
        }

        install_prereqs = {
            # There is a bug hit when using ``install_prereqs`` with some
            # distributions.
            # See https://jira.d2iq.com/browse/DCOS-40894.
            Distribution.CENTOS_7:
            False,
            Distribution.RHEL_7:
            False,
        }[cluster_backend.linux_distribution]

        prereqs_script_filename = {
            Distribution.CENTOS_7: 'install_prereqs.sh',
            Distribution.RHEL_7: 'install_prereqs.sh',
        }[cluster_backend.linux_distribution]
        self._default_user = ssh_user[cluster_backend.linux_distribution]

        self.cluster_backend = cluster_backend
        self.dcos_launcher = None  # type: Optional[AbstractLauncher]

        aws_distros = {
            Distribution.CENTOS_7: 'cent-os-7-dcos-prereqs',
            Distribution.RHEL_7: 'rhel-7-dcos-prereqs',
        }

        deployment_name = (
            cluster_backend.aws_cloudformation_stack_name or unique
        )
        launch_config = {
            'admin_location': cluster_backend.admin_location,
            'aws_region': cluster_backend.aws_region,
            'deployment_name': deployment_name,
            # Supply a valid URL to the preliminary config.
            # This is replaced later before the DC/OS installation.
            'installer_url': 'https://example.com',
            'instance_type': cluster_backend.aws_instance_type,
            'launch_config_version': 1,
            'num_masters': masters,
            'num_private_agents': agents,
            'num_public_agents': public_agents,
            'os_name': aws_distros[cluster_backend.linux_distribution],
            'platform': 'aws',
            'provider': 'onprem',
            'install_prereqs': install_prereqs,
            'prereqs_script_filename': prereqs_script_filename,
        }

        if cluster_backend.aws_key_pair is None:
            launch_config['key_helper'] = True
        else:
            aws_key_name, local_key_path = cluster_backend.aws_key_pair
            launch_config['ssh_private_key_filename'] = str(local_key_path)
            launch_config['aws_key_name'] = aws_key_name

        # First we create a preliminary dcos-config inside the
        # dcos-launch config to pass the config validation step.
        launch_config['dcos_config'] = self.cluster_backend.base_config

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
        # Get the AWS SSH key information from this.
        cluster_create_info = self.launcher.create()
        private_key = cluster_create_info['ssh_private_key']

        # Store the generated AWS SSH key to the file system.
        self._ssh_key_path = self._path / 'id_rsa'
        self._ssh_key_path.write_bytes(private_key.encode())
        self._ssh_key_path.chmod(mode=stat.S_IRUSR)

        # Wait for the AWS stack setup completion.
        self.launcher.wait()

        # Update the cluster_info with AWS stack information:
        # ``describe`` fetches the latest information for the stack.
        # This makes node IP addresses available to ``cluster_info``.
        # This also inserts bootstrap node information into ``cluster_info``.
        self.cluster_info = self.launcher.describe()
        ec2 = boto3.resource('ec2', region_name=cluster_backend.aws_region)

        for nodes, tags in (
            (self.masters, cluster_backend.master_ec2_instance_tags),
            (self.agents, cluster_backend.agent_ec2_instance_tags),
            (
                self.public_agents,
                cluster_backend.public_agent_ec2_instance_tags,
            ),
        ):
            node_public_ips = set(
                str(node.public_ip_address) for node in nodes
            )
            ec2_instances = ec2.instances.filter(
                Filters=[
                    {
                        'Name': 'ip-address',
                        'Values': list(node_public_ips),
                    },
                ],
            )
            instance_ids = [instance.id for instance in ec2_instances]

            node_tags = {**cluster_backend.ec2_instance_tags, **tags}

            if not nodes:
                continue

            if not node_tags:
                continue

            ec2_tags = [
                {
                    'Key': key,
                    'Value': value,
                } for key, value in node_tags.items()
            ]

            ec2.create_tags(Resources=instance_ids, Tags=ec2_tags)

    def install_dcos_from_url(
        self,
        dcos_installer: str,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]],
    ) -> None:
        """
        Install DC/OS from a URL.

        Args:
            dcos_installer: The URL string to an installer to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The path to an ``ip-detect`` script to be used
                during the DC/OS installation.
            output: What happens with stdout and stderr.
            files_to_copy_to_genconf_dir: Pairs of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS.
        """
        new_ip_detect_given = bool(ip_detect_path != self._ip_detect_path)
        if new_ip_detect_given or files_to_copy_to_genconf_dir:
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
            return

        # In order to install DC/OS with the preliminary dcos-launch
        # config the ``dcos_installer`` URL is overwritten.
        self.launcher.config['installer_url'] = dcos_installer
        self.launcher.config['dcos_config'] = dcos_config
        self.launcher.install_dcos()

    def install_dcos_from_path(
        self,
        dcos_installer: Path,
        dcos_config: Dict[str, Any],
        ip_detect_path: Path,
        output: Output,
        files_to_copy_to_genconf_dir: Iterable[Tuple[Path, Path]] = (),
    ) -> None:
        """
        Install DC/OS from a given installer with a bootstrap node.

        Args:
            dcos_installer: The ``Path`` to an installer to install DC/OS
                from.
            dcos_config: The DC/OS configuration to use.
            ip_detect_path: The path to an ``ip-detect`` script to be used
                during the DC/OS installation.
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
            files_to_copy_to_genconf_dir=files_to_copy_to_genconf_dir,
            output=output,
        )

    def destroy_node(self, node: Node) -> None:
        """
        Destroy a nodes in the cluster. This is not implemented.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        # Deletion only works if valid AWS credentials are present. This
        # a problem if temporary credentials become invalid before
        # destroying a cluster because the generated AWS KeyPair persists.
        # https://jira.d2iq.com/browse/DCOS-21893
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
                default_user=self._default_user,
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
                default_user=self._default_user,
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
                default_user=self._default_user,
                ssh_key_path=self._ssh_key_path,
            )
            nodes.add(node)

        return nodes

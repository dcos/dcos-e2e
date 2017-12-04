"""
Helpers for interacting with the AWS backend.
"""

import logging
import uuid
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Type
from tempfile import TemporaryDirectory
import itertools
import stat
import pkg_resources
import yaml

from dcos_e2e.backends._aws import aws
from dcos_e2e.backends._base_classes import ClusterBackend, ClusterManager
from dcos_e2e.node import Node
from dcos_test_utils import onprem, ssh_client
from dcos_test_utils.helpers import Host

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=logging-format-interpolation

# Amazon Machine Images for cent-os-7-dcos-prereqs
AMIS = {
    'ap-northeast-1': 'ami-1d50567a',
    'ap-southeast-1': 'ami-f4a12097',
    'ap-southeast-2': 'ami-0d50476e',
    'eu-central-1': 'ami-d47fa4bb',
    'eu-west-1': 'ami-b6c8ded0',
    'sa-east-1': 'ami-41640d2d',
    'us-east-1': 'ami-5f5d1449',
    'us-west-1': 'ami-54614234',
    'us-west-2': 'ami-61acce01'
}


class AWS(ClusterBackend):  # pylint: disable=invalid-name
    """
    A record of an AWS backend which can be used to create clusters.
    """

    #  pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        admin_location: str,
        instance_type: str,
        deploy_timeout: int = 60,
        workspace_dir: Optional[Path] = None,
    ) -> None:
        """
        Create a configuration for an AWS backend.

        Args:
            aws_region: Region to create Amazon Web Service clusters in.
            aws_access_key_id: Amazon Web Service Access Key ID.
            aws_secret_access_key: Amazon Web Service Secret Access Key.
            admin_location: IP address range of the hosts that can communicate
                with the clusters created by this backend, defaults to all.
            instance_type: Amazon Web Services Instance Type.
            deploy_timeout: Time until clusters of this backend are destroyed.
            workspace_dir: Directory to store temporary files in.

        Attributes:
            workspace_dir: Directory to store temporary files in.
        """
        self.workspace_dir = workspace_dir

        # The AWS backend uses the cent-os-7-dcos-prereqs disk image
        self._instance_ami = AMIS[aws_region]
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key

        self._admin_location = admin_location
        self._instance_type = instance_type
        self._deploy_timeout = deploy_timeout

        self._boto_wrapper = aws.BotoWrapper(
            aws_region, aws_access_key_id, aws_secret_access_key
        )

    def create_stack(
        self,
        deployment_name: str,
        cluster_size: int,
        aws_key_name: str,
    ) -> aws.CloudFormationStack:
        """
        Create a cluster stack on AWS using the given parameters.

        Args:
            deployment_name: Name identifier of the stack on AWS.
            cluster_size: Number of total hosts for the DC/OS deployment.
            aws_key_name: Name of a key pair stored on AWS that will be
                used to access nodes via SSH.
        """
        try:
            stack = self._boto_wrapper.create_bare_dcos_stack(
                stack_name=deployment_name,
                instance_type=self._instance_type,
                instance_ami=self._instance_ami,
                cluster_size=cluster_size,
                aws_key_name=aws_key_name,
                admin_location=self._admin_location,
                deploy_timeout=self._deploy_timeout,
            )
        except Exception as ex:
            raise aws.AWSError('AWSError', None) from ex

        cf_stack = aws.CloudFormationStack(stack.stack_id, self._boto_wrapper)

        cf_stack.wait_for_complete(
            transition_states=[
                'CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS',
                'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'
            ],
            end_states=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
        )
        return cf_stack

    def create_keypair(self, key_name: str) -> str:
        """
        Create a public/private key pair with key_name on AWS.
        Return private key material as a string.
        """
        return str(self._boto_wrapper.create_key_pair(key_name))

    def delete_keypair(self, key_name: str) -> None:
        """
        Delete a public/private key pair identified by key_name.
        """
        self._boto_wrapper.delete_key_pair(key_name)

    @property
    def cluster_cls(self) -> Type['AWSCluster']:
        """
        Return the `ClusterManager` class to use to create and manage a
        cluster.
        """
        return AWSCluster

    @property
    def supports_destruction(self) -> bool:
        """
        AWS clusters can be destroyed.
        """
        return True

    @property
    def default_ssh_user(self) -> str:
        """
        Return the default SSH user for cent-os-7-dcos-prereqs.
        """
        return 'centos'


class AWSCluster(ClusterManager):
    """
    A record of a AWS Cloudformation DC/OS cluster.
    """

    #  pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=super-init-not-called
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
            files_to_copy_to_installer: A mapping of host paths to paths on
                the installer node. These are files to copy from the host to
                the installer node before installing DC/OS. Currently
                this function is not supported for the AWS backend.
            cluster_backend: Details of the specific Docker backend to use.
        """

        self._aws_backend = cluster_backend

        unique = 'dcos-e2e-{random}'.format(random=uuid.uuid4())

        self._tmp_dir = TemporaryDirectory(
            suffix=unique,
            dir=(
                str(cluster_backend.workspace_dir)
                if cluster_backend.workspace_dir else None
            ),
        )

        tmp_dir = Path(self._tmp_dir.name).resolve()

        stack_name = unique
        self._aws_key_name = stack_name
        self._ssh_private_key = self._aws_backend.create_keypair(
            self._aws_key_name
        )

        ssh_key_path = Path(tmp_dir / 'id_rsa')
        ssh_key_path.write_bytes(data=self._ssh_private_key.encode('utf-8'))
        ssh_key_path.chmod(mode=stat.S_IRUSR)

        cluster_size = masters + agents + public_agents

        self._cf_stack = self._aws_backend.create_stack(
            deployment_name=stack_name,
            cluster_size=cluster_size,
            aws_key_name=self._aws_key_name,
        )

        bootstrap_host = self._cf_stack.get_bootstrap_host()
        cluster_hosts = self._cf_stack.get_cluster_hosts()

        cluster_hosts_iter = iter(cluster_hosts)

        master_hosts = list(itertools.islice(cluster_hosts_iter, masters))
        agent_hosts = list(itertools.islice(cluster_hosts_iter, agents))
        public_agent_hosts = list(
            itertools.islice(cluster_hosts_iter, public_agents)
        )

        def nodes_from_hosts(hosts: Iterable[Host]) -> Set[Node]:
            return set(
                [
                    Node(
                        ip_address=IPv4Address(host.public_ip),
                        ssh_key_path=ssh_key_path,
                        private_ip_address=IPv4Address(host.private_ip),
                    ) for host in hosts
                ]
            )

        self._bootstrap_host = Node(
            ip_address=IPv4Address(bootstrap_host.public_ip),
            ssh_key_path=ssh_key_path,
            private_ip_address=IPv4Address(bootstrap_host.private_ip),
        )

        self._masters = nodes_from_hosts(master_hosts)
        self._agents = nodes_from_hosts(agent_hosts)
        self._public_agents = nodes_from_hosts(public_agent_hosts)

        self._default_ssh_user = self._aws_backend.default_ssh_user

    def install_dcos_from_path(
        self,
        build_artifact: Path,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Args:
            build_artifact: The `Path` to a build artifact to install DC/OS
                from.
            extra_config: May contain extra installation configuration
                variables that are applied on top of the default DC/OS
                configuration of the AWS backend.
            log_output_live: If `True`, log output of the installation live.

        Raises:
            NotImplementedError: `NotImplementedError` because the AWS
                backend can be utilized more efficiently by installing DC/OS
                from from a URL using the advanced installation method.
        """
        message = (
            'The AWS backend does not support the installing DC/OS from '
            'a build artifact on the file system. This is due a more '
            'efficient method existing in `install_dcos_from_url`.'
        )
        raise NotImplementedError(message)

    def install_dcos_from_url(
        self,
        build_artifact: str,
        extra_config: Dict[str, Any],
        log_output_live: bool,
    ) -> None:
        """
        Args:
            build_artifact: The URL string to a build artifact to install DC/OS
                from.
            extra_config: This may contain extra installation configuration
                variables that are applied on top of the default DC/OS
                configuration of the AWS backend.
            log_output_live: If `True`, log output of the installation live.
        """
        ssh_user = self._default_ssh_user

        config = {
            'cluster_name':
            self._cf_stack.stack_id,
            'resolvers': ['8.8.8.8'],
            'dns_search':
            'mesos',
            'exhibitor_storage_backend':
            'static',
            'master_discovery':
            'static',
            'ssh_key':
            self._ssh_private_key,
            'ssh_user':
            ssh_user,
            'master_list': [str(n.private_ip_address) for n in self.masters],
            'agent_list': [str(n.private_ip_address) for n in self.agents],
            'public_agent_list':
            [str(n.private_ip_address) for n in self.public_agents],
        }

        config['ip_detect_script'] = pkg_resources.resource_string(
            'dcos_e2e.backends._aws', 'resources/ip-detect/aws.sh'
        ).decode()

        config['ip_detect_public_contents'] = yaml.dump(
            pkg_resources.resource_string(
                'dcos_e2e.backends._aws', 'resources/ip-detect/aws_public.sh'
            ).decode()
        )

        config['fault_domain_detect_contents'] = yaml.dump(
            pkg_resources.resource_string(
                'dcos_e2e.backends._aws',
                'resources/fault-domain-detect/aws.sh'
            ).decode()
        )

        config = {**config, **extra_config}

        log.info('Cluster config: {config}'.format(config=config))

        # Parameters must match the AWS templates
        installer_port = 9000
        ssh_port = 22

        client = ssh_client.SshClient(
            ssh_user,
            self._ssh_private_key,
        )

        log.info('Waiting for SSH connectivity to cluster host...')
        for node in {
            *set([self._bootstrap_host]), *self.masters, *self.agents,
            *self.public_agents
        }:
            client.wait_for_ssh_connection(str(node.ip_address), ssh_port)

        installer = onprem.DcosInstallerApiSession.api_session_from_host(
            ssh_client=client,
            host=str(self._bootstrap_host.ip_address),
            installer_url=build_artifact,
            offline_mode=False,
            port=installer_port,
        )

        state_file = 'LAST_COMPLETED_STAGE'

        def post_state(state: str) -> None:
            self._bootstrap_host.run(
                args=['printf', state, '>', state_file],
                user=ssh_user,
                log_output_live=log_output_live,
            )

        last_complete = 'SETUP'
        post_state(last_complete)
        if last_complete == 'SETUP':
            last_complete = 'GENCONF'
            installer.genconf(config)
            post_state(last_complete)
        if last_complete == 'GENCONF':
            installer.preflight()
            last_complete = 'PREFLIGHT'
            post_state(last_complete)
        if last_complete == 'PREFLIGHT':
            installer.deploy()
            last_complete = 'DEPLOY'
            post_state(last_complete)
        if last_complete == 'DEPLOY':
            installer.postflight()
            last_complete = 'POSTFLIGHT'
            post_state(last_complete)
        if last_complete != 'POSTFLIGHT':
            raise aws.AWSError(
                'InconsistentState',
                'State on bootstrap host is: ' + last_complete
            )

    def destroy(self) -> None:
        """
        Destroy all nodes in the cluster.
        """
        self._cf_stack.delete()
        self._aws_backend.delete_keypair(self._aws_key_name)

    @property
    def masters(self) -> Set[Node]:
        """
        Return all DC/OS master ``Node``s.
        """
        return self._masters

    @property
    def agents(self) -> Set[Node]:
        """
        Return all DC/OS agent ``Node``s.
        """
        return self._agents

    @property
    def public_agents(self) -> Set[Node]:
        """
        Return all DC/OS public agent ``Node``s.
        """
        return self._public_agents

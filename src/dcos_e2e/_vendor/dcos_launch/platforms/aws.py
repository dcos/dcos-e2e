""" Abstractions for handling resources via Amazon Web Services (AWS) API

The intention of these utilities is to allow other infrastructure to
interact with AWS without having to understand AWS APIs. Additionally,
this module provides helper functions for the most common queries required
to manipulate and test a DC/OS cluster, which would be otherwise cumbersome
to do with AWS API calls only

BotoWrapper: AWS credentials and region bound to various helper methods
CfStack: Generic representation of a CloudFormation stack
DcosCfStack: Represents DC/OS in a simple deployment
DcosZenCfStack: Represents DC/OS  deployed from a zen template
MasterStack: thin wrapper for master stack in a zen template
PrivateAgentStack: thin wrapper for public agent stack in a zen template
PublicAgentStack: thin wrapper for public agent stack in a zen template
BareClusterCfStack: Represents a homogeneous cluster of hosts with a specific AMI
"""
import copy
import logging
import os

import boto3
import pkg_resources
from botocore.exceptions import ClientError, WaiterError
from retrying import retry

from ... import dcos_launch
from ...dcos_test_utils.helpers import Host, SshInfo

log = logging.getLogger(__name__)


def template_by_instance_type(instance_type):
    if instance_type.split('.')[0] in ('c4', 't2', 'm4'):
        template = pkg_resources.resource_string(dcos_launch.__name__, 'templates/vpc-ebs-only-cluster-template.json')
    else:
        template = pkg_resources.resource_string(dcos_launch.__name__, 'templates/vpc-cluster-template.json')
    return template.decode('utf-8')


def param_dict_to_aws_format(user_parameters):
    return [{'ParameterKey': str(k), 'ParameterValue': str(v)} for k, v in user_parameters.items()]


def tag_dict_to_aws_format(tag_dict: dict):
    return [{'Key': k, 'Value': v} for k, v in tag_dict.items()]


def retry_on_rate_limiting(e: Exception):
    """ Returns 'True' if a rate limiting error occurs and raises the exception otherwise
    """
    if isinstance(e, ClientError):
        error_code = e.response['Error']['Code']
    elif isinstance(e, WaiterError):
        error_code = e.last_response['Error']['Code']
    else:
        raise e
    if error_code in ['Throttling', 'RequestLimitExceeded']:
        log.warning('AWS API Limiting error: {}'.format(error_code))
        return True
    raise e


@retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000, retry_on_exception=retry_on_rate_limiting)
def instances_to_hosts(instances):
    return [Host(i.private_ip_address, i.public_ip_address) for i in instances]


@retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000, retry_on_exception=retry_on_rate_limiting)
def fetch_stack(stack_name, boto_wrapper):
    log.debug('Attemping to fetch AWS Stack: {}'.format(stack_name))
    stack = boto_wrapper.resource('cloudformation').Stack(stack_name)
    for resource in stack.resource_summaries.all():
        if resource.logical_resource_id == 'MasterStack':
            log.debug('Using Zen DC/OS Cloudformation interface')
            return DcosZenCfStack(stack_name, boto_wrapper)
        if resource.logical_resource_id == 'MasterServerGroup':
            log.debug('Using Basic DC/OS Cloudformation interface')
            return DcosCfStack(stack_name, boto_wrapper)
        if resource.logical_resource_id == 'BareServerAutoScale':
            log.debug('Using Bare Cluster Cloudformation interface')
            return BareClusterCfStack(stack_name, boto_wrapper)
    log.warning('No recognized resources found; using generic stack')
    return CfStack(stack_name, boto_wrapper)


class BotoWrapper:
    def __init__(self, region):
        self.region = region
        self.session = boto3.session.Session()

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def client(self, name):
        return self.session.client(service_name=name, region_name=self.region)

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def resource(self, name, region=None):
        region = self.region if region is None else region
        return self.session.resource(service_name=name, region_name=region)

    def create_key_pair(self, key_name):
        """Returns private key of newly generated pair
        """
        log.info('Creating KeyPair: {}'.format(key_name))
        key = self.client('ec2').create_key_pair(KeyName=key_name)
        return key['KeyMaterial']

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def get_service_resources(self, service, resource_name):
        """Return resources and boto wrapper in every region for the given boto3 service and resource type."""
        for region in aws_region_names:
            # line below is needed because function get_all_stacks needs to copy the boto wrapper with the correct
            # region when initializing each CfStack object
            self.region = region['id']
            # It is common to have access to an account, but not all regions. In that case, we still want to be able
            # to pull whatever resources we can from the regions we have access to
            try:
                yield from getattr(self.resource(service, region['id']), resource_name).all()
            except ClientError as e:
                if e.response['Error']['Code'] == 'UnauthorizedOperation':
                    log.error("Failed getting resources ({}) for region {} with exception: {}".format(
                        resource_name, self.region, repr(e)))
                else:
                    raise e

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def get_all_stacks(self):
        """Get all AWS CloudFormation stacks in all regions."""
        for stack in self.get_service_resources('cloudformation', 'stacks'):
            yield CfStack(stack.stack_name, copy.deepcopy(self))

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def get_all_buckets(self):
        """Get all S3 buckets in all regions."""
        yield from self.get_service_resources('s3', 'buckets')

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def get_all_keypairs(self):
        """Get all EC2 key pairs in all regions."""
        yield from self.get_service_resources('ec2', 'key_pairs')

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def delete_key_pair(self, key_name):
        log.info('Deleting KeyPair: {}'.format(key_name))
        self.resource('ec2').KeyPair(key_name).delete()

    def create_stack(
            self,
            name: str,
            parameters: dict,
            template_url: str=None,
            template_body: str=None,
            deploy_timeout: int=60,
            disable_rollback: bool=False,
            tags=None):
        """Pulls template and checks user params versus temlate params.
        Does simple casting of strings or numbers
        Starts stack creation if validation is successful
        """
        log.info('Requesting AWS CloudFormation: {}'.format(name))
        role_arn = os.getenv('DCOS_LAUNCH_ROLE_ARN')
        args = {
            'StackName': name,
            'DisableRollback': disable_rollback,
            'TimeoutInMinutes': deploy_timeout,
            'Capabilities': ['CAPABILITY_IAM'],
            # this python API only accepts data in string format; cast as string here
            # so that we may pass parameters directly from yaml (which parses numbers as non-strings)
            'Parameters': param_dict_to_aws_format(parameters)}
        if template_body is not None:
            assert template_url is None, 'tempate_body and template_url cannot be supplied simultaneously'
            args['TemplateBody'] = template_body
        else:
            assert template_url is not None, 'template_url must be set if template_body is not provided'
            args['TemplateURL'] = template_url
        if tags is not None:
            args['Tags'] = tag_dict_to_aws_format(tags)
        if role_arn is not None:
            log.info('Passing effective role as per DCOS_LAUNCH_ROLE_ARN')
            args['RoleARN'] = role_arn
        return self.resource('cloudformation').create_stack(**args)

    def create_vpc_tagged(self, cidr, name_tag):
        ec2 = self.client('ec2')
        log.info('Creating new VPC...')
        vpc_id = ec2.create_vpc(CidrBlock=cidr, InstanceTenancy='default')['Vpc']['VpcId']
        ec2.get_waiter('vpc_available').wait(VpcIds=[vpc_id])
        ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': name_tag}])
        log.info('Created VPC with ID: {}'.format(vpc_id))
        return vpc_id

    def create_internet_gateway_tagged(self, vpc_id, name_tag):
        ec2 = self.client('ec2')
        log.info('Creating new InternetGateway...')
        gateway_id = ec2.create_internet_gateway()['InternetGateway']['InternetGatewayId']
        ec2.attach_internet_gateway(InternetGatewayId=gateway_id, VpcId=vpc_id)
        ec2.create_tags(Resources=[gateway_id], Tags=[{'Key': 'Name', 'Value': name_tag}])
        log.info('Created internet gateway with ID: {}'.format(gateway_id))
        return gateway_id

    def create_subnet_tagged(self, vpc_id, cidr, name_tag):
        ec2 = self.client('ec2')
        log.info('Creating new Subnet...')
        subnet_id = ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr)['Subnet']['SubnetId']
        ec2.create_tags(Resources=[subnet_id], Tags=[{'Key': 'Name', 'Value': name_tag}])
        ec2.get_waiter('subnet_available').wait(SubnetIds=[subnet_id])
        log.info('Created subnet with ID: {}'.format(subnet_id))
        return subnet_id

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def delete_subnet(self, subnet_id):
        log.info('Deleting subnet: {}'.format(subnet_id))
        self.client('ec2').delete_subnet(SubnetId=subnet_id)

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def delete_internet_gateway(self, gateway_id):
        ig = self.resource('ec2').InternetGateway(gateway_id)
        for vpc in ig.attachments:
            vpc_id = vpc['VpcId']
            log.info('Detaching gateway {} from vpc {}'.format(gateway_id, vpc_id))
            ig.detach_from_vpc(VpcId=vpc_id)
        log.info('Deleting internet gateway: {}'.format(gateway_id))
        ig.delete()

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def delete_vpc(self, vpc_id):
        log.info('Deleting vpc: {}'.format(vpc_id))
        self.client('ec2').delete_vpc(VpcId=vpc_id)

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def get_auto_scaling_instances(self, asg_physical_resource_id):
        """ Returns instance objects as described here:
        http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#instance
        """
        ec2 = self.resource('ec2')
        return [ec2.Instance(i['InstanceId']) for asg in self.client('autoscaling').
                describe_auto_scaling_groups(
                    AutoScalingGroupNames=[asg_physical_resource_id])
                ['AutoScalingGroups'] for i in asg['Instances']]

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def empty_and_delete_bucket(self, bucket_id):
        """ Buckets must be empty to be deleted. Additionally, there is no high-level
        method to check if buckets exist, so the try/except statement is required
        """
        try:
            # just check to see if the head is accessible before continuing
            self.resource('s3').meta.client.head_bucket(Bucket=bucket_id)
            bucket = self.resource('s3').Bucket(bucket_id)
        except ClientError:
            log.exception('Bucket could not be fetched')
            log.warning('S3 bucket not found when expected during delete, moving on...')
            return
        log.info('Starting bucket {} deletion'.format(bucket))
        for obj in bucket.objects.all():
            obj.delete()
        log.info('Trying deleting bucket {} itself'.format(bucket))
        bucket.delete()


class CfStack:
    def __init__(self, stack_name, boto_wrapper):
        self.boto_wrapper = boto_wrapper
        self.stack = self.boto_wrapper.resource('cloudformation').Stack(stack_name)

    @property
    def name(self):
        return self.stack.stack_name

    def wait_for_complete(self, transition_states: list, end_states: list) -> str:
        """
        Note: Do not use unwrapped boto waiter class, it has very poor error handling

        Stacks can have one of the following statuses. See:
        http://boto3.readthedocs.io/en/latest/reference/
        services/cloudformation.html#CloudFormation.Client.describe_stacks

        CREATE_IN_PROGRESS, CREATE_FAILED, CREATE_COMPLETE
        ROLLBACK_IN_PROGRESS, ROLLBACK_FAILED, ROLLBACK_COMPLETE
        DELETE_IN_PROGRESS, DELETE_FAILED, DELETE_COMPLETE
        UPDATE_IN_PROGRESS, UPDATE_COMPLETE_CLEANUP_IN_PROGRESS
        UPDATE_COMPLETE, UPDATE_ROLLBACK_IN_PROGRESS
        UPDATE_ROLLBACK_FAILED, UPDATE_ROLLBACK_COMPLETE
        UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS

        :param transition_states: as long as the current state is in one of these, the wait continues
        :param end_states: when the current state becomes one of these, the wait stops as the operation completed

        """
        log.info('Waiting for stack operation to complete')

        # wait for 60 seconds before retry
        @retry(wait_fixed=60 * 1000, retry_on_result=lambda result: result is None, retry_on_exception=lambda ex: False)
        def wait_loop():
            self.refresh_stack()
            stack_status = self.get_status()
            if stack_status in end_states:
                log.info("Final stack status: " + stack_status)
                return stack_status
            log.info("Stack status {status}. Continuing to wait... ".format(status=stack_status))
            if stack_status not in transition_states:
                for event in self.get_stack_events():
                    log.error('Stack Events: {}'.format(event))
                raise Exception('StackStatus changed unexpectedly to: {}'.format(stack_status))

        status = wait_loop()

        return status

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def get_stack_events(self):
        log.debug('Requesting stack events')
        return self.boto_wrapper.client('cloudformation').describe_stack_events(
            StackName=self.stack.stack_id)['StackEvents']

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def update_tags(self, tags: dict):
        cf_tags = tag_dict_to_aws_format(tags)
        new_keys = tags.keys()
        for tag in self.stack.tags:
            if tag['Key'] not in new_keys:
                cf_tags.append(tag)
        log.info('Updating tags of stack {} to {}'.format(self.stack.name, tags))
        return self.stack.update(Capabilities=['CAPABILITY_IAM'],
                                 Parameters=self.stack.parameters,
                                 UsePreviousTemplate=True,
                                 Tags=cf_tags)

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def refresh_stack(self):
        # we need to refresh the stack to get the latest info
        self.stack = self.boto_wrapper.resource('cloudformation').Stack(self.name)
        return self.stack

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def get_status(self):
        self.refresh_stack()
        return self.stack.stack_status

    def get_parameter(self, param):
        """Returns param if in stack parameters, else returns None
        """
        for p in self.stack.parameters:
            if p['ParameterKey'] == param:
                return p['ParameterValue']
        raise KeyError('Key not found in template parameters: {}. Parameters: {}'.
                       format(param, self.stack.parameters))

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
           retry_on_exception=retry_on_rate_limiting)
    def delete(self):
        log.info('Deleting stack: {}'.format(self.stack.stack_name))
        self.stack.delete()
        log.info('Delete successfully initiated for {}'.format(self.stack.stack_name))


class CleanupS3BucketMixin(CfStack):
    """ Exhibitor S3 Buckets are not deleted with the rest of the resources
    in the cloudformation template so this method must be used to prevent
    leaking cloud resources.
    """
    def delete(self):
        try:
            self.boto_wrapper.empty_and_delete_bucket(
                self.stack.Resource('ExhibitorS3Bucket').physical_resource_id)
        except Exception:
            # Exhibitor S3 Bucket might not be a resource
            log.exception('Failed to get S3 bucket physical ID')
        super().delete()


class DcosCfStack(CleanupS3BucketMixin):
    """ This abstraction will work for a simple DC/OS template.
    A simple template has its exhibitor bucket and auto scaling groups
    for each of the master, public agent, and private agent groups
    """
    @classmethod
    def create(cls, stack_name: str, template_url: str, public_agents: int, private_agents: int,
               admin_location: str, key_pair_name: str, boto_wrapper: BotoWrapper):

        parameters = {
            'KeyName': key_pair_name,
            'AdminLocation': admin_location,
            'PublicSlaveInstanceCount': str(public_agents),
            'SlaveInstanceCount': str(private_agents)}

        boto_wrapper.create_stack(stack_name, parameters, template_url=template_url)

        return cls(stack_name, boto_wrapper), SSH_INFO['coreos']

    @property
    def master_instances(self):
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('MasterServerGroup').physical_resource_id)

    @property
    def private_agent_instances(self):
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('SlaveServerGroup').physical_resource_id)

    @property
    def public_agent_instances(self):
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('PublicSlaveServerGroup').physical_resource_id)

    def get_master_ips(self):
        return instances_to_hosts(self.master_instances)

    def get_private_agent_ips(self):
        return instances_to_hosts(self.private_agent_instances)

    def get_public_agent_ips(self):
        return instances_to_hosts(self.public_agent_instances)


class MasterStack(CleanupS3BucketMixin):
    @property
    def instances(self):
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('MasterServerGroup').physical_resource_id)


class PrivateAgentStack(CfStack):
    @property
    def instances(self):
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('PrivateAgentServerGroup').physical_resource_id)


class PublicAgentStack(CfStack):
    @property
    def instances(self):
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('PublicAgentServerGroup').physical_resource_id)


class DcosZenCfStack(CfStack):
    """Zen stacks are stacks that have the masters, infra, public agents, and private
    agents split into resources stacks under one zen stack
    """
    @classmethod
    def create(cls, stack_name, boto_wrapper, template_url,
               public_agents, private_agents, key_pair_name,
               private_agent_type, public_agent_type, master_type,
               gateway, vpc, private_subnet, public_subnet):
        parameters = {
            'KeyName': key_pair_name,
            'Vpc': vpc,
            'InternetGateway': gateway,
            'MasterInstanceType': master_type,
            'PublicAgentInstanceCount': public_agents,
            'PublicAgentInstanceType': public_agent_type,
            'PublicSubnet': public_subnet,
            'PrivateAgentInstanceCount': private_agents,
            'PrivateAgentInstanceType': private_agent_type,
            'PrivateSubnet': private_subnet}
        boto_wrapper.create_stack(stack_name, parameters, template_url=template_url)
        os_string = None
        try:
            os_string = template_url.split('/')[-1].split('.')[-2].split('-')[0]
            ssh_info = CF_OS_SSH_INFO[os_string]
        except (KeyError, IndexError):
            log.critical('Unexpected template URL: {}'.format(template_url))
            if os_string is not None:
                log.critical('No SSH info for OS string: {}'.format(os_string))
            raise
        return cls(stack_name, boto_wrapper), ssh_info

    @property
    def master_stack(self):
        return MasterStack(
            self.stack.Resource('MasterStack').physical_resource_id, self.boto_wrapper)

    @property
    def private_agent_stack(self):
        return PrivateAgentStack(
            self.stack.Resource('PrivateAgentStack').physical_resource_id, self.boto_wrapper)

    @property
    def public_agent_stack(self):
        return PublicAgentStack(
            self.stack.Resource('PublicAgentStack').physical_resource_id, self.boto_wrapper)

    @property
    def infrastructure(self):
        return CfStack(self.stack.Resource('Infrastructure').physical_resource_id, self.boto_wrapper)

    def delete(self):
        log.info('Starting deletion of Zen CF stack')
        # These resources might have failed to create or been removed prior, except their
        # failures and log it out
        for nested_stack in ['infrastructure', 'master_stack', 'private_agent_stack', 'public_agent_stack']:
            try:
                s = getattr(self, nested_stack)
                s.delete()
            except Exception:
                log.exception('Delete encountered an error!')
        super().delete()

    @property
    def master_instances(self):
        yield from self.master_stack.instances

    @property
    def private_agent_instances(self):
        yield from self.private_agent_stack.instances

    @property
    def public_agent_instances(self):
        yield from self.public_agent_stack.instances

    def get_master_ips(self):
        return instances_to_hosts(self.master_instances)

    def get_private_agent_ips(self):
        return instances_to_hosts(self.private_agent_instances)

    def get_public_agent_ips(self):
        return instances_to_hosts(self.public_agent_instances)


class BareClusterCfStack(CfStack):
    @classmethod
    def create(cls, stack_name, instance_type, instance_os, instance_count,
               admin_location, key_pair_name, boto_wrapper):
        stack = cls.create_from_ami(
            stack_name,
            instance_type,
            OS_AMIS[instance_os][boto_wrapper.region],
            instance_count,
            admin_location,
            key_pair_name,
            boto_wrapper,
        )
        return stack, OS_SSH_INFO[instance_os]

    @classmethod
    def create_from_ami(cls, stack_name, instance_type, instance_ami, instance_count,
                        admin_location, key_pair_name, boto_wrapper):
        template = template_by_instance_type(instance_type)
        parameters = {
            'KeyName': key_pair_name,
            'AllowAccessFrom': admin_location,
            'ClusterSize': instance_count,
            'InstanceType': instance_type,
            'AmiCode': instance_ami,
        }
        boto_wrapper.create_stack(stack_name, parameters, template_body=template)
        return cls(stack_name, boto_wrapper)

    @property
    def instances(self):
        """ only represents the cluster instances (i.e. NOT bootstrap)
        """
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('BareServerAutoScale').physical_resource_id)

    @property
    def bootstrap_instances(self):
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('BootstrapServerPlaceholderAutoScale').physical_resource_id)

    def get_cluster_host_ips(self):
        return instances_to_hosts(self.instances)

    def get_bootstrap_ip(self):
        return instances_to_hosts(self.bootstrap_instances)[0]


SSH_INFO = {
    'centos': SshInfo(
        user='centos',
        home_dir='/home/centos',
    ),
    'coreos': SshInfo(
        user='core',
        home_dir='/home/core',
    ),
    'debian': SshInfo(
        user='admin',
        home_dir='/home/admin',
    ),
    'rhel': SshInfo(
        user='ec2-user',
        home_dir='/home/ec2-user',
    ),
    'ubuntu': SshInfo(
        user='ubuntu',
        home_dir='/home/ubuntu',
    ),
}

# Update these mappings to expand OS support
OS_SSH_INFO = {
    'cent-os-7.4': SSH_INFO['centos'],
    'cent-os-7-dcos-prereqs': SSH_INFO['centos'],
    'cent-os-7.4-with-docker-selinux-disabled': SSH_INFO['centos'],
    'cent-os-7.4-with-docker-selinux-enforcing': SSH_INFO['centos'],
    'coreos': SSH_INFO['coreos'],
    'debian-8': SSH_INFO['debian'],
    'rhel-7-dcos-prereqs': SSH_INFO['rhel'],
    'ubuntu-16-04': SSH_INFO['ubuntu'],
}

CF_OS_SSH_INFO = {
    'el7': SSH_INFO['centos'],
    'coreos': SSH_INFO['coreos']
}

CENTOS_74_WITH_DOCKER_SELINUX_ENFORCING = {'ap-northeast-1': 'ami-0bc386484490ade7f',
                                           'ap-northeast-2': 'ami-04be7998b246727cb',
                                           'ap-south-1': 'ami-05df5a77e02a3e66f',
                                           'ap-southeast-1': 'ami-0a7ca9fe50e8b6882',
                                           'ap-southeast-2': 'ami-0fe85a17db4dc8cd3',
                                           'ca-central-1': 'ami-0af6de696e00750aa',
                                           'eu-central-1': 'ami-0fd78465e18a6450a',
                                           'eu-west-1': 'ami-056a9758ebedad71a',
                                           'eu-west-2': 'ami-06267aa2f48954032',
                                           'eu-west-3': 'ami-0760a4919cd3e034f',
                                           'sa-east-1': 'ami-047b3e4ef6a6d7be7',
                                           'us-east-1': 'ami-079bfc2b0c5f1db87',
                                           'us-east-2': 'ami-0f0494bd2aad99db9',
                                           'us-west-1': 'ami-02af2dc49f253922c',
                                           'us-west-2': 'ami-0ff76065de2567eec'}

OS_AMIS = {
    'cent-os-7.4': {'ap-northeast-1': 'ami-965345f8',
                    'ap-southeast-1': 'ami-8af586e9',
                    'ap-southeast-2': 'ami-427d9c20',
                    'eu-central-1': 'ami-2d0cbc42',
                    'eu-west-1': 'ami-e46ea69d',
                    'sa-east-1': 'ami-a5acd0c9',
                    'us-east-1': 'ami-771beb0d',
                    'us-west-1': 'ami-866151e6',
                    'us-west-2': 'ami-a9b24bd1'},
    # run_centos74_prereqs.sh will also be ran when this option is specified
    'cent-os-7-dcos-prereqs': CENTOS_74_WITH_DOCKER_SELINUX_ENFORCING,
    'cent-os-7.4-with-docker-selinux-disabled': {'ap-northeast-1': 'ami-023fe9ba88dfc1339',
                                                 'ap-northeast-2': 'ami-085f7275040429a2f',
                                                 'ap-south-1': 'ami-07b913395ee5282df',
                                                 'ap-southeast-1': 'ami-06890ad7295bd4e4b',
                                                 'ap-southeast-2': 'ami-01a1c6ded405b43a9',
                                                 'ca-central-1': 'ami-010bd16a1ea7d010a',
                                                 'eu-central-1': 'ami-0b6a8b2453889f012',
                                                 'eu-west-1': 'ami-0f4101e8c6c46f86a',
                                                 'eu-west-2': 'ami-0c64993daba80da53',
                                                 'eu-west-3': 'ami-02f3169248abeab2f',
                                                 'sa-east-1': 'ami-0c6bf10f43f4ab65c',
                                                 'us-east-1': 'ami-0df90d83033b1c207',
                                                 'us-east-2': 'ami-07f48e9948906d95d',
                                                 'us-west-1': 'ami-0b1320a3d397fa07a',
                                                 'us-west-2': 'ami-0116dcbe0583de7ca'},
    'cent-os-7.4-with-docker-selinux-enforcing': CENTOS_74_WITH_DOCKER_SELINUX_ENFORCING,
    'coreos': {'ap-northeast-1': 'ami-884835ee',
               'ap-southeast-1': 'ami-b9c280c5',
               'ap-southeast-2': 'ami-04be7b66',
               'eu-central-1': 'ami-862140e9',
               'eu-west-1': 'ami-022d646e',
               'sa-east-1': 'ami-022d646e',
               'us-east-1': 'ami-3f061b45',
               'us-west-1': 'ami-cc0900ac',
               'us-west-2': 'ami-692faf11'},
    'debian-8': {'ap-northeast-1': 'ami-fe54f3fe',
                 'ap-southeast-1': 'ami-60989c32',
                 'ap-southeast-2': 'ami-07e3993d',
                 'eu-central-1': 'ami-b092aaad',
                 'eu-west-1': 'ami-0ed89d79',
                 'sa-east-1': 'ami-a5bd3fb8',
                 'us-east-1': 'ami-8b9a63e0',
                 'us-west-1': 'ami-a5d621e1',
                 'us-west-2': 'ami-3d56520d'},
    # Red Hat 7.4
    'rhel-7-dcos-prereqs': {'ap-northeast-1': 'ami-9f2b90f9',
                            'ap-southeast-1': 'ami-56154835',
                            'ap-southeast-2': 'ami-4e52a72c',
                            'eu-central-1': 'ami-b78906d8',
                            'eu-west-1': 'ami-b372cfca',
                            'sa-east-1': 'ami-38b1f554',
                            'us-east-1': 'ami-78ed7402',
                            'us-west-1': 'ami-c96b51a9',
                            'us-west-2': 'ami-23aa725b'},
    'ubuntu-16-04': {'ap-northeast-1': 'ami-0919cd68',
                     'ap-southeast-1': 'ami-42934921',
                     'ap-southeast-2': 'ami-623c0d01',
                     'eu-central-1': 'ami-a9a557c6',
                     'eu-west-1': 'ami-643d4217',
                     'sa-east-1': 'ami-60bd2d0c',
                     'us-east-1': 'ami-2ef48339',
                     'us-west-1': 'ami-a9a8e4c9',
                     'us-west-2': 'ami-746aba14'}
}


aws_region_names = [
    {
        'name': 'US West (N. California)',
        'id': 'us-west-1'
    },
    {
        'name': 'US West (Oregon)',
        'id': 'us-west-2'
    },
    {
        'name': 'US East (N. Virginia)',
        'id': 'us-east-1'
    },
    {
        'name': 'South America (Sao Paulo)',
        'id': 'sa-east-1'
    },
    {
        'name': 'EU (Ireland)',
        'id': 'eu-west-1'
    },
    {
        'name': 'EU (Frankfurt)',
        'id': 'eu-central-1'
    },
    {
        'name': 'Asia Pacific (Tokyo)',
        'id': 'ap-northeast-1'
    },
    {
        'name': 'Asia Pacific (Singapore)',
        'id': 'ap-southeast-1'
    },
    {
        'name': 'Asia Pacific (Sydney)',
        'id': 'ap-southeast-2'
    },
    {
        'name': 'Asia Pacific (Seoul)',
        'id': 'ap-northeast-2'
    },
    {
        'name': 'Asia Pacific (Mumbai)',
        'id': 'ap-south-1'
    },
    {
        'name': 'US East (Ohio)',
        'id': 'us-east-2'
    }]

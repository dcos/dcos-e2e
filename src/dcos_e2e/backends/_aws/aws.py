"""
Abstractions for handling resources via Amazon Web Services (AWS)

The intention of these utilities is to allow other infrastructure to
interact with AWS without having to understand the AWS APIs. Additionally,
this module provides helper functions for the most common queries required
to manipulate and test a DC/OS cluster, which would be otherwise cumbersome
to do with AWS calls directly.
"""

import copy
import functools
import logging
import time
from typing import Any, Dict, Iterable, List, Optional

import boto3
import pkg_resources
import retrying
from botocore.exceptions import ClientError, WaiterError
from dcos_test_utils.helpers import Host

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

# pylint: disable=logging-format-interpolation


def template_by_instance_type(instance_type: str) -> str:
    """
    Identify the right template for an instance type.
    """
    if instance_type.split('.')[0] in ('c4', 't2', 'm4'):
        template = pkg_resources.resource_string(
            'dcos_e2e.backends._aws',
            'resources/templates/vpc-ebs-only-cluster-template.json'
        )
    else:
        template = pkg_resources.resource_string(
            'dcos_e2e.backends._aws',
            'resources/templates/vpc-cluster-template.json'
        )
    return template.decode('utf-8')


def param_dict_to_aws_format(user_parameters: Dict[str, Any],
                             ) -> List[Dict[str, str]]:
    """
    Convert dict to AWS parameter format by casting all types to string.
    """
    return [
        {
            'ParameterKey': str(k),
            'ParameterValue': str(v)
        } for k, v in user_parameters.items()
    ]


def retry_boto_rate_limits(
    boto_fn: Any, wait: int = 2, timeout: float = 60 * 60
) -> Any:
    """
    Decorate boto3 functions to make them resilient to AWS rate limiting and
    throttling. If one of these errors is encountered, the function will
    sleep for a geometrically increasing amount of time.
    """

    @functools.wraps(boto_fn)
    def ignore_rate_errors(*args: Any, **kwargs: Any) -> Any:
        local_wait = copy.copy(wait)
        local_timeout = copy.copy(timeout)
        while local_timeout > 0:
            next_time = time.time() + local_wait
            try:
                return boto_fn(*args, **kwargs)
            except (ClientError, WaiterError) as exc:
                if isinstance(exc, ClientError):
                    error_code = exc.response['Error']['Code']
                elif isinstance(exc, WaiterError):
                    error_code = exc.last_response['Error']['Code']
                else:
                    raise
                if error_code in ['Throttling', 'RequestLimitExceeded']:
                    log.info(
                        'AWS rate limiting error: {error_code}'.format(
                            error_code=error_code,
                        )
                    )
                    log.info(
                        'Sleeping for {local_wait} seconds before retrying'.
                        format(local_wait=local_wait, )
                    )
                    time_to_next = next_time - time.time()
                    if time_to_next > 0:
                        time.sleep(time_to_next)
                    else:
                        local_timeout += time_to_next
                    local_timeout -= local_wait
                    local_wait *= 2
                    continue
                raise
        raise Exception(
            'Rate-limit timeout encountered waiting for {}'.format(
                boto_fn.__name__
            )
        )

    return ignore_rate_errors


@retry_boto_rate_limits
def instances_to_hosts(instances: Iterable[Any]) -> List[Host]:
    """
    Return the corresponding host to each EC2 instances.
    """
    return [Host(i.private_ip_address, i.public_ip_address) for i in instances]


class BotoWrapper:
    """
    Wrapper around boto3 session to access the AWS functions.
    """

    def __init__(
        self, region: str, aws_access_key_id: str, aws_secret_access_key: str
    ) -> None:
        """
        Args:
            region: The AWS region to operate in.
            aws_access_key_id: AWS access key ID to authenticate.
            aws_secret_access_key: AWS secret access key to authenticate with.

        """
        self.region = region
        self.session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    @retry_boto_rate_limits
    def client(self, service_name: str) -> Any:
        """
        Return AWS session client.
        """
        return self.session.client(
            service_name=service_name,
            region_name=self.region,
        )

    @retry_boto_rate_limits
    def resource(self, name: str, region: Optional[str] = None) -> Any:
        """
        Return a AWS resource within a region and identified by name.
        """
        region = self.region if region is None else region
        return self.session.resource(
            service_name=name,
            region_name=region,
        )

    @retry_boto_rate_limits
    def create_key_pair(self, key_name: str) -> str:
        """
        Generate new key pair on AWS with the given name.
        Return private key for newly generated key pair.
        """
        key = self.client('ec2').create_key_pair(KeyName=key_name)
        return str(key['KeyMaterial'])

    @retry_boto_rate_limits
    def delete_key_pair(self, key_name: str) -> None:
        """
        Delete the key pair on AWS identified by the given name.
        """
        self.resource('ec2').KeyPair(key_name).delete()

    def create_bare_dcos_stack(
        self,
        stack_name: str,
        instance_type: str,
        instance_ami: str,
        cluster_size: int,
        aws_key_name: str,
        admin_location: str,
        deploy_timeout: Optional[int] = 60,
    ) -> Any:
        """
        Pull template and start cloudformation stack from template parameters.
        Starts stack creation if validation is successful
        """
        template_parameters = {
            'AllowAccessFrom': admin_location,
            'ClusterSize': cluster_size,
            'InstanceType': instance_type,
            'AmiCode': instance_ami,
            'KeyName': aws_key_name,
            'BootstrapInstanceType': 'm4.xlarge',
            'BootstrapAmiCode': instance_ami,
        }

        template_body = template_by_instance_type(instance_type)

        stack_args = {
            'StackName': stack_name,
            'DisableRollback': True,
            'TimeoutInMinutes': deploy_timeout,
            'Capabilities': ['CAPABILITY_IAM'],
            'Parameters': param_dict_to_aws_format(template_parameters),
            'TemplateBody': template_body,
        }

        log.info(
            'STACK CREATION ARGS: {stack_args}'.format(stack_args=stack_args)
        )

        return self.resource('cloudformation').create_stack(**stack_args)

    @retry_boto_rate_limits
    def get_auto_scaling_instances(self, physical_resource_id: str) -> Any:
        """
        Return ec2 instance objects in the auto scaling group specified
        by the physical_resource_id.
        """
        ec2 = self.resource('ec2')
        asgs = self.client('autoscaling').describe_auto_scaling_groups(
            AutoScalingGroupNames=[physical_resource_id]
        )['AutoScalingGroups']
        ec2_instances = []
        for auto_scaling_group in asgs:
            for instance in auto_scaling_group['Instances']:
                ec2_instances.append(ec2.Instance(instance['InstanceId']))
        return ec2_instances


class CloudFormationStack:
    """
    Representation of a wrapped Cloud Formation Stack
    """

    def __init__(self, stack_id: str, boto_wrapper: BotoWrapper) -> None:
        """
        Args:
            stack_id: Unique ID of the cloud formation stack on AWS.
            boto_wrapper: Boto3 wrapper instance to access AWS functions.

        """
        self.boto_wrapper = boto_wrapper
        self.stack_id = stack_id

    def wait_for_complete(
        self,
        transition_states: List[str],
        end_states: List[str],
    ) -> None:
        """
        Note: Unwrapped boto3 waiter class has very poor error handling.

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

        Args:
            transition_states: Wait as long as in one of these states.
            end_states: Stop waiting after next operation in these states.

        """
        log.info('Waiting for stack operation to complete')

        @retrying.retry(
            wait_fixed=60 * 1000,
            retry_on_result=lambda res: res is False,
            retry_on_exception=lambda ex: False
        )
        def wait_loop() -> bool:
            stack_status = self.get_status()
            if stack_status in end_states:
                return True
            if stack_status not in transition_states:
                for event in self.get_stack_events():
                    log.error('Stack Events: {event}'.format(event=event, ))
                raise Exception(
                    'Unexpected StackStatus: {status}'.format(
                        status=stack_status
                    )
                )
            log.info('Continuing to wait...')
            return False

        wait_loop()

    @retry_boto_rate_limits
    def get_stack_events(self) -> Any:
        """
        Return up-to-date events for the wrapped cloudformation stack.
        """
        log.info('Requesting stack events')
        return self.boto_wrapper.client('cloudformation'
                                        ).describe_stack_events(
                                            self.stack_id
                                        )['StackEvents']

    @retry_boto_rate_limits
    def get_status(self) -> Any:
        """
        Return the updated status of the wrapped cloudformation stack.
        """
        return self.stack.stack_status

    @retry_boto_rate_limits
    def delete(self) -> None:
        """
        Delete the wrapped cloudformation stack on AWS.
        """
        self.stack.delete()
        log.info(
            'Deleting stack initiated: {stack_id}'.format(
                stack_id=self.stack_id
            )
        )

    @property
    def instances(self) -> Iterable[Any]:
        """
        Return all current node EC2 instances.
        """
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('BareServerAutoScale').physical_resource_id
        )

    @property
    def bootstrap_instances(self) -> Iterable[Any]:
        """
        Return all current bootstrap EC2 instance.
        """
        yield from self.boto_wrapper.get_auto_scaling_instances(
            self.stack.Resource('BootstrapServerPlaceholderAutoScale')
            .physical_resource_id
        )

    @property
    def stack(self) -> Any:
        """
        Fetch and return the latest representation of the cloudformation stack.
        """
        return self.boto_wrapper.resource('cloudformation').Stack(
            self.stack_id
        )

    def get_cluster_hosts(self) -> Any:
        """
        Return cluster hosts to the corresponding EC2 instances.
        """
        return instances_to_hosts(self.instances)

    def get_bootstrap_host(self) -> Host:
        """
        Return the bootstrap host to the corresponding EC2 instance.
        """
        return next(iter(instances_to_hosts(self.bootstrap_instances)))


class AWSError(Exception):
    """
    Indicates an error with querying AWS.
    """

    def __init__(  # pylint: disable=super-init-not-called
        self,
        error: str,
        msg: Optional[str] = None
    ) -> None:
        """
        Represent errors of Amazon Web Services.
        """
        self.error = error
        self.msg = msg

    def __repr__(self) -> str:
        """
        Return custom AWS error representation.
        """
        return '{error}: {message}'.format(
            error=self.error,
            message=self.msg if self.msg else self.__cause__,
        )

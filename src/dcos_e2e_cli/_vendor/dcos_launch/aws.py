import json
import logging

from retrying import retry

from .. import dcos_test_utils
from ..dcos_test_utils import onprem as ___vendorize__0
dcos_test_utils.onprem = ___vendorize__0
from ..dcos_launch import util
from ..dcos_launch import onprem
from ..dcos_launch.platforms import aws

log = logging.getLogger(__name__)


class DcosCloudformationLauncher(util.AbstractLauncher):
    def __init__(self, config: dict, env=None):
        self.boto_wrapper = aws.BotoWrapper(
            config['aws_region'])
        self.config = config

    def create(self):
        """ Checks if the key helper or zen helper are enabled,
        provides resources according to those helpers, tracking which resources
        were created, and then attempts to deploy the template.

        Note: both key helper and zen helper will mutate the config to inject
        the appropriate template parameters for the generated resources
        """
        temp_resources = {}
        temp_resources.update(self.key_helper())
        temp_resources.update(self.zen_helper())
        try:
            stack = self.boto_wrapper.create_stack(
                self.config['deployment_name'],
                self.config['template_parameters'],
                template_url=self.config.get('template_url'),
                template_body=self.config.get('template_body'),
                disable_rollback=self.config['disable_rollback'],
                tags=self.config.get('tags'))
        except Exception as ex:
            self.delete_temp_resources(temp_resources)
            raise util.LauncherError('ProviderError', None) from ex
        self.config.update({
            'stack_id': stack.stack_id,
            'temp_resources': temp_resources})
        return self.config

    def zen_helper(self):
        """
        Checks parameters for Zen template prerequisites are met. If not met, they
        will be provided (must be done in correct order) and added to the info
        JSON as 'temp_resources'
        """
        if not self.config['zen_helper']:
            return {}
        parameters = self.config['template_parameters']
        temp_resources = {}
        if 'Vpc' not in parameters:
            vpc_id = self.boto_wrapper.create_vpc_tagged('10.0.0.0/16', self.config['deployment_name'])
            parameters['Vpc'] = vpc_id
            temp_resources['vpc'] = vpc_id
        if 'InternetGateway' not in parameters:
            gateway_id = self.boto_wrapper.create_internet_gateway_tagged(vpc_id, self.config['deployment_name'])
            parameters['InternetGateway'] = gateway_id
            temp_resources.update({'gateway': gateway_id})
        if 'PrivateSubnet' not in parameters:
            private_subnet_id = self.boto_wrapper.create_subnet_tagged(
                vpc_id, '10.0.0.0/17', self.config['deployment_name'] + 'private')
            parameters['PrivateSubnet'] = private_subnet_id
            temp_resources.update({'private_subnet': private_subnet_id})
        if 'PublicSubnet' not in parameters:
            public_subnet_id = self.boto_wrapper.create_subnet_tagged(
                vpc_id, '10.0.128.0/20', self.config['deployment_name'] + '-public')
            parameters['PublicSubnet'] = public_subnet_id
            temp_resources.update({'public_subnet': public_subnet_id})
        self.config['template_parameters'] = parameters
        return temp_resources

    def wait(self):
        self.stack.wait_for_complete(transition_states=['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS',
                                                        'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'],
                                     end_states=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])

    def describe(self):
        return {
            'masters': util.convert_host_list(self.stack.get_master_ips()),
            'private_agents': util.convert_host_list(self.stack.get_private_agent_ips()),
            'public_agents': util.convert_host_list(self.stack.get_public_agent_ips())}

    def delete(self):
        # If the stack is in the middle of another operation (probably because its tags were being updated), wait for
        # the operation to complete before trying to delete it
        if 'IN_PROGRESS' in self.stack.get_status():
            self.stack.wait_for_complete(transition_states=['ROLLBACK_IN_PROGRESS', 'UPDATE_IN_PROGRESS',
                                                            'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                                                            'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                                                            'UPDATE_ROLLBACK_IN_PROGRESS'],
                                         end_states=['CREATE_COMPLETE', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE',
                                                     'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_FAILED',
                                                     'UPDATE_ROLLBACK_COMPLETE'])
        self.stack.delete()
        # we must wait for the stack to be deleted for 2 reasons:
        # 1. required to remove network resources on which it depends
        # 2. to make sure it successfully deletes. If not (for example got interrupted by tagging), we retry deleting
        status = self.stack.wait_for_complete(
            transition_states=[
                'DELETE_IN_PROGRESS', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'UPDATE_IN_PROGRESS',
                'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_ROLLBACK_IN_PROGRESS'
            ],
            end_states=['DELETE_COMPLETE', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE', 'UPDATE_COMPLETE',
                        'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE'])
        if status != 'DELETE_COMPLETE':
            log.info('Deletion was interrupted by another operation (most likely tagging). Retrying to delete...')
            self.delete()
        elif len(self.config['temp_resources']) > 0:
            self.delete_temp_resources(self.config['temp_resources'])

    def delete_temp_resources(self, temp_resources):
        if 'key_name' in temp_resources:
            self.boto_wrapper.delete_key_pair(temp_resources['key_name'])
        if 'public_subnet' in temp_resources:
            self.boto_wrapper.delete_subnet(temp_resources['public_subnet'])
        if 'private_subnet' in temp_resources:
            self.boto_wrapper.delete_subnet(temp_resources['private_subnet'])
        if 'gateway' in temp_resources:
            self.boto_wrapper.delete_internet_gateway(temp_resources['gateway'])
        if 'vpc' in temp_resources:
            self.boto_wrapper.delete_vpc(temp_resources['vpc'])

    def key_helper(self):
        """ If key_helper is true, then create an EC2 keypair with the same name
        as the cloudformation stack, update the config with the resulting private key,
        and amend the cloudformation template parameters to have KeyName set as this key
        """
        if not self.config['key_helper']:
            return {}
        if 'KeyName' in self.config['template_parameters']:
            raise util.LauncherError('KeyHelperError', 'KeyName cannot be set in '
                                     'template_parameters when key_helper is true')
        key_name = self.config['deployment_name']
        private_key = self.boto_wrapper.create_key_pair(key_name)
        self.config.update({'ssh_private_key': private_key})
        self.config['template_parameters'].update({'KeyName': key_name})
        return {'key_name': key_name}

    @property
    def stack(self):
        try:
            return aws.fetch_stack(self.config['stack_id'], self.boto_wrapper)
        except Exception as ex:
            raise util.LauncherError('StackNotFound', None) from ex


class OnPremLauncher(DcosCloudformationLauncher, onprem.AbstractOnpremLauncher):
    """ Launches a homogeneous cluster of plain AMIs intended for onprem DC/OS
    """
    def create(self):
        """ Amend the config to add a template_body and the appropriate parameters
        """
        template_parameters = {
            'AllowAccessFrom': self.config['admin_location'],
            'ClusterSize': (self.config['num_masters'] + self.config['num_public_agents'] +
                            self.config['num_private_agents']),
            'InstanceType': self.config['instance_type'],
            'InstanceDeviceName': self.config['instance_device_name'],
            'AmiCode': self.config['instance_ami'],
            # Bootstrap instance is currently instantiated as a single-server AutoScaleGroup which is terrible and is
            # intended to be updated to be configured properly as an EC2 instance later
            'BootstrapInstanceType': self.config['bootstrap_instance_type'],
            'BootstrapInstanceDeviceName': self.config['bootstrap_instance_device_name'],
            'BootstrapAmiCode': self.config['bootstrap_instance_ami']
        }
        if not self.config['key_helper']:
            template_parameters['KeyName'] = self.config['aws_key_name']
        template_body = aws.template_by_instance_type(self.config['instance_type'])
        template_body_json = json.loads(template_body)
        if 'aws_block_device_mappings' in self.config:
            log.warning(
                'Custom AWS block device specified; please consult '
                'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html '
                'to address deployment issues that may arise from this')
            template_body_json['Resources']['BareServerLaunchConfig']['Properties']['BlockDeviceMappings'].extend(
                self.config['aws_block_device_mappings'])
        if 'iam_role_permissions' in self.config:
            template_body_json[
                'Resources']['BareRole']['Properties']['Policies'][0]['PolicyDocument']['Statement'].extend(
                self.config['iam_role_permissions'])
        self.config.update({
            'template_body': json.dumps(template_body_json),
            'template_parameters': template_parameters})
        return super().create()

    def describe(self):
        return onprem.AbstractOnpremLauncher.describe(self)

    def get_cluster_hosts(self):
        return self.stack.get_cluster_host_ips()

    def get_bootstrap_host(self):
        return self.stack.get_bootstrap_ip()

    def get_onprem_cluster(self):
        num_masters = int(self.config['num_masters'])
        num_private_agents = int(self.config['num_private_agents'])
        num_public_agents = int(self.config['num_public_agents'])

        @retry(wait_exponential_multiplier=1000, wait_exponential_max=20 * 60 * 1000,
               retry_on_result=lambda res: res[1])
        def _get_cluster():
            """ Whenever an AWS rate limiting error occurs, for a reason still unknown, there's a strong possibility
            that the hosts will not be found inside the stack. So here we implement a retrying logic with exponential
            backoff that asserts all the cluster hosts are found in the stack.
            """
            cluster = dcos_test_utils.onprem.OnpremCluster.from_hosts(
                bootstrap_host=self.get_bootstrap_host(),
                cluster_hosts=self.get_cluster_hosts(),
                num_masters=num_masters,
                num_private_agents=num_private_agents,
                num_public_agents=num_public_agents)

            num_masters_found = len(cluster.masters)
            num_private_agents_found = len(cluster.private_agents)
            num_public_agents_found = len(cluster.public_agents)
            bootstrap_host_found = bool(cluster.bootstrap_host)

            cluster_matches_config = (num_masters_found == num_masters and
                                      num_private_agents_found == num_private_agents and
                                      num_public_agents_found == num_public_agents and
                                      bootstrap_host_found)

            if not cluster_matches_config:
                msg = ("Not all required hosts were found:\n"
                       "\tmaster count: expected {}, found {}\n"
                       "\tprivate agent count: expected {}, found {}\n"
                       "\tpublic agent count: expected {}, found {}\n"
                       "\tbootstrap host found: {}".format(num_masters, num_masters_found,
                                                           num_private_agents, num_private_agents_found,
                                                           num_public_agents, num_public_agents_found,
                                                           bootstrap_host_found))
                log.info("Stack not ready yet for DC/OS installation. " + msg)
                self.stack.refresh_stack()

            return cluster, not cluster_matches_config

        cluster, _ = _get_cluster()
        return cluster

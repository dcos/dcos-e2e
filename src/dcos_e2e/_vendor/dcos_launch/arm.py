""" Launcher functionality for the Azure Resource Manager (ARM)
"""
import logging
import os

from .. import dcos_launch
from ..dcos_launch import platforms as ___vendorize__0
dcos_launch.platforms = ___vendorize__0
from ..dcos_launch.platforms import arm as ___vendorize__1
dcos_launch.platforms.arm = ___vendorize__1
from .. import dcos_launch
from ..dcos_launch import util as ___vendorize__0
dcos_launch.util = ___vendorize__0

log = logging.getLogger(__name__)


class AzureResourceGroupLauncher(dcos_launch.util.AbstractLauncher):
    def __init__(self, config: dict, env=None):
        if env:
            os.environ.update(env)
        self.azure_wrapper = dcos_launch.platforms.arm.AzureWrapper(
            config['azure_location'],
            dcos_launch.util.set_from_env('AZURE_SUBSCRIPTION_ID'),
            dcos_launch.util.set_from_env('AZURE_CLIENT_ID'),
            dcos_launch.util.set_from_env('AZURE_CLIENT_SECRET'),
            dcos_launch.util.set_from_env('AZURE_TENANT_ID'))
        self.config = config
        log.debug('Using Azure Resource Group Launcher')

    def create(self):
        self.key_helper()
        self.azure_wrapper.deploy_template_to_new_resource_group(
            self.config['template_url'],
            self.config['deployment_name'],
            self.config['template_parameters'],
            self.config.get('tags'))
        return self.config

    def wait(self):
        self.resource_group.wait_for_deployment()

    def describe(self):
        return {
            'masters': dcos_launch.util.convert_host_list(self.resource_group.get_master_ips()),
            'private_agents': dcos_launch.util.convert_host_list(self.resource_group.get_private_agent_ips()),
            'public_agents': dcos_launch.util.convert_host_list(self.resource_group.get_public_agent_ips()),
            'master_fqdn': self.resource_group.public_master_lb_fqdn,
            'public_agent_fqdn': self.resource_group.public_agent_lb_fqdn}

    def delete(self):
        self.resource_group.delete()

    def key_helper(self):
        """ Adds private key to the config and injects the public key into
        the template parameters
        """
        if not self.config['key_helper']:
            return
        if 'sshRSAPublicKey' in self.config['template_parameters']:
            raise dcos_launch.util.LauncherError('KeyHelperError', 'key_helper will automatically'
                                                 'calculate and inject sshRSAPublicKey; do not set this parameter')
        private_key, public_key = dcos_launch.util.generate_rsa_keypair()
        self.config.update({'ssh_private_key': private_key.decode()})
        self.config['template_parameters'].update({'sshRSAPublicKey': public_key.decode()})

    @property
    def resource_group(self):
        try:
            return dcos_launch.platforms.arm.DcosAzureResourceGroup(self.config['deployment_name'], self.azure_wrapper)
        except Exception as ex:
            raise dcos_launch.util.LauncherError('GroupNotFound', None) from ex

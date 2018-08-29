""" Launcher functionality for the Azure Resource Manager (ARM)
"""
import json
import logging
import os
import subprocess
import tarfile
import tempfile
import uuid

import requests

from .. import dcos_launch
from ..dcos_launch import platforms as ___vendorize__0
dcos_launch.platforms = ___vendorize__0
from ..dcos_launch.platforms import arm as ___vendorize__1
dcos_launch.platforms.arm = ___vendorize__1
from .. import dcos_launch
from ..dcos_launch import util as ___vendorize__0
dcos_launch.util = ___vendorize__0

log = logging.getLogger(__name__)


def generate_dcos_engine_template(
        linux_ssh_public_key: str,
        num_masters: int,
        master_vm_size: str,
        num_windows_private_agents: int,
        windows_private_vm_size: str,
        num_windows_public_agents: int,
        windows_public_vm_size: str,
        num_linux_private_agents: int,
        linux_private_vm_size: str,
        num_linux_public_agents: int,
        linux_public_vm_size: str,
        windows_admin_user: str,
        windows_admin_password: str,
        linux_admin_user: str,
        dcos_engine_orchestrator_release: str,
        ):
    """ Generates the template provided to dcos-engine
    """
    unique_id = str(uuid.uuid4())[:8] + 'dcos'
    template = {
        "apiVersion": "vlabs",
        "properties": {
            "orchestratorProfile": {
                "orchestratorType": "DCOS",
                "orchestratorRelease": dcos_engine_orchestrator_release
            },
            "masterProfile": {
                "count": num_masters,
                "dnsPrefix": "master" + unique_id,
                "vmSize": master_vm_size
            },
            "agentPoolProfiles": [
                {
                    "name": "wpub",
                    "count": num_windows_public_agents,
                    "vmSize": windows_public_vm_size,
                    "osType": "Windows",
                    "dnsPrefix": "wpub" + unique_id,
                    "ports": [80, 443, 8080, 3389]
                },
                {
                    "name": "wpri",
                    "count": num_windows_private_agents,
                    "vmSize": windows_private_vm_size,
                    "osType": "Windows",
                },
                {
                    "name": "linpub",
                    "count": num_linux_public_agents,
                    "vmSize": linux_public_vm_size,
                    "osType": "Linux",
                    "dnsPrefix": "linpub" + unique_id,
                    "ports": [80, 443, 22]
                },
                {
                    "name": "linpri",
                    "count": num_linux_private_agents,
                    "vmSize": linux_private_vm_size,
                    "osType": "Linux"
                }
            ],
            "windowsProfile": {
                "adminUsername": windows_admin_user,
                "adminPassword": windows_admin_password
            },
            "linuxProfile": {
                "adminUsername": linux_admin_user,
                "ssh": {
                    "publicKeys": [
                        {
                            "keyData": linux_ssh_public_key
                        }
                    ]
                }
            }
        }
    }
    return template


def run_dcos_engine(dcos_engine_url: str, dcos_engine_template):
    """ Runs the dcos-engine
    """
    tmpdir = tempfile.mkdtemp()
    # pull down dcos engine in temp dir
    download_path = os.path.join(tmpdir, 'download.tar.gz')
    with open(download_path, 'wb') as f:
        r = requests.get(dcos_engine_url)
        for chunk in r.iter_content(1024):
            f.write(chunk)
    extract_path = os.path.join(tmpdir, 'extract')
    with tarfile.open(download_path) as tar:
        tar.extractall(path=extract_path)
    extracted_name = dcos_engine_url.split('/')[-1].rstrip('.tar.gz')
    dcos_engine_bin_path = os.path.join(extract_path, extracted_name, 'dcos-engine')
    # inject parameters into the JSON (keyhelper, agent definitions)
    acs_template_path = os.path.join(tmpdir, 'acs_template.json')
    with open(acs_template_path, 'w') as f:
        json.dump(dcos_engine_template, f)
    # run acs vs template
    cmd = [dcos_engine_bin_path, 'generate', acs_template_path]
    subprocess.check_call(cmd, cwd=tmpdir)

    cluster_name = dcos_engine_template['properties']['masterProfile']['dnsPrefix']
    with open(os.path.join(tmpdir, '_output/{}/azuredeploy.json'.format(cluster_name)), 'r') as f:
        arm_template = json.load(f)
    with open(os.path.join(tmpdir, '_output/{}/azuredeploy.parameters.json'.format(cluster_name)), 'r') as f:
        arm_template_parameters_raw = json.load(f)
    arm_template_parameters = dict()
    for k, v in arm_template_parameters_raw['parameters'].items():
        arm_template_parameters[k] = v['value']
    return arm_template, arm_template_parameters


class DcosEngineLauncher(dcos_launch.util.AbstractLauncher):
    def __init__(self, config: dict, env=None):
        if env is None:
            azure_subscription_id = dcos_launch.util.set_from_env('AZURE_SUBSCRIPTION_ID')
            azure_client_id = dcos_launch.util.set_from_env('AZURE_CLIENT_ID')
            azure_client_secret = dcos_launch.util.set_from_env('AZURE_CLIENT_SECRET')
            azure_tenant_id = dcos_launch.util.set_from_env('AZURE_TENANT_ID')
        else:
            azure_subscription_id = env['AZURE_SUBSCRIPTION_ID']
            azure_client_id = env['AZURE_CLIENT_ID']
            azure_client_secret = env['AZURE_CLIENT_SECRET']
            azure_tenant_id = env['AZURE_TENANT_ID']
        self.azure_wrapper = dcos_launch.platforms.arm.AzureWrapper(
            config['azure_location'],
            azure_subscription_id,
            azure_client_id,
            azure_client_secret,
            azure_tenant_id)
        self.config = config
        log.debug('Using Azure Resource Group Launcher')

    def create(self):
        if self.config['key_helper']:
            private_key, public_key = dcos_launch.util.generate_rsa_keypair()
            self.config.update({
                'ssh_private_key': private_key.decode(),
                'ssh_public_key': public_key.decode()})
        dcos_engine_template = generate_dcos_engine_template(
            self.config['ssh_public_key'],
            self.config['num_masters'],
            self.config['master_vm_size'],
            self.config['num_windows_private_agents'],
            self.config['windows_private_vm_size'],
            self.config['num_windows_public_agents'],
            self.config['windows_public_vm_size'],
            self.config['num_linux_private_agents'],
            self.config['linux_private_vm_size'],
            self.config['num_linux_public_agents'],
            self.config['linux_public_vm_size'],
            self.config['windows_admin_user'],
            self.config['windows_admin_password'],
            self.config['linux_admin_user'],
            self.config['dcos_engine_orchestrator_release'])
        windows_image_source_url = self.config.get('windows_image_source_url')
        if windows_image_source_url:
            dcos_engine_template["properties"]["windowsProfile"]["WindowsImageSourceUrl"] = windows_image_source_url
        else:
            # Use the official Azure image if a custom VHD was not specified
            # via the windows_image_source_url config option
            windows_publisher = self.config.get('windows_publisher')
            windows_offer = self.config.get('windows_offer')
            windows_sku = self.config.get('windows_sku')
            dcos_engine_template["properties"]["windowsProfile"]["WindowsPublisher"] = windows_publisher
            dcos_engine_template["properties"]["windowsProfile"]["WindowsOffer"] = windows_offer
            dcos_engine_template["properties"]["windowsProfile"]["WindowsSku"] = windows_sku
        linux_bs_url = self.config.get('dcos_linux_bootstrap_url')
        arm_template, self.config['template_parameters'] = run_dcos_engine(self.config['dcos_engine_tarball_url'], dcos_engine_template)  # noqa
        if linux_bs_url:
            self.config['template_parameters']['dcosBootstrapURL'] = linux_bs_url
        windows_bs_url = self.config.get('dcos_windows_bootstrap_url')
        if windows_bs_url:
            self.config['template_parameters']['dcosWindowsBootstrapURL'] = windows_bs_url
        self.azure_wrapper.deploy_template_to_new_resource_group(
            self.config.get('template_url'),
            self.config['deployment_name'],
            self.config['template_parameters'],
            self.config.get('tags'),
            template=arm_template)
        return self.config

    def wait(self):
        self.resource_group.wait_for_deployment()

    def describe(self):
        return {
            'masters': dcos_launch.util.convert_host_list(self.resource_group.get_master_ips()),
            'private_agents': dcos_launch.util.convert_host_list(
                self.resource_group.get_linux_private_agent_ips()),
            'public_agents': dcos_launch.util.convert_host_list(
                self.resource_group.get_linux_public_agent_ips()),
            'windows_private_agents': dcos_launch.util.convert_host_list(
                self.resource_group.get_windows_private_agent_ips()),
            'windows_public_agents': dcos_launch.util.convert_host_list(
                self.resource_group.get_windows_public_agent_ips()),
            'master_fqdn': self.resource_group.public_master_lb_fqdn,
            'public_agent_fqdn': self.resource_group.linux_public_agent_lb_fqdn}

    def delete(self):
        self.resource_group.delete()

    def test(self, args: list, env_dict: dict, test_host=None, test_port=2200, details: dict=None) -> int:
        details = self.describe()
        env_dict.update({
            'WINDOWS_HOSTS': ','.join(m['private_ip'] for m in details['windows_private_agents']),
            'WINDOWS_PUBLIC_HOSTS': ','.join(m['private_ip'] for m in details['windows_public_agents'])})
        return super().test(args, env_dict, test_host=details['master_fqdn'], test_port=test_port, details=details)

    @property
    def resource_group(self):
        try:
            return dcos_launch.platforms.arm.HybridDcosAzureResourceGroup(
                self.config['deployment_name'], self.azure_wrapper)
        except Exception as ex:
            raise dcos_launch.util.LauncherError('GroupNotFound', None) from ex

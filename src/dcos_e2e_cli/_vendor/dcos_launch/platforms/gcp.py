""" This module allows for the creation and polling of network-isolated, homogeneous clusters on Google Compute Engine
(GCE) for installing DC/OS. To achieve this, it uses the Cloud Deployment Manager and Compute Engine APIs. Usage of the
Cloud Deployment Manager results in simpler code and far fewer API calls.
"""

import copy
import logging
import typing
from functools import wraps

import yaml
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
from retrying import retry

from ...dcos_test_utils.helpers import Host

log = logging.getLogger(__name__)

# mapping used for the commonly used os name formats that differ from their respective formats in gce.
# If you must expand OS support, update these mappings
OS_IMAGE_FAMILIES = {
    'cent-os-7': 'centos-7',
    'ubuntu-16-04': 'ubuntu-1604-lts',
    'coreos': 'coreos-stable',
}

# template for an "instance template" resource to be used in a managed instance group
INSTANCE_TEMPLATE = """
type: compute.v1.instanceTemplate
name: {name}
metadata:
  dependsOn:
  - {network}
properties:
  project: {project}
  properties:
    machineType: {machineType}
    disks:
    - deviceName: boot
      type: PERSISTENT
      boot: true
      autoDelete: true
      initializeParams:
        diskSizeGb: {diskSizeGb}
        diskType: {diskType}
        sourceImage: projects/{imageProject}/global/images/{sourceImage}
    networkInterfaces:
    - network: global/networks/{network}
      # Access Config required to give the instance a public IP address
      accessConfigs:
      - name: External NAT
        type: ONE_TO_ONE_NAT
    metadata:
      items:
      - key: ssh-keys
        value: {ssh_user}:{ssh_public_key}
    scheduling:
      preemptible: {usePreemptibleVMs}
    tags:
      items:
        - {deploymentName}
"""

# template for a network resource in a gce deployment
NETWORK_TEMPLATE = """
type: compute.v1.network
name: {name}
properties:
  autoCreateSubnetworks: True
"""

# template for an instance group manager resource in a gce deployment
MANAGED_INSTANCE_GROUP_TEMPLATE = """
type: compute.v1.instanceGroupManager
name: {name}
metadata:
  dependsOn:
  - {instance_template_name}
properties:
  baseInstanceName: vm
  instanceTemplate: global/instanceTemplates/{instance_template_name}
  zone: {zone}
  targetSize: {size}
"""

# template for a firewall that controls external access
EXTERNAL_FIREWALL_TEMPLATE = """
type: compute.v1.firewall
name: {name}-external
metadata:
  dependsOn:
  - {network}
properties:
  description: external
  network: global/networks/{network}
  sourceRanges:
  - 0.0.0.0/0
  allowed:
  - IPProtocol: tcp
    ports:
    - 22
    - 80
    - 443
    - 61001
  - IPProtocol: icmp
"""

# template for a firewall that controls internal access
INTERNAL_FIREWALL_TEMPLATE = """
type: compute.v1.firewall
name: {name}-internal
metadata:
  dependsOn:
  - {network}
properties:
  description: internal
  network: global/networks/{network}
  sourceTags:
  - {deploymentName}
  allowed:
  - IPProtocol: all
"""

# Used to disable automatic updates on CoreOS
IGNITION_CONFIG = """
{
    "ignition": {
        "version": "2.0.0",
        "config": {}
    },
    "storage": {},
    "systemd": {
        "units": [
            {
                "name": "update-engine.service",
                "mask": true
            },
            {
                "name": "locksmithd.service",
                "mask": true
            }
        ]
    },
    "networkd": {},
    "passwd": {}
}
"""


def tag_dict_to_gce_format(tags: dict):
    return [{'key': k, 'value': v} for k, v in tags.items()]


# Function decorator that adds detail to potential googleapiclient.errors.HttpError exceptions with code 404 or 409
def catch_http_exceptions(f):
    @wraps(f)
    def handle_exception(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HttpError as e:
            if e.resp.status == 404:
                log.exception("The resource you are trying to access doesn't exist")
            elif e.resp.status == 409:
                log.exception('''The specified resources exist and might be under an active operation
                                   (operation conflict)''')
            raise e

    return handle_exception


class GcpWrapper:
    @catch_http_exceptions
    def __init__(self, credentials_dict):
        """
        Build GCE service account credentials from info stored in environment variables, then build a GCE API wrapper
            with those credentials. Only one of the two environment variables must be set.
        :param creds_env_var_name: JSON string that contains your GCE service account credentials
        :param creds_path_env_var_name: string that contains the path to the file containing your GCE service account
            credentials.
        """
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, scopes='https://www.googleapis.com/auth/cloud-platform')

        self.compute = discovery.build('compute', 'v1', credentials=credentials)
        self.deployment_manager = discovery.build('deploymentmanager', 'v2', credentials=credentials)
        self.project_id = credentials_dict['project_id']

    @catch_http_exceptions
    def get_instance_info(self, name: str, zone: str):
        """ Returns the dictionary representation of a GCE instance resource. For details on the contents of this
        resource,see https://cloud.google.com/compute/docs/reference/latest/instances
        """
        response = self.compute.instances().get(project=self.project_id, zone=zone, instance=name).execute()
        log.debug('get_instance_info response: ' + str(response))
        return response

    @catch_http_exceptions
    def list_group_instances(self, group_name: str, zone: str) -> typing.Iterator[dict]:
        response = self.compute.instanceGroupManagers().listManagedInstances(project=self.project_id, zone=zone,
                                                                             instanceGroupManager=group_name).execute()
        log.debug('list_group_instances response: ' + str(response))

        for instance in response.get('managedInstances', []):
            yield instance

    @retry(wait_fixed=2000, retry_on_result=lambda res: res is None, stop_max_delay=30 * 1000)
    def get_instance_network_properties(self, instance_name: str, zone: str) -> dict:
        network_info = self.get_instance_info(instance_name, zone)['networkInterfaces'][0]
        if 'networkIP' not in network_info or 'accessConfigs' not in network_info:
            return None
        if 'natIP' not in network_info['accessConfigs'][0]:
            return None
        return network_info

    @catch_http_exceptions
    def create_deployment(self, name: str, deployment_config: dict, tags: dict=None):
        if tags is None:
            tags = dict()
        body = {
            'name': name,
            'description': """{"cluster_type": "DC/OS Onprem on GCE"}""",
            'target': {
                'config': {
                    'content': yaml.dump(deployment_config, default_flow_style=False)}
            },
            'labels': tag_dict_to_gce_format(tags)
        }

        log.info('Creating GCE deployment...')
        response = self.deployment_manager.deployments().insert(
            project=self.project_id, body=body).execute()
        log.debug('create_deployment response: ' + str(response))

    @catch_http_exceptions
    def get_deployments(self):
        """ iterates over all current deployments, returning a generic Deployment class
        when there is no instanceGroupManager to establish that we are dealing with
        a BareClusterDeployment. Any deployments that are in the process of being deleted
        are skipped to avoid query errors on deleted deployments
        """
        request = self.deployment_manager.deployments().list(project=self.project_id)
        while request is not None:
            response = request.execute()
            for deployment_info in response.get('deployments', []):
                # we don't want to retrieve deployments that are in the process of being deleted
                if deployment_info['operation']['operationType'] == 'deleted':
                    continue
                deployment = Deployment(self, deployment_info['name'])
                zone = None
                for r in deployment.get_resources()['resources']:
                    if r['type'] == 'compute.v1.instanceGroupManager':
                        zone = r.get('properties', {}).get('zone')
                if zone is None:
                    yield deployment
                else:
                    yield BareClusterDeployment(self, deployment_info['name'], zone)
            request = self.deployment_manager.deployments().list_next(previous_request=request,
                                                                      previous_response=response)


class Deployment:
    def __init__(self, gcp_wrapper: GcpWrapper, name: str):
        self.gcp_wrapper = gcp_wrapper
        self.name = name

    @catch_http_exceptions
    def delete(self):
        response = self.gcp_wrapper.deployment_manager.deployments().delete(project=self.gcp_wrapper.project_id,
                                                                            deployment=self.name).execute()
        log.debug('delete response: ' + str(response))

    @catch_http_exceptions
    def get_info(self) -> dict:
        """ Returns the dictionary representation of a GCE deployment resource. For details on the contents of this
        resource, see https://cloud.google.com/deployment-manager/docs/reference/latest/deployments#resource
        """
        response = self.gcp_wrapper.deployment_manager.deployments().get(project=self.gcp_wrapper.project_id,
                                                                         deployment=self.name).execute()
        log.debug('get_info response: ' + str(response))
        return response

    def _check_status(response: dict) -> bool:
        """ Checks the status of the deployment until it is done or has failed
        :param response : <dict> http response containing info about the deployment
        :return: <boolean> whether to continue checking the status of the deployment (True) or not (False)
        """
        status = response['operation']['status']
        if status == 'DONE':
            return False
        elif status == 'RUNNING' or status == 'PENDING':
            log.debug('Waiting for deployment')
            return True
        else:
            raise Exception('Deployment failed with response: ' + str(response))

    @retry(wait_fixed=60 * 1000, retry_on_result=_check_status, retry_on_exception=lambda _: False)
    def wait_for_completion(self) -> dict:
        return self.get_info()

    def get_resources(self):
        resources = []
        request = self.gcp_wrapper.deployment_manager.resources().list(project=self.gcp_wrapper.project_id,
                                                                       deployment=self.name)
        while request is not None:
            response = request.execute()
            for resource in response.get('resources', []):
                resource_copy = copy.deepcopy(resource)
                for key in resource_copy:
                    # The only fields we need as you can see in the templates at the top of this file. Other fields
                    # are present that would cause an error when the API is called for updating a deployment
                    if key not in ('type', 'name', 'metadata', 'properties'):
                        del resource[key]
                    # the yaml strings in these fields are not properly formatted for the API (error thrown when
                    # updating a deployment) so we load it and then dump the whole resource data structure correctly in
                    # update_tags afterwards -> default_flow_style=False
                    if key in ['properties', 'metadata']:
                        resource[key] = yaml.load(resource[key])

                resources.append(resource)
            request = self.gcp_wrapper.deployment_manager.resources().list_next(previous_request=request,
                                                                                previous_response=response)
        return {'resources': resources}

    def update_tags(self, tags):
        info = self.gcp_wrapper.deployment_manager.deployments().get(project=self.gcp_wrapper.project_id,
                                                                     deployment=self.name).execute()
        # we need to get the resources because they're not provided in the info and they're necessary for update
        info['target'] = {
            'config': {'content': yaml.dump(self.get_resources(), default_flow_style=False)}
        }
        info['labels'] = tag_dict_to_gce_format(tags)
        response = self.gcp_wrapper.deployment_manager.deployments().update(project=self.gcp_wrapper.project_id,
                                                                            deployment=self.name, body=info).execute()
        log.debug('update_tags response: ' + str(response))
        return response

    def get_tags(self):
        try:
            info = self.get_info()['labels']
        except KeyError:
            return {}

        return {entry['key']: entry['value'] for entry in info}


class BareClusterDeployment(Deployment):
    """ A specialized deployment that contains a basic, network-connected,
    cluster of identical, minimally configured machines for installing DC/OS
    """
    @property
    def instance_group_name(self):
        return self.name + '-group'

    @property
    def template_name(self):
        return self.name + '-template'

    @property
    def network_name(self):
        return self.name + '-network'

    @property
    def firewall_name(self):
        return self.name + '-firewall'

    def __init__(self, gcp_wrapper, name, zone):
        """ zone argument dictates where the single managed
        instance group will be deployed to
        """
        super().__init__(gcp_wrapper, name)
        self.zone = zone

    @classmethod
    def create(
            cls,
            gcp_wrapper: GcpWrapper,
            name: str,
            zone: str,
            node_count: int,
            disk_size: int,
            disk_type: str,
            source_image: str,
            machine_type: str,
            image_project: str,
            ssh_user: str,
            ssh_public_key: str,
            disable_updates: bool,
            use_preemptible_vms: bool,
            tags: dict=None):

        deployment = cls(gcp_wrapper, name, zone)

        network_resource = NETWORK_TEMPLATE.format(name=deployment.network_name)
        instance_template_resource = INSTANCE_TEMPLATE.format(
            project=gcp_wrapper.project_id,
            sourceImage=source_image,
            name=deployment.template_name,
            machineType=machine_type,
            imageProject=image_project,
            zone=zone,
            ssh_user=ssh_user,
            ssh_public_key=ssh_public_key,
            network=deployment.network_name,
            diskSizeGb=disk_size,
            diskType=disk_type,
            usePreemptibleVMs=use_preemptible_vms,
            deploymentName=deployment.name)
        instance_group_resource = MANAGED_INSTANCE_GROUP_TEMPLATE.format(
            name=deployment.instance_group_name,
            instance_template_name=deployment.template_name,
            size=node_count,
            zone=zone,
            network=deployment.network_name)
        external_firewall_resource = EXTERNAL_FIREWALL_TEMPLATE.format(
            name=deployment.firewall_name,
            network=deployment.network_name)
        internal_firewall_resource = INTERNAL_FIREWALL_TEMPLATE.format(
            name=deployment.firewall_name,
            network=deployment.network_name,
            deploymentName=deployment.name)

        deployment_config = {
            'resources': [yaml.load(network_resource),
                          yaml.load(instance_template_resource),
                          yaml.load(instance_group_resource),
                          yaml.load(external_firewall_resource),
                          yaml.load(internal_firewall_resource)]
        }

        if disable_updates and image_project == 'coreos-cloud':
            user_data = {
                'key': 'user-data',
                'value': IGNITION_CONFIG
            }
            deployment_config['resources'][1]['properties']['properties']['metadata']['items'].append(user_data)

        gcp_wrapper.create_deployment(name, deployment_config, tags=tags)
        return deployment

    @property
    def instance_names(self):
        # only returns the names of the
        for instance in self.gcp_wrapper.list_group_instances(self.instance_group_name, self.zone):
            yield instance['instance'].split('/')[-1]

    @property
    def hosts(self):
        """ order of return here determines cluster composition, so make sure its consistent
        """
        output_list = list()
        for name in self.instance_names:
            info = self.gcp_wrapper.get_instance_network_properties(name, self.zone)
            output_list.append(Host(private_ip=info['networkIP'], public_ip=info['accessConfigs'][0]['natIP']))
        return sorted(output_list)

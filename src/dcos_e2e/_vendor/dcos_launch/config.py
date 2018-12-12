""" Module for defining and validating user-provided configuration
"""
import logging
import os
import sys
import uuid

import requests
import cerberus
import yaml

from ..dcos_launch import util
from ..dcos_launch.platforms import aws, gcp

log = logging.getLogger(__name__)


def expand_path(path: str, relative_dir: str) -> str:
    """ Returns an absolute path by performing '~' and '..' substitution target path

    path: the user-provided path
    relative_dir: the absolute directory to which `path` should be seen as
        relative
    """
    path = os.path.expanduser(path)
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(relative_dir, path))


def load_config(config_path: str) -> dict:
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as ex:
        raise util.LauncherError('InvalidYaml', None) from ex
    except FileNotFoundError as ex:
        raise util.LauncherError('MissingConfig', None) from ex


def validate_url(field, value, error):
    if not value.startswith('http'):
        error(field, 'Not a valid HTTP URL')


def load_ssh_private_key(doc):
    if doc.get('key_helper') == 'true':
        return 'unset'
    if 'ssh_private_key_filename' not in doc:
        return util.NO_TEST_FLAG
    return util.read_file(doc['ssh_private_key_filename'])


class LaunchValidator(cerberus.Validator):
    """ Needs to use unintuitive pattern so that child validator can be created
    for validated the nested dcos_config. See:
    http://docs.python-cerberus.org/en/latest/customize.html#instantiating-custom-validators
    """
    def __init__(self, *args, **kwargs):
        super(LaunchValidator, self).__init__(*args, **kwargs)
        assert 'config_dir' in kwargs, 'This class must be supplied with the config_dir kwarg'
        self.config_dir = kwargs['config_dir']

    def _normalize_coerce_expand_local_path(self, value):
        if not value:
            return value
        return expand_path(value, self.config_dir)


def _expand_error_dict(errors: dict) -> str:
    message = ''
    for key, errors in errors.items():
        sub_message = 'Field: {}, Errors: '.format(key)
        for e in errors:
            if isinstance(e, dict):
                sub_message += _expand_error_dict(e)
            else:
                sub_message += e
            sub_message += '\n'
        message += sub_message
    return message


def _raise_errors(validator: LaunchValidator):
    message = _expand_error_dict(validator.errors)
    raise util.LauncherError('ValidationError', message)


def get_validated_config_from_path(config_path: str) -> dict:
    config = load_config(config_path)
    config_dir = os.path.dirname(config_path)
    return get_validated_config(config, config_dir)


def get_validated_config(user_config: dict, config_dir: str) -> dict:
    """ Returns validated a finalized argument dictionary for dcos-launch
    Given the huge range of configuration space provided by this configuration
    file, it must be processed in three steps (common, provider-specifc,
    platform-specific)
    Args:
        use_config: options (perhaps incomplete) provided by the user
        config_dir: path for the config file for resolving relative
            file links
    """
    owner = os.environ.get('USER')
    if owner:
        user_config.setdefault('tags', {'owner': owner})
    # validate against the fields common to all configs
    user_config['config_dir'] = config_dir
    validator = LaunchValidator(COMMON_SCHEMA, config_dir=config_dir, allow_unknown=True)
    if not validator.validate(user_config):
        _raise_errors(validator)

    # add provider specific information to the basic validator
    provider = validator.normalized(user_config)['provider']
    if provider == 'onprem':
        validator.schema.update(ONPREM_DEPLOY_COMMON_SCHEMA)
    elif provider == 'terraform':
        validator.schema.update(TERRAFORM_COMMON_SCHEMA)
    elif provider in ('aws', 'azure'):
        validator.schema.update(TEMPLATE_DEPLOY_COMMON_SCHEMA)
    elif provider == 'dcos-engine':
        validator.schema.update(DCOS_ENGINE_SCHEMA)
    else:
        raise Exception('Unknown provider!: {}'.format(provider))

    # validate again before attempting to add platform information
    if not validator.validate(user_config):
        _raise_errors(validator)

    # use the intermediate provider-validated config to add the platform schema
    platform = validator.normalized(user_config)['platform']
    if provider == 'terraform' and 'ssh_user' in user_config['terraform_config']:
        if platform in ('gcp', 'gce'):
            user_config['terraform_config']['gcp_ssh_user'] = user_config['ssh_user']
        else:
            raise Exception('Cannot currently set ssh_user parameter for ' + platform)

    if platform == 'aws':
        region = None
        if provider == 'terraform':
            region = user_config['terraform_config'].get('aws_region')
        else:
            validator.schema.update({
                'disable_rollback': {
                    'type': 'boolean',
                    'required': False,
                    'default': False},
                'zen_helper': {
                    'type': 'boolean',
                    'default': False}})
        validator.schema.update({
            'aws_region': {
                'type': 'string',
                'required': True,
                'default_setter':
                    lambda doc:
                    region if region else
                    os.environ['AWS_REGION'] if 'AWS_REGION' in os.environ else
                    util.set_from_env('AWS_DEFAULT_REGION')}})
        if provider == 'onprem':
            if user_config.get('os_name', 'cent-os-7-dcos-prereqs') == 'cent-os-7-dcos-prereqs':
                user_config['install_prereqs'] = True
                user_config['prereqs_script_filename'] = 'run_centos74_prereqs.sh'
            validator.schema.update(AWS_ONPREM_SCHEMA)
    elif platform in ('gcp', 'gce'):
        if provider != 'terraform':
            validator.schema.update({
                'gce_zone': {
                    'type': 'string',
                    'required': True,
                    'default_setter': lambda doc: util.set_from_env('GCE_ZONE')}})
        # only use gcp here on out
        user_config['platform'] = 'gcp'
        if provider == 'onprem':
            validator.schema.update(GCP_ONPREM_SCHEMA)
    elif platform == 'azure':
        if provider != 'terraform':
            validator.schema.update({
                'azure_location': {
                    'type': 'string',
                    'required': True,
                    'default_setter': lambda doc: util.set_from_env('AZURE_LOCATION')}})
    else:
        raise NotImplementedError()

    # do final validation
    validator.allow_unknown = False
    if not validator.validate(user_config):
        _raise_errors(validator)
    if 'genconf_dir' in user_config:
        if 'dcos_config' in user_config:
            genconf_dir = expand_path(user_config['genconf_dir'], user_config['config_dir'])
            _validate_genconf_scripts(genconf_dir, user_config['dcos_config'])
    return validator.normalized(user_config)


COMMON_SCHEMA = {
    'provider': {
        'type': 'string',
        'required': True,
        'allowed': [
            'aws',
            'azure',
            'dcos-engine',
            'onprem',
            'terraform']},
    'config_dir': {
        'type': 'string',
        'required': False},
    'dcos_version': {
        'type': 'float',
        'required': False},
    'launch_config_version': {
        'type': 'integer',
        'required': True,
        'allowed': [1]},
    'ssh_port': {
        'type': 'integer',
        'required': False,
        'default': 22},
    'ssh_private_key_filename': {
        'type': 'string',
        'coerce': 'expand_local_path',
        'required': False},
    'ssh_private_key': {
        'type': 'string',
        'required': False,
        'default_setter': load_ssh_private_key},
    'ssh_user': {
        'type': 'string',
        'required': False,
        'default': 'core'},
    'key_helper': {
        'type': 'boolean',
        'default': False},
    'tags': {
        'type': 'dict',
        'required': False},
}


TEMPLATE_DEPLOY_COMMON_SCHEMA = {
    # platform MUST be equal to provider when using templates
    'deployment_name': {
        'type': 'string',
        'required': True},
    'platform': {
        'type': 'string',
        'readonly': True,
        'default_setter': lambda doc: doc['provider']},
    'template_url': {
        'type': 'string',
        'required': True,
        'validator': validate_url},
    'template_parameters': {
        'type': 'dict',
        'required': True},
}


def _validate_fault_domain_helper(field, value, error):
    have_primary_region = False
    for region, info in value.items():
        if info['local'] and have_primary_region:
            error(field, 'Cannot have more than one region with masters!')
        elif info['local']:
            have_primary_region = True
    if not have_primary_region:
        error(field, 'Must have one region declared with `local: true` (i.e. the master region)')


def _validate_genconf_dir(field, value, error):
    if not value.endswith('genconf'):
        error(field, 'genconf_dir must be named genconf')


def _validate_genconf_scripts(genconf_dir, dcos_config):
    for script in ('ip_detect', 'ip_detect_public', 'fault_domain_detect'):
        filename_key = script + '_filename'
        if filename_key in dcos_config:
            if os.path.isabs(dcos_config[filename_key]):
                continue
            if not os.path.exists(os.path.join(genconf_dir, dcos_config[filename_key])):
                raise util.LauncherError('FileNotFoundError', '{} script must exist in the genconf dir ({})'.format(
                    dcos_config[filename_key], genconf_dir))


ONPREM_DEPLOY_COMMON_SCHEMA = {
    'deployment_name': {
        'type': 'string',
        'required': True},
    'enable_selinux': {
        'type': 'boolean',
        'default_setter': lambda doc:
            doc.get('dcos_version', 0) >= 1.12 and 'dcos-enterprise' in doc['installer_url'] and
            doc['os_name'] == 'cent-os-7-dcos-prereqs'},
    'platform': {
        'type': 'string',
        'required': True,
        # allow gce but remap it to GCP during validation
        'allowed': ['aws', 'gcp', 'gce']},
    'installer_url': {
        'validator': validate_url,
        'type': 'string',
        'required': True},
    'installer_port': {
        'type': 'integer',
        'default': 9000},
    'num_private_agents': {
        'type': 'integer',
        'required': False,
        'min': 0,
        # note: cannot assume nested schema values will be populated with defaults
        #   when the default setter runs
        'default_setter': lambda doc:
            sum([v.get('num_private_agents',  0) for v in doc['fault_domain_helper'].values()])
            if 'fault_domain_helper' in doc else 0},
    'num_public_agents': {
        'type': 'integer',
        'required': False,
        'min': 0,
        # note: cannot assume nested schema values will be populated with defaults
        #   when the default setter runs
        'default_setter': lambda doc:
            sum([v.get('num_public_agents',  0) for v in doc['fault_domain_helper'].values()])
            if 'fault_domain_helper' in doc else 0},
    'num_masters': {
        'type': 'integer',
        'allowed': [1, 3, 5, 7, 9],
        'required': True},
    'dcos_config': {
        'type': 'dict',
        'required': True,
        'allow_unknown': True,
        'default_setter': lambda doc: yaml.load(util.read_file(os.path.join(doc['genconf_dir'], 'config.yaml'))),
        'schema': {
            'ip_detect_filename': {
                'excludes': 'ip_detect_contents'},
            'ip_detect_public_filename': {
                'excludes': 'ip_detect_public_contents'},
            'fault_domain_detect_filename': {
                'excludes': 'fault_domain_detect_contents'},
            'license_key_filename': {
                'excludes': 'license_key_contents'},
            # the following are fields that will be injected by dcos-launch
            'agent_list': {'readonly': True},
            'public_agent_list': {'readonly': True}
            }
        },
    'genconf_dir': {
        'type': 'string',
        'required': False,
        'default': 'genconf',
        'validator': _validate_genconf_dir
        },
    'fault_domain_helper': {
        'type': 'dict',
        'required': False,
        'keyschema': {'type': 'string'},
        'valueschema': {
            'type': 'dict',
            'schema': {
                'num_zones': {
                    'required': True,
                    'type': 'integer',
                    'default': 1},
                'num_private_agents': {
                    'required': True,
                    'type': 'integer',
                    'default': 0},
                'num_public_agents': {
                    'required': True,
                    'type': 'integer',
                    'default': 0},
                'local': {
                    'required': True,
                    'type': 'boolean',
                    'default': False}
                }
            },
        'validator': _validate_fault_domain_helper
    },
    'prereqs_script_filename': {
        'type': 'string',
        'default': 'install_prereqs.sh'
    },
    'install_prereqs': {
        'type': 'boolean',
        'required': False,
        'default': False
    },
    'onprem_install_parallelism': {
        'type': 'integer',
        'required': False,
        'default': 10
    },
}


AWS_ONPREM_SCHEMA = {
    'aws_key_name': {
        'type': 'string',
        'dependencies': {
            'key_helper': False}},
    'os_name': {
        'type': 'string',
        # not required because machine image can be set directly
        'required': False,
        'default': 'cent-os-7-dcos-prereqs',
        'allowed': list(aws.OS_AMIS.keys())},
    'bootstrap_os_name': {
        'type': 'string',
        'required': False,
        # bootstrap node requires docker to be installed
        'default': 'cent-os-7.4-with-docker-selinux-disabled',
        'allowed': list(aws.OS_AMIS.keys())},
    'instance_ami': {
        'type': 'string',
        'required': True,
        'default_setter': lambda doc: aws.OS_AMIS[doc['os_name']][doc['aws_region']]},
    'instance_type': {
        'type': 'string',
        'required': True},
    'instance_device_name': {
        'type': 'string',
        'required': True,
        'default_setter': lambda doc: '/dev/xvda' if doc['os_name'] == 'coreos' else '/dev/sda1'},
    'bootstrap_instance_ami': {
        'type': 'string',
        'required': True,
        'default_setter': lambda doc: aws.OS_AMIS[doc['bootstrap_os_name']][doc['aws_region']]},
    'bootstrap_instance_type': {
        'type': 'string',
        'required': True,
        'default': 'm4.xlarge'},
    'bootstrap_instance_device_name': {
        'type': 'string',
        'required': True,
        'default_setter': lambda doc: '/dev/xvda' if doc['bootstrap_os_name'] == 'coreos' else '/dev/sda1'},
    'admin_location': {
        'type': 'string',
        'required': True,
        'default': '0.0.0.0/0'},
    'bootstrap_ssh_user': {
        'required': True,
        'type': 'string',
        'default_setter': lambda doc: aws.OS_SSH_INFO[doc['bootstrap_os_name']].user},
    'ssh_user': {
        'required': True,
        'type': 'string',
        'default_setter': lambda doc: aws.OS_SSH_INFO[doc['os_name']].user},
    'aws_block_device_mappings': {
        'required': False,
        'type': 'list',
        'valueschema': {
            'type': 'dict',
            'allow_unknown': True}},
    'iam_role_permissions': {
        'required': False,
        'type': 'list',
        'valueschema': {
            'type': 'dict',
            'schema': {
                'Resource': {
                    'type': 'list',
                    'required': True},
                'Action': {
                    'required': True,
                    'type': 'list'},
                'Effect': {
                    'required': True,
                    'allowed': ['Allow', 'Deny']}}}},
}


def get_platform_dependent_url(url_to_format: str, error_msg: str) -> str:
    """ Format download url to be os-specific
    :param url_to_format: download url containing braces "{}" to be replaced by os-specific word
    :param error_msg: error message to raise if system platform is not recognized
    :return: os-matching url
    """
    if sys.platform in ['linux', 'linux2']:
        return url_to_format.format('linux')
    elif sys.platform == 'darwin':
        return url_to_format.format('darwin')
    elif sys.platform == 'win32':
        return url_to_format.format('windows')
    else:
        raise Exception(error_msg)


DCOS_ENGINE_SCHEMA = {
    'deployment_name': {
        'type': 'string',
        'required': True},
    'dcos_engine_version': {
        'type': 'string',
        'default_setter': lambda doc: get_latest_github_release('Azure', 'dcos-engine', '0.2.0')
    },
    'dcos_engine_tarball_url': {
        'type': 'string',
        'default_setter': lambda doc: get_platform_dependent_url(
            'https://github.com/Azure/dcos-engine/releases/download/v{0}/dcos-engine-v{0}-{1}-amd64.tar.gz'.
                format(doc['dcos_engine_version'], '{}'),
            'No DCOS-Engine distribution for {}'.format(sys.platform))},
    'acs_template_filename': {
        'type': 'string',
        'required': False},
    'dcos_engine_orchestrator_release': {
        'type': 'string',
        'default': '1.11'},
    'platform': {
        'type': 'string',
        'readonly': True,
        'default': 'azure'},
    'ssh_public_key': {
        'type': 'string',
        'required': False},
    'num_masters': {
        'type': 'integer',
        'allowed': [1, 3, 5, 7, 9],
        'required': True},
    'master_vm_size': {
        'type': 'string',
        'default': 'Standard_D2_v2'},
    'num_windows_private_agents': {
        'type': 'integer',
        'default': 0},
    'windows_private_vm_size': {
        'type': 'string',
        'default': 'Standard_D2_v2'},
    'num_windows_public_agents': {
        'type': 'integer',
        'default': 0},
    'windows_public_vm_size': {
        'type': 'string',
        'default': 'Standard_D2_v2'},
    'num_linux_private_agents': {
        'type': 'integer',
        'default': 0},
    'linux_private_vm_size': {
        'type': 'string',
        'default': 'Standard_D2_v2'},
    'num_linux_public_agents': {
        'type': 'integer',
        'default': 0},
    'linux_public_vm_size': {
        'type': 'string',
        'default': 'Standard_D2_v2'},
    'windows_admin_user': {
        'type': 'string',
        'default': 'azureuser'},
    'windows_admin_password': {
        'type': 'string',
        'default': 'Replacepassword123'},
    'linux_admin_user': {
        'type': 'string',
        'default': 'azureuser'},
    'template_parameters': {
        'type': 'dict'},
    'dcos_linux_bootstrap_url': {
        'type': 'string',
        'required': False},
    'dcos_windows_bootstrap_url': {
        'type': 'string',
        'required': False},
    'windows_publisher': {
        'type': 'string',
        'default': 'MicrosoftWindowsServer'
    },
    'windows_offer': {
        'type': 'string',
        'default': 'WindowsServerSemiAnnual'
    },
    'windows_sku': {
        'type': 'string',
        'default': 'Datacenter-Core-1803-with-Containers-smalldisk'
    },
    'windows_image_source_url': {
        'type': 'string',
        'required': False},
    'ssh_user': {
        'type': 'string',
        'required': True,
        'readonly': True,
        'default_setter': lambda doc: doc['linux_admin_user']},
}


def deduce_image_project(doc: dict):
    src_image = doc['source_image']
    if 'centos' in src_image or 'cent-os' in src_image:
        return 'centos-cloud'
    if 'rhel' in src_image:
        return 'rhel-cloud'
    if 'ubuntu' in src_image:
        return 'ubuntu-os-cloud'
    if 'coreos' in src_image:
        return 'coreos-cloud'
    if 'debian' in src_image:
        return 'debian-cloud'

    raise util.LauncherError('ValidationError', """Couldn't deduce the image project for your source image. Please
                             specify the "image_project" parameter in your dcos-launch config. Possible values are:
                             centos-cloud, rhel-cloud, ubuntu-os-cloud, coreos-cloud and debian-cloud.""")


GCP_ONPREM_SCHEMA = {
    'machine_type': {
        'type': 'string',
        'required': False,
        'default': 'n1-standard-4'},
    'os_name': {
        # To see all image families: https://cloud.google.com/compute/docs/images
        'type': 'string',
        'required': False,
        'default': 'coreos'},
    'source_image': {
        'type': 'string',
        'required': False,
        'default_setter': lambda doc: 'family/' + gcp.OS_IMAGE_FAMILIES.get(doc['os_name'], doc['os_name'])},
    'image_project': {
        'type': 'string',
        'required': False,
        'default_setter': deduce_image_project},
    'ssh_public_key': {
        'type': 'string',
        'required': False},
    'disk_size': {
        'type': 'integer',
        'required': False,
        'default': 42},
    'disk_type': {
        'type': 'string',
        'required': False,
        'default': 'pd-ssd'},
    # FIXME: GCP should also have a well-defined bootstrap node
    'bootstrap_ssh_user': {
        'required': True,
        # cannot  set this as it MUST be ssh_user (there is no separate BS node configuration for GCP)
        'readonly': True,
        'type': 'string',
        'default_setter': lambda doc: doc['ssh_user']},
    'disable_updates': {
        'type': 'boolean',
        'required': False,
        'default': False},
    'use_preemptible_vms': {
        'type': 'boolean',
        'required': False,
        'default': False},
}


def set_key_helper(platform: str, terraform_config: dict):
    if platform in ('gcp', 'gce'):
        return 'gcp_ssh_pub_key_file' not in terraform_config
    elif platform == 'azure':
        return 'ssh_pub_key' not in terraform_config
    elif platform == 'aws':
        return 'ssh_key_name' not in terraform_config
    raise Exception('Platform {} unrecognized'.format(platform))


def get_latest_github_release(org: str, repo: str, default: str):
    try:
        response = requests.get('https://api.github.com/repos/{}/{}/releases/latest'.format(org, repo))
        return response.json()['tag_name'][1:]
    except Exception as e:
        log.error('Failed to get latest {} version. Defaulting to {}. Error details: {}'.format(repo, default, repr(e)))
        return default


TERRAFORM_COMMON_SCHEMA = {
    'dcos-enterprise': {
        'type': 'boolean',
        'default': False},
    'terraform_version': {
        'type': 'string',
        'default_setter': lambda doc: get_latest_github_release('hashicorp', 'terraform', '0.11.6')
    },
    'terraform_tarball_url': {
        'type': 'string',
        'readonly': True,
        'default_setter': lambda doc: get_platform_dependent_url(
            'https://releases.hashicorp.com/terraform/{0}/terraform_{0}_{1}_amd64.zip'.format(doc['terraform_version'],
                                                                                              sys.platform),
            'No Terraform distribution for {}'.format(sys.platform))},
    'platform': {
        'type': 'string',
        'required': True,
        # allow gce but remap it to GCP during validation
        'allowed': ['aws', 'gcp', 'gce', 'azure']},
    'terraform_config': {
        'type': 'dict',
        'default': dict()},
    'init_dir': {
        'type': 'string',
        'default_setter': lambda doc: 'terraform-init-' + str(uuid.uuid4())},
    'terraform_dcos_version': {
        'type': 'string',
        'default': 'master'},
    'terraform_dcos_enterprise_version': {
        'type': 'string',
        'default': 'master'},
    'key_helper': {
        'type': 'boolean',
        'default_setter': lambda doc: set_key_helper(doc['platform'], doc['terraform_config'])},
}

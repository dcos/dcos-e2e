import abc
import json
import logging
import os
import subprocess
import sys

import cryptography.hazmat.backends
import pkg_resources
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .. import dcos_launch
from .. import dcos_test_utils
import yaml

log = logging.getLogger(__name__)

MOCK_SSH_KEY_DATA = 'ssh_key_data'
MOCK_KEY_NAME = 'my_key_name'
MOCK_VPC_ID = 'vpc-foo-bar'
MOCK_SUBNET_ID = 'subnet-foo-bar'
MOCK_GATEWAY_ID = 'gateway-foo-bar'
MOCK_STACK_ID = 'this-is-a-important-test-stack::deadbeefdeadbeef'
NO_TEST_FLAG = 'NO PRIVATE SSH KEY PROVIDED - CANNOT TEST'


json_prettyprint_args = {
    "sort_keys": True,
    "indent": 2,
    "separators": (',', ':')
}


def write_json(filename, data):
    with open(filename, "w+") as f:
        return json.dump(data, f, **json_prettyprint_args)


def json_prettyprint(data):
    return json.dumps(data, **json_prettyprint_args)


def load_json(filename):
    try:
        with open(filename) as f:
            return json.load(f)
    except ValueError as ex:
        raise ValueError("Invalid JSON in {0}: {1}".format(filename, ex)) from ex


def set_from_env(key):
    """ If key is set in env, return its value, else raise an error
    """
    if key in os.environ:
        return os.environ[key]
    raise LauncherError(
        'MissingParameter', '{} must be set in local env, but was not found'.format(key))


def read_file(filename: str):
    with open(filename) as f:
        return f.read().strip()


def stub(output):
    def accept_any_args(*args, **kwargs):
        return output
    return accept_any_args


def get_temp_config_path(tmpdir, name, update: dict = None):
    config = yaml.load(
        pkg_resources.resource_string(dcos_launch.__name__, 'sample_configs/{}'.format(name)).decode('utf-8'))
    if update is not None:
        config.update(update)
    new_config_path = tmpdir.join('my_config.yaml')
    new_config_path.write(yaml.dump(config))
    return str(new_config_path)


class DeploymentError(Exception):
    pass


class LauncherError(Exception):
    def __init__(self, error, msg):
        self.error = error
        self.msg = msg

    def __repr__(self):
        return '{}: {}'.format(self.error, self.msg if self.msg else self.__cause__)


class AbstractLauncher(metaclass=abc.ABCMeta):
    def get_ssh_client(self, user='ssh_user'):
        return dcos_test_utils.ssh_client.SshClient(self.config[user], self.config['ssh_private_key'])

    def __init__(self, config: dict, env=None):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def wait(self):
        raise NotImplementedError()

    def describe(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    def install_dcos(self):
        # Only implemented in onprem. For other deployment methods, dcos installation occurs in the wait() step.
        pass

    def test(self, args: list, env_dict: dict, test_host: str=None, test_port: int=22, details: dict=None) -> int:
        """ Connects to master host with SSH and then run the internal integration test

        Args:
            args: a list of args that will follow the py.test command
            env_dict: the env to use during the test
        """
        if args is None:
            args = list()
        if self.config['ssh_private_key'] == NO_TEST_FLAG or 'ssh_user' not in self.config:
            raise LauncherError('MissingInput', 'DC/OS Launch is missing sufficient SSH info to run tests!')
        if details is None:
            details = self.describe()
        # populate minimal env if not already set. Note: use private IPs as this test is from
        # within the cluster
        # required for 1.8
        dcos_version = self.config.get('dcos_version')
        if dcos_version:
            env_dict['DCOS_CLI_URL'] = 'https://downloads.dcos.io/cli/testing/binaries/dcos/linux/x86-64/master/dcos' \
                if dcos_version == 'master' else \
                'https://downloads.dcos.io/binaries/cli/linux/x86-64/dcos-{}/dcos'.format(dcos_version)
        if 'DNS_SEARCH' not in env_dict:
            env_dict['DNS_SEARCH'] = 'false'
        if 'DCOS_PROVIDER' not in env_dict:
            env_dict['DCOS_PROVIDER'] = self.config['provider']
        # required for 1.8 and 1.9
        if 'MASTER_HOSTS' not in env_dict:
            env_dict['MASTER_HOSTS'] = ','.join(m['private_ip'] for m in details['masters'])
        if 'PUBLIC_MASTER_HOSTS' not in env_dict:
            env_dict['PUBLIC_MASTER_HOSTS'] = ','.join(m['private_ip'] for m in details['masters'])
        if 'SLAVE_HOSTS' not in env_dict:
            env_dict['SLAVE_HOSTS'] = ','.join(m['private_ip'] for m in details['private_agents'])
        if 'PUBLIC_SLAVE_HOSTS' not in env_dict:
            env_dict['PUBLIC_SLAVE_HOSTS'] = ','.join(m['private_ip'] for m in details['public_agents'])
        if 'DCOS_DNS_ADDRESS' not in env_dict:
            env_dict['DCOS_DNS_ADDRESS'] = 'http://' + details['masters'][0]['private_ip']
        # check for any environment variables that contain spaces
        env_dict = {e: "'{}'".format(env_dict[e]) if ' ' in env_dict[e] else env_dict[e] for e in env_dict}
        env_string = ' '.join(['{}={}'.format(e, env_dict[e]) for e in env_dict])
        arg_string = ' '.join(args)
        # To support 1.8.9-EE, try using the dcos-integration-test-ee folder if possible
        pytest_cmd = """ "source /opt/mesosphere/environment.export &&
cd `find /opt/mesosphere/active/ -name dcos-integration-test* | sort | tail -n 1` &&
{env} py.test {args}" """.format(env=env_string, args=arg_string)
        log.info('Running integration test...')
        if test_host is None:
            test_host = details['masters'][0]['public_ip']
        if ':' in test_host:
            test_host, test_port = test_host.split(':')
        return try_to_output_unbuffered(self.config, test_host, pytest_cmd, test_port)


def try_to_output_unbuffered(info, test_host: str, bash_cmd: str, port: int) -> int:
    """ Tries to run a command and directly output to STDOUT

    Args:
        test_host: ip string for host to connect to
        bash_cmd: string to be passed to BASH
        port: SSH port to use on test_host

    Returns:
        return code of bash_cmd (int)
    """
    ssh_client = dcos_test_utils.ssh_client.SshClient(info['ssh_user'], info['ssh_private_key'])
    ssh_client.wait_for_ssh_connection(test_host, port=port)
    try:
        ssh_client.command(test_host, ['bash', '-c', bash_cmd], port=port, stdout=sys.stdout.buffer)
    except subprocess.CalledProcessError as e:
        log.exception('Test run failed!')
        return e.returncode
    return 0


def convert_host_list(host_list):
    """ Makes Host tuples more readable when using describe
    """
    return [{'private_ip': h.private_ip, 'public_ip': h.public_ip} for h in host_list]


def generate_rsa_keypair(key_size=2048, priv_key_format=serialization.PrivateFormat.PKCS8):
    """Generate an RSA keypair.
    Create new RSA keypair with an exponent of 65537. Serialize the public
    key OpenSSH format that is used by providers for specifying access keys
    Serialize the private key in the PKCS#8 (RFC 3447) format.
    Args:
        bits (int): the key length in bits.
    Returns:
        (private key, public key) 2-tuple, both unicode objects holding the
        serialized keys
    """
    crypto_backend = cryptography.hazmat.backends.default_backend()

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=crypto_backend)

    privkey_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=priv_key_format,
        encryption_algorithm=serialization.NoEncryption())

    public_key = private_key.public_key()
    pubkey_pem = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH)

    return privkey_pem, pubkey_pem

""" This module is intended to provide a thin wrapper for the dcos-cli *binary*

The dcos-cli in some versions is highly dependent upon state and is not the most direct
interface for interacting with a DC/OS cluster. Under the hood, the CLI is just a helper
for making calls to the HTTP REST APIs so often users will get better results by using
the :class:`~dcos_test_utils.dcos_api.DcosApiSession` object for direct API access
"""
import logging
import os
import platform
import shutil
import stat
import subprocess
import tempfile
from typing import Optional

import requests

log = logging.getLogger(__name__)

DCOS_CLI_URL = os.getenv('DCOS_CLI_URL', 'https://downloads.dcos.io/binaries/cli/linux/x86-64/dcos-1.12/dcos')


class DcosCli():
    """ This wrapper assists in setting up the CLI and running CLI commands in subprocesses

    :param cli_path: path to a binary with executable permissions already set
    :type cli_path: str
    """
    def __init__(self, cli_path: str):
        self.path = os.path.abspath(os.path.expanduser(cli_path))
        updated_env = os.environ.copy()
        # make sure the designated CLI is on top of the PATH
        updated_env.update({
            'PATH': "{}:{}".format(
                os.path.dirname(self.path),
                os.environ['PATH']),
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONUNBUFFERED': 'x',
        })

        if 'coreos' in platform.platform():
            updated_env.update({
                'LC_ALL': 'C.UTF-8'
            })

        if 'LANG' not in updated_env:
            updated_env.update({
                'LANG': 'C.UTF-8'
            })

        self.env = updated_env

    @classmethod
    def new_cli(
        cls,
        download_url: str=DCOS_CLI_URL,
        tmpdir: Optional[str]=None
    ):
        """Download and set execute permission for a new dcos-cli binary

        :param download_url: URL of the dcos-cli binary to be used.
            If not set, a stable cli will be used.
        :type download_url: str
        :param tmpdir: path to a temporary directory to contain the executable.
            If not set, a temporary directory will be created.
        :type tmpdir: Optional[str]
        """
        if tmpdir is None:
            tmpdir = tempfile.mkdtemp()
        dcos_cli_path = os.path.join(tmpdir, "dcos")
        requests.packages.urllib3.disable_warnings()
        with open(dcos_cli_path, 'wb') as f:
            r = requests.get(download_url, stream=True, verify=True)
            for chunk in r.iter_content(8192):
                f.write(chunk)

        # make binary executable
        st = os.stat(dcos_cli_path)
        os.chmod(dcos_cli_path, st.st_mode | stat.S_IEXEC)

        return cls(dcos_cli_path)

    @staticmethod
    def clear_cli_dir():
        """Remove the CLI state directory.

        Cluster and installed plugins are stored in the CLI state directory.
        Remove this directory to reset the CLI to its initial state.
        """
        path = os.path.expanduser("~/.dcos")
        if os.path.exists(path):
            shutil.rmtree(path)

    def exec_command(self, cmd: str, stdin=None) -> tuple:
        """Execute CLI command and processes result.

        This method expects that process won't block.

        :param cmd: Program and arguments
        :type cmd: str
        :param stdin: File to use for stdin
        :type stdin: File
        :returns: A tuple with stdout and stderr
        :rtype: (str, str)
        """

        log.info('CMD: {!r}'.format(cmd))

        try:
            process = subprocess.run(
                cmd,
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env,
                check=True)
        except subprocess.CalledProcessError as e:
            if e.stderr:
                stderr = e.stderr.decode('utf-8')
                log.error('STDERR: {}'.format(stderr))
            raise

        stdout, stderr = process.stdout.decode('utf-8'), process.stderr.decode('utf-8')

        log.info('STDOUT: {}'.format(stdout))
        log.info('STDERR: {}'.format(stderr))

        return (stdout, stderr)

    def setup_enterprise(
        self,
        url: str,
        username: Optional[str]=None,
        password: Optional[str]=None
    ):
        """ This method does the CLI setup for a Mesosphere Enterprise DC/OS cluster

        Note:
            This is not an idempotent operation and can only be ran once per CLI state-session

        :param url: URL of EE DC/OS cluster to setup the CLI with
        :type  url: str
        :param username: username to login with
        :type username: Optional[str]
        :param password: password to use with username
        :type password: Optional[str]
        """
        if not username:
            username = os.environ['DCOS_LOGIN_UNAME']
        if not password:
            password = os.environ['DCOS_LOGIN_PW']
        stdout, stderr = self.exec_command(
            ["dcos", "cluster", "setup", str(url), "--no-check",
             "--username={}".format(username), "--password={}".format(password)])
        assert stdout == ''
        assert stderr == ''
        self.exec_command(
            ["dcos", "package", "install", "dcos-enterprise-cli", "--cli", "--yes"])

    def login_enterprise(self, username=None, password=None, provider=None):
        """ Authenticates the CLI with the setup Mesosphere Enterprise DC/OS cluster

        :param username: username to login with
        :type username: str
        :param password: password to use with username
        :type password: str
        :param provider: authentication type to use
        :type password: str
        """
        if not username:
            username = os.environ['DCOS_LOGIN_UNAME']
        if not password:
            password = os.environ['DCOS_LOGIN_PW']

        command = ["dcos", "auth", "login", "--username={}".format(username), "--password={}".format(password)]
        if provider:
            command.append("--provider={}".format(provider))

        _, stderr = self.exec_command(command)
        assert stderr == ''


class DcosCliConfiguration:
    """Represents helper for simple access to the CLI configuration

    :param cli: DcosCli object to grab config data from
    :type cli: DcosCli
    """
    NOT_FOUND_MSG = "Property '{}' doesn't exist"

    def __init__(self, cli: DcosCli):
        self.cli = cli

    def get(self, key: str, default: str=None):
        """Retrieves configuration value from CLI

        :param key: key to grab from CLI config
        :type key: str
        :param default: value to return if key not present
        :type default: str
        """
        try:
            stdout, _ = self.cli.exec_command(
                ["dcos", "config", "show", key])
            return stdout.strip("\n ")
        except subprocess.CalledProcessError as e:
            if self.NOT_FOUND_MSG.format(key) in e.stderr.decode('utf-8'):
                return default
            else:
                raise e

    def set(self, name: str, value: str):
        """Sets configuration option

        :param name: key to set in CLI config
        :type name: str
        :param default: value to set
        :type default: str
        """
        self.cli.exec_command(
            ["dcos", "config", "set", name, value])

    def __getitem__(self, key: str):
        value = self.get(key)
        if value is None:
            raise KeyError("'{}' wasn't found".format(key))

    def __setitem__(self, key, value):
        self.set(key, value)

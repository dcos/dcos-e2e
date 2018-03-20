import logging
import os
import platform
import shutil
import stat
import subprocess
import tempfile

import requests

log = logging.getLogger(__name__)

DCOS_CLI_URL = os.getenv('DCOS_CLI_URL', 'https://downloads.dcos.io/binaries/cli/linux/x86-64/dcos-1.11/dcos')


class DcosCli():

    def __init__(self, cli_path):
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
    def new_cli(cls, download_url=DCOS_CLI_URL):
        tmpdir = tempfile.mkdtemp()
        dcos_cli_path = os.path.join(tmpdir, "dcos")
        requests.packages.urllib3.disable_warnings()
        with open(dcos_cli_path, 'wb') as f:
            r = requests.get(download_url, stream=True, verify=True)
            for chunk in r.iter_content(1024):
                f.write(chunk)

        # make binary executable
        st = os.stat(dcos_cli_path)
        os.chmod(dcos_cli_path, st.st_mode | stat.S_IEXEC)

        return cls(dcos_cli_path)

    @staticmethod
    def clear_cli_dir():
        shutil.rmtree(os.path.expanduser("~/.dcos"))

    def exec_command(self, cmd, stdin=None):
        """Execute CLI command and processes result.

        This method expects that process won't block.

        :param cmd: Program and arguments
        :type cmd: [str]
        :param stdin: File to use for stdin
        :type stdin: file
        :returns: A tuple with stdout and stderr
        :rtype: (str, str)
        """

        log.info('CMD: {!r}'.format(cmd))

        process = subprocess.run(
            cmd,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
            check=True)

        stdout, stderr = process.stdout.decode('utf-8'), process.stderr.decode('utf-8')

        log.info('STDOUT: {}'.format(stdout))
        log.info('STDERR: {}'.format(stderr))

        return (stdout, stderr)

    def setup_enterprise(self, url, username=None, password=None):
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
            ["dcos", "package", "install", "dcos-enterprise-cli", "--cli", "--global", "--yes"])

    def login_enterprise(self, username=None, password=None):
        if not username:
            username = os.environ['DCOS_LOGIN_UNAME']
        if not password:
            password = os.environ['DCOS_LOGIN_PW']
        stdout, stderr = self.exec_command(
            ["dcos", "auth", "login", "--username={}".format(username), "--password={}".format(password)])
        assert stdout == 'Login successful!\n'
        assert stderr == ''


class DcosCliConfiguration:
    """Represents helper for simple access to the CLI configuration"""

    NOT_FOUND_MSG = "Property '{}' doesn't exist"

    def __init__(self, cli: DcosCli):
        self.cli = cli

    def get(self, key, default=None):
        """Retrieves configuration value from CLI"""

        try:
            stdout, _ = self.cli.exec_command(
                ["dcos", "config", "show", key])
            return stdout.strip("\n ")
        except subprocess.CalledProcessError as e:
            if self.NOT_FOUND_MSG.format(key) in e.stderr.decode('utf-8'):
                return default
            else:
                raise e

    def set(self, name, value):
        """Sets configuration option"""
        self.cli.exec_command(
            ["dcos", "config", "set", name, value])

    def __getitem__(self, key: str):
        value = self.get(key)
        if value is None:
            raise KeyError("'{}' wasn't found".format(key))

    def __setitem__(self, key, value):
        self.set(key, value)

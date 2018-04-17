""" Simple, robust SSH client(s) for basic I/O with remote hosts
"""
import asyncio
import logging
import os
import pty
import stat
import subprocess
import tempfile
from contextlib import contextmanager

import retrying

from dcos_test_utils import helpers

log = logging.getLogger(__name__)


SHARED_SSH_OPTS = [
        '-oConnectTimeout=10',
        '-oStrictHostKeyChecking=no',
        '-oUserKnownHostsFile=/dev/null',
        '-oLogLevel=ERROR',
        '-oBatchMode=yes',
        '-oPasswordAuthentication=no']


class Tunnelled():
    def __init__(self, opt_list: list, target: str, port: int):
        """ Abstraction of an already instantiated SSH-tunnel

        Args:
            opt_list: list of SSH options strings. E.G. '-oControlPath=foo'
            target: string in the form user@host
            port: port number to be used for SSH or SCP
        """
        self.opt_list = opt_list
        self.target = target
        self.port = port

    def command(self, cmd: list, **kwargs) -> bytes:
        """ Run a command at the tunnel target

        Args:
            cmd: list of strings that will be sent as a command to the target
            **kwargs: any keywork args that can be passed into
                subprocess.check_output. For more information, see:
                https://docs.python.org/3/library/subprocess.html#subprocess.check_output
        """
        run_cmd = ['ssh', '-p', str(self.port)] + self.opt_list + [self.target] + cmd
        log.debug('Running socket cmd: ' + ' '.join(run_cmd))
        if 'stdout' in kwargs:
            return subprocess.check_call(run_cmd, **kwargs)
        else:
            return subprocess.check_output(run_cmd, **kwargs)

    def copy_file(self, src: str, dst: str) -> None:
        """ Copy a path from localhost to target. If path is a directory, then
        recursive copy will be used

        Args:
            src: local path representing source data
            dst: destination for path
        """
        copy_command = []
        if os.path.isdir(src):
            copy_command.append('-r')
        remote_full_path = '{}:{}'.format(self.target, dst)
        copy_command += [src, remote_full_path]
        cmd = ['scp'] + self.opt_list + ['-P', str(self.port)] + copy_command
        log.debug('Copying {} to {}'.format(src, remote_full_path))
        log.debug('scp command: {}'.format(cmd))
        subprocess.check_call(cmd)


def temp_ssh_key(key: str) -> str:
    key_path = helpers.session_tempfile(key)
    os.chmod(str(key_path), stat.S_IREAD | stat.S_IWRITE)
    return key_path


@contextmanager
def open_tunnel(
        user: str,
        host: str,
        port: int,
        control_path: str,
        key_path: str) -> Tunnelled:
    """ Provides clean setup/tear down for an SSH tunnel
    Args:
        user: SSH user
        key_path: path to a private SSH key
        host: string containing target host
        port: target's SSH port
    """
    target = user + '@' + host
    opt_list = SHARED_SSH_OPTS + [
        '-oControlPath=' + control_path,
        '-oControlMaster=auto']
    base_cmd = ['ssh', '-p', str(port)] + opt_list

    start_tunnel = base_cmd + ['-fnN', '-i', key_path, target]
    log.debug('Starting SSH tunnel: ' + ' '.join(start_tunnel))
    subprocess.check_call(start_tunnel)
    log.debug('SSH Tunnel established!')

    yield Tunnelled(opt_list, target, port)

    close_tunnel = base_cmd + ['-O', 'exit', target]
    log.debug('Closing SSH Tunnel: ' + ' '.join(close_tunnel))
    # after we are done using the tunnel, we do not care about its output
    subprocess.check_call(close_tunnel, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class SshClient:
    """ class for binding SSH user and key to tunnel
    """
    def __init__(self, user: str, key: str):
        self.user = user
        self.key = key
        self.key_path = temp_ssh_key(key)

    def tunnel(self, host: str, port: int=22):
        with tempfile.NamedTemporaryFile() as f:
            return open_tunnel(self.user, host, port, f.name, self.key_path)

    def command(self, host: str, cmd: list, port: int=22, **kwargs) -> bytes:
        with self.tunnel(host, port) as t:
            return t.command(cmd, **kwargs)

    def get_home_dir(self, host: str, port: int=22) -> str:
        """ Returns the SSH home dir
        """
        return self.command(host, ['pwd'], port=port).decode().strip()

    @retrying.retry(wait_fixed=1000)
    def wait_for_ssh_connection(self, host: str, port: int=22) -> None:
        """ Blocks until SSH connection can be established
        """
        self.get_home_dir(host, port)

    def add_ssh_user_to_docker_users(self, host: str, port: int=22):
        self.command(host, ['sudo', 'usermod', '-aG', 'docker', self.user], port=port)


@contextmanager
def make_slave_pty():
    master_pty, slave_pty = pty.openpty()
    yield slave_pty
    os.close(slave_pty)
    os.close(master_pty)


def parse_ip(ip: str) -> (str, int):
    """  takes an IP string and either a hostname and either the given port or
    the default ssh port of 22
    """
    tmp = ip.split(':')
    if len(tmp) == 2:
        return tmp[0], int(tmp[1])
    elif len(tmp) == 1:
        # no port, assume default SSH
        return ip, 22
    else:
        raise ValueError(
            "Expected a string of form <ip> or <ip>:<port> but found a string with more than one " +
            "colon in it. NOTE: IPv6 is not supported at this time. Got: {}".format(ip))


class AsyncSshClient(SshClient):
    def __init__(
            self,
            user: str,
            key: str,
            targets: list,
            process_timeout=120,
            parallelism=10):
        """ SshClient for running against a set of hosts in parallel

        Args:
            user: ssh user name
            key: ssh private key contents
            targets: list of host strings for SSH use (hostname:optional_port)
            process_timeout (optional): how many seconds any given process can run for
            parallelism (optional): how many processes to run at the same time. Rarely is
                a SSH command CPU bound, so this number can be greater than CPU concurrency
        """
        super().__init__(user, key)
        self.process_timeout = process_timeout
        self.__targets = targets
        self.__parallelism = parallelism

    async def _run_cmd_return_dict_async(self, cmd: list) -> dict:
        """ Runs an arbitrary command as an asynchronous subprocess

        Args:
            cmd: list or argument to initialize the process

        Returns:
            dict of the command args, output, returncode, and pid
        """
        log.debug('Starting command: {}'.format(str(cmd)))
        with make_slave_pty() as slave_pty:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=slave_pty,
                env={'TERM': 'linux'})
            stdout = b''
            stderr = b''
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), self.process_timeout)
            except asyncio.TimeoutError:
                try:
                    process.terminate()
                except ProcessLookupError:
                    log.info('process with pid {} not found'.format(process.pid))
                log.error('timeout of {} sec reached. PID {} killed'.format(self.process_timeout, process.pid))

        return {
            "cmd": cmd,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode,
            "pid": process.pid
        }

    async def run(self, sem: asyncio.Semaphore, host: str, cmd: list) -> dict:
        """ Uses SSH tunnel to run a command against a host

        Args:
            sem: semaphore for concurrency control
            host: host string to run copy to
            cmd: argument list to be executed on the remote host

        Returns:
            command result dict (see _run_cmd_return_dict_async)
        """
        hostname, port = parse_ip(host)
        async with sem:
            log.debug('Starting run command on {}'.format(host))
            with self.tunnel(hostname, port) as t:
                full_cmd = ['ssh', '-p', str(t.port)] + t.opt_list + [t.target] + cmd
                result = await self._run_cmd_return_dict_async(full_cmd)
        result['host'] = host
        return result

    async def copy(
            self,
            sem: asyncio.Semaphore,
            host: str,
            local_path: str,
            remote_path: str,
            recursive: bool) -> dict:
        """ uses SCP to copy files to remote host

        Args:
            sem: semaphore for concurrency control
            host: host string to run copy to
            local_path: path that will be copied
            remote_path: where the data will be copied to
            recursive: if True, recursive SCP the local_path to remote_path

        Returns:
            command result dict (see _run_cmd_return_dict_async)
        """
        async with sem:
            log.debug('Starting copy command on {}'.format(host))
            hostname, port = parse_ip(host)
            copy_command = []
            if recursive:
                copy_command.append('-r')
            remote_full_path = '{}@{}:{}'.format(self.user, hostname, remote_path)
            copy_command += [local_path, remote_full_path]
            full_cmd = ['scp'] + SHARED_SSH_OPTS + ['-P', str(port), '-i', self.key_path] + copy_command
            log.debug('copy with command {}'.format(full_cmd))
            result = await self._run_cmd_return_dict_async(full_cmd)
        result['host'] = host
        return result

    async def run_command_on_hosts(self, coroutine_name: str, *args, sem: asyncio.Semaphore=None) -> list:
        """ Starts and waits upon tasks running across all hosts

        Args:
            coroutine_name: either 'copy' or 'run'
            *args: arg list to be passed to copy or run
            sem (optional): semaphore for controlling concurrency. If not supplied, a semaphore
                of the default parallelism will be created

        Returns:
            list of result dicts from _run_cmd_return_dict_async

        """
        if not sem:
            sem = asyncio.Semaphore(self.__parallelism)
        tasks = self.start_command_on_hosts(sem, coroutine_name, *args)
        log.debug('Waiting for asynchonrous processes to finish')
        await asyncio.wait(tasks)
        return [task.result() for task in tasks]

    def start_command_on_hosts(self, sem: asyncio.Semaphore, coroutine_name: str, *args) -> list:
        """ Starts coroutines against all hosts and returns futures

        Args:
            sem: semaphore for blocking job creation to control concurrency
            coroutine_name: either 'copy' or 'run'
            *args: args to be passed to copy or run

        Returns:
            list of futures of the commands that were started

        """
        log.debug('Starting {} with {} to execute on all hosts'.format(coroutine_name, str(args)))
        tasks = []
        for host in self.__targets:
            log.debug('Starting {} on {}'.format(coroutine_name, host))
            tasks.append(asyncio.ensure_future(getattr(self, coroutine_name)(sem, host, *args)))
        return tasks

    def run_command(self, coroutine_name: str, *args) -> list:
        """ Runs a _run_command_on_hosts in an async loop

        Args:
            coroutine_name: either 'copy' or 'run'
            *args: args to pass to copy or run

        Returns:
            list of result dicts
        """
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                self.run_command_on_hosts(coroutine_name, *args))
        finally:
            loop.close()
        return results

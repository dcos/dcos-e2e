""" Tools for facilitating onprem deployments
"""
import asyncio
import logging
import os
import sys

import retrying
from ...dcos_launch import util
from ...dcos_test_utils import onprem, ssh_client

log = logging.getLogger(__name__)


def get_client(
        cluster: onprem.OnpremCluster,
        node_type: str,
        ssh: ssh_client.SshClient,
        parallelism: int=None) -> ssh_client.AsyncSshClient:
    """ Returns an async client for a given Host generator property of cluster
    """
    targets = [host.public_ip for host in getattr(cluster, node_type)]
    if parallelism is None:
        parallelism = len(targets)
    return ssh_client.AsyncSshClient(
        ssh.user,
        ssh.key,
        targets,
        parallelism=parallelism,
        process_timeout=1200)


def check_results(results: list, node_client, tag: str):
    """ loops through result dict list and will print the stderr and raise an exception
    for any nonzero return code
    """
    failures = list()
    for result in results:
        if result['returncode'] != 0:
            log.error('Command failed (exit {}): '.format(result['returncode']) + ' '.join(result['cmd']))
            log.error('STDOUT: \n' + result['stdout'].decode())
            log.error('STDERR: \n' + result['stderr'].decode())
            log_name = generate_log_filename('{}-{}-journald.log'.format(tag, result['host']))
            log.error('Writing journald output to: {}'.format(log_name))
            with open(log_name, 'wb') as f:
                f.write(node_client.command(result['host'], ['journalctl', '-xe']))
            failures.append(log_name)
    if len(failures) > 0:
        raise Exception(
            'The error were encountered in {}. See journald logs for more info: {}'.format(
                tag, ','.join(failures)))


def generate_log_filename(target_name: str):
    if not os.path.exists(target_name):
        return target_name
    i = 1
    while True:
        new_name = target_name + '.' + str(i)
        if not os.path.exists(new_name):
            return new_name
        i += 1


def install_dcos(
        cluster: onprem.OnpremCluster,
        node_client: ssh_client.SshClient,
        prereqs_script_path: str,
        bootstrap_script_url: str,
        parallelism: int):
    """
    Args:
        cluster: cluster abstraction for handling network addresses
        node_client: SshClient that can access all non-bootstrap nodes in `cluster`
        prereqs_script_path: if given, this will be run before preflight on any nodes
        bootstrap_script_url: where the installation script will be pulled from (see do_genconf)
        parallelism: how many concurrent SSH tunnels to run
    """
    # Check to make sure we can talk to the cluster
    for host in cluster.cluster_hosts:
        node_client.wait_for_ssh_connection(host.public_ip)
    # do genconf and configure bootstrap if necessary
    all_client = get_client(cluster, 'cluster_hosts', node_client, parallelism=parallelism)
    # install prereqs if enabled
    if prereqs_script_path:
        log.info('Installing prerequisites on cluster hosts')
        check_results(
            all_client.run_command('run', [util.read_file(prereqs_script_path)]), node_client, 'install_prereqs')
    # download install script from boostrap host and run it
    remote_script_path = '/tmp/install_dcos.sh'
    log.info('Starting preflight')
    check_results(
        do_preflight(all_client, remote_script_path, bootstrap_script_url), node_client, 'preflight')
    log.info('Preflight check succeeded; moving onto deploy')
    check_results(
        do_deploy(cluster, node_client, parallelism, remote_script_path), node_client, 'deploy')
    log.info('Deploy succeeded; moving onto postflight')
    check_results(
        do_postflight(all_client), node_client, 'postflight')
    log.info('Postflight succeeded')


def prepare_bootstrap(
        ssh_tunnel: ssh_client.Tunnelled,
        download_url: str) -> str:
    """ Will setup a host as a 'bootstrap' host. This includes:
    * creating a genconf dir so its not owned by the root user, which happens
        if you run the installer without a genconf directory
    * downloading the installer from `download_url`
    """
    log.info('Setting up installer on bootstrap host')
    ssh_tunnel.command(['mkdir', '-p', 'genconf'])
    bootstrap_home = ssh_tunnel.command(['pwd']).decode().strip()
    installer_path = os.path.join(bootstrap_home, 'dcos_generate_config.sh')
    download_dcos_installer(ssh_tunnel, installer_path, download_url)
    return installer_path


def do_genconf(
        ssh_tunnel: ssh_client.Tunnelled,
        genconf_dir: str,
        installer_path: str):
    """ runs --genconf with the installer
    if an nginx is running, kill it and restart the nginx to host the files
    Args:
        ssh_tunnel: tunnel to the host running the installer
        genconf_dir: path on localhost of genconf directory to transfer
        installer_path: path of the installer on the remote host
    """
    log.debug('Copying config to host bootstrap host')
    installer_dir = os.path.dirname(installer_path)
    # copy config to genconf/
    ssh_tunnel.copy_file(genconf_dir, installer_dir)
    # try --genconf
    log.info('Runnnig --genconf command...')
    ssh_tunnel.command(['sudo', 'bash', installer_path, '--genconf'], stdout=sys.stdout.buffer)
    # if OK we just need to restart nginx
    host_share_path = os.path.join(installer_dir, 'genconf/serve')
    volume_mount = host_share_path + ':/usr/share/nginx/html'
    nginx_service_name = 'dcos-bootstrap-nginx'
    log.info('Starting nginx server to host bootstrap packages')
    if get_docker_service_status(ssh_tunnel, nginx_service_name):
        ssh_tunnel.command(['sudo', 'docker', 'rm', '-f', nginx_service_name])
    start_docker_service(
        ssh_tunnel,
        nginx_service_name,
        ['--publish=80:80', '--volume=' + volume_mount, 'nginx'])


def curl(download_url: str, out_path: str) -> list:
    """ returns a robust curl command in list form
    """
    return ['curl', '-fLsSv', '--retry', '20', '-Y', '100000', '-y', '60',
            '--create-dirs', '-o', out_path, download_url]


@retrying.retry(wait_fixed=3000, stop_max_delay=300 * 1000)
def download_dcos_installer(ssh_tunnel: ssh_client.Tunnelled, installer_path: str, download_url: str):
    """Response status 403 is fatal for curl's retry. Additionally, S3 buckets
    have been returning 403 for valid uploads for 10-15 minutes after CI finished build
    Therefore, give a five minute buffer to help stabilize CI
    """
    log.info('Attempting to download installer from: ' + download_url)
    try:
        ssh_tunnel.command(curl(download_url, installer_path))
    except Exception:
        log.exception('Download failed!')
        raise


def get_docker_service_status(ssh_tunnel: ssh_client.Tunnelled, docker_name: str) -> str:
    return ssh_tunnel.command(
        ['sudo', 'docker', 'ps', '-q', '--filter', 'name=' + docker_name,
         '--filter', 'status=running']).decode().strip()


def start_docker_service(ssh_tunnel: ssh_client.Tunnelled, docker_name: str, docker_args: list):
    ssh_tunnel.command(
        ['sudo', 'docker', 'run', '--name', docker_name, '--detach=true'] + docker_args)


def do_preflight(client: ssh_client.AsyncSshClient, remote_script_path: str, bootstrap_script_url: str):
    """ Runs preflight instructions against client
    remote_script_path: where the install script should be downloaded to on the remote host
    bootstrap_script_url: the URL where the install script will be pulled from
    """
    preflight_script_template = """
mkdir -p {remote_script_dir}
{download_cmd}
sudo bash {remote_script_path} --preflight-only master"""
    preflight_script = preflight_script_template.format(
        remote_script_dir=os.path.dirname(remote_script_path),
        download_cmd=' '.join(curl(bootstrap_script_url, remote_script_path)),
        remote_script_path=remote_script_path)
    return client.run_command('run', [preflight_script])


def do_deploy(
        cluster: onprem.OnpremCluster,
        node_client: ssh_client.SshClient,
        parallelism: int,
        remote_script_path: str):
    """ Creates a separate client for each agent command and runs them asynchronously
    based on the chosen parallelism
    """
    # make distinct clients
    master_client = get_client(cluster, 'masters', node_client)
    private_agent_client = get_client(cluster, 'private_agents', node_client)
    public_agent_client = get_client(cluster, 'public_agents', node_client)

    async def await_tasks():
        # make shared semaphore for all
        sem = asyncio.Semaphore(parallelism)
        master_deploy = master_client.start_command_on_hosts(
            sem, 'run', ['sudo', 'bash', remote_script_path, 'master'])
        private_agent_deploy = private_agent_client.start_command_on_hosts(
            sem, 'run', ['sudo', 'bash', remote_script_path, 'slave'])
        public_agent_deploy = public_agent_client.start_command_on_hosts(
            sem, 'run', ['sudo', 'bash', remote_script_path, 'slave_public'])
        results = list()
        for task_list in (master_deploy, private_agent_deploy, public_agent_deploy):
            if task_list:
                await asyncio.wait(task_list)
                results.extend([task.result() for task in task_list])
        return results

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(await_tasks())
    finally:
        loop.close()
    return results


def do_postflight(client: ssh_client.AsyncSshClient):
    """ Runs a script that will check if DC/OS is operational without needing to authenticate
    """
    postflight_script = """
T=900
if [ -f /opt/mesosphere/etc/dcos-diagnostics-runner-config.json ]; then
    for check_type in node-poststart cluster; do
        until OUT=$(sudo /opt/mesosphere/bin/dcos-shell /opt/mesosphere/bin/dcos-diagnostics check $check_type) \
                || [[ T -eq 0 ]]; do
            sleep 1
            let T=T-1
        done
        RETCODE=$?
        echo $OUT
        if [[ RETCODE -ne 0 ]]; then
            exit $RETCODE
        fi
        T=900
    done
else
    until OUT=$(sudo /opt/mesosphere/bin/./3dt --diag) || [[ T -eq 0 ]]; do
        sleep 1
        let T=T-1
    done
    RETCODE=$?
    for value in $OUT; do
        echo $value
    done
fi
exit $RETCODE
"""
    return client.run_command('run', [postflight_script])

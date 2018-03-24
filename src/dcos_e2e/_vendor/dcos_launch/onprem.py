import abc
import json
import logging
import os
import shutil
import typing

import pkg_resources

import yaml
from ..dcos_launch import util
from ..dcos_launch.platforms import onprem as platforms_onprem
from dcos_e2e._vendor.dcos_test_utils import onprem

log = logging.getLogger(__name__)


class AbstractOnpremLauncher(util.AbstractLauncher, metaclass=abc.ABCMeta):
    def get_bootstrap_host(self):
        raise NotImplementedError()

    def get_cluster_hosts(self):
        raise NotImplementedError()

    def get_onprem_cluster(self):
        return onprem.OnpremCluster.from_hosts(
            bootstrap_host=self.get_bootstrap_host(),
            cluster_hosts=self.get_cluster_hosts(),
            num_masters=int(self.config['num_masters']),
            num_private_agents=int(self.config['num_private_agents']),
            num_public_agents=int(self.config['num_public_agents']))

    def get_bootstrap_ssh_client(self):
        return self.get_ssh_client(user='bootstrap_ssh_user')

    def get_completed_onprem_config(self) -> typing.Tuple[dict, str]:
        """ Will fill in the necessary and/or recommended sections of the config file, including:
        * starting a ZK backend if left undefined
        * filling in the master_list for a static exhibitor backend
        * adding ip-detect script
        * adding ip-detect-public script
        * adding fault domain real or logical script

        Returns:
            config dict, path to genconf directory
        """
        cluster = self.get_onprem_cluster()
        onprem_config = self.config['dcos_config']
        # Every install will need a cluster-clocal bootstrap URL with this installer
        onprem_config['bootstrap_url'] = 'http://' + cluster.bootstrap_host.private_ip
        # Its possible that the masters may live outside the cluster being installed
        if 'master_list' not in onprem_config:
            onprem_config['master_list'] = json.dumps([h.private_ip for h in cluster.masters])
        # First, try and retrieve the agent list from the cluster
        # if the user wanted to use exhibitor as the backend, then start it
        exhibitor_backend = onprem_config.get('exhibitor_storage_backend')
        if exhibitor_backend == 'zookeeper' and 'exhibitor_zk_hosts' not in onprem_config:
            zk_service_name = 'dcos-bootstrap-zk'
            with self.get_bootstrap_ssh_client().tunnel(cluster.bootstrap_host.public_ip) as t:
                if not platforms_onprem.get_docker_service_status(t, zk_service_name):
                    platforms_onprem.start_docker_service(
                        t,
                        zk_service_name,
                        ['--publish=2181:2181', '--publish=2888:2888', '--publish=3888:3888', 'jplock/zookeeper'])
            onprem_config['exhibitor_zk_hosts'] = cluster.bootstrap_host.private_ip + ':2181'
        elif exhibitor_backend == 'static' and 'master_list' not in onprem_config:
            onprem_config['master_list'] = [h.private_ip for h in cluster.masters]

        # Check for ip-detect configuration and inject defaults if not present
        # set the simple default IP detect script if not provided
        genconf_dir = self.config['genconf_dir']
        if not os.path.exists(genconf_dir):
            os.makedirs(genconf_dir)
        for script in ('ip_detect', 'ip_detect_public', 'fault_domain_detect'):
            script_hyphen = script.replace('_', '-')
            default_path_local = os.path.join(genconf_dir, script_hyphen)
            filename_key = script + '_filename'

            if (script == 'fault_domain_detect'):
                if 'fault_domain_helper' in self.config:
                    # fault_domain_helper is enabled; use it
                    with open(default_path_local, 'w') as f:
                        f.write(self._fault_domain_helper())
                    continue
                elif onprem_config.get('fault_domain_enabled') == 'false':
                    # fault domain is explicitly disabled, so inject nothing.
                    # if disabled implicitly, the injected default won't be used
                    continue

            if filename_key in onprem_config:
                if not onprem_config[script + '_filename'].startswith('genconf'):
                    raise util.LauncherError(
                        'ValidationError',
                        'Only files in the genconf folder will be copied')
                local_script_path = onprem_config[filename_key].replace('genconf', genconf_dir)
                if not os.path.exists(local_script_path):
                    raise util.LauncherError(
                        'MissingInput',
                        '{} script must exist at the given path ({})'.format(
                            script_hyphen, local_script_path))
            elif script + '_contents' in onprem_config:
                continue
            elif os.path.exists(default_path_local):
                continue
            elif script == 'ip_detect_public':
                # this is a special case where DC/OS does not expect this field by default
                onprem_config[filename_key] = os.path.join('genconf', script_hyphen)

            # use a sensible default
            shutil.copyfile(
                pkg_resources.resource_filename(
                    'dcos_e2e._vendor.dcos_launch', script_hyphen + '/{}.sh'.format(self.config['platform'])),
                default_path_local)

        with open(os.path.join(genconf_dir, 'config.yaml'), 'w') as f:
            f.write(yaml.safe_dump(onprem_config))
        log.debug('Generated cluster configuration: {}'.format(onprem_config))
        return onprem_config, genconf_dir

    def _fault_domain_helper(self) -> str:
        """ Will create a script with cluster hostnames baked in so that
        an arbitary cluster/zone composition can be provided
        Note: agent count has already been validated by the config module so
            we can assume everything will be correct here
        """
        region_zone_map = dict()
        cluster = self.get_onprem_cluster()
        public_agents = cluster.get_public_agent_ips()
        private_agents = cluster.get_private_agent_ips()
        masters = cluster.get_master_ips()
        case_str = ""
        case_template = """
{hostname})
    REGION={region}
    ZONE={zone} ;;
"""
        for region, info in self.config['fault_domain_helper'].items():
            z_i = 0  # zones iterator
            z_mod = info['num_zones']  # zones modulo
            zones = list(range(1, z_mod + 1))
            if info['local']:
                while len(masters) > 0:
                    hostname = self.get_ssh_client().command(
                        masters.pop().public_ip, ['hostname']).decode().strip('\n')
                    region_zone_map[hostname] = region + '-' + str(zones[z_i % z_mod])
                    z_i += 1
            for _ in range(info['num_public_agents']):
                if len(public_agents) > 0:
                    # distribute out the nodes across the zones until we run out
                    hostname = self.get_ssh_client().command(
                        public_agents.pop().public_ip, ['hostname']).decode().strip('\n')
                    region_zone_map[hostname] = region + '-' + str(zones[z_i % z_mod])
                    z_i += 1
            for _ in range(info['num_private_agents']):
                if len(private_agents) > 0:
                    # distribute out the nodes across the zones until we run out
                    hostname = self.get_ssh_client().command(
                        private_agents.pop().public_ip, ['hostname']).decode().strip('\n')
                    region_zone_map[hostname] = region + '-' + str(zones[z_i % z_mod])
                    z_i += 1
            # now format the hostname-zone map into a BASH case statement
            for host, zone in region_zone_map.items():
                case_str += case_template.format(
                    hostname=host,
                    region=region,
                    zone=zone)

        # double escapes and curly brackets are needed for python interpretation
        bash_script = """
#!/bin/bash
hostname=$(hostname)
case $hostname in
{cases}
esac
echo "{{\\"fault_domain\\":{{\\"region\\":{{\\"name\\": \\"$REGION\\"}},\\"zone\\":{{\\"name\\": \\"$ZONE\\"}}}}}}"
"""
        return bash_script.format(cases=case_str)

    def wait(self):
        cluster = self.get_onprem_cluster()
        bootstrap_host = cluster.bootstrap_host.public_ip
        bootstrap_ssh_client = self.get_bootstrap_ssh_client()
        bootstrap_ssh_client.wait_for_ssh_connection(bootstrap_host)
        with bootstrap_ssh_client.tunnel(bootstrap_host) as t:
            installer_path = platforms_onprem.prepare_bootstrap(t, self.config['installer_url'])
            complete_config, genconf_dir = self.get_completed_onprem_config()
            platforms_onprem.do_genconf(t, genconf_dir, installer_path)
        platforms_onprem.install_dcos(
            cluster,
            self.get_ssh_client(),
            self.config['prereqs_script_filename'] if self.config['install_prereqs'] else None,
            complete_config['bootstrap_url'] + '/dcos_install.sh',
            self.config['onprem_install_parallelism'])

    def describe(self):
        """ returns host information stored in the config as
        well as the basic provider info
        """
        cluster = self.get_onprem_cluster()
        return {
            'bootstrap_host': util.convert_host_list([cluster.bootstrap_host])[0],
            'masters': util.convert_host_list(cluster.get_master_ips()),
            'private_agents': util.convert_host_list(cluster.get_private_agent_ips()),
            'public_agents': util.convert_host_list(cluster.get_public_agent_ips())}

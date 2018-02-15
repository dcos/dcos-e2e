""" Utilities to assist with orchestrating and testing an onprem deployment
"""
import copy
import itertools
import logging
from typing import List

import requests

from dcos_test_utils.helpers import Host

log = logging.getLogger(__name__)


def log_and_raise_if_not_ok(response: requests.Response):
    if not response.ok:
        log.error(response.content.decode())
        response.raise_for_status()


class OnpremCluster:

    def __init__(
            self,
            masters: List[Host],
            private_agents: List[Host],
            public_agents: List[Host],
            bootstrap_host: Host):
        """ An abstration for an arbitrary group of servers to be used
        as bootstrapping node and deployment nodes for DC/OS
        Args:
            masters: list of Hosts tuples to be used as masters
            private_agents: list of Host tuples to be used as private agents
            public_agents: list of Host tuples to be used as public agents
            bootstrap_host: Host tuple for the bootstrap host I.E. has installer
                downloaded to it and perhaps hosts a bootstrap ZooKeeper
        """
        self.masters = masters
        self.private_agents = private_agents
        self.public_agents = public_agents
        self.bootstrap_host = bootstrap_host
        assert all(h.private_ip for h in self.hosts), (
            'All cluster hosts require a private IP. hosts: {}'.format(repr(self.hosts))
        )

    def get_master_ips(self):
        return copy.copy(self.masters)

    def get_private_agent_ips(self):
        return copy.copy(self.private_agents)

    def get_public_agent_ips(self):
        return copy.copy(self.public_agents)

    @classmethod
    def from_hosts(cls, bootstrap_host, cluster_hosts, num_masters, num_private_agents, num_public_agents):
        masters, private_agents, public_agents = (
            cls.partition_cluster(cluster_hosts, num_masters, num_private_agents, num_public_agents))
        return cls(
            masters=masters,
            private_agents=private_agents,
            public_agents=public_agents,
            bootstrap_host=bootstrap_host,
        )

    @property
    def hosts(self):
        return self.masters + self.private_agents + self.public_agents + (
            [self.bootstrap_host] if self.bootstrap_host else []
        )

    @property
    def cluster_hosts(self):
        return self.masters + self.private_agents + self.public_agents

    @staticmethod
    def partition_cluster(
            cluster_hosts: List[Host],
            num_masters: int,
            num_agents: int,
            num_public_agents: int):
        """Return (masters, agents, public_agents) from hosts."""
        hosts_iter = iter(sorted(cluster_hosts))
        return (
            list(itertools.islice(hosts_iter, num_masters)),
            list(itertools.islice(hosts_iter, num_agents)),
            list(itertools.islice(hosts_iter, num_public_agents)),
        )

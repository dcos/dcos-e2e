"""
Helpers for determining the state of a DC/OS cluster.
"""
import logging

from retrying import retry
import requests


log = logging.getLogger(__name__)


@retry(
    stop_max_delay=900000,
    wait_fixed=2000
)
def diagnostics_up(master):
    """
    Retries querying the Mesos instances on the given master node every 2
    seconds for a maxmium time of 10 minutes until it replies sucessfully.
    """
    log.info('Polling for Mesos Up.')
    _mesos_leader_opinion_func(master)


@retry(
    stop_max_delay=300000,
    wait_fixed=2000
)
def adminrouter_marathon(superuser_api_session):
    """
    Return mesos leader via Admin Router
    """
    response = superuser_api_session.get('/marathon')
    response.raise_for_status()


@retry(
    stop_max_delay=60000,
    wait_fixed=2000,
    retry_on_result=lambda res: res is None
)
def dns_mesos_leader(master, user):
    """
    Get IP for current Mesos leader from MesosDNS
    """
    cmd = ['dig', 'leader.mesos', 'a', '+short']
    result = master.run(args=cmd, user=user)
    return result.stdout.strip().decode(encoding='utf8')


@retry(
    stop_max_delay=60000,
    wait_fixed=2000,
    retry_on_result=lambda res: res is None
)
def dns_marathon_leader(master, user):
    """
    Get IP for current Marathon leader from MesosDNS
    """
    cmd = ['dig', 'marathon.mesos', 'a', '+short']
    result = master.run(args=cmd, user=user)
    return result.stdout.strip().decode(encoding='utf8')


@retry(
    stop_max_delay=60000,
    wait_fixed=5000,
    retry_on_result=lambda res: res is None
)
def mesos_consensus(masters):
    """
    Retries querying Mesos instances on the given master nodes every 5
    seconds for a maxmium time of 1 minutes until they reach consensus
    on the Mesos leader.
    """
    log.info('Polling for Mesos consensus.')
    return _consensus(_mesos_leader_opinion_func, masters)


@retry(
    stop_max_delay=60000,
    wait_fixed=5000,
    retry_on_result=lambda res: res is None
)
def marathon_consensus(masters):
    """
    Retries querying Marathon instances on the given master nodes every 5
    seconds for a maxmium time of 1 minutes until they reach consensus on
    the Marathon leader.
    """
    log.info('Polling for Marathon consensus.')
    return _consensus(_marathon_leader_opinion_func, masters)


@retry(
    stop_max_delay=900000,
    wait_fixed=2000
)
def mesos_up(master):
    """
    Retries querying the Mesos instances on the given master node every 2
    seconds for a maxmium time of 10 minutes until it replies sucessfully.
    """
    log.info('Polling for Mesos Up.')
    _mesos_leader_opinion_func(master)


def _mesos_leader_opinion_func(master):
    """
    Queries the Mesos instance on the given master node for its
    opinion on the current leading Mesos master.
    """
    response = requests.get(
        'https://{master_ip}:5050/master/redirect'.format(
            master_ip=master.ip_address
        ),
        verify=False,
        allow_redirects=False,
        timeout=1
    )
    response.raise_for_status()
    mesos_leader_ip = (response.headers['Location'][2:])[:-5]
    return mesos_leader_ip


@retry(
    stop_max_delay=900000,
    wait_fixed=2000
)
def marathon_up(master):
    """
    Retries querying the Mesos instances on the given master node every 2
    seconds for a maxmium time of 10 minutes until it replies sucessfully.
    """
    log.info('Polling for Marathon Up.')
    _marathon_leader_opinion_func(master)


def _marathon_leader_opinion_func(master):
    """
    Queries the Marathon instance on the given master node for its
    opinion on the current leading Marathon master.
    """
    response = requests.get(
        'https://{master_ip}:8443/ping'.format(
            master_ip=master.ip_address
        ),
        verify=False,
        timeout=1
    )
    response.raise_for_status()
    marathon_leader_ip = (response.headers['X-Marathon-Leader'][8:])[:-5]
    return marathon_leader_ip


def _consensus(opinion_func, nodes):
    """
    Generic consensus procedure that takes an opinion
    function and evaluates whether the nodes agree
    on a common opinion.
    """
    opinions = set([])
    for node in nodes:
        opinion = opinion_func(node)
        log.info(
            'Node {node_ip} provided opinion {node_opinion}'.format(
                node_ip=node.ip_address,
                node_opinion=opinion
            )
        )
        opinions.add(opinion)
    if len(opinions) == 1:
        return next(iter(opinions))
    return None

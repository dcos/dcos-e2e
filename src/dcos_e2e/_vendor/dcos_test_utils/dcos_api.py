""" Utilities for interacting with a DC/OS instance via REST API

Most DC/OS deployments will have auth enabled, so this module includes
DcosUser and DcosAuth to be attached to a DcosApiSession. Additionally,
it is sometimes necessary to query specific nodes within a DC/OS cluster,
so there is ARNodeApiClientMixin to allow querying nodes without boilerplate
to set the correct port and scheme.
"""
import copy
import logging
import os
from typing import List, Optional

import requests
import retrying

from dcos_test_utils import (
    diagnostics,
    marathon,
    package,
    helpers
)

log = logging.getLogger(__name__)


class DcosUser:
    """A lightweight user representation for grabbing the auth info and stashing it"""
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.auth_token = None
        self.auth_cookie = None

    @property
    def auth_header(self):
        return {'Authorization': 'token={}'.format(self.auth_token)}


class DcosAuth(requests.auth.AuthBase):
    def __init__(self, auth_token: str):
        self.auth_token = auth_token

    def __call__(self, request):
        request.headers['Authorization'] = 'token={}'.format(self.auth_token)
        return request


class Exhibitor(helpers.RetryCommonHttpErrorsMixin, helpers.ApiClientSession):
    def __init__(self, default_url: helpers.Url, session: Optional[requests.Session]=None,
                 exhibitor_admin_password: Optional[str]=None):
        super().__init__(default_url)
        if session is not None:
            self.session = session
        if exhibitor_admin_password is not None:
            # Override auth to use HTTP basic auth with the provided admin password.
            self.session.auth = requests.auth.HTTPBasicAuth('admin', exhibitor_admin_password)


class DcosApiSession(helpers.ARNodeApiClientMixin, helpers.RetryCommonHttpErrorsMixin, helpers.ApiClientSession):
    def __init__(
            self,
            dcos_url: str,
            masters: Optional[List[str]],
            slaves: Optional[List[str]],
            public_slaves: Optional[List[str]],
            auth_user: Optional[DcosUser],
            exhibitor_admin_password: Optional[str]=None):
        """Proxy class for DC/OS clusters. If any of the host lists (masters,
        slaves, public_slaves) are provided, the wait_for_dcos function of this
        class will wait until provisioning is complete. If these lists are not
        provided, then there is no ground truth and the cluster will be assumed
        the be in a completed state.

        Args:
            dcos_url: address for the DC/OS web UI.
            masters: list of Mesos master advertised IP addresses.
            slaves: list of Mesos slave/agent advertised IP addresses.
            public_slaves: list of public Mesos slave/agent advertised IP addresses.
            auth_user: use this user's auth for all requests
                Note: user must be authenticated explicitly or call self.wait_for_dcos()
        """
        super().__init__(helpers.Url.from_string(dcos_url))
        self.master_list = masters
        self.slave_list = slaves
        self.public_slave_list = public_slaves
        self.auth_user = auth_user
        self.exhibitor_admin_password = exhibitor_admin_password

    @classmethod
    def create(cls):
        api = cls(**cls.get_args_from_env())
        api._authenticate_default_user()
        return api

    @staticmethod
    def get_args_from_env():
        """ Provides the required arguments for a unauthenticated cluster
        """
        dcos_acs_token = os.getenv('DCOS_ACS_TOKEN')
        if dcos_acs_token is None:
            auth_user = DcosUser(helpers.CI_CREDENTIALS)
        else:
            auth_user = DcosUser({'token': dcos_acs_token})
        masters = os.getenv('MASTER_HOSTS')
        slaves = os.getenv('SLAVE_HOSTS')
        public_slaves = os.getenv('PUBLIC_SLAVE_HOSTS')
        return {
            'auth_user': auth_user,
            'dcos_url': os.getenv('DCOS_DNS_ADDRESS', 'http://leader.mesos'),
            'masters': masters.split(',') if masters else None,
            'slaves': slaves.split(',') if slaves else None,
            'public_slaves': public_slaves.split(',') if public_slaves else None}

    @property
    def masters(self):
        return sorted(self.master_list)

    @property
    def slaves(self):
        return sorted(self.slave_list)

    @property
    def public_slaves(self):
        return sorted(self.public_slave_list)

    @property
    def all_slaves(self):
        return sorted(self.slaves + self.public_slaves)

    def set_node_lists_if_unset(self):
        """ Sets the expected cluster topology to be the observed cluster
        topology from exhibitor and mesos. I.E. if masters, slave, or
        public_slaves were not provided, accept whatever is currently available
        """
        if self.master_list is None:
            log.debug('Master list not provided, setting from exhibitor...')
            r = self.get('/exhibitor/exhibitor/v1/cluster/list')
            r.raise_for_status()
            self.master_list = sorted(r.json()['servers'])
            log.info('Master list set as: {}'.format(self.masters))
        if self.slave_list is not None and self.public_slave_list is not None:
            return
        r = self.get('/mesos/slaves')
        r.raise_for_status()
        slaves_json = r.json()['slaves']
        if self.slave_list is None:
            log.debug('Private slave list not provided; fetching from mesos...')
            self.slave_list = sorted(
                [s['hostname'] for s in slaves_json if s['attributes'].get('public_ip') != 'true'])
            log.info('Private slave list set as: {}'.format(self.slaves))
        if self.public_slave_list is None:
            log.debug('Public slave list not provided; fetching from mesos...')
            self.public_slave_list = sorted(
                [s['hostname'] for s in slaves_json if s['attributes'].get('public_ip') == 'true'])
            log.info('Public slave list set as: {}'.format(self.public_slaves))

    @retrying.retry(wait_fixed=2000, stop_max_delay=120 * 1000)
    def _authenticate_default_user(self):
        """retry default auth user because in some deployments,
        the auth endpoint might not be routable immediately
        after Admin Router is up. DcosUser.authenticate()
        will raise exception if authorization fails
        """
        if self.auth_user is None:
            return
        log.info('Attempting authentication')
        # explicitly use a session with no user authentication for requesting auth headers
        r = self.post('/acs/api/v1/auth/login', json=self.auth_user.credentials, auth=None)
        r.raise_for_status()
        log.info('Received authentication blob: {}'.format(r.json()))
        self.auth_user.auth_token = r.json()['token']
        self.auth_user.auth_cookie = r.cookies['dcos-acs-auth-cookie']
        log.info('Authentication successful')
        # Set requests auth
        self.session.auth = DcosAuth(self.auth_user.auth_token)

    @retrying.retry(wait_fixed=1000,
                    retry_on_result=lambda ret: ret is False,
                    retry_on_exception=lambda x: False)
    def _wait_for_marathon_up(self):
        r = self.get('/marathon/v2/info')
        # http://mesosphere.github.io/marathon/api-console/index.html
        # 200 at /marathon/v2/info indicates marathon is up.
        if r.status_code == 200:
            log.info("Marathon is up.")
            return True
        else:
            msg = "Waiting for Marathon, resp code is: {}"
            log.info(msg.format(r.status_code))
            return False

    @retrying.retry(wait_fixed=1000)
    def _wait_for_zk_quorum(self):
        """Queries exhibitor to ensure all master ZKs have joined
        """
        r = self.get('/exhibitor/exhibitor/v1/cluster/status')
        if not r.ok:
            log.warning('Exhibitor status not available')
            r.raise_for_status()
        status = r.json()
        log.info('Exhibitor cluster status: {}'.format(status))
        zk_nodes = sorted([n['hostname'] for n in status])
        # zk nodes will be private but masters can be public
        assert len(zk_nodes) == len(self.masters), 'ZooKeeper has not formed the expected quorum'

    @retrying.retry(wait_fixed=1000,
                    retry_on_result=lambda ret: ret is False,
                    retry_on_exception=lambda x: False)
    def _wait_for_slaves_to_join(self):
        r = self.get('/mesos/master/slaves')
        if r.status_code != 200:
            msg = "Mesos master returned status code {} != 200 "
            msg += "continuing to wait..."
            log.info(msg.format(r.status_code))
            return False
        data = r.json()
        # Check that there are all the slaves the test knows about. They are all
        # needed to pass the test.
        num_slaves = len(data['slaves'])
        if num_slaves >= len(self.all_slaves):
            msg = "Sufficient ({} >= {}) number of slaves have joined the cluster"
            log.info(msg.format(num_slaves, self.all_slaves))
            return True
        else:
            msg = "Current number of slaves: {} < {}, continuing to wait..."
            log.info(msg.format(num_slaves, self.all_slaves))
            return False

    @retrying.retry(wait_fixed=1000,
                    retry_on_result=lambda ret: ret is False,
                    retry_on_exception=lambda x: False)
    def _wait_for_dcos_history_up(self):
        r = self.get('/dcos-history-service/ping')
        # resp_code >= 500 -> backend is still down probably
        if r.status_code <= 500:
            log.info("DC/OS History is probably up")
            return True
        else:
            msg = "Waiting for DC/OS History, resp code is: {}"
            log.info(msg.format(r.status_code))
            return False

    @retrying.retry(wait_fixed=1000,
                    retry_on_result=lambda ret: ret is False,
                    retry_on_exception=lambda x: False)
    def _wait_for_dcos_history_data(self):
        ro = self.get('/dcos-history-service/history/last')
        # resp_code >= 500 -> backend is still down probably
        if ro.status_code <= 500:
            json = ro.json()
            # We have observed cases of the returned JSON being '{}'.
            if 'slaves' in json:
                # The json['slaves'] is an array of dicts that must be
                # mapped to set of hostnames so it can be compared with
                # all_slaves.
                # if an agent was removed, it may linger in the history data
                # so simply check that at least the number agents we expect are present
                if len(json['slaves']) >= len(self.all_slaves):
                    return True
                slaves_from_history_service = set(
                    map(lambda x: x['hostname'], json['slaves']))
                log.info('Still waiting for agents to join. Expected: {}, present: {}'.format(
                    self.all_slaves, slaves_from_history_service))
                return False

            log.info(
                'Data on the number of slaves from DC/OS History is not yet '
                'available'
            )

        msg = "Waiting for DC/OS History, resp code is: {}"
        log.info(msg.format(ro.status_code))
        return False

    @retrying.retry(wait_fixed=1000,
                    retry_on_result=lambda ret: ret is False,
                    retry_on_exception=lambda x: False)
    def _wait_for_adminrouter_up(self):
        try:
            # Yeah, we can also put it in retry_on_exception, but
            # this way we will loose debug messages
            self.get('/')
        except requests.ConnectionError as e:
            msg = "Cannot connect to nginx, error string: '{}', continuing to wait"
            log.info(msg.format(e))
            return False
        else:
            log.info("Nginx is UP!")
            return True

    # Retry if returncode is False, do not retry on exceptions.
    @retrying.retry(wait_fixed=2000,
                    retry_on_result=lambda r: r is False,
                    retry_on_exception=lambda _: False)
    def _wait_for_srouter_slaves_endpoints(self):
        # Get currently known agents. This request is served straight from
        # Mesos (no AdminRouter-based caching is involved).
        r = self.get('/mesos/master/slaves')
        assert r.status_code == 200

        data = r.json()
        # only check against the slaves we expect to be in the cluster
        # so we can check that cluster has returned after a failure
        # in which case will will have new slaves and dead slaves
        slaves_ids = sorted(x['id'] for x in data['slaves'] if x['hostname'] in self.all_slaves)

        for slave_id in slaves_ids:
            # AdminRouter's slave endpoint internally uses cached Mesos
            # state data. That is, slave IDs of just recently joined
            # slaves can be unknown here. For those, this endpoint
            # returns a 404. Retry in this case, until this endpoint
            # is confirmed to work for all known agents.
            uri = '/slave/{}/slave%281%29/state.json'.format(slave_id)
            r = self.get(uri)
            if r.status_code == 404:
                return False
            assert r.status_code == 200
            data = r.json()
            assert "id" in data
            assert data["id"] == slave_id

    @retrying.retry(wait_fixed=2000,
                    retry_on_result=lambda r: r is False,
                    retry_on_exception=lambda _: False)
    def _wait_for_metronome(self):
        # Although this is named `wait_for_metronome`, some of the waiting
        # done in this function is, implicitly, for Admin Router.
        r = self.get('/service/metronome/v1/jobs')
        expected_error_codes = {
            404: ('It may be the case that Admin Router is returning a 404 '
                  'despite the Metronome service existing because it uses a cache. '
                  'This cache is updated periodically.'),
            504: ('Metronome is returning a Gateway Timeout Error.'
                  'It may be that the service is still starting up.')
        }
        log.info('Metronome status code:')
        log.info(r.status_code)
        log.info('Metronome response body:')
        log.info(r.text)

        if r.status_code in expected_error_codes or r.status_code >= 500:
            error_message = expected_error_codes.get(r.status_code)
            if error_message:
                log.info(error_message)
            log.info('Continuing to wait for Metronome')
            return False

        assert r.status_code == 200, "Expecting status code 200 for Metronome but got {} with body {}"\
            .format(r.status_code, r.content)

    @retrying.retry(wait_fixed=2000,
                    retry_on_result=lambda r: r is False,
                    retry_on_exception=lambda _: False)
    def _wait_for_all_healthy_services(self):
        r = self.health.get('units')
        r.raise_for_status()

        all_healthy = True
        for unit in r.json()['units']:
            if unit['health'] != 0:
                log.info("{} service health: {}".format(unit['id'], unit['health']))
                all_healthy = False

        return all_healthy

    def wait_for_dcos(self):
        self._wait_for_adminrouter_up()
        self._authenticate_default_user()
        wait_for_hosts = os.getenv('WAIT_FOR_HOSTS', 'true') == 'true'
        master_list_set = self.master_list is not None
        slave_list_set = self.slave_list is not None
        public_slave_list_set = self.public_slave_list is not None
        node_lists_set = all([master_list_set, slave_list_set, public_slave_list_set])
        if wait_for_hosts and not node_lists_set:
            raise Exception(
                'This cluster is set to wait for hosts, however, not all host lists '
                'were suppplied. Please set all three environment variables of MASTER_HOSTS, '
                'SLAVE_HOSTS, and PUBLIC_SLAVE_HOSTS to the appropriate cluster IPs (comma separated). '
                'Alternatively, set WAIT_FOR_HOSTS=false in the environment to use whichever hosts '
                'are currently registered.')
        self.set_node_lists_if_unset()
        self._wait_for_marathon_up()
        self._wait_for_zk_quorum()
        self._wait_for_slaves_to_join()
        self._wait_for_dcos_history_up()
        self._wait_for_srouter_slaves_endpoints()
        self._wait_for_dcos_history_data()
        self._wait_for_metronome()
        self._wait_for_all_healthy_services()

    def copy(self):
        """ Create a new client session without cookies, with the authentication intact.
        """
        new = copy.deepcopy(self)
        new.session.cookies.clear()
        return new

    def get_user_session(self, user):
        """Returns a copy of this client but with auth for user (can be None)
        """
        new = self.copy()
        new.session.auth = None
        new.auth_user = None
        if user is not None:
            new.auth_user = user
            new._authenticate_default_user()
        return new

    @property
    def exhibitor(self):
        if self.exhibitor_admin_password is None:
            # No basic HTTP auth. Access Exhibitor via the adminrouter.
            default_url = self.default_url.copy(path='exhibitor')
        else:
            # Exhibitor is protected with HTTP basic auth, which conflicts with adminrouter's auth. We must bypass
            # the adminrouter and access Exhibitor directly.
            default_url = helpers.Url.from_string('http://{}:8181'.format(self.masters[0]))

        return Exhibitor(
            default_url=default_url,
            session=self.copy().session,
            exhibitor_admin_password=self.exhibitor_admin_password)

    @property
    def marathon(self):
        return marathon.Marathon(
            default_url=self.default_url.copy(path='marathon'),
            session=self.copy().session)

    @property
    def metronome(self):
        new = self.copy()
        new.default_url = self.default_url.copy(path='service/metronome/v1')
        return new

    @property
    def cosmos(self):
        return package.Cosmos(
            default_url=self.default_url.copy(path="package"),
            session=self.copy().session)

    @property
    def health(self):
        health_url = self.default_url.copy(query='cache=0', path='system/health/v1')
        return diagnostics.Diagnostics(
            health_url,
            self.masters,
            self.all_slaves,
            session=self.copy().session)

    @property
    def logs(self):
        new = self.copy()
        new.default_url = self.default_url.copy(path='system/v1/logs')
        return new

    @property
    def metrics(self):
        new = self.copy()
        new.default_url = self.default_url.copy(path='/system/v1/metrics/v0')
        return new

    def metronome_one_off(self, job_definition, timeout=300, ignore_failures=False):
        """Run a job on metronome and block until it returns success
        """
        job_id = job_definition['id']

        @retrying.retry(wait_fixed=2000, stop_max_delay=timeout * 1000,
                        retry_on_result=lambda ret: not ret,
                        retry_on_exception=lambda x: False)
        def wait_for_completion():
            r = self.metronome.get('jobs/' + job_id, params={'embed': 'history'})
            r.raise_for_status()
            out = r.json()
            if not ignore_failures and (out['history']['failureCount'] != 0):
                raise Exception('Metronome job failed!: ' + repr(out))
            if out['history']['successCount'] != 1:
                log.info('Waiting for one-off to finish. Status: ' + repr(out))
                return False
            log.info('Metronome one-off successful')
            return True
        log.info('Creating metronome job: ' + repr(job_definition))
        r = self.metronome.post('jobs', json=job_definition)
        helpers.assert_response_ok(r)
        log.info('Starting metronome job')
        r = self.metronome.post('jobs/{}/runs'.format(job_id))
        helpers.assert_response_ok(r)
        wait_for_completion()
        log.info('Deleting metronome one-off')
        r = self.metronome.delete('jobs/' + job_id)
        helpers.assert_response_ok(r)

    def mesos_sandbox_directory(self, slave_id, framework_id, task_id):
        r = self.get('/agent/{}/state'.format(slave_id))
        r.raise_for_status()
        agent_state = r.json()

        try:
            framework = next(f for f in agent_state['frameworks'] if f['id'] == framework_id)
        except StopIteration:
            raise Exception('Framework {} not found on agent {}'.format(framework_id, slave_id))

        try:
            executor = next(e for e in framework['executors'] if e['id'] == task_id)
        except StopIteration:
            raise Exception('Executor {} not found on framework {} on agent {}'.format(task_id, framework_id, slave_id))

        return executor['directory']

    def mesos_sandbox_file(self, slave_id, framework_id, task_id, filename):
        r = self.get(
            '/agent/{}/files/download'.format(slave_id),
            params={'path': self.mesos_sandbox_directory(slave_id, framework_id, task_id) + '/' + filename}
        )
        r.raise_for_status()
        return r.text

    def get_version(self):
        version_metadata = self.get('/dcos-metadata/dcos-version.json')
        version_metadata.raise_for_status()
        data = version_metadata.json()
        return data["version"]

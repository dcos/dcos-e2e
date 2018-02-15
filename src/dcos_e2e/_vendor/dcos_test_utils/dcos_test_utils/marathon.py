""" Utilities for integration testing marathon in a deployed DC/OS cluster
"""
import collections
import contextlib
import enum
import logging
import typing

import retrying

from dcos_test_utils.helpers import (ApiClientSession,
                                     RetryCommonHttpErrorsMixin, path_join)

REQUIRED_HEADERS = {'Accept': 'application/json, text/plain, */*'}
FORCE_PARAMS = {'force': 'true'}
Endpoint = collections.namedtuple("Endpoint", ["host", "port", "ip"])
log = logging.getLogger(__name__)


class Container(enum.Enum):
    DOCKER = 'DOCKER'
    MESOS = 'MESOS'
    NONE = None


class Network(enum.Enum):
    HOST = 'HOST'
    USER = 'USER'
    BRIDGE = 'BRIDGE'


class Healthcheck(enum.Enum):
    HTTP = 'HTTP'
    MESOS_HTTP = 'MESOS_HTTP'


class Marathon(RetryCommonHttpErrorsMixin, ApiClientSession):
    def __init__(self, default_url, session=None):
        super().__init__(default_url)
        if session is not None:
            self.session = session
        self.session.headers.update(REQUIRED_HEADERS)

    def check_app_instances(
            self,
            app_id: str,
            app_instances: int,
            check_health: bool,
            ignore_failed_tasks: bool) -> bool:
        """ Check a marathon app ID and return True if healthy
        Args:
            app_id: marathon app ID ro be checked
            app_instances: number of expected app instances
            check_health: if True, health check status must pass to return True
            ignore_failed_tasks: if False, any failed tasks will result in an exception
        """
        # Some of the counters need to be explicitly enabled now and/or in
        # future versions of Marathon:
        req_params = (('embed', 'apps.lastTaskFailure'),
                      ('embed', 'apps.counts'))

        log.info('Waiting for application to be deployed...')
        r = self.get(path_join('v2/apps', app_id), params=req_params)
        r.raise_for_status()

        data = r.json()
        log.debug('Current application state data: {}'.format(repr(data)))

        if 'lastTaskFailure' in data['app']:
            message = data['app']['lastTaskFailure']['message']
            if not ignore_failed_tasks:
                raise AssertionError('Application deployment failed, reason: {}'.format(message))
            else:
                log.warn('Task failure detected: {}'.format(message))

        check_tasks_running = (data['app']['tasksRunning'] == app_instances)
        check_tasks_healthy = (not check_health or data['app']['tasksHealthy'] == app_instances)

        if check_tasks_running and check_tasks_healthy:
            log.info('Application deployed!')
            return True
        elif not check_tasks_running:
            log.debug('Not all instances are running!')
            return False
        elif not check_tasks_healthy:
            log.debug('Not all instances are healthy!')
            return False
        else:
            log.debug('Still waiting for application to scale...')
            return False

    def get_app_service_endpoints(self, app_id: str) -> typing.List[Endpoint]:
        """ returns endpoint tuples for the given application ID
        """
        r = self.get(path_join('v2/apps', app_id))
        r.raise_for_status()
        data = r.json()
        res = [Endpoint(t['host'], t['ports'][0], t['ipAddresses'][0]['ipAddress'])
               if len(t['ports']) is not 0
               else Endpoint(t['host'], 0, t['ipAddresses'][0]['ipAddress'])
               for t in data['app']['tasks']]
        log.info('Application deployed, running on {}'.format(res))
        return res

    def wait_for_app_deployment(
            self,
            app_id: str,
            app_instances: int,
            check_health: bool,
            ignore_failed_tasks: bool,
            timeout: int):
        """ Retries the check_app_instance function for a limited time
        Args:
            app_id: ID of the marathon app to check
            app_instances: expected number of instances
            check_health: if True, health checks must pass before unblocking
            ignore_failed_tasks: if False, then failed tasks will raise an exception
            timeout: time (in seconds) to wait before raising an exception
        """

        @retrying.retry(
            wait_fixed=5000,
            stop_max_delay=timeout*1000,
            retry_on_result=lambda res: res is False,
            retry_on_exception=lambda ex: False)
        def wait():
            return self.check_app_instances(app_id, app_instances, check_health, ignore_failed_tasks)
        wait()

    def deploy_app(self, app_definition, check_health=True, ignore_failed_tasks=False, timeout=1200):
        """Deploy an app to marathon

        This function deploys an an application and then waits for marathon to
        acknowledge it's successful creation or fails the test.

        The wait for application is immediately aborted if Marathon returns
        nonempty 'lastTaskFailure' field. Otherwise it waits until all the
        instances reach tasksRunning and then tasksHealthy state.

        Args:
            app_definition: a dict with application definition as specified in
                            Marathon API (https://mesosphere.github.io/marathon/docs/rest-api.html#post-v2-apps)
            check_health: wait until Marathon reports tasks as healthy before
                          returning

        Returns:
            A list of named tuples which represent service points of deployed
            applications. I.E:
                [Endpoint(host='172.17.10.202', port=10464), Endpoint(host='172.17.10.201', port=1630)]
        """
        r = self.post('v2/apps', json=app_definition)
        log.info('Response from marathon: {}'.format(repr(r.json())))
        r.raise_for_status()

        try:
            return self.wait_for_app_deployment(
                    app_definition['id'],
                    app_definition['instances'],
                    check_health, ignore_failed_tasks, timeout)
        except retrying.RetryError:
            raise Exception("Application deployment failed - operation was not "
                            "completed in {} seconds.".format(timeout))

    def deploy_pod(self, pod_definition, timeout=1200):
        """Deploy a pod to marathon

        This function deploys an a pod and then waits for marathon to
        acknowledge it's successful creation or fails the test.

        It waits until all the instances reach tasksRunning and then tasksHealthy state.

        Args:
            pod_definition: a dict with pod definition as specified in
                            Marathon API
            timeout: seconds to wait for deployment to finish
        Returns:
            Pod data JSON
        """
        r = self.post('v2/pods', json=pod_definition)
        assert r.ok, 'status_code: {} content: {}'.format(r.status_code, r.content)
        log.info('Response from marathon: {}'.format(repr(r.json())))

        @retrying.retry(wait_fixed=5000, stop_max_delay=timeout * 1000,
                        retry_on_result=lambda ret: ret is False,
                        retry_on_exception=lambda x: False)
        def _wait_for_pod_deployment(pod_id):
            # In the context of the `deploy_pod` function, simply waiting for
            # the pod's status to become STABLE is sufficient. In the future,
            # if test pod deployments become more complex, we should switch to
            # using Marathon's event bus and listen for specific events.
            # See DCOS_OSS-1056.
            r = self.get('v2/pods' + pod_id + '::status')
            r.raise_for_status()
            data = r.json()
            if 'status' in data and data['status'] == 'STABLE':
                # deployment complete
                return data
            log.info('Waiting for pod to be deployed %r', data)
            return False

        try:
            return _wait_for_pod_deployment(pod_definition['id'])
        except retrying.RetryError as ex:
            raise Exception("Pod deployment failed - operation was not "
                            "completed in {} seconds.".format(timeout)) from ex

    def destroy_pod(self, pod_id, timeout=300):
        """Remove a marathon pod

        Abort the test if the removal was unsuccessful.

        Args:
            pod_id: id of the pod to remove
            timeout: seconds to wait for destruction before failing test
        """
        @retrying.retry(wait_fixed=5000, stop_max_delay=timeout * 1000,
                        retry_on_result=lambda ret: not ret,
                        retry_on_exception=lambda x: False)
        def _destroy_pod_complete(deployment_id):
            r = self.get('v2/deployments')
            assert r.ok, 'status_code: {} content: {}'.format(r.status_code, r.content)

            for deployment in r.json():
                if deployment_id == deployment.get('id'):
                    log.info('Waiting for pod to be destroyed')
                    return False
            log.info('Pod destroyed')
            return True

        r = self.delete('v2/pods' + pod_id)
        assert r.ok, 'status_code: {} content: {}'.format(r.status_code, r.content)

        try:
            _destroy_pod_complete(r.headers['Marathon-Deployment-Id'])
        except retrying.RetryError as ex:
            raise Exception("Pod destroy failed - operation was not "
                            "completed in {} seconds.".format(timeout)) from ex

    def destroy_app(self, app_name, timeout=300):
        """Remove a marathon app

        Abort the test if the removal was unsuccessful.

        Args:
            app_name: name of the application to remove
            timeout: seconds to wait for destruction before failing test
        """
        @retrying.retry(wait_fixed=5000, stop_max_delay=timeout * 1000,
                        retry_on_result=lambda ret: not ret,
                        retry_on_exception=lambda x: False)
        def _destroy_complete(deployment_id):
            r = self.get('v2/deployments')
            r.raise_for_status()

            for deployment in r.json():
                if deployment_id == deployment.get('id'):
                    log.info('Waiting for application to be destroyed')
                    return False
            log.info('Application destroyed')
            return True

        r = self.delete(path_join('v2/apps', app_name))
        r.raise_for_status()

        try:
            _destroy_complete(r.json()['deploymentId'])
        except retrying.RetryError:
            raise Exception("Application destroy failed - operation was not "
                            "completed in {} seconds.".format(timeout))

    @contextlib.contextmanager
    def deploy_and_cleanup(self, app_definition, timeout=1200, check_health=True, ignore_failed_tasks=False):
        try:
            yield self.deploy_app(
                app_definition, check_health, ignore_failed_tasks, timeout=timeout)
        finally:
            self.destroy_app(app_definition['id'], timeout)

    @contextlib.contextmanager
    def deploy_pod_and_cleanup(self, pod_definition, timeout=1200):
        try:
            yield self.deploy_pod(pod_definition, timeout=timeout)
        finally:
            self.destroy_pod(pod_definition['id'], timeout)

    def purge(self):
        """ Force deletes all applications, all pods, and then waits
        indefinitely for any deployments to finish
        """
        apps_response = self.get('v2/apps')
        apps_response.raise_for_status()
        for app in apps_response.json()['apps']:
            log.info('Purging application: {}'.format(app['id']))
            self.delete('v2/apps' + app['id'], params=FORCE_PARAMS)
        pods_response = self.get('v2/pods')
        pods_response.raise_for_status()
        for pod in pods_response.json():
            log.info('Deleting pod: {}'.format(pod['id']))
            self.delete('v2/pods' + pod['id'], params=FORCE_PARAMS)
        self.wait_for_deployments_complete()

    @retrying.retry(
        wait_fixed=10 * 1000,
        retry_on_result=lambda res: res is False,
        retry_on_exception=lambda ex: False)
    def wait_for_deployments_complete(self):
        if not self.get('v2/deployments').json():
            return True
        log.info('Deployments in progress, continuing to wait...')
        return False

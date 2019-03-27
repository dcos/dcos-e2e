""" Utilities for integration testing metronome in a deployed DC/OS cluster
"""
import logging

import retrying
import requests

from ..dcos_test_utils import helpers

REQUIRED_HEADERS = {'Accept': 'application/json, text/plain, */*'}
log = logging.getLogger(__name__)


class Jobs(helpers.RetryCommonHttpErrorsMixin, helpers.ApiClientSession):
    """ Specialized client for interacting with DC/OS jobs functionality

    :param default_url: URL of the jobs service to bind to
    :type default_url: helpers.Url
    :param session: option session to bootstrap this session with
    :type session: requests.Session
    """
    def __init__(self, default_url: helpers.Url, session: requests.Session=None):
        super().__init__(default_url)
        if session is not None:
            self.session = session
        self.session.headers.update(REQUIRED_HEADERS)
        self._api_version = '/v1'

    def _http_req_json(self, fn: callable,
                       *args: list,
                       **kwargs: dict) -> dict:
        """Helper method that executes the HTTP request, calls
        `raise_for_status()` and returns the `json()` response.

        `fn` is a callable, such as `self.post`.

        Example:
            self._http_req_json(self.get, 'https://example.com')

        :param fn: Function from helpers to run
        :type fn: callable
        :param args: args
        :type args: list
        :param kwargs: kwargs
        :type kwargs: dict
        :return: JSON response
        :rtype: dict
        """
        r = fn(*args, **kwargs)
        r.raise_for_status()
        return r.json()

    def _is_history_available(self, job_id: str, run_id: str) -> bool:
        """ When job run is finished, history might not be available right ahead.
            This method returns true if run of given id is already present in the history endpoint.
        """
        result = self.details(job_id, history=True)
        history = result['history']
        for field in ('successfulFinishedRuns', 'failedFinishedRuns'):
            for result in history[field]:
                if result['id'] == run_id:
                    return True

        return False

    def wait_for_run(self, job_id: str, run_id: str, timeout=600):
        """Wait for a given run to complete or timeout seconds to
        elapse.

        :param job_id: Job ID
        :type job_id: str
        :param run_id: Run ID
        :type run_id: str
        :param timeout: Time in seconds to wait before giving up
        :type timeout: int
        :return: None

        """

        @retrying.retry(wait_fixed=1000, stop_max_delay=timeout * 1000,
                        retry_on_result=lambda ret: ret is False,
                        retry_on_exception=lambda x: False)
        def _wait_for_run_completion(j_id: str, r_id: str) -> bool:
            try:
                # 200 means the run is still in progress
                self.run_details(job_id=j_id, run_id=r_id)
                log.info('Waiting on job run {} to finish.'.format(r_id))
                return False
            except requests.HTTPError as http_error:
                rc = http_error.response

            # 404 means the run is complete and this is done
            # anything else is a problem and should not happen
            if rc.status_code == 404:
                history_available = self._is_history_available(j_id, r_id)
                if history_available:
                    log.info('Job run {} finished.'.format(r_id))
                    return True
                else:
                    raise requests.HTTPError(
                        'Waiting for job run {} to be finished, but history for that job run is not available'
                        .format(r_id), response=rc)
            else:
                raise requests.HTTPError(
                    'Waiting for job run {} to be finished, but getting HTTP status code {}'
                    .format(r_id, rc.status_code), response=rc)

        try:
            # wait for the run to complete and then return the
            # run's result
            _wait_for_run_completion(job_id, run_id)
        except retrying.RetryError as ex:
            raise Exception("Job run failed - operation was not "
                            "completed in {} seconds.".format(timeout)) from ex

    def details(self, job_id: str, history=False) -> dict:
        """Get the details of a specific Job.

        :param job_id: Job ID
        :type job_id: str
        :param history: Include embedded history in details
        :type history: bool
        :return: Job details as JSON
        :rtype: dict

        """
        url = '{api}/jobs/{job_id}'.format(api=self._api_version,
                                           job_id=job_id)
        params = {'embed': 'history'} if history else None
        return self._http_req_json(self.get, url, params=params)

    def create(self, job_definition: dict) -> dict:
        """Create a new job with given definition.

        :param job_definition: Job definition
        :type job_definition: dict
        :return: Response from Jobs service as JSON
        :rtype: dict

        """
        url = '{api}/jobs'.format(api=self._api_version)
        return self._http_req_json(self.post, url, json=job_definition)

    def destroy(self, job_id: str):
        """Delete an existing job and all data.

        :param job_id: Job ID
        :type job_id: str

        """
        url = '{api}/jobs/{job_id}'.format(
                api=self._api_version, job_id=job_id)
        return self._http_req_json(self.delete,
                                   url,
                                   params={'stopCurrentJobRuns': 'true'})

    def start(self, job_id: str) -> dict:
        """Create a run and return the Run.

        :param job_id: Job ID
        :type job_id: str
        :return: Run creation response from Jobs service
        :rtype: dict

        """
        url = '{api}/jobs/{job_id}/runs'.format(
                api=self._api_version,
                job_id=job_id)
        r_json = self._http_req_json(self.post, url)

        log.info("Started job {}, run id {}".format(job_id, r_json['id']))
        return r_json

    def run(self, job_id: str, timeout=600) -> (bool, dict, dict):
        """Create a run, wait for it to finish, and return whether it was
        successful and the run itself.

        This will run the job immediately and block until
        the run is complete.

        :param job_id: Job ID
        :type job_id: str
        :param timeout: Timeout in seconds
        :type timeout: int
        :return: tuple of success, Run details, Job details
        :rtype: bool, dict, dict
        """
        run_json = self.start(job_id)
        run_id = run_json['id']
        self.wait_for_run(job_id, run_id, timeout)

        result = self.details(job_id, history=True)
        history = result['history']

        for field in ('successfulFinishedRuns', 'failedFinishedRuns'):
            success = field == 'successfulFinishedRuns'
            for job_run in history[field]:
                if job_run['id'] == run_id:
                    return success, job_run, result

        return False, None, result

    def run_details(self, job_id: str, run_id: str) -> dict:
        """Return details about the given Run ID.

        :param job_id: Job ID
        :type job_id: str
        :param run_id: Run ID
        :type run_id: str
        :return: Run details
        :rtype: dict
        """
        url = '{api}/jobs/{job_id}/runs/{run_id}'.format(
                api=self._api_version,
                job_id=job_id,
                run_id=run_id)
        return self._http_req_json(self.get, url)

    def run_stop(self, job_id: str, run_id: str) -> dict:
        """Stop the run `run_id` if it is in-progress.

        :param job_id: Job ID
        :type job_id: str
        :param run_id: Run ID
        :type run_id: str
        :return: JSON response
        :rtype: dict
        """
        url = '{api}/jobs/{job_id}/runs/{run_id}/actions/stop'.format(
                api=self._api_version, job_id=job_id, run_id=run_id)
        return self._http_req_json(self.post, url)

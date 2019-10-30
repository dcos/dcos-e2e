"""Utilities for running and downloading diagnostics reports

Based on the utilities in dcos/dcos-integration-tests test_dcos_diagnostics.py

This is tested via the test_dcos_diagnostics.py module in the dcos-integration-test module in dcos/dcos
"""

import datetime
import logging
import os
import uuid

import retrying

from dcos_test_utils import helpers

from dcos_test_utils.helpers import (
    ARNodeApiClientMixin,
    ApiClientSession,
    RetryCommonHttpErrorsMixin,
    check_json
)

log = logging.getLogger(__name__)


class Diagnostics(ARNodeApiClientMixin, RetryCommonHttpErrorsMixin, ApiClientSession):
    """ Specialized session client for diagnostics service that is aware of the cluster agents

    :param default_url: URL for the diagnostics service API
    :type default_url: helpers.Url
    :param masters: list of master IP strings
    :type masters: list
    :param all_slaves: list of slave IP strings
    :type all_slaves: list
    :param session: Session object to bootstrap this session with
    :type session: requets.Session
    :type use_legacy_api: bool if true then legacy API is used
    """
    def __init__(
            self,
            default_url: helpers.Url,
            masters: list,
            all_slaves: list,
            session=None,
            use_legacy_api=False):
        super().__init__(default_url)
        if session is not None:
            self.session = session
        self.masters = masters
        self.all_slaves = all_slaves
        self.use_legacy_api = use_legacy_api

    def start_diagnostics_job(self, nodes: dict=None):
        """ POSTs to the endpoint that triggers diagnostics report creation

        :param nodes: JSON-like definition of nodes
        :type nodes: dict

        :returns: Response from diagnostics service
        :rtype: requests.Response
        """
        if self.use_legacy_api:
            return self._legacy_start_diagnostics_job(nodes)
        return self._start_diagnostics_job()

    def _start_diagnostics_job(self):
        return self.put('/diagnostics/' + str(uuid.uuid1()))

    def _legacy_start_diagnostics_job(self, nodes: dict = None):
        if nodes is None:
            nodes = {"nodes": ["all"]}
        return self.post('/report/diagnostics/create', json=nodes)

    # stop_max_delay set to 20 minutes to provide enough time for bundle to be
    # created. See DCOS-41819
    @retrying.retry(wait_fixed=2000, stop_max_delay=1200000,
                    retry_on_result=lambda x: x is False)
    def wait_for_diagnostics_job(self, last_datapoint: dict):
        """
        initial value of last_datapoint should be
        last_datapoint = {
            'time': None,
            'value': 0
        }
        """
        if self.use_legacy_api:
            return self._legacy_wait_for_diagnostics_job(last_datapoint)
        return self._wait_for_diagnostics_job()

    def _wait_for_diagnostics_job(self):
        session_response = self.get('/diagnostics')
        response = check_json(session_response)
        for bundle in response:
            if bundle['status'] in {'Unknown', 'Started', 'InProgress'}:
                return False
        return True

    def _legacy_wait_for_diagnostics_job(self, last_datapoint: dict):
        """
        initial value of last_datapoint should be
        last_datapoint = {
            'time': None,
            'value': 0
        }
        """
        session_response = self.get('/report/diagnostics/status/all')
        response = check_json(session_response)
        job_running = False
        percent_done = 0
        for attributes in response.values():
            assert 'is_running' in attributes, '`is_running` field is missing in response'
            assert 'job_progress_percentage' in attributes, '`job_progress_percentage` field is missing'

            if attributes['is_running']:
                percent_done = attributes['job_progress_percentage']
                logging.info("Job is running. Progress: {}".format(percent_done))
                job_running = True
                break

        # if we ran this bit previously, compare the current datapoint with the one we saved
        if last_datapoint['time'] and last_datapoint['value']:
            assert (datetime.datetime.now() - last_datapoint['time']) < datetime.timedelta(seconds=15), (
                "Job is not progressing"
            )
        last_datapoint['value'] = percent_done
        last_datapoint['time'] = datetime.datetime.now()

        return not job_running

    def get_diagnostics_reports(self) -> list:
        """ Gets the complete list of diagnostics reports

        :returns: list of report filenames
        :rtype: list
        """
        if self.use_legacy_api:
            return self._legacy_get_diagnostics_reports()
        return self._get_diagnostics_reports()

    def _get_diagnostics_reports(self) -> list:
        response = check_json(self.get('/diagnostics'))
        return [bundle['id'] for bundle in response if bundle['status'] != 'Deleted']

    def _legacy_get_diagnostics_reports(self) -> list:
        response = check_json(self.get('/report/diagnostics/list/all'))

        def _at_least_one_item(bundle):
            return bundle is not None and isinstance(bundle, list) and len(bundle) > 0

        bundles = []
        for bundle_list in response.values():
            if _at_least_one_item(bundle_list):
                bundles += map(lambda s: os.path.basename(s['file_name']), bundle_list)
        return bundles

    @retrying.retry(stop_max_delay=50000, wait_fixed=2000, retry_on_result=lambda x: x == [])
    def wait_for_diagnostics_reports(self):
        """ Sometimes it may take extra few seconds to list bundles after the job is finished.
        This method will retry until the reports are non empty or 50 seconds has elapsed
        """
        return self.get_diagnostics_reports()

    def download_diagnostics_reports(self, diagnostics_bundles, download_directory=None, master=None):
        """ Given diagnostics bundle names, this method will download them

        Args:
            diagnostics_bundles (List[str]): list of bundle names to download. Result of self.get_diagnostics_reports
            download_directory (str): path, defaults to home directory
        """
        if download_directory is None:
            download_directory = os.path.join(os.path.expanduser('~'))
        if master is None:
            master = self.masters[0]
        if self.use_legacy_api:
            return self._legacy_download_diagnostics_reports(diagnostics_bundles, download_directory, master)
        return self._download_diagnostics_reports(diagnostics_bundles, download_directory, master)

    def _download_diagnostics_reports(self, diagnostics_bundles, download_directory, master):
        for bundle in diagnostics_bundles:
            log.info('Downloading {}'.format(bundle))
            r = self.get(os.path.join('/diagnostics/', bundle, 'file'), stream=True, node=master)
            bundle_path = os.path.join(download_directory, bundle)
            with open(bundle_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

    def _legacy_download_diagnostics_reports(self, diagnostics_bundles, download_directory, master):
        for bundle in diagnostics_bundles:
            log.info('Downloading {}'.format(bundle))
            r = self.get(os.path.join('/report/diagnostics/serve', bundle), stream=True, node=master)
            bundle_path = os.path.join(download_directory, bundle)
            with open(bundle_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

    def delete_bundle(self, diagnostics_bundle: str):
        """ Given diagnostics bundle name, this method will delete it

        Args:
            diagnostics_bundles (str): bundle name to delete. Item of result of self.get_diagnostics_reports
        """
        if self.use_legacy_api:
            self.post('/report/diagnostics/delete/' + diagnostics_bundle)
        self.delete('/diagnostics/' + diagnostics_bundle)

"""Utilities for integration testing package management (https://github.com/dcos/cosmos)
"""

import logging

from dcos_test_utils import helpers

log = logging.getLogger(__name__)


class Cosmos(helpers.RetryCommonHttpErrorsMixin, helpers.ApiClientSession):
    """ Specialized client for interacting with Cosmos (universe gateway) functionality

    :param default_url: URL of the jobs service to bind to
    :type default_url: helpers.Url
    :param session: option session to bootstrap this session with
    :type session: requests.Session
    """
    def __init__(self, default_url: helpers.Url, session=None):
        super().__init__(default_url)
        if session is not None:
            self.session = session

    def _update_headers(self, endpoint, request_version='1', response_version='1'):
        """Set the Content-type and Accept headers

        Args:
            request_version: str Version number of the cosmos API
            response_version: str Version number of the cosmos API
            endpoint: str cosmos API endpoint
        Returns:
            None
        """
        media_type = "application/vnd.dcos.package." + endpoint + \
            "-{action}+json;charset=utf-8;" + \
            "version=v{version}"
        self.session.headers.update({
            'Content-type': media_type.format(action="request", version=request_version),
            'Accept': media_type.format(action="response", version=response_version)
        })

    def _post(self, endpoint, data):
        response = self.post(endpoint, json=data)
        log.info('Response from cosmos: {0}'.format(repr(response.text)))
        response.raise_for_status()
        return response

    def install_package(self, package_name, package_version=None, options=None, app_id=None):
        """Install a package using the cosmos packaging API

        Args:
            package_name: str
            package_version: str
            options: JSON dict
            appId: str

        Returns:
            requests.response object

        Notes:
            Use Marathon.poll_marathon_for_app_deployment to check if the installed app deployed
            successfully (Need the appId from the response)
        """
        self._update_headers('install', response_version='2')
        package = {
            'packageName': package_name
        }
        if package_version is not None:
            package.update({'packageVersion': package_version})
        if options is not None:
            package.update({'options': options})
        if app_id is not None:
            package.update({'appId': app_id})
        return self._post('/install', package)

    def uninstall_package(self, package_name, app_id=None):
        """Uninstall a package using the cosmos packaging API

        Args:
            package_name: str
            app_id: str, should have leading slash

        Returns:
            requests.response object
        """
        self._update_headers('uninstall')
        package = {
            'packageName': package_name
        }
        if app_id is not None:
            package.update({'appId': app_id})
        return self._post('/uninstall', package)

    def list_packages(self):
        """List all packages using the cosmos packaging API

        Returns:
            requests.response object
        """
        self._update_headers('list')
        return self._post('/list', {})

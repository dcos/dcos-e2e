"""Various helpers for test runners and integration testing directly
"""
import atexit
import logging
import os
import tempfile
from collections import namedtuple
from typing import Union
from urllib.parse import urlsplit, urlunsplit

import requests
import retrying

Host = namedtuple('Host', ['private_ip', 'public_ip'])
SshInfo = namedtuple('SshInfo', ['user', 'home_dir'])

log = logging.getLogger(__name__)


# Token valid until 2036 for user albert@bekstil.net
#    {
#        "email": "albert@bekstil.net",
#        "email_verified": true,
#        "iss": "https://dcos.auth0.com/",
#        "sub": "google-oauth2|109964499011108905050",
#        "aud": "3yF5TOSzdlI45Q1xspxzeoGBe9fNxm9m",
#        "exp": 2090884974,
#        "iat": 1460164974
#    }

CI_CREDENTIALS = {'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ik9UQkVOakZFTWtWQ09VRTRPRVpGTlRNMFJrWXlRa015Tnprd1JrSkVRemRCTWpBM1FqYzVOZyJ9.eyJlbWFpbCI6ImFsYmVydEBiZWtzdGlsLm5ldCIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJpc3MiOiJodHRwczovL2Rjb3MuYXV0aDAuY29tLyIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTA5OTY0NDk5MDExMTA4OTA1MDUwIiwiYXVkIjoiM3lGNVRPU3pkbEk0NVExeHNweHplb0dCZTlmTnhtOW0iLCJleHAiOjIwOTA4ODQ5NzQsImlhdCI6MTQ2MDE2NDk3NH0.OxcoJJp06L1z2_41_p65FriEGkPzwFB_0pA9ULCvwvzJ8pJXw9hLbmsx-23aY2f-ydwJ7LSibL9i5NbQSR2riJWTcW4N7tLLCCMeFXKEK4hErN2hyxz71Fl765EjQSO5KD1A-HsOPr3ZZPoGTBjE0-EFtmXkSlHb1T2zd0Z8T5Z2-q96WkFoT6PiEdbrDA-e47LKtRmqsddnPZnp0xmMQdTr2MjpVgvqG7TlRvxDcYc-62rkwQXDNSWsW61FcKfQ-TRIZSf2GS9F9esDF4b5tRtrXcBNaorYa9ql0XAWH5W_ct4ylRNl3vwkYKWa4cmPvOqT5Wlj9Tf0af4lNO40PQ'}     # noqa


def check_json(response: requests.Response):
    """ Simple method which will raise an error if response has non-existent or empty JSON
    """
    response.raise_for_status()
    try:
        json_response = response.json()
        logging.debug('Response: {}'.format(json_response))
    except ValueError:
        logging.exception('Could not deserialize response contents:{}'.format(response.content.decode()))
        raise
    assert len(json_response) > 0, 'Empty JSON returned from dcos-diagnostics request'
    return json_response


def path_join(p1: str, p2: str):
    """Helper to ensure there is only one '/' between two strings"""
    return '{}/{}'.format(p1.rstrip('/'), p2.lstrip('/'))


class Url:
    """URL abstraction to allow convenient substitution of URL anatomy
    without having to copy and dissect the entire original URL
    """
    def __init__(self, scheme: str, host: str, path: str, query: str,
                 fragment: str, port: Union[str, int]):
        """{scheme}://{host}:{port}/{path}?{query}#{fragment}
        """
        self.scheme = scheme
        self.host = host
        self.path = path
        self.query = query
        self.fragment = fragment
        self.port = port

    @classmethod
    def from_string(cls, url_str: str):
        """ Creates a Url object from a string like 'http://foo.bar/baz?=qux'
        """
        u = urlsplit(url_str)
        if ':' in u.netloc:
            host, port = u.netloc.split(':')
        else:
            host = u.netloc
            port = None
        return cls(u.scheme, host, u.path, u.query, u.fragment, port)

    @property
    def netloc(self) -> str:
        """ Property which returns the a string of the form IP:port
        """
        return '{}:{}'.format(self.host, self.port) if self.port else self.host

    def __str__(self):
        return urlunsplit((
            self.scheme,
            self.netloc,
            self.path,
            self.query if self.query else '',
            self.fragment if self.fragment else ''))

    def copy(self, scheme=None, host=None, path=None, query=None, fragment=None, port=None):
        """return new Url with any component replaced
        """
        return Url(
            scheme if scheme is not None else self.scheme,
            host if host is not None else self.host,
            path if path is not None else self.path,
            query if query is not None else self.query,
            fragment if fragment is not None else self.fragment,
            port if port is not None else self.port)


class ApiClientSession:
    """This class functions like the requests.session interface but adds
    a default Url and a request wrapper. This class only differs from requests.Session
    in that the cookies are cleared after each request (but not purged from the response)
    so that the request state may be more well-defined betweens tests sharing this object

    :param default_url: The base URL to which all requests will be appended to
    :type default_url: Url
    """
    def __init__(self, default_url: Url):
        self.default_url = default_url
        self.session = requests.Session()

    def api_request(self, method, path_extension, *, scheme=None, host=None, query=None,
                    fragment=None, port=None, **kwargs) -> requests.Response:
        """ Direct wrapper for requests.session.request. This method is kept deliberatly
        simple so that child classes can alter this behavior without much copying

        :param method: the HTTP verb
        :type method: str
        :param path_extension: the extension to the path that is set as the default Url
        :type path_extension: str
        :param scheme: scheme to be used instead of that included with self.default_url
        :type scheme: str
        :param host: host to be used instead of that included with self.default_url
        :type host: str
        :param query: query to be used instead of that included with self.default_url
        :type query: str
        :param fragment: fragment to be used instead of that included with self.default_url
        :type fragment: str
        :param port: port to be used instead of that included with self.default_url
        :type port: int, str

        :param **kwargs: anything that can be passed to requests.request

        :returns: requests.Response -- response object from the request
        """

        final_path = self.default_url.path + path_extension

        request_url = str(self.default_url.copy(
            scheme=scheme,
            host=host,
            path=final_path,
            query=query,
            fragment=fragment,
            port=port))

        log.debug('Request method {}: {}. Arguments: {}'.format(method, request_url, repr(kwargs)))
        r = self.session.request(method, request_url, **kwargs)
        self.session.cookies.clear()
        return r

    def get(self, *args, **kwargs):
        """ GET method for :func:`~dcos_test_utils.helpers.ApiClientSession.api_request` method
        """
        return self.api_request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        """ POST method for :func:`~dcos_test_utils.helpers.ApiClientSession.api_request` method
        """
        return self.api_request('POST', *args, **kwargs)

    def put(self, *args, **kwargs):
        """ PUT method for :func:`~dcos_test_utils.helpers.ApiClientSession.api_request` method
        """
        return self.api_request('PUT', *args, **kwargs)

    def patch(self, *args, **kwargs):
        """ PATCH method for :func:`~dcos_test_utils.helpers.ApiClientSession.api_request` method
        """
        return self.api_request('PATCH', *args, **kwargs)

    def delete(self, *args, **kwargs):
        """ DELETE method for :func:`~dcos_test_utils.helpers.ApiClientSession.api_request` method
        """
        return self.api_request('DELETE', *args, **kwargs)

    def head(self, *args, **kwargs):
        """ HEAD method for :func:`~dcos_test_utils.helpers.ApiClientSession.api_request` method
        """
        return self.api_request('HEAD', *args, **kwargs)

    def options(self, *args, **kwargs):
        """ OPTIONS method for :func:`~dcos_test_utils.helpers.ApiClientSession.api_request` method
        """
        return self.api_request('OPTIONS', *args, **kwargs)


def is_retryable_exception(exception: Exception) -> bool:
    """ Helper method to catch HTTP errors that are likely safe to retry.
    Args:
        exception: exception raised from ApiClientSession.api_request instance
    """
    for ex in [requests.exceptions.ConnectionError, requests.exceptions.Timeout]:
        if isinstance(exception, ex):
            log.debug('Retrying common HTTP error: {}'.format(repr(exception)))
            return True
    return False


class RetryCommonHttpErrorsMixin:
    """ Mixin for ApiClientSession so that random disconnects from network
    instability do not derail entire scripts. This functionality is configured
    through the retry_timeout keyword
    """
    def api_request(self, *args, retry_timeout: int=60, **kwargs) -> requests.Response:
        """ Adds 'retry_timeout' keyword to API requests.
        Args:
            *args: args to be passed to super()'s api_request method
            **kwargs: keyword args to be passed to super()'s api_request method
            retry_timeout: total number of seconds to keep retrying after
                the initial exception was raised
        """
        @retrying.retry(
            wait_fixed=1000,
            stop_max_delay=retry_timeout * 1000,
            retry_on_exception=is_retryable_exception)
        def retry_errors():
            return super(RetryCommonHttpErrorsMixin, self).api_request(*args, **kwargs)

        return retry_errors()


class ARNodeApiClientMixin:
    def api_request(self, method, path_extension, *, scheme=None, host=None, query=None,
                    fragment=None, port=None, node=None, **kwargs):
        """ Communicating with a DC/OS cluster is done by default through Admin Router.
        Use this Mixin with an ApiClientSession that requires distinguishing between nodes.
        Admin Router has both a master and agent process and so this wrapper accepts a
        node argument. node must be a host in self.master or self.all_slaves. If given,
        the request will be made to the Admin Router endpoint for that node type

        :param node: IP of a master or agent
        :type node: str
        """
        if node is not None:
            assert port is None, 'node is intended to retrieve port; cannot set both simultaneously'
            assert host is None, 'node is intended to retrieve host; cannot set both simultaneously'
            if node in self.masters:
                # Due to guarantees about state in DcosApiSession, nothing else to do.
                # Master Admin Router uses default HTTP (80) and HTTPS (443) ports.
                pass
            elif node in self.all_slaves:
                scheme = scheme if scheme is not None else self.default_url.scheme
                if scheme == 'http':
                    port = 61001
                if scheme == 'https':
                    port = 61002
            else:
                raise Exception('Node {} is not recognized within the DC/OS cluster'.format(node))
            host = node
        return super().api_request(method, path_extension, scheme=scheme, host=host,
                                   query=query, fragment=fragment, port=port, **kwargs)


def session_tempfile(data):
    """Writes bytes to a named temp file and returns its path
    the temp file will be removed when the interpreter exits
    """
    with tempfile.NamedTemporaryFile(delete=False) as f:
        if isinstance(data, str):
            f.write(data.encode('utf-8'))
        else:
            f.write(data)
        temp_path = f.name

    def remove_file():
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # Attempt to remove the file upon normal interpreter exit.
    atexit.register(remove_file)
    return temp_path


def marathon_app_id_to_mesos_dns_subdomain(app_id: str):
    """Return app_id's subdomain as it would appear in a Mesos DNS A record.

    >>> marathon_app_id_to_mesos_dns_subdomain('/app-1')
    'app-1'
    >>> marathon_app_id_to_mesos_dns_subdomain('app-1')
    'app-1'
    >>> marathon_app_id_to_mesos_dns_subdomain('/group-1/app-1')
    'app-1-group-1'

    """
    return '-'.join(reversed(app_id.strip('/').split('/')))


def assert_response_ok(r: requests.Response):
    """ Simple helper to print out the status code and response content if a response is not OK
    """
    assert r.ok, 'status_code: {} content: {}'.format(r.status_code, r.content)

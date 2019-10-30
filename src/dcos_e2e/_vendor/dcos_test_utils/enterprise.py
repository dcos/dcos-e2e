""" This module defines an DcosApiSession child class for using Mesosphere Enterprise DC/OS
"""
import logging
import os

from dcos_test_utils import dcos_api, helpers, iam

log = logging.getLogger(__name__)


class MesosNodeClientMixin:
    """ This Mixin allows any request to be made against a master or agent
    mesos HTTP port by providing the keyword 'mesos_node'. Thus, the user
    does not have to specify the master/agent port or which arbitrary host
    in the cluster meeting that role
    """
    def api_request(self, method, path_extension, *, scheme=None, host=None, query=None,
                    fragment=None, port=None, mesos_node=None, **kwargs):
        """ This mixin method provides an additional keyword for easily directing to
        Mesos endpoints on either masters or slaves

        :param mesos_node: IP string of either a master or slave in the cluster
        :type mesos_node: str
        :returns: API response
        :rtype: requests.Response
        """
        if mesos_node is not None:
            assert port is None, 'Usage error: mesos_node keyword will set port'
            assert host is None, 'Usage error: mesos_node keyword will set host'
            if mesos_node == 'master':
                port = 5050
                host = self.masters[0]
            elif mesos_node == 'agent':
                port = 5051
                host = self.slaves[0]
            else:
                raise AssertionError('Mesos node type not recognized: {}'.format(mesos_node))
        return super().api_request(method, path_extension, scheme=scheme, host=host, query=query,
                                   fragment=fragment, port=port, **kwargs)


class EnterpriseUser(dcos_api.DcosUser):
    """ Enterprise user abstraction for authenticating the EnterpriseApiSession client

    :param uid: username to log in with
    :type uid: str
    :param password: password to be used with uid
    :type password: str
    """
    def __init__(self, uid: str, password: str):
        self.uid = uid
        self.password = password
        super().__init__(self.auth_json)

    @property
    def auth_json(self):
        """ Property for the headers needed to log into an Enterprise Edition cluster"""
        return {'uid': self.uid, 'password': self.password}


class EnterpriseApiSession(MesosNodeClientMixin, dcos_api.DcosApiSession):
    """ DcosApiSession specialized for use with an Enterprise cluster

    Note:
        This class is **required** for Enterprise API interaction

    :param ssl_enabled: if the security parameter is configured to permissive or strict, this should be True
    :type ssl_enabled: bool
    """
    def __init__(self, *args, ssl_enabled=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssl_enabled = ssl_enabled

    @classmethod
    def create(cls):
        """ Uses the method :func:`EnterpriseApiSession.get_args_from_env` to create an EnterpriseApiSession
        """
        api = cls(**cls.get_args_from_env())
        if api.ssl_enabled:
            api.set_ca_cert()
        api.login_default_user()
        api.set_initial_resource_ids()
        return api

    @property
    def iam(self):
        """ Property which generates a new client for :class:`~dcos_test_utils.iam.Iam`
        """
        return iam.Iam(self.default_url.copy(path='acs/api/v1'), session=self.copy().session)

    @property
    def secrets(self):
        """ Property which generates a new client where all paths are prepended with /secrets/v1
        """
        new = self.copy()
        new.default_url = self.default_url.copy(path='secrets/v1')
        return new

    @property
    def ca(self):
        """ Property which generates a new client where all paths are prepended with /ca/api/v2
        """
        new = self.copy()
        new.default_url = self.default_url.copy(path='ca/api/v2')
        return new

    @staticmethod
    def get_args_from_env():
        """ Uses all parameters defined in :func:`~dcos_test_utils.dcos_api.DcosApiSession.get_args_from_env`
        and adds some additional environment variables:

        * **DCOS_LOGIN_UNAME** username to user for DC/OS login
        * **DCOS_LOGIN_PW** password to user for DC/OS login
        * **DCOS_SSL_ENABLED** can be 'true' or 'false'. Set to false only if security is configured as disabled
        """
        assert 'DCOS_LOGIN_UNAME' in os.environ, 'DCOS_LOGIN_UNAME must be set to login!'
        assert 'DCOS_LOGIN_PW' in os.environ, 'DCOS_LOGIN_PW must be set!'
        uid = os.environ['DCOS_LOGIN_UNAME']
        password = os.environ['DCOS_LOGIN_PW']
        args = dcos_api.DcosApiSession.get_args_from_env()
        args['auth_user'] = EnterpriseUser(uid, password)
        args['ssl_enabled'] = os.getenv('DCOS_SSL_ENABLED', 'true') == 'true'
        return args

    def set_ca_cert(self):
        """ If security is permissive or strict, and the API session is not configured with verify=False,
        then the custom CA cert for the desired cluster must be attached to the session, which this method will do
        """
        log.info('Attempt to get CA bundle via Admin Router')
        r = self.get('/ca/dcos-ca.crt', verify=False)
        r.raise_for_status()
        self.session.verify = helpers.session_tempfile(r.content)

    def set_initial_resource_ids(self):
        """ helper method for setting the `initial_resource_ids` property of this ApiSession object

        This is useful for resetting the RIDs that were added over the couse of interaction with the cluster
        """
        self.initial_resource_ids = []
        r = self.iam.get('/acls')
        r.raise_for_status()
        for o in r.json()['array']:
            self.initial_resource_ids.append(o['rid'])

    def wait_for_dcos(self):
        """ This method will wait for basic DC/OS services to be running. Once basic endpoints are up,
        this method will set the custom CA cert and authenticate with the cluster
        """
        if self.ssl_enabled:
            self.set_ca_cert()
        super().wait_for_dcos()
        self.set_initial_resource_ids()

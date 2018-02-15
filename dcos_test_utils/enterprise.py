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
    def __init__(self, uid: str, password: str):
        self.uid = uid
        self.password = password
        super().__init__(self.auth_json)

    @property
    def auth_json(self):
        return {'uid': self.uid, 'password': self.password}


class EnterpriseApiSession(MesosNodeClientMixin, dcos_api.DcosApiSession):
    @property
    def iam(self):
        return iam.Iam(self.default_url.copy(path='acs/api/v1'), session=self.copy().session)

    @property
    def secrets(self):
        new = self.copy()
        new.default_url = self.default_url.copy(path='secrets/v1')
        return new

    @property
    def ca(self):
        new = self.copy()
        new.default_url = self.default_url.copy(path='ca/api/v2')
        return new

    @staticmethod
    def get_args_from_env():
        assert 'DCOS_LOGIN_UNAME' in os.environ, 'DCOS_LOGIN_UNAME must be set to login!'
        assert 'DCOS_LOGIN_PW' in os.environ, 'DCOS_LOGIN_PW must be set!'
        uid = os.environ['DCOS_LOGIN_UNAME']
        password = os.environ['DCOS_LOGIN_PW']
        args = dcos_api.DcosApiSession.get_args_from_env()
        args['auth_user'] = EnterpriseUser(uid, password)
        return args

    def set_ca_cert(self):
        log.info('Attempt to get CA bundle via Admin Router')
        r = self.get('ca/dcos-ca.crt', verify=False)
        r.raise_for_status()
        self.session.verify = helpers.session_tempfile(r.content)

    def set_initial_resource_ids(self):
        self.initial_resource_ids = []
        r = self.iam.get('/acls')
        r.raise_for_status()
        for o in r.json()['array']:
            self.initial_resource_ids.append(o['rid'])

from dcos_test_utils import helpers


class Iam(helpers.ApiClientSession):
    """
    Helpers for interacting with service user accounts.

    Note that some terminology is confused.
    The methods here interact with service user accounts and not services.
    """

    def __init__(self, default_url, session=None):
        super().__init__(default_url)
        if session:
            self.session = session

    def create_service(self, uid, pubkey, description):
        data = {
            'description': description,
            'public_key': pubkey
        }
        r = self.put('/users/{}'.format(uid), json=data)
        assert r.status_code == 201

    def delete_service(self, uid: str) -> None:
        """Delete a service account and verify that this worked.

        Args:
            uid: The user ID of the service account user to delete.

        Raises:
            AssertionError: The delete operation does not succeed.
        """
        resp = self.delete('/users/{}'.format(uid))
        assert resp.status_code == 204

        # Verify that service does not appear in collection anymore.
        resp = self.get('/users', query='type=service')
        resp.raise_for_status()
        uids = [account['uid'] for account in resp.json()['array']]
        assert uid not in uids

    def grant_user_permission(self, uid, action, rid):
        rid = rid.replace('/', '%252F')
        r = self.put('/acls/{}/users/{}/{}'.format(rid, uid, action))
        assert r.status_code == 204, ('Permission was not granted. Code: {}. '
                                      'Content {}'.format(r.status_code, r.content.decode()))

    def create_user_permission(self, uid, action, rid, description):
        rid = rid.replace('/', '%252F')
        r = self.put('/acls/{}'.format(rid), json={'description': description})
        assert r.status_code == 201, ('Permission was not created. Code {}. '
                                      'Content {}'.format(r.status_code, r.content.decode()))

    def delete_user_permission(self, uid, action, rid):
        rid = rid.replace('/', '%252F')
        r = self.delete('/acls/{}/users/{}/{}'.format(rid, uid, action))
        assert r.status_code == 204

    def create_acl(self, rid, description):
        rid = rid.replace('/', '%252F')
        # Create ACL if it does not yet exist.
        r = self.put('/acls/{}'.format(rid), json={'description': description})
        assert r.status_code == 201 or r.status_code == 409

    def delete_acl(self, rid):
        rid = rid.replace('/', '%252F')
        r = self.delete('/acls/{}'.format(rid))
        assert r.status_code == 204

    def make_service_account_credentials(self, uid, privkey):
        return {
            'scheme': 'RS256',
            'uid': uid,
            'login_endpoint': str(self.default_url) + '/auth/login',
            'private_key': privkey
        }

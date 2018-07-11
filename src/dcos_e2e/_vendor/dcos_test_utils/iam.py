""" This module provides a specialized client for interacting with
the Identity Access and Management (IAM) service endpoints
"""
from dcos_test_utils import helpers


class Iam(helpers.ApiClientSession):
    """
    Helpers for interacting with service user accounts.

    Note that some terminology is confused.
    The methods here interact with service user accounts and not services.

    :param default_url: URL for the IAM service endpoint
    :type default_url: helpers.Url
    :param session: Session to bootstrap this session client with
    :type session: requests.Session
    """

    def __init__(self, default_url: helpers.Url, session=None):
        super().__init__(default_url)
        if session:
            self.session = session

    def create_service(self, uid: str, pubkey: str, description: str):
        """ creates a service user

        :param uid: ID for the new service
        :type uid: str
        :param pubkey: Public key to be used by this new service
        :type pubkey: str
        :param description: simple description metadata to include with account creation
        :type description: str

        :returns: None
        """
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

    def grant_user_permission(self, uid: str, action: str, rid: str) -> None:
        """ Will grant a user with an action for a given RID

        :param uid: ID of the user that this permission will be granted to
        :type uid: str
        :param action: action that user will be granted for the RID
        :type action: str
        :param rid: resource ID that the user will be granted the action to
        :type rid: str
        """
        rid = rid.replace('/', '%252F')
        r = self.put('/acls/{}/users/{}/{}'.format(rid, uid, action))
        assert r.status_code == 204, ('Permission was not granted. Code: {}. '
                                      'Content {}'.format(r.status_code, r.content.decode()))

    def delete_user_permission(self, uid: str, action: str, rid: str) -> None:
        """ Will delete permission for a user for an action for a given RID

        :param uid: ID of the user that this permission will be deleted from
        :type uid: str
        :param action: action that will be deleted for the RID for the user
        :type action: str
        :param rid: resource ID that the user will be removed from for the given action
        :type rid: str
        """
        rid = rid.replace('/', '%252F')
        rid = rid.replace('/', '%252F')
        r = self.delete('/acls/{}/users/{}/{}'.format(rid, uid, action))
        assert r.status_code == 204

    def create_acl(self, rid: str, description: str) -> None:
        """ creates an ACL

        :param rid: RID for the ACL to be created
        :type rid: str
        :param description: text description for the new RID
        :type description: str
        """
        rid = rid.replace('/', '%252F')
        # Create ACL if it does not yet exist.
        r = self.put('/acls/{}'.format(rid), json={'description': description})
        assert r.status_code == 201 or r.status_code == 409

    def delete_acl(self, rid: str) -> None:
        """ Deletes an ACL

        :param rid: RID for the ACL to be deleted
        :type rid: str
        """
        rid = rid.replace('/', '%252F')
        r = self.delete('/acls/{}'.format(rid))
        assert r.status_code == 204

    def make_service_account_credentials(self, uid, privkey) -> dict:
        """ Generates the JSON object to post to create a service account

        :param uid: ID for the service account to be created
        :type uid: str
        :param privkey: private key to be used for the new service account
        :type privkey: str

        :returns: JSON-like dict to POST to IAM service
        """
        return {
            'scheme': 'RS256',
            'uid': uid,
            'login_endpoint': str(self.default_url) + '/auth/login',
            'private_key': privkey
        }

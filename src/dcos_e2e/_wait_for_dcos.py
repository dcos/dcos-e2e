"""
Helpers for waiting for DC/OS.
"""

import json
import logging
import subprocess
from typing import Set, Union

import retrying
import timeout_decorator
from retry import retry

from ._vendor.dcos_test_utils.dcos_api import DcosApiSession, DcosUser
from ._vendor.dcos_test_utils.enterprise import EnterpriseApiSession
from ._vendor.dcos_test_utils.helpers import CI_CREDENTIALS
from .base_classes import ClusterManager  # noqa: F401
from .exceptions import DCOSTimeoutError
from .node import Node, Output

LOGGER = logging.getLogger(__name__)


@retry(exceptions=(retrying.RetryError, ))
def _test_utils_wait_for_dcos(
    session: Union[DcosApiSession, EnterpriseApiSession],
) -> None:
    """
    Wait for DC/OS using DC/OS Test Utils.

    DC/OS Test Utils raises its own timeout, a ``retrying.RetryError``.
    We want to ignore this error and use our own timeouts, so we wrap this in
    our own retried function.
    """
    session.wait_for_dcos()  # type: ignore


@retry(
    exceptions=(subprocess.CalledProcessError),
    delay=10,
)
def _wait_for_node_poststart(masters: Set[Node]) -> None:
    """
    Wait until all DC/OS node-poststart checks are healthy.

    The execution will differ for different version of DC/OS.
    ``dcos-check-runner`` only exists on DC/OS 1.12+. ``dcos-diagnostics
    check node-poststart`` only works on DC/OS 1.10 and 1.11. ``3dt`` only
    exists on DC/OS 1.9. ``node-poststart`` requires ``sudo`` to allow
    reading the CA certificate used by certain checks.
    """
    for node in masters:
        log_msg = 'Running a poststart check on `{}`'.format(str(node))
        LOGGER.debug(log_msg)
        node.run(
            args=[
                'sudo',
                '/opt/mesosphere/bin/dcos-check-runner',
                'check',
                'node-poststart',
                '||',
                'sudo',
                '/opt/mesosphere/bin/dcos-diagnostics',
                'check',
                'node-poststart',
                '||',
                '/opt/mesosphere/bin/3dt',
                '--diag',
            ],
            # We capture output because else we would see a lot of output
            # in a normal start up, for example during tests.
            output=Output.CAPTURE,
            shell=True,
        )


def wait_for_dcos_oss(
    masters: Set[Node],
    agents: Set[Node],
    public_agents: Set[Node],
    http_checks: bool,
) -> None:
    """
    Wait until the DC/OS OSS boot process has completed.

    Args:
        masters: Master nodes in the cluster.
        agents: Agent nodes in the cluster.
        public_agents: Public agent nodes in the cluster.
        http_checks: Whether or not to wait for checks which involve HTTP.
            If this is `False`, this function may return before DC/OS is
            fully ready. This is useful in cases where an HTTP connection
            cannot be made to the  For example, this is useful on
            macOS without a VPN set up.

    Raises:
        dcos_e2e.exceptions.DCOSTimeoutError: Raised if components
            did not become ready within one hour.
    """

    @timeout_decorator.timeout(
        # We choose a one hour timeout based on experience that the cluster
        # will almost certainly not start up after this time.
        #
        # In the future we may want to increase this or make it
        # customizable.
        60 * 60,
        timeout_exception=DCOSTimeoutError,
    )
    def wait_for_dcos_oss_until_timeout() -> None:
        """
        Wait until DC/OS OSS is up or timeout hits.
        """

        _wait_for_node_poststart(masters=masters)
        if not http_checks:
            return

        email = 'albert@bekstil.net'
        curl_url = 'http://localhost:8101/acs/api/v1/users/{email}'.format(
            email=email,
        )

        delete_user_args = ['curl', '-X', 'DELETE', curl_url]

        create_user_args = [
            '.',
            '/opt/mesosphere/environment.export',
            '&&',
            'python',
            '/opt/mesosphere/bin/dcos_add_user.py',
            email,
        ]

        # The dcos-diagnostics check is not yet sufficient to determine
        # when a CLI login would be possible with DC/OS OSS. It only
        # checks the healthy state of the systemd units, not reachability
        # of services through HTTP.

        # Since DC/OS uses a Single-Sign-On flow with Identity Providers
        # outside the for the login and Admin Router only rewrites
        # requests to them, the login endpoint does not provide anything.

        # Current solution to guarantee the CLI login:

        # Try until one can login successfully with a long lived token
        # (dirty hack in dcos-test-utils wait_for_dcos). This is to avoid
        # having to simulate a browser that does the SSO flow.

        # Suggestion for replacing this with a DC/OS check for CLI login:

        # Determine and wait for all dependencies of the SSO OAuth login
        # inside of DC/OS. This should include Admin Router, ZooKeeper and
        # the DC/OS OAuth login service. Note that this may only guarantee
        # that the login could work, however not that is actually works.

        # In order to fully replace this method one would need to have
        # DC/OS checks for every HTTP endpoint exposed by Admin Router.

        any_master = next(iter(masters))
        # We create a user.
        # This allows this function to work even after a user has logged
        # in.
        # In particular, we need the "albert" user to exist, or for no
        # users to exist, for the DC/OS Test Utils API session to work.
        #
        # Creating the "albert" user will error if the user already exists.
        # Therefore, we delete the user.
        # This command returns a 0 exit code even if the user is not found.
        any_master.run(
            args=delete_user_args,
            output=Output.LOG_AND_CAPTURE,
        )
        any_master.run(
            args=create_user_args,
            shell=True,
            output=Output.LOG_AND_CAPTURE,
        )
        credentials = CI_CREDENTIALS

        api_session = DcosApiSession(
            dcos_url='http://{ip}'.format(ip=any_master.public_ip_address),
            masters=[str(n.public_ip_address) for n in masters],
            slaves=[str(n.public_ip_address) for n in agents],
            public_slaves=[str(n.public_ip_address) for n in public_agents],
            auth_user=DcosUser(credentials=credentials),
        )

        _test_utils_wait_for_dcos(session=api_session)

        # Only the first user can log in with SSO, before granting others
        # access.
        # Therefore, we delete the user who was created to wait for DC/OS.
        any_master.run(
            args=delete_user_args,
            output=Output.LOG_AND_CAPTURE,
        )

    wait_for_dcos_oss_until_timeout()


def wait_for_dcos_ee(
    masters: Set[Node],
    agents: Set[Node],
    public_agents: Set[Node],
    superuser_username: str,
    superuser_password: str,
    http_checks: bool,
) -> None:
    """
    Wait until the DC/OS Enterprise boot process has completed.

    Args:
        masters: Master nodes in the cluster.
        agents: Agent nodes in the cluster.
        public_agents: Public agent nodes in the cluster.
        superuser_username: Username of a user with superuser privileges.
        superuser_password: Password of a user with superuser privileges.
        http_checks: Whether or not to wait for checks which involve HTTP.
            If this is `False`, this function may return before DC/OS is
            fully ready. This is useful in cases where an HTTP connection
            cannot be made to the  For example, this is useful on
            macOS without a VPN set up.

    Raises:
        dcos_e2e.exceptions.DCOSTimeoutError: Raised if components
            did not become ready within one hour.
    """

    @timeout_decorator.timeout(
        # will almost certainly not start up after this time.
        #
        # In the future we may want to increase this or make it
        # customizable.
        60 * 60,
        timeout_exception=DCOSTimeoutError,
    )
    def wait_for_dcos_ee_until_timeout() -> None:
        """
        Wait until DC/OS Enterprise is up or timeout hits.
        """

        _wait_for_node_poststart(masters=masters)
        if not http_checks:
            return

        # The dcos-diagnostics check is not yet sufficient to determine
        # when a CLI login would be possible with Enterprise DC/OS. It only
        # checks the healthy state of the systemd units, not reachability
        # of services through HTTP.

        # In the case of Enterprise DC/OS this method uses dcos-test-utils
        # and superuser credentials to perform a superuser login that
        # assure authenticating via CLI is working.

        # Suggestion for replacing this with a DC/OS check for CLI login:

        # In Enterprise DC/OS this could be replace by polling the login
        # endpoint with random login credentials until it returns 401. In
        # that case the guarantees would be the same as with the OSS
        # suggestion.

        # The progress on a partial replacement can be followed here:
        # https://jira.d2iq.com/browse/DCOS_OSS-1313

        # In order to fully replace this method one would need to have
        # DC/OS checks for every HTTP endpoint exposed by Admin Router.

        credentials = {
            'uid': superuser_username,
            'password': superuser_password,
        }

        any_master = next(iter(masters))
        config_result = any_master.run(
            args=['cat', '/opt/mesosphere/etc/bootstrap-config.json'],
        )
        config = json.loads(config_result.stdout.decode())
        ssl_enabled = config['ssl_enabled']

        scheme = 'https://' if ssl_enabled else 'http://'
        dcos_url = scheme + str(any_master.public_ip_address)
        enterprise_session = EnterpriseApiSession(  # type: ignore
            dcos_url=dcos_url,
            masters=[str(n.public_ip_address) for n in masters],
            slaves=[str(n.public_ip_address) for n in agents],
            public_slaves=[
                str(n.public_ip_address) for n in public_agents
            ],
            auth_user=DcosUser(credentials=credentials),
        )

        if ssl_enabled:
            response = enterprise_session.get(
                # Avoid hitting a RetryError in the get function.
                # Waiting a year is considered equivalent to an
                # infinite timeout.
                '/ca/dcos-ca.crt',
                retry_timeout=60 * 60 * 24 * 365,
                verify=False,
            )
            response.raise_for_status()
            # This is already done in enterprise_session.wait_for_dcos()
            enterprise_session.set_ca_cert()

        _test_utils_wait_for_dcos(session=enterprise_session)

    wait_for_dcos_ee_until_timeout()

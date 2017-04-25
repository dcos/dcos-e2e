from subprocess import CalledProcessError

import pytest

from .testtools import Cluster


class TestHarness:
    """
    Example tests which demonstrate the features of the test harness.
    """

    @pytest.fixture
    def path(self) -> str:
        return '/opt/mesosphere/etc/docker_credentials'

    def test_extend_config(self, path: str) -> None:
        """
        This example demonstrates that it is possible to create a cluster
        with an extended configuration file.

        See ``test_file_does_not_exist`` for evidence that the custom
        configuration is used.
        """
        config = {
            'cluster_docker_credentials': {
                'auths': {
                    'https://index.docker.io/v1/': {
                        'auth': 'redacted'
                    },
                },
            },
            'cluster_docker_credentials_enabled': True,
        }

        with Cluster(extra_config=config) as cluster:
            (master, ) = cluster.masters
            master.run_as_root(args=['test', '-f', path])

    def test_file_does_not_exist(self, path: str) -> None:
        """
        This example demonstrates that a non-0 return code from a command run
        on a node raises a ``CalledProcessError``.
        """
        with Cluster(extra_config={}) as cluster:
            (master, ) = cluster.masters
            with pytest.raises(CalledProcessError):
                master.run_as_root(args=['test', '-f', path])

    @pytest.mark.parametrize('security', ['disabled', 'permissive', 'strict'])
    def test_security(self, security: str) -> None:
        """
        Clusters can be created with any security setting.
        For DC/OS Enterprise, this requires
        https://github.com/dcos/dcos-docker/pull/34.
        For DC/OS OSS, this is not relevant.
        """
        config = {'security': security}
        with Cluster(extra_config=config):
            pass

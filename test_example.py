from subprocess import CalledProcessError

import pytest

from .testtools import Cluster


class TestHarness:
    """
    Example tests which demonstrate the features of the test harness.
    """

    @pytest.fixture
    def path(self) -> str:
        """
        Return the path to a file which will exist on a cluster only if a
        particular config variable is given.
        """
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

    @pytest.mark.parametrize('run', [1, 2])
    def test_concurrency(self, run: int) -> None:
        """
        This example can be run with `-n 2` to show that clusters can be
        created concurrently.
        """
        with Cluster(extra_config={}):
            pass

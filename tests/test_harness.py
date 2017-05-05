"""
Tests for the test harness.
"""

from subprocess import CalledProcessError

import pytest

from dcos_e2e.cluster import Cluster


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    def test_run_as_root(self) -> None:
        """
        It is possible to run commands as root and see their output.
        """
        with Cluster(extra_config={}) as cluster:
            (master, ) = cluster.masters
            result = master.run_as_root(args=['echo', '$USER'])
            assert result.returncode == 0
            assert result.stdout.strip() == b'root'
            assert result.stderr == b''

            # Commands which return a non-0 code raise a
            # ``CalledProcessError``.
            with pytest.raises(CalledProcessError):
                result = master.run_as_root(args=['unset_command'])
                assert result.returncode == 127
                assert result.stdout == b''
                assert b'command not found' in result.stderr


class TestExtendConfig:
    """
    Tests for extending the configuration file.
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

        See ``test_default`` for evidence that the custom
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

    def test_default(self, path: str) -> None:
        """
        The example file does not exist with the standard configuration.
        This demonstrates that ``test_extend_config`` actually changes the
        configuration.
        """
        with Cluster(extra_config={}) as cluster:
            (master, ) = cluster.masters
            with pytest.raises(CalledProcessError):
                master.run_as_root(args=['test', '-f', path])


class TestClusterSize:
    """
    Tests for setting the cluster size.
    """

    def test_default(self) -> None:
        """
        By default, a cluster with one master and zero agents is created.
        """
        with Cluster(extra_config={}) as cluster:
            assert len(cluster.masters) == 1
            assert len(cluster.agents) == 0
            assert len(cluster.public_agents) == 0

    def test_custom(self) -> None:
        """
        It is possible to create a cluster with a custom number of nodes.
        """
        # These are chosen be low numbers which are not the defaults.
        # They are also different to one another to make sure that they are not
        # mixed up.
        # Low numbers are chosen to keep the resource usage low.
        masters = 3
        agents = 1
        public_agents = 2

        with Cluster(
            extra_config={},
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        ) as cluster:
            assert len(cluster.masters) == masters
            assert len(cluster.agents) == agents
            assert len(cluster.public_agents) == public_agents

"""
Tests for the test harness.

Some tests are together when it would be neater otherwise as the tests take a
long time to run.
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
        with Cluster(agents=0, public_agents=0) as cluster:
            (master, ) = cluster.masters
            result = master.run_as_root(args=['echo', '$USER'])
            assert result.returncode == 0
            assert result.stdout.strip() == b'root'
            assert result.stderr == b''

            # Commands which return a non-0 code raise a
            # ``CalledProcessError``.
            with pytest.raises(CalledProcessError) as excinfo:
                master.run_as_root(args=['unset_command'])

            exception = excinfo.value
            assert exception.returncode == 127
            assert exception.stdout == b''
            assert b'command not found' in exception.stderr


class TestIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(self) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster() as cluster:
            # No error is raised with a successful command.
            pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_auth.py']
            cluster.run_integration_tests(pytest_command=pytest_command)

            # An error is raised with an unsuccessful command.
            with pytest.raises(CalledProcessError) as excinfo:
                pytest_command = ['pytest', 'test_no_such_file.py']
                cluster.run_integration_tests(pytest_command=pytest_command)

            # `pytest` results in an exit code of 4 when no tests are
            # collected.
            # See https://docs.pytest.org/en/latest/usage.html.
            assert excinfo.value.returncode == 4


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

        See ``test_default`` for evidence that the custom configuration is
        used.
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

        with Cluster(
            extra_config=config, agents=0, public_agents=0
        ) as cluster:
            (master, ) = cluster.masters
            master.run_as_root(args=['test', '-f', path])

    def test_default(self, path: str) -> None:
        """
        The example file does not exist with the standard configuration.
        This demonstrates that ``test_extend_config`` actually changes the
        configuration.
        """
        with Cluster(agents=0, public_agents=0) as cluster:
            (master, ) = cluster.masters
            with pytest.raises(CalledProcessError):
                master.run_as_root(args=['test', '-f', path])


class TestClusterSize:
    """
    Tests for setting the cluster size.
    """

    def test_default(self) -> None:
        """
        By default, a cluster with one master and one agent and one private
        agent is created.
        """
        with Cluster() as cluster:
            assert len(cluster.masters) == 1
            assert len(cluster.agents) == 1
            assert len(cluster.public_agents) == 1

    def test_custom(self) -> None:
        """
        It is possible to create a cluster with a custom number of nodes.
        """
        # These are chosen be low numbers which are not the defaults.
        # They are also different to one another to make sure that they are not
        # mixed up.
        # Low numbers are chosen to keep the resource usage low.
        masters = 3
        agents = 0
        public_agents = 2

        with Cluster(
            masters=masters,
            agents=agents,
            public_agents=public_agents,
        ) as cluster:
            assert len(cluster.masters) == masters
            assert len(cluster.agents) == agents
            assert len(cluster.public_agents) == public_agents


class TestMultipleClusters:
    """
    Tests for working with multiple clusters.
    """

    def test_two_clusters(self) -> None:
        """
        It is possible to start two clusters.
        """
        with Cluster():
            with Cluster():
                pass

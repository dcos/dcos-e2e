"""
Tests for the test harness.

Some tests are together when it would be neater otherwise as the tests take a
long time to run.
"""

import logging
import uuid
from pathlib import Path
from subprocess import CalledProcessError
from typing import List

import pytest
from py.path import local
from pytest_capturelog import CaptureLogFuncArg

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestNode:
    """
    Tests for interacting with cluster nodes.
    """

    def test_run_as_root(
        self,
        caplog: CaptureLogFuncArg,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        It is possible to run commands as root and see their output.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
        ) as cluster:
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
            for record in caplog.records():
                # The error which caused this exception is not in the debug
                # log output.
                if record.levelno == logging.DEBUG:
                    assert 'unset_command' not in record.getMessage()

            # With `log_output_live`, output is logged and stderr is merged
            # into stdout.
            with pytest.raises(CalledProcessError) as excinfo:
                master.run_as_root(
                    args=['unset_command'], log_output_live=True
                )

            exception = excinfo.value
            assert exception.stderr == b''
            assert b'command not found' in exception.stdout
            expected_error_substring = 'unset_command'
            found_expected_error = False
            for record in caplog.records():
                if expected_error_substring in record.getMessage():
                    if record.levelno == logging.DEBUG:
                        found_expected_error = True
            assert found_expected_error


class TestIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(self, cluster_backend: ClusterBackend) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            # No error is raised with a successful command.
            pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_auth.py']
            cluster.run_integration_tests(pytest_command=pytest_command)

            # An error is raised with an unsuccessful command.
            with pytest.raises(CalledProcessError) as excinfo:
                pytest_command = ['pytest', 'test_no_such_file.py']
                result = cluster.run_integration_tests(
                    pytest_command=pytest_command
                )
                # This result will not be printed if the test passes, but it
                # may provide useful debugging information.
                print(result)  # pragma: no cover

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
        particular configuration variable is given.
        """
        return '/opt/mesosphere/etc/docker_credentials'

    def test_extend_config(
        self, path: str, cluster_backend: ClusterBackend
    ) -> None:
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
            extra_config=config,
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
        ) as cluster:
            cluster.wait_for_dcos()
            (master, ) = cluster.masters
            master.run_as_root(args=['test', '-f', path])

    def test_default(self, path: str, cluster_backend: ClusterBackend) -> None:
        """
        The example file does not exist with the standard configuration.
        This demonstrates that ``test_extend_config`` actually changes the
        configuration.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
        ) as cluster:
            (master, ) = cluster.masters
            cluster.wait_for_dcos()
            with pytest.raises(CalledProcessError):
                master.run_as_root(args=['test', '-f', path])


class TestClusterSize:
    """
    Tests for setting the cluster size.
    """

    def test_default(self, cluster_backend: ClusterBackend) -> None:
        """
        By default, a cluster with one master and one agent and one private
        agent is created.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            assert len(cluster.masters) == 1
            assert len(cluster.agents) == 1
            assert len(cluster.public_agents) == 1

    def test_custom(self, cluster_backend: ClusterBackend) -> None:
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
            cluster_backend=cluster_backend,
        ) as cluster:
            assert len(cluster.masters) == masters
            assert len(cluster.agents) == agents
            assert len(cluster.public_agents) == public_agents


class TestClusterLogging:
    """
    Tests for logs created by the ``Cluster``.
    """

    def _two_masters_error_logged(
        self,
        log_records: List[logging.LogRecord],
    ) -> bool:
        """
        Return whether a particular error is logged as a DEBUG message.

        This is prone to being broken as it checks for a string in the DC/OS
        repository.

        Args:
            log_records: Messages logged from the logger.

        Returns:
            Whether a particular error is logged as a DEBUG message.
        """
        message = 'Must have 1, 3, 5, 7, or 9 masters'
        encountered_error = False
        for record in log_records:
            if record.levelno == logging.DEBUG and message in str(record.msg):
                encountered_error = True
        return encountered_error

    def test_live_logging(
        self,
        caplog: CaptureLogFuncArg,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `log_output_live` is given as `True`, subprocess output is logged.
        """
        with pytest.raises(CalledProcessError):
            # It is not possible to create a cluster with two master nodes.
            with Cluster(
                masters=2,
                log_output_live=True,
                cluster_backend=cluster_backend
            ):
                pass  # pragma: no cover

        assert self._two_masters_error_logged(log_records=caplog.records())

    def test_no_live_logging(
        self,
        caplog: CaptureLogFuncArg,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        By default, subprocess output is not logged in the creation of a
        cluster.
        """
        with pytest.raises(CalledProcessError):
            # It is not possible to create a cluster with two master nodes.
            with Cluster(masters=2, cluster_backend=cluster_backend):
                pass  # pragma: no cover

        assert not self._two_masters_error_logged(log_records=caplog.records())


class TestMultipleClusters:
    """
    Tests for working with multiple clusters.
    """

    def test_two_clusters(
        self,
        cluster_backend: ClusterBackend,
    ) -> None:  # pragma: no cover
        """
        It is possible to start two clusters.

        We ignore this test's coverage because it cannot be run on Travis CI.
        This is because Travis CI has a space limit which is exceeded if we
        have multiple installer artifacts.
        """
        with Cluster(cluster_backend=cluster_backend):
            with Cluster(cluster_backend=cluster_backend):
                pass


class TestDestroyOnError:
    """
    Tests for `destroy_on_error`.
    """

    def test_default_exception_raised(
        self,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        By default, if an exception is raised, the cluster is destroyed.
        """
        with pytest.raises(Exception):
            with Cluster(
                agents=0,
                public_agents=0,
                cluster_backend=cluster_backend,
            ) as cluster:
                (master, ) = cluster.masters
                raise Exception()

        with pytest.raises(CalledProcessError):
            master.run_as_root(args=['echo', 'hello'])

    def test_set_false_exception_raised(
        self,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `destroy_on_error` is set to `False` and an exception is raised,
        the cluster is not destroyed.
        """
        with pytest.raises(Exception):
            with Cluster(
                agents=0,
                public_agents=0,
                destroy_on_error=False,
                cluster_backend=cluster_backend,
            ) as cluster:
                (master, ) = cluster.masters
                raise Exception()
        # No exception is raised. The node still exists.
        master.run_as_root(args=['echo', 'hello'])
        cluster.destroy()

    def test_set_false_no_exception(
        self,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `destroy_on_error` is set to `False` and no exception is raised,
        the cluster is not destroyed.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            destroy_on_error=False,
            cluster_backend=cluster_backend,
        ) as cluster:
            (master, ) = cluster.masters

        with pytest.raises(CalledProcessError):
            master.run_as_root(args=['echo', 'hello'])


class TestCopyFiles:
    """
    Tests for copying files to nodes.
    """

    def test_copy_files(
        self,
        cluster_backend: ClusterBackend,
        tmpdir: local,
    ) -> None:
        """
        Files can be copied from the host to master nodes and the installer
        node at creation time.
        """
        content = str(uuid.uuid4())
        local_file = tmpdir.join('example_file.txt')
        local_file.write(content)
        master_destination_path = Path('/etc/on_master_nodes.txt')
        files_to_copy_to_masters = {Path(local_file): master_destination_path}
        # We currently do not have a way of testing that this works without
        # using custom CA certificates on an enterprise cluster.
        # We add it to the test to at least exercise the code which uses this,
        # but this is insufficient.
        files_to_copy_to_installer = {
            Path(local_file): Path('/genconf/on_installer.txt'),
        }
        with Cluster(
            cluster_backend=cluster_backend,
            files_to_copy_to_masters=files_to_copy_to_masters,
            files_to_copy_to_installer=files_to_copy_to_installer,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            result = master.run_as_root(args=['cat', str(master_destination_path)])
            assert result.stdout.decode() == content

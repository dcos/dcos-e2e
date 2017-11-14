"""
Tests for the test harness.

Some tests are together when it would be neater otherwise as the tests take a
long time to run.
"""

import logging
from pathlib import Path
from subprocess import CalledProcessError
from typing import List

import pytest
from pytest_catchlog import CompatLogCaptureFixture

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    def test_run_pytest(
        self, cluster_backend: ClusterBackend, oss_artifact: Path
    ) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(oss_artifact, log_output_live=True)
            # No error is raised with a successful command.
            pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_auth.py']
            cluster.run_integration_tests(
                pytest_command=pytest_command,
                log_output_live=True,
            )

            # An error is raised with an unsuccessful command.
            with pytest.raises(CalledProcessError) as excinfo:
                pytest_command = ['pytest', 'test_no_such_file.py']
                result = cluster.run_integration_tests(
                    pytest_command=pytest_command,
                    log_output_live=True,
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
        self,
        path: str,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
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
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
        ) as cluster:
            cluster.install_dcos_from_path(
                oss_artifact,
                extra_config=config,
            )
            cluster.wait_for_dcos()
            (master, ) = cluster.masters
            master.run(
                args=['test', '-f', path], user=cluster.default_ssh_user
            )

    def test_default_config(
        self,
        path: str,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
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
            cluster.install_dcos_from_path(oss_artifact)
            (master, ) = cluster.masters
            cluster.wait_for_dcos()
            with pytest.raises(CalledProcessError):
                master.run(
                    args=['test', '-f', path], user=cluster.default_ssh_user
                )


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


class TestInstallDcosFromPath:
    """
    Tests for logs created when calling `install_dcos_from_path` on
    ``Cluster``.
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
        caplog: CompatLogCaptureFixture,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        If `log_output_live` is given as `True`, the installation output is
        logged live.
        """
        with pytest.raises(CalledProcessError):
            # It is not possible to install DC/OS with two master nodes.
            with Cluster(
                masters=2,
                cluster_backend=cluster_backend,
            ) as cluster:
                cluster.install_dcos_from_path(
                    oss_artifact,
                    log_output_live=True,
                )

        assert self._two_masters_error_logged(log_records=caplog.records)

    def test_no_live_logging(
        self,
        caplog: CompatLogCaptureFixture,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        By default, subprocess output is not logged during DC/OS installation.
        """
        with pytest.raises(CalledProcessError):
            # It is not possible to install DC/OS with two master nodes.
            with Cluster(
                masters=2,
                cluster_backend=cluster_backend,
            ) as cluster:
                cluster.install_dcos_from_path(oss_artifact)

        assert not self._two_masters_error_logged(log_records=caplog.records)


class TestMultipleClusters:
    """
    Tests for working with multiple clusters.
    """

    def test_two_clusters(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
    ) -> None:
        """
        It is possible to start two clusters.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(oss_artifact)
            with Cluster(cluster_backend=cluster_backend) as cluster:
                cluster.install_dcos_from_path(oss_artifact)


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
            master.run(args=['echo', 'hello'], user=cluster.default_ssh_user)

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
        master.run(
            args=['echo', 'hello'],
            log_output_live=True,
            user=cluster.default_ssh_user
        )
        cluster.destroy()


class TestDestroyOnSuccess:
    """
    Tests for `destroy_on_success`.
    """

    def test_default(
        self,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        By default the cluster is destroyed if there is no exception raised.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
        ) as cluster:
            (master, ) = cluster.masters

        with pytest.raises(CalledProcessError):
            master.run(args=['echo', 'hello'], user=cluster.default_ssh_user)

    def test_false(
        self,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `destroy_on_success` is set to `False`, the cluster is
        preserved if there is no exception raised.
        """
        with Cluster(
            agents=0,
            public_agents=0,
            cluster_backend=cluster_backend,
            destroy_on_success=False,
        ) as cluster:
            (master, ) = cluster.masters

        master.run(args=['echo', 'hello'], user=cluster.default_ssh_user)
        cluster.destroy()

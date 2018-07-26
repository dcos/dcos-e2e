"""
Tests for the test harness.

Some tests are together when it would be neater otherwise as the tests take a
long time to run.
"""

import logging
from pathlib import Path
from subprocess import CalledProcessError
from textwrap import dedent
from typing import Iterator, List

import pytest
from _pytest.logging import LogCaptureFixture
from kazoo.client import KazooClient
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import ClusterBackend
from dcos_e2e.cluster import Cluster


class TestIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    @pytest.fixture(scope='class')
    def cluster(
        self,
        oss_artifact: Path,
        cluster_backend: ClusterBackend,
    ) -> Iterator[Cluster]:
        """
        Return a `Cluster` with DC/OS installed and running.

        This is class scoped as we do not intend to modify the cluster in ways
        that make tests interfere with one another.
        """
        with Cluster(cluster_backend=cluster_backend) as dcos_cluster:
            dcos_cluster.install_dcos_from_path(
                dcos_config=dcos_cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                build_artifact=oss_artifact,
                log_output_live=True,
            )
            dcos_cluster.wait_for_dcos_oss()
            yield dcos_cluster

    @pytest.fixture(scope='class')
    def zk_client(self, cluster: Cluster) -> Iterator[KazooClient]:
        """
        Return a ZooKeeper client connected to ``cluster``.
        """
        (master, ) = cluster.masters
        zk_client_port = '2181'
        zk_host = str(master.public_ip_address)
        zk_client = KazooClient(hosts=zk_host + ':' + zk_client_port)
        zk_client.start()
        try:
            yield zk_client
        finally:
            zk_client.stop()

    def test_wait_for_dcos_oss(
        self,
        cluster: Cluster,
        zk_client: KazooClient,
    ) -> None:
        """
        Exercise ``wait_for_dcos_oss`` code.
        """
        # We exercise the "http_checks=False" code here but we do not test
        # its functionality. It is a temporary measure while we wait for
        # more thorough dcos-checks.
        cluster.wait_for_dcos_oss(http_checks=False)

        cluster.wait_for_dcos_oss()
        email = 'albert@bekstil.net'
        path = '/dcos/users/{email}'.format(email=email)
        assert not zk_client.exists(path=path)

    def test_run_pytest(self, cluster: Cluster) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
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
            logging.debug(str(result))  # pragma: no cover

        # `pytest` results in an exit code of 4 when no tests are
        # collected.
        # See https://docs.pytest.org/en/latest/usage.html.
        assert excinfo.value.returncode == 4

    def test_default_node(self, cluster: Cluster) -> None:
        """
        By default commands are run on an arbitrary master node.
        """
        (master, ) = cluster.masters
        command = ['/opt/mesosphere/bin/detect_ip']
        result = cluster.run_integration_tests(pytest_command=command).stdout
        assert str(master.public_ip_address).encode() == result.strip()

    def test_custom_node(self, cluster: Cluster) -> None:
        """
        It is possible to run commands on any node.
        """
        (agent, ) = cluster.agents
        command = ['/opt/mesosphere/bin/detect_ip']
        result = cluster.run_integration_tests(
            pytest_command=command,
            test_host=agent,
        ).stdout
        assert str(agent.public_ip_address).encode() == result.strip()


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


class TestCopyFiles:
    """
    Tests for copying files to the cluster.
    """

    def test_install_cluster_from_path(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        Install a DC/OS cluster with a custom ``ip-detect`` script.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:

            (master, ) = cluster.masters
            ip_detect_file = tmpdir.join('ip-detect')
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write(ip_detect_contents)

            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=[
                    (Path(str(ip_detect_file)), Path('/genconf/ip-detect')),
                ],
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/detect_ip'],
            )
            assert cat_result.stdout.decode() == ip_detect_contents

    def test_install_cluster_from_url(
        self,
        cluster_backend: ClusterBackend,
        oss_artifact_url: str,
        tmpdir: local,
    ) -> None:
        """
        Install a DC/OS cluster with a custom ``ip-detect`` script.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:

            (master, ) = cluster.masters
            ip_detect_file = tmpdir.join('ip-detect')
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write(ip_detect_contents)

            cluster.install_dcos_from_url(
                build_artifact=oss_artifact_url,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=[
                    (Path(str(ip_detect_file)), Path('/genconf/ip-detect')),
                ],
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/detect_ip'],
            )
            assert cat_result.stdout.decode() == ip_detect_contents


class TestInstallDcosFromPathLogging:
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
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.DEBUG,
                log_records,
            ),
        )
        matching_messages = set(
            filter(lambda record: message in record.getMessage(), log_records),
        )
        return bool(len(debug_messages & matching_messages))

    def test_live_logging(
        self,
        caplog: LogCaptureFixture,
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
                    build_artifact=oss_artifact,
                    ip_detect_path=cluster_backend.ip_detect_path,
                    dcos_config=cluster.base_config,
                    log_output_live=True,
                )

        assert self._two_masters_error_logged(log_records=caplog.records)

    def test_no_live_logging(
        self,
        caplog: LogCaptureFixture,
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
                cluster.install_dcos_from_path(
                    build_artifact=oss_artifact,
                    dcos_config=cluster.base_config,
                    ip_detect_path=cluster_backend.ip_detect_path,
                )

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
            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            with Cluster(cluster_backend=cluster_backend) as cluster:
                cluster.install_dcos_from_path(
                    build_artifact=oss_artifact,
                    dcos_config=cluster.base_config,
                    ip_detect_path=cluster_backend.ip_detect_path,
                )


class TestClusterFromNodes:
    """
    Tests for creating a `Cluster` with the `Cluster.from_nodes` method.
    """

    def test_cluster_from_nodes(self, cluster_backend: ClusterBackend) -> None:
        """
        It is possible to create a cluster from existing nodes, but not destroy
        it, or any nodes in it.
        """
        cluster = Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=1,
            public_agents=1,
        )

        (master, ) = cluster.masters
        (agent, ) = cluster.agents
        (public_agent, ) = cluster.public_agents

        with Cluster.from_nodes(
            masters=cluster.masters,
            agents=cluster.agents,
            public_agents=cluster.public_agents,
        ) as duplicate_cluster:
            (duplicate_master, ) = duplicate_cluster.masters
            (duplicate_agent, ) = duplicate_cluster.agents
            (duplicate_public_agent, ) = duplicate_cluster.public_agents
            assert 'master_list' in duplicate_cluster.base_config
            assert 'agent_list' in duplicate_cluster.base_config
            assert 'public_agent_list' in duplicate_cluster.base_config

            duplicate_master.run(args=['touch', 'example_master_file'])
            duplicate_agent.run(args=['touch', 'example_agent_file'])
            duplicate_public_agent.run(
                args=['touch', 'example_public_agent_file'],
            )

            master.run(args=['test', '-f', 'example_master_file'])
            agent.run(args=['test', '-f', 'example_agent_file'])
            public_agent.run(args=['test', '-f', 'example_public_agent_file'])

        with pytest.raises(NotImplementedError):
            duplicate_cluster.destroy()

        with pytest.raises(NotImplementedError):
            duplicate_cluster.destroy_node(node=duplicate_master)

        cluster.destroy()

    def test_install_dcos_from_url(
        self,
        oss_artifact_url: str,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        DC/OS can be installed on an existing cluster from a URL.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as original_cluster:
            cluster = Cluster.from_nodes(
                masters=original_cluster.masters,
                agents=original_cluster.agents,
                public_agents=original_cluster.public_agents,
            )

            cluster.install_dcos_from_url(
                build_artifact=oss_artifact_url,
                dcos_config=original_cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
            )

            cluster.wait_for_dcos_oss()

    def test_install_dcos_from_path(
        self,
        oss_artifact: Path,
        cluster_backend: ClusterBackend,
    ) -> None:
        """
        DC/OS can be installed on an existing cluster from a path.
        """
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as original_cluster:
            cluster = Cluster.from_nodes(
                masters=original_cluster.masters,
                agents=original_cluster.agents,
                public_agents=original_cluster.public_agents,
            )

            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                dcos_config=original_cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
            )

            cluster.wait_for_dcos_oss()


class TestDestroyNode:
    """
    Tests for destroying nodes.
    """

    def test_destroy_node(self, cluster_backend: ClusterBackend) -> None:
        """
        It is possible to destroy a node in the cluster.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            (agent, ) = cluster.agents
            cluster.destroy_node(node=agent)
            assert not cluster.agents

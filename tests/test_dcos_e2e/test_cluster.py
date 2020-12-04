"""
Tests for the test harness.

Some tests are together when it would be neater otherwise as the tests take a
long time to run.
"""

import json
import logging
from pathlib import Path
from subprocess import CalledProcessError
from textwrap import dedent
from typing import Iterator, List

import pytest
from _pytest.logging import LogCaptureFixture

from dcos_e2e.base_classes import ClusterBackend
from dcos_e2e.cluster import Cluster
from dcos_e2e.node import DCOSVariant, Output


class TestIntegrationTests:
    """
    Tests for running integration tests on a node.
    """

    @pytest.fixture(scope='class')
    def cluster(
        self,
        oss_installer: Path,
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
                dcos_installer=oss_installer,
                output=Output.CAPTURE,
            )
            dcos_cluster.wait_for_dcos_oss()
            yield dcos_cluster

    def test_wait_for_dcos_oss(self, cluster: Cluster) -> None:
        """
        Exercise ``wait_for_dcos_oss`` code.
        """
        # We exercise the "http_checks=False" code here but we do not test
        # its functionality. It is a temporary measure while we wait for
        # more thorough dcos-checks.
        cluster.wait_for_dcos_oss(http_checks=False)
        cluster.wait_for_dcos_oss(http_checks=True)
        # We check that no users are added by ``wait_for_dcos_oss``.
        # If a user is added, a user cannot log in via the web UI.
        get_users_args = ['curl', 'http://localhost:8101/acs/api/v1/users']
        (master, ) = cluster.masters
        result = master.run(args=get_users_args, output=Output.CAPTURE)
        users = json.loads(result.stdout.decode())['array']
        assert not users

    def test_run_pytest(self, cluster: Cluster) -> None:
        """
        Integration tests can be run with `pytest`.
        Errors are raised from `pytest`.
        """
        # No error is raised with a successful command.
        pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_auth.py']
        cluster.run_with_test_environment(
            args=pytest_command,
            output=Output.CAPTURE,
        )

        # An error is raised with an unsuccessful command.
        with pytest.raises(CalledProcessError) as excinfo:
            pytest_command = ['pytest', 'test_no_such_file.py']
            result = cluster.run_with_test_environment(
                args=pytest_command,
                output=Output.CAPTURE,
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
        result = cluster.run_with_test_environment(args=command).stdout
        assert str(master.public_ip_address).encode() == result.strip()

    def test_custom_node(self, cluster: Cluster) -> None:
        """
        It is possible to run commands on any node.
        """
        (agent, ) = cluster.agents
        command = ['/opt/mesosphere/bin/detect_ip']
        result = cluster.run_with_test_environment(args=command, node=agent)
        assert str(agent.public_ip_address).encode() == result.stdout.strip()


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
        oss_installer: Path,
        tmp_path: Path,
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
            ip_detect_file = tmp_path / 'ip-detect'
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write_text(ip_detect_contents)

            cluster.install_dcos_from_path(
                dcos_installer=oss_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=[
                    (ip_detect_file, Path('/genconf/ip-detect')),
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
        oss_installer_url: str,
        tmp_path: Path,
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
            ip_detect_file = tmp_path / 'ip-detect'
            ip_detect_contents = dedent(
                """\
                #!/bin/bash
                echo {ip_address}
                """,
            ).format(ip_address=master.private_ip_address)
            ip_detect_file.write_text(ip_detect_contents)

            cluster.install_dcos_from_url(
                dcos_installer=oss_installer_url,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                files_to_copy_to_genconf_dir=[
                    (ip_detect_file, Path('/genconf/ip-detect')),
                ],
                output=Output.LOG_AND_CAPTURE,
            )
            cluster.wait_for_dcos_oss()
            cat_result = master.run(
                args=['cat', '/opt/mesosphere/bin/detect_ip'],
            )
            assert cat_result.stdout.decode() == ip_detect_contents


class TestMultipleClusters:
    """
    Tests for working with multiple clusters.
    """

    def test_two_clusters(self, cluster_backend: ClusterBackend) -> None:
        """
        It is possible to start two clusters.
        """
        # What is not tested here is that two cluster installations of DC/OS
        # can be started at the same time.
        with Cluster(cluster_backend=cluster_backend):
            with Cluster(cluster_backend=cluster_backend):
                pass


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
        oss_installer_url: str,
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
                dcos_installer=oss_installer_url,
                dcos_config=original_cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
            )

            cluster.wait_for_dcos_oss()

    def test_install_dcos_from_path(
        self,
        oss_installer: Path,
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
                dcos_installer=oss_installer,
                dcos_config=original_cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
            )
            cluster.wait_for_dcos_oss()
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.')
                assert build.commit
                assert build.variant == DCOSVariant.OSS


class TestUpgrade:
    """
    Tests for upgrading a cluster.
    """

    def test_upgrade_from_path(
        self,
        cluster_backend: ClusterBackend,
        oss_2_0_installer: Path,
        oss_2_1_installer: Path,
    ) -> None:
        """
        DC/OS OSS can be upgraded from 2.0 to 2.1 from a local installer.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_2_0_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                output=Output.LOG_AND_CAPTURE,
            )
            cluster.wait_for_dcos_oss()

            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.0')
                assert build.variant == DCOSVariant.OSS

            cluster.upgrade_dcos_from_path(
                dcos_installer=oss_2_1_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                output=Output.LOG_AND_CAPTURE,
            )

            cluster.wait_for_dcos_oss()
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.1')
                assert build.variant == DCOSVariant.OSS

    def test_upgrade_from_url(
        self,
        cluster_backend: ClusterBackend,
        oss_2_0_installer: Path,
        oss_2_1_installer_url: str,
    ) -> None:
        """
        DC/OS OSS can be upgraded from 2.0 to 2.1 from a URL.
        """
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_path(
                dcos_installer=oss_2_0_installer,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                output=Output.LOG_AND_CAPTURE,
            )
            cluster.wait_for_dcos_oss()

            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.0')
                assert build.variant == DCOSVariant.OSS

            cluster.upgrade_dcos_from_url(
                dcos_installer=oss_2_1_installer_url,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                output=Output.LOG_AND_CAPTURE,
            )

            cluster.wait_for_dcos_oss()
            for node in {
                *cluster.masters,
                *cluster.agents,
                *cluster.public_agents,
            }:
                build = node.dcos_build_info()
                assert build.version.startswith('2.1')
                assert build.variant == DCOSVariant.OSS


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


class TestInstallDCOS:
    """
    Tests for ``Cluster.install_dcos``.
    """

    @pytest.fixture(autouse=True)
    def configure_logging(self, caplog: LogCaptureFixture) -> None:
        """
        Set the ``caplog`` logging level to ``DEBUG`` so it captures any log
        messages produced by ``dcos_e2e`` library.
        """
        caplog.set_level(logging.DEBUG, logger='dcos_e2e')

    def _two_masters_error_logged(
        self,
        log_records: List[logging.LogRecord],
    ) -> bool:
        """
        Return whether a particular error is logged as a WARNING message.

        This is prone to being broken as it checks for a string in the DC/OS
        repository.

        Args:
            log_records: Messages logged from the logger.

        Returns:
            Whether a particular error is logged as a WARNING message.
        """
        message = 'Must have 1, 3, 5, 7, or 9 masters'
        debug_messages = set(
            filter(
                lambda record: record.levelno == logging.WARNING,
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
        oss_installer: Path,
    ) -> None:
        """
        If ``output`` is given as ``Output.LOG_AND_CAPTURE``, the installation
        output is logged live.
        """
        with pytest.raises(CalledProcessError):
            # It is not possible to install DC/OS with two master nodes.
            with Cluster(
                masters=2,
                cluster_backend=cluster_backend,
            ) as cluster:
                cluster.install_dcos_from_path(
                    dcos_installer=oss_installer,
                    ip_detect_path=cluster_backend.ip_detect_path,
                    dcos_config=cluster.base_config,
                    output=Output.LOG_AND_CAPTURE,
                )

        assert self._two_masters_error_logged(log_records=caplog.records)

    def test_no_live_logging(
        self,
        caplog: LogCaptureFixture,
        cluster_backend: ClusterBackend,
        oss_installer: Path,
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
                    dcos_installer=oss_installer,
                    dcos_config=cluster.base_config,
                    ip_detect_path=cluster_backend.ip_detect_path,
                )

        assert not self._two_masters_error_logged(log_records=caplog.records)

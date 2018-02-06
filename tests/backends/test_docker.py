"""
Tests for the Docker backend.
"""

import subprocess
import uuid
from pathlib import Path

# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
import docker
import pytest
from passlib.hash import sha512_crypt
from py.path import local  # pylint: disable=no-name-in-module, import-error
from requests_mock import Mocker
from retry import retry

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Node


class TestDockerBackend:
    """
    Tests for functionality specific to the Docker backend.
    """

    def test_custom_mounts(self, tmpdir: local) -> None:
        """
        It is possible to mount local files to master nodes.
        """
        local_master_file = tmpdir.join('master_file.txt')
        local_master_file.write('')
        local_agent_file = tmpdir.join('agent_file.txt')
        local_agent_file.write('')
        local_public_agent_file = tmpdir.join('public_agent_file.txt')
        local_public_agent_file.write('')

        master_path = Path('/etc/on_master_nodes.txt')
        agent_path = Path('/etc/on_agent_nodes.txt')
        public_agent_path = Path('/etc/on_public_agent_nodes.txt')

        custom_master_mounts = {
            str(local_master_file): {
                'bind': str(master_path),
                'mode': 'rw',
            },
        }

        custom_agent_mounts = {
            str(local_agent_file): {
                'bind': str(agent_path),
                'mode': 'rw',
            },
        }

        custom_public_agent_mounts = {
            str(local_public_agent_file): {
                'bind': str(public_agent_path),
                'mode': 'rw',
            },
        }

        backend = Docker(
            custom_master_mounts=custom_master_mounts,
            custom_agent_mounts=custom_agent_mounts,
            custom_public_agent_mounts=custom_public_agent_mounts,
        )

        with Cluster(
            cluster_backend=backend,
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            for nodes, path, local_file in [
                (cluster.masters, master_path, local_master_file),
                (cluster.agents, agent_path, local_agent_file),
                (
                    cluster.public_agents, public_agent_path,
                    local_public_agent_file
                ),
            ]:
                for node in nodes:
                    content = str(uuid.uuid4())
                    local_file.write(content)
                    args = ['cat', str(path)]
                    result = node.run(args=args, user=cluster.default_ssh_user)
                    assert result.stdout.decode() == content

    def test_install_dcos_from_url(self, oss_artifact_url: str) -> None:
        """
        The Docker backend requires a build artifact in order
        to launch a DC/OS cluster.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            with pytest.raises(NotImplementedError) as excinfo:
                cluster.install_dcos_from_url(build_artifact=oss_artifact_url)

        expected_error = (
            'The Docker backend does not support the installation of DC/OS '
            'by build artifacts passed via URL string. This is because a more '
            'efficient installation method exists in `install_dcos_from_path`.'
        )

        assert str(excinfo.value) == expected_error


class TestDistributions:
    """
    Tests for setting the Linux distribution.
    """

    def _get_node_distribution(
        self,
        node: Node,
        default_ssh_user: str,
    ) -> Distribution:
        """
        Given a `Node`, return the `Distribution` on that node.
        """
        cat_cmd = node.run(
            args=['cat /etc/*-release'],
            user=default_ssh_user,
            shell=True,
        )

        version_info = cat_cmd.stdout
        version_info_lines = [
            line for line in version_info.decode().split('\n') if '=' in line
        ]
        version_data = dict(item.split('=') for item in version_info_lines)

        distributions = {
            ('"centos"', '"7"'): Distribution.CENTOS_7,
            ('ubuntu', '"16.04"'): Distribution.UBUNTU_16_04,
            ('coreos', '1298.7.0'): Distribution.COREOS,
            ('fedora', '23'): Distribution.FEDORA_23,
            ('debian', '"8"'): Distribution.DEBIAN_8,
        }

        return distributions[(version_data['ID'], version_data['VERSION_ID'])]

    def test_default(self) -> None:
        """
        The default Linux distribution for a `Node`s is the default Linux
        distribution of the backend.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            node_distribution = self._get_node_distribution(
                node=master,
                default_ssh_user=cluster.default_ssh_user,
            )

        assert node_distribution == Distribution.CENTOS_7

    @pytest.mark.parametrize(
        'unsupported_linux_distribution',
        set(Distribution) - {Distribution.CENTOS_7, Distribution.COREOS}
    )
    def test_custom_choice(
        self,
        unsupported_linux_distribution: Distribution,
    ) -> None:
        """
        Starting a cluster with a non-default Linux distribution raises a
        `NotImplementedError`.
        """
        with pytest.raises(NotImplementedError):
            Docker(linux_distribution=unsupported_linux_distribution)

    def test_coreos_oss(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        DC/OS OSS can start up on CoreOS.
        """
        with Cluster(
            cluster_backend=Docker(linux_distribution=Distribution.COREOS),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                log_output_live=True,
            )
            cluster.wait_for_dcos_oss()
            (master, ) = cluster.masters
            node_distribution = self._get_node_distribution(
                node=master,
                default_ssh_user=cluster.default_ssh_user,
            )

        assert node_distribution == Distribution.COREOS

    def test_coreos_enterprise(
        self,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on CoreOS.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        with Cluster(
            cluster_backend=Docker(linux_distribution=Distribution.COREOS),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=enterprise_artifact,
                extra_config=config,
                log_output_live=True,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )
            (master, ) = cluster.masters
            node_distribution = self._get_node_distribution(
                node=master,
                default_ssh_user=cluster.default_ssh_user,
            )

        assert node_distribution == Distribution.COREOS


class TestDockerVersion:
    """
    Tests for setting the version of Docker on the nodes.
    """

    def _get_docker_version(
        self,
        node: Node,
        default_ssh_user: str,
    ) -> DockerVersion:
        """
        Given a `Node`, return the `DockerVersion` on that node.
        """
        result = node.run(
            args=['docker', 'version', '--format', '{{.Server.Version}}'],
            user=default_ssh_user,
        )
        docker_versions = {
            '1.13.1': DockerVersion.v1_13_1,
        }

        return docker_versions[result.stdout.decode().strip()]

    def test_default(self) -> None:
        """
        By default, the Docker version is 1.13.1.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            docker_version = self._get_docker_version(
                node=master,
                default_ssh_user=cluster.default_ssh_user,
            )

        assert docker_version == DockerVersion.v1_13_1


class TestDockerStorageDriver:
    """
    Tests for setting the Docker storage driver.
    """

    DOCKER_STORAGE_DRIVERS = {
        'aufs': DockerStorageDriver.AUFS,
        'overlay': DockerStorageDriver.OVERLAY,
        'overlay2': DockerStorageDriver.OVERLAY_2,
    }

    # Retry because Docker may not be up.
    # @retry(
    #     exceptions=(subprocess.CalledProcessError),
    #     tries=5,
    #     delay=10,
    # )
    def _get_storage_driver(
        self,
        node: Node,
        default_ssh_user: str,
    ) -> DockerStorageDriver:
        """
        Given a `Node`, return the `DockerStorageDriver` on that node.
        """
        result = node.run(
            args=['docker', 'info', '--format', '{{.Driver}}'],
            user=default_ssh_user,
        )

        return self.DOCKER_STORAGE_DRIVERS[result.stdout.decode().strip()]

    # @pytest.mark.parametrize('host_driver', DOCKER_STORAGE_DRIVERS.keys())
    # def test_default(self, host_driver: str) -> None:
    #     """
    #     By default, the Docker storage driver is the same as the host's
    #     storage driver, if that driver is supported.
    #     """
    #     client = docker.from_env(version='auto')
    #     info = {**client.info(), **{'Driver': 'not_supported'}}
    #
    #     with Mocker(real_http=True) as mock:
    #         mock.get(url='http+docker://localunixsocket/v1.35/info', json=info)
    #         cluster_backend = Docker()
    #
    #     with Cluster(
    #         cluster_backend=cluster_backend,
    #         masters=1,
    #         agents=0,
    #         public_agents=0,
    #     ) as cluster:
    #         (master, ) = cluster.masters
    #         storage_driver = self._get_storage_driver(
    #             node=master,
    #             default_ssh_user=cluster.default_ssh_user,
    #         )
    #
    #     assert storage_driver == DockerStorageDriver.OVERLAY_2

    def test_host_driver_not_supported(self) -> None:
        """
        If the host's storage driver is not supported, `overlay2` is used.
        """
        client = docker.from_env(version='auto')
        info = {**client.info(), **{'Driver': 'not_supported'}}

        with Mocker(real_http=True) as mock:
            mock.get(url='http+docker://localunixsocket/v1.35/info', json=info)
            cluster_backend = Docker()

        assert cluster_backend.docker_storage_driver == 'overlay2'
        with Cluster(
            cluster_backend=cluster_backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            storage_driver = self._get_storage_driver(
                node=master,
                default_ssh_user=cluster.default_ssh_user,
            )

        assert storage_driver == DockerStorageDriver.OVERLAY_2

"""
Tests for the Docker backend.

This module contains tests for Docker backend features which are not covered by
sibling modules.
"""

import subprocess
import uuid
from pathlib import Path
from typing import Dict

# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
import docker
import pytest
from py.path import local  # pylint: disable=no-name-in-module, import-error
from requests_mock import Mocker, NoMockAddress
from retry import retry

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Node


@retry(
    exceptions=(subprocess.CalledProcessError),
    tries=60,
    delay=1,
)
def _wait_for_docker(node: Node) -> None:
    """
    Retry for up to one minute (arbitrary) until Docker is running on the given
    node.
    """
    node.run(args=['docker', 'info'])


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
                    cluster.public_agents,
                    public_agent_path,
                    local_public_agent_file,
                ),
            ]:
                for node in nodes:
                    content = str(uuid.uuid4())
                    local_file.write(content)
                    args = ['cat', str(path)]
                    result = node.run(args=args)
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


class TestDockerVersion:
    """
    Tests for setting the version of Docker on the nodes.
    """

    def _get_docker_version(
        self,
        node: Node,
    ) -> DockerVersion:
        """
        Given a `Node`, return the `DockerVersion` on that node.
        """
        _wait_for_docker(node=node)
        args = ['docker', 'version', '--format', '{{.Server.Version}}']
        result = node.run(args)
        docker_versions = {
            '1.11.2': DockerVersion.v1_11_2,
            '1.13.1': DockerVersion.v1_13_1,
            '17.12.1-ce': DockerVersion.v17_12_1_ce,
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
            docker_version = self._get_docker_version(node=master)

        assert docker_version == DockerVersion.v1_13_1

    @pytest.mark.parametrize('docker_version', list(DockerVersion))
    def test_custom_version(self, docker_version: DockerVersion) -> None:
        """
        It is possible to set a custom version of Docker.
        """
        # We specify the storage driver because `overlay2` is not compatible
        # with old versions of Docker.
        with Cluster(
            cluster_backend=Docker(
                docker_version=docker_version,
                storage_driver=DockerStorageDriver.AUFS,
            ),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            node_docker_version = self._get_docker_version(node=master)

        assert docker_version == node_docker_version


class TestDockerStorageDriver:
    """
    Tests for setting the Docker storage driver.
    """

    DOCKER_STORAGE_DRIVERS = {
        'aufs': DockerStorageDriver.AUFS,
        'overlay': DockerStorageDriver.OVERLAY,
        'overlay2': DockerStorageDriver.OVERLAY_2,
    }

    @property
    def _docker_info_endpoint(self) -> str:
        """
        Return the endpoint used when getting Docker information.
        """
        client = docker.from_env(version='auto')

        try:
            with Mocker() as mock:
                client.info()
        except NoMockAddress:
            pass

        [request] = mock.request_history
        return str(request).split()[1]

    def _get_storage_driver(
        self,
        node: Node,
    ) -> DockerStorageDriver:
        """
        Given a `Node`, return the `DockerStorageDriver` on that node.
        """
        _wait_for_docker(node=node)
        result = node.run(args=['docker', 'info', '--format', '{{.Driver}}'])

        return self.DOCKER_STORAGE_DRIVERS[result.stdout.decode().strip()]

    @pytest.mark.parametrize('host_driver', DOCKER_STORAGE_DRIVERS.keys())
    def test_default(self, host_driver: str) -> None:
        """
        By default, the Docker storage driver is the same as the host's
        storage driver, if that driver is supported.
        """
        client = docker.from_env(version='auto')
        info = {**client.info(), **{'Driver': host_driver}}

        with Mocker(real_http=True) as mock:
            mock.get(url=self._docker_info_endpoint, json=info)
            cluster_backend = Docker()

        storage_driver = cluster_backend.docker_storage_driver
        assert storage_driver == self.DOCKER_STORAGE_DRIVERS[host_driver]

    def test_host_driver_not_supported(self) -> None:
        """
        If the host's storage driver is not supported, `aufs` is used.
        """
        client = docker.from_env(version='auto')
        info = {**client.info(), **{'Driver': 'not_supported'}}

        with Mocker(real_http=True) as mock:
            mock.get(url=self._docker_info_endpoint, json=info)
            backend = Docker()

        assert backend.docker_storage_driver == DockerStorageDriver.AUFS

        with Cluster(
            cluster_backend=backend,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            node_driver = self._get_storage_driver(node=master)

        assert node_driver == DockerStorageDriver.AUFS

    @pytest.mark.parametrize('host_driver', DOCKER_STORAGE_DRIVERS.keys())
    @pytest.mark.parametrize('custom_driver', list(DockerStorageDriver))
    def test_custom(
        self,
        host_driver: str,
        custom_driver: DockerStorageDriver,
    ) -> None:
        """
        A custom storage driver can be used.
        """
        client = docker.from_env(version='auto')
        info = {**client.info(), **{'Driver': host_driver}}

        with Mocker(real_http=True) as mock:
            mock.get(url=self._docker_info_endpoint, json=info)
            cluster_backend = Docker(storage_driver=custom_driver)

        storage_driver = cluster_backend.docker_storage_driver
        assert storage_driver == custom_driver
        # We do not test actually changing the storage driver because only
        # `aufs` is supported on Travis CI.


class TestLabels:
    """
    Tests for setting labels on Docker containers.
    """

    def _get_labels(self, node: Node) -> Dict[str, str]:
        """
        Return the labels on the container which maps to ``node``.
        """
        client = docker.from_env(version='auto')
        containers = client.containers.list()
        [container] = [
            container for container in containers
            if container.attrs['NetworkSettings']['IPAddress'] ==
            str(node.public_ip_address)
        ]
        return dict(container.labels)

    def test_custom(self) -> None:
        """
        It is possible to set node Docker container labels.
        """
        cluster_key = uuid.uuid4().hex
        cluster_value = uuid.uuid4().hex
        cluster_labels = {cluster_key: cluster_value}

        master_key = uuid.uuid4().hex
        master_value = uuid.uuid4().hex
        master_labels = {master_key: master_value}

        agent_key = uuid.uuid4().hex
        agent_value = uuid.uuid4().hex
        agent_labels = {agent_key: agent_value}

        public_agent_key = uuid.uuid4().hex
        public_agent_value = uuid.uuid4().hex
        public_agent_labels = {public_agent_key: public_agent_value}

        with Cluster(
            cluster_backend=Docker(
                docker_container_labels=cluster_labels,
                docker_master_labels=master_labels,
                docker_agent_labels=agent_labels,
                docker_public_agent_labels=public_agent_labels,
            ),
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            for node in cluster.masters:
                node_labels = self._get_labels(node=node)
                assert node_labels[cluster_key] == cluster_value
                assert node_labels[master_key] == master_value
                assert agent_key not in node_labels
                assert public_agent_key not in node_labels

            for node in cluster.agents:
                node_labels = self._get_labels(node=node)
                assert node_labels[cluster_key] == cluster_value
                assert node_labels[agent_key] == agent_value
                assert master_key not in node_labels
                assert public_agent_key not in node_labels

            for node in cluster.public_agents:
                node_labels = self._get_labels(node=node)
                assert node_labels[cluster_key] == cluster_value
                assert node_labels[public_agent_key] == public_agent_value
                assert master_key not in node_labels
                assert agent_key not in node_labels

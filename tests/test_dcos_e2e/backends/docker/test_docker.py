"""
Tests for the Docker backend.

This module contains tests for Docker backend features which are not covered by
sibling modules.
"""

import subprocess
import uuid
from pathlib import Path
from typing import Iterator

import docker
import pytest
from docker.models.networks import Network
from docker.types import Mount
from requests_mock import Mocker, NoMockAddress
from retry import retry

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.docker_storage_drivers import DockerStorageDriver
from dcos_e2e.docker_versions import DockerVersion
from dcos_e2e.node import Node, Output, Transport


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


def _get_container_from_node(node: Node) -> docker.models.containers.Container:
    """
    Return the container which represents the given ``node``.
    """
    client = docker.from_env(version='auto')
    containers = client.containers.list()
    matching_containers = []
    for container in containers:
        networks = container.attrs['NetworkSettings']['Networks']
        for net in networks:
            if networks[net]['IPAddress'] == str(node.public_ip_address):
                matching_containers.append(container)

    assert len(matching_containers) == 1
    return matching_containers[0]


class TestDockerBackend:
    """
    Tests for functionality specific to the Docker backend.
    """

    def test_custom_mounts(self, tmp_path: Path) -> None:
        """
        It is possible to mount local files to master nodes.
        """
        local_all_file = tmp_path / 'all_file.txt'
        local_all_file.write_text('')
        local_master_file = tmp_path / 'master_file.txt'
        local_master_file.write_text('')
        local_agent_file = tmp_path / 'agent_file.txt'
        local_agent_file.write_text('')
        local_public_agent_file = tmp_path / 'public_agent_file.txt'
        local_public_agent_file.write_text('')

        master_path = Path('/etc/on_master_nodes.txt')
        agent_path = Path('/etc/on_agent_nodes.txt')
        public_agent_path = Path('/etc/on_public_agent_nodes.txt')
        all_path = Path('/etc/on_all_nodes.txt')

        custom_container_mount = Mount(
            source=str(local_all_file),
            target=str(all_path),
            type='bind',
        )

        custom_master_mount = Mount(
            source=str(local_master_file),
            target=str(master_path),
            type='bind',
        )

        custom_agent_mount = Mount(
            source=str(local_agent_file),
            target=str(agent_path),
            type='bind',
        )

        custom_public_agent_mount = Mount(
            source=str(local_public_agent_file),
            target=str(public_agent_path),
            type='bind',
        )

        backend = Docker(
            custom_container_mounts=[custom_container_mount],
            custom_master_mounts=[custom_master_mount],
            custom_agent_mounts=[custom_agent_mount],
            custom_public_agent_mounts=[custom_public_agent_mount],
        )

        with Cluster(
            cluster_backend=backend,
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            for nodes, path, local_file in [
                (cluster.masters, master_path, local_master_file),
                (cluster.masters, all_path, local_all_file),
                (cluster.agents, agent_path, local_agent_file),
                (cluster.agents, all_path, local_all_file),
                (
                    cluster.public_agents,
                    public_agent_path,
                    local_public_agent_file,
                ),
                (cluster.public_agents, all_path, local_all_file),
            ]:
                for node in nodes:
                    content = str(uuid.uuid4())
                    local_file.write_text(content)
                    args = ['cat', str(path)]
                    result = node.run(args=args)
                    assert result.stdout.decode() == content

    def test_install_dcos_from_url(self, oss_installer_url: str) -> None:
        """
        It is possible to install DC/OS on a cluster with a Docker backend.
        """
        cluster_backend = Docker()
        with Cluster(cluster_backend=cluster_backend) as cluster:
            cluster.install_dcos_from_url(
                dcos_installer=oss_installer_url,
                dcos_config=cluster.base_config,
                ip_detect_path=cluster_backend.ip_detect_path,
                output=Output.LOG_AND_CAPTURE,
            )
            cluster.wait_for_dcos_oss()


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
            '18.06.3-ce': DockerVersion.v18_06_3_ce,
        }

        return docker_versions[result.stdout.decode().strip()]

    def test_default(self) -> None:
        """
        By default, the Docker version is 18.06.3.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            docker_version = self._get_docker_version(node=master)

        assert docker_version == DockerVersion.v18_06_3_ce

    @pytest.mark.parametrize('docker_version', list(DockerVersion))
    def test_custom_version(self, docker_version: DockerVersion) -> None:
        """
        It is possible to set a custom version of Docker.

        Running this test requires ``aufs`` to be available.
        Depending on your system, it may be possible to make ``aufs`` available
        using the following commands:

        .. code

           $ apt-get install linux-image-extra-$(uname -r)
           $ modprobe aufs
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

        cluster_backend = Docker(
            docker_container_labels=cluster_labels,
            docker_master_labels=master_labels,
            docker_agent_labels=agent_labels,
            docker_public_agent_labels=public_agent_labels,
        )

        with Cluster(cluster_backend=cluster_backend) as cluster:
            for node in cluster.masters:
                node_labels = dict(_get_container_from_node(node=node).labels)
                assert node_labels[cluster_key] == cluster_value
                assert node_labels[master_key] == master_value
                assert agent_key not in node_labels
                assert public_agent_key not in node_labels

            for node in cluster.agents:
                node_labels = dict(_get_container_from_node(node=node).labels)
                assert node_labels[cluster_key] == cluster_value
                assert node_labels[agent_key] == agent_value
                assert master_key not in node_labels
                assert public_agent_key not in node_labels

            for node in cluster.public_agents:
                node_labels = dict(_get_container_from_node(node=node).labels)
                assert node_labels[cluster_key] == cluster_value
                assert node_labels[public_agent_key] == public_agent_value
                assert master_key not in node_labels
                assert agent_key not in node_labels


class TestNetworks:
    """
    Tests for Docker container networks.

    On macOS, by default, it is not possible to SSH to containers without
    forwarded ports.

    We therefore recommend that people use ``minidcos docker
    setup-mac-network``.  This makes it possible to SSH to containers in the
    default network range.

    However, in these tests, we use custom networks.
    Using the VPN created by ``minidcos docker setup-mac-network`` it is not
    possible to SSH to containers on custom networks.
    See https://github.com/wojas/docker-mac-network#openvpn for details.

    Therefore, we use the ``Transport.DOCKER_EXEC`` transport to communicate
    with nodes.
    """

    @pytest.fixture()
    def docker_network(self) -> Iterator[Network]:
        """
        Return a Docker network.
        """
        client = docker.from_env(version='auto')
        ipam_pool = docker.types.IPAMPool(
            subnet='172.28.0.0/16',
            iprange='172.28.0.0/24',
            gateway='172.28.0.254',
        )
        # We use the default container prefix so that the
        # ``minidcos docker clean`` command cleans this up.
        prefix = Docker().container_name_prefix
        random = uuid.uuid4()
        name = '{prefix}-network-{random}'.format(prefix=prefix, random=random)
        network = client.networks.create(
            name=name,
            driver='bridge',
            ipam=docker.types.IPAMConfig(pool_configs=[ipam_pool]),
            attachable=False,
        )
        try:
            yield network
        finally:
            network.remove()

    def test_custom_docker_network(
        self,
        docker_network: Network,
    ) -> None:
        """
        When a network is specified on the Docker backend, each container is
        connected to the default bridge network ``docker0`` and in addition it
        also connected to the custom network.

        The ``Node``'s IP addresses correspond to the custom network.
        """
        with Cluster(
            cluster_backend=Docker(
                network=docker_network,
                transport=Transport.DOCKER_EXEC,
            ),
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            container = _get_container_from_node(node=master)
            networks = container.attrs['NetworkSettings']['Networks']
            assert networks.keys() == set(['bridge', docker_network.name])
            custom_network_ip = networks[docker_network.name]['IPAddress']
            assert custom_network_ip == str(master.public_ip_address)
            assert custom_network_ip == str(master.private_ip_address)

    def test_docker_exec_transport(
        self,
        docker_network: Network,
        tmp_path: Path,
    ) -> None:
        """
        ``Node`` operations with the Docker exec transport work even if the
        node is on a custom network.
        """
        with Cluster(
            cluster_backend=Docker(
                network=docker_network,
                transport=Transport.DOCKER_EXEC,
            ),
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            content = str(uuid.uuid4())
            local_file = tmp_path / 'example_file.txt'
            local_file.write_text(content)
            random = uuid.uuid4().hex
            master_destination_dir = '/etc/{random}'.format(random=random)
            master_destination_path = Path(master_destination_dir) / 'file.txt'
            master.send_file(
                local_path=local_file,
                remote_path=master_destination_path,
                transport=Transport.DOCKER_EXEC,
            )
            args = ['cat', str(master_destination_path)]
            result = master.run(args=args, transport=Transport.DOCKER_EXEC)
            assert result.stdout.decode() == content

    def test_default(self) -> None:
        """
        By default, the only network a container is in is the Docker default
        bridge network.
        """
        with Cluster(
            cluster_backend=Docker(),
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            container = _get_container_from_node(node=master)
            networks = container.attrs['NetworkSettings']['Networks']
            assert networks.keys() == set(['bridge'])
            bridge_ip_address = networks['bridge']['IPAddress']
            assert bridge_ip_address == str(master.public_ip_address)
            assert bridge_ip_address == str(master.private_ip_address)

    def test_pass_bridge(self) -> None:
        """
        If the bridge network is given, the only network a container is in
        is the Docker default bridge network.
        """
        client = docker.from_env(version='auto')
        network = client.networks.get(network_id='bridge')
        with Cluster(
            cluster_backend=Docker(network=network),
            agents=0,
            public_agents=0,
        ) as cluster:
            (master, ) = cluster.masters
            container = _get_container_from_node(node=master)
            networks = container.attrs['NetworkSettings']['Networks']
            assert networks.keys() == set(['bridge'])
            bridge_ip_address = networks['bridge']['IPAddress']
            assert bridge_ip_address == str(master.public_ip_address)
            assert bridge_ip_address == str(master.private_ip_address)


class TestOneMasterHostPortMap:
    """
    Tests for setting host port map on a master Docker container.
    """

    def test_one_master_host_port_map(self) -> None:
        """
        It is possible to expose admin router to a host port.
        """

        with Cluster(
            cluster_backend=Docker(one_master_host_port_map={'80/tcp': 8000}),
            masters=3,
            agents=0,
            public_agents=0,
        ) as cluster:
            masters_containers = [
                _get_container_from_node(node=node) for node in cluster.masters
            ]

            masters_ports_settings = [
                container.attrs['HostConfig']['PortBindings']
                for container in masters_containers
            ]

            masters_ports_settings.remove(None)
            masters_ports_settings.remove(None)

            [master_port_settings] = masters_ports_settings
            expected_master_port_settings = {
                '80/tcp': [{
                    'HostIp': '',
                    'HostPort': '8000',
                }],
            }
            assert master_port_settings == expected_master_port_settings

from typing import Tuple

import docker
import pytest

from dcos_e2e.docker_utils import DockerLoopbackVolume

# We ignore this error because it conflicts with `pytest` standard usage.
# pylint: disable=redefined-outer-name


@pytest.fixture
def loopback_sidecar() -> Tuple[docker.models.containers.Container, str]:
    return DockerLoopbackVolume.create(name='test', size=1)


class TestDockerLoopbackVolume:
    """
    Tests for setting device mapping on master or agent Docker containers.
    """

    def test_loopback(self) -> None:
        """
        An instance of `DockerLoopbackVolume` provides a block device.
        """
        labels = {'foo': 'bar'}

        with DockerLoopbackVolume(
            name='test',
            size=1,
            labels=labels,
        ) as device:
            cmd = 'lsblk {}'.format(device.path)
            exit_code, output = device.container.exec_run(cmd=cmd)
            assert exit_code == 0, cmd + ': ' + output.decode()

            for key, value in labels.items():
                assert device.container.labels[key] == value

    def test_create(self) -> None:
        """
        Calling `DockerLoopbackVolume.create` creates a sidecar container.
        """
        labels = {'foo': 'bar'}

        container, path = DockerLoopbackVolume.create(
            name='test',
            size=1,
            labels=labels,
        )

        try:
            for key, value in labels.items():
                assert container.labels[key] == value

            cmd = 'lsblk {}'.format(path)
            exit_code, output = container.exec_run(cmd=cmd)
            assert exit_code == 0, cmd + ': ' + output.decode()

        finally:
            DockerLoopbackVolume.destroy(container)

    def test_destroy(
        self,
        loopback_sidecar: Tuple[docker.models.containers.Container, str],
    ) -> None:
        """
        Calling `DockerLoopbackVolume.destroy` destroys a sidecar container
        without throwing an exception.
        """
        DockerLoopbackVolume.destroy(loopback_sidecar[0])

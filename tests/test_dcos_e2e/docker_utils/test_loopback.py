from typing import Tuple

import docker

from dcos_e2e.docker_utils import DockerLoopbackVolume


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
            exit_code, output = device.container.exec_run(
                cmd=['lsblk', device.path],
            )
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

            exit_code, output = container.exec_run(cmd=['lsblk', path])
            assert exit_code == 0, cmd + ': ' + output.decode()

        finally:
            DockerLoopbackVolume.destroy(container)

    def test_destroy(self) -> None:
        """
        Calling `DockerLoopbackVolume.destroy` destroys a sidecar container
        without throwing an exception.
        """
        container, _ = DockerLoopbackVolume.create(name='test', size=1)
        DockerLoopbackVolume.destroy(container=container)

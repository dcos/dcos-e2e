import uuid

import docker
import pytest

from dcos_e2e.docker_utils import DockerLoopbackVolume


class TestDockerLoopbackVolume:
    """
    Tests for setting device mapping on master or agent Docker containers.
    """

    def test_loopback(self) -> None:
        """
        A block device is created which is accessible to multiple containers.
        """
        client = docker.from_env(version='auto')

        with DockerLoopbackVolume(size_megabytes=1) as device:
            new_container = client.containers.create(
                privileged=True,
                detach=True,
                image='centos:7',
                entrypoint =['/bin/sleep', 'infinity'],
            )
            new_container.start()

            try:
                block_device_exists_cmd = ['lsblk', device.path]
                exit_code, output = new_container.exec_run(
                    cmd=block_device_exists_cmd,
                )
                assert exit_code == 0, device.path + ': ' + output.decode()

                block_device_has_right_size = [
                    'stat',
                    '-f',
                    '"%z"',
                    device.path,
                ]
                exit_code, output = new_container.exec_run(
                    cmd=block_device_has_right_size,
                )
                assert exit_code == 0, device.path + ': ' + output.decode()
                assert output == '1048576'
            finally:
                new_container.stop()
                new_container.remove()

    def test_labels(self) -> None:
        """
        The given labels are applied to the new container.
        """
        client = docker.from_env(version='auto')
        key = uuid.uuid4().hex
        value = uuid.uuid4().hex
        labels = {key: value}

        with DockerLoopbackVolume(size_megabytes=1, labels=labels):
            filters = {'label': ['{key}={value}'.format(key=key, value=value)]}
            [existing_container] = client.containers.list(filters=filters)
            for key, value in labels.items():
                assert existing_container.labels[key] == value

    def test_multiple(self) -> None:
        """
        Multiple sidecars can exist at once.
        """
        with DockerLoopbackVolume(size_megabytes=1) as first:
            with DockerLoopbackVolume(size_megabytes=1) as second:
                assert first.path != second.path

    def test_destroy(self) -> None:
        """
        The container and block device are destroyed.
        """
        client = docker.from_env(version='auto')
        key = uuid.uuid4().hex
        value = uuid.uuid4().hex
        labels = {key: value}

        with DockerLoopbackVolume(size_megabytes=1, labels=labels) as device:
            filters = {'label': ['{key}={value}'.format(key=key, value=value)]}
            [existing_container] = client.containers.list(filters=filters)
            block_device_exists_cmd = ['lsblk', device.path]

        with pytest.raises(docker.errors.NotFound):
            existing_container.reload()

        new_container = client.containers.create(
            privileged=True,
            detach=True,
            image='centos:7',
        )
        new_container.start()
        exit_code, output = new_container.exec_run(cmd=block_device_exists_cmd)
        new_container.stop()
        new_container.remove()

        assert exit_code != 0, output.decode()

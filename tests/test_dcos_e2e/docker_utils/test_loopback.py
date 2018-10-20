from dcos_e2e.docker_utils import DockerLoopbackVolume

import docker

class TestDockerLoopbackVolume:
    """
    Tests for setting device mapping on master or agent Docker containers.
    """

    def test_loopback(self) -> None:
        """
        An instance of ``DockerLoopbackVolume`` provides a container which can
        access a block device.
        """
        client = docker.from_env(version='auto')
        labels = {'foo': 'bar'}

        with DockerLoopbackVolume(
            size=1,
            labels=labels,
        ) as device:
            block_device_exists_cmd = ['lsblk', device.path]
            exit_code, output = device.container.exec_run(
                cmd=block_device_exists_cmd,
            )

            # TODO new container can access this
            assert exit_code == 0, device.path + ': ' + output.decode()
            new_container_1 = client.containers.create(
                privileged=True,
                detach=True,
                tty=True,
                image='centos:7',
            )
            new_container_1.start()
            exit_code, output = new_container_1.exec_run(
                cmd=block_device_exists_cmd,
            )

            assert exit_code == 0, device.path + ': ' + output.decode()

            for key, value in labels.items():
                assert device.container.labels[key] == value

        new_container_2 = client.containers.create(
            privileged=True,
            detach=True,
            tty=True,
            image='centos:7',
        )
        new_container_2.start()
        exit_code, output = new_container_2.exec_run(
            cmd=block_device_exists_cmd,
        )

        # TODO new container can access this
        assert exit_code == 1

    def test_labels(self) -> None:
        """
        The given labels are applied to the new container.
        """

    def test_multiple(self) -> None:
        """
        Multiple sidecars can exist at once.
        """

    def test_accessible_multiple_containers(self) -> None:
        """
        The block device created is accessible to multiple containers.
        """

        # TODO new container cannot access
        # TODO destroy new container
        # TODO old container is gone
        # TODO update CLI
        # TODO remove tty
        # TODO test size

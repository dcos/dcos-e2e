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
            size=1,
            labels=labels,
        ) as device:
            exit_code, output = device.container.exec_run(
                cmd=['lsblk', device.path],
            )

            # TODO new container can access this
            assert exit_code == 0, device.path + ': ' + output.decode()

            for key, value in labels.items():
                assert device.container.labels[key] == value

        # TODO new container cannot access
        # TODO old container is gone
        # TODO update CLI

"""
Helpers for creating loopback devices on Docker.
"""

from typing import Any, Dict, Optional, Tuple

import docker


class DockerLoopbackVolume():
    """
    A loopback device sidecar, created in a Docker container.
    """

    def __init__(
        self,
        name: str,
        size: int,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Create a loopback device pointing to a block device running
        in a container. This can be used to provide an unformatted
        disk to a cluster.

        Args:
            name: Unique name of the loopback volume.
            size: Size of the block device in Megabytes.
            labels: Docker labels to add to the container.
        """
        self.size = size

        self.container, self.path = DockerLoopbackVolume.create(
            name=name,
            size=size,
            labels=labels,
        )

    @staticmethod
    def create(
        name: str,
        size: int,
        labels: Optional[Dict[str, str]] = None,
    ) -> Tuple[docker.models.containers.Container, str]:
        """
        Create a loopback device pointing to a block device running
        in a container.

        Args:
            name: Unique name of the loopback volume.
            size: Size of the block device in Megabytes.
            labels: Docker labels to add to the container.

        Returns:
            A tuple containing the container and the path of
            the loopback device.
        """
        client = docker.from_env(version='auto')

        # We use CentOS 7 here, as it provides all the binaries we need
        # and might already be pulled as it is a distribution supported
        # by DC/OS.
        container = client.containers.create(
            name='dcos-e2e-loopback-sidecar-{name}'.format(name=name),
            privileged=True,
            detach=True,
            tty=True,
            image='centos:7',
            labels=labels or {},
        )
        container.start()

        create_loopback_device = (
            'dd if=/dev/zero of=/volume0 bs=1M count={size};'
        ).format(size=size)

        exit_code, output = container.exec_run(
            cmd=['/bin/bash', '-c', create_loopback_device],
        )
        assert exit_code == 0, output.decode()

        setup_loopback_device = 'losetup --find --show /volume0;'

        exit_code, output = container.exec_run(
            cmd=['/bin/bash', '-c', setup_loopback_device],
        )
        assert exit_code == 0, output.decode()

        path = output.decode().rstrip()

        write_device_path = 'echo {path} > loopback_device_path'.format(
            path=path,
        )

        exit_code, output = container.exec_run(
            cmd=['/bin/bash', '-c', write_device_path],
        )
        assert exit_code == 0, output.decode()

        return (container, path)

    @staticmethod
    def destroy(container: docker.models.containers.Container) -> None:
        """
        Destroy a container containing a block device that is used with
        loopback devices. Also removes the loopback device.

        Args:
            container: The container to destroy.
        """
        exit_code, output = container.exec_run(
            cmd=['cat', 'loopback_device_path'],
        )
        assert exit_code == 0, output.decode()

        path = output.decode().rstrip()

        exit_code, output = container.exec_run(cmd=['losetup', '-d', path])
        assert exit_code == 0, output.decode()

        container.stop()
        container.remove(v=True)

    def __enter__(self) -> 'DockerLoopbackVolume':
        """
        Enter a context manager.
        The context manager receives this ``DockerLoopbackVolume`` instance.
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Any,
    ) -> bool:
        """
        On exiting, destroy the loopback volume.
        """
        DockerLoopbackVolume.destroy(self.container)
        return True

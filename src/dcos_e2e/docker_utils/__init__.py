"""
Helpers for creating loopback devices on Docker.
"""

import uuid
from typing import Any, Dict, Optional

import docker

from dcos_e2e.backends import Docker


class DockerLoopbackVolume:
    """
    A loopback device sidecar, created in a Docker container.
    """

    def __init__(
        self,
        size_megabytes: int,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Create a loopback device pointing to a block device running
        in a container. This can be used to provide an unformatted
        disk to a cluster.

        Args:
            size_megabytes: Size of the block device in Megabytes.
            labels: Docker labels to add to the container.

        Attributes:
            path: The path to the block device inside the container.
        """
        client = docker.from_env(version='auto')

        # We use CentOS 7 here, as it provides all the binaries we need
        # and might already be pulled as it is a distribution supported
        # by DC/OS.
        self._container = client.containers.create(
            name='{prefix}-loopback-sidecar-{random}'.format(
                prefix=Docker().container_name_prefix,
                random=uuid.uuid4().hex,
            ),
            privileged=True,
            detach=True,
            tty=True,
            image='centos:7',
            labels=labels or {},
        )
        self._container.start()

        create_loopback_device = [
            'dd',
            'if=/dev/zero',
            'of=volume0',
            'bs=1M',
            'count={size}'.format(size=size_megabytes),
        ]

        exit_code, output = self._container.exec_run(
            cmd=create_loopback_device,
        )
        assert exit_code == 0, output.decode()

        setup_loopback_device = 'losetup --find --show /volume0;'

        exit_code, output = self._container.exec_run(
            cmd=['/bin/bash', '-c', setup_loopback_device],
        )
        assert exit_code == 0, output.decode()

        self.path = output.decode().rstrip()

        write_device_path = 'echo {path} > loopback_device_path'.format(
            path=self.path,
        )

        exit_code, output = self._container.exec_run(
            cmd=['/bin/bash', '-c', write_device_path],
        )
        assert exit_code == 0, output.decode()

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
        DockerLoopbackVolume.destroy(self._container)
        return False

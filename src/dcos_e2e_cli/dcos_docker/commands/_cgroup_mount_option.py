"""
Mount /sys/fs/cgroup Option
"""

from typing import Callable

import click


def cgroup_mount_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    Option for choosing to mount `/sys/fs/cgroup` into the container.
    """
    function = click.option(
        '--mount-sys-fs-cgroup/--no-mount-sys-fs-cgroup',
        default=True,
        show_default=True,
        help=(
            'Mounting ``/sys/fs/cgroup`` from the host is required to run '
            'applications which require ``cgroup`` isolation. '
            'Choose to not mount ``/sys/fs/cgroup`` if it is not available on '
            'the host.'
        ),
    )(command)  # type: Callable[..., None]
    return function

"""
Linux Distribution Option
"""

from typing import Callable, Union

import click

from dcos_e2e.distributions import Distribution

_LINUX_DISTRIBUTIONS = {
    'centos-7': Distribution.CENTOS_7,
    'centos-8': Distribution.CENTOS_8,
    'coreos': Distribution.COREOS,
    'flatcar': Distribution.FLATCAR,
    'ubuntu-16.04': Distribution.UBUNTU_16_04,
}


def _get_linux_distribution(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: str,
) -> Distribution:
    """
    Get the chosen Linux distribution.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    return _LINUX_DISTRIBUTIONS[value]


def linux_distribution_option(command: Callable[..., None],
                              ) -> Callable[..., None]:
    """
    Option for choosing the Linux distribution to use.
    """
    function = click.option(
        '--linux-distribution',
        type=click.Choice(sorted(_LINUX_DISTRIBUTIONS.keys())),
        default='centos-7',
        show_default=True,
        help='The Linux distribution to use on the nodes.',
        callback=_get_linux_distribution,
    )(command)  # type: Callable[..., None]
    return function

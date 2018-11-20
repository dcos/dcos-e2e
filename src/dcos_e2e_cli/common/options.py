"""
Click options which are common across CLI tools.
"""

import re
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import click
import yaml

from .validators import (
    validate_path_is_directory,
    validate_path_pair,
    validate_paths_are_directories,
)


def _validate_cluster_id(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Optional[Union[int, bool, str]],
) -> str:
    """
    Validate that a value is a valid cluster ID.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    # This matches the Docker ID regular expression.
    # This regular expression can be seen by running:
    # > docker run -it --rm --id=' WHAT ? I DUNNO ! ' alpine
    if not re.fullmatch('^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', str(value)):
        message = (
            'Invalid cluster id "{value}", only [a-zA-Z0-9][a-zA-Z0-9_.-] '
            'are allowed and the cluster ID cannot be empty.'
        ).format(value=value)
        raise click.BadParameter(message)

    return str(value)


def _validate_environment_variable(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Any,
) -> Dict[str, str]:
    """
    Validate that environment variables are set as expected.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (param, ctx):
        pass

    env = {}
    for definition in value:
        try:
            key, val = definition.split(sep='=', maxsplit=1)
        except ValueError:
            message = (
                '"{definition}" does not match the format "<KEY>=<VALUE>".'
            ).format(definition=definition)
            raise click.BadParameter(message=message)
        env[key] = val
    return env


def _validate_dcos_configuration(
    ctx: click.core.Context,
    param: Union[click.core.Option, click.core.Parameter],
    value: Union[int, bool, str],
) -> Dict[str, Any]:
    """
    Validate that a given value is a file containing a YAML map.
    """
    # We "use" variables to satisfy linting tools.
    for _ in (ctx, param):
        pass

    if value is None:
        return {}

    content = Path(str(value)).read_text()

    try:
        return dict(yaml.load(content) or {})
    except ValueError:
        message = '"{content}" is not a valid DC/OS configuration'.format(
            content=content,
        )
    except yaml.YAMLError:
        message = '"{content}" is not valid YAML'.format(content=content)

    raise click.BadParameter(message=message)


def masters_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of masters.
    """
    function = click.option(
        '--masters',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of master nodes.',
    )(command)  # type: Callable[..., None]
    return function


def agents_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of agents.
    """
    function = click.option(
        '--agents',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of agent nodes.',
    )(command)  # type: Callable[..., None]
    return function


def public_agents_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the number of agents.
    """
    function = click.option(
        '--public-agents',
        type=click.INT,
        default=1,
        show_default=True,
        help='The number of public agent nodes.',
    )(command)  # type: Callable[..., None]
    return function


def environment_variables_option(command: Callable[..., None],
                                 ) -> Callable[..., None]:
    """
    An option decorator for setting environment variables.
    """
    function = click.option(
        '--env',
        type=str,
        callback=_validate_environment_variable,
        multiple=True,
        help='Set environment variables in the format "<KEY>=<VALUE>"',
    )(command)  # type: Callable[..., None]
    return function


def superuser_username_option(command: Callable[..., None],
                              ) -> Callable[..., None]:
    """
    An option decorator for a superuser username.
    """
    function = click.option(
        '--superuser-username',
        type=str,
        default='admin',
        help=(
            'The superuser username is needed only on DC/OS Enterprise '
            'clusters. '
            'By default, on a DC/OS Enterprise cluster, `admin` is used.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def superuser_password_option(command: Callable[..., None],
                              ) -> Callable[..., None]:
    """
    An option decorator for a superuser password.
    """
    function = click.option(
        '--superuser-password',
        type=str,
        default='admin',
        help=(
            'The superuser password is needed only on DC/OS Enterprise '
            'clusters. '
            'By default, on a DC/OS Enterprise cluster, `admin` is used.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def extra_config_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for supplying extra DC/OS configuration options.
    """
    function = click.option(
        '--extra-config',
        type=click.Path(exists=True),
        callback=_validate_dcos_configuration,
        help=(
            'The path to a file including DC/OS configuration YAML. '
            'The contents of this file will be added to add to a default '
            'configuration.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def workspace_dir_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the workspace directory.
    """
    help_text = (
        'Creating a cluster can use approximately 2 GB of temporary storage. '
        'Set this option to use a custom "workspace" for this temporary '
        'storage. '
        'See '
        'https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir '
        'for details on the temporary directory location if this option is '
        'not set.'
    )
    function = click.option(
        '--workspace-dir',
        type=click.Path(exists=True),
        callback=validate_path_is_directory,
        help=help_text,
    )(command)  # type: Callable[..., None]
    return function


def variant_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for a DC/OS variant.
    """
    function = click.option(
        '--variant',
        type=click.Choice(['auto', 'oss', 'enterprise']),
        default='auto',
        help=(
            'Choose the DC/OS variant. '
            'If the variant does not match the variant of the given '
            'installer, an error will occur. '
            'Using "auto" finds the variant from the installer. '
            'Finding the variant from the installer takes some time and so '
            'using another option is a performance optimization.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def license_key_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for passing a license key.
    """
    function = click.option(
        '--license-key',
        type=click.Path(exists=True),
        envvar='DCOS_LICENSE_KEY_PATH',
        help=(
            'This is ignored if using open source DC/OS. '
            'If using DC/OS Enterprise, this defaults to the value of the '
            '`DCOS_LICENSE_KEY_PATH` environment variable.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def security_mode_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for the DC/OS Enterprise security mode.
    """
    function = click.option(
        '--security-mode',
        type=click.Choice(['disabled', 'permissive', 'strict']),
        help=(
            'The security mode to use for a DC/OS Enterprise cluster. '
            'This overrides any security mode set in ``--extra-config``.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def copy_to_master_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    A decorator for setting files to copy to master nodes before installing
    DC/OS.
    """
    function = click.option(
        '--copy-to-master',
        type=str,
        callback=validate_path_pair,
        multiple=True,
        help=(
            'Files to copy to master nodes before installing DC/OS. '
            'This option can be given multiple times. '
            'Each option should be in the format '
            '/absolute/local/path:/remote/path.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def dcos_login_uname_option(command: Callable[..., None],
                            ) -> Callable[..., None]:
    """
    A decorator for choosing the username to set the ``DCOS_LOGIN_UNAME``
    environment variable to.
    """
    function = click.option(
        '--dcos-login-uname',
        type=str,
        default='admin',
        help=(
            'The username to set the ``DCOS_LOGIN_UNAME`` environment '
            'variable to.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def dcos_login_pw_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    A decorator for choosing the password to set the ``DCOS_LOGIN_PW``
    environment variable to.
    """
    function = click.option(
        '--dcos-login-pw',
        type=str,
        default='admin',
        help=(
            'The password to set the ``DCOS_LOGIN_PW`` environment variable '
            'to.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def sync_dir_run_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    A decorator for choosing a DC/OS checkout to sync before running commands.
    """
    function = click.option(
        '--sync-dir',
        type=click.Path(exists=True),
        multiple=True,
        help=(
            'The path to a DC/OS checkout. '
            'Part of this checkout will be synced to all master nodes before '
            'the command is run. '
            'The bootstrap directory is synced if the checkout directory '
            'variant matches the cluster variant.'
            'Integration tests are also synced.'
            'Use this option multiple times on a DC/OS Enterprise cluster to '
            'sync both DC/OS Enterprise and DC/OS Open Source tests.'
        ),
        callback=validate_paths_are_directories,
    )(command)  # type: Callable[..., None]
    return function


def verbosity_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    A decorator for setting the verbosity of logging.
    """
    function = click.option(
        '-v',
        '--verbose',
        help=(
            'Use verbose output. '
            'Use this option multiple times for more verbose output.'
        ),
        count=True,
    )(command)  # type: Callable[..., None]
    return function


def test_env_run_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    A decorator for choosing whether to run commands in a test environment.
    """
    function = click.option(
        '--test-env',
        '-te',
        is_flag=True,
        help=(
            'With this flag set, environment variables are set and the '
            'command is run in the integration test directory. '
            'This means that "pytest" will run the integration tests.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def cluster_id_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    A Click option for choosing a new cluster ID.
    """
    function = click.option(
        '-c',
        '--cluster-id',
        type=str,
        default='default',
        callback=_validate_cluster_id,
        help=(
            'A unique identifier for the cluster. '
            'Use the value "default" to use this cluster for other '
            'commands without specifying --cluster-id.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def existing_cluster_id_option(command: Callable[..., None],
                               ) -> Callable[..., None]:
    """
    An option decorator for an existing Cluster ID.
    """
    function = click.option(
        '-c',
        '--cluster-id',
        type=str,
        default='default',
        show_default=True,
        help='The ID of the cluster to use.',
    )(command)  # type: Callable[..., None]
    return function


def genconf_dir_option(command: Callable[..., None]) -> Callable[..., None]:
    """
    An option decorator for a custom "genconf" directory.
    """
    function = click.option(
        '--genconf-dir',
        type=click.Path(exists=True),
        callback=validate_path_is_directory,
        help=(
            'Path to a directory that contains additional files for the DC/OS '
            'installer. '
            'All files from this directory will be copied to the "genconf" '
            'directory before running the DC/OS installer.'
        ),
    )(command)  # type: Callable[..., None]
    return function


def enable_selinux_enforcing_option(command: Callable[..., None],
                                    ) -> Callable[..., None]:
    """
    An option decorator for setting the SELinux mode to "enforcing".
    """
    function = click.option(
        '--enable-selinux-enforcing',
        is_flag=True,
        help=(
            'With this flag set, SELinux is set to enforcing before DC/OS is '
            'installed on the cluster.'
        ),
    )(command)  # type: Callable[..., None]
    return function

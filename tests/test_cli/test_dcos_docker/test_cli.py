"""
Tests for the Docker CLI.

This mostly provides error case coverage.
We rely mostly on manual testing.
This is because automated tests for this would be very slow.
"""

import os
import uuid
from pathlib import Path
from tempfile import mkstemp
from textwrap import dedent
from typing import List

import pytest
from click.testing import CliRunner

from dcos_e2e_cli import dcos_docker, minidcos

_SUBCOMMANDS = [[item] for item in dcos_docker.commands.keys()]
_BASE_COMMAND = [[]]  # type: List[List[str]]
_COMMANDS = _BASE_COMMAND + _SUBCOMMANDS


class TestHelp:
    """
    Test help texts.
    """

    @pytest.mark.parametrize(
        'command',
        _COMMANDS,
        ids=[str(cmd) for cmd in _COMMANDS],
    )
    def test_help(self, command: List[str]) -> None:
        """
        Expected help text is shown for ``minidcos docker`` commands.

        This help text is defined in files.
        To update these files, run the command
        ``bash admin/update_cli_tests.sh``.
        """
        runner = CliRunner()
        arguments = ['docker'] + command + ['--help']
        result = runner.invoke(minidcos, arguments, catch_exceptions=False)
        assert result.exit_code == 0
        help_output_filename = '-'.join(['dcos-docker'] + command) + '.txt'
        help_outputs_dir = Path(__file__).parent / 'help_outputs'
        expected_help_file = help_outputs_dir / help_output_filename
        try:
            expected_help = expected_help_file.read_text()
            assert result.output == expected_help
        except (AssertionError, FileNotFoundError):  # pragma: no cover
            if os.getenv('FIX_CLI_TESTS') == '1':
                help_outputs_dir.mkdir(exist_ok=True)
                expected_help_file.touch()
                expected_help_file.write_text(result.output)
            else:
                raise


class TestCreate:
    """
    Tests for the `create` subcommand.
    """

    def test_copy_to_master_bad_format(
        self,
        oss_installer: Path,
    ) -> None:
        """
        An error is shown if ``--copy-to-master`` is given a value in an
        invalid format.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--copy-to-master',
                '/some/path',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER

            Error: Invalid value for "--copy-to-master": "/some/path" is not in the format /absolute/local/path:/remote/path.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

    def test_copy_to_master_no_local(self, oss_installer: Path) -> None:
        """
        An error is shown if the given local path does not exist.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--copy-to-master',
                '/some/path:some/remote',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER

            Error: Invalid value for "--copy-to-master": "/some/path" does not exist.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

    @pytest.mark.parametrize(
        'option',
        [
            '--custom-volume',
            '--custom-master-volume',
            '--custom-agent-volume',
            '--custom-public-agent-volume',
        ],
    )
    def test_custom_volume_bad_mode(
        self,
        oss_installer: Path,
        option: str,
    ) -> None:
        """
        Given volumes must have the mode "rw" or "ro", or no mode.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                option,
                '/opt:/opt:ab',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER

            Error: Invalid value for "{option}": Mode in "/opt:/opt:ab" is "ab". If given, the mode must be one of "ro", "rw".
            """,# noqa: E501,E261
        ).format(option=option)
        # yapf: enable
        assert result.output == expected_message

    @pytest.mark.parametrize(
        'option',
        [
            '--custom-volume',
            '--custom-master-volume',
            '--custom-agent-volume',
            '--custom-public-agent-volume',
        ],
    )
    def test_custom_volume_bad_format(
        self,
        oss_installer: Path,
        option: str,
    ) -> None:
        """
        Given volumes must have 0, 1 or 2 colons.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                option,
                '/opt:/opt:/opt:rw',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER

            Error: Invalid value for "{option}": "/opt:/opt:/opt:rw" is not a valid volume definition. See https://docs.docker.com/engine/reference/run/#volume-shared-filesystems for the syntax to use.
            """,# noqa: E501,E261
        ).format(option=option)
        # yapf: enable
        assert result.output == expected_message

    def test_copy_to_master_relative(
        self,
        oss_installer: Path,
    ) -> None:
        """
        An error is shown if the given local path is not an absolute path.
        """
        _, temporary_file_path = mkstemp(dir='.')
        relative_path = Path(temporary_file_path).relative_to(os.getcwd())

        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--copy-to-master',
                '{relative}:some/remote'.format(relative=relative_path),
            ],
            catch_exceptions=False,
        )
        Path(relative_path).unlink()
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER

            Error: Invalid value for "--copy-to-master": "some/remote is not an absolute path.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

    def test_invalid_installer_path(self) -> None:
        """
        An error is shown if an invalid installer path is given.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'create', '/not/a/path'],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "INSTALLER": '
            'File "/not/a/path" does not exist.'
        )
        assert expected_error in result.output

    def test_config_does_not_exist(self, oss_installer: Path) -> None:
        """
        An error is shown if the ``--extra-config`` file does not exist.
        """
        runner = CliRunner()
        invalid_path = '/' + uuid.uuid4().hex
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--extra-config',
                invalid_path,
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER
            Try "minidcos docker create -h" for help.

            Error: Invalid value for "--extra-config": File "{path}" does not exist.
            """,# noqa: E501,E261
        ).format(path=invalid_path)
        # yapf: enable
        assert result.output == expected_message

    def test_invalid_yaml(self, oss_installer: Path, tmp_path: Path) -> None:
        """
        An error is shown if invalid YAML is given in the file given to
        ``--extra-config``.
        """
        invalid_file = tmp_path / uuid.uuid4().hex
        invalid_file.write_text('@')
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--extra-config',
                str(invalid_file),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
           Usage: minidcos docker create [OPTIONS] INSTALLER

           Error: Invalid value for "--extra-config": "@" is not valid YAML
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

    def test_not_key_value(self, oss_installer: Path, tmp_path: Path) -> None:
        """
        An error is shown if YAML is given for ``--extra-config`` which is not
        a key-value mapping.
        """
        invalid_file = tmp_path / uuid.uuid4().hex
        invalid_file.write_text('example')
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--extra-config',
                str(invalid_file),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER

            Error: Invalid value for "--extra-config": "example" is not a valid DC/OS configuration
            """,  # noqa: E501
        )
        # yapf: enable
        assert result.output == expected_message

    @pytest.mark.parametrize('invalid_id', ['@', ''])
    def test_invalid_cluster_id(
        self,
        oss_installer: Path,
        invalid_id: str,
    ) -> None:
        """
        Cluster IDs must match a certain pattern.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--cluster-id',
                invalid_id,
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
            """\
            Usage: minidcos docker create [OPTIONS] INSTALLER

            Error: Invalid value for "-c" / "--cluster-id": Invalid cluster id "{cluster_id}", only [a-zA-Z0-9][a-zA-Z0-9_.-] are allowed and the cluster ID cannot be empty.
            """,  # noqa: E501
        ).format(cluster_id=invalid_id)
        # yapf: enable
        assert result.output == expected_message

    def test_genconf_path_not_exist(self, oss_installer: Path) -> None:
        """
        Genconf path must exist.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--genconf-dir',
                'non-existing',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--genconf-dir": '
            'Directory "non-existing" does not exist.'
        )
        assert expected_error in result.output

    def test_genconf_path_is_file(
        self,
        oss_installer: Path,
        tmp_path: Path,
    ) -> None:
        """
        Genconf path must be a directory.
        """
        genconf_file = tmp_path / 'testfile'
        genconf_file.write_text('test')

        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--genconf-dir',
                str(genconf_file),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--genconf-dir": '
            'Directory "{path}" is a file.'
        ).format(path=str(genconf_file))
        assert expected_error in result.output

    def test_workdir_path_not_exist(self, oss_installer: Path) -> None:
        """
        ``--workspace-dir`` must exist.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--workspace-dir',
                'non-existing',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--workspace-dir": '
            'Directory "non-existing" does not exist.'
        )
        assert expected_error in result.output

    def test_workspace_path_is_file(
        self,
        oss_installer: Path,
        tmp_path: Path,
    ) -> None:
        """
        ``--workspace-dir`` must be a directory.
        """
        workspace_file = tmp_path / 'testfile'
        workspace_file.write_text('test')

        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'create',
                str(oss_installer),
                '--workspace-dir',
                str(workspace_file),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--workspace-dir": '
            'Directory "{path}" is a file.'
        ).format(path=str(workspace_file))
        assert expected_error in result.output


class TestDestroy:
    """
    Tests for the `destroy` subcommand.
    """

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'destroy', '--cluster-id', unique],
        )
        assert result.exit_code == 2
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output


class TestDestroyList:
    """
    Tests for the `destroy-list` subcommand.
    """

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'destroy-list', unique],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output

    def test_multiple_clusters(self) -> None:
        """
        It is possible to give multiple cluster IDs.
        """
        unique = uuid.uuid4().hex
        unique_2 = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'destroy-list', unique, unique_2],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output
        expected_error = expected_error.format(unique=unique_2)
        assert expected_error in result.output


class TestInspect:
    """
    Tests for the `inspect` subcommand.
    """

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'inspect', '--cluster-id', unique],
        )
        assert result.exit_code == 2
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output


class TestWait:
    """
    Tests for the ``wait`` subcommand.
    """

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'wait', '--cluster-id', unique],
        )
        assert result.exit_code == 2
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output


class TestDoctor:
    """
    Tests for the ``doctor`` subcommand.
    """

    def test_doctor(self) -> None:
        """
        No exception is raised by the ``doctor`` subcommand.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'doctor'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


class TestSetupMacNetwork():
    """
    Tests for the ``setup-mac-network`` subcommand.
    """

    def test_suffix_not_ovpn(self, tmp_path: Path) -> None:
        """
        If a configuration file does not have the 'ovpn' suffix, an error is
        shown.
        """
        configuration_file = tmp_path / 'example.txt'
        configuration_file.write_text('example')
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'setup-mac-network',
                '--configuration-dst',
                str(configuration_file),
            ],
            catch_exceptions=False,
        )
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_error = dedent(
            """\
            Usage: minidcos docker setup-mac-network [OPTIONS]

            Error: Invalid value for "--configuration-dst": "{value}" does not have the suffix ".ovpn".
            """,# noqa: E501,E261
        ).format(
            value=str(configuration_file),
        )
        # yapf: enable
        assert result.exit_code == 2
        assert result.output == expected_error

    def test_configuration_already_exists(self, tmp_path: Path) -> None:
        """
        If a configuration file already exists at the given location, an error
        is shown.
        """
        profile_name = uuid.uuid4().hex
        configuration_filename = str(Path(profile_name).with_suffix('.ovpn'))
        configuration_file = tmp_path / configuration_filename
        configuration_file.write_text('example')
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            [
                'docker',
                'setup-mac-network',
                '--configuration-dst',
                str(configuration_file),
            ],
            catch_exceptions=False,
        )
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_error = dedent(
            """\
            Usage: minidcos docker setup-mac-network [OPTIONS]

            Error: Invalid value: "{configuration_dst}" already exists so no new OpenVPN configuration was created.

            To use {configuration_dst}:
            1. Install an OpenVPN client such as Tunnelblick (https://tunnelblick.net/downloads.html) or Shimo (https://www.shimovpn.com).
            2. Run "open {configuration_dst}".
            3. If your OpenVPN client is Shimo, edit the new "{profile_name}" profile's Advanced settings to deselect "Send all traffic over VPN".
            4. In your OpenVPN client, connect to the new "{profile_name}" profile.
            5. Run "minidcos docker doctor" to confirm that everything is working.
            """,# noqa: E501,E261
        ).format(
            configuration_dst=str(configuration_file),
            profile_name=profile_name,
        )
        # yapf: enable
        assert result.exit_code == 2
        assert result.output == expected_error


class TestCreateLoopbackSidecar:
    """
    Tests for the ``create-loopback-sidecar`` subcommand.
    """

    def test_sidecar_container_already_exists(self) -> None:
        """
        An error is shown if the given sidecar container already exists.
        """
        test_sidecar = 'test-sidecar'
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'create-loopback-sidecar', test_sidecar],
        )
        assert result.exit_code == 0

        try:
            result = runner.invoke(
                minidcos,
                ['docker', 'create-loopback-sidecar', test_sidecar],
            )
            assert result.exit_code == 2
            expected_error = 'Loopback sidecar "{name}" already exists'
            expected_error = expected_error.format(name=test_sidecar)
            assert expected_error in result.output
        finally:
            result = runner.invoke(
                minidcos,
                ['docker', 'destroy-loopback-sidecar', test_sidecar],
            )
            assert result.exit_code == 0


class TestDestroyLoopbackSidecar:
    """
    Tests for the ``destroy-loopback-sidecar`` subcommand.
    """

    def test_sidecar_container_does_not_exist(self) -> None:
        """
        An error is shown if the given sidecar container does not exist.
        """
        does_not_exist = 'does-not-exist'
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'destroy-loopback-sidecar', does_not_exist],
        )
        assert result.exit_code == 2
        expected_error = 'Loopback sidecar "{name}" does not exist'
        expected_error = expected_error.format(name=does_not_exist)
        assert expected_error in result.output


class TestListLoopbackSidecars:
    """
    Tests for the ``list-loopback-sidecars`` subcommand.
    """

    def test_no_error(self) -> None:
        """
        A success code is given.
        """
        runner = CliRunner()
        result = runner.invoke(
            minidcos,
            ['docker', 'list-loopback-sidecars'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

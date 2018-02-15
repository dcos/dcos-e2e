"""
Tests for the CLI.

This mostly provides error case coverage.
We rely mostly on manual testing.
This is because automated tests for this would be very slow.

For developing help texts, it is useful to add a breakpoint on failure and then
to capture what the help text actually is with:

  .. code: python

       import pyperclip; pyperclip.copy(result.output)
"""

import uuid
from pathlib import Path
from textwrap import dedent
from typing import List

import pytest
from click.testing import CliRunner
# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
from py.path import local  # pylint: disable=no-name-in-module, import-error

from cli import dcos_docker


class TestDcosDocker:
    """
    Tests for the top level `dcos_docker` command.
    """

    @pytest.mark.parametrize('arguments', [
        [],
        ['--help'],
    ])
    def test_help(self, arguments: List[str]) -> None:
        """
        Help test is shown with `dcos_docker` and `dcos_docker --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, arguments, catch_exceptions=False)
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker [OPTIONS] COMMAND [ARGS]...

              Manage DC/OS clusters on Docker.

            Options:
              -v, --verbose
              --help         Show this message and exit.

            Commands:
              create   Create a DC/OS cluster.
              destroy  Destroy clusters.
              doctor   Diagnose common issues which stop DC/OS E2E...
              inspect  Show cluster details.
              list     List all clusters.
              run      Run an arbitrary command on a node.
              sync     Sync files from a DC/OS checkout to master...
              wait     Wait for DC/OS to start.
            """
        )
        assert result.output == expected_help


class TestCreate:
    """
    Tests for the `create` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker create --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['create', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos_docker create [OPTIONS] ARTIFACT

              Create a DC/OS cluster.

                  DC/OS Enterprise

                              DC/OS Enterprise clusters require different configuration variables to DC/OS OSS.
                              For example, enterprise clusters require the following configuration parameters:

                      ``superuser_username``, ``superuser_password_hash``,
                      ``fault_domain_enabled``, ``license_key_contents``

                              These can all be set in ``extra_config``.
                              However, some defaults are provided for all but the license key.

                              The default superuser username is ``admin``.
                              The default superuser password is ``admin``.
                              The default ``fault_domain_enabled`` is ``false``.

                              ``license_key_contents`` must be set for DC/OS Enterprise 1.11 and above.
                              This is set to one of the following, in order:

                              * The ``license_key_contents`` set in ``extra_config``.
                              * The contents of the path given with ``--license-key-path``.
                              * The contents of the path set in the ``DCOS_LICENSE_KEY_PATH`` environment variable.

                              If none of these are set, ``license_key_contents`` is not given.

            Options:
              --docker-version [1.13.1|1.11.2]
                                              The Docker version to install on the nodes.
                                              [default: 1.13.1]
              --linux-distribution [centos-7|ubuntu-16.04|coreos|fedora-23|debian-8]
                                              The Linux distribution to use on the nodes.
                                              [default: centos-7]
              --docker-storage-driver [aufs|overlay|overlay2]
                                              The storage driver to use for Docker in
                                              Docker. By default this uses the host's
                                              driver.
              --masters INTEGER               The number of master nodes.  [default: 1]
              --agents INTEGER                The number of agent nodes.  [default: 1]
              --public-agents INTEGER         The number of public agent nodes.  [default:
                                              1]
              --extra-config TEXT             Extra DC/OS configuration YAML to add to a
                                              default configuration.
              --security-mode [disabled|permissive|strict]
                                              The security mode to use for a DC/OS
                                              Enterprise cluster. This overrides any
                                              security mode set in ``extra_config``.
              -c, --cluster-id TEXT           A unique identifier for the cluster. Defaults
                                              to a random value. Use the value "default" to
                                              use this cluster for other
              --license-key-path PATH         This is ignored if using open source DC/OS. If
                                              using DC/OS Enterprise, this defaults to the
                                              value of the `DCOS_LICENSE_KEY_PATH`
                                              environment variable.
              --genconf-path PATH             Path to a directory that contains additional
                                              files for DC/OS installer. All files from this
                                              directory will be copied to the `genconf`
                                              directory before running DC/OS installer.
              --help                          Show this message and exit.
            """# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

    def test_invalid_artifact_path(self) -> None:
        """
        An error is shown if an invalid artifact path is given.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['create', '/not/a/path'],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "artifact": '
            'Path "/not/a/path" does not exist.'
        )
        assert expected_error in result.output

    def test_invalid_yaml(self, oss_artifact: Path) -> None:
        """
        An error is shown if invalid YAML is given for `--extra-config`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--extra-config',
                '@',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_message = dedent(
            """\
           Usage: dcos_docker create [OPTIONS] ARTIFACT

           Error: Invalid value for "--extra-config": "@" is not valid YAML
           """
        )
        assert result.output == expected_message

    def test_not_key_value(self, oss_artifact: Path) -> None:
        """
        An error is shown if YAML is given for `--extra-config` which is not
        a key-value mapping.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--extra-config',
                'some_key',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_message = dedent(
           """\
           Usage: dcos_docker create [OPTIONS] ARTIFACT

           Error: Invalid value for "--extra-config": "some_key" is not a valid DC/OS configuration
            """# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

    @pytest.mark.parametrize('invalid_id', ['@', ''])
    def test_invalid_cluster_id(
        self,
        oss_artifact: Path,
        invalid_id: str,
    ) -> None:
        """
        Cluster IDs must match a certain pattern.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
            Usage: dcos_docker create [OPTIONS] ARTIFACT

            Error: Invalid value for "-c" / "--cluster-id": Invalid cluster id "{cluster_id}", only [a-zA-Z0-9][a-zA-Z0-9_.-] are allowed and the cluster ID cannot be empty.
            """# noqa: E501,E261
        ).format(cluster_id=invalid_id)
        # yapf: enable
        assert result.output == expected_message

    def test_genconf_path_does_not_exist(self, oss_artifact: Path) -> None:
        """
        Genconf path must exist.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--genconf-path',
                'non-existing',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--genconf-path": '
            'Path "non-existing" does not exist.'
        )
        assert expected_error in result.output

    def test_genconf_path_is_file(
        self,
        oss_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        Genconf path must be a directory.
        """
        file = tmpdir.join('testfile')
        file.write("test")

        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--genconf-path',
                str(file),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--genconf-path": '
            '"{path}" is not a directory.'
        ).format(path=str(file))
        assert expected_error in result.output


class TestDestroy:
    """
    Tests for the `destroy` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker destroy --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['destroy', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos_docker destroy [OPTIONS] [CLUSTER_IDS]...

              Destroy clusters.

              To destroy all clusters, run ``dcos_docker destroy $(dcos_docker list)``.

            Options:
              --help  Show this message and exit.
            """# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['destroy', unique],
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
            dcos_docker,
            ['destroy', unique, unique_2],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output
        expected_error = expected_error.format(unique=unique_2)
        assert expected_error in result.output


class TestList:
    """
    Tests for the `list` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker list --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['list', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker list [OPTIONS]

              List all clusters.

            Options:
              --help  Show this message and exit.
            """
        )
        assert result.output == expected_help


class TestInspect:
    """
    Tests for the `inspect` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker inspect --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['inspect', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker inspect [OPTIONS]

              Show cluster details.

              To quickly get environment variables to use with Docker tooling, use the
              ``--env`` flag.

              Run ``eval $(dcos_docker inspect <CLUSTER_ID> --env)``, then run ``docker
              exec -it $MASTER_0`` to enter the first master, for example.

            Options:
              -c, --cluster-id TEXT  If not given, "default" is used.
              --env                  Show details in an environment variable format to eval.
              --help                 Show this message and exit.
            """
        )
        assert result.output == expected_help

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['inspect', '--cluster-id', unique],
        )
        assert result.exit_code == 2
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output


class TestWait:
    """
    Tests for the ``wait`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker inspect --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['wait', '--help'])
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker wait [OPTIONS]

              Wait for DC/OS to start.

            Options:
              -c, --cluster-id TEXT      If not given, "default" is used.
              --superuser-username TEXT  The superuser username is needed only on DC/OS
                                         Enterprise clusters. By default, on a DC/OS
                                         Enterprise cluster, `admin` is used.
              --superuser-password TEXT  The superuser password is needed only on DC/OS
                                         Enterprise clusters. By default, on a DC/OS
                                         Enterprise cluster, `admin` is used.
              --help                     Show this message and exit.
            """
        )
        assert result.output == expected_help

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['wait', '--cluster-id', unique])
        assert result.exit_code == 2
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output


class TestSync:
    """
    Tests for the ``sync`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker sync --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['sync', '--help'])
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker sync [OPTIONS] [CHECKOUT]

              Sync files from a DC/OS checkout to master nodes.

              This syncs integration test files and bootstrap files.

              ``CHECKOUT`` should be set to the path of clone of an open source DC/OS or
              DC/OS Enterprise repository.

              By default the ``CHECKOUT`` argument is set to the value of the
              ``DCOS_CHECKOUT_PATH`` environment variable.

              If no ``CHECKOUT`` is given, the current working directory is used.

            Options:
              -c, --cluster-id TEXT  If not given, "default" is used.
              --help                 Show this message and exit.
            """
        )
        assert result.output == expected_help


class TestDoctor:
    """
    Tests for the ``doctor`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker doctor --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['doctor', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker doctor [OPTIONS]

              Diagnose common issues which stop DC/OS E2E from working correctly.

            Options:
              --help  Show this message and exit.
            """
        )
        assert result.output == expected_help

    def test_doctor(self) -> None:
        """
        No exception is raised by the ``doctor`` subcommand.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['doctor'], catch_exceptions=False)
        assert result.exit_code == 0


class TestWeb:
    """
    Tests for the ``web`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker web --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['web', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker web [OPTIONS]

              Open the browser at the web UI.

              Note that the web UI may not be available at first. Consider using
              ``dcos_docker wait`` before running this command.

            Options:
              -c, --cluster-id TEXT  If not given, "default" is used.
              --help                 Show this message and exit.
            """
        )
        assert result.output == expected_help

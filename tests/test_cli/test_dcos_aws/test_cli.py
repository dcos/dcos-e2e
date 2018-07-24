"""
Tests for the AWS CLI.

This mostly provides error case coverage.
We rely mostly on manual testing.
This is because automated tests for this would be very slow.

For developing help texts, it is useful to add a breakpoint on failure and then
to capture what the help text actually is with:

  .. code: python

       import pyperclip; pyperclip.copy(result.output)
"""

from textwrap import dedent
from typing import List

import pytest
from click.testing import CliRunner

from cli import dcos_aws


class TestDcosAWS:
    """
    Tests for the top level `dcos-aws` command.
    """

    def test_version(self) -> None:
        """
        The CLI version is shown with ``dcos-aws --version``.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_aws,
            ['--version'],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        expected = 'dcos-aws, version'
        assert expected in result.output

    @pytest.mark.parametrize('arguments', [
        [],
        ['--help'],
    ])
    def test_help(self, arguments: List[str]) -> None:
        """
        Help test is shown with `dcos-aws` and `dcos-aws --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_aws, arguments, catch_exceptions=False)
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-aws [OPTIONS] COMMAND [ARGS]...

              Manage DC/OS clusters on AWS.

            Options:
              --version  Show the version and exit.
              --help     Show this message and exit.

            Commands:
              create  Create a DC/OS cluster.
              doctor  Diagnose common issues which stop DC/OS E2E...
              list    List all clusters.
              run     Run an arbitrary command on a node.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestCreate:
    """
    Tests for the `create` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-aws create --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_aws,
            ['create', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-aws create [OPTIONS] ARTIFACT_URL

              Create a DC/OS cluster.

                  DC/OS Enterprise

                              DC/OS Enterprise clusters require different configuration variables to DC/OS OSS.
                              For example, enterprise clusters require the following configuration parameters:

                      ``superuser_username``, ``superuser_password_hash``,
                      ``fault_domain_enabled``, ``license_key_contents``

                              These can all be set in ``--extra-config``.
                              However, some defaults are provided for all but the license key.

                              The default superuser username is ``admin``.
                              The default superuser password is ``admin``.
                              The default ``fault_domain_enabled`` is ``false``.

                              ``license_key_contents`` must be set for DC/OS Enterprise 1.11 and above.
                              This is set to one of the following, in order:

                              * The ``license_key_contents`` set in ``--extra-config``.
                              * The contents of the path given with ``--license-key``.
                              * The contents of the path set in the ``DCOS_LICENSE_KEY_PATH`` environment variable.

                              If none of these are set, ``license_key_contents`` is not given.

            Options:
              --variant [oss|enterprise]      Choose the DC/OS variant. If the variant does
                                              not match the variant of the given artifact
                                              URL, an error will occur.
              --masters INTEGER               The number of master nodes.  [default: 1]
              --agents INTEGER                The number of agent nodes.  [default: 1]
              --extra-config PATH             The path to a file including DC/OS
                                              configuration YAML. The contents of this file
                                              will be added to add to a default
                                              configuration.
              --public-agents INTEGER         The number of public agent nodes.  [default:
                                              1]
              --aws-region TEXT               The AWS region to use.  [default: us-west-2]
              --workspace-dir PATH            Creating a cluster can use approximately 2 GB
                                              of temporary storage. Set this option to use a
                                              custom "workspace" for this temporary storage.
                                              See https://docs.python.org/3/library/tempfile
                                              .html#tempfile.gettempdir for details on the
                                              temporary directory location if this option is
                                              not set.
              --license-key PATH              This is ignored if using open source DC/OS. If
                                              using DC/OS Enterprise, this defaults to the
                                              value of the `DCOS_LICENSE_KEY_PATH`
                                              environment variable.
              --security-mode [disabled|permissive|strict]
                                              The security mode to use for a DC/OS
                                              Enterprise cluster. This overrides any
                                              security mode set in ``--extra-config``.
              --copy-to-master TEXT           Files to copy to master nodes before
                                              installing DC/OS. This option can be given
                                              multiple times. Each option should be in the
                                              format /absolute/local/path:/remote/path.
              -v, --verbose                   Use verbose output. Use this option multiple
                                              times for more verbose output.
              -c, --cluster-id TEXT           A unique identifier for the cluster. Use the
                                              value "default" to use this cluster for other
                                              commands without specifying --cluster-id.
              --help                          Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestList:
    """
    Tests for the `list` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-aws list --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_aws,
            ['list', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos-aws list [OPTIONS]

              List all clusters.

            Options:
              --aws-region TEXT  The AWS region to use.  [default: us-west-2]
              --help             Show this message and exit.
            """,
        )
        assert result.output == expected_help


class TestDoctor:
    """
    Tests for the ``doctor`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-aws doctor --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_aws,
            ['doctor', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-aws doctor [OPTIONS]

              Diagnose common issues which stop DC/OS E2E from working correctly.

            Options:
              --help  Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

    def test_doctor(self) -> None:
        """
        No exception is raised by the ``doctor`` subcommand.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_aws,
            ['doctor'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


class TestRun:
    """
    Tests for the ``run`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-aws run --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_aws,
            ['run', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-aws run [OPTIONS] NODE_ARGS...

              Run an arbitrary command on a node.

              This command sets up the environment so that ``pytest`` can be run.

              For example, run ``dcos-aws run --cluster-id 1231599 pytest -k
              test_tls.py``.

              Or, with sync: ``dcos-aws run --sync-dir . --cluster-id 1231599 pytest -k
              test_tls.py``.

              To use special characters such as single quotes in your command, wrap the
              whole command in double quotes.

            Options:
              -c, --cluster-id TEXT    The ID of the cluster to use.  [default: default]
              --dcos-login-uname TEXT  The username to set the ``DCOS_LOGIN_UNAME``
                                       environment variable to.
              --dcos-login-pw TEXT     The password to set the ``DCOS_LOGIN_PW`` environment
                                       variable to.
              --sync-dir PATH          The path to a DC/OS checkout. Part of this checkout
                                       will be synced to all master nodes before the command
                                       is run.
              --no-test-env            With this flag set, no environment variables are set
                                       and the command is run in the home directory.
              --env TEXT               Set environment variables in the format
                                       "<KEY>=<VALUE>"
              --aws-region TEXT        The AWS region to use.  [default: us-west-2]
              -v, --verbose            Use verbose output. Use this option multiple times
                                       for more verbose output.
              --help                   Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

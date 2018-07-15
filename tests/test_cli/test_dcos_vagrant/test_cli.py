"""
Tests for the Vagrant CLI.

This mostly provides error case coverage.
We rely mostly on manual testing.
This is because automated tests for this would be very slow.

For developing help texts, it is useful to add a breakpoint on failure and then
to capture what the help text actually is with:

  .. code: python

       import pyperclip; pyperclip.copy(result.output)
"""

import os
from textwrap import dedent
from typing import List

import pytest
from click.testing import CliRunner

from cli import dcos_vagrant


class TestDcosVagrant:
    """
    Tests for the top level `dcos-vagrant` command.
    """

    def test_version(self) -> None:
        """
        The CLI version is shown with ``dcos-vagrant --version``.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['--version'],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        expected = 'dcos-vagrant, version'
        assert expected in result.output

    @pytest.mark.parametrize('arguments', [
        [],
        ['--help'],
    ])
    def test_help(self, arguments: List[str]) -> None:
        """
        Help test is shown with `dcos-vagrant` and `dcos-vagrant --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_vagrant, arguments, catch_exceptions=False)
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant [OPTIONS] COMMAND [ARGS]...

              Manage DC/OS clusters on Vagrant.

            Options:
              --version      Show the version and exit.
              -v, --verbose
              --help         Show this message and exit.

            Commands:
              create        Create a DC/OS cluster.
              destroy       Destroy a cluster.
              destroy-list  Destroy clusters.
              doctor        Diagnose common issues which stop DC/OS E2E...
              list          List all clusters.
              wait          Wait for DC/OS to start.
              web           Open the browser at the web UI.
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
        Help text is shown with `dcos-vagrant create --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['create', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant create [OPTIONS] ARTIFACT

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
              --masters INTEGER               The number of master nodes.  [default: 1]
              --agents INTEGER                The number of agent nodes.  [default: 1]
              --extra-config PATH             The path to a file including DC/OS
                                              configuration YAML. The contents of this file
                                              will be added to add to a default
                                              configuration.
              --public-agents INTEGER         The number of public agent nodes.  [default:
                                              1]
              --workspace-dir PATH            Creating a cluster can use approximately 2 GB
                                              of temporary storage. Set this option to use a
                                              custom "workspace" for this temporary storage.
                                              See https://docs.python.org/3/library/tempfile
                                              .html#tempfile.gettempdir for details on the
                                              temporary directory location if this option is
                                              not set.
              --variant [auto|oss|enterprise]
                                              Choose the DC/OS variant. If the variant does
                                              not match the variant of the given artifact,
                                              an error will occur. Using "auto" finds the
                                              variant from the artifact. Finding the variant
                                              from the artifact takes some time and so using
                                              another option is a performance optimization.
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
              -c, --cluster-id TEXT           A unique identifier for the cluster. Use the
                                              value "default" to use this cluster for other
                                              commands without specifying --cluster-id.
              --help                          Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestDestroy:
    """
    Tests for the `destroy` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant destroy --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['destroy', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant destroy [OPTIONS]

              Destroy a cluster.

            Options:
              -c, --cluster-id TEXT  The ID of the cluster to use.  [default: default]
              --help                 Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestDestroyList:
    """
    Tests for the `destroy-list` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant destroy --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['destroy-list', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant destroy-list [OPTIONS] [CLUSTER_IDS]...

              Destroy clusters.

              To destroy all clusters, run ``dcos-vagrant destroy $(dcos-vagrant list)``.

            Options:
              --help  Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestDoctor:
    """
    Tests for the ``doctor`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant doctor --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['doctor', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant doctor [OPTIONS]

              Diagnose common issues which stop DC/OS E2E from working correctly.

            Options:
              --help  Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

    @pytest.mark.skipif(
        os.environ.get('TRAVIS') == 'true',
        reason='It is not possible to run VirtualBox on Travis CI',
    )
    def test_doctor(self) -> None:  # pragma: no cover
        """
        No exception is raised by the ``doctor`` subcommand.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['doctor'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0


class TestList:
    """
    Tests for the `list` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant list --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['list', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos-vagrant list [OPTIONS]

              List all clusters.

            Options:
              --help  Show this message and exit.
            """,
        )
        assert result.output == expected_help


class TestWait:
    """
    Tests for the ``wait`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant wait --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_vagrant, ['wait', '--help'])
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant wait [OPTIONS]

              Wait for DC/OS to start.

            Options:
              -c, --cluster-id TEXT      The ID of the cluster to use.  [default: default]
              --superuser-username TEXT  The superuser username is needed only on DC/OS
                                         Enterprise clusters. By default, on a DC/OS
                                         Enterprise cluster, `admin` is used.
              --superuser-password TEXT  The superuser password is needed only on DC/OS
                                         Enterprise clusters. By default, on a DC/OS
                                         Enterprise cluster, `admin` is used.
              --help                     Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestWeb:
    """
    Tests for the ``web`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant web --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['web', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant web [OPTIONS]

              Open the browser at the web UI.

              Note that the web UI may not be available at first. Consider using ``dcos-
              vagrant wait`` before running this command.

            Options:
              -c, --cluster-id TEXT  The ID of the cluster to use.  [default: default]
              --help                 Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

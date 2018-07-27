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
              --version  Show the version and exit.
              --help     Show this message and exit.

            Commands:
              create             Create a DC/OS cluster.
              destroy            Destroy a cluster.
              destroy-list       Destroy clusters.
              doctor             Diagnose common issues which stop DC/OS E2E...
              download-artifact  Download a DC/OS Open Source artifact.
              inspect            Show cluster details.
              list               List all clusters.
              run                Run an arbitrary command on a node.
              sync               Sync files from a DC/OS checkout to master...
              wait               Wait for DC/OS to start.
              web                Open the browser at the web UI.
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
              --genconf-dir PATH              Path to a directory that contains additional
                                              files for the DC/OS installer. All files from
                                              this directory will be copied to the "genconf"
                                              directory before running the DC/OS installer.
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
              -v, --verbose                   Use verbose output. Use this option multiple
                                              times for more verbose output.
              --enable-selinux-enforcing      With this flag set, SELinux is set to
                                              enforcing before DC/OS is installed on the
                                              cluster.
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
              -v, --verbose  Use verbose output. Use this option multiple times for more
                             verbose output.
              --help         Show this message and exit.
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


class TestInspect:
    """
    Tests for the `inspect` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant inspect --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['inspect', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant inspect [OPTIONS]

              Show cluster details.

            Options:
              -c, --cluster-id TEXT  The ID of the cluster to use.  [default: default]
              --help                 Show this message and exit.
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


class TestRun:
    """
    Tests for the ``run`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant run --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['run', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant run [OPTIONS] NODE_ARGS...

              Run an arbitrary command on a node.

              This command sets up the environment so that ``pytest`` can be run.

              For example, run ``dcos-vagrant run --cluster-id 1231599 pytest -k
              test_tls.py``.

              Or, with sync: ``dcos-vagrant run --sync-dir . --cluster-id 1231599 pytest
              -k test_tls.py``.

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
              --node TEXT              A reference to a particular node to run the command
                                       on. This can be one of: The node's IP address, the
                                       node's VM name, a reference in the format
                                       "<role>_<number>". These details be seen with ``dcos-
                                       vagrant inspect``.
              -v, --verbose            Use verbose output. Use this option multiple times
                                       for more verbose output.
              --help                   Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestSync:
    """
    Tests for the ``sync`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant sync --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_vagrant, ['sync', '--help'])
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant sync [OPTIONS] [DCOS_CHECKOUT_DIR]

              Sync files from a DC/OS checkout to master nodes.

              This syncs integration test files and bootstrap files.

              ``DCOS_CHECKOUT_DIR`` should be set to the path of clone of an open source
              DC/OS or DC/OS Enterprise repository.

              By default the ``DCOS_CHECKOUT_DIR`` argument is set to the value of the
              ``DCOS_CHECKOUT_DIR`` environment variable.

              If no ``DCOS_CHECKOUT_DIR`` is given, the current working directory is used.

            Options:
              -c, --cluster-id TEXT  The ID of the cluster to use.  [default: default]
              --help                 Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestDownloadArtifact:
    """
    Tests for the ``download-artifact`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-vagrant download-artifact --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_vagrant,
            ['download-artifact', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-vagrant download-artifact [OPTIONS]

              Download a DC/OS Open Source artifact.

              For DC/OS Enterprise release artifacts, contact your sales representative.

            Options:
              --dcos-version TEXT   The DC/OS Open Source artifact version to download. This
                                    can be in one of the following formats: ``stable``,
                                    ``testing/master``, ``testing/<DC/OS MAJOR RELEASE>``,
                                    ``stable/<DC/OS MINOR RELEASE>``,
                                    ``testing/pull/<GITHUB-PR-NUMBER>``.
                                    See
                                    https://dcos.io/releases/ for available releases.
                                    [default: stable]
              --download-path TEXT  The path to download a release artifact to.  [default:
                                    /tmp/dcos_generate_config.sh]
              --help                Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
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
              -v, --verbose              Use verbose output. Use this option multiple times
                                         for more verbose output.
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

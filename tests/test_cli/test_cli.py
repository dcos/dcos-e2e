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
        result = runner.invoke(dcos_docker, arguments)
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker [OPTIONS] COMMAND [ARGS]...

              Manage DC/OS clusters on Docker.

            Options:
              --help  Show this message and exit.

            Commands:
              create   Create a DC/OS cluster.
              destroy  Destroy clusters.
              inspect  Show cluster details.
              list     List all clusters.
              wait     If Enterprise, uses admin admin like the...
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
        result = runner.invoke(dcos_docker, ['create', '--help'])
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

                              * `superuser_username`
                              * `superuser_password_hash`
                              * `fault_domain_enabled`
                              * `license_key_contents`

                              These can all be set in `extra_config`.
                              However, some defaults are provided for all but the license key.

                              The default superuser username is `admin`.
                              The default superuser password is `admin`.
                              The default `fault_domain_enabled` is `false`.

                              `license_key_contents` must be set for DC/OS Enterprise 1.11 and above.
                              This is set to one of the following, in order:

                              * The `license_key_contents` set in `extra_config`.
                              * The contents of the path given with `--license-key-path`.
                              * The contents of the path set in the `DCOS_LICENSE_KEY_PATH` environment variable.

                              If none of these are set, `license_key_contents` is not given.

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
              --cluster-id TEXT               A unique identifier for the cluster. Defaults
                                              to a random value.
              --license-key-path PATH         This is ignored if using open source DC/OS. If
                                              using DC/OS Enterprise, this defaults to the
                                              value of the `DCOS_LICENSE_KEY_PATH`
                                              environment variable.
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
        result = runner.invoke(dcos_docker, ['create', '/not/a/path'])
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

    def test_empty_cluster_name(self, oss_artifact: Path) -> None:
        """
        XXX
        """

    def test_invalid_cluster_name(self, oss_artifact: Path) -> None:
        """
        XXX
        """


class TestDestroy:
    """
    Tests for the `destroy` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos_docker destroy --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['destroy', '--help'])
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker destroy [OPTIONS] [CLUSTER_IDS]...

              Destroy clusters.

              This takes >= 1 cluster IDs. To destroy all clusters, run:

              dcos_docker destroy $(dcos_docker list)

            Options:
              --help  Show this message and exit.
            """
        )
        assert result.output == expected_help

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['destroy', unique])
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
        result = runner.invoke(dcos_docker, ['destroy', unique, unique_2])
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
        result = runner.invoke(dcos_docker, ['list', '--help'])
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
        result = runner.invoke(dcos_docker, ['inspect', '--help'])
        assert result.exit_code == 0
        expected_help = dedent(
            """\
            Usage: dcos_docker inspect [OPTIONS] CLUSTER_ID

              Show cluster details.

            Options:
              --env   Show details in an environment variable format to eval.
              --help  Show this message and exit.
            """
        )
        assert result.output == expected_help

    def test_cluster_does_not_exist(self) -> None:
        """
        An error is shown if the given cluster does not exist.
        """
        unique = uuid.uuid4().hex
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['inspect', unique])
        assert result.exit_code == 2
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output

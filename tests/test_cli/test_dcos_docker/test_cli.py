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

import os
import uuid
from pathlib import Path
from tempfile import mkstemp
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
    Tests for the top level `dcos-docker` command.
    """

    def test_version(self) -> None:
        """
        The CLI version is shown with ``dcos-docker --version``.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['--version'],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        expected = 'dcos-docker, version'
        assert expected in result.output

    @pytest.mark.parametrize('arguments', [
        [],
        ['--help'],
    ])
    def test_help(self, arguments: List[str]) -> None:
        """
        Help test is shown with `dcos-docker` and `dcos-docker --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, arguments, catch_exceptions=False)
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker [OPTIONS] COMMAND [ARGS]...

              Manage DC/OS clusters on Docker.

            Options:
              --version  Show the version and exit.
              --help     Show this message and exit.

            Commands:
              create               Create a DC/OS cluster.
              destroy              Destroy a cluster.
              destroy-list         Destroy clusters.
              destroy-mac-network  Destroy containers created by "dcos-docker...
              doctor               Diagnose common issues which stop DC/OS E2E...
              download-artifact    Download a DC/OS Open Source artifact.
              inspect              Show cluster details.
              list                 List all clusters.
              run                  Run an arbitrary command on a node.
              setup-mac-network    Set up a network to connect to nodes on...
              sync                 Sync files from a DC/OS checkout to master...
              wait                 Wait for DC/OS to start.
              web                  Open the browser at the web UI.
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
        Help text is shown with `dcos-docker create --help`.
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

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
              --docker-version [1.11.2|1.13.1|17.12.1-ce]
                                              The Docker version to install on the nodes.
                                              [default: 1.13.1]
              --linux-distribution [centos-7|coreos|ubuntu-16.04]
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
              --extra-config PATH             The path to a file including DC/OS
                                              configuration YAML. The contents of this file
                                              will be added to add to a default
                                              configuration.
              --security-mode [disabled|permissive|strict]
                                              The security mode to use for a DC/OS
                                              Enterprise cluster. This overrides any
                                              security mode set in ``--extra-config``.
              -c, --cluster-id TEXT           A unique identifier for the cluster. Use the
                                              value "default" to use this cluster for other
                                              commands without specifying --cluster-id.
              --license-key PATH              This is ignored if using open source DC/OS. If
                                              using DC/OS Enterprise, this defaults to the
                                              value of the `DCOS_LICENSE_KEY_PATH`
                                              environment variable.
              --genconf-dir PATH              Path to a directory that contains additional
                                              files for DC/OS installer. All files from this
                                              directory will be copied to the `genconf`
                                              directory before running DC/OS installer.
              --copy-to-master TEXT           Files to copy to master nodes before
                                              installing DC/OS. This option can be given
                                              multiple times. Each option should be in the
                                              format /absolute/local/path:/remote/path.
              --workspace-dir PATH            Creating a cluster can use approximately 2 GB
                                              of temporary storage. Set this option to use a
                                              custom "workspace" for this temporary storage.
                                              See https://docs.python.org/3/library/tempfile
                                              .html#tempfile.gettempdir for details on the
                                              temporary directory location if this option is
                                              not set.
              --custom-volume TEXT            Bind mount a volume on all cluster node
                                              containers. See https://docs.docker.com/engine
                                              /reference/run/#volume-shared-filesystems for
                                              the syntax to use.
              --custom-master-volume TEXT     Bind mount a volume on all cluster master node
                                              containers. See https://docs.docker.com/engine
                                              /reference/run/#volume-shared-filesystems for
                                              the syntax to use.
              --custom-agent-volume TEXT      Bind mount a volume on all cluster agent node
                                              containers. See https://docs.docker.com/engine
                                              /reference/run/#volume-shared-filesystems for
                                              the syntax to use.
              --custom-public-agent-volume TEXT
                                              Bind mount a volume on all cluster public
                                              agent node containers. See https://docs.docker
                                              .com/engine/reference/run/#volume-shared-
                                              filesystems for the syntax to use.
              --variant [auto|oss|enterprise]
                                              Choose the DC/OS variant. If the variant does
                                              not match the variant of the given artifact,
                                              an error will occur. Using "auto" finds the
                                              variant from the artifact. Finding the variant
                                              from the artifact takes some time and so using
                                              another option is a performance optimization.
              --wait-for-dcos                 Wait for DC/OS after creating the cluster.
                                              This is equivalent to using "dcos-docker wait"
                                              after this command. "dcos-docker wait" has
                                              various options available and so may be more
                                              appropriate for your use case. If the chosen
                                              transport is "docker-exec", this will skip
                                              HTTP checks and so the cluster may not be
                                              fully ready.
              --network TEXT                  The Docker network containers will be
                                              connected to.It may not be possible to SSH to
                                              containers on a custom network on macOS.
              --transport [docker-exec|ssh]   The communication transport to use. On macOS
                                              the SSH transport requires IP routing to be
                                              set up. See "dcos-docker setup-mac-network".It
                                              also requires the "ssh" command to be
                                              available. This can be provided by setting the
                                              `DCOS_DOCKER_TRANSPORT` environment variable.
                                              [default: docker-exec]
              --one-master-host-port-map TEXT
                                              Publish a container port of one master node to
                                              the host. Only Transmission Control Protocol
                                              is supported currently. The syntax is
                                              <HOST_PORT>:<CONTAINER_PORT>
              -v, --verbose                   Use verbose output. Use this option multiple
                                              times for more verbose output.
              --help                          Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

    def test_copy_to_master_bad_format(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        An error is shown if ``--copy-to-master`` is given a value in an
        invalid format.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

            Error: Invalid value for "--copy-to-master": "/some/path" is not in the format /absolute/local/path:/remote/path.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

    def test_copy_to_master_no_local(self, oss_artifact: Path) -> None:
        """
        An error is shown if the given local path does not exist.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

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
        oss_artifact: Path,
        option: str,
    ) -> None:
        """
        Given volumes must have the mode "rw" or "ro", or no mode.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

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
        oss_artifact: Path,
        option: str,
    ) -> None:
        """
        Given volumes must have 0, 1 or 2 colons.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

            Error: Invalid value for "{option}": "/opt:/opt:/opt:rw" is not a valid volume definition. See https://docs.docker.com/engine/reference/run/#volume-shared-filesystems for the syntax to use.
            """,# noqa: E501,E261
        ).format(option=option)
        # yapf: enable
        assert result.output == expected_message

    def test_copy_to_master_relative(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        An error is shown if the given local path is not an absolute path.
        """
        _, temporary_file_path = mkstemp(dir='.')
        relative_path = Path(temporary_file_path).relative_to(os.getcwd())

        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

            Error: Invalid value for "--copy-to-master": "some/remote is not an absolute path.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

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

    def test_config_does_not_exist(self, oss_artifact: Path) -> None:
        """
        An error is shown if the ``--extra-config`` file does not exist.
        """
        runner = CliRunner()
        invalid_path = '/' + uuid.uuid4().hex
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

            Error: Invalid value for "--extra-config": Path "{path}" does not exist.
            """,# noqa: E501,E261
        ).format(path=invalid_path)
        # yapf: enable
        assert result.output == expected_message

    def test_invalid_yaml(self, oss_artifact: Path, tmpdir: local) -> None:
        """
        An error is shown if invalid YAML is given in the file given to
        ``--extra-config``.
        """
        invalid_file = tmpdir.join(uuid.uuid4().hex)
        invalid_file.write('@')
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
           Usage: dcos-docker create [OPTIONS] ARTIFACT

           Error: Invalid value for "--extra-config": "@" is not valid YAML
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_message

    def test_not_key_value(self, oss_artifact: Path, tmpdir: local) -> None:
        """
        An error is shown if YAML is given for ``--extra-config`` which is not
        a key-value mapping.
        """
        invalid_file = tmpdir.join(uuid.uuid4().hex)
        invalid_file.write('example')
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
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
           Usage: dcos-docker create [OPTIONS] ARTIFACT

           Error: Invalid value for "--extra-config": "example" is not a valid DC/OS configuration
            """,# noqa: E501,E261
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
            Usage: dcos-docker create [OPTIONS] ARTIFACT

            Error: Invalid value for "-c" / "--cluster-id": Invalid cluster id "{cluster_id}", only [a-zA-Z0-9][a-zA-Z0-9_.-] are allowed and the cluster ID cannot be empty.
            """,# noqa: E501,E261
        ).format(cluster_id=invalid_id)
        # yapf: enable
        assert result.output == expected_message

    def test_genconf_path_not_exist(self, oss_artifact: Path) -> None:
        """
        Genconf path must exist.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--genconf-dir',
                'non-existing',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--genconf-dir": '
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
        genconf_file = tmpdir.join('testfile')
        genconf_file.write('test')

        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--genconf-dir',
                str(genconf_file),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--genconf-dir": '
            '"{path}" is not a directory.'
        ).format(path=str(genconf_file))
        assert expected_error in result.output

    def test_workdir_path_not_exist(self, oss_artifact: Path) -> None:
        """
        ``--workspace-dir`` must exist.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--workspace-dir',
                'non-existing',
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--workspace-dir": '
            'Path "non-existing" does not exist.'
        )
        assert expected_error in result.output

    def test_workspace_path_is_file(
        self,
        oss_artifact: Path,
        tmpdir: local,
    ) -> None:
        """
        ``--workspace-dir`` must be a directory.
        """
        workspace_file = tmpdir.join('testfile')
        workspace_file.write('test')

        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
                'create',
                str(oss_artifact),
                '--workspace-dir',
                str(workspace_file),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 2
        expected_error = (
            'Error: Invalid value for "--workspace-dir": '
            '"{path}" is not a directory.'
        ).format(path=str(workspace_file))
        assert expected_error in result.output


class TestDestroy:
    """
    Tests for the `destroy` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker destroy --help`.
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
            Usage: dcos-docker destroy [OPTIONS]

              Destroy a cluster.

            Options:
              -c, --cluster-id TEXT          The ID of the cluster to use.  [default:
                                             default]
              --transport [docker-exec|ssh]  The communication transport to use. On macOS
                                             the SSH transport requires IP routing to be set
                                             up. See "dcos-docker setup-mac-network".It also
                                             requires the "ssh" command to be available.
                                             This can be provided by setting the
                                             `DCOS_DOCKER_TRANSPORT` environment variable.
                                             [default: docker-exec]
              --help                         Show this message and exit.
            """,# noqa: E501,E261
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
            ['destroy', '--cluster-id', unique],
        )
        assert result.exit_code == 2
        expected_error = 'Cluster "{unique}" does not exist'
        expected_error = expected_error.format(unique=unique)
        assert expected_error in result.output


class TestDestroyList:
    """
    Tests for the `destroy-list` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker destroy --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['destroy-list', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker destroy-list [OPTIONS] [CLUSTER_IDS]...

              Destroy clusters.

              To destroy all clusters, run ``dcos-docker destroy $(dcos-docker list)``.

            Options:
              --transport [docker-exec|ssh]  The communication transport to use. On macOS
                                             the SSH transport requires IP routing to be set
                                             up. See "dcos-docker setup-mac-network".It also
                                             requires the "ssh" command to be available.
                                             This can be provided by setting the
                                             `DCOS_DOCKER_TRANSPORT` environment variable.
                                             [default: docker-exec]
              --help                         Show this message and exit.
            """,# noqa: E501,E261
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
            ['destroy-list', unique],
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
            ['destroy-list', unique, unique_2],
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
        Help text is shown with `dcos-docker list --help`.
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
            Usage: dcos-docker list [OPTIONS]

              List all clusters.

            Options:
              --help  Show this message and exit.
            """,
        )
        assert result.output == expected_help


class TestInspect:
    """
    Tests for the `inspect` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker inspect --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['inspect', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker inspect [OPTIONS]

              Show cluster details.

              To quickly get environment variables to use with Docker tooling, use the
              ``--env`` flag.

              Run ``eval $(dcos-docker inspect <CLUSTER_ID> --env)``, then run ``docker
              exec -it $MASTER_0`` to enter the first master, for example.

            Options:
              -c, --cluster-id TEXT  The ID of the cluster to use.  [default: default]
              --env                  Show details in an environment variable format to eval.
              --help                 Show this message and exit.
            """,# noqa: E501,E261
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
        Help text is shown with `dcos-docker wait --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['wait', '--help'])
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker wait [OPTIONS]

              Wait for DC/OS to start.

            Options:
              -c, --cluster-id TEXT          The ID of the cluster to use.  [default:
                                             default]
              --superuser-username TEXT      The superuser username is needed only on DC/OS
                                             Enterprise clusters. By default, on a DC/OS
                                             Enterprise cluster, `admin` is used.
              --superuser-password TEXT      The superuser password is needed only on DC/OS
                                             Enterprise clusters. By default, on a DC/OS
                                             Enterprise cluster, `admin` is used.
              --skip-http-checks             Do not wait for checks which require an HTTP
                                             connection to the cluster. If this flag is
                                             used, this command may return before DC/OS is
                                             fully ready. Use this flag in cases where an
                                             HTTP connection cannot be made to the cluster.
                                             For example this is useful on macOS without a
                                             VPN set up.
              --transport [docker-exec|ssh]  The communication transport to use. On macOS
                                             the SSH transport requires IP routing to be set
                                             up. See "dcos-docker setup-mac-network".It also
                                             requires the "ssh" command to be available.
                                             This can be provided by setting the
                                             `DCOS_DOCKER_TRANSPORT` environment variable.
                                             [default: docker-exec]
              -v, --verbose                  Use verbose output. Use this option multiple
                                             times for more verbose output.
              --help                         Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
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
        Help text is shown with `dcos-docker sync --help`.
        """
        runner = CliRunner()
        result = runner.invoke(dcos_docker, ['sync', '--help'])
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker sync [OPTIONS] [DCOS_CHECKOUT_DIR]

              Sync files from a DC/OS checkout to master nodes.

              This syncs integration test files and bootstrap files.

              ``DCOS_CHECKOUT_DIR`` should be set to the path of clone of an open source
              DC/OS or DC/OS Enterprise repository.

              By default the ``DCOS_CHECKOUT_DIR`` argument is set to the value of the
              ``DCOS_CHECKOUT_DIR`` environment variable.

              If no ``DCOS_CHECKOUT_DIR`` is given, the current working directory is used.

            Options:
              -c, --cluster-id TEXT          The ID of the cluster to use.  [default:
                                             default]
              --transport [docker-exec|ssh]  The communication transport to use. On macOS
                                             the SSH transport requires IP routing to be set
                                             up. See "dcos-docker setup-mac-network".It also
                                             requires the "ssh" command to be available.
                                             This can be provided by setting the
                                             `DCOS_DOCKER_TRANSPORT` environment variable.
                                             [default: docker-exec]
              --help                         Show this message and exit.
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
        Help text is shown with `dcos-docker doctor --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['doctor', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker doctor [OPTIONS]

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
        result = runner.invoke(dcos_docker, ['doctor'], catch_exceptions=False)
        assert result.exit_code == 0


class TestDownloadArtifact:
    """
    Tests for the ``download-artifact`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker download-artifact --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['download-artifact', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker download-artifact [OPTIONS]

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


class TestWeb:
    """
    Tests for the ``web`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker web --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['web', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker web [OPTIONS]

              Open the browser at the web UI.

              Note that the web UI may not be available at first. Consider using ``dcos-
              docker wait`` before running this command.

            Options:
              -c, --cluster-id TEXT  The ID of the cluster to use.  [default: default]
              --help                 Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestSetupMacNetwork():
    """
    Tests for the ``setup-mac-network`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker setup-mac-network --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['setup-mac-network', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker setup-mac-network [OPTIONS]

              Set up a network to connect to nodes on macOS.

              This creates an OpenVPN configuration file and describes how to use it.

            Options:
              --force                   Overwrite any files and destroy conflicting
                                        containers from previous uses of this command.
              --configuration-dst PATH  The location to create an OpenVPN configuration
                                        file.  [default: ~/Documents/docker-for-mac.ovpn]
              --help                    Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

    def test_suffix_not_ovpn(self, tmpdir: local) -> None:
        """
        If a configuration file does not have the 'ovpn' suffix, an error is
        shown.
        """
        configuration_file = tmpdir.join('example.txt')
        configuration_file.write('example')
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
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
            Usage: dcos-docker setup-mac-network [OPTIONS]

            Error: Invalid value for "--configuration-dst": "{value}" does not have the suffix ".ovpn".
            """,# noqa: E501,E261
        ).format(
            value=str(configuration_file),
        )
        # yapf: enable
        assert result.exit_code == 2
        assert result.output == expected_error

    def test_configuration_already_exists(self, tmpdir: local) -> None:
        """
        If a configuration file already exists at the given location, an error
        is shown.
        """
        configuration_file = tmpdir.join('example.ovpn')
        configuration_file.write('example')
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            [
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
            Usage: dcos-docker setup-mac-network [OPTIONS]

            Error: Invalid value for "--configuration-dst": "{value}" already exists so no new OpenVPN configuration was created.

            To use {value}:
            1. Install an OpenVPN client such as Tunnelblick (https://tunnelblick.net/downloads.html) or Shimo (https://www.shimovpn.com).
            2. Run "open {value}".
            3. In your OpenVPN client, connect to the new "example" profile.
            4. Run "dcos-docker doctor" to confirm that everything is working.
            """,# noqa: E501,E261
        ).format(
            value=str(configuration_file),
        )
        # yapf: enable
        assert result.exit_code == 2
        assert result.output == expected_error


class TestDestroyMacNetwork():
    """
    Tests for the ``destroy-mac-network`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker destroy-mac-network --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['destroy-mac-network', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker destroy-mac-network [OPTIONS]

              Destroy containers created by "dcos-docker setup-mac-network".

            Options:
              --help  Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help


class TestRun:
    """
    Tests for the ``run`` subcommand.
    """

    def test_help(self) -> None:
        """
        Help text is shown with `dcos-docker run --help`.
        """
        runner = CliRunner()
        result = runner.invoke(
            dcos_docker,
            ['run', '--help'],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # yapf breaks multi-line noqa, see
        # https://github.com/google/yapf/issues/524.
        # yapf: disable
        expected_help = dedent(
            """\
            Usage: dcos-docker run [OPTIONS] NODE_ARGS...

              Run an arbitrary command on a node.

              This command sets up the environment so that ``pytest`` can be run.

              For example, run ``dcos-docker run --cluster-id 1231599 pytest -k
              test_tls.py``.

              Or, with sync: ``dcos-docker run --sync-dir . --cluster-id 1231599 pytest -k
              test_tls.py``.

              To use special characters such as single quotes in your command, wrap the
              whole command in double quotes.

            Options:
              -c, --cluster-id TEXT          The ID of the cluster to use.  [default:
                                             default]
              --dcos-login-uname TEXT        The username to set the ``DCOS_LOGIN_UNAME``
                                             environment variable to.
              --dcos-login-pw TEXT           The password to set the ``DCOS_LOGIN_PW``
                                             environment variable to.
              --sync-dir PATH                The path to a DC/OS checkout. Part of this
                                             checkout will be synced to all master nodes
                                             before the command is run.
              --no-test-env                  With this flag set, no environment variables
                                             are set and the command is run in the home
                                             directory.
              --node TEXT                    A reference to a particular node to run the
                                             command on. This can be one of: The node's IP
                                             address, the node's Docker container name, the
                                             node's Docker container ID, a reference in the
                                             format "<role>_<number>". These details be seen
                                             with ``dcos_docker inspect``.
              --env TEXT                     Set environment variables in the format
                                             "<KEY>=<VALUE>"
              --transport [docker-exec|ssh]  The communication transport to use. On macOS
                                             the SSH transport requires IP routing to be set
                                             up. See "dcos-docker setup-mac-network".It also
                                             requires the "ssh" command to be available.
                                             This can be provided by setting the
                                             `DCOS_DOCKER_TRANSPORT` environment variable.
                                             [default: docker-exec]
              --help                         Show this message and exit.
            """,# noqa: E501,E261
        )
        # yapf: enable
        assert result.output == expected_help

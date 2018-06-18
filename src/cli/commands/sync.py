"""
Tools for syncing code to a node.
"""

import tempfile
from pathlib import Path

import click

from dcos_e2e.node import Transport

from ._options import existing_cluster_id_option, node_transport_option


@dcos_docker.command('sync')
@existing_cluster_id_option
@click.argument(
    'dcos_checkout_dir',
    type=click.Path(exists=True),
    envvar='DCOS_CHECKOUT_DIR',
    default='.',
)
@node_transport_option
def sync_code(
    cluster_id: str,
    dcos_checkout_dir: str,
    transport: Transport,
) -> None:
    """
    Sync files from a DC/OS checkout to master nodes.

    This syncs integration test files and bootstrap files.

    ``DCOS_CHECKOUT_DIR`` should be set to the path of clone of an open source
    DC/OS or DC/OS Enterprise repository.

    By default the ``DCOS_CHECKOUT_DIR`` argument is set to the value of the
    ``DCOS_CHECKOUT_DIR`` environment variable.

    If no ``DCOS_CHECKOUT_DIR`` is given, the current working directory is
    used.
    """

    # This is not covered by automated tests, and it is non-trivial.
    #
    # In the following instructions, running a test might look like:
    #
    # `dcos-docker run pytest <test_filename>`
    #
    # The manual test cases we want to work are:
    # * Sync a DC/OS Enterprise checkout and run a test - it should work.
    # * Delete a test file, sync, try to run this test file - it should fail
    #   with "file not found".
    # * Add a test file, sync, try to run this test file - it should work.
    # * Add `assert False`, sync, to a test file and run this test file - it
    #   should fail.
    # * Test bootstrap sync with no changes (a partial test that nothing
    #   breaks):
    #   - Sync
    #   - `dcos-docker run systemctl restart dcos-mesos-master`
    #   - `dcos-docker run journalctl -f -u dcos-mesos-master`
    #   - We expect to see no assertion error.
    # * Test bootstrap sync with some changes
    #   - Add `assert False` to
    #     `packages/bootstrap/extra/dcos_internal_utils/bootstrap.py`
    #   - `dcos-docker run systemctl restart dcos-mesos-master`
    #   - `dcos-docker run journalctl -f -u dcos-mesos-master`
    #   - We expect to see the assertion error.

    local_packages = Path(dcos_checkout_dir) / 'packages'
    local_test_dir = local_packages / 'dcos-integration-test' / 'extra'
    if not Path(local_test_dir).exists():
        message = (
            'DCOS_CHECKOUT_DIR must be set to the checkout of a DC/OS '
            'repository.\n'
            '"{local_test_dir}" does not exist.'
        ).format(local_test_dir=local_test_dir)
        raise click.BadArgumentUsage(message=message)

    cluster_containers = ClusterContainers(
        cluster_id=cluster_id,
        transport=transport,
    )
    cluster = cluster_containers.cluster
    node_active_dir = Path('/opt/mesosphere/active')
    node_test_dir = node_active_dir / 'dcos-integration-test'
    node_lib_dir = node_active_dir / 'bootstrap' / 'lib'
    # Different versions of DC/OS have different versions of Python.
    master = next(iter(cluster.masters))
    ls_result = master.run(args=['ls', str(node_lib_dir)])
    python_version = ls_result.stdout.decode().strip()
    node_python_dir = node_lib_dir / python_version
    node_bootstrap_dir = (
        node_python_dir / 'site-packages' / 'dcos_internal_utils'
    )

    local_bootstrap_dir = (
        local_packages / 'bootstrap' / 'extra' / 'dcos_internal_utils'
    )

    test_tarstream = _tar_with_filter(
        path=local_test_dir,
        tar_filter=_cache_filter,
    )
    bootstrap_tarstream = _tar_with_filter(
        path=local_bootstrap_dir,
        tar_filter=_cache_filter,
    )

    node_test_py_pattern = node_test_dir / '*.py'
    tar_path = '/tmp/dcos_e2e_tmp.tar'
    for master in cluster.masters:
        master.run(
            args=['rm', '-rf', str(node_test_py_pattern)],
            # We use a wildcard character, `*`, so we need shell expansion.
            shell=True,
        )

        for tarstream, node_destination in (
            (test_tarstream, node_test_dir),
            (bootstrap_tarstream, node_bootstrap_dir),
        ):

            with tempfile.NamedTemporaryFile() as tmp_file:
                tmp_file.write(tarstream.getvalue())
                tmp_file.flush()

                master.send_file(
                    local_path=Path(tmp_file.name),
                    remote_path=Path(tar_path),
                )

            tar_args = ['tar', '-C', str(node_destination), '-xvf', tar_path]
            master.run(args=tar_args)
            master.run(args=['rm', tar_path])

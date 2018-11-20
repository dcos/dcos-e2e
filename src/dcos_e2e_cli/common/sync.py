"""
Tools for syncing code to a cluster.
"""

import io
import tarfile
import tempfile
from pathlib import Path
from typing import Callable, Optional

import click

from dcos_e2e.cluster import Cluster
from dcos_e2e.node import Node


def _tar_with_filter(
    path: Path,
    tar_filter: Callable[[tarfile.TarInfo], Optional[tarfile.TarInfo]],
) -> io.BytesIO:
    """
    Return a tar of a files in a given directory, which are not filtered out
    by the ``filter``.
    """
    tarstream = io.BytesIO()
    with tarfile.TarFile(fileobj=tarstream, mode='w') as tar:
        tar.add(name=str(path), arcname='/', filter=tar_filter)
    tarstream.seek(0)

    return tarstream


def _cache_filter(tar_info: tarfile.TarInfo) -> Optional[tarfile.TarInfo]:
    """
    Filter for ``tarfile.TarFile.add`` which removes Python and pytest cache
    files.
    """
    if '__pycache__' in tar_info.name:
        return None
    if tar_info.name.endswith('.pyc'):
        return None
    return tar_info


def _send_tarstream_to_node_and_extract(
    tarstream: io.BytesIO,
    node: Node,
    remote_path: Path,
) -> None:
    """
    Given a tarstream, send the contents to a remote path.
    """
    tar_path = Path('/tmp/dcos_e2e_tmp.tar')
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(tarstream.getvalue())
        tmp_file.flush()

        node.send_file(
            local_path=Path(tmp_file.name),
            remote_path=tar_path,
        )

    tar_args = ['tar', '-c', str(remote_path), '-xvf', str(tar_path)]
    node.run(args=tar_args)
    node.run(args=['rm', str(tar_path)])


def _sync_bootstrap_to_masters(
    cluster: Cluster,
    dcos_checkout_dir: Path,
) -> None:
    """
    Sync bootstrap code to all masters in a cluster.
    """
    local_packages = dcos_checkout_dir / 'packages'
    local_bootstrap_dir = (
        local_packages / 'bootstrap' / 'extra' / 'dcos_internal_utils'
    )
    node_lib_dir = Path('/opt/mesosphere/active/bootstrap/lib')
    # Different versions of DC/OS have different versions of Python.
    master = next(iter(cluster.masters))
    ls_result = master.run(args=['ls', str(node_lib_dir)])
    python_version = ls_result.stdout.decode().strip()
    node_python_dir = node_lib_dir / python_version
    node_bootstrap_dir = (
        node_python_dir / 'site-packages' / 'dcos_internal_utils'
    )
    bootstrap_tarstream = _tar_with_filter(
        path=local_bootstrap_dir,
        tar_filter=_cache_filter,
    )

    for master in cluster.masters:
        _send_tarstream_to_node_and_extract(
            tarstream=bootstrap_tarstream,
            node=master,
            remote_path=node_bootstrap_dir,
        )


def sync_code_to_masters(cluster: Cluster, dcos_checkout_dir: Path) -> None:
    """
    Sync files from a DC/OS checkout to master nodes.

    This syncs integration test files and bootstrap files.

    This is not covered by automated tests, and it is non-trivial.

    In the following instructions, running a test might look like:

    `minidcos docker run --test-env pytest <test_filename>`

    The manual test cases we want to work are:
    * Sync a DC/OS Enterprise checkout and run a test - it should work.
    * Delete a test file, sync, try to run this test file - it should fail
      with "file not found".
    * Add a test file, sync, try to run this test file - it should work.
    * Add `assert False`, sync, to a test file and run this test file - it
      should fail.
    * Test bootstrap sync with no changes (a partial test that nothing
      breaks):
      - Sync
      - `minidcos docker run systemctl restart dcos-mesos-master`
      - `minidcos docker run journalctl -f -u dcos-mesos-master`
      - We expect to see no assertion error.
    * Test bootstrap sync with some changes
      - Add `assert False` to
        `packages/bootstrap/extra/dcos_internal_utils/bootstrap.py`
      - `minidcos docker run systemctl restart dcos-mesos-master`
      - `minidcos docker run journalctl -f -u dcos-mesos-master`
      - We expect to see the assertion error.

    Args:
        cluster: The cluster to sync code to.
        dcos_checkout_dir: The path to a DC/OS (Enterprise) checkout to sync
            code from.
    """
    local_packages = dcos_checkout_dir / 'packages'
    local_test_dir = local_packages / 'dcos-integration-test' / 'extra'
    if not Path(local_test_dir).exists():
        message = (
            'DCOS_CHECKOUT_DIR must be set to the checkout of a DC/OS '
            'repository.\n'
            '"{local_test_dir}" does not exist.'
        ).format(local_test_dir=local_test_dir)
        raise click.BadArgumentUsage(message=message)

    _sync_bootstrap_to_masters(
        cluster=cluster,
        dcos_checkout_dir=dcos_checkout_dir,
    )

    # checkout_directory_variant
    # cluster_variant

    # If cluster is EE and checkout is OSS:
    #   * Delete util directory in node_test_dir
    #   * Move tarred tests to node_test_dir / open_source_tests
    #   * Delete open_source_tests/conftest.py
    #   * Move open_source_tests/util one level up

    # If cluster is OSS and checkout is EE:
    #   * Error

    test_tarstream = _tar_with_filter(
        path=local_test_dir,
        tar_filter=_cache_filter,
    )

    # * Tell people "delete conftest.py"
    # * If you're using DC/OS enterprise, sync takes a DC/OS Enterprise repo
    #   and optionally a DC/OS OSS
    # * If enterprise cluster and enterprise checkout dir, sync only EE code
    #    AND if enterprise cluster and OSS checkout dir, sync OSS code to the right place

    # run --sync-dir
    # OSS:
    #   minidcos docker run --sync-dir .
    # EE:
    #   minidcos docker run --sync-dir /path/to/ee --sync-dir /path/to/oss run

    # On the cluster already:
    # test_foo.py
    # open_source_tests/test_bar.py

    # sync enterprise
    # local enterprise checkout has a open_source_tests/


    node_active_dir = Path('/opt/mesosphere/active')
    node_test_dir = node_active_dir / 'dcos-integration-test'
    for master in cluster.masters:
        master.run(
            args=['rm', '-rf', str(node_test_dir / '*.py')],
            # We use a wildcard character, `*`, so we need shell expansion.
            shell=True,
        )

        _send_tarstream_to_node_and_extract(
            tarstream=test_tarstream,
            node=master,
            remote_path=Path('/opt/mesosphere/active/dcos-integration-test'),
        )

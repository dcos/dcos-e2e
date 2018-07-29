"""
Run tests and linters on Travis CI.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple  # noqa: F401

import click
import pytest
import requests

OSS_PATTERN = (
    'https://downloads.dcos.io/dcos/testing/{version}/dcos_generate_config.sh'
)
OSS_MASTER_ARTIFACT_URL = OSS_PATTERN.format(version='master')
OSS_1_9_ARTIFACT_URL = OSS_PATTERN.format(version='1.9')
OSS_1_10_ARTIFACT_URL = OSS_PATTERN.format(version='1.10')
OSS_1_11_ARTIFACT_URL = OSS_PATTERN.format(version='1.11')

EE_MASTER_ARTIFACT_URL = os.environ.get('EE_MASTER_ARTIFACT_URL')
EE_1_9_ARTIFACT_URL = os.environ.get('EE_1_9_ARTIFACT_URL')
EE_1_10_ARTIFACT_URL = os.environ.get('EE_1_10_ARTIFACT_URL')
EE_1_11_ARTIFACT_URL = os.environ.get('EE_1_11_ARTIFACT_URL')

OSS_MASTER_ARTIFACT_PATH = Path('/tmp/dcos_generate_config.sh')
OSS_1_9_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_9.sh')
OSS_1_10_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_10.sh')
OSS_1_11_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_11.sh')

EE_MASTER_ARTIFACT_PATH = Path('/tmp/dcos_generate_config.ee.sh')
EE_1_9_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_9.ee.sh')
EE_1_10_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_10.ee.sh')
EE_1_11_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_11.ee.sh')

OSS_MASTER = (OSS_MASTER_ARTIFACT_URL, OSS_MASTER_ARTIFACT_PATH)
OSS_1_9 = (OSS_1_9_ARTIFACT_URL, OSS_1_9_ARTIFACT_PATH)
OSS_1_10 = (OSS_1_10_ARTIFACT_URL, OSS_1_10_ARTIFACT_PATH)
OSS_1_11 = (OSS_1_11_ARTIFACT_URL, OSS_1_11_ARTIFACT_PATH)
EE_MASTER = (EE_MASTER_ARTIFACT_URL, EE_MASTER_ARTIFACT_PATH)
EE_1_9 = (EE_1_9_ARTIFACT_URL, EE_1_9_ARTIFACT_PATH)
EE_1_10 = (EE_1_10_ARTIFACT_URL, EE_1_10_ARTIFACT_PATH)
EE_1_11 = (EE_1_11_ARTIFACT_URL, EE_1_11_ARTIFACT_PATH)

ALL_ARTIFACTS = (
    OSS_MASTER,
    OSS_1_9,
    OSS_1_10,
    OSS_1_11,
    EE_MASTER,
    EE_1_9,
    EE_1_10,
    EE_1_11,
)

PATTERNS = {
    'tests/test_cli':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestDefaults':
    (),
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestRunIntegrationTest':
    (),
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestUnsupported':
    (),
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestCustomKeyPair':
    (),
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestDCOSInstallation::test_install_dcos_from_path':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestDCOSInstallation::test_install_dcos_from_node':  # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestDCOSInstallation::test_install_dcos_with_custom_genconf':  # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestCentos7':
    (),
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestCoreOS::test_enterprise':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestCoreOS::test_oss':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestUbuntu1604::test_oss':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestUbuntu1604::test_enterprise':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/backends/docker/test_docker.py':
    (),
    'tests/test_dcos_e2e/backends/vagrant':
    (),
    'tests/test_dcos_e2e/test_cluster.py::TestClusterFromNodes':
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestClusterSize':
    (),
    'tests/test_dcos_e2e/test_cluster.py::TestCopyFiles::test_install_cluster_from_path':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestCopyFiles::test_install_cluster_from_url':  # noqa: E501
    (),
    'tests/test_dcos_e2e/test_cluster.py::TestInstallDcosFromPathLogging':
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestIntegrationTests':
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestMultipleClusters':
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestDestroyNode':
    (),
    'tests/test_dcos_e2e/test_enterprise.py::TestCopyFiles::test_copy_directory_to_installer':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestCopyFiles::test_copy_files_to_installer':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestCopyFiles::test_copy_directory_to_node_installer_genconf_dir':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestEnterpriseIntegrationTests':
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestSSLDisabled':
    (EE_1_11, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestWaitForDCOS':
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_legacy.py::Test110::test_enterprise':
    (EE_1_10, ),
    'tests/test_dcos_e2e/test_legacy.py::Test110::test_oss':
    (OSS_1_10, ),
    'tests/test_dcos_e2e/test_legacy.py::Test111::test_enterprise':
    (EE_1_11, ),
    'tests/test_dcos_e2e/test_legacy.py::Test111::test_oss':
    (OSS_1_11, ),
    'tests/test_dcos_e2e/test_legacy.py::Test19::test_enterprise':
    (EE_1_9, ),
    'tests/test_dcos_e2e/test_legacy.py::Test19::test_oss':
    (OSS_1_9, ),
    'tests/test_dcos_e2e/test_node.py':
    (),
    'tests/test_dcos_e2e/test_node_install.py::TestAdvancedInstallationMethod::test_install_dcos_from_url':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_node_install.py::TestAdvancedInstallationMethod::test_install_dcos_from_path':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_node_install.py::TestCopyFiles::test_install_from_path_with_genconf_files':  # noqa: E501
    (OSS_MASTER, ),
}  # type: Dict[str, Tuple]


def _download_file(url: str, path: Path) -> None:
    """
    Download a file to a given path.
    """
    label = 'Downloading to ' + str(path)
    stream = requests.get(url, stream=True)
    content_length = int(stream.headers['Content-Length'])
    total_written = 0
    chunk_size = 1024
    # See http://click.pocoo.org/6/arguments/#file-args for parameter
    # information
    with click.open_file(
        filename=str(path),
        mode='wb',
        atomic=True,
        lazy=True,
    ) as file_descriptor:
        content_iter = stream.iter_content(chunk_size=chunk_size)
        with click.progressbar(  # type: ignore
            content_iter,
            length=content_length / chunk_size,
            label=label,
        ) as progress_bar:
            for chunk in progress_bar:
                # Filter out keep-alive new chunks.
                if chunk:
                    total_written += len(chunk)
                    file_descriptor.write(chunk)  # type: ignore

    assert total_written == content_length


def download_artifacts(test_pattern: str) -> None:
    """
    Download artifacts.
    """
    downloads = PATTERNS[test_pattern]
    for url, path in downloads:
        _download_file(url=url, path=path)


def run_test(test_pattern: str) -> None:
    """
    Run pytest with a given test pattern.
    """
    result = pytest.main(
        [
            '-vvv',
            '--exitfirst',
            '--capture',
            'no',
            test_pattern,
            '--cov',
            'src/dcos_e2e',
            '--cov',
            'tests',
        ],
    )
    sys.exit(result)


if __name__ == '__main__':
    CI_PATTERN = os.environ.get('CI_PATTERN')
    if CI_PATTERN:
        download_artifacts(test_pattern=CI_PATTERN)
        run_test(test_pattern=CI_PATTERN)
    else:
        subprocess.check_call(['make', 'lint'])
        subprocess.check_call(['dcos-docker', 'doctor'])
        subprocess.check_call(['make', 'docs'])

"""
Download requirements for a test pattern.

This separates the download step from the test step. We could download all
artifacts for all tests, but in the interest of speed, we only download what we
need.
"""

import os
from pathlib import Path
from typing import Dict, Tuple  # noqa: F401

import click
import requests

OSS_PATTERN = (
    'https://downloads.dcos.io/dcos/testing/{version}/dcos_generate_config.sh'
)
OSS_MASTER_ARTIFACT_URL = OSS_PATTERN.format(version='master')
OSS_1_9_ARTIFACT_URL = OSS_PATTERN.format(version='1.9')
OSS_1_10_ARTIFACT_URL = OSS_PATTERN.format(version='1.10')
OSS_1_11_ARTIFACT_URL = OSS_PATTERN.format(version='1.11')

EE_MASTER_ARTIFACT_URL = os.environ['EE_MASTER_ARTIFACT_URL']
EE_1_9_ARTIFACT_URL = os.environ['EE_1_9_ARTIFACT_URL']
EE_1_10_ARTIFACT_URL = os.environ['EE_1_10_ARTIFACT_URL']
EE_1_11_ARTIFACT_URL = os.environ['EE_1_11_ARTIFACT_URL']

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
    'tests/test_dcos_e2e/test_cluster.py::TestClusterFromNodes':
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestClusterSize':
    (),
    'tests/test_dcos_e2e/test_cluster.py::TestExtendConfig::test_default_config':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestExtendConfig::test_extend_config':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestInstallDcosFromPathLogging':
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestIntegrationTests::test_run_pytest':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_cluster.py::TestMultipleClusters::test_two_clusters':  # noqa: E501
    (OSS_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestCopyFiles::test_copy_directory_to_installer':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestCopyFiles::test_copy_files_to_installer':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestEnterpriseIntegrationTests::test_run_pytest':  # noqa: E501
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestSecurityDisabled':
    (EE_MASTER, ),
    'tests/test_dcos_e2e/test_enterprise.py::TestWaitForDCOS::test_auth_with_cli':  # noqa: E501
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
    'tests/test_dcos_e2e/test_node.py::TestNode':
    (OSS_MASTER, ),
}  # type: Dict[str, Tuple]


def download_file(url: str, path: Path) -> None:
    """
    Download a file to a given path.
    """
    label = 'Downloading to ' + str(path)
    stream = requests.get(url, stream=True)
    content_length = int(stream.headers['Content-Length'])
    chunk_size = 100 * 1024
    with click.open_file(str(path), 'wb') as file_descriptor:
        content_iter = stream.iter_content(chunk_size=chunk_size)
        with click.progressbar(  # type: ignore
            content_iter,
            length=content_length / chunk_size,
            label=label,
        ) as progress_bar:
            for chunk in progress_bar:
                if chunk:
                    file_descriptor.write(chunk)  # type: ignore
                    file_descriptor.flush()  # type: ignore


def main() -> None:
    """
    Download artifacts.
    """
    pattern = os.environ['TEST_PATTERN']
    downloads = PATTERNS[pattern]
    for url, path in downloads:
        download_file(url=url, path=path)


if __name__ == '__main__':
    main()

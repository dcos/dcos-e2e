"""
Download requirements for a test pattern.

This separates the download step from the test step. We could download all
artifacts for all tests, but in the interest of speed, we only download what we
need.
"""

import logging
import os
from pathlib import Path

import requests

LOGGER = logging.getLogger(__name__)

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
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestCoreOS::test_enterprise':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestCoreOS::test_oss':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestUbuntu1604::test_oss':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/backends/docker/test_distributions.py::TestUbuntu1604::test_enterprise':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/backends/docker/test_docker.py':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_cluster.py::TestClusterFromNodes':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_cluster.py::TestClusterSize':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_cluster.py::TestExtendConfig::test_default_config':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_cluster.py::TestExtendConfig::test_extend_config':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_cluster.py::TestInstallDcosFromPathLogging':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_cluster.py::TestIntegrationTests::test_run_pytest':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_cluster.py::TestMultipleClusters::test_two_clusters':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_enterprise.py::TestCopyFiles::test_copy_directory_to_installer':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_enterprise.py::TestCopyFiles::test_copy_files_to_installer':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_enterprise.py::TestEnterpriseIntegrationTests::test_run_pytest':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_enterprise.py::TestSecurityDisabled':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_enterprise.py::TestWaitForDCOS::test_auth_with_cli':  # noqa: E501
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_legacy.py::Test110::test_enterprise':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_legacy.py::Test110::test_oss':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_legacy.py::Test111::test_enterprise':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_legacy.py::Test111::test_oss':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_legacy.py::Test19::test_enterprise':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_legacy.py::Test19::test_oss':
    ALL_ARTIFACTS,
    'tests/test_dcos_e2e/test_node.py::TestNode':
    ALL_ARTIFACTS,
}


def download_file(url: str, path: Path) -> None:
    """
    Download a file to a given path.
    """
    message = 'Downloading to ' + str(path)
    LOGGER.warning(message)
    stream = requests.get(url, stream=True)
    chunk_size = 100 * 1024
    with open(str(path), 'wb') as file_descriptor:
        for chunk in stream.iter_content(chunk_size=chunk_size):
            file_descriptor.write(chunk)


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

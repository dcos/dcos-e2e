"""
Download installers.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict  # noqa: F401
from typing import Tuple  # noqa: F401

OSS_PATTERN = (
    'https://downloads.dcos.io/dcos/testing/{version}/dcos_generate_config.sh'
)
OSS_MASTER_INSTALLER_URL = OSS_PATTERN.format(version='master')
OSS_1_9_INSTALLER_URL = OSS_PATTERN.format(version='1.9')
OSS_1_10_INSTALLER_URL = OSS_PATTERN.format(version='1.10')
OSS_1_11_INSTALLER_URL = OSS_PATTERN.format(version='1.11')
OSS_1_12_INSTALLER_URL = OSS_PATTERN.format(version='1.12')

EE_MASTER_INSTALLER_URL = os.environ.get('EE_MASTER_INSTALLER_URL')
EE_1_9_INSTALLER_URL = os.environ.get('EE_1_9_INSTALLER_URL')
EE_1_10_INSTALLER_URL = os.environ.get('EE_1_10_INSTALLER_URL')
EE_1_11_INSTALLER_URL = os.environ.get('EE_1_11_INSTALLER_URL')
EE_1_12_INSTALLER_URL = os.environ.get('EE_1_12_INSTALLER_URL')

OSS_MASTER_INSTALLER_PATH = Path('/tmp/dcos_generate_config.sh')
OSS_1_9_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_9.sh')
OSS_1_10_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_10.sh')
OSS_1_11_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_11.sh')
OSS_1_12_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_12.sh')

EE_MASTER_INSTALLER_PATH = Path('/tmp/dcos_generate_config.ee.sh')
EE_1_9_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_9.ee.sh')
EE_1_10_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_10.ee.sh')
EE_1_11_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_11.ee.sh')
EE_1_12_INSTALLER_PATH = Path('/tmp/dcos_generate_config_1_12.ee.sh')

OSS_MASTER = (OSS_MASTER_INSTALLER_URL, OSS_MASTER_INSTALLER_PATH)
OSS_1_9 = (OSS_1_9_INSTALLER_URL, OSS_1_9_INSTALLER_PATH)
OSS_1_10 = (OSS_1_10_INSTALLER_URL, OSS_1_10_INSTALLER_PATH)
OSS_1_11 = (OSS_1_11_INSTALLER_URL, OSS_1_11_INSTALLER_PATH)
OSS_1_12 = (OSS_1_12_INSTALLER_URL, OSS_1_12_INSTALLER_PATH)
EE_MASTER = (EE_MASTER_INSTALLER_URL, EE_MASTER_INSTALLER_PATH)
EE_1_9 = (EE_1_9_INSTALLER_URL, EE_1_9_INSTALLER_PATH)
EE_1_10 = (EE_1_10_INSTALLER_URL, EE_1_10_INSTALLER_PATH)
EE_1_11 = (EE_1_11_INSTALLER_URL, EE_1_11_INSTALLER_PATH)
EE_1_12 = (EE_1_12_INSTALLER_URL, EE_1_12_INSTALLER_PATH)


PATTERNS = {
    'tests/test_cli': (),
    'tests/test_admin/test_brew.py':
    (),
    'tests/test_admin/test_binaries.py':
    (),
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
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestDCOSInstallation::test_install_dcos_with_custom_ip_detect':  # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_distributions.py::TestCentos7::test_default_distribution':   # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_distributions.py::TestCentos7::test_set_distribution':   # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_distributions.py::TestRHEL7::test_oss':  # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_distributions.py::TestRHEL7::test_enterprise':  # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_distributions.py::TestCoreOS::test_oss':  # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_distributions.py::TestCoreOS::test_enterprise':  # noqa: E501
    (),
    'tests/test_dcos_e2e/backends/aws/test_aws.py::TestTags':  # noqa: E501
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
    'tests/test_dcos_e2e/docker_utils/test_loopback.py':
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
    (),
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
    'tests/test_dcos_e2e/test_legacy.py::Test112::test_enterprise':
    (EE_1_12, ),
    'tests/test_dcos_e2e/test_legacy.py::Test112::test_oss':
    (OSS_1_12, ),
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


def download_installers(test_pattern: str) -> None:
    """
    Download installers.
    """
    downloads = PATTERNS[test_pattern]
    for url, path in downloads:
        args = [
            'minidcos',
            'docker',
            'download-installer',
            '--download-path',
            str(path),
            '--dcos-version',
            url,
        ]
        subprocess.check_output(args=args)


if __name__ == '__main__':
    CI_PATTERN = os.environ.get('CI_PATTERN')
    if CI_PATTERN:
        download_installers(test_pattern=CI_PATTERN)

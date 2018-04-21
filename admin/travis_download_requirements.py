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

# EE_MASTER_ARTIFACT_URL = os.environ['EE_MASTER_ARTIFACT_URL']
# EE_1_9_ARTIFACT_URL = os.environ['EE_1_9_ARTIFACT_URL']
# EE_1_10_ARTIFACT_URL = os.environ['EE_1_10_ARTIFACT_URL']
# EE_1_11_ARTIFACT_URL = os.environ['EE_1_11_ARTIFACT_URL']

OSS_MASTER_ARTIFACT_PATH = Path('/tmp/dcos_generate_config.sh')
OSS_1_9_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_9.sh')
OSS_1_10_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_10.sh')
OSS_1_11_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_11.sh')

EE_MASTER_ARTIFACT_PATH = Path('/tmp/dcos_generate_config.ee.sh')
EE_1_9_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_9.ee.sh')
EE_1_10_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_10.ee.sh')
EE_1_11_ARTIFACT_PATH = Path('/tmp/dcos_generate_config_1_11.ee.sh')


def download_file(url: str, path: Path) -> None:
    """
    Download a file to a given path.
    """
    LOGGER.warn('Downloading to ' + str(path))
    stream = requests.get(url, stream=True)
    chunk_size = 100 * 1024
    with open(str(path), 'wb') as file_descriptor:
        for chunk in stream.iter_content(chunk_size=chunk_size):
            LOGGER.warn('Next chunk')
            file_descriptor.write(chunk)


def main() -> None:
    """
    Download artifacts.
    """
    downloads = (
        (OSS_MASTER_ARTIFACT_URL, OSS_MASTER_ARTIFACT_PATH),
        # (OSS_1_9_ARTIFACT_URL, OSS_1_9_ARTIFACT_PATH),
        # (OSS_1_10_ARTIFACT_URL, OSS_1_10_ARTIFACT_PATH),
        # (OSS_1_11_ARTIFACT_URL, OSS_1_11_ARTIFACT_PATH),
        # (EE_MASTER_ARTIFACT_URL, EE_MASTER_ARTIFACT_PATH),
        # (EE_1_9_ARTIFACT_URL, EE_1_9_ARTIFACT_PATH),
        # (EE_1_10_ARTIFACT_URL, EE_1_10_ARTIFACT_PATH),
        # (EE_1_11_ARTIFACT_URL, EE_1_11_ARTIFACT_PATH),
    )

    for url, path in downloads:
        download_file(url=url, path=path)


if __name__ == '__main__':
    main()

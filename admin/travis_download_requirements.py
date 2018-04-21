"""
Download requirements for a test pattern.

This separates the download step from the test step. We could download all
artifacts for all tests, but in the interest of speed, we only download what we
need.
"""

OSS_MASTER_ARTIFACT_URL = 'https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh'
OSS_1_9_ARTIFACT_URL = 'https://downloads.dcos.io/dcos/testing/1.9/dcos_generate_config.sh'
OSS_1_10_ARTIFACT_URL = 'https://downloads.dcos.io/dcos/testing/1.10/dcos_generate_config.sh'
OSS_1_11_ARTIFACT_URL = 'https://downloads.dcos.io/dcos/testing/1.11/dcos_generate_config.sh'

OSS_MASTER_ARTIFACT_PATH = '/tmp/dcos_generate_config.sh'
OSS_1_9_ARTIFACT_PATH = '/tmp/dcos_generate_config_1_9.sh'
OSS_1_10_ARTIFACT_PATH = '/tmp/dcos_generate_config_1_10.sh'
OSS_1_11_ARTIFACT_PATH = '/tmp/dcos_generate_config_1_11.sh'

EE_MASTER_ARTIFACT_PATH = '/tmp/dcos_generate_config.ee.sh'
EE_1_9_ARTIFACT_PATH = '/tmp/dcos_generate_config_1_9.ee.sh'
EE_1_10_ARTIFACT_PATH = '/tmp/dcos_generate_config_1_10.ee.sh'
EE_1_11_ARTIFACT_PATH = '/tmp/dcos_generate_config_1_11.ee.sh'

[![Build Status](https://travis-ci.org/mesosphere/dcos-e2e.svg?branch=master)](https://travis-ci.org/mesosphere/dcos-e2e)

[![codecov](https://codecov.io/gh/mesosphere/dcos-e2e/branch/master/graph/badge.svg)](https://codecov.io/gh/mesosphere/dcos-e2e)

[![Updates](https://pyup.io/repos/github/mesosphere/dcos-e2e/shield.svg)](https://pyup.io/repos/github/mesosphere/dcos-e2e/)

# DC/OS E2E

Spin up DC/OS clusters with various configurations and run tests using those clusters.

Interactions can be "end to end", meaning that you can test start up and shut down of clusters.

Requires Python 3.5.2+.

<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Usage](#usage)
- [Contributing](#contributing)
- [Required Environment](#required-environment)
- [Cleaning Up and Troubleshooting](#cleaning-up-and-troubleshooting)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

## Usage

Tests must be run in a supported environment.
See "Required Environment".

To create tests using clusters with custom configurations, first install the harness:

```sh
pip install --process-dependency-links git+https://github.com/mesosphere/dcos-e2e.git@master 
```

Then, create a test, such as the following:

```python
import subprocess
import uuid
from pathlib import Path

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from passlib.hash import sha512_crypt

def test_oss_example():

    oss_artifact = Path('/tmp/dcos_generate_config.sh')

    with Cluster(cluster_backend=Docker()) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=oss_artifact,
            extra_config={'check_time': True},
        )
        (master, ) = cluster.masters
        result = master.run(args=['test', '-f', path],
                            user=cluster.default_ssh_user)
        print(result.stdout)
        cluster.wait_for_dcos_oss()
        cluster.run_integration_tests(pytest_command=['pytest', '-x', 'test_tls.py'])
        try:
            master.run(args=['test', '-f', '/no/file/here'],
                       user=cluster.default_ssh_user)
        except subprocess.CalledProcessError:
            print('No file exists')

def test_ee_example():

    ee_artifact = Path('/tmp/dcos_generate_config.ee.sh')
    license_key_contents = Path('/tmp/license-key.txt').read_text()

    superuser_username = str(uuid.uuid4())
    superuser_password = str(uuid.uuid4())

    # DC/OS Enterprise clusters require various configuration variables which
    # are not allowed or required by DC/OS OSS clusters.
    extra_config = {
        'superuser_username': superuser_username,
        'superuser_password_hash': sha512_crypt.hash(superuser_password),
        'fault_domain_enabled': False,
        'license_key_contents': license_key_contents,
    }

    with Cluster(cluster_backend=Docker()) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=ee_artifact,
            extra_config=extra_config,
        )
        cluster.wait_for_dcos_ee(
            superuser_username=superuser_username,
            superuser_password=superuser_password,
        )
```

See [`API.md`](./API.md) for details on the API.

## Contributing

See [`CONTRIBUTING.rst`](./CONTRIBUTING.rst) for details on how to contribute to this repository.

## Required Environment

See [`BACKENDS.md`](./BACKENDS.md) for details on requirements for launching clusters with each backend.

## Cleaning Up and Troubleshooting

Some backends leave junk around, especially when tests are cancelled.
See [`BACKENDS.md`](./BACKENDS.md) for specifics of dealing with particular backends.

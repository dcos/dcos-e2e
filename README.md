[![Build Status](https://travis-ci.org/mesosphere/dcos-e2e.svg?branch=master)](https://travis-ci.org/mesosphere/dcos-e2e)

[![codecov](https://codecov.io/gh/mesosphere/dcos-e2e/branch/master/graph/badge.svg)](https://codecov.io/gh/mesosphere/dcos-e2e)

[![Updates](https://pyup.io/repos/github/mesosphere/dcos-e2e/shield.svg)](https://pyup.io/repos/github/mesosphere/dcos-e2e/)

# DC/OS End to End tests

End to end tests are tests which require a DC/OS cluster to run against.
Each test spins up at least one cluster, and has the choice of configuring this cluster as appropriate.
For example, a test may require a cluster with a certain number of agents, or certain configuration options.

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
pip install git+https://github.com/mesosphere/dcos-e2e.git@master
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

    superuser_username = str(uuid.uuid4())
    superuser_password = str(uuid.uuid4())

    with Cluster(cluster_backend=Docker()) as cluster:
        cluster.install_dcos_from_path(
            build_artifact=ee_artifact,
            extra_config={
                'superuser_username': superuser_username,
                'superuser_password_hash': sha512_crypt.hash(superuser_password),
                'check_time': True,
            },
        )
        cluster.wait_for_dcos_ee(
            superuser_username=superuser_username,
            superuser_password=superuser_password,
        )
        cluster.run_integration_tests(pytest_command=['pytest', '-x', 'test_tls.py'])

```

See [`API.md`](./API.md) for details on the API.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for details on how to contribute to this repository.

## Required Environment

See [`BACKENDS.md`](./BACKENDS.md) for details on requirements for launching clusters with each backend.

## Cleaning Up and Troubleshooting

Some backends leave junk around, especially when tests are cancelled.
See [`BACKENDS.md`](./BACKENDS.md) for specifics of dealing with particular backends.

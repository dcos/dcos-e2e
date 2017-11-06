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

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster


class TestExample:

    def test_example(self):
        with Cluster(
            extra_config={'check_time': True},
            cluster_backend=Docker(),
            generate_config_url=Path('file:///tmp/dcos_generate_config.sh'),
        ) as cluster:
            (master, ) = cluster.masters
            result = master.run_as_root(args=['test', '-f', path])
            print(result.stdout)
            cluster.run_integration_tests(pytest_command=['pytest', '-x', 'test_tls.py'])
            try:
                master.run_as_root(args=['test', '-f', '/no/file/here'])
            except subprocess.CalledProcessError:
                print('No file exists')
```

See [`API.md`](./API.md) for details on the API.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for details on how to contribute to this repository.

## Required Environment

See [`BACKENDS.md`](./BACKENDS.md) for details on requirements for launching clusters with each backend.

## Cleaning Up and Troubleshooting

Some backends leave junk around, especially when tests are cancelled.
See [`BACKENDS.md`](./BACKENDS.md) for specifics of dealing with particular backends.

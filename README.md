[![Build Status](https://travis-ci.org/adamtheturtle/dcos-e2e.svg?branch=master)](https://travis-ci.org/adamtheturtle/dcos-e2e)

# DC/OS End to End tests

End to end tests are tests which require a DC/OS cluster to run against.
Each test spins up at least one cluster, and has the choice of configuring this cluster as appropriate.
For example, a test may require a cluster with a certain number of agents, or certain configuration options.

The tests should be not be tied to the backend infrastructure.
That is, they should pass against clusters on all supported infrastructures.
The current implementation supports only a [DC/OS Docker](https://github.com/dcos/dcos-docker) backend.

This is a proof of concept.
We plan to iterate on this repository and manually run tests.
With that experience, we will choose where to put the test suite and whether it should be run on CI.

## Usage

Tests must be run in a supported environment.
See "Test Environment".

To create tests using clusters with custom configurations, first install the harness:

```sh
pip install git+https://github.com/adamtheturtle/dcos-e2e.git@genconf-extra
```

Then, create a test, such as the following:

```python
from dcos_e2e.cluster import Cluster

class TestExample:

    def test_example(self):
        config = {
            'cluster_docker_credentials': {
                'auths': {
                    'https://index.docker.io/v1/': {
                        'auth': 'redacted'
                    },
                },
            },
            'cluster_docker_credentials_enabled': True,
        }

        with Cluster(
            extra_config=config,
            # Default 1
            masters=1,
            # Default 0
            agents=1,
            # Default 0
            public_agents=1,
        ) as cluster:
            (master, ) = cluster.masters
            result = master.run_as_root(args=['test', '-f', path])
            print(result.stdout)
```

## Contributing

See `CONTRIBUTING.md` for details on how to contribute to this repository.

## Test Environment

Tests for this package and tests which use this package must be run on a host which is supported by DC/OS Docker.
See the [DC/OS Docker README](https://github.com/dcos/dcos-docker/blob/master/README.md).

Then set the test options.

Configuration options are specified in [`sample-configuration.yaml`](https://raw.githubusercontent.com/adamtheturtle/dcos-e2e/master/sample-configuration.yaml).

Copy this file to `~/.dcos-e2e.yaml` and fill it in as appropriate.

### Quick Start Options

```sh
ARTIFACT_URL=https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh
DCOS_DOCKER_REPOSITORY=https://github.com/dcos/dcos-docker.git
DCOS_DOCKER_BRANCH=master
SAMPLE_CONFIGURATION_URL=https://raw.githubusercontent.com/adamtheturtle/dcos-e2e/master/sample-configuration.yaml

curl $SAMPLE_CONFIGURATION_URL > ~/.dcos-e2e.yaml
curl -o ~/dcos_generate_config.sh $ARTIFACT_URL
git clone -b $DCOS_DOCKER_BRANCH $DCOS_DOCKER_REPOSITORY /tmp/dcos-docker
```

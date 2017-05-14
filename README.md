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
pip install git+https://github.com/adamtheturtle/dcos-e2e.git@master
```

Then, create a test, such as the following:

```python
import subprocess

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

        with Cluster(extra_config=config) as cluster:
            (master, ) = cluster.masters
            result = master.run_as_root(args=['test', '-f', path])
            print(result.stdout)
            pytest_command = ['pytest', '-x', 'test_tls.py']
            cluster.run_integration_tests(pytest_command=pytest_command)
            try:
                master.run_as_root(args=['test', '-f', '/no/file/here'])
            except subprocess.CalledProcessError:
                print('No file exists')
```

#### `Cluster(extra_config=None, masters=1, agents=1, public_agents=1, log_output_live=False)`

This is a context manager which spins up a cluster.
At the time of writing, this uses DC/OS Docker.

##### Parameters

###### `extra_config`

Configuration variables to add to a base configuration.

###### `masters`

The number of master nodes.

###### `agents`

The number of agent nodes.

###### `public_agents`

The number of public agent nodes.

###### `log_output_live`

If set to `True`, the output of processes run on the host to create and manage clusters will be logged.

To see these logs in `pytest` tests, use the `-s` flag.

##### Attributes

###### `masters`

The `master` nodes in the cluster.

###### `agents`

The agent nodes in the cluster.

###### `public_agents`

The public agent nodes in the cluster.

###### `run_integration_tests`

This takes a `pytest_command` and allows integration tests to be run on the
cluster.

#### Nodes

Commands can be run on nodes in clusters.

###### `node.run_as_root(log_output_live=False)`

If `log_output_live` is set to `True`, the output of processes run on the host to create and manage clusters will be logged.

To see these logs in `pytest` tests, use the `-s` flag.

## Contributing

See `CONTRIBUTING.md` for details on how to contribute to this repository.

## Test Environment

Tests for this package and tests which use this package must be run on a host which is supported by DC/OS Docker.
See the [DC/OS Docker README](https://github.com/dcos/dcos-docker/blob/master/README.md).

Running tests for or with this package requires:

* A DC/OS Docker clone at `/tmp/dcos-docker`
* DC/OS OSS or Enterprise artifact at `/tmp/dcos_generate_config.sh`.

For example:

```sh
ARTIFACT_URL=https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh
DCOS_DOCKER_REPOSITORY=https://github.com/adamtheturtle/dcos-docker.git
DCOS_DOCKER_BRANCH=macos-DCOS-15645

curl -o /tmp/dcos_generate_config.sh $ARTIFACT_URL
git clone -b $DCOS_DOCKER_BRANCH $DCOS_DOCKER_REPOSITORY /tmp/dcos-docker
```

## Cleaning Up

Tests run with this harness clean up after themselves.
However, if a test is interrupted, it can leave behind containers, volumes and files.
To remove these, run the following:

```sh
docker stop $(docker ps -a -q --filter="name=dcos-")
docker rm --volumes $(docker ps -a -q --filter="name=dcos-")
docker volume prune --force
rm -rf /tmp/dcos-docker-*
```

If this repository is available, run `make clean`.

## Troubleshooting

### macOS File Sharing

On macOS `/tmp` is a symlink to `/private/tmp`.
`/tmp` is used by the harness.
Docker for Mac must be configured to allow `/private` to be bind mounted into Docker containers.
This is the default.
See Docker > Preferences > File Sharing.

### Out of space errors

See "Cleaning up".

### Parallelization

To see print output while running tests in parallel,
use the `-s` `pytest` flag and put the following in the code:

```python
import sys
sys.stdout = sys.stderr
```

`pdb` will not work when running tests in parallel.

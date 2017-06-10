[![Build Status](https://travis-ci.org/adamtheturtle/dcos-e2e.svg?branch=master)](https://travis-ci.org/adamtheturtle/dcos-e2e)

[![Requirements Status](https://requires.io/github/adamtheturtle/dcos-e2e/requirements.svg?branch=master)](https://requires.io/github/adamtheturtle/dcos-e2e/requirements/?branch=master)

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

<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Usage](#usage)
    - [`dcos_e2e.backend.DCOS_Docker`](#dcos_e2ebackenddcos_docker)
      - [Parameters](#parameters)
        - [`generate_config_path`](#generate_config_path)
        - [`dcos_docker_path`](#dcos_docker_path)
        - [`workspace_path`](#workspace_path)
    - [`dcos_e2e.cluster.Cluster`](#dcos_e2eclustercluster)
      - [Parameters](#parameters-1)
        - [`cluster_backend`](#cluster_backend)
        - [`extra_config`](#extra_config)
        - [`masters`](#masters)
        - [`agents`](#agents)
        - [`public_agents`](#public_agents)
        - [`log_output_live`](#log_output_live)
        - [`files_to_copy_to_installer`](#files_to_copy_to_installer)
        - [`files_to_copy_to_masters`](#files_to_copy_to_masters)
        - [`destroy_on_error`](#destroy_on_error)
      - [Attributes](#attributes)
        - [`masters`](#masters-1)
        - [`agents`](#agents-1)
        - [`public_agents`](#public_agents-1)
        - [`run_integration_tests(pytest_command)`](#run_integration_testspytest_command)
        - [`destroy()`](#destroy)
        - [`wait_for_dcos()`](#wait_for_dcos)
    - [Nodes](#nodes)
        - [`node.run_as_root(log_output_live=False)`](#noderun_as_rootlog_output_livefalse)
- [Contributing](#contributing)
- [Test Environment](#test-environment)
- [Vagrant Quick Start](#vagrant-quick-start)
- [Cleaning Up](#cleaning-up)
- [Troubleshooting](#troubleshooting)
  - [macOS File Sharing](#macos-file-sharing)
  - [Out of space errors](#out-of-space-errors)
  - [Parallelization](#parallelization)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

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
from pathlib import Path

from dcos_e2e.backend import DCOS_Docker
from dcos_e2e.cluster import Cluster

class TestExample:

    def test_example(self):
        backend = DCOS_Docker(
            workspace_path=Path('/tmp'),
            generate_config_path=Path('/tmp/dcos_generate_config.sh'),
            dcos_docker_path=Path('/tmp/dcos-docker'),
        )

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

        with Cluster(extra_config=config, cluster_backend=backend) as cluster:
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

#### `dcos_e2e.backend.DCOS_Docker`

This is a backend which can be used to run a `Cluster`.

```python
DCOS_Docker(
    generate_config_path,
    dcos_docker_path,
    workspace_path,
)
```

##### Parameters

###### `generate_config_path`

The path to a build artifact to install.

###### `dcos_docker_path`

The path to a clone of DC/OS Docker.
This clone will be used to create the cluster.

###### `workspace_path`

The directory to create large temporary files in.
The files are cleaned up when the cluster is destroyed.

#### `dcos_e2e.cluster.Cluster`

```python
Cluster(
    cluster_backend,
    extra_config=None,
    masters=1,
    agents=1,
    public_agents=1,
    log_output_live=False,
    destroy_on_error=True,
    files_to_copy_to_installer=None,
    files_to_copy_to_masters=None,
)
```

This is a context manager which spins up a cluster.
At the time of writing, this uses DC/OS Docker.

##### Parameters

###### `cluster_backend`

The backend to use for the cluster.
Currently, the only supported backend is an instance of `dcos_e2e.backend.DCOS_Docker`.

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


###### `files_to_copy_to_installer`

A mapping of host paths to paths on the installer node.
These are files to copy from the host to the installer node before installing DC/OS.
Currently on DC/OS Docker the only supported paths on the installer are in the `/genconf` directory.

###### `files_to_copy_to_masters`

A mapping of host paths to paths on the master nodes.
These are files to copy from the host to the master nodes before installing DC/OS.
On DC/OS Docker the files are mounted, read only, to the masters.

###### `destroy_on_error`

If set to `True`, the cluster is destroyed on exit in all cases.
If set to `False`, the cluster is preserved if there is an error.

##### Methods

###### `run_integration_tests(pytest_command)`

Run integration tests on the cluster.

###### `destroy()`

Destroy all nodes in the cluster.

###### `wait_for_dcos()`

Wait for the cluster set up to be complete.

##### Attributes

###### `masters`

The `master` nodes in the cluster.

###### `agents`

The agent nodes in the cluster.

###### `public_agents`

The public agent nodes in the cluster.

##### `original_superuser_username`

The original superuser username of the cluster.

##### `original_superuser_password`

The original superuser password of the cluster.

#### Nodes

Commands can be run on nodes in clusters.

###### `node.run_as_root(log_output_live=False)`

If `log_output_live` is set to `True`, the output of processes run on the host to create and manage clusters will be logged.

To see these logs in `pytest` tests, use the `-s` flag.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for details on how to contribute to this repository.

## Test Environment

Tests for this package and tests which use this package must be run on a host which is supported by DC/OS Docker.
See the [DC/OS Docker README](https://github.com/dcos/dcos-docker/blob/master/README.md).

Running tests for or with this package requires:

*   A DC/OS Docker clone at `/tmp/dcos-docker`, and
*   DC/OS OSS or Enterprise artifact at `/tmp/dcos_generate_config.sh`.

For example:

```sh
ARTIFACT_URL=https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh
DCOS_DOCKER_REPOSITORY=https://github.com/dcos/dcos-docker.git
DCOS_DOCKER_BRANCH=master

curl -o /tmp/dcos_generate_config.sh $ARTIFACT_URL
git clone -b $DCOS_DOCKER_BRANCH $DCOS_DOCKER_REPOSITORY /tmp/dcos-docker
```

or `make download-dependencies`.

## Vagrant Quick Start

With [Vagrant](https://www.vagrantup.com) and [VirtualBox](https://www.virtualbox.org/wiki/Downloads), it is possible to quickly get a test environment running.

Run the following commands to create an environment.
These commands will create a Vagrant VM with access to the files in the
directory from which they are launched.
These files will be at `/vagrant` in the VM.

```sh
# Download files from the DC/OS Docker repository to create a VM.
mkdir -p vagrant
cd vagrant
curl -O https://raw.githubusercontent.com/dcos/dcos-docker/master/vagrant/resize-disk.sh
curl -O https://raw.githubusercontent.com/dcos/dcos-docker/master/vagrant/vbox-network.sh
chmod +x resize-disk.sh
chmod +x vbox-network.sh
cd ..
curl -O https://raw.githubusercontent.com/dcos/dcos-docker/master/Vagrantfile
vagrant/resize-disk.sh 102400
```

Then create a virtual environment:

```
vagrant ssh -c 'curl https://raw.githubusercontent.com/adamtheturtle/dcos-e2e/master/vagrant_create_env.sh | /bin/bash'
```

Then, to enter the environment, run the following:

```sh
laptop$ vagrant ssh
[root@vagrant]$ pyenv activate dcos
```

Then install the dependencies of the package you want to test.

There is a common issue which causes error messages on old kernels.
See  <https://github.com/moby/moby/issues/5618>.
Optionally on the VM run the following commands to update the kernel:

```sh
sudo yum update -y kernel
reboot
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

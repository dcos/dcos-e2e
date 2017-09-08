[![Build Status](https://travis-ci.org/mesosphere/dcos-e2e.svg?branch=master)](https://travis-ci.org/mesosphere/dcos-e2e)

[![Requirements Status](https://requires.io/github/mesosphere/dcos-e2e/requirements.svg?branch=master)](https://requires.io/github/mesosphere/dcos-e2e/requirements/?branch=master)

[![codecov](https://codecov.io/gh/mesosphere/dcos-e2e/branch/master/graph/badge.svg)](https://codecov.io/gh/mesosphere/dcos-e2e)

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
- [Test Environment](#test-environment)
  - [Vagrant Quick Start](#vagrant-quick-start)
- [Cleaning Up](#cleaning-up)
  - [DC/OS Docker Backend](#dcos-docker-backend)
- [Troubleshooting](#troubleshooting)
  - [DC/OS Docker Backend](#dcos-docker-backend-1)
    - [macOS File Sharing](#macos-file-sharing)
    - [Out of space errors](#out-of-space-errors)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

## Usage

Tests must be run in a supported environment.
See "Test Environment".

To create tests using clusters with custom configurations, first install the harness:

```sh
pip install git+https://github.com/mesosphere/dcos-e2e.git@master
```

Then, create a test, such as the following:

```python
import subprocess
from pathlib import Path

from dcos_e2e.backends import DCOS_Docker
from dcos_e2e.cluster import Cluster


class TestExample:

    def test_example(self):
        with Cluster(
            extra_config={'check_time': True},
            cluster_backend=DCOS_Docker(),
            generate_config_path=Path('/tmp/dcos_generate_config.sh'),
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

## Test Environment

Tests for this package and tests which use this package must be run on a host which is supported by DC/OS Docker.
For more information about `DC/OS Docker` see the [DC/OS Docker README](https://github.com/dcos/dcos-docker/blob/master/README.md).
To run unit tests see [`CONTRIBUTING.md`](./CONTRIBUTING.md).

### Vagrant Quick Start

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
vagrant ssh -c 'curl https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/vagrant_create_env.sh | /bin/bash'
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

### DC/OS Docker Backend

Tests run with this harness clean up after themselves.
However, if a test is interrupted, it can leave behind containers, volumes and files.
To remove these, run the following:

```sh
docker stop $(docker ps -a -q --filter="name=dcos-e2e")
docker rm --volumes $(docker ps -a -q --filter="name=dcos-e2e")
docker volume prune --force
```

If this repository is available, run `make clean`.

## Troubleshooting

### DC/OS Docker Backend

#### macOS File Sharing

On macOS `/tmp` is a symlink to `/private/tmp`.
`/tmp` is used by the harness.
Docker for Mac must be configured to allow `/private` to be bind mounted into Docker containers.
This is the default.
See Docker > Preferences > File Sharing.

#### Out of space errors

See "Cleaning up".

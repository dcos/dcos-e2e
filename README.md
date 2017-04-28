# DC/OS End to End tests

End to end tests are tests which require a DC/OS cluster to run against.
Each test spins up at least one cluster, and has the choice of configuring this cluster as appropriate.
For example, a test may require a cluster with a certain number of agents, or certain configuration options.

The tests should be not be tied to the backend infrastructure.
That is, they should pass against clusters on all supported infrastructures.
The current implementation supports only a [DC/OS Docker](https://github.com/dcos/dcos-docker) backend.

Usually tests are kept with the source code.
However, this is a proof of concept.
We plan to iterate on this repository and manually run tests.
With that experience, we will choose where to put the test suite and whether it should be run on CI.

## Test Environment

Tests for this package and tests which use this package must be run on a host which is supported by DC/OS Docker.
One way to guarantee this support is to create a Vagrant VM which supports DC/OS Docker.

```sh
mkdir -p vagrant
cd vagrant
curl -O https://raw.githubusercontent.com/dcos/dcos-docker/master/vagrant/resize-disk.sh
curl -O https://raw.githubusercontent.com/dcos/dcos-docker/master/vagrant/vbox-network.sh
chmod +x resize-disk.sh
chmod +x vbox-network.sh
cd ..
curl -O https://raw.githubusercontent.com/dcos/dcos-docker/master/Vagrantfile
vagrant/resize-disk.sh 102400
# Update the kernel and re-provision to work around
# https://github.com/moby/moby/issues/5618
vagrant ssh -c 'sudo yum update -y kernel'
vagrant reload
vagrant provision
# Wait until the VM has presumably booted
sleep 30
vagrant ssh
```

Then when in the environment, install dependencies and enter a `virtualenv`:

```sh
curl -O https://raw.githubusercontent.com/adamtheturtle/dcos-e2e/master/vagrant_bootstrap.sh
source vagrant_bootstrap.sh
```

Then set the test options.
See "Options".

### Tests for this package

To run tests for this package, run `pytest`:

```sh
pytest
```

To run the tests concurrently, use [pytest-xdist](https://github.com/pytest-dev/pytest-xdist).
For example:

```sh
pytest -n 2
```

### Options

#### tl;dr Vagrant

```sh
# Download the Vagrant sample config
curl \
    https://raw.githubusercontent.com/adamtheturtle/dcos-e2e/master/vagrant-sample-configuration.yaml \
    > ~/.dcos-e2e.yaml

# Download the DC/OS master artifact.
curl \
    -o /home/vagrant/dcos_generate_config.sh \
    https://downloads.dcos.io/dcos/testing/master/dcos_generate_config.sh

# Clone a specific branch of DC/OS Docker
git clone \
    -b dcos-enterprise-postflight-DCOS-15322 \
    https://github.com/adamtheturtle/dcos-docker.git \
    /tmp/dcos-docker
```

#### Details

Configuration options are specified in [`sample-configuration.yaml`](https://raw.githubusercontent.com/adamtheturtle/dcos-e2e/master/sample-configuration.yaml).

Copy this file to `~/.dcos-e2e.yaml` and fill it in as appropriate.

The DC/OS Docker clone should be in a location which the tests can write to.
In the Vagrant development environment, `/tmp/dcos-docker` is a suitable place.
This directory may be interfered with by the tests.

Postflight checks to see if DC/OS is ready do not work for DC/OS Enterprise.
See <https://jira.mesosphere.com/browse/DCOS-15322>.
As a workaround, use a particular fork of `DC/OS Docker`
until <https://github.com/dcos/dcos-docker/pull/34> is merged:

```sh
git clone -b dcos-enterprise-postflight-DCOS-15322 https://github.com/adamtheturtle/dcos-docker.git
```

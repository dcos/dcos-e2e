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

## Running tests

The tests must be run on a host which is supported by DC/OS Docker.
One way to guarantee this support is to create a Vagrant VM which supports DC/OS Docker.

```sh
cd tests/end_to_end/
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
vagrant ssh
```

Then when in the environment, install dependencies and enter a `virtualenv`:

```sh
source bootstrap.sh
```

Then set the test options.
See "Options".

Then run the tests:

```sh
pytest
```

### Options

Configuration options are specified in `sample-configuration.yaml`.
Copy this file to `configuration.yaml` and fill it in as appropriate.
Values with `null` in the sample configuration are not required.

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

## Parallelisation

These tests are very slow and they should be very parallelisable,
perhaps with [pytest-xdist](https://github.com/pytest-dev/pytest-xdist).
However, that may require some changes as currently DC/OS Docker names containers in a deterministic manner.
That is, you can't spin up two DC/OS Docker clusters simultaneously right now.

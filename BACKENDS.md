# Backends

DC/OS E2E has a pluggable backend system.
A backend is used as the `cluster_backend` parameter to the `Cluster` class.
These backend classes allow backend-specific configuration of the cluster.

<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [`dcos_e2e.backend.Docker`](#dcos_e2ebackenddocker)
  - [Requirements](#requirements)
  - [Parameters](#parameters)
    - [`workspace_dir`](#workspace_dir)
    - [`master_mounts`, `agent_mounts`, `public_agent_mounts`](#master_mounts-agent_mounts-public_agent_mounts)
    - [`linux_distribution`](#linux_distribution)
    - [`docker_version`](#docker_version)
  - [DC/OS Installation](#dcos-installation)
  - [Troubleshooting](#troubleshooting)
    - [Cleaning Up and Fixing "Out of Space" Errors](#cleaning-up-and-fixing-out-of-space-errors)
    - [macOS File Sharing](#macos-file-sharing)
    - [SELinux](#selinux)
    - [Clock sync errors](#clock-sync-errors)
- [Using existing nodes](#using-existing-nodes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

## `dcos_e2e.backend.Docker`

```python
Docker(
    workspace_dir=None,
    master_mounts=None,
    agent_mounts=None,
    public_agent_mounts=None,
    linux_distribution=dcos_e2e.distributions.Distributions,
    docker_version=dcos_e2e.docker_versions.DockerVersion,
    storage_driver=None,
)
```

### Requirements

* Docker

Plenty of memory must be given to Docker.
On Docker for Mac, this can be done from Docker > Preferences > Advanced.
This backend has been tested with a four node cluster with 9 GB memory given to Docker.

* IP routing set up for Docker

On Docker for Mac this requires a tool such as [docker-mac-network](https://github.com/wojas/docker-mac-network).

* `ssh`

### Parameters

#### `workspace_dir`

The directory in which large temporary files will be created.
These files will be deleted at the end of a test run.
This is equivalent to `dir` in [TemporaryDirectory](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory).

#### `master_mounts`, `agent_mounts`, `public_agent_mounts`

Mounts to add to node containers.
See `volumes` in [the `docker-py` documentation](http://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run) for details.

#### `linux_distribution`

Linux distribution to use.
Currently only `dcos_e2e.distributions.Distribution.CENTOS_7` and `dcos_e2e.distributions.Distribution.COREOS` are supported.

#### `docker_version`

The Docker version to use.
See `list(dcos_e2e.docker_versions)` for available versions.

#### `storage_driver`

The Docker storage driver to use.
The storage driver is the host's driver by default.
If this is not a supported driver, `aufs` is used.
See `list(dcos_e2e.docker_storage_drivers)` for available storage drivers.

### DC/OS Installation

`Cluster`s created by the Docker backend only support installing DC/OS via `install_dcos_from_path`.
`Node`s of `Cluster`s created by the Docker backend do not distinguish between `public_ip_address` and `private_ip_address`.

### Troubleshooting

#### Cleaning Up and Fixing "Out of Space" Errors

If a test is interrupted, it can leave behind containers, volumes and files.
To remove these, run the following:

```sh
docker stop $(docker ps -a -q --filter="name=dcos-e2e")
docker rm --volumes $(docker ps -a -q --filter="name=dcos-e2e")
docker volume prune --force
```

If this repository is available, run `make clean`.

#### macOS File Sharing

On macOS `/tmp` is a symlink to `/private/tmp`.
`/tmp` is used by the harness.
Docker for Mac must be configured to allow `/private` to be bind mounted into Docker containers.
This is the default.
See Docker > Preferences > File Sharing.

#### SELinux

Tests inherit the host's environment.
Any tests that rely on SELinux being available require it be available on the host.

#### Clock sync errors

On various platforms, the clock can get out of sync between the host machine and Docker containers.
This is particularly problematic if using `check_time: true` in the DC/OS configuration.
To work around this, run `docker run --rm --privileged alpine hwclock -s`.

## Using existing nodes

It is possible to use existing nodes on any platform with DC/OS E2E.

`Cluster.from_nodes(masters, agents, public_agents, default_ssh_user)`

Clusters created with this method cannot be destroyed by DC/OS E2E.
It is assumed that DC/OS is already up and running on the given nodes and installing DC/OS is not supported.

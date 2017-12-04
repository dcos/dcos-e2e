# Backends

DC/OS E2E has a pluggable backend system.
A backend is used as the `cluster_backend` parameter to the `Cluster` class.
These backend classes allow backend-specific configuration of the cluster.

<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [`dcos_e2e.backend.Docker`](#dcos_e2ebackenddocker)
  - [Parameters](#parameters)
    - [`workspace_dir`](#workspace_dir)
    - [`master_mounts`, `agent_mounts`, `public_agent_mounts`](#master_mounts-agent_mounts-public_agent_mounts)
  - [DC/OS Installation](#dcos-installation)
  - [Troubleshooting](#troubleshooting)
    - [Cleaning Up and Fixing "Out of Space" Errors](#cleaning-up-and-fixing-out-of-space-errors)
    - [macOS File Sharing](#macos-file-sharing)
    - [Clock sync errors](#clock-sync-errors)
- [`dcos_e2e.backend.AWS`](#dcos_e2ebackendaws)
  - [Parameters](#parameters-1)
    - [`aws_access_key_id`](#aws_access_key_id)
    - [`aws_secret_access_key`](#aws_secret_access_key)
    - [`aws_region`](#aws_region)
    - [`admin_location`](#admin_location)
    - [`instance_type`](#instance_type)
    - [`deploy_timeout`](#deploy_timeout)
    - [`workspace_dir`](#workspace_dir-1)
  - [DC/OS Installation](#dcos-installation-1)
- [Using existing nodes](#using-existing-nodes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

## `dcos_e2e.backend.Docker`

```python
Docker(workspace_dir=None, master_mounts=None, agent_mounts=None, public_agent_mounts)
```

### Parameters

#### `workspace_dir`

The directory in which large temporary files will be created.
These files will be deleted at the end of a test run.
This is equivalent to `dir` in [TemporaryDirectory](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory).

#### `master_mounts`, `agent_mounts`, `public_agent_mounts`

Mounts to add to node containers.
See `volumes` in [the `docker-py` documentation](http://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run) for details.

### DC/OS Installation

`Cluster`s created by the Docker backend only support installing DC/OS via `install_dcos_from_path`.

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

#### Clock sync errors

On various platforms, the clock can get out of sync between the host machine and Docker containers.
This is particularly problematic if using `check_time: true` in the DC/OS configuration.
To work around this, run `docker run --rm --privileged alpine hwclock -s`.

## `dcos_e2e.backend.AWS`

```python
AWS(
    aws_access_key_id,
    aws_secret_access_key,
    aws_region,
    admin_location,
    instance_type,
    deploy_timeout=60,
    workspace_dir=None,
)
```

### Parameters

#### `aws_access_key_id`

The access key ID which must be specified as part of the authentication with AWS.

#### `aws_secret_access_key`

The secret access key which must be specified as part of the authentication with AWS.

#### `aws_region`

The AWS region that the backend should create the clusters in. This must be a string representation of an [AWS region code](http://docs.aws.amazon.com/general/latest/gr/rande.html). The following regions are supported.

*`'ap-northeast-1'`
*`'ap-southeast-1'`
*`'ap-southeast-2'`
*`'eu-central-1'`
*`'eu-west-1'`
*`'sa-east-1'`
*`'us-east-1'`
*`'us-west-1'`
*`'us-west-2'`

#### `admin_location`

IP address range of which the corresponding hosts are allowed to access nodes of clusters created by this backend. Specifiying ``'0.0.0.0/32'`` will alone anyone to connect.

#### `instance_type`

The [AWS instance type](https://aws.amazon.com/ec2/instance-types/) for all hosts of clusters created by this backend.

#### `deploy_timeout`

The lifespan measured in minutes for clusters created by this backend.

#### `workspace_dir`

The directory in which temporary files will be created.
These files will be deleted at the end of a test run.
This is equivalent to `dir` in [TemporaryDirectory](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory).

### DC/OS Installation

`Cluster`s created by the AWS backend only support installing DC/OS via `install_dcos_from_url`.

## Using existing nodes

It is possible to use existing nodes on any platform with DC/OS E2E.

`Cluster.from_nodes(masters, agents, public_agents, default_ssh_user)`

Clusters created with this method cannot be destroyed by DC/OS E2E.
It is assumed that DC/OS is already up and running on the given nodes and installing DC/OS is not supported.

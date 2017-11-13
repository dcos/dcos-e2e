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
    - [`master_mounts`](#master_mounts)
  - [Troubleshooting](#troubleshooting)
    - [Cleaning Up and Fixing "Out of Space" Errors](#cleaning-up-and-fixing-out-of-space-errors)
    - [macOS File Sharing](#macos-file-sharing)
- [`dcos_e2e.backend.ExistingCluster`](#dcos_e2ebackendexistingcluster)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

## `dcos_e2e.backend.Docker`

```python
Docker(workspace_dir=None, master_mounts=None)
```

### Parameters

#### `workspace_dir`

The directory in which large temporary files will be created.
These files will be deleted at the end of a test run.
This is equivalent to `dir` in [TemporaryDirectory](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory).

#### `master_mounts`

Mounts to add to master node containers.
See `volumes` in [the `docker-py` documentation](http://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run) for details.


When creating a `Cluster` with this backend, the following parameter conditions must be true:
* `build_artifact` must be of type `pathlib.Path`

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

## `dcos_e2e.backend.ExistingCluster`

This is a backend which can be used to run a `Cluster`.
It is unusual because it does not provision a cluster, but it instead takes `set`s of `dcos_e2e.node.Node`s and a `default_ssh_user` that can `run` commands on those `Node`s.
This means that it cannot support various operations which rely on access to the start up and teardown mechanisms of a cluster.

As such, various `Cluster` parameters must be set in particular ways.

```python
ExistingCluster(masters, agents, public_agents, default_ssh_user)
```

When creating a `Cluster` with this backend, the following parameter conditions must be true:
* `build_artifact` must be `None`,
* `extra_config` must be `None` or `{}`,
* `masters` matches the number of master nodes in the existing cluster,
* `agents` matches the number of agent nodes in the existing cluster,
* `public_agents` matches the number of public agent nodes in the existing cluster,
* `destroy_on_error` must be `False`,
* `destroy_on_success` must be `False`,
* `files_to_copy_to_installer` must be `None` or `{}`,

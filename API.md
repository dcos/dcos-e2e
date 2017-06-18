<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [API](#api)
  - [`dcos_e2e.backend.DCOS_Docker`](#dcos_e2ebackenddcos_docker)
    - [Parameters](#parameters)
      - [`dcos_docker_path`](#dcos_docker_path)
  - [`dcos_e2e.cluster.Cluster`](#dcos_e2eclustercluster)
    - [Parameters](#parameters-1)
      - [`cluster_backend`](#cluster_backend)
      - [`generate_config_path`](#generate_config_path)
      - [`extra_config`](#extra_config)
      - [`masters`](#masters)
      - [`agents`](#agents)
      - [`public_agents`](#public_agents)
      - [`log_output_live`](#log_output_live)
      - [`files_to_copy_to_installer`](#files_to_copy_to_installer)
      - [`files_to_copy_to_masters`](#files_to_copy_to_masters)
      - [`destroy_on_error`](#destroy_on_error)
      - [`superuser_password`](#superuser_password)
    - [Methods](#methods)
      - [`run_integration_tests(pytest_command)`](#run_integration_testspytest_command)
      - [`destroy()`](#destroy)
      - [`wait_for_dcos()`](#wait_for_dcos)
    - [Attributes](#attributes)
      - [`masters`](#masters-1)
      - [`agents`](#agents-1)
      - [`public_agents`](#public_agents-1)
  - [Nodes](#nodes)
    - [Methods](#methods-1)
      - [`node.run_as_root(log_output_live=False)`](#noderun_as_rootlog_output_livefalse)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

# API

## `dcos_e2e.backend.DCOS_Docker`

This is a backend which can be used to run a `Cluster`.

```python
DCOS_Docker(dcos_docker_path)
```

### Parameters

#### `dcos_docker_path`

The path to a clone of DC/OS Docker.
This clone will be used to create the cluster.

## `dcos_e2e.cluster.Cluster`

```python
Cluster(
    cluster_backend,
    generate_config_path,
    extra_config=None,
    masters=1,
    agents=1,
    public_agents=1,
    log_output_live=False,
    destroy_on_error=True,
    files_to_copy_to_installer=None,
    files_to_copy_to_masters=None,
    superuser_password=None,
)
```

This is a context manager which spins up a cluster.
At the time of writing, this uses DC/OS Docker.

### Parameters

#### `cluster_backend`

The backend to use for the cluster.
Currently, the only supported backend is an instance of `dcos_e2e.backend.DCOS_Docker`.

#### `generate_config_path`

The path to a build artifact to install.

#### `extra_config`

Configuration variables to add to a base configuration.

#### `masters`

The number of master nodes.

#### `agents`

The number of agent nodes.

#### `public_agents`

The number of public agent nodes.

#### `log_output_live`

If set to `True`, the output of processes run on the host to create and manage clusters will be logged.

To see these logs in `pytest` tests, use the `-s` flag.

#### `files_to_copy_to_installer`

A mapping of host paths to paths on the installer node.
These are files to copy from the host to the installer node before installing DC/OS.
Currently on DC/OS Docker the only supported paths on the installer are in the `/genconf` directory.

#### `files_to_copy_to_masters`

A mapping of host paths to paths on the master nodes.
These are files to copy from the host to the master nodes before installing DC/OS.
On DC/OS Docker the files are mounted, read only, to the masters.

#### `destroy_on_error`

If set to `True`, the cluster is destroyed on exit in all cases.
If set to `False`, the cluster is preserved if there is an error.

#### `superuser_password`

The superuser password to use.
This is only relevant to DC/OS Enterprise clusters.
If `extra_config` includes `superuser_password_hash` then that is must be a hash of this password.

### Methods

#### `run_integration_tests(pytest_command)`

Run integration tests on the cluster.

#### `destroy()`

Destroy all nodes in the cluster.

#### `wait_for_dcos()`

Wait for the cluster set up to be complete.

### Attributes

#### `masters`

The `master` nodes in the cluster.

#### `agents`

The agent nodes in the cluster.

#### `public_agents`

The public agent nodes in the cluster.

## Nodes

Commands can be run on nodes in clusters.

### Methods

#### `node.run_as_root(log_output_live=False)`

If `log_output_live` is set to `True`, the output of processes run on the host to create and manage clusters will be logged.

To see these logs in `pytest` tests, use the `-s` flag.

# API

<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [`dcos_e2e.cluster.Cluster`](#dcos_e2eclustercluster)
  - [Parameters](#parameters)
    - [`cluster_backend`](#cluster_backend)
    - [`build_artifact`](#build_artifact)
    - [`extra_config`](#extra_config)
    - [`masters`](#masters)
    - [`agents`](#agents)
    - [`public_agents`](#public_agents)
    - [`log_output_live`](#log_output_live)
    - [`files_to_copy_to_installer`](#files_to_copy_to_installer)
    - [`destroy_on_error`](#destroy_on_error)
    - [`destroy_on_success`](#destroy_on_success)
  - [Methods](#methods)
    - [`run_integration_tests(pytest_command, env=None)`](#run_integration_testspytest_command-envnone)
    - [`destroy()`](#destroy)
    - [`wait_for_dcos()`](#wait_for_dcos)
  - [Attributes](#attributes)
    - [`masters`](#masters-1)
    - [`agents`](#agents-1)
    - [`public_agents`](#public_agents-1)
- [`dcos_e2e.node.Node`](#dcos_e2enodenode)
  - [Parameters](#parameters-1)
    - [`ip_address`](#ip_address)
    - [`ssh_key_path`](#ssh_key_path)
  - [Methods](#methods-1)
    - [`node.run(args, user, log_output_live=False, env=None)`](#noderunargs-user-log_output_livefalse-envnone)
    - [`node.run_as_root(args, log_output_live=False, env=None)`](#noderun_as_rootargs-log_output_livefalse-envnone)
    - [`node.popen(args, user, env=None) -> Popen`](#nodepopenargs-user-envnone---popen)
    - [`node.send_file(local_path, remote_path) -> None`](#nodesend_filelocal_path-remote_path---none)
  - [Attributes](#attributes-1)
    - [`ip_address`](#ip_address-1)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->


## `dcos_e2e.cluster.Cluster`

```python
Cluster(
    cluster_backend,
    build_artifact=None,
    extra_config=None,
    masters=1,
    agents=1,
    public_agents=1,
    log_output_live=False,
    destroy_on_error=True,
    destroy_on_success=True,
    files_to_copy_to_installer=None,
)
```

This is a context manager which spins up a cluster.

### Parameters

#### `cluster_backend`

The backend to use for the cluster.
See [`BACKENDS.md`](./BACKENDS.md) for details.

#### `build_artifact`

The url to a build artifact to install.

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

#### `destroy_on_error`

If set to `True`, the cluster is destroyed on exit if there is an exception raised in the context of the context manager.

#### `destroy_on_success`

If set to `True`, the cluster is destroyed on exit if there is no exception raised in the context of the context manager.

### Methods

#### `run_integration_tests(pytest_command, env=None)`

Run integration tests on the cluster.

To run integration tests on an enterprise cluster, an administrator's username and password must be set as environment variables.
For example:

```
pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_tls.py']

environment_variables = {
    'DCOS_LOGIN_UNAME': 'alice',
    'DCOS_LOGIN_PW': 'password123',
}

cluster.run_integration_tests(
    pytest_command=pytest_command,
    env=environment_variables,
)
```

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

## `dcos_e2e.node.Node`

Commands can be run on nodes in clusters.

```python
Node(ip_address, ssh_key_path)
```

### Parameters

#### `ip_address`

The IP address of the node.

#### `ssh_key_path`

The path to an SSH key which can be used to SSH to the node as the `root` user.

### Methods

#### `node.run(args, user, log_output_live=False, env=None)`

`user` specifies the user that the given command will be run for over SSH.

If `log_output_live` is set to `True`, the output of processes run on the host to create and manage clusters will be logged.

To see these logs in `pytest` tests, use the `-s` flag.

`env` is an optional mapping of environment variable names to values.
These environment variables will be set on the node before running the command specified in `args`.

#### `node.run_as_root(args, log_output_live=False, env=None)`

If `log_output_live` is set to `True`, the output of processes run on the host to create and manage clusters will be logged.

To see these logs in `pytest` tests, use the `-s` flag.

`env` is an optional mapping of environment variable names to values.
These environment variables will be set on the node before running the command specified in `args`.

#### `node.popen(args, user, env=None) -> Popen`

`user` specifies the user that the given command will be run for over SSH.

`env` is an optional mapping of environment variable names to values.
These environment variables will be set on the node before running the command specified in `args`.

The method returns a `Popen` object that can be used to communicate to the underlying subprocess.

#### `node.send_file(local_path, remote_path) -> None`

Copy a file to the node.

### Attributes

#### `ip_address`

The IP address of the node.

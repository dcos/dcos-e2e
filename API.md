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

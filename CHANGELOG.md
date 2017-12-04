<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Changelog](#changelog)
  - [Next](#next)
  - [2017.11.29.0](#201711290)
  - [2017.11.21.0](#201711210)
  - [2017.11.15.0](#201711150)
  - [2017.11.14.0](#201711140)
  - [2017.11.02.0](#201711020)
  - [2017.10.04.0](#201710040)
  - [2017.08.11.0](#201708110)
  - [2017.08.08.0](#201708080)
  - [2017.08.05.0](#201708050)
  - [2017.06.23.0](#201706230)
  - [2017.06.22.0](#201706220)
  - [2017.06.21.1](#201706211)
  - [2017.06.21.0](#201706210)
  - [2017.06.20.0](#201706200)
  - [2017.06.19.0](#201706190)
  - [2017.06.15.0](#201706150)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

# Changelog

## Next

Add basic AWS backend.

## 2017.11.29.0

* Backwards incompatible change: Introduce separate `wait_for_dcos_oss` and `wait_for_dcos_ee` methods.
Both methods improve the boot process waiting time for the corresponding DC/OS version.
* Backwards incompatible change: `run_integration_tests` now requires to call `wait_for_dcos_oss` or `wait_for_dcos_ee` beforehand.

## 2017.11.21.0

* Remove `ExistingCluster` backend and replaced it with simpler `Cluster.from_nodes` method.
* Simplified the default configuration for the Docker backend.
  Notably this no longer contains a default `superuser_username` or `superuser_password_hash`.
* Support `custom_agent_mounts` and `custom_public_agent_mounts` on the Docker backend.

## 2017.11.15.0

* Remove `destroy_on_error` and `destroy_on_success` from `Cluster`.
  Instead, avoid using `Cluster` as a context manager to keep the cluster alive.

## 2017.11.14.0

* Backwards incompatible change: Rename `DCOS_Docker` backend to `Docker` backend.
* Backwards incompatible change: Replace `generate_config_path` with `build_artifact`
that can either be a `Path` or a HTTP(S) URL string. This allows for supporting installation
methods that require build artifacts to be downloaded from a HTTP server.
* Backwards incompatible change: Remove `run_as_root`. Instead require a `default_ssh_user`
for backends to `run` commands over SSH on any cluster `Node` created with this backend.
* Backwards incompatible change: Split the DC/OS installation from the ClusterManager
`__init__` procedure. This allows for installing DC/OS after `Cluster` creation,
and therefore enables decoupling of transfering files ahead of the installation process.
* Backwards incompatible change: Explicit distinction of installtion methods by providing
separate methods for `install_dcos_from_path` and `install_dcos_from_url` instead
of inspecting the type of `build_artifact`.
* Backwards incompatible change: `log_output_live` is no longer an attribute of the `Cluster`
class. It may now be passed separately as a parameter for each output-generating operation.

## 2017.11.02.0

* Added `Node.send_file` to allow files to be copied to nodes.
* Added `custom_master_mounts` to the DC/OS Docker backend.
* Backwards incompatible change: Removed `files_to_copy_to_masters`.
  Instead, use `custom_master_mounts` or `Node.send_file`.

## 2017.10.04.0

* Added Apache2 license.
* Repository moved to `https://github.com/mesosphere/dcos-e2e`.
* Added `run`, which is similar to `run_as_root` but takes a `user` argument.
* Added `popen`, which can be used for running commands asynchronously.

## 2017.08.11.0

* Fix bug where `Node` `repr`s were put into environment variables rather than IP addresses. This prevented some integration tests from working.

## 2017.08.08.0

* Fixed issue which prevented `files_to_copy_to_installer` from working.

## 2017.08.05.0

* The Enterprise DC/OS integration tests now require environment variables describing the IP addresses of the cluster. Now passes these environment variables.

## 2017.06.23.0

* Wait for 5 minutes after diagnostics check.

## 2017.06.22.0

* Account for the name of `3dt` having changed to `dcos-diagnostics`.

## 2017.06.21.1

* Support platforms where `$HOME` is set as `/root`.
* `Cluster.wait_for_dcos` now waits for CA cert to be available.

## 2017.06.21.0

* Add ability to specify a workspace.
* Fixed issue with DC/OS Docker files not existing in the repository.

## 2017.06.20.0

* Vendor DC/OS Docker so a path is not needed.
* If `log_output_live` is set to `True` for a `Cluster`, logs are shown in `wait_for_dcos`.

## 2017.06.19.0

* More storage efficient.
* Removed need to tell `Cluster` whether a cluster is an enterprise cluster.
* Removed need to tell `Cluster` the `superuser_password`.
* Added ability to set environment variables on remote nodes when running commands.

## 2017.06.15.0

* Initial release.

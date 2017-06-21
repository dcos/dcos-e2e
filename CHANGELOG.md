<!--lint disable list-item-indent-->
<!--lint disable list-item-bullet-indent-->
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Changelog](#changelog)
  - [2017.06.21.1](#201706211)
  - [2017.06.21.0](#201706210)
  - [2017.06.20.0](#201706200)
  - [2017.06.19.0](#201706190)
  - [2017.06.15.0](#201706150)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->
<!--lint enable list-item-indent-->
<!--lint enable list-item-bullet-indent-->

# Changelog

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

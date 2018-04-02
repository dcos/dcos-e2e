Versioning, Support and API Stability
=====================================

DC/OS E2E aims to work with DC/OS OSS and DC/OS Enterprise ``master`` branches.
These are moving targets.
For this reason, `CalVer <http://calver.org/>`__ is used as a date at which the repository is last known to have worked with DC/OS OSS and DC/OS Enterprise is the main versioning use.

As well as ``master``, DC/OS E2E supports the following versions:

* DC/OS 1.11
* DC/OS 1.10
* DC/OS 1.9 (not supported on macOS, see :issue:`DCOS_OSS-2176`)

Other versions may work but are not tested.

See `GitHub <https://github.com/mesosphere/dcos-e2e/releases>`_ for releases.

There is no guarantee of API stability at this point.
All backwards incompatible changes will be documented in the :doc:`changelog`.

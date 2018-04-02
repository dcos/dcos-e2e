Versioning, Support and API Stability
=====================================

DC/OS E2E aims to work with DC/OS OSS and DC/OS Enterprise ``master`` branches.
These are moving targets.
For this reason, `CalVer <http://calver.org/>`__ is used as a date at which the repository is last known to have worked with DC/OS OSS and DC/OS Enterprise is the main versioning use.

As well as ``master``, DC/OS E2E supports the following versions:

* DC/OS 1.11
* DC/OS 1.10
* DC/OS 1.9 (limited support, see :ref:`legacy_installers`)

Other versions may work but are not tested.

See `GitHub <https://github.com/mesosphere/dcos-e2e/releases>`_ for releases.

There is no guarantee of API stability at this point.
All backwards incompatible changes will be documented in the :doc:`changelog`.

.. _legacy_installers:

DC/OS 1.9 and below
-------------------

DC/OS installers are not immediately compatible with the BSD sed that ships with macOS. This will be fixed in a future release of DC/OS: https://github.com/dcos/dcos/pull/1571 . For now, use one of the following options:

1. Modify the installer with the following script:

    ```
    sed -e 'H;1h;$!d;x' -e "s/sed '0,/sed '1,/" dcos_generate_config.sh > dcos_generate_config.sh.bak
    mv dcos_generate_config.sh.bak dcos_generate_config.sh
    ```

2. Install GNU sed with Homebrew:

    ```
    brew install gnu-sed --with-default-names
    ```

    Warning: This method will make GNU sed the default sed, which may have unforeseen side-effects.


Versioning, Support and API Stability
=====================================

|project| aims to work with DC/OS OSS and DC/OS Enterprise ``master`` branches.
These are moving targets.
For this reason, `CalVer <https://calver.org/>`__ is used as a date at which the repository is last known to have worked with DC/OS OSS and DC/OS Enterprise is the main versioning use.

As well as ``master``, |project| supports the following versions of DC/OS:

* DC/OS 1.11
* DC/OS 1.10
* DC/OS 1.9 (limited support, see :ref:`legacy_installers`)

Other versions may work but are not tested.

See `GitHub <https://github.com/dcos/dcos-e2e/releases>`_ for releases.

There is no guarantee of API stability at this point.
All backwards incompatible changes will be documented in the :doc:`changelog`.

.. _legacy_installers:

DC/OS 1.9 and below
-------------------

Installers for DC/OS 1.9 and below require a version of ``sed`` that is not compatible with the BSD sed that ships with macOS.
``minidcos docker doctor`` includes a check for compatible ``sed`` versions.

To use these versions of DC/OS with macOS and :paramref:`~dcos_e2e.cluster.Cluster.install_dcos_from_path` with a local installer path, we can either modify the installer or modify the local version of ``sed``.

Modify the installer
^^^^^^^^^^^^^^^^^^^^

The following command replaces an installer named :file:`dcos_generate_config.sh` with a slightly different installer that works with the default ``sed`` on macOS.

.. prompt:: bash
   :substitutions:

   sed \
       -e 'H;1h;$!d;x' \
       -e "s/sed '0,/sed '1,/" \
       dcos_generate_config.sh > dcos_generate_config.sh.bak
   mv dcos_generate_config.sh.bak dcos_generate_config.sh

Change the local version of ``sed``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to use unmodified installers if we use ``GNU sed`` as the system's default ``sed``.
This may have unforeseen side-effects.
This requires `Homebrew`_ to be installed.

.. prompt:: bash
   :substitutions:

   brew install gnu-sed --with-default-names

.. _Homebrew: https://brew.sh

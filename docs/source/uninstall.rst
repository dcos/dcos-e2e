Uninstall
~~~~~~~~~

To uninstall DC/OS E2E, use one of the following methods, depending on how you installed DC/OS E2E.

For ``pip`` installations:

.. code:: sh

   pip3 uninstall -y dcos-e2e

For Homebrew or Linuxbrew installations:

.. code:: sh

   # --force uninstalls all versions of DC/OS E2E which have been installed.
   brew uninstall dcose2e --force

For installations from pre-built packages:

.. code:: sh

   rm -f /usr/local/bin/dcos-docker
   rm -f /usr/local/bin/dcos-vagrant
   rm -f /usr/local/bin/dcos-aws

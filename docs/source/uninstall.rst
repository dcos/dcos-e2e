Uninstall
~~~~~~~~~

To uninstall DC/OS E2E, use one of the following methods, depending on how you installed DC/OS E2E.

.. code:: sh

   pip3 uninstall -y dcos-e2e

.. code:: sh

   # --force uninstalls all versions of DC/OS E2E which have been installed.
   brew uninstall dcose2e --force

.. code:: sh

   rm -rf /usr/local/bin/dcos-docker
   rm -rf /usr/local/bin/dcos-vagrant
   rm -rf /usr/local/bin/dcos-aws

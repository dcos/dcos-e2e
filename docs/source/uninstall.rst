Uninstall
~~~~~~~~~

To uninstall |project|, use one of the following methods, depending on how you installed |project|.

For ``pip`` installations:

.. smart-prompt:: bash

   pip3 uninstall -y dcos-e2e

For Homebrew or Linuxbrew installations:

.. smart-prompt:: bash

   # --force uninstalls all versions of DC/OS E2E which have been installed.
   brew uninstall dcose2e --force

For installations from pre-built packages:

.. smart-prompt:: bash

   rm -f /usr/local/bin/dcos-docker
   rm -f /usr/local/bin/dcos-vagrant
   rm -f /usr/local/bin/dcos-aws

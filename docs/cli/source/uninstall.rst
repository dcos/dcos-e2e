Uninstall
~~~~~~~~~

To uninstall the |project|, use one of the following methods.

For ``pip`` installations:

.. smart-prompt:: bash

   pip3 uninstall -y dcos-e2e

For Homebrew or Linuxbrew installations:

.. smart-prompt:: bash

   # --force uninstalls all versions which have been installed.
   brew uninstall |brewfile-stem| --force

For installations from pre-built packages:

.. smart-prompt:: bash

   rm -f /usr/local/bin/minidcos

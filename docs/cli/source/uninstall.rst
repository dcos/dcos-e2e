Uninstall
~~~~~~~~~

To uninstall the |project|, use one of the following methods.

For ``pip`` installations:

.. substitution-prompt:: bash

   pip3 uninstall -y dcos-e2e

For Homebrew or Linuxbrew installations:

.. substitution-prompt:: bash

   # --force uninstalls all versions of DC/OS E2E which have been installed.
   brew uninstall |brewfile-stem| --force

For installations from pre-built packages:

.. substitution-prompt:: bash

   rm -f /usr/local/bin/dcos-docker
   rm -f /usr/local/bin/dcos-vagrant
   rm -f /usr/local/bin/dcos-aws

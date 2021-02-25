Uninstall
~~~~~~~~~

To uninstall the |project|, use one of the following methods.

For ``pip`` installations:

.. prompt:: bash
   :substitutions:

   pip3 uninstall -y dcos-e2e

For Homebrew or Linuxbrew installations:

.. prompt:: bash
   :substitutions:

   # --force uninstalls all versions which have been installed.
   brew uninstall |brewfile-stem| --force

For installations from pre-built packages:

.. prompt:: bash
   :substitutions:

   rm -f /usr/local/bin/minidcos

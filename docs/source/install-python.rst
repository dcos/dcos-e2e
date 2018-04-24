Library and CLI with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the CLI has been installed with Homebrew, you do not need to install the library to use the CLI.

Requires Python 3.5.2+.

Check the Python version:

.. code:: sh

   python3 --version

Optionally replace ``master`` with a particular version of DC/OS E2E.
The latest release is |release|.
See `available versions <https://github.com/mesosphere/dcos-e2e/tags>`_.

.. code:: sh

    pip3 install git+https://github.com/mesosphere/dcos-e2e.git@master


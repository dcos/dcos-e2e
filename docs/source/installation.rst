Installation
------------

DC/OS E2E consists of a :doc:`library` and a :doc:`cli`.

The CLI works only with the :doc:`docker-backend`, while the library supports multiple :doc:`backends`.
The CLI can be installed with Homebrew on macOS, and the library and CLI can be installed together with ``pip`` on any Linux and macOS.

Windows is not currently supported, but we provide instructions on using DC/OS E2E on Windows with Vagrant on particular :doc:`backends`\ ' documentation.

CLI macOS With Homebrew
~~~~~~~~~~~~~~~~~~~~~~~

To install the CLI on macOS, install `Homebrew`_.

Then install the latest stable version:

.. code:: sh

    brew install https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

To upgrade to a newer version, run the following command:

.. code:: sh

    brew upgrade https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

Or the latest ``master``:

Homebrew installs the dependencies for the latest released version and so installing ``master`` may not work.

.. code:: sh

    brew install --HEAD https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb



Library and CLI with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires Python 3.5.2+.

Optionally replace ``master`` with a particular version of DC/OS E2E.
The latest release is |release|.
See `available versions <https://github.com/mesosphere/dcos-e2e/tags>`_.

.. code:: sh

    pip install git+https://github.com/mesosphere/dcos-e2e.git@master

.. _Homebrew: https://brew.sh

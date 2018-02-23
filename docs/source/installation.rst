Installation
------------

DC/OS E2E consists of a Python library and a CLI.

CLI macOS With Homebrew
~~~~~~~~~~~~~~~~~~~~~~~

To install the CLI on macOS, install `Homebrew`_.

Then install the latest stable version:

.. code:: sh

    brew install https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

Or the latest ``master``:

Homebrew installs the dependencies for the latest released version and so installing ``master`` may not work.

.. code:: sh

    brew install --HEAD https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb


Library and CLI with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires Python 3.5.2+.

Optionally replace ``master`` with a particular version of DC/OS E2E.
The latest release is |release|.

.. code:: sh

    pip install git+https://github.com/mesosphere/dcos-e2e.git@master

.. _Homebrew: https://brew.sh

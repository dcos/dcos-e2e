CLI macOS With Homebrew
~~~~~~~~~~~~~~~~~~~~~~~

To install the CLI on macOS, install `Homebrew`_.

Then install the latest stable version:

.. code:: sh

    brew install https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

To upgrade from an older version, run the following command:

.. code:: sh

    brew upgrade https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

Or the latest ``master``:

Homebrew installs the dependencies for the latest released version and so installing ``master`` may not work.

.. code:: sh

    brew install --HEAD https://raw.githubusercontent.com/mesosphere/dcos-e2e/master/dcosdocker.rb

.. _Homebrew: https://brew.sh

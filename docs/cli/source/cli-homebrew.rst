Homebrew or Linuxbrew
~~~~~~~~~~~~~~~~~~~~~

Install `Homebrew`_ (macOS) or `Linuxbrew`_ (Linux).
Then install the latest stable version:

.. smart-prompt:: bash

    brew install https://raw.githubusercontent.com/|github-owner|/|github-repository|/master/|brewfile-stem|.rb

To upgrade from an older version, run the following command:

.. smart-prompt:: bash

    brew upgrade https://raw.githubusercontent.com/|github-owner|/|github-repository|/master/|brewfile-stem|.rb

Or the latest ``master``:

Homebrew installs the dependencies for the latest released version and so installing ``master`` may not work.

.. smart-prompt:: bash

    brew install --HEAD https://raw.githubusercontent.com/|github-owner|/|github-repository|/master/|brewfile-stem|.rb

.. _Homebrew: https://brew.sh
.. _Linuxbrew: https://linuxbrew.sh

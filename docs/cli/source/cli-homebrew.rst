Homebrew or Linuxbrew
~~~~~~~~~~~~~~~~~~~~~

Install `Homebrew`_ (macOS) or `Linuxbrew`_ (Linux).
Then install the latest stable version:

.. substitution-prompt:: bash

    brew install python
    brew postinstall python
    brew install https://raw.githubusercontent.com/|github-owner|/|github-repository|/master/|brewfile-stem|.rb

To upgrade from an older version, run the following command:

.. substitution-prompt:: bash

    brew install python
    brew postinstall python
    brew upgrade https://raw.githubusercontent.com/|github-owner|/|github-repository|/master/|brewfile-stem|.rb

Or the latest ``master``:

Homebrew installs the dependencies for the latest released version and so installing ``master`` may not work.

.. substitution-prompt:: bash

    brew install python
    brew postinstall python
    brew install --HEAD https://raw.githubusercontent.com/|github-owner|/|github-repository|/master/|brewfile-stem|.rb

.. _Homebrew: https://brew.sh
.. _Linuxbrew: https://linuxbrew.sh

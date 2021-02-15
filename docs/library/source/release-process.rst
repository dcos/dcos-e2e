Release Process
===============

Outcomes
--------

* A new ``git`` tag available to install.
* A release on GitHub.
* An updated `Homebrew`_ recipe.
* A changed Vagrantfile.
* Linux binaries.
* The new version title in the changelog.

Prerequisites
-------------

* ``python3`` on your ``PATH`` set to Python 3.6+.
* Docker available and set up for your user.
* ``virtualenv``.
* Push access to this repository.
* Trust that ``master`` is ready and high enough quality for release.
  This includes the ``Next`` section in ``CHANGELOG.rst`` being up to date.

Perform a Release
-----------------

#. Get a GitHub access token:

   Follow the `GitHub instructions <https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/>`__ for getting an access token.

#. Set environment variables to GitHub credentials, e.g.:

    .. prompt:: bash
       :substitutions:

       export GITHUB_TOKEN=75c72ad718d9c346c13d30ce762f121647b502414

#. Perform a release:

    .. prompt:: bash
       :substitutions:

       export GITHUB_OWNER=|github-owner|
       curl https://raw.githubusercontent.com/"$GITHUB_OWNER"/dcos-e2e/master/admin/release.sh | bash

.. _Homebrew: https://brew.sh/

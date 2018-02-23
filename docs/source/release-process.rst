Release Process
===============

Outcomes
--------

* A new ``git`` tag available to install.
* An updated `Homebrew`_ recipe.

Prerequisites
-------------

* `Homebrew`_ or `Linuxbrew`_.
* ``python3`` on your ``PATH`` set to Python 3.5+.
* Push access to this repository.
* Trust that ``master`` is ready and high enough quality for release.
  This includes the ``Next`` section in ``CHANGELOG.rst`` being up to date.

Preparing For a Release
-----------------------

# Get a GitHub access token:

Follow the `GitHub instructions <https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/>`__ for getting an access token.

# Set environment variables to GitHub credentials, e.g.:

    .. code:: sh

       export GITHUB_TOKEN=75c72ad718d9c346c13d30ce762f121647b502414

# Create a release environment:

    .. code:: sh

       cd $(mktemp -d)
       cd dcos-e2e
       git clone git@github.com:mesosphere/dcos-e2e.git
       virtualenv -p python3 release
       source release/bin/activate
       pip install --editable .[dev]
       python admin/prepare_release.py


#. Commit and push changes.

   .. code:: sh

       git commit -am "Bump version to $DCOS_E2E_RELEASE"
       git push


Release
-------

#. Merge the ``release`` Pull Request.

#. Tag a release:

   Visit https://github.com/mesosphere/dcos-e2e/releases/new.
   Set the "Tag version" to the new version.
   Choose "master" as the target.
   Add the changes from the changelog to the release description.

.. _Homebrew: https://brew.sh/
.. _Linuxbrew: http://linuxbrew.sh/

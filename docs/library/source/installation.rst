Installing |project|
--------------------

.. include:: install-python-build-dependencies.rst

Install dependencies, preferably in a virtual environment.
If you are not in a virtualenv, you may have to use ``sudo`` before the following command, or ``--user`` after ``install``.

.. prompt:: bash
   :substitutions:

    pip3 install --upgrade git+https://github.com/|github-owner|/|github-repository|.git@|release|

Uninstall
~~~~~~~~~

To uninstall |project|, run the following command:

.. prompt:: bash
   :substitutions:

   pip3 uninstall -y dcos-e2e

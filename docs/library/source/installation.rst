Installing |project|
--------------------

Requires Python 3.5.2+.
To avoid interfering with your system's Python, we recommend using a `virtualenv <https://virtualenv.pypa.io/en/stable/>`_.

Check the Python version:

.. smart-prompt:: bash

   python3 --version

On Fedora, install Python development requirements:

.. smart-prompt:: bash

   sudo dnf install -y git python3-devel

On Ubuntu, install Python development requirements:

.. smart-prompt:: bash

   apt install -y gcc python3-dev

If you are not in a virtualenv, you may have to use ``sudo`` before the following command, or ``--user`` after ``install``.

.. smart-prompt:: bash

    pip3 install --upgrade git+https://github.com/|github-owner|/|github-repository|.git@|release|

Uninstall
~~~~~~~~~

To uninstall the |project| library, use the following instructions:

.. smart-prompt:: bash

   pip3 uninstall -y dcos-e2e

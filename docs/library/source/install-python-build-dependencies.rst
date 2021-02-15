.. Note: This is duplicated in the library documentation.

Requires Python 3.6+.
To avoid interfering with your system's Python, we recommend using a `virtualenv <https://virtualenv.pypa.io/en/stable/>`_.

Check the Python version:

.. This has been tested by using:
.. $ docker run -it fedora bash

.. prompt:: bash
   :substitutions:

   python3 --version

On Fedora, install Python development requirements:

.. prompt:: bash
   :substitutions:

   dnf install -y git python3-devel

On Ubuntu, install Python development requirements:

.. This has been tested by using:
.. $ docker run -it vcatechnology/linux-mint bash
.. and
.. $ docker run -it ubuntu bash

.. prompt:: bash
   :substitutions:

   apt update -y && \
   apt install -y software-properties-common && \
   apt upgrade -y python-apt && \
   add-apt-repository -y ppa:deadsnakes/ppa && \
   apt update -y && \
   apt upgrade -y gcc python3-dev python3.6-dev libffi-dev libssl-dev git python3-pip

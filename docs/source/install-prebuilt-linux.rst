CLI on Linux with Prebuilt Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One way to install the CLI on Linux is with a prebuilt package.

* Initial install
  - Stable?


To install or upgrade to the latest stable version:
# TODO if we need to it will be possible to make the version dynamic with Sphinx
e.g. using |release|

TODO: Be careful if the URLs are version specific

.. code:: sh

   curl -O /usr/local/bin/dcos-docker <URL> && \
   chmod +x /usr/local/bin/dcos-docker

   curl -O /usr/local/bin/dcos-vagrant <URL> && \
   chmod +x /usr/local/bin/dcos-vagrant

   curl -O /usr/local/bin/dcos-aws <URL> && \
   chmod +x /usr/local/bin/dcos-aws

Requirements
------------

Amazon Web Services
~~~~~~~~~~~~~~~~~~~

An Amazon Web Services account with sufficient funds must be available.

The AWS credentials for the account must be present either in the environment as environment variables or in the default file system location under :file:`~/.aws/credentials` with a AWS profile in the environment referencing those credentials.

The Mesosphere internal AWS tool `maws`_ automatically stores account specific temporary AWS credentials in the default file system location and exports the corresponding profile into the environment.
After logging in with `maws`_ clusters can be launched using the AWS backend.

For CI deployments long lived credentials are preferred.
It is recommended to use the environment variables method for AWS credentials in that case.

The environment variables are set as follows:

.. code:: sh

   export AWS_ACCESS_KEY_ID=<aws_access_key_id>
   export AWS_SECRET_ACCESS_KEY=<aws_secret_access_key>


The EC2 instances launched by the AWS backend will bring about costs in the order of 24 ct per instance, assuming the fixed cluster lifetime of two hours and ``m4.large`` EC2 instances.

``ssh``
~~~~~~~

The ``ssh`` command must be available.

Operating System
~~~~~~~~~~~~~~~~

The AWS backend has been tested on macOS and on Linux.

It is not expected that it will work out of the box with Windows, see :issue:`QUALITY-1771`.

If your operating system is not supported, it may be possible to use Vagrant, or another Linux virtual machine.

.. _maws: https://github.com/mesosphere/maws

AWS Backend
===========

The AWS backend is used to spin up clusters using EC2 instances on Amazon Web Services, where each instance is a DC/OS node.

.. include:: aws-backend-requirements.rst

DC/OS Installation
------------------

:py:class:`~dcos_e2e.cluster.Cluster`\ s created by the :py:class:`~dcos_e2e.backends.AWS` backend only support installing DC/OS via :py:meth:`~dcos_e2e.cluster.Cluster.install_dcos_from_url`.

This is because the installation method employs a bootstrap node that directly downloads the :paramref:`~dcos_e2e.cluster.Cluster.install_dcos_from_url.build_artifact` from the specified URL.

:py:class:`~dcos_e2e.node.Node`\ s of :py:class:`~dcos_e2e.cluster.Cluster`\ s created by the :py:class:`~dcos_e2e.backends.AWS` backend distinguish between :py:attr:`~dcos_e2e.node.Node.public_ip_address` and :py:attr:`~dcos_e2e.node.Node.private_ip_address`.
The :py:attr:`~dcos_e2e.node.Node.private_ip_address` refers to the internal network of the AWS stack which is also used by DC/OS internally.
The :py:attr:`~dcos_e2e.node.Node.public_ip_address` allows for reaching AWS EC2 instances from the outside e.g. from the ``dcos-e2e`` testing environment.

AWS Regions
-----------

When launching a cluster with Amazon Web Services there are a number of different regions to choose from where the cluster is launched using :paramref:`~dcos_e2e.backends.AWS.aws_region`.
It is recommended to use ``us-west-1`` or ``us-west-2`` to keep the cost low.

See the `AWS Regions and Availability Zones`_ for available regions.

Restricting access to the cluster
---------------------------------

The AWS backend takes a parameter :paramref:`~dcos_e2e.backends.AWS.admin_location`.
This parameter restricts the access to the AWS stack from the outside to a particular IP address range.
The default value ``'0.0.0.0/0'`` will allow accessing the cluster from anywhere.
It is recommended to restrict the address range to a subnet including the public IP of the machine executing tests with the AWS backend.
For example ``<external-ip>/24``.

Accessing cluster nodes
-----------------------

SSH can be used to access cluster nodes for the purpose of debugging if :paramref:`~dcos_e2e.backends.AWS.workspace_dir` is set.
The AWS backend generates a SSH key file ``id_rsa`` in a cluster-specific sub-directory under the :paramref:`~dcos_e2e.backends.AWS.workspace_dir` directory. The sub-directory is named after the unique cluster ID generated during cluster creation. The cluster ID is prefixed with ``dcos-e2e-`` and can be found through the DC/OS UI in the upper left corner or through the CCM UI when using `maws`_ with a Mesosphere AWS account.
Adding this key to the ``ssh-agent`` or manually providing it via the ``-i`` flag after changing its file permissions to ``400`` will allow for connecting to the cluster via the ``ssh`` command.
The SSH user depends on the :paramref:`~dcos_e2e.backends.AWS.linux_distribution` given to the :py:class:`~dcos_e2e.backends.AWS` backend.
For :py:obj:`~dcos_e2e.distributions.Distribution.CENTOS_7` that is ``centos``.

It is important to keep in mind files in the given :paramref:`~dcos_e2e.backends.AWS.workspace_dir` are temporary and are removed when the cluster is destroyed.
If :paramref:`~dcos_e2e.backends.AWS.workspace_dir` is unset the :py:class:`~dcos_e2e.backends.AWS` backend will create a new temporary directory in an operating system specific location.

Cluster lifetime
----------------

The cluster lifetime is fixed at two hours.

If the cluster was launched with `maws`_ (Mesosphere temporary AWS credentials) the cluster can be controlled via `CCM`_.
This allows for extending the cluster lifetime and also for cleaning up the cluster if anything goes wrong.

EC2 instance types
------------------

Currently the AWS backend launches ``m4.large`` instances for all DC/OS nodes.

Unsupported DC/OS versions
--------------------------

The AWS backend does currently not support DC/OS versions below 1.10.
Adding support for DC/OS 1.9 is tracked in :issue:`DCOS-21960`.

Unsupported features
--------------------

The AWS backend does currently not support the :py:class:`~dcos_e2e.cluster.Cluster` feature of copying files to the DC/OS installer by supplying :paramref:`~dcos_e2e.cluster.Cluster.files_to_copy_to_installer`.
The progress on this feature is tracked in :issue:`DCOS-21894`.

Troubleshooting
---------------

In case of an error during the DC/OS installation the journal from each node will be dumped and downloaded to the folder that the tests were executed in.
The logs are prefixed with the installation phase that failed, ``preflight``, ``deploy`` or ``postflight``.

When using temporary credentials it is required to pay attention that the credentials are still valid or renewed when destroying a cluster.
If the credentials are not valid anymore the AWS backend does not delete the public/private key pair generated during cluster creation.
It is therefore recommended to periodically renew temporary AWS credentials when executing tests using the AWS backend.

In rare cases it might also happen that a AWS stack deployment fails with the message ``ROLLBACK_IN_PROGRESS``.
In that case at least one of the EC2 instances failed to come up. Starting a new cluster is the only option then.

Reference
---------

.. autoclass:: dcos_e2e.backends.AWS

.. _CCM: ccm.mesosphere.com
.. _AWS Regions and Availability Zones: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions
.. _dcos-launch: https://github.com/dcos/dcos-launch

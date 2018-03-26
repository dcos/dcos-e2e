AWS Backend
==============

The AWS backend is used to spin up clusters using EC2 instances on Amazon Web Services, where each instance is a DC/OS node.

.. include:: aws-backend-requirements.rst

DC/OS Installation
------------------

``Cluster``\ s created by the AWS backend only support installing DC/OS via ``install_dcos_from_url``.

This is because the installation method employs a bootstrap node that directly downloads the ``build_artifact`` from the specified URL.

``Node``\ s of ``Cluster``\ s created by the AWS backend distinguish between ``public_ip_address`` and ``private_ip_address``. The ``private_ip_address`` refers to the internal network of the AWS stack which is also used by DC/OS internally. The ``public_ip_address`` allows for reaching AWS EC2 instances from the outside e.g. from the ``dcos-e2e`` testing environment.

Restricting access to a cluster
---------------------------------

The AWS backend takes a parameter ``admin_location``. This parameter restricts the access to the AWS stack from the outside to a particular IP address range. The default value ``'0.0.0.0/0'`` will allow accessing the cluster from anywhere. It is recommended to restrict the IP address range to the public IP of the machine executing tests with the AWS backend.

Accessing a cluster
-------------------

SSH is used to access cluster nodes. The ``dcos-e2e`` testing environment provides
tool to run commands on clusters, however for debugging purposes it may be desirable
to access a cluster node manually. The AWS backend generates a key


Cluster lifetime
------------------

The cluster lifetime is fixed at a maximum of two hours, that's because of a limitation of ``dcos-launch`` which is used under the hood. That will most likely change in the future.

If the cluster was launched with ``maws`` (Mesosphere temporary AWS credentials) the cluster can be controlled via CCM at ``ccm.mesosphere.com``. This allows for extending the cluster lifetime and also for cleaning up the cluster if anything goes wrong.

EC2 instance types
------------------

The AWS backend does not offer a choice for EC2 instances. Currently it launches ``x4.large`` instances for DC/OS nodes. Please direct requests for supporting more instance types towards Adam Dangoor.

Unsupported features
--------------------

The AWS backend does currently not support the ``Cluster`` feature of copying files to the DC/OS installer.

Troubleshooting
---------------

In case of an error during the DC/OS installation the journal from each node will be dumped and downloaded to the folder that the tests were executed in. The logs are prefixed with the installation phase that failed, ``preflight``, ``deploy`` or ``postflight``.

When using temporary credentials it is required to pay attention that the credentials are still valid or renewed when deleting a cluster. If the credentials are not valid anymore the AWS backend fails to delete the private keypair generated at cluster creation.
It is therefore recommended to a periodically renew temporary AWS credentials when executing tests using the AWS backend.

Reference
---------

.. autoclass:: dcos_e2e.backends._aws.AWS

.. autoclass:: dcos_e2e.backends._aws.AWSCluster

API
===

.. contents::
   :depth: 2

``dcos_e2e.cluster.Cluster``
----------------------------

.. code:: python

    Cluster(
        cluster_backend,
        masters=1,
        agents=1,
        public_agents=1,
        files_to_copy_to_installer=None,
    )

This is a context manager which spins up a cluster.

Parameters
~~~~~~~~~~

``cluster_backend``
^^^^^^^^^^^^^^^^^^^

The backend to use for the cluster.
See `BACKENDS.md`_ for details.

``masters``
^^^^^^^^^^^

The number of master nodes.

``agents``
^^^^^^^^^^

The number of agent nodes.

``public_agents``
^^^^^^^^^^^^^^^^^

The number of public agent nodes.

``files_to_copy_to_installer``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A mapping of host paths to paths on the installer node.
These are files to copy from the host to the installer node before installing DC/OS.

Methods
~~~~~~~

``install_dcos_from_url(build_artifact, extra_config=None, log_output_live=False)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installs DC/OS on the given cluster using the DC/OS advanced installation method if supported by the backend.
This method spins up a persistent bootstrap host that supplies all dedicated DC/OS hosts with the necessary installation files.
Since the bootstrap host is different from the host initating the cluster creation passing the ``build_artifact`` via URL string saves the time of copying the ``build_artifact`` to the boostrap host.

``build_artifact``
''''''''''''''''''

The HTTP(S) URL string to a build artifact to install.

``extra_config``
''''''''''''''''

Configuration variables to add to a base configuration.

``log_output_live``
'''''''''''''''''''

If set to ``True``, the output of the DC/OS installation process will be logged live.
To see these logs in pytest tests, use the ``-s`` flag.

``install_dcos_from_path(build_artifact, extra_config=None, log_output_live=False)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installs DC/OS on the given cluster using an alternative installation method that uses a ``build_artifact`` stored on the local filesystem.
If supported by a given backend, this method is more efficient than the advanced installation method.

``build_artifact``
''''''''''''''''''

The ``pathlib.Path`` to a build artifact to install.

``extra_config``
''''''''''''''''

Configuration variables to add to a base configuration.

``log_output_live``
'''''''''''''''''''

If set to ``True``, the output of the DC/OS installation process will be logged live.
To see these logs in pytest tests, use the ``-s`` flag.

``run_integration_tests(pytest_command, env=None, log_output_live=False)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run integration tests on the cluster.

To run integration tests on an enterprise cluster, an administrator’s username and password must be set as environment variables.
For example:

.. code:: python

    pytest_command = ['pytest', '-vvv', '-s', '-x', 'test_tls.py']

    environment_variables = {
        'DCOS_LOGIN_UNAME': 'alice',
        'DCOS_LOGIN_PW': 'password123',
    }

    cluster.run_integration_tests(
        pytest_command=pytest_command,
        env=environment_variables,
    )

If set to ``True``, the output of the ``pytest_command`` will be logged live.
To see these logs in pytest tests, use the ``-s`` flag.

``destroy()``
^^^^^^^^^^^^^

Destroy all nodes in the cluster.

``wait_for_dcos_oss()``
^^^^^^^^^^^^^^^^^^^^^^^

Wait for the DC/OS OSS cluster set up to be complete.

``wait_for_dcos_ee(superuser_username, superuser_password)``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Wait for the DC/OS Enterprise cluster set up to be complete.

``superuser_username`` must be set to the cluster’s default superuser username.

``superuser_password`` must be set to the cluster’s default superuser password.

Attributes
~~~~~~~~~~

``masters``
^^^^^^^^^^^

The ``master`` nodes in the cluster.

``agents``
^^^^^^^^^^

The agent nodes in the cluster.

``public_agents``
^^^^^^^^^^^^^^^^^

The public agent nodes in the cluster.

``default_ssh_user``
^^^^^^^^^^^^^^^^^^^^

The default SSH user to access cluster nodes.

Creating a cluster from existing nodes
--------------------------------------

.. code:: python

    Cluster.from_nodes(
        masters,
        agents,
        public_agents,
        default_ssh_user,
    )

Parameters
~~~~~~~~~~

``masters``
^^^^^^^^^^^

A ``set`` of master ``Node``\ s in an existing cluster.

``agents``
^^^^^^^^^^

A ``set`` of agent ``Node``\ s in an existing cluster.

``public_agents``
^^^^^^^^^^^^^^^^^

A ``set`` of public agent ``Node``\ s in an existing cluster.

``default_ssh_user``
^^^^^^^^^^^^^^^^^^^^

The default SSH user to access cluster nodes.

``dcos_e2e.node.Node``
----------------------

Commands can be run on nodes in clusters.

.. code:: python

    Node(public_ip_address, private_ip_address, ssh_key_path)

Parameters
~~~~~~~~~~

``public_ip_address``
^^^^^^^^^^^^^^^^^^^^^

The public IP address of the host represented by this node.

``private_ip_address``
^^^^^^^^^^^^^^^^^^^^^^

The IP address that the DC/OS component on this node uses.

``ssh_key_path``
^^^^^^^^^^^^^^^^

The path to an SSH key which can be used to SSH to the node as the cluster’s ``default_ssh_user`` user.

Methods
~~~~~~~

``node.run(args, user, log_output_live=False, env=None, shell=False) -> CompletedProcess``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``user`` specifies the user that the given command will be run for over SSH.

If ``log_output_live`` is set to ``True``, the output of processes run on the host to create and manage clusters will be logged live.

To see these logs in ``pytest`` tests, use the ``-s`` flag.

``env`` is an optional mapping of environment variable names to values.
These environment variables will be set on the node before running the command specified in ``args``.

``shell`` is a boolean controlling whether the command args should be interpreted as a sequence of literals or as parts of a shell command.
If ``shell=False`` (the default), each argument is passed as a literal value to the command.
If ``shell=True``, the command line is interpreted as a shell command, with a special meaning applied to some characters (e.g. ``$``, ``&&``, ``>``).
This means the caller must quote arguments if they may contain these special characters, including whitespace.

``node.popen(args, user, env=None, shell=False) -> Popen``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``user`` specifies the user that the given command will be run for over SSH.

``env`` is an optional mapping of environment variable names to values.
These environment variables will be set on the node before running the command specified in ``args``.

``shell`` is a boolean controlling whether the command args should be interpreted as a sequence of literals or as parts of a shell command.
If ``shell=False`` (the default), each argument is passed as a literal value to the command.
If ``shell=True``, the command line is interpreted as a shell command, with a special meaning applied to some characters (e.g. ``$``, ``&&``, ``>``).
This means the caller must quote arguments if they may contain these special characters, including whitespace.

The method returns a ``Popen`` object that can be used to communicate to the underlying subprocess.

``node.send_file(local_path, remote_path, user) -> None``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy a file to the node via SSH as the given user.

Attributes
~~~~~~~~~~

``public_ip_address``
^^^^^^^^^^^^^^^^^^^^^

The public IP address of the host represented by this node.

``private_ip_address``
^^^^^^^^^^^^^^^^^^^^^^

The IP address that the DC/OS component on this node uses.

.. _BACKENDS.md: BACKENDS.md

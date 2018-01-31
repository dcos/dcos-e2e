"""
Tests for the Docker backend.
"""

import uuid
from pathlib import Path

# See https://github.com/PyCQA/pylint/issues/1536 for details on why the errors
# are disabled.
import pytest
from passlib.hash import sha512_crypt
from py.path import local  # pylint: disable=no-name-in-module, import-error

from dcos_e2e.backends import Docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.distributions import Distribution


class TestDockerBackend:
    """
    Tests for functionality specific to the Docker backend.
    """

    def test_custom_mounts(self, tmpdir: local) -> None:
        """
        It is possible to mount local files to master nodes.
        """
        local_master_file = tmpdir.join('master_file.txt')
        local_master_file.write('')
        local_agent_file = tmpdir.join('agent_file.txt')
        local_agent_file.write('')
        local_public_agent_file = tmpdir.join('public_agent_file.txt')
        local_public_agent_file.write('')

        master_path = Path('/etc/on_master_nodes.txt')
        agent_path = Path('/etc/on_agent_nodes.txt')
        public_agent_path = Path('/etc/on_public_agent_nodes.txt')

        custom_master_mounts = {
            str(local_master_file): {
                'bind': str(master_path),
                'mode': 'rw',
            },
        }

        custom_agent_mounts = {
            str(local_agent_file): {
                'bind': str(agent_path),
                'mode': 'rw',
            },
        }

        custom_public_agent_mounts = {
            str(local_public_agent_file): {
                'bind': str(public_agent_path),
                'mode': 'rw',
            },
        }

        backend = Docker(
            custom_master_mounts=custom_master_mounts,
            custom_agent_mounts=custom_agent_mounts,
            custom_public_agent_mounts=custom_public_agent_mounts,
        )

        with Cluster(
            cluster_backend=backend,
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            for nodes, path, local_file in [
                (cluster.masters, master_path, local_master_file),
                (cluster.agents, agent_path, local_agent_file),
                (
                    cluster.public_agents, public_agent_path,
                    local_public_agent_file
                ),
            ]:
                for node in nodes:
                    content = str(uuid.uuid4())
                    local_file.write(content)
                    args = ['cat', str(path)]
                    result = node.run(args=args, user=cluster.default_ssh_user)
                    assert result.stdout.decode() == content

    def test_install_dcos_from_url(self, oss_artifact_url: str) -> None:
        """
        The Docker backend requires a build artifact in order
        to launch a DC/OS cluster.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            with pytest.raises(NotImplementedError) as excinfo:
                cluster.install_dcos_from_url(build_artifact=oss_artifact_url)

        expected_error = (
            'The Docker backend does not support the installation of DC/OS '
            'by build artifacts passed via URL string. This is because a more '
            'efficient installation method exists in `install_dcos_from_path`.'
        )

        assert str(excinfo.value) == expected_error


class TestDistributions:
    """
    Tests for setting the Linux distribution.
    """

    def test_default(self, ) -> None:
        """
        The default Linux distribution for a `Node`s is CentOS.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:

            (master, ) = cluster.masters
            cat_cmd = master.run(
                args=['cat /etc/*-release'],
                user=cluster.default_ssh_user,
                shell=True,
            )

        version_info = cat_cmd.stdout
        version_info_lines = [
            line for line in version_info.decode().split('\n') if '=' in line
        ]
        version_data = dict(item.split('=') for item in version_info_lines)

        assert version_data['ID'] == '"centos"'
        assert version_data['VERSION_ID'] == '"7"'

    @pytest.mark.parametrize('linux_distribution', list(Distribution))
    def test_custom_choice(
        self,
        linux_distribution: Distribution,
    ) -> None:
        """
        It is possible to start a cluster with various Linux distributions.
        """
        ids = {
            Distribution.CENTOS_7: '"centos"',
            Distribution.UBUNTU_16_04: 'ubuntu',
            Distribution.COREOS: 'coreos',
            Distribution.FEDORA_23: 'fedora',
            Distribution.DEBIAN_8: 'debian',
        }

        version_ids = {
            Distribution.CENTOS_7: '"7"',
            Distribution.UBUNTU_16_04: '"16.04"',
            Distribution.COREOS: '1298.7.0',
            Distribution.FEDORA_23: '23',
            Distribution.DEBIAN_8: '"8"',
        }

        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
            linux_distribution=linux_distribution,
        ) as cluster:
            (master, ) = cluster.masters
            cat_cmd = master.run(
                args=['cat /etc/*-release'],
                user=cluster.default_ssh_user,
                shell=True,
            )

        version_info = cat_cmd.stdout
        version_info_lines = [
            line for line in version_info.decode().split('\n') if '=' in line
        ]
        version_data = dict(item.split('=') for item in version_info_lines)

        assert version_data['ID'] == ids[linux_distribution]
        assert version_data['VERSION_ID'] == version_ids[linux_distribution]

    def test_coreos_oss(
        self,
        oss_artifact: Path,
    ) -> None:
        """
        DC/OS OSS can start up on CoreOS.
        """
        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=1,
            public_agents=0,
            linux_distribution=Distribution.COREOS,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=oss_artifact,
                log_output_live=True,
            )
            cluster.wait_for_dcos_oss()

    def test_coreos_enterprise(
        self,
        enterprise_artifact: Path,
        license_key_contents: str,
    ) -> None:
        """
        DC/OS Enterprise can start up on CoreOS.
        """
        superuser_username = str(uuid.uuid4())
        superuser_password = str(uuid.uuid4())
        config = {
            'superuser_username': superuser_username,
            'superuser_password_hash': sha512_crypt.hash(superuser_password),
            'fault_domain_enabled': False,
            'license_key_contents': license_key_contents,
        }

        with Cluster(
            cluster_backend=Docker(),
            masters=1,
            agents=0,
            public_agents=0,
            linux_distribution=Distribution.COREOS,
        ) as cluster:
            cluster.install_dcos_from_path(
                build_artifact=enterprise_artifact,
                extra_config=config,
                log_output_live=True,
            )
            cluster.wait_for_dcos_ee(
                superuser_username=superuser_username,
                superuser_password=superuser_password,
            )

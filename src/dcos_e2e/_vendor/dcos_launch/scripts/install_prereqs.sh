#!/usr/bin/env bash

# Exit on error, unset variable, or error in pipe chain
set -o errexit -o nounset -o pipefail

# For setenforce & xfs_info
PATH=$PATH:/usr/sbin:/sbin

echo "Validating distro..."
distro="$(source /etc/os-release && echo "${ID}")"
if [[ "${distro}" == 'coreos' ]]; then
  echo "Distro: CoreOS"
  echo "CoreOS includes all prerequisites by default." >&2
  exit 0
elif [[ "${distro}" == 'rhel' ]]; then
  echo "Distro: RHEL"
elif [[ "${distro}" == 'centos' ]]; then
  echo "Distro: CentOS"
else
  echo "Distro: ${distro}"
  echo "Error: Distro ${distro} is not supported. Only CoreOS, RHEL, and CentOS are supported." >&2
  exit 1
fi

echo "Validating distro version..."
# CentOS & RHEL < 7 have inconsistent release file locations
distro_major_version="$(source /etc/os-release && echo "${VERSION_ID}" | sed -e 's/^\([0-9][0-9]*\).*$/\1/')"
if [[ ${distro_major_version} -lt 7 ]]; then
  echo "Error: Distro version ${distro_major_version} is not supported. Only >= 7 is supported." >&2
  exit 1
fi
# CentOS & RHEL >= 7 both have the full version in /etc/redhat-release
distro_minor_version="$(cat /etc/redhat-release | sed -e 's/[^0-9]*[0-9][0-9]*\.\([0-9][0-9]*\).*/\1/')"
echo "Distro Version: ${distro_major_version}.${distro_minor_version}"
if [[ ${distro_major_version} -eq 7 && ${distro_minor_version} -lt 2 ]]; then
  echo "Error: Distro version ${distro_major_version}.${distro_minor_version} is not supported. "\
"Only >= 7.2 is supported." >&2
  exit 1
fi

echo "Validating kernel version..."
kernel_major_version="$(uname -r | sed -e 's/\([0-9][0-9]*\).*/\1/')"
kernel_minor_version="$(uname -r | sed -e "s/${kernel_major_version}\.\([0-9][0-9]*\).*/\1/")"
echo "Kernel Version: ${kernel_major_version}.${kernel_minor_version}"
if [[ ${kernel_major_version} -lt 3 ]] ||
   [[ ${kernel_major_version} -eq 3 && ${kernel_minor_version} -lt 10 ]]; then
  echo -n "Error: Kernel version ${kernel_major_version}.${kernel_minor_version} is not supported. " >&2
  echo "Only >= 3.10 is supported." >&2
  exit 1
fi

echo "Validating kernel modules..."
if ! lsmod | grep -q overlay; then
  echo "Enabling OverlayFS kernel module..."
  # Enable now
  sudo modprobe overlay
  # Load on reboot via systemd
  sudo tee /etc/modules-load.d/overlay.conf <<-'EOF'
overlay
EOF
fi

echo "Detecting Docker..."
if hash docker 2>/dev/null; then
  docker_client_version="$(docker --version | sed -e 's/Docker version \(.*\),.*/\1/')"
  echo "Docker Client Version: ${docker_client_version}"

  if ! sudo docker info &>/dev/null; then
    echo "Docker Server not found. Please uninstall Docker and try again." >&2
    exit 1
  fi

  docker_server_version="$(sudo docker info | grep 'Server Version:' | sed -e 's/Server Version: \(.*\)/\1/')"
  echo "Docker Server Version: ${docker_server_version}"

  if [[ "${docker_client_version}" != "${docker_server_version}" ]]; then
    echo "Docker Server and Client versions do not match. Please uninstall Docker and try again." >&2
    exit 1
  fi

  # Require Docker >= 1.11
  docker_major_version="$(echo "${docker_server_version}" | sed -e 's/\([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\1/')"
  docker_minor_version="$(echo "${docker_server_version}" | sed -e 's/\([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\2/')"
  if [[ ${docker_major_version} -lt 1 ]] ||
     [[ ${docker_major_version} -eq 1 && ${docker_minor_version} -lt 11 ]]; then
    echo -n "Docker version ${docker_major_version}.${docker_minor_version} not supported. " >&2
    echo "Please uninstall Docker and try again." >&2
    exit 1
  fi

  install_docker='false'
else
  echo "Docker not found (install queued)"
  install_docker='true'
fi

echo "Validating Docker Data Root..."
if [[ "${install_docker}" == 'true' ]]; then
  docker_data_root="/var/lib/docker"
else
  docker_data_root="$(sudo docker info | grep 'Docker Root Dir:' | sed -e 's/Docker Root Dir: \(.*\)/\1/')"
fi
echo "Docker Data Root: ${docker_data_root}"
sudo mkdir -p "${docker_data_root}"

file_system="$(sudo df --output=fstype "${docker_data_root}" | tail -1)"
echo "File System: ${file_system}"
if [[ "${file_system}" != 'xfs' ]] || ! sudo xfs_info "${docker_data_root}" | grep -q 'ftype=1'; then
  echo "Error: "${docker_data_root}" must use XFS provisioned with ftype=1 to avoid known issues with OverlayFS." >&2
  exit 1
fi

function yum_install() {
  local cmd="$1"
  echo "Validating ${cmd}..."
  if ! hash "${cmd}" 2>/dev/null; then
    echo "Installing ${cmd}..."
    sudo yum install -y ${cmd}
  fi
  # print installed version
  rpm -q "${cmd}"
}

echo "Installing Utilities..."
yum_install wget
yum_install curl
yum_install git
yum_install unzip
yum_install xz
yum_install ipset
yum_install bind-utils  # required by dcos-iam-ldap-sync

echo "Validating SELinux..."
if [[ "$(getenforce)" == "Enforcing" ]]; then
  echo "Disabling enforcement..."
  sudo setenforce 0
fi
if ! grep -q '^SELINUX=disabled' /etc/sysconfig/selinux; then
  echo "Disabling SELinux..."
  sudo sed -i --follow-symlinks 's/^SELINUX=.*/SELINUX=disabled/g' /etc/sysconfig/selinux
fi

if [[ "${install_docker}" == 'true' ]]; then
  echo "Installing Docker..."

  # Add Docker Yum Repo
  sudo tee /etc/yum.repos.d/docker.repo <<-'EOF'
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/centos/7
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF

  # Add Docker systemd service
  sudo mkdir -p /etc/systemd/system/docker.service.d
  sudo tee /etc/systemd/system/docker.service.d/override.conf <<- EOF
[Service]
Restart=always
StartLimitInterval=0
RestartSec=15
ExecStartPre=-/sbin/ip link del docker0
ExecStart=
ExecStart=/usr/bin/dockerd --storage-driver=overlay --data-root=${docker_data_root}
EOF

  # Install and enable Docker
  sudo yum install -y docker-engine-17.05.0.ce docker-engine-selinux-17.05.0.ce
  sudo systemctl start docker
  sudo systemctl enable docker
fi

if ! sudo getent group nogroup >/dev/null; then
  echo "Creating 'nogroup' group..."
  sudo groupadd nogroup
fi

echo "Prerequisites installed."

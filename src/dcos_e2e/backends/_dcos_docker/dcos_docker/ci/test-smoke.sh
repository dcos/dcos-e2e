#!/usr/bin/env bash

# Performs smoke testing of DC/OS Docker.
#
# Options:
#   LOG_LINES    Number of log lines to export for each node (exports all, if unset)
#
# Usage:
# $ ci/test-e2e.sh

set -o errexit
set -o nounset
set -o pipefail
set -o xtrace

if [[ -n "${LOG_LINES:-}" ]]; then
  LOG_LINES_ARG="-n=${LOG_LINES}"
else
  LOG_LINES_ARG=""
fi

# Require bash 4+ for associative arrays
if [[ ${BASH_VERSINFO[0]} -lt 4 ]]; then
  echo "Requires Bash 4+" >&2
  exit 1
fi

project_dir=$(cd "$(dirname "${BASH_SOURCE}")/.." && pwd -P)
cd "${project_dir}"

# Log dependency versions
docker --version
jq --version
echo "${BASH_VERSINFO[@]}"

# Check for running containers
docker ps

# Destroy All VMs
make clean

# Destroy All VMs on exit
function cleanup() {
  ci/dcos-logs.sh ${LOG_LINES_ARG} || true
  make clean
}
trap cleanup EXIT

# Auto-configure
./configure --auto

# Cassandra requires 3 private agents
sed 's/^AGENTS :=.*/AGENTS := 3/' make-config.mk > make-config.mk.bak
mv make-config.mk.bak make-config.mk

# Deploy
make

# Wait
make postflight POSTFLIGHT_PROGRESS=--progress=time

# Cleanup hosts on exit
function cleanup2() {
  make clean-hosts
  cleanup
}
trap cleanup2 EXIT

# Setup /etc/hosts (password required)
make hosts

# Test API (unauthenticated)
curl --fail --location --silent --show-error --verbose http://m1.dcos/dcos-metadata/dcos-version.json

# Install CLI
DCOS_CLI="$(ci/dcos-install-cli.sh)"
echo "${DCOS_CLI}"

# Delete CLI on exit
function cleanup3() {
  # only use sudo if required
  if [[ -w "$(dirname "${DCOS_CLI}")" ]]; then
    rm -rf "${DCOS_CLI}"
  else
    sudo rm -rf "${DCOS_CLI}"
  fi
  cleanup2
}
trap cleanup3 EXIT

# Create User
DCOS_USER="test@example.com"
ci/dcos-create-user.sh "${DCOS_USER}"

# Login
DCOS_ACS_TOKEN="$(ci/dcos-login.sh "${DCOS_USER}")"
dcos config set core.dcos_acs_token "${DCOS_ACS_TOKEN}"

# Install & test Oinker
ci/test-oinker.sh

# Detect URL
DCOS_URL="$(dcos config show core.dcos_url)"

# Test GUI (authenticated)
curl --fail --location --silent --show-error --verbose -H "Authorization: token=${DCOS_ACS_TOKEN}" ${DCOS_URL} -o /dev/null

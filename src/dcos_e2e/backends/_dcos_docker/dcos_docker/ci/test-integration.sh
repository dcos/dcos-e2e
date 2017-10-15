#!/usr/bin/env bash

# Performs smoke testing of DC/OS Docker.
#
# Options:
#   LOG_LINES    Number of log lines to export for each node (exports all, if unset)
#
# Usage:
# $ ci/test-e2e.sh

set -o errexit -o nounset -o pipefail -o xtrace

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

# Destroy all containers
make clean

# Destroy all containers on exit
function cleanup() {
  ci/dcos-logs.sh ${LOG_LINES_ARG} || true
  make clean
}
trap cleanup EXIT

# Auto-configure
./configure --auto

# Networking integration tests require 2 private agents
sed 's/^AGENTS :=.*/AGENTS := 2/' make-config.mk > make-config.mk.bak
mv make-config.mk.bak make-config.mk

# Unbuffered postflight output
tee >> make-config.mk << EOM
POSTFLIGHT_PROGRESS := --progress=time
EOM

# Verbose test output
TEST_ARGS='-vv'
# Report test results as junit xml
TEST_ARGS+=' --junitxml=test-junit.xml'
# Skip CCM-only tests
TEST_ARGS+=' -m "not ccm"'
# Use teamcity-messages to fold unbuffered stdout/stderr
if [[ -n "${TEAMCITY_VERSION:-}" ]]; then
  TEST_ARGS+=' --teamcity --capture=no'
fi
# Configure integration tests
tee >> make-config.mk << EOM
DCOS_PYTEST_CMD := py.test ${TEST_ARGS}
EOM

# Deploy
make

# Wait
make postflight

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

# Add test user (required to be added when not the first user)
# TODO: only required for OSS DC/OS
ci/dcos-create-user.sh "albert@bekstil.net"

# Delete CLI on exit
function cleanup3() {
  # Copy out test results
  docker cp dcos-docker-master1:/opt/mesosphere/active/dcos-integration-test/test-junit.xml test-junit.xml || true
  cleanup2
}
trap cleanup3 EXIT

# Integration tests
make test

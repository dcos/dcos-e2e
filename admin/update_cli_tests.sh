#!/usr/bin/env bash

# There are CLI tests which check that --help output for various commands is
# as expected.
#
# Expected output is stored in files.
# This script updates those files.
#
# The expected use of this script:
#  * Make a change which changes expected help text for CLI commands
#  * Run this script
#  * Inspect the diff to check that changes are as expected
#  * Commit and push

set -ex

export FIX_CLI_TESTS=1

mkdir -p tests/test_cli/test_minidcos/help_outputs
git rm -f tests/test_cli/test_minidcos/help_outputs/*.txt || true
pytest tests/test_cli/test_minidcos/test_cli.py::TestHelp::test_help || true
git add tests/test_cli/test_minidcos/help_outputs/*.txt

mkdir -p tests/test_cli/test_dcos_docker/help_outputs
git rm -f tests/test_cli/test_dcos_docker/help_outputs/*.txt || true
pytest tests/test_cli/test_dcos_docker/test_cli.py::TestHelp::test_help || true
git add tests/test_cli/test_dcos_docker/help_outputs/*.txt

mkdir -p tests/test_cli/test_dcos_vagrant/help_outputs
git rm -f tests/test_cli/test_dcos_vagrant/help_outputs/*.txt || true
pytest tests/test_cli/test_dcos_vagrant/test_cli.py::TestHelp::test_help || true
git add tests/test_cli/test_dcos_vagrant/help_outputs/*.txt

mkdir -p tests/test_cli/test_dcos_aws/help_outputs
git rm -f tests/test_cli/test_dcos_aws/help_outputs/*.txt || true
pytest tests/test_cli/test_dcos_aws/test_cli.py::TestHelp::test_help || true
git add tests/test_cli/test_dcos_aws/help_outputs/*.txt

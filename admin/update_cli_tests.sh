#!/usr/bin/env bash

set -ex

mkdir tests/test_cli/test_dcos_docker/help_outputs || true
git rm -f tests/test_cli/test_dcos_docker/help_outputs/*.txt || true
export FIX_CLI_TESTS=1
pytest tests/test_cli/test_dcos_docker/test_cli.py::TestHelp::test_help || true
git add tests/test_cli/test_dcos_docker/help_outputs/*.txt

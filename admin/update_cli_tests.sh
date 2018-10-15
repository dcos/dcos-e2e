#!/usr/bin/env bash

set -ex

git rm -r tests/test_cli/test_dcos_docker/test_cli/help_output
export FIX_CLI_TESTS=1
pytest tests/test_cli/test_dcos_docker/test_cli::TestHelp::test_help
git add tests/test_cli/test_dcos_docker/test_cli/help_output/*

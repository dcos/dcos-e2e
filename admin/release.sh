#!/usr/bin/env bash

set -ex

# Perform a release.
# See the release process documentation for details.
cd "$(mktemp -d)"
git clone git@github.com:"${GITHUB_OWNER}"/dcos-e2e.git
cd dcos-e2e
virtualenv -p python3 release
source release/bin/activate
# Use pip with older, more forgiving dependency resolution
pip install --upgrade 'pip<20.3'
pip install --editable '.[dev]'
PYTHONPATH=${PWD} python admin/release.py "${GITHUB_TOKEN}" "${GITHUB_OWNER}"

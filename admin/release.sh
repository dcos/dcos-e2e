#!/usr/bin/env bash

# Perform a release.
# See the release process documentation for details.
cd "$(mktemp -d)"
git clone git@github.com:mesosphere/dcos-e2e.git
cd dcos-e2e
virtualenv -p python3 release
source release/bin/activate
pip install --editable .[dev]
python admin/release.py

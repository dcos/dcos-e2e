#!/usr/bin/env bash

set -ex

# Update vendored packages.

git rm -rf src/dcos_e2e/_vendor/ || true
rm -rf src/dcos_e2e/_vendor || true
git rm -rf src/dcos_e2e_cli/_vendor/ || true
rm -rf src/dcos_e2e_cli/_vendor || true
python admin/update_vendored_packages.py
git add src/dcos_e2e/_vendor
git add src/dcos_e2e_cli/_vendor
git commit -m "Update vendored packages"

#!/usr/bin/env bash

# Update vendored packages.

git rm -rf src/dcos_e2e/_vendor/
rm -rf src/dcos_e2e/_vendor
python admin/update_vendored_packages.py
git add src/dcos_e2e/_vendor
git commit -m "Update vendored packages"

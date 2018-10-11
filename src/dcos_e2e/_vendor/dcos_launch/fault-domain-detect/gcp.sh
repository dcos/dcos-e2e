#!/bin/sh
set -o nounset -o errexit

# Get COREOS COREOS_PRIVATE_IPV4
if [ -e /etc/environment ]
then
  set -o allexport
  source /etc/environment
  set +o allexport
fi

BODY=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone 2>/dev/null)

ZONE=$(echo "$BODY" | sed 's@^projects/.*/zones/\(.*\)$@\1@')
REGION=$(echo "$ZONE" | sed 's@\(.*-.*\)-.*@\1@')

echo "{\"fault_domain\":{\"region\":{\"name\": \"$REGION\"},\"zone\":{\"name\": \"$ZONE\"}}}"

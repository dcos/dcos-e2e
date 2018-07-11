#!/bin/sh
# Example ip-detect script using an external authority
# Uses the GCE metadata server to get the node's external
# ipv4 address

/opt/mesosphere/bin/curl -fsSL -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip

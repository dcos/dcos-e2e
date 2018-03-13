FROM quay.io/shift/coreos:stable-1298.7.0

# This works around a systemd bug.
# See https://jira.mesosphere.com/browse/DCOS_OSS-1240
COPY systemd-journald-init.service /lib/systemd/system/
RUN systemctl enable systemd-journald-init.service || true

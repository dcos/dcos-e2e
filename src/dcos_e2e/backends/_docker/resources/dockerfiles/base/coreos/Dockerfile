FROM quay.io/shift/coreos:stable-1298.7.0

# This works around a systemd bug.
# See https://jira.mesosphere.com/browse/DCOS_OSS-1240
RUN <<EOR
    cat < /lib/systemd/system/ << EOF
    [Unit]
    Description=Initialize /run/log/journal ACLs
    After=systemd-journald.service

    [Service]
    Type=oneshot
    ExecStart=/usr/bin/systemd-tmpfiles --create --prefix /run/log/journal

    [Install]
    WantedBy=default.target
    EOF
EOR
RUN systemctl enable systemd-journald-init.service || true

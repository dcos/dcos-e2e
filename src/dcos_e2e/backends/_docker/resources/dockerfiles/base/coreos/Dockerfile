FROM quay.io/shift/coreos:stable-1298.7.0

# This works around a systemd bug.
# See https://jira.mesosphere.com/browse/DCOS_OSS-1240
RUN echo '[Unit]' >> /lib/systemd/system/systemd-journald-init.service
RUN echo 'Description=Initialize /run/log/journal ACLs' >> /lib/systemd/system/systemd-journald-init.service
RUN echo 'After=systemd-journald.service' >> /lib/systemd/system/systemd-journald-init.service
RUN echo '' >> /lib/systemd/system/systemd-journald-init.service
RUN echo '[Service]' >> /lib/systemd/system/systemd-journald-init.service
RUN echo 'Type=oneshot' >> /lib/systemd/system/systemd-journald-init.service
RUN echo 'ExecStart=/usr/bin/systemd-tmpfiles --create --prefix /run/log/journal' >> /lib/systemd/system/systemd-journald-init.service
RUN echo '' >> /lib/systemd/system/systemd-journald-init.service
RUN echo '[Install]' >> /lib/systemd/system/systemd-journald-init.service
RUN echo 'WantedBy=default.target' >> /lib/systemd/system/systemd-journald-init.service
RUN systemctl enable systemd-journald-init.service || true

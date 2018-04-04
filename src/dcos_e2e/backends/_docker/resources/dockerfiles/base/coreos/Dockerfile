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

# This works around https://github.com/coreos/bugs/issues/1591.
RUN mkdir -p /etc/systemd/system/sshd.service.d
RUN touch /etc/systemd/system/sshd.service.d/override.conf
RUN echo '[Service]' >> /etc/systemd/system/sshd.service.d/override.conf
RUN echo 'Restart=always' >> /etc/systemd/system/sshd.service.d/override.conf
# Without this we get:
# sshd.service: Start request repeated too quickly.
# Failed to start OpenSSH server daemon.
# sshd.service: Unit entered failed state.
# sshd.service: Failed with result 'start-limit-hit'.
RUN echo 'RestartSec=3s' >> /etc/systemd/system/sshd.service.d/override.conf

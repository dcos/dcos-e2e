FROM centos:7

RUN yum install -y \
		bash-completion \
		bind-utils \
		btrfs-progs \
		ca-certificates \
		curl \
		gettext \
		git \
		iproute \
		ipset \
		iptables \
		iputils \
		libcgroup \
		libselinux-utils \
		net-tools \
		openssh-client \
		openssh-server \
		sudo \
		systemd \
		tar \
		tree \
		unzip \
		which \
                # This is needed to run DC/OS E2E on hosts with XFS.
		xfsprogs \
		xz \
&& ( \
cd /lib/systemd/system/sysinit.target.wants/; \
for i in *; do \
if [ "$i" != "systemd-tmpfiles-setup.service" ]; then \
rm -f $i; \
fi \
done \
) \
&& rm -f /lib/systemd/system/multi-user.target.wants/* \
&& rm -f /etc/systemd/system/*.wants/* \
&& rm -f /lib/systemd/system/local-fs.target.wants/* \
&& rm -f /lib/systemd/system/sockets.target.wants/*udev* \
&& rm -f /lib/systemd/system/sockets.target.wants/*initctl* \
&& rm -f /lib/systemd/system/anaconda.target.wants/* \
&& rm -f /lib/systemd/system/basic.target.wants/* \
&& rm -f /lib/systemd/system/graphical.target.wants/* \
&& ln -vf /lib/systemd/system/multi-user.target /lib/systemd/system/default.target

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

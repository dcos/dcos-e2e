FROM ubuntu:xenial

RUN apt-get update \
	&& apt-get install -y \
		aufs-tools \
		bash-completion \
		btrfs-tools \
		ca-certificates \
		curl \
		debianutils \
		dbus \
		gawk \
		gettext \
		git \
		iproute \
		ipset \
		iptables \
		iputils-ping \
		libcgroup-dev \
		libpopt0 \
		locales \
		net-tools \
		openssh-client \
		openssh-server \
		sudo \
		systemd \
		tar \
		tree \
		unzip \
		xfsprogs \
		xz-utils \
	&& rm -rf /var/lib/apt/lists/* \
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
RUN ln -s /bin/mkdir /usr/bin/mkdir
RUN ln -s /bin/ln /usr/bin/ln
RUN ln -s /bin/tar /usr/bin/tar
RUN ln -s /usr/sbin/useradd /usr/bin/useradd
RUN ln -s /usr/sbin/groupadd /usr/bin/groupadd
RUN ln -s /bin/systemd-tmpfiles /usr/bin/systemd-tmpfiles

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

RUN locale-gen en_US.UTF-8

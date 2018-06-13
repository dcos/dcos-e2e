FROM mesosphere/dcos-docker:base

ENV TERM xterm
ENV LANG en_US.UTF-8

RUN rpm --import "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xee6d536cf7dc86e2d7d56f59a178ac6c6238f52e"
RUN yum-config-manager --add-repo "https://packages.docker.com/1.13/yum/repo/main/centos/7"
RUN yum install -y "docker-engine-1.13.1.cs9"

RUN groupadd -r nogroup \
	&& (gpasswd -a "root" docker || true) \
	&& rm -f /etc/securetty \
	&& ln -vf /bin/true /usr/sbin/modprobe \
	&& ln -vf /bin/true /sbin/modprobe

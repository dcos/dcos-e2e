# This is a method of installing Docker, and setting up Docker-in-Docker which
# works across the platforms we currently support.
#
# CoreOS does not provide a package manager.
# CentOS and Ubuntu include different package managers.

FROM mesosphere/dcos-docker:base

ENV TERM xterm
ENV LANG en_US.UTF-8
ARG DOCKER_URL

RUN curl -sSL --fail "${DOCKER_URL}" | tar xvzf - -C /usr/bin/ --strip 1 \
	&& chmod +x /usr/bin/docker* \
	&& (getent group nogroup || groupadd -r nogroup) \
	&& (getent group docker || groupadd -r docker) \
	&& (gpasswd -a "root" docker || true) \
	&& rm -f /etc/securetty \
	&& ln -vf /bin/true /usr/sbin/modprobe \
	&& ln -vf /bin/true /sbin/modprobe

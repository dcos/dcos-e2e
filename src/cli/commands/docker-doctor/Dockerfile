FROM quay.io/shift/coreos:stable-1298.7.0

ENV TERM xterm
ENV LANG en_US.UTF-8
ARG DOCKER_URL

RUN curl -sSL --fail "https://get.docker.com/builds/Linux/x86_64/docker-1.13.1.tgz" | tar xvzf - -C /usr/bin/ --strip 1 \
	&& chmod +x /usr/bin/docker* \
	&& (getent group nogroup || groupadd -r nogroup) \
	&& (getent group docker || groupadd -r docker) \
	&& (gpasswd -a "root" docker || true) \
	&& rm -f /etc/securetty \
	&& ln -vf /bin/true /usr/sbin/modprobe \
	& ln -vf /bin/true /sbin/modprobe \
    && mkdir -p /lib/systemd/system \
    && /usr/bin/docker daemon -D -s overlay

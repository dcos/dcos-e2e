FROM mesosphere/dcos-docker:base

ENV DOCKER_VERSION 17.12.1-ce
ENV TERM xterm
ENV LANG en_US.UTF-8

# install dind and docker
RUN curl -sSL --fail "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" | tar xvzf - -C /usr/bin/ --strip 1 \
	&& curl -sSL --fail "https://raw.githubusercontent.com/docker/docker-ce/17.12/components/cli/contrib/completion/bash/docker" -o /etc/bash_completion.d/docker \
	&& chmod +x /usr/bin/docker* \
	&& groupadd -r nogroup \
	&& groupadd -r docker \
	&& gpasswd -a "root" docker || true \
	&& rm -f /etc/securetty \
	&& ln -vf /bin/true /usr/sbin/modprobe \
	&& ln -vf /bin/true /sbin/modprobe

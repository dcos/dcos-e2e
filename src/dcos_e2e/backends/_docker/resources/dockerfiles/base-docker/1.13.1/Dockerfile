FROM mesosphere/dcos-docker:base

ENV DOCKER_VERSION 1.13.1
ENV TERM xterm
ENV LANG en_US.UTF-8

RUN rpm --import "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xee6d536cf7dc86e2d7d56f59a178ac6c6238f52e"
RUN yum-config-manager --add-repo "https://packages.docker.com/1.13/yum/repo/main/centos/7"
RUN yum install -y "docker-engine-1.13.1.cs9"

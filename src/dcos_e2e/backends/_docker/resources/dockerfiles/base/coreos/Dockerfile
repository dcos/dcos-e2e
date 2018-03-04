FROM quay.io/shift/coreos:stable-1298.7.0

# systemd needs a different stop signal
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]

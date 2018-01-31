import sys
import traceback

import docker

image = 'mesosphere/dcos-docker:base-docker'
count = 0

for i in range(100):
    sys.stderr.write('%2d...' % i)
    client = docker.from_env(version='auto')
    try:
        client.images.pull(image)
        sys.stderr.write('OK\n')
    except Exception:
        count += 1
        sys.stderr.write('ERROR\n')
        traceback.print_exc()
    client.images.remove(image)

sys.exit(count)

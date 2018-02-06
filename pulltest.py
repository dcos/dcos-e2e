import sys
import traceback

import docker
from dcos_e2e.cluster import Cluster
from dcos_e2e.backends import Docker

count = 0

for i in range(200):
    sys.stderr.write('%3d...\n' % i)
    client = docker.from_env(version='auto')
    client.images.prune()
    try:
        with Cluster(cluster_backend=Docker(), agents=0, public_agents=1):
            pass
    except Exception:
        count += 1
        traceback.print_exc()

sys.exit(count)

"""
XXX
"""

def clean():
    client = docker_client()

    filters = {
        'label': [
            '{key}={value}'.format(
                key=NODE_TYPE_LABEL_KEY,
                value=NODE_TYPE_LOOPBACK_SIDECAR_LABEL_VALUE,
            ),
        ],
    }
    loopback_sidecars = client.containers.list(filters=filters)
    for loopback_sidecar in loopback_sidecars:
        DockerLoopbackVolume.destroy(container=loopback_sidecar)

    node_filters = {
        'name': 'dcos-e2e'
    }

    node_containers = containers.list(filters=filters, all=True)

    for container in containers:
        container.stop()
        container.remove(v=True)

	- docker network rm $$(docker network ls -q --filter="name=dcos-e2e") | :

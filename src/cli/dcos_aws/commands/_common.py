"""
Common code for dcos-docker CLI modules.
"""

CLUSTER_ID_TAG_KEY = 'dcos_e2e.cluster_id'

def existing_cluster_ids() -> Set[str]:
    """
    Return the IDs of existing clusters.
    """
    # TODO Maybe hardcode region for now?
    # Take option later?
    client = docker_client()
    filters = {'label': CLUSTER_ID_LABEL_KEY}
    containers = client.containers.list(filters=filters)
    return set(
        container.labels[CLUSTER_ID_LABEL_KEY] for container in containers
    )

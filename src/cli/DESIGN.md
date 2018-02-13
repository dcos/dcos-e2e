# CLI

## Goals

* Match DC/OS Docker in terms of what users can achieve.
* Be pleasant to use.
* Be pleasant to use by people who are not familiar with Python packaging.
* More robust than DC/OS Docker.
* Simple ways to test DC/OS integration test changes, for OSS and Enterprise.
* Start up and tear down multiple clusters.

## Non-goals

* Scriptability, DC/OS E2E provides that.
* Backwards compatibility with non-current versions of DC/OS.
* Non-Docker backends

## Where should this live

Develop in this repository, then we can decide between:

* Shipped with E2E
* Shipped seperately
* Replacement for DC/OS Docker (breaking change in terms of API)

## Interface ideas

### Help

```
$ dcos-docker --help

Commands:
  doctor
  create
  destroy
  list
  wait
  inspect
```

### doctor

Tells you about e.g. RAM and Docker for Mac network issues.

### Create

```
$ dcos-docker create --help
Usage: dcos-docker create ARTIFACT

Get a DC/OS OSS artifact from...
Get a DC/OS Enterprise artifact from...

Options:
  # Should also take optional name, to replace cluster ID
  # Must be unique (validation)
  --extra-config (string or file)
  # Also mount options, look like Docker -v
  --masters
  --agents
  --public-agents
  --docker-storage-driver
  --docker-version
  --linux-distribution
  --dcos-checkout (syncs bootstrap / tests)
  --name
```

```
# Maybe docker-machine like - without name is 'default' then you never
# need the name - uses `default` everywhere
$ dcos-docker create /path/to/build/artifact.sh
385171
```

```
$ dcos-docker download-oss --pr 1235
$ dcos-docker download-oss --master
```

```
$ dcos-docker create /path/to/artifact.sh
```

### Destroy

```
$ dcos-docker destroy 385171 291288
385171
291288
$ dcos-docker destroy $(dcos-docker list)
928932
```

### List

```
# Should list be called ps
$ dcos-docker list
832532
151531
```

### Wait

```
$ dcos-docker wait 151531
```

### Inspect

```
$ dcos-docker inspect 151531
...
... Details like the web address
... format = set env vars, like source-cluster.sh
... also ship a generic run-master as a command
```

### Enterprise ideas

License parameter?
Handle custom CA cert?
Sync different integration tests?

### Run command

A command which basically does `./run-master`.

## Misc ideas

sphinx-click for docs
SSH key location in a label
Single generated file in Wiki

dcos-docker run 213143 pytest

Label for inspect = bash -> EE?? + version

Should `destroy` be called `rm`?

autocomplete container id
https://github.com/click-contrib/click-completion

# dcos_docker foo 2194312531
export MASTER_0=<docker_id>
export MASTER_1=<docker_id_>
export AGENT_0=<docker_id_>

eval $(dcos_docker inspect 2321431 --env)
docker exec -it $MASTER_0 /bin/bash

--wait on `create`

Document multiple ways to use --license,
e.g. use case of set env var once

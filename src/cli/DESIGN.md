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
  create
  destroy
  list
  wait
  inspect
```

### Create

```
$ dcos-docker create --help
Usage: dcos-docker create ARTIFACT

Get a DC/OS OSS artifact from...
Get a DC/OS Enterprise artifact from...

Options:
  --extra-config
  --masters
  --agents
  --docker-storage-driver
  --docker-version
  --linux-distribution
```

```
$ dcos-docker create /path/to/build/artifact.sh
385171
```

### Destroy

```
$ dcos-docker destroy 385171 291288
385171
291288
$ dcos-docker destroy --all
928932
```

### List

```
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
```

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
  sync
  run
```

### doctor

Tells you about e.g. RAM and Docker for Mac network issues.

### Create

```
$ dcos-docker create --help
  --dcos-checkout (syncs bootstrap / tests)
```

```
# Maybe docker-machine like - without name is 'default' then you never
# need the name - uses `default` everywhere
$ dcos-docker create /path/to/build/artifact.sh
385171
```

### Enterprise ideas

Handle custom CA cert?
Sync different integration tests?

### Run command

A command which basically does `./run-master`.
dcos-docker run 213143 pytest

## Misc ideas


autocomplete container id
https://github.com/click-contrib/click-completion

--wait on `create`

Document multiple ways to use --license,
e.g. use case of set env var once

Customisable logging system (wait?)

pip install click-spinner
Are dangling volumes left

Document this in index

test run on OSS
does OSS boot?

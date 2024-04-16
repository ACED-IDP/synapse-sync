# synapse-sync

## Overview

This command-line utility facilitates the synchronization of user accounts from Sage Synapse system to University of Chicago's Gen3 system. It's designed to streamline user management processes in DevOps environments where data exchange between these systems is required.

## Features

* User Synchronization: Transfer user accounts from Sage's Synapse system to University of Chicago's Gen3 system seamlessly.
* Selective Sync: Option to specify particular users for synchronization, offering flexibility and control over the process.
* Configuration Flexibility: Easily configurable parameters for specifying source and target systems, ensuring adaptability to different environments.
* Logging: Comprehensive logging of sync operations for auditing and troubleshooting purposes.

## Installation

```shell
pip install g3t-synapse-sync
```

## Configuration

* Follow [these instructions](https://aced-idp.github.io/getting-started/) to configure the g3t client.
  * We recommend using the g3t profile 'bridg2ai' ie `export G3T_PROFILE=bridge2ai`

* Follow these instructions to setup the synapse client:
  *  https://python-docs.synapse.org/tutorials/authentication/#prerequisites
  *  https://help.synapse.org/docs/Client-Configuration.1985446156.html#ClientConfiguration-ForDevelopers

## Test
```shell
g3t ping
```

## Usage

* crontab
```shell
PATH=/root/synapse-sync/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
SHELL=/bin/bash
SYNAPSE_SYNC_CONFIG=/root/synapse-sync/config.yaml
*/30 * * * * cd /root/synapse-sync && source venv/bin/activate && g3t_synapse_sync teams sync-all
```


```shell
g3t_synapse_sync teams --help
Using default config
Usage: g3t_synapse_sync teams [OPTIONS] COMMAND [ARGS]...

  Teams commands.

Options:
  --help  Show this message and exit.

Commands:
  sync      List commands to add users (and current status) of a team to...
  sync-all  Sync teams with gen3.

```

## Project Directories

g3t ready project directories are available in the `projects/` directories.  Please respect .gitignore and do not commit any data or meta information.

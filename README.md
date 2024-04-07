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
* We recommend using the g3t profile 'bridg2ai' 

* Follow these instructions to setup the synapse client:
*  https://python-docs.synapse.org/tutorials/authentication/#prerequisites
*  https://help.synapse.org/docs/Client-Configuration.1985446156.html#ClientConfiguration-ForDevelopers

## Test
```shell
g3t ping
```

## Usage

```shell
$ g3t_synapse_sync teams ls --help
Using default config
Usage: g3t_synapse_sync teams ls [OPTIONS] TEAM_ID

  List commands to add users (and current status) of a team to gen3.

      TEAM_ID one of:
      * AI_READI: https://www.synapse.org/#!Team:3499899
      * CHoRUS: https://www.synapse.org/#!Team:3499900
      * CM4AI: https://www.synapse.org/#!Team:3499897
      * Voice: https://www.synapse.org/#!Team:3499898
          

# eg

$ g3t_synapse_sync teams ls AI_READI -l
Using default config
Logging in to synapse
Getting current gen3 users
Syncing team: Bridge2AI AI-READI Open House Participants
<cmd> # name status updated_time policy_id
g3t utilities users add --username '3327899 (Synapse ID)' # bwalsh STATUS SIGNED 2024-04-06T23:58:31.828793 programs.bridge2ai.projects.AI_READI_reader 
g3t utilities users add --username '3409305 (Synapse ID)' # weiwang1973 STATUS NONE
g3t utilities users add --username '3421787 (Synapse ID)' # Hayley.Sanchez STATUS SIGNED 2024-04-06T23:58:31.132397 programs.bridge2ai.projects.AI_READI_reader 
g3t utilities users add --username '3432088 (Synapse ID)' # albrecht STATUS SIGNED 2024-04-06T23:58:31.327220 programs.bridge2ai.projects.AI_READI_reader 
g3t utilities users add --username '3465139 (Synapse ID)' # lbeckman314 STATUS SIGNED 2024-04-06T23:58:31.517115 programs.bridge2ai.projects.AI_READI_reader 

```
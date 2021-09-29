# morpheus-sos-plugin

## Build

```
docker build -t sosbuild .
mkdir build
docker run -v /home/ncelebic/morpheus-sos-plugin/build:/dist sosbuild
```
RPMs located in ./build

## Process

(In-tool means verification is performed within the tool, and we can see the result without having to compare files)

### Morpheus UI
#### Files Grabbed
- /etc/morpheus/*
  - /etc/morpheus/ssl/* is actively ignored
  - /etc/morpheus/morpheus-secrets.json is ignored
  - Passwords masked in morpheus.rb
- /opt/morpheus/version-manifest.json
- /opt/morpheus/conf/application.yml
  - Passwords masked
- /opt/morpheus/embedded/cookbooks/chef-run.log

Commands Run
- `morpheus-ctl status`

#### TODO

In-tool - Verification of connectivity to all services listed in application.yml

In-tool - Comparison of application.yml to morpheus.rb

In-tool - Verification of file/dir permissions

#### Analysis
Colorization of log files with search function

Possibly reimport to elastic on support side

### Elasticsearch
#### Files Grabbed
- /opt/morpheus/embedded/elasticsearch/config/elasticsearch.yml
- /var/log/morpheus/elasticsearch/current
  - morpheus.log
  - morpheus_*.log

#### Queries
Curls the following on localhost or remote if detected:
- /_cluster/settings,health,stats
- /_cat/nodes?v

#### Notes
_Logs are actually pulled from this module_
- If elasticsearch is down, we have no logs
- Default is 7 days worth of logs
- Using --since <YYYYMMDD> you can limit how far back logs will be grabbed

### RabbitMQ
_If embedded:_

#### Files Grabbed
- /opt/morpheus/embedded/rabbitmq/etc/*
- /opt/morpheus/embedded/rabbitmq/etc/*
- /etc/security/limits.d/
= /etc/systemd/
- /var/log/morpheus/rabbitmq/*

#### Queries
`rabbitmqctl report`

_If system-local_:

Uses default rabbitmq plugin for sos

### MySQL - Not Done
#### Files grabbed:
- /opt/morpheus/embedded/mysql/my.cnf
- /opt/morpheus/embedded/mysql/ops-my.cnf
  - Passwords masked
- /var/log/morpheus/mysql/*.log
- /var/log/morpheus/mysql/current

#### Queries:

- processlist
- dbdump

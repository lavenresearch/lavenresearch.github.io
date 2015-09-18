---
layout: hpost
category : linux
tagline: ""
tags : [linux,swift,openstack,syslog,rsyslog]
---
{% include JB/setup %}

# Openstack Swift 的日志系统

## Linux 系统日志

[syslog and syslog-ng 详解](http://ant595.blog.51cto.com/5074217/1080922), [SAIO 配置日志系统的方法](http://docs.openstack.org/developer/swift/development_saio.html#optional-setting-up-rsyslog-for-individual-logging)


Openstack swift 的日志和 linux 系统日志是混合在一起的。在没有特别配置的情况下，日志信息将被记录在 `/var/log/messages` 中。Linux 使用的日志系统为 syslog。在 Centos 7 中与之对应的服务为 `rsyslog.service`。

rsyslog 配置文件一个重要作用是建立“日志主体”与日志文件之间的关系。例如，下面的配置指定“日志主体”（local1,local2,local3,etc.）中的数据被写入的文件名。不同的程序可以选择不同的“日志主体”用于日志记录。例如，swift proxy-server 可以指定将日志放入 local1 中，因此，根据下面的配置文件，proxy-server 的日志数据将被记录在 `/var/log/swift/proxy.log` 中。

~~~conf
# Uncomment the following to have a log containing all logs together
#local1,local2,local3,local4,local5.*   /var/log/swift/all.log

# Uncomment the following to have hourly proxy logs for stats processing
#$template HourlyProxyLog,"/var/log/swift/hourly/%$YEAR%%$MONTH%%$DAY%%$HOUR%"
#local1.*;local1.!notice ?HourlyProxyLog

local1.*;local1.!notice /var/log/swift/proxy.log
local1.notice           /var/log/swift/proxy.error
local1.*                ~

local2.*;local2.!notice /var/log/swift/storage1.log
local2.notice           /var/log/swift/storage1.error
local2.*                ~

local3.*;local3.!notice /var/log/swift/storage2.log
local3.notice           /var/log/swift/storage2.error
local3.*                ~

local4.*;local4.!notice /var/log/swift/storage3.log
local4.notice           /var/log/swift/storage3.error
local4.*                ~

local5.*;local5.!notice /var/log/swift/storage4.log
local5.notice           /var/log/swift/storage4.error
local5.*                ~

local6.*;local6.!notice /var/log/swift/expirer.log
local6.notice           /var/log/swift/expirer.error
local6.*                ~
~~~

系统包含的一般性的日志也对应于不同的“日志主体”，具体配置在 `/etc/rsyslog.conf` 中。需要注意的是 local0, 即写入`/var/log/messages` 的日志主体。其日志等级默认被设为 info, 即 debug 日志信息将无法被记录。相关配置如下。如果将日志文件删除，需要重启 rsyslog 服务，被删除的日子文件才会被重新创建。

~~~conf
# Log anything (except mail) of level info or higher.
# Don't log private authentication messages!
*.info;mail.none;authpriv.none;cron.none                /var/log/messages
~~~

## Openstack Swift 日志系统

[proxy_logging middleware](https://github.com/openstack/swift/blob/master/swift/common/middleware/proxy_logging.py), [openstack swift 获取系统logger的方法](https://github.com/openstack/swift/blob/master/swift/common/utils.py#L1423), [Proxy Server Configuration](http://docs.openstack.org/juno/config-reference/content/proxy-server-configuration.html), [Openstack swift logs](http://docs.openstack.org/developer/swift/logs.html)

Openstack swift 不同服务的各自的配置文件中包含日志系统的配置信息，例如，在 proxy-server.conf 文件中添加如下指令可以控制 proxy-server 记录日志的行为。__注意：日志还受 syslog 配置的影响。__ 例如，配置 proxy-server 记录 debug level 的日志，但是在 rsyslog 中对应的日志主体配置为记录 info level 的日志，最终，debug level 的日子将不会被记录。

- log_facility 指定了日志主体，即，log_local0，因此这些日志信息将被记入 `/var/log/messages`. 若该值为 log_local1, 则根据上面的配置，对应的日志文件为 `/var/log/swift/proxy.log`
- log_name 指定了日志的名字，日志的名字将被显示在最终的日志里，可以用此区别不同来源的日志信息。
- log_level 指定了日志记录的level，这里为 DEBUG，因此将记录所有的日志信息。

这些配置语句可以放在配置文件中所有的 app 或者 filter 块之外，即，发挥全局作用，所有的 app 或者 middleware 将默认使用全局配置。但是，也可以放在具体某一个 app 或者 filter 块之内，作为相应的 app 或者 middleware 的局部配置，用于覆盖全局配置。

~~~conf
set log_name = tempauth
set log_facility = LOG_LOCAL0
set log_level = DEBUG
set log_headers = false
set log_address = /dev/log
~~~

另外，`eventlet_debug = true` 可以使一些调试事件被记录在 stderr 中，对应于日志主体中的 notice, 例如， rsyslog 配置中 `local1.notice    /var/log/swift/proxy.error`.

---
layout: hpost
category : Openstack
tagline: ""
tags : [cloud computing,swift,object storage,openstack]
---
{% include JB/setup %}

# Openstack Swift 安装配置笔记

Based On:

[Openstack Swift 原理、架构与 API 介绍](http://www.ibm.com/developerworks/cn/cloud/library/1310_zhanghua_openstackswift/)

[OpenStack(Juno) Installation Guide for Ubuntu 14.04](http://docs.openstack.org/juno/install-guide/install/apt/content/index.html)

[OpenStack Swift Overview](https://swiftstack.com/openstack-swift/)

## OpenStack Swift 系统架构及角色分配

OpenStack 系统结构如图所示，搭建 Swift 需要安装配置其中的 Controller Node 和 Object Storage Nodes。这两种节点的主要功能如下。

- Controller Node
    + 各个节点时间同步服务（NTP）
    + 认证服务 keystone 的服务端及客户端
    + Swift Proxy Server（用于处理数据存储请求）
- Object Storage Server
    + Swift Account Server（负责Account相关数据存储）
    + Swift Container Server（负责Container相关数据存储）
    + Swift Object Server（负责Object相关数据存储）

![Openstack 系统架构及角色分配](/images/openstackArchitecture.png)

下图为 Swift 的架构，其处理数据存储请求的流程为：

- Proxy Server 接收用户端数据存储请求，并使用请求中包含的认证信息，向认证服务器（TempAuth，Keystone，etc.）认证；
- 若认证成功，解析出请求对应的 partition index，从相应的 Ring 中读取相应 partition 的副本所在的 Devices 信息；
- 从相应 Devices 读取或写入数据并返回。

![Swift 系统架构](/images/openstackSwiftArchitecture.png)

## Swift 包含的主要服务及功能

### Proxy server

主要功能为请求转发（通过查询相应的Ring定位），对于涉及纠删码的 storage policies，object 数据的编解码也由 proxy server 执行。

数据流应该需要经过 proxy server 后发送给用户的（因为编解码需要在 proxy server 处执行）。但是 proxy server 并不缓冲数据（为什么？TODO）。

> When objects are streamed to or from an object server, they are streamed directly through the proxy server to or from the user – the proxy server does not spool them.

### The Ring

Ring 是一个从存储数据的名字到其物理位置的映射。因此，对于 account，container，object 操作需要查询相应的 Ring 以确定数据所在设备（Devices）的信息。

> The rings determine where data should reside in the cluster. There is a separate ring for account databases, container databases, and individual objects but each ring works in the same way.

系统中的Ring包括：

1. 系统中所有 Accounts 的数据对应一个 Account Ring
2. 系统中所有的 Containers 对应一个 Container Ring
3. 系统中使用相同 storage policy 的 objects 数据对应一个 Object Ring

### Object Server

负责在本地设备上存储，检索，删除数据。其以2进制的形式将数据保存在文件系统中，并在文件的扩展属性（xattrs，这需要底层文件系统的支持）中存储相应的元数据。

删除也被看作是object的一个版本，在这个版本中，数据长度为0，其副本数和正常文件是一样的。通过这种方式，避免了存在失效恢复将已删除的文件恢复出来的情况。

### Container Server

记录一个 container 内包含 objects 的列表（不包括 object 的位置信息）。这些信息存储在一个数据库文件中，该文件和普通的 Object 一样会被冗余存储在系统中。

### Account Server

与 Container Server 一样，不过存储的信息是 Account 中包含的 container 列表。

### Replication

Replication processes 会将本地的数据与远端的数据副本进行对比，以确保所有的数据副本都处在最新版本。其通过哈希对比数据，每一个 partition 对应一个哈希列表，列表中每一个哈希值对应一个 partition 中的一块数据。

> Object replication uses a hash list to quickly compare subsections of each partition, and container and account replication use a combination of hashes and shared high water marks.

### Updaters

处理 container 或者 account 数据没有及时更新的情况（例如发生失效，系统过载等情况）。在最终一致的窗口时， updater 重新执行失败的 update 操作。

### Auditors

检查本地数据（object, container, account）的完整性以及其他错误。如果本地数据出错（例如，发生 bit rot）就将本地副本隔离，并使用其他副本更新本地副本。

## Openstack Swift 安装环境

共四台机器：swift-aa, swift-bb, swift-cc, swift-dd

- swift-aa（192.168.245.130）
    + swift 客户端
- swift-bb（192.168.245.131）
    + Controller Node
- swift-cc（192.168.245.132） 和 swift-dd（192.168.245.133）
    + Object Storage Node

其中，在 swift-cc 和 swift-dd 上分别用两个文件设置成 loop 设备作为供 swift 使用的存储设备： loop0, loop1.

## Openstack Swift 安装配置过程

每一步的验证方法详见[OpenStack(Juno) Installation Guide for Ubuntu 14.04](http://docs.openstack.org/juno/install-guide/install/apt/content/index.html)。

### 基本环境

@(swift-aa, swift-bb, swift-cc, swift-dd)

修改/etc/hosts，添加如下内容。

    # controller
    192.168.245.131       controller

    # object storage
    192.168.245.132       object1
    192.168.245.133       object2

@swift-bb

安装配置NTP服务。[ntp.conf](/recource/swiftConfFiles/swift-bb/ntp.conf)

    apt-get install ntp
    vim /etc/ntp.conf
        # server 0.ubuntu.pool.ntp.org iburst
        # server 1.ubuntu.pool.ntp.org iburst
        # server 2.ubuntu.pool.ntp.org iburst
        # server 3.ubuntu.pool.ntp.org iburst
        # server ntp.ubuntu.com iburst
        # restrict -4 default kod notrap nomodify nopeer noquery
        # restrict -6 default kod notrap nomodify nopeer noquery
    service ntp restart

@(swift-cc, swift-dd)

安装配置NTP服务。[ntp.conf@swift-cc](/recource/swiftConfFiles/swift-cc/ntp.conf), [ntp.conf@swift-dd](/recource/swiftConfFiles/swift-dd/ntp.conf)

    apt-get install ntp
    vim /etc/ntp.conf
        # server controller iburst
    service ntp restart

@swift-bb

安装数据库服务。[my.cnf](/recource/swiftConfFiles/swift-bb/my.cnf)

    apt-get install mariadb-server python-mysqldb
    vim /etc/mysql/my.cnf
    service mysql restart
    mysql_secure_installation

### 认证服务

@swift-bb

安装 keystone 服务端。[keystone.conf](/recource/swiftConfFiles/swift-bb/keystone.conf)

    mysql -u root -p
        CREATE DATABASE keystone;
        GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'localhost' \
          IDENTIFIED BY 'aa';
        GRANT ALL PRIVILEGES ON keystone.* TO 'keystone'@'%' \
          IDENTIFIED BY 'aa';
    openssl rand -hex 10
    # 28bfc1d5efc9028539d1

    apt-get install keystone python-keystoneclient
    vim /etc/keystone/keystone.conf
        # [DEFAULT]
        # ...
        # admin_token = 28bfc1d5efc9028539d1
        # ...
        # verbose = True
        # [database]
        # ...
        # connection = mysql://keystone:aa@controller/keystone
        # [token]
        # ...
        # provider = keystone.token.providers.uuid.Provider
        # driver = keystone.token.persistence.backends.sql.# Token
        # [revoke]
        # ...
        # driver = keystone.contrib.revoke.backends.sql.Revoke
    su -s /bin/sh -c "keystone-manage db_sync" keystone
        # commenting "driver = keystone.token.persistence.backends.sql.Token" of the [token] section in the /etc/keystone/keystone.conf file
    service keystone restart
    rm -f /var/lib/keystone/keystone.db
    (crontab -l -u keystone 2>&1 | grep -q token_flush) || \
        echo '@hourly /usr/bin/keystone-manage token_flush >/var/log/keystone/keystone-tokenflush.log 2>&1' \
        >> /var/spool/cron/crontabs/keystone

在 keystone 中创建 tenants, users, and roles。

    export OS_SERVICE_TOKEN=28bfc1d5efc9028539d1
    export OS_SERVICE_ENDPOINT=http://controller:35357/v2.0

    keystone tenant-create --name admin --description "Admin Tenant"
    keystone user-create --name admin --pass aa --email aa@aa.aa
    keystone role-create --name admin
    keystone user-role-add --user admin --tenant admin --role admin
    keystone tenant-create --name aa --description "Demo Tenant"
    keystone user-create --name aa --tenant aa --pass aa --email aa@aa.aa
    keystone tenant-create --name service --description "Service Tenant"

创建 service entity 和 API endpoint。

    keystone service-create --name keystone --type identity \
        --description "OpenStack Identity"

    keystone endpoint-create \
        --service-id $(keystone service-list | awk '/ identity / {print $2}') \
        --publicurl http://controller:5000/v2.0 \
        --internalurl http://controller:5000/v2.0 \
        --adminurl http://controller:35357/v2.0 \
        --region regionOne

@swift-aa

认证服务安装结果验证。

    unset OS_SERVICE_TOKEN OS_SERVICE_ENDPOINT

    keystone --os-tenant-name admin --os-username admin --os-password aa \
        --os-auth-url http://controller:35357/v2.0 token-get
    keystone --os-tenant-name admin --os-username admin --os-password aa \
        --os-auth-url http://controller:35357/v2.0 tenant-list
    keystone --os-tenant-name admin --os-username admin --os-password aa \
        --os-auth-url http://controller:35357/v2.0 user-list
    keystone --os-tenant-name admin --os-username admin --os-password aa \
        --os-auth-url http://controller:35357/v2.0 role-list
    keystone --os-tenant-name demo --os-username aa --os-password aa \
        --os-auth-url http://controller:35357/v2.0 token-get
    keystone --os-tenant-name demo --os-username aa --os-password aa \
        --os-auth-url http://controller:35357/v2.0 user-list

### Swift Proxy Server

Swift Proxy Server 可以被部署在任意一台机器上，这里将其部署在 Controller Node（swift-bb）上。

@swift-bb

认证相关的设置。

    keystone user-create --name swift --pass aa
    keystone user-role-add --user swift --tenant service --role admin
    keystone service-create --name swift --type object-store \
        --description "OpenStack Object Storage"
    keystone endpoint-create \
        --service-id $(keystone service-list | awk '/ object-store / {print $2}') \
        --publicurl 'http://controller:8080/v1/AUTH_%(tenant_id)s' \
        --internalurl 'http://controller:8080/v1/AUTH_%(tenant_id)s' \
        --adminurl http://controller:8080 \
        --region regionOne

安装所需服务。[proxy-server.conf](/recource/swiftConfFiles/swift-bb/proxy-server.conf)

    apt-get install swift swift-proxy python-swiftclient python-keystoneclient memcached
    mkdir /etc/swift
    curl -o /etc/swift/proxy-server.conf \
        https://raw.githubusercontent.com/openstack/swift/stable/juno/etc/proxy-server.conf-sample
    vim /etc/swift/proxy-server.conf
        # [DEFAULT]
        # bind_port = 8080
        # user = swift
        # swift_dir = /etc/swift

        # [pipeline:main]
        # pipeline = authtoken cache healthcheck keystoneauth proxy-logging proxy-server

        # [app:proxy-server]
        # allow_account_management = true
        # account_autocreate = true

        # [filter:keystoneauth]
        # use = egg:swift#keystoneauth
        # operator_roles = admin,_member_

        # [filter:authtoken]
        # paste.filter_factory = keystonemiddleware.auth_token:filter_factory
        # auth_uri = http://controller:5000/v2.0
        # identity_uri = http://controller:35357
        # admin_tenant_name = service
        # admin_user = swift
        # admin_password = aa
        # delay_auth_decision = true

        # [filter:cache]
        # memcache_servers = 127.0.0.1:11211

### Swift Storage Nodes

@(swift-cc, swift-dd)

配置基本环境。[fstab@swift-cc](/recource/swiftConfFiles/swift-cc/fstab), [fstab@swift-dd](/recource/swiftConfFiles/swift-dd/fstab), [rsyncd.conf@swift-cc](/recource/swiftConfFiles/swift-cc/rsyncd.conf), [rsyncd.conf@swift-dd](/recource/swiftConfFiles/swift-dd/rsyncd.conf)

    apt-get install xfsprogs rsync
    mkfs.xfs /dev/loop0
    mkfs.xfs /dev/loop1
    mkdir -p /srv/node/loop0
    mkdir -p /srv/node/loop1
    vim /etc/fstab
        # /dev/loop0 /srv/node/loop0 xfs noatime,nodiratime,nobarrier,logbufs=8 0 2
        # /dev/loop1 /srv/node/loop1 xfs noatime,nodiratime,nobarrier,logbufs=8 0 2
    mount /srv/node/loop0
    mount /srv/node/loop1

    vim /etc/rsyncd.conf
        # Replace MANAGEMENT_INTERFACE_IP_ADDRESS with the IP address of the management network on the storage node.
        # uid = swift
        # gid = swift
        # log file = /var/log/rsyncd.log
        # pid file = /var/run/rsyncd.pid
        # address = MANAGEMENT_INTERFACE_IP_ADDRESS
        # [account]
        # max connections = 2
        # path = /srv/node/
        # read only = false
        # lock file = /var/lock/account.lock
        # [container]
        # max connections = 2
        # path = /srv/node/
        # read only = false
        # lock file = /var/lock/container.lock
        # [object]
        # max connections = 2
        # path = /srv/node/
        # read only = false
        # lock file = /var/lock/object.lock
    vim /etc/default/rsync
        # RSYNC_ENABLE=true
    service rsync start

安装所需服务。[account-server.conf@swift-cc](/recource/swiftConfFiles/swift-cc/account-server.conf), [account-server.conf@swift-dd](/recource/swiftConfFiles/swift-dd/account-server.conf), [container-server.conf@swift-cc](/recource/swiftConfFiles/swift-cc/container-server.conf), [container-server.conf@swift-dd](/recource/swiftConfFiles/swift-dd/container-server.conf), [object-server.conf@swift-cc](/recource/swiftConfFiles/swift-cc/object-server.conf), [object-server.conf@swift-dd](/recource/swiftConfFiles/swift-dd/object-server.conf)

    apt-get install swift swift-account swift-container swift-object
    curl -o /etc/swift/account-server.conf \
        https://raw.githubusercontent.com/openstack/swift/stable/juno/etc/account-server.conf-sample
    curl -o /etc/swift/container-server.conf \
        https://raw.githubusercontent.com/openstack/swift/stable/juno/etc/container-server.conf-sample
    curl -o /etc/swift/object-server.conf \
        https://raw.githubusercontent.com/openstack/swift/stable/juno/etc/object-server.conf-sample
    vim /etc/swift/account-server.conf
        # [DEFAULT]
        # bind_ip = MANAGEMENT_INTERFACE_IP_ADDRESS
        # bind_port = 6002
        # user = swift
        # swift_dir = /etc/swift
        # devices = /srv/node
        # [pipeline:main]
        # pipeline = healthcheck recon account-server
        # [filter:recon]
        # recon_cache_path = /var/cache/swift
    vim /etc/swift/container-server.conf
        # [DEFAULT]
        # bind_ip = MANAGEMENT_INTERFACE_IP_ADDRESS
        # bind_port = 6001
        # user = swift
        # swift_dir = /etc/swift
        # devices = /srv/node
        # [pipeline:main]
        # pipeline = healthcheck recon container-server
        # [filter:recon]
        # recon_cache_path = /var/cache/swift
    vim /etc/swift/object-server.conf
        # [DEFAULT]
        # bind_ip = MANAGEMENT_INTERFACE_IP_ADDRESS
        # bind_port = 6000
        # user = swift
        # swift_dir = /etc/swift
        # devices = /srv/node
        # [pipeline:main]
        # pipeline = healthcheck recon object-server
        # [filter:recon]
        # recon_cache_path = /var/cache/swift
    chown -R swift:swift /srv/node
    mkdir -p /var/cache/swift
    chown -R swift:swift /var/cache/swift

@swift-bb

创建 Rings。

    cd /etc/swift

    swift-ring-builder account.builder create 10 3 1
    swift-ring-builder account.builder add r1z1-192.168.245.132:6002/loop0 100
    swift-ring-builder account.builder add r1z1-192.168.245.132:6002/loop1 100
    swift-ring-builder account.builder add r1z1-192.168.245.133:6002/loop0 100
    swift-ring-builder account.builder add r1z1-192.168.245.133:6002/loop1 100
    swift-ring-builder account.builder rebalance

    swift-ring-builder container.builder create 10 3 1
    swift-ring-builder container.builder add r1z1-192.168.245.132:6002/loop0 100
    swift-ring-builder container.builder add r1z1-192.168.245.132:6002/loop1 100
    swift-ring-builder container.builder add r1z1-192.168.245.133:6002/loop0 100
    swift-ring-builder container.builder add r1z1-192.168.245.133:6002/loop1 100
    swift-ring-builder container.builder rebalance

    swift-ring-builder object.builder create 10 3 1
    swift-ring-builder object.builder add r1z1-192.168.245.132:6002/loop0 100
    swift-ring-builder object.builder add r1z1-192.168.245.132:6002/loop1 100
    swift-ring-builder object.builder add r1z1-192.168.245.133:6002/loop0 100
    swift-ring-builder object.builder add r1z1-192.168.245.133:6002/loop1 100
    swift-ring-builder object.builder rebalance

    scp *.ring.gz 192.168.245.132:/etc/swift
    scp *.ring.gz 192.168.245.133:/etc/swift

配置 hash 和 storage policy。

    curl -o /etc/swift/swift.conf \
        https://raw.githubusercontent.com/openstack/swift/stable/juno/etc/swift.conf-sample
    vim /etc/swift/swift.conf
        # [swift-hash]
        # swift_hash_path_suffix = HASH_PATH_PREFIX
        # swift_hash_path_prefix = HASH_PATH_SUFFIX
        # [storage-policy:0]
        # name = Policy-0
        # default = yes
    scp /etc/swift/swift.conf 192.168.245.132:/etc/swift/
    scp /etc/swift/swift.conf 192.168.245.133:/etc/swift/

启动 Swift Proxy Server 服务。

    chown -R swift:swift /etc/swift
    service memcached restart
    service swift-proxy restart

@(swift-cc, swift-dd)

启动 Swift 存储端服务。

    chown -R swift:swift /etc/swift
    swift-init all start

@swift-aa

验证 Swift 安装结果。

    apt-get install swift python-swiftclient python-keystoneclient
    vim aa-openrc.sh
        # export OS_TENANT_NAME=aa
        # export OS_USERNAME=aa
        # export OS_PASSWORD=aa
        # export OS_AUTH_URL=http://controller:5000/v2.0
    source aa-openrc.sh
    swift stat
    swift upload aa-container1 FILE
    swift list
    swift download aa-container1 FILE

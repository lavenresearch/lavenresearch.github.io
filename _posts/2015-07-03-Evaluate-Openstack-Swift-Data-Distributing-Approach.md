---
layout: hpost
category : Openstack
tagline: ""
tags : [cloud computing,swift,object storage,openstack]
---
{% include JB/setup %}

# Openstack Swift 数据分布方法（Ring）及评价

Swift 使用 Ring 实现的数据分布的目标是，将所有 objects 按权平均分布在集群中所有 devices 上，并且尽量减少当集群中新增 device 或者删除 device 时需要迁移的数据量。

## OpenStack Swift 数据分布方法

Based On: [Openstack Swift Documents: The Rings](http://docs.openstack.org/developer/swift/overview_ring.html) , [Openstack Swift Documents: Storage Policies](http://docs.openstack.org/developer/swift/overview_policies.html)

### Ring 的结构

Swift 使用 Ring 来管理数据分布。 Ring 的主要内容为：

> The ring data structure consists of three top level fields: a list of devices in the cluster, a list of lists of device ids indicating partition to device assignments, and an integer indicating the number of bits to shift an MD5 hash to calculate the partition for the hash.

- devices 列表（数据结构为 python 中的 array('H')）
- 每个副本对应一个内容为 device id 的列表，列表长度是系统中 partition 的总量。
- Partition Shift 值

![Devices 列表](/images/dev_chart.png)

![Partition 定位表](/images/replicas_chart.png)

系统中 partitions 的总量在系统创建时确定，并在整个生命周期中不变。每个 partition 对应存储端的一个目录，该目录是进行数据迁移时的最小单位。Proxy Server 会将每一个数据对象（Object）根据其路径名映射到一个 partition 中。使用该方式的原因在[深入云存储系统Swift核心组件：Ring实现原理剖析](http://www.cnblogs.com/yuxc/archive/2012/06/22/2558312.html)中有详细说明。

### Ring 的分类及关系

Rings 共分为三种 Account Ring, Container Ring, Object Ring。其中 Object Ring 可以存在多个，分别对应于不同的 Storage Policies。不同 Ring 之间的数据相互独立，但是其处理过程是一样的。

对于每一个 Ring， 在存储端的每个 device 挂载的文件夹下，都有一个单独的文件夹与之对应。该文件夹中的每个文件夹对应相应 Ring 中索引的 partitions。

> /objects maps to objects associated with Policy-0

> /objects-N maps to storage policy index #N

### 基于 Ring 的数据定位流程

使用 Swift 时，读写数据的请求发送到 proxy-server，由 proxy-server 查询相应的 Ring 来确定数据所在的 device。使用 Ring 实现数据定位的流程如下。

![Swift 数据定位流程](/images/swift_request_processing.png)

### Ring 的创建及管理

Ring 的创建及管理通过 ring-builder 命令实现，该命令需要人工执行。下面命令的功能为:创建ring，向ring中添加device，进行partitions到devices的分配。

~~~bash
swift-ring-builder account.builder create 18 3 1
swift-ring-builder account.builder add z1-192.168.1.50:6002/sdc 100
swift-ring-builder account.builder add z2-192.168.1.51:6002/sdc 100
swift-ring-builder account.builder add z3-192.168.1.52:6002/sdc 100
swift-ring-builder account.builder add z4-192.168.1.54:6002/sdc 100
swift-ring-builder account.builder rebalance
~~~

ring-builder 会把将来建立重建ring需要的信息保存在自己的builder文件里。如果该文件丢失，相当于让ring-builder从头开始创建一个新的ring，这意味着，重排所有partitions到devices的映射，因此将有大量的数据被迁移到新的devices上（数据在迁移完成前是无法被访问的）。

创建的ring需要被复制到swift所有的节点上才能发挥作用，存储节点每隔一段时间会重新加载ring到内存中。而使用老版本的ring的后果是，一小部分partitions的位置信息是错误的。然而ring-builder更新ring时，会尽量使一个partition最多只会有一个副本被迁移，因此在使用最新版的ring之前，一个partition最多只有一个replica会出现定位错误。

#### Ring 创建及更新流程

首次创建 Ring：

- 根据Device的weight计算每个Device需要存储partition个数；
- 将device按照其存储的partition数量排序（对于存储partition数量相同的devices，按照其tiebreaker值排序，每个device的tiebreaker值随机生成）；
- ring-builder按照devices顺序从上往下分配partition的replica，但是会最大程度将一个partition的不同replica分布在不同的区域内。

更新 Ring:

- 计算每个device在这一轮分配中可以接收的partition数量；
- 收集需要被重新分配的partitions；
    + 被删除的devices上的partitions全部被记入重新分配列表；
    + 在增加device的情况下，一个partition的replicas能够更加分散，则被记入重新分配列表；
    + 一个device若目前存储的partitions多于其可以接收的partition数量，则随机选择该device上的一些partition记入重新分配列表。
- 使用与首次创建 Ring 相同的方法，对重新分配列表中的 partitions 进行重新分配。

当一个partition的一个replica被重新分配后，则该partition的所有replicas在一段时间内都不可被再次重新分配。除非是因为device移除造成的重分配。

Rebalance过程会被反复执行，直到数据的分布的平衡度小于1%，或者执行结果相对与前一次的提升不足1%。

### 数据可靠性与均匀分布的权衡

> The ring builder tries to keep replicas as far apart as possible while still respecting device weights. When it can’t do both, the overload factor determines what happens.

> Essentially, the overload factor lets the operator trade off replica dispersion (durability) against data dispersion (uniform disk usage).

在 Swift 中，使用 overload factor 这个参数控制数据分布。这个参数的值意味着，每个 device 可以存储超出其权重的数据。使用 overload_factor 可以调整数据均匀分布度和数据分散程度（可靠性）。

在分配 partitions 时，一个 partition 的不同 replicas 可能会由于 device weight 的限制而无法达到最好的分散度（即，被分配到不同的 regin, zone, server, device 上）。这样让一个device可以接收部分超出其 weight 的 partitions 可以让数据被更好的分散开，从而提供更好的 durability。

Overload factor 的作用会受到集群 warning threshold 的限制，因而 weight 低的 device 存储的 partitions 数量并不会超过 weight 高的 device。

## Openstack Swift 数据分布方法评价

### Swift 面向的数据存储需求

- 静态数据
    + 存放在 Swift 中的数据一般为视频，图片，电子邮件备份等一次写入多次读取的数据。
    + 每一次数据访问的数据量相对而言较大（相对于一般的 Key-Value 数据库，例如 MongoDB, Dynamo 等）。
- 大规模并行访问
- 时延的要求较宽松（相对于一般的 Key-Value 数据库）
- 弱一致性要求（最终一致性）
    + 即，应用可以接受，一段时间内的数据不一致。

### 数据分布管理方法对比

对于分布式文件系统的而言，数据分布的管理一般采用元数据服务器的方式，例如，Ceph，Google File System。

<!-- TODO 微软的flat datacenter storage system是采用的什么方式？ -->

相对于元数据服务器的方式，Swift 这种基于 Hash 的数据分布管理其实是一种功能较弱的方法。

- 由于只要求最终一致性，并且应用模型是一次写多次读，因此，不需要实现文件锁。从而可以避免同步分布式客户端并发的数据读写时的状态同步问题（即要把并发写改造成顺序写）。进而使中心控制的必要性变弱。这样带来的好处是，数据定位操作具有__极高的可扩展性__，每一个 Proxy server 都相当于一个功能完备的元数据服务器（相对于子树分割，一个元数据服务器只能相应部分元数据操作请求），并且不用考虑，多个元数据服务器之间的元数据同步问题。
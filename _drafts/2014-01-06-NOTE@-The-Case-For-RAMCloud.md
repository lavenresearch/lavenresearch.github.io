---
layout: post
category : Memory
tagline: "July 2011 Communication Of The ACM"
tags : [RAMCloud]
---
{% include JB/setup %}

## RAMCloud产生的背景
1. 磁盘容量增长速度远大于磁盘性能增长速度。
2. 目前一个多核存储服务器的计算能力每秒钟可以处理 1000，000个小读请求，但是以内存作cache的磁盘存储系统每秒只能响应1000~10000个小读请求。

## RAMCloud Overview
RAMCloud的特点是：
1. 所有的数据都存储在DRAM中，与传统的cache不同。
2. 具有良好的 scalability ，能够自动的扩展到上千的存储节点。

通过RAMCloud，可以将datacenter中application server到storage server之间数百字节访问的时延降低至5μs–10μs。基于磁盘的存储系统访问时延为0.5ms–10ms，取决于数据是否被缓存在内存中。

RAMCloud目前并不适合存储大规模media，例如视屏，音乐，图片。因为它们的large size。

_The combination of latency and scale offered by RAMCloud will change the storage landscape。_
1. 简化大规模web应用开发
2. 产生新的data intensive的应用
3. 支持云计算

## RAMCloud Motivation
### latency的重要性
when Facebook receives an HTTP request for a Web page, the application server makes an average of 130 internal requests for data (inside the Facebook site) as part of generating the HTML for the page, 15 and the requests must typically be issued sequentially.

Amazon has reported similar results, with 100–200 internal requests to generate HTML for each page.

这些intern request的响应时延是用户响应时延中一个重要的部分。These limitations rule out entire classes of algorithms (such as those traversing large graphs).

### Scalability
关系型数据库的扩展性很低，因此需要在多个数据库之间划分数据。这些数据的划分，一致性维护等工作都需要在应用中实现，使得应用变得和复杂。为了提高性能，还需要在内存中缓存数据，缓存涉及的管理操作也需要在应用程序中实现。

NOSQL是为了解决关系型数据库的扩展性问题而出现的，但是，NOSQL不具备关系型数据库的通用性，而且其性能也受到硬盘性能的限制。

One motivation for RAMCloud is to provide a general-purpose storage system that scales far beyond existing systems, so application developers need not resort to specialized approaches (such as NoSQL systems).

### cache的不足
1. 增加了系统性能的变化性
2. 一些新的应用，例如，facebook，由于其数据间复杂的连接关系，使得数据访问缺少局部性。

### 不使用flash的原因
DRAM-based implementation offers higher performance.

 For  high  query rates and smaller data set sizes, DRAM is cheapest; for low query rates and large data sets, disk is cheapest; and in the middle ground, flash is cheapest.

## 需要解决的问题
### Low latency RPC
RPC round-trip times：
IB，Myrinet < 10μs
Ethernet/IP/TCP 300μs–500μs

Ethernet在数据中心中被广泛使用，降低Ethernet的方法需要从两方面考虑：硬件（升级交换机和NIC到10Gbit/s),软件（简化协议处理，消除中断开销，一个方法是将NIC直接映射到地址空间中去）

目前的网络协议都是针对throughput优化，牺牲一定latency。但是对于RAMCloud来说，需要一个以latency-centric的网络设计。

### 持久性和可用性
要求是：
1. a crash of a single server cannot cause data to be lost or affect system availability for more than a few seconds.
2. systemic loss of power to a data center cannot result in permanent loss of information.

一种不影响RAMCloud性能的方案是，多节点内存中副本，异步刷新到硬盘，为了不丢失最近的数据，增加电池保证断电后server可以将数据刷新到硬盘。The ideal solution is to provision each server with small batteries that keep the server alive after a power failure long enough for it to flush buffered log entries to disk. Google uses such a configuration in its data centers;

可用性要求能够做到快速恢复。失效节点上的数据会被存储在几百节点上，因此在进行数据恢复的时候就可以从这些节点上并行读取数据到数百个顶替失效节点的节点上，从而实现快速恢复。

### cluster management
要根据数据的特性选择数据的放置的位置。
For small tables it is most efficient to store the entire table plus any related indexes on a single server, since it would allow multiple objects to be retrieved from the table with a single request to a single server.
另外：
1. 对于超出单个server能力的tables能够进行自动分块。
2. 对于访问热点（访问超过单个server的处理能力），能够对其进行分块和副本。

### 多租赁（multi-tenancy）
在RAMCloud中会同时存在多个使用者，因此需要能够合理使用各个租户的剩余资源，还包括实现访问控制，安全机制及性能隔离。

### 数据模型（data model）
| Data Model type       | Features                                           |
|-----------------------|----------------------------------------------------|
| Relational Data Model | 1. convenient programming interface                |
|                       | 2. incompatible with low-latency goals of RAMCloud |

 no one has yet constructed a system with ACID (atomicity, consistency, isolation, and durability) properties at the scale we envision for RAMCloud. Thus the best data model for RAMCloud is likely to be something simpler (such as a keyvalue store)

最终选择了key-value。

### concurrency,transactions,consistency
transaction完成速度越快，conflicting transaction之间覆盖的概率越小，因此减少 the costs of preventing or resolving conflicts.

## RAMCloud disadvantages
1. high cost per bit
2. high energy use per bit
3. more floor space in datacenter
4. 对跨数据中心的应用中的写性能没有提升（因为这时的时延主要是数据中心之间通信产生的），但是会提升其读性能。

但是对于high throughput的应用来说，DRAM更加省钱和节能。（使用另外一种衡量标准：cost per operation,energy per operation）

## 相关工作
Both InfiniBand and iWARP support the remote direct memory access (RDMA) protocol, allowing a client application to issue read and write requests to selected memory regions of a server;

对于RDMA而言，虽然其提供了low latency,但是它提供的操作接口太底层，client使用很复杂。

## 可能产生的影响
1. 解决cloud computing中没有scalable storage system的情况。
2. 影响网络基础架构，latency-driven network design
3. 影响数据中心的管理，considering more about latency
4. 影响服务器架构，比如说加个电源。

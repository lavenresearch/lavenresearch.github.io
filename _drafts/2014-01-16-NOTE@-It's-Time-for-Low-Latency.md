---
layout: post
category : Network
tagline: ""
tags : [performance]
---
{% include JB/setup %}
It's Time for Low Latency - HotOS 2011

# OUTLINE
1. Introduction（ **latency 100μs to 5~10μs to 1μs** ）
    
    目前 network latency 的情况（需要使用特殊的软硬件实现 low latency ，主要用在HPC中，但是，作者认为在一般的数据中心里实现 low latency 是一个几年内可以实现的目标）。

    在一个非HPC的数据中心中实现 low latency 需要做出如下改变：

    - 应用可直接访问网卡，不再通过操作系统。
    - 设计新的网络协议
    - 一些硬件的提升
    - 从长期上考虑，将网卡和CPU集成在一起使更低的latency成为可能

2. latency 的组成

    Component |Delay |Round-Trip
    ----------|--|--
    Network Switch |10-30μs| 100-300μs
    Network Interface Card| 2.5-32μs |10-128μs
    OS Network Stack |15μs| 60μs
    Speed of Light (in Fiber) |5ns/m |0.6-1.2μs

3. latency 对应用的影响

    - 相对于NoSQL， low latency 意味着事务间冲突的概率变小，降低了处理冲突的开销，使NoSQL在性能降低不多的情况下提供更一般的接口。
    - 为了降低 latency ， client 需要将一个任务中的多个请求并行发出，因此在接收请求数据时造成了 client 处的拥塞。（ **为什么不采用流水线？** ）

4. low latency 是可以做到的
    
    - 在数据中心里，计算与存储设备都是集中放置的，因此可以不用考虑传输时延，在物理上是可以实现 low latency 的。
    - 新的交换机技术
    - 新的网卡技术
    - HPC中已经做到，只是难以推广（由于HPC倾向于将更多的工作交给网卡来做，使得其网卡比较贵而且不够灵活）

5. 需要对操作系统的改进

    - 以使用内存的方式使用网卡（应用直接访问）。
    - 重新设计网络协议，比如说TCP（TCP适用于单向大的数据传输，并不适合类似RPC的小的数据交换）。

6. 进一步提升

    信息应该直接在 on-chip cache 和 network 间传输，而不经过内存，因为把数据放进内存，网卡再从内存中读数据会造成大概100ns的延迟。

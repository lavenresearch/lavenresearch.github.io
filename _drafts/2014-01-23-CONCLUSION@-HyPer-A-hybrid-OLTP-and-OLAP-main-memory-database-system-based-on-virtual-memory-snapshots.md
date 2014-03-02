---
layout: post
category : memory
tagline: ""
tags : [one-size-fit-all , database]
---
{% include JB/setup %}

2014-01-22 23:51:44
## 研究动机
> 为什么研究的问题有意义，已有解决这个问题的方案是什么，为什么要改变这个解决方案。

1. OLTP(online transaction processing)

    + 使用 DataBase 进行数据存储， DataBase 特点为：
        * 运行在单机上（需要进行数据库 partition 以集群化[^nosql]）

    + 主要负载为 transaction ， 负载特点为：
        * 涉及数据量极少，可快速处理完毕
        * 交互式响应速度
        * transaction 满足 ACID 性质
        * WRITE and UPDATE transaction 占据很大一部分比例

2. OLAP(online analytical processing)

    + 使用 Data Warehouse 进行数据存储， Data Warehouse 特点为：
        * 使用列存储( column store )以提高统计性能。

    + 主要负载为 Business Intelligence(BI) OLAP queries ，特点为：
        * 设计数据量大，通常是全部数据的某个部分
        * 以 READ 为主，不会更改数据集
        * 一般需要产出统计结果，例如 aggregated sales statistics grouped by geographical regions, or by product categories.

3. OLTP and OLAP

    + 在一起的问题：
        * 在 OLTP 系统上执行 OLAP queries 会产生资源竞争( resource contention ) ，对 OLTP 的处理性能产生极大影响

    + 不在一起的问题：
        * Data freshness issue ( OLTP 的数据只能 periodically 向 OLAP 系统中导入[^data_import])
        * Resource consumption ( 因为要维护两个数据存储系统，而存储的数据在本质上市相同的，因此造成了资源浪费。)

4. 新的需求

    + Real time BI
        * 需要能够实时的对 OLTP 产生的数据进行 OLAP 的 BI 分析，使用两套分离的数据存储系统不能满足这个需求。
        * OLTP 和 OLAP 负载之间不相互影响
        * OLTP 相关的性能能够和 OLTP 专用系统[^oltp_system] 一样高效
        * OLAP 相关的性能能够和 OLAP 专用系统[^olap_system] 一样高效

## 解决方案
> 提出的解决方案是什么（描述），为什么这个解决方案要比原来的好（分析）。

解决方案中两个关键点为使用内存数据库( In-memory database ) 和 Snapshot。

1. HyPer 的特点
    
    + HyPer’s partitioning technique (cf. Section III-D) is primarily used for **intra-node parallelism** and is particularly beneficial for **multi-tenancy** database applications. 节点内并行，适合多用户共同使用
    + The concurrent transactional workload and the BI query processing use **multi core** architectures effectively without concurrency interference. 能够高效利用多核
    + a single server **scale up** system. 目前还存在于单节点上

2. In-memory database
    
    + 可行性分析
        * Business critical transactional database volume has **limited** size.[^limited_size] 即，数据全部放入一个机器的内存
        * the main memory capacity of commodity as well as high-end servers is growing faster than the largest business customer’s requirements. 因此将来也可以将数据全部放入内存
        * For transaction rate, it is fair to assume that the peak load will be below a few thousand order lines per second. 因此从 transaction 处理速率上来说也能够满足需求

    + 带来的好处
        * 可以采用 lock-less 的方式实现数据库[^lockless] ，从而避免相应的开销。[^lock_overhead]
        * 可以采用 page-shadowing 技术，因为 memory 的访问性能不受 data location 的影响，而对于 disk ， 顺序访问和随机访问区别很大。

3. Snapshot
    
    + OLAP 的 BI queries 在 OLTP transactional data 的 snapshot 上执行，因此不会影响到 OLTP 的性能
    + Snapshot 各种性质（ same , arbitrarily current , consistent ）的保证由硬件辅助完成（ Virtual memory management[^vmm] ）

## 评价方案及结果
> 如何验证解决方案的效果，分析实验结果得到的结论或者问题。

## 我的评价
> 亮点是什么，是否存在有争议的观点，判断是否具有应用场景并且可实现。

## 总结论文的贡献
> 不仅仅局限于论文所解决的问题，还包括提出的实验验证方法。

## 未来发展方向
> 未完全解决的问题，未完成的工作

## 我的问题
> 哪些东西看不懂，需要补充背景知识。

1. HyPer is a new **RISC-style** database systems like RDF-3X (albeit for a very different purpose). 什么是 RISC-style 数据库系统？

2. In HyPer we rely on hardware-supported **page shadowing** that is controlled by the processor’s memory management unit (MMU). For disk based database systems shadowing was not really successful because it destroys the **page clustering**. This hurts the **scan performance**, e.g., for a full table scan, as the disk’s read/write head has to be moved. HyPer is based on virtual memory supported shadow paging where scan performance is not hurt by shadowing. 这些到底是什么，及这些东西之间的相互影响是什么？ 



 [^nosql]: NoSQL 的出现也是为了解决数据库集群化的问题， automatic partition 将处理数据分布式的问题交给应用，因此每个应用对需要根据自己的需求增加或者更改数据库的功能。比如在使用 spanner 之前，是将 mysql 的数据库进行 partition 并且由应用维护 partitions 之间的关系。

 [^data_import]: 这个过程一般在深夜，而且由于 OLTP 数据存储格式和 OLAP(column store) 中不同，因此这个过程可分为：Extract-Transform-Load(ETL) 三个阶段。

 [^oltp_system]: VoltDB(H-store) , TimesTen 等。

 [^olap_system]: MonetDB , TREX 等。

 [^limited_size]: 根据文章中的估算， amazon 的交易数据库一年只产生 54GB ，而目前有 TB 级内存的机器。另外， RAMCloud 中也提出数据可以全部放在内存中。
 
 [^lockless]: 数据库系统使用内存进行数据存储，可以使 transaction 在很短的时间内处理完成，避免了 disk IO ，因此不需要多个 transactions 之间的 CPU 复用以提高资源利用率。从而是 lock-less 可实现。

 [^lock_overhead]: 在论文 H-Store 中有详细分析。
 

 [^vmm]: address translation, caching, copy on update.

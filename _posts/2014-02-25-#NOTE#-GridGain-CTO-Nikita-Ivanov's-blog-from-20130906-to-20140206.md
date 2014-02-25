---
layout: post
category : memory
tagline: ""
tags : [in-memory,cache,big data,hadoop]
---
{% include JB/setup %}

# Notes on [GridGain CTO's blog](http://blog.gridgainsystems.com/)
Time range: from 20130906 to 20140206

GridGain5.2 产品结构：
![](./gg_stack_670.png)

## Cache < Data Grid < Database
1. in memory distributed cache 
    1. improve data availability
    2. fundamental data management capabilities
2. in memory data grid 
    1. above all
    2. basic capabilities to move the computations to the data
3. in memory data base 
    1. above all
    2. distributed MPP processing based on standard SQL and/or MapReduce

In-memory database 与 In-memory cache 的不同在于增加了计算管理，并提供更加复杂的数据处理接口（比如说: mapreduce）。

>  in-memory databases were developed to respond to the growing complexities of data processing. It was no longer enough to have simple key-based access or RPC type processing. Distributed SQL, complex indexing and MapReduce-based processing across TBs of data in-memory are necessary tools for today’s demanding data processing.

## Why Oracle and SAP Are Missing The Point Of In-Memory Computing.
>  In-Memory Computing is much more significant than just getting a slow SQL database to go faster.

1. 内存计算将用于比RDBMS更广泛的领域，因此纯SQL是不够的。
    * in high performance computations:
        - use case: anything from traditional MonteCarlo simulations, video and audio processing, to NLP and image processing software. 
        - MPI, MapReduce or MPP are needed for use cases above.
    * in streaming and CEP(Complex Event Processing)
        - use case: ingest hundreds of thousands of events per seconds and process them in real time
        - sliding window processing, streaming indexing and complex distributed workflow management are need for use case above.

使用内存存储数据带来的巨大性能提升能够为更多类型的应用带来变革。

## Hadoop – 100x Faster. How we did it…
In-Memory Hadoop Accelerator 的目标：最小的迁移代价，使 mapreduce 程序享受到 in memory 带来的巨大性能提升。

这是 In-memory 在大数据存储及处理上的应用。（不仅仅局限于数据库了！！）

1. In-Memory File System
    * ![](./in_memory_hadoop2_white.png)
    * standalone version(file level cache)
        -  trades capacity for maximum performance.(**内存的容量还是会有限制**)
    * caching HDFS(block level cache)
2. In-Memory MapReduce
    * 优化 mapreduce 的执行流程。消除 Hadoop job tracker polling, task tracker process creation, deployment and provisioning 等对性能的影响。

## Distributed Caching is Dead – Long Live…

1. 内存数据库技术（SAP HANA，Oracle ......）的发展使 cache 不再必要。
2. 客户将更多**种类**的数据放入内存，对内存的数据存储提出了更多要求。key-value形式的cache已经不能满足需求，例如，需要有数据索引以方便事务处理等！
3. 客户需要更复杂的数据处理功能，单纯的数据存储是没有用的，因此需要重新设计，使计算和数据存储紧密的关联在一起。

**One-size-fit-all**的需求：
> What we are finding as well is that just SQL or just MapReduce, for instance, is often not enough as customers are increasingly expecting to combine the benefits of both (for different payloads within their systems).

## Four Myths of In-Memory Computing
内存和块存储十分不同，访问内存省去了访问块存储需要的一系列额外操作，包括与OS IO相关的操作，与IO控制器相关的操作。而块设备SSD相对于HDD只是提高了寻道时间！！[^ssd]
### Memory-First Principle
RAM is different from block-level devices like HDD or SSD.
* it completely eliminates the traditional overhead of block-level devices including marshaling, paging, buffering, memory-mapping, possible networking, OS I/O, and I/O controller.
* to read a record from block level devices: Your code will have to deal with OS I/O, buffered read, I/O controller, seek time of the device, and de-marshaling back the byte stream that you get from it to an object representation that you actually need. 

### Four Myths
1. 太贵
    * 内存价格下降的趋势和磁盘一样
    * 1TB的内存集群价格已经在20K~40K dollar 了
    * 价格已经不是主要考虑标准了，还要考虑发热，占地，能耗等因素
    * 新的技术： **Memory Channel Storage (MCS)** [^mcs]
2. 无可持续性
    * 内存数据库有一系列措施来备份数据
        - in-memory backups, durable storage backups, disk-based swap space overflow, etc
        - 层次存储（tiered storage），允许用户设定数据存储的位置：内存，localdisk，RDBMS/HDFS
    * 内存数据库是用来存储 operational datasets 的，historical datasets 依然由 enterprise data warehouse (EDW), backup or offline storage services – like Hadoop 来存储。这些存储系统中依然使用disk。
3. flash足够快
    * 对于某些应用场景来说，flash还是不够快
4. 只有内存数据库
    * 除了数据库或cache，流处理将会是内存计算的一个巨大应用场景。因为流计算的大数据量和实时要求会堵塞任何disk IO。

[^ssd]:  Note that SSDs and Flash-on-PCI-E only improves portion of the overhead related to seek time of the device (and only marginally).

[^mcs]: http://blog.gridgainsystems.com/why-mci-means-rapid-in-memory-computing-adoption/

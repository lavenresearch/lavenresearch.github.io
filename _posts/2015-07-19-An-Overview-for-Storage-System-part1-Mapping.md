---
layout: hpost
category : Storage
tagline: ""
tags : [distributed storage system,GFS,object storage,file system,key value store]
---
{% include JB/setup %}

# 存储系统综述 Part 1 -- 龙星计划课程总结

课程名称 ： [文件系统和分布式数据管理系统](http://stlab.wnlo.hust.edu.cn/dragonstar/)

授课教师 ： [江松](http://www.ece.eng.wayne.edu/~sjiang/) Wayne State University

课程内容 ： [Local File System]("/docs/Lecture1-localFS.pdf"), [Distributed File System]("/docs/Lecture2-DFS.pdf"), [Key-Value Store]("/docs/Lecture3-KV.pdf")

参考资料 ： [Operating Systems Three Easy Pieces]("/docs/Operating Systems Three Easy Pieces.pdf")

1. File Systems
1.1 Files and directories
1.2 File system implementation
1.3 FSCK and journaling
1.4 Log-structured file system (LFS)
1.5 Data integrity and protection
2. Distributed File Systems and Others
2.1 Replication, consistency, and fault tolerance
2.3 Google’s GFS file system
2.4 The Ceph distributed file System
2.5 Facebook’s Haystack: Facebook’s photo storage
2.6 Microsfot’s Flat Datacenter Storage
3. Key-Value Data Management Systems
3.1 Earlier KV stores: FAWN, SkimpyStash,and BufferHash stores.
3.2 SILT: a memory-efficient key-value store
3.3 LevelDB: a key-value store based on LSM tree from Google
3.4 The LSM-trie KV store for very large set of small data

所谓存储系统其实是一个纽带，连接人与存储介质，其中存储介质包括CPU cache，内存，磁盘，固态盘，光盘等。存储系统作为纽带的一个重要功能就是，为存储设备封装一个对人类来说易用的接口。直接使用存储设备的复杂之处在于需要记住哪一块数据在设备的哪一个地方，除此之外还需要根据设备的特性做优化。总体来说包含两件事情：

- mapping（数据在设备中的地址 to 人访问数据使用的地址）
- 利用存储设备的硬件特性

## 所有 Mapping 的概述

总体来说，实现 Mapping 有两种方式，一个是将存在的一一对应关系保存下来，需要用的时候搜索保存下来的信息；另一个是制定一种映射的规则，需要用的时候根据规则进行计算。

上述两种 Mapping 方式，前者灵活（对应更多的映射方案），后者简单（对应更小的查询开销）。对于前者，一种减少查找开销的办法是使用多层次的树形结构（能够减小开销的原因是，将查找时的全局搜索，缩减到对某一个子树的搜索），其中最具代表性的就是文件系统中的目录树。

## CPU Cache 中的 Mapping

CPU cache 对软件程序员来说是透明的，程序在访问内存中的数据的时，会先查找 cache 看是否存在，不过这个查找过程由硬件自动执行。Cache 和一般的存储系统不同的地方在于，__数据可能不存在于 cache 中__。也因此，cache 中的 mapping 给出的其实是数据__可能__在的位置。

存在的映射关系为： 数据对应内存地址 to 数据可能在的 cache line

这里有三种 mapping 方式： 直接相连（一个内存块关联特定一个 cache line），n路组相连（一个内存块关联特定 n 个 cache line），全相连（一个内存块可以关联所有 cache line）

全相连的方式最灵活，内存块的数据可以被放在任意一个 cache line 中，这种情况下，可以提供__最优化的资源（cache lines）分配__。使用直接相连的方式时，若不同 cache line 对应的内存块被访问的热度不同，就会出现某些关联热点数据的 cache line 中数据被频繁的替换，而其他的 cache line 相对闲置。但是，相对于全相连，直接相连中__查找数据的操作更廉价__（因为对于内存块，只要查找一个 cache line 就可以确定数据是否存在于 cache 中，全相连需要查找所有的 cache line 才可以确定这一点）。n路组相连是直接相连和全相连之间的折中。

如果把每一个 cache line 看成是一个分布式存储系统中的一个节点，则可以发现分布式文件系统中数据定位涉及到的 Mapping 其实本质上和这里是一样的。同样是需要在__数据分布的灵活性__和__数据定位操作开销__之间做出权衡。

## 内存中的 Mapping

## 文件系统中的 Mapping

## Blob 存储系统中的 Mapping

## 分布式系统中的 Mapping









---
layout: hpost
category : Storage
tagline: ""
tags : [distributed storage,system,GFS,object storage,file system,key value store]
---
{% include JB/setup %}

# 存储系统综述 Part 2 ( 适应硬件 )

存储系统的设计一个重要的方面是如何利用硬件的特性实现特定的目标（包括性能，可靠性等）。因此，新的硬件的产生会导致存储系统层面的变革。例如，现在研究针对 SSD 如何做存储系统，以及基于 NVRAM 存储数据的研究。

## 基于内存的 Key Value Store

memcache 的内存管理方案。

slob的划分。

使用slob方案的原因，对于块存储设备，就没有使用 slob 而是直接顺序存储数据。有这个区别的原因是：内存资源较少。因此内存资源面临着需要尽快能够被重用的问题。使用slob以避免数据删除和更新所造成的空洞。硬盘没有这个考虑，因为硬盘容量大，可以等到垃圾回收后再重用资源。

## 基于块设备的 Key Value Store

共识：写的时候要顺序写。

继承了 log-structure file system 的思想和方法。包括读，更新，删除等操作。
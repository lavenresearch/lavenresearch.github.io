---
layout: post
category : memory
tagline: ""
tags : [iteration , big-data]
---
{% include JB/setup %}
2014-01-20 15:10:24
## 研究动机
> 为什么研究的问题有意义，已有解决这个问题的方案是什么，为什么要改变这个解决方案。

为用户能够更好的利用cluster中的内存资源，RDDs实现了一个为优化应用中 **data reuse** 的分布内存的抽象[^target] ， 功能包括 **fault-tolerant** ， user defined data partitioning and other rich set of operators to manipulate data。

mapreduce 和 dryad 等 computing framework 只对 cluster 中的计算资源进行了抽象，没有提供 cluster 内存的抽象，因此用户无法优化内存使用以提高应用的效率[^iterative_application]。而已有的解决这个问题的方案如:  Pregel , HaLoop , 只是对某种特定的计算方式的内存使用进行优化，其对内存的使用是隐式的，没有向用户提供使用 cluster 内存的方式。因此这两个方案的应用范围有限。

已有的 cluster 内存抽象机制由于使用了细粒度的数据更新，导致必须使用副本或日志进行容错，引入大量网络数据传输，相对于内存的带宽，网络成为性能提升的瓶颈。RRDs提供粗粒度的数据更新[^coarse_grained_transformations],因此，避免使用需要大量数据传输的容错方式。

## 解决方案
> 提出的解决方案是什么（描述），为什么这个解决方案要比原来的好（分析）。

Formally, an RDD is a **read-only**, **partitioned collection of records**. RDDs can only be created through deterministic operations on either (1) data in stable storage or (2) other RDDs.


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


[^target]: 存储的数据为计算的中间结果，重点在于利用内存进行数据暂存。与 RAMCloud 不同的地方在于， RAMCloud 目标在于存储计算的最终结果，是一个数据存储系统。

[^iterative_application]: 对于 iterative application ，例如，机器学习，图处理，数据挖掘等，在计算之间 reuse data ，可以将中间数据存储在内存中以提高性能。

[^coarse_grained_transformations]: 由于并行应用天然会将同一个操作应用到多个数据条目上，因此，使用粗粒度的数据更新依然可以表达多种计算模型。

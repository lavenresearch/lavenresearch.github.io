---
layout: post
category : Research
tagline: ""
tags : [method]
---
{% include JB/setup %}

BASIC CONCEPTS FOR RESEARCHING
## SPEEDUP
在并行计算中，SPEEDUP是指，任务顺序执行时间是并行执行时间的多少倍。

> Speedup is defined by the following formula:
> S(p) = T(1)/T(p)
> where:
> p is the number of processors
> T(1) is the execution time of the sequential algorithm
> T(p) is the execution time of the parallel algorithm with p processors

在论文 PACMan（NDSI'12） 中 SPEEDUP 的意义是：内存cache命中时，task执行的时间是内存不命中时其执行的时间的倍数。（正好和上面定义成倒数关系）

## CDF
> In probability theory and statistics, the cumulative distribution function (CDF), or just distribution function, describes the probability that a real-valued random variable X with a given probability distribution will be found at a value less than or equal to x. In the case of a continuous distribution, it gives the area under the probability density function from minus infinity to x.

CDF是一个函数: f(x) = P(X<=x)
其中：
自变量是 x ， x 的取值范围是随机变量 X 的值域。
f(x)的值为随机变量 X 的值不大于 x 的概率。
随机变量 X 本质上也是一个函数，该函数的自变量是一个随机事件，该函数的值是一个随机事件对应的一个值。

以论文PACMan（NSDI'12）中的figure 9为例：

    Figure 9: Skewed popularity of data. CDF of the access counts of the input blocks stored in the cluster
    其中每一个block是一个随机事件，对应一个access counts.
    随机变量 X 为： access counts of the blocks
    CDF的自变量 x 为： access counts
    f(x) 的意义为 access counts <= x 的 blocks 在所有 blocks 中占的比例

CDF的一个性质： P(a < X <= b) = f(b) - f(a)
因此从CDF的图上可以很容易的看出 x 在某一区间内随机事件发生的概率。
这个性质在PACMan例子中的意义为： a < access counts <= b 的 blocks 在所有 blocks中占的比例。

## MEDIAN & PERCENTILE
MEDIAN
> In statistics and probability theory, the median is the numerical value separating the higher half of a data sample, a population, or a probability distribution, from the lower half. The median of a finite list of numbers can be found by arranging all the observations from lowest value to highest value and picking the middle one (e.g., the median of {3, 3, 5, 9, 11} is 5). If there is an even number of observations, then there is no single middle value; the median is then usually defined to be the mean of the two middle values (the median of {3, 5, 7, 9} is (5 + 7) / 2 = 6), which corresponds to interpreting the median as the fully trimmed mid-range.

PERCENTILE
> A percentile (or a centile) is a measure used in statistics indicating the value below which a given percentage of observations in a group of observations fall. For example, the 20th percentile is the value (or score) below which 20 percent of the observations may be found.

MEDIAN is 50th PERCENTILE.

MEDIAN 意味着在一组数字中，有50%的数字小于MEDIAN，并且有50%的数字大于MEDIAN。因此MEDIAN的一个作用是用来估计一组数字其数值的分布情况。例如：

    如果已知一组数字的 MEDIAN 和 95th PERCENTILE， 意味着这组数字中有 45% 的数字在区间 (median , 95th percentile) 中，若这两个值比较接近，那么区间长度比较小，这一部分数字的分布就比较紧密，反之，其分布就比较稀疏。

## NETWORK LATENCY & THROUGHPUT & BANDWIDTH
LATENCY
>  In a network, latency, a synonym for delay, is an expression of how much time it takes for a packet of data to get from one designated point to another. In some usages , latency is measured by sending a packet that is returned to the sender and the round-trip time is considered the latency.
> The latency assumption seems to be that data should be transmitted instantly between one point and another (that is, with no delay at all). The contributors to network latency include:
> - Propagation: This is simply the time it takes for a packet to travel between one place and another at the speed of light.
> - Transmission: The medium itself (whether optical fiber, wireless, or some other) introduces some delay. The size of the packet introduces delay in a round trip since a larger packet will take longer to receive and return than a short one.
> - Router and other processing: Each gateway node takes time to examine and possibly change the header in a packet (for example, changing the hop count in the time-to-live field).
> - Other computer and storage delays: Within networks at each end of the journey, a packet may be subject to storage and hard disk access delays at intermediate devices such as switches and bridges. (In backbone statistics, however, this kind of latency is probably not considered.)

BANDWIDTH
> Commonly measured in bits/second is the maximum rate that information can be transferred.

THROUGHPUT
> The actual rate that information is transferred.
> Throughput is the number of messages successfully delivered per unit time. Throughput is controlled by available bandwidth, as well as the available signal-to-noise ratio and hardware limitations.

网卡（NIC）这部分的latency和bandwidth的区别：
网卡一次最多能够处理 X bit 数据，其中 X 一定的。一次处理需要用 N 个CPU周期，一个CPU周期为 T s，那么对于网卡来说:

- bandwidth = X/(NT) bit/s
- latency = NT s

即 latency 只关心数据在网卡上被处理的速度，使用的CPU周期越少，CPU越快，则 latency 越小，与网卡一次能够处理的数据多少没有关系。当 latency 很大的时候，如果网卡能够一次处理很多数据，那么其 bandwidth 还是可以很高。

## Availability vs. Reliability

Availability ：指应用或服务可用的时间，例如，一年中其正常运行的时间总和。

Reliability ：指发生失效的概率。

Availability 和 Reliability 之间的差距在于，当失效发生后，应用或者服务恢复正常所需要的时间。当这个时间很长时，即使 Reliability 很高（失效很少发生），其 Availability 也可能会比较低，反之亦然。



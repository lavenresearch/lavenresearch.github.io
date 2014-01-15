---
layout: post
category : memory
tagline: "NSDI'12"
tags : [cache , parallel]
---
{% include JB/setup %}
2014-01-14 10:38:12
## 研究动机
> 为什么研究的问题有意义，已有解决这个问题的方案是什么，为什么要改变这个解决方案。

1. 应用现状

    Data-intensive jobs 都存在一个 IO-intensive phrase 用来处理的 input data。这个 IO-intensive phrase 占据了整个 job 完成时间的79%，并且占用整个 job 69%的系统资源。而目前集群中的服务器拥有的大容量内存的利用率很低（95%的服务器内存利用率在42%以下）。而通过将 input data 在内存中 cache 能够加速 data-intensive jobs 的执行。

2. 应用特点

    Data-intensive jobs 的并行特性使得已有的 cache 策略并不适用。对于并行jobs来说，存在 all-of-nothing 性质，即jobs中的tasks的调度与执行有wave的特征。只有当一个wave中的tasks的input都有memory locality，即所有一个wave中tasks都提前完成时，整个job才会提前完成。

3. 应用要求

    因此必须要基于全局信息进行cache替换，保证一个wave中在不同服务器上运行的tasks所需的数据都在cache中。即 sticky policy.

4. 应用负载特征

    分析对象为 Facebook's hadoop cluster 和 Microsoft bing's dryad cluster 两个集群都有数千台服务器组成。

    1. JOB SIZES[^1] 服从 power-law distribution（即 small size jobs 占绝大多数）。正是因为这个特性是的一个job的input全部被放入内存有可行性。
    2. JOB SIZE 与 wave width 之前有联系（因此可以使用job size近似代替wave-width，在系统实现时job size很容易获得一些）。
    3. 大部分访问集中在少部分文件上。大文件被访问的概率更高。
    4. 存在数据重访问的特性，因此使用cache提升性能具有可行性（在facebook和bing的trace中只被访问了一次的文件分别只有11%和6%）。

## 解决方案
> 提出的解决方案是什么（描述），为什么这个解决方案要比原来的好（分析）。

1. 系统实现技巧
    
    1. **松耦合**：PACMan的实现很简单很巧妙，虽然基于hadoop，但是其基本功能和hadoop实现了松耦合，即，其cache策略并没有在hadoop的系统中实现，而是形成了一个独立的软件。这大大降低了这篇论文的成本。使作者能够更加专注于科研问题的解决。
        
        实现方式为在hadoop的每个slave上运行一个pacman的client，修改hadoop使其优先从pacman的client上读取数据。pacman client执行内存的cache管理操作并将cache信息传输给pacman coordinator形成集群的全局cache信息，并提供给替换策略。cache替换决策有替换策略给出。

    2. **寻求近似**：在理想状况下的各项参数在实际系统不能够轻易得到，此时应该使用其他容易得到的参数来代替理想情况下需要使用到的参数。从而简化系统的实现。

        1. 这本文中，LIFE通过优先cache wave width小的数据来提高jobs的平均完成时间。但是每个job的wave width在实际执行时是不断变化的，因此获得wave width的代价比较高，而有workload分析发现有job size和wave width之间有关联，因此采用job size代替wave width进行计算。
        
        2. 由于pacman是运行在文件系统层上的，无法获得job信息，因此将缓存一个job的完整输入近似为缓存整个文件。即假设一个job只读一个文件。这种假设对于小job是基本成立的。

2. 实际系统中面临的问题
    
    1. 总资源量不固定

        由于集群是在多应用间复用的，因此在其它应用的负载较轻时，会给数据处理分配更多的系统资源。因此虽然集群中的节点数量及配置并不会动态变化，但对于某一个应用，其能够拥有的资源总量是会动态变化的。


## 评价方案及结果
> 如何验证解决方案的效果，分析实验结果得到的结论或者问题。

1. 系统评价角度
    
    1. 总体评价
        
        对pacman分别和LIFE，LFU-F共同作用下整体效果进行测试。**_在进行总体测试的时候对负载进行分类_**，在这里，由于基于不同job size将jobs分装到5个bins里，使得可以清楚的看出pacman对不同job size的job的影响，使分析更透彻。

    2. 模块评价
        
        评价系统中各个模块对整体表现的贡献。为了显示sticky policy的重要性，本文分别对比了LIFE和LIFE(NO sticky)，LFU-F和LFU-F(NO sticky)，量化NO sticky对总体性能的影响，证明sticky policy的重要性。

    3. 对近似的评价
        
        由于在系统实现中使用了近似参数，因此要测试使用近似参数对系统的最终表现的影响。

    4. 和已有方案对比
        
        将pacman+replacement policy(LIFE,LFU-F)同已有cache策略（MIN，LFU，LFU）进行对比。证明新提出的理论是有效的。

    5. 对影响系统性能的因素的评估
        
        1. cache size（内存大小对系统性能的影响）
        
        2. scalability（PACMan client的吞吐量，pacman coordinator相应请求的并发数及时延）

2. 实验结果
    
    1. cache主要用于小文件，cache能够发挥作用的基础是，存在power-law distribution（小job占大多数）。
    
    2. LIFE（优先cache wave width小的数据，即小文件）在cluster efficiency上也有着良好的表现。因为cache了小文件后依然还有很大内存空间可以cache大文件。
    
    3. LFU-F（优先cache 访问频率高的文件，根据负载分析知道，为大文件）在average completing time上的表现不好，因为cache了大文件对小文件cache的干扰太大。

3. 实验方法
    
    1. scale down workload trace

        scale down workload trace 的目标是使其适合用来做实验的小规模集群，同时保持其在大规模集群上的负载特征，并且是小规模集群上实验结果能够反映在大规模集群上的真实情况。这里做的scale down是减小了input data size并且降低了每个机器用来做cache的内存。

## 我的评价
> 亮点是什么，是否存在有争议的观点，判断是否具有应用场景并且可实现。

1. 使用cache是否可作为一个长期解决方案？
    
    1. cache作用的对象是小文件，当应用需要的数据量变大时，要使cache机制产生很好的效果需要使cache的容量也变得也来越大。而cache存在的目标（通过少量的资源增加获得极大的性能提升）将变得不现实[^2]。此时cache就失去的存在的意义。
    
    2. 随着系统规模的变得越来越大，系统复杂性也越来越高，在这种条件下，越来越难以让cache发挥作用。本文提出应用方案的只针对一个特定的很应用场景（拥有一个IO intensive[^3]的input phrase的应用[^4]）。是否可以被广泛使用的情况不明。
    
    3. 作者使用cache而不是像ramcloud那样把全部数据都缓存到内存中的原因是：
        
        + JOB SIZE 有 power-law distribution（即小job占绝大多数）。
        
        + FACEBOOK 集群的 disk capacity 是 memory capacity 的 600 倍（潜台词是数据量远远超出内存可容纳的范围）。

        首先，pacman系统对大job的性能提升主要来源于小job的数据不足以占满cache，使得内存中仍然有足够的空间供大job的数据进行调度。也就是说如果针对于小job进行优化的话，为何不将小job的所有数据放在内存里保证其性能，而对大job采用别的方式进行性能优化。

        其次，关于disk capacity远远大于memory capacity还需要考虑的一点是disk上数据的分类，是否所有的disk上的数据相关的数据访问都有高吞吐低时延的要求，即是否所有的数据都需要被放在内存里？还有对这些远远超出内存能力的数据是否有cache的必要，即数据是否具有的重访问特征。

    4. 使用cache会使性能表现有很大变化（分别对应于cache hit 和 cache miss），使得QoS难以得到保障。

    综上所述，cache不是一个可以值得玩下去的游戏。以后提升系统性能的方式应该是对数据分类，将具有低时延的小数据完全放入内存即ramcloud，对于没有这个要求的数据放在磁盘内。

## 总结论文的贡献
> 不仅仅局限于论文所解决的问题，还包括提出的实验验证方法。

1. 发现parallel data intensive jobs的执行存在wave特征（wave-width个tasks被同时调度开始执行）。

2. 提出了对于wave内的tasks进行cache时存在all-or-nothing性质。

    指明只有所有parallel tasks都命中cache并提前完成时，整个input phrase才会提前完成。并且由于jobs中各阶段由于一般使用流水线的执行方式来提高效率，all-or-nothing性质还会影响到cluster efficiency（使下一阶段的程序空转等待最后执行完成的task）。

## 未来发展方向
> 未完全解决的问题，未完成的工作。

无

## 我的问题
> 哪些东西看不懂，需要补充背景知识。

无

[^1]: 衡量 job size 的两个指标: input data size and number of tasks.

[^2]: J. Ousterhout, P. Agrawal, D. Erickson, C. Kozyrakis, J. Leverich, D. Mazières, S. Mitra, A. Narayanan, D. Ongaro, G. Parulkar, M. Rosenblum, S. M. Rumble, E. Stratmann, and R. Stutsman, “The Case for RAMCloud,” Commun. ACM, vol. 54, no. 7, pp. 121–130, Jul. 2011.

[^3]: 在论文 MixApart: Decoupled Analytics for Shared Storage Systems （FAST'13）中提到 mapreduce 的 map phrase 是 **CPU Intensive** 的，而且其引用的文献是本篇论文作者写的另一篇论文。太不靠谱了。。。到底是什么！？-_-|||

[^4]: 作者给出了两个例子，mapreduce中的map phrase，dryad中的extract phrase。这两种都是批量数据处理的例子。在其它类型的应用中是否也存在这种合适cache发挥作用的场景不清楚，例如，NOSQL。

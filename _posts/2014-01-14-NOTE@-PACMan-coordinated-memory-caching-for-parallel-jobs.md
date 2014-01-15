---
layout: post
category : memory
tagline: "NSDI'12"
tags : [cache , parallel]
---
{% include JB/setup %}
PACMan: coordinated memory caching for parallel jobs
# OUTLINE
This paper have clarified three things.

1. all-or-nothing property for parallel tasks: only all of the tasks input data cached in memory contributed to completion time reduction and cluster efficiency.
2. average completion time can be minimized by evicting large incomplete inputs. By favoring small wave width jobs.
3. cluster efficiency can be maximized by evicting less frequently accessed inputs.

## 工作的整体介绍
1. 数据处理中tasks，wave-based的执行方式。
2. wave-based执行tasks的方式引出使用内存cache，对并行tasks执行条件下all-or-nothing的性质。
3. 协同cache框架PACMan。（addressing all-or-nothing）
4. 基于PACMan的替换策略LIFE。（减少jobs的平均完成时间）
5. 基于PACMan的替换策略LFU-F。（提高集群利用率）
6. 基于PACMan和两种替换策略的实验结果。

## 详细说明
1. all-or-nothing性质存在性说明及验证
2. LIFE对于降低平均完成时间的有效性的证明
3. LFU-F对于提高集群利用率有效性的证明

## 负载分析
1. Input sizes of jobs（tasks数量和input sizes）对满足all-or-nothing性质可行性及LIFE有效性的验证
2. Large file are popular（对LFU-F有效性的验证）

## 系统设计
1. PACman
2. LIFE和LFU-F与PACMan的整合

## 实验
1. 实验平台介绍及对workload的处理（使其能够运行在小规模集群上，有可以真实的反应实际系统的状态）
2. PACMan的效果
3. LIFE和LFU-F的效果
4. 传统cache替换策略的效果
5. cache size的影响
6. 系统的可扩展性

## 对PACMan的提升
1. 最优替换策略
2. 预取


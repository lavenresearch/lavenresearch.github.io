---
layout: hpost
category : Storage
tagline: ""
tags : [distributed storage system,GFS,object storage,file system,key value store]
---
{% include JB/setup %}

# 存储系统综述 -- 龙星计划课程总结

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
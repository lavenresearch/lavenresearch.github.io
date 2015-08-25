---
layout: hpost
category : python
tagline: ""
tags : [python,programming,multiprocessing]
---
{% include JB/setup %}

Reference:

1. [Parallelism and Serialization how poor pickling breaks multiprocessing](http://matthewrocklin.com/blog/work/2013/12/05/Parallelism-and-Serialization/)
2. [multiprocessing problem and some solutions on stack overflow](http://stackoverflow.com/questions/1816958/cant-pickle-type-instancemethod-when-using-pythons-multiprocessing-pool-ma)
3. [Python Docs - multiprocessing](https://docs.python.org/2/library/multiprocessing.html#multiprocessing.Process.join)
4. [multiprocessing – Manage processes like threads](https://pymotw.com/2/multiprocessing/index.html)

# 使用 multiprocessing 的注意事项

传给进程对象的用以执行的目标函数及参数需要是能够被 pickle 序列化的。即，lambda 表达式，对象的方法（methods），Closure ，交互式的函数都不行。

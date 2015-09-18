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
5. [multiprocessing 的设计目标](http://iswwwup.com/t/008271c1f33d/python-multiprocessing-and-independence-of-children-processes.html)
6. [how do you create a daemon in python](http://stackoverflow.com/questions/473620/how-do-you-create-a-daemon-in-python)
7. [访问其他进程内存空间的方法](http://unix.stackexchange.com/questions/6301/how-do-i-read-from-proc-pid-mem-under-linux)

# multiprocessing 概述

## 设计目标

设计 multiprocessing 库的目标是为了提高程序的并发度，从而更好的利用多核 CPU 的计算资源。 multiprocessing 使用接口很大一部分是仿照 threading 库的，使用 multiprocessing 可以避开 CPython 实现中线程的全局解释器锁（Global Interpreter Lock）。GIL 使得多个线程在执行时必须顺序执行，因此使得 CPython 中的多线程只能够在有大量 I/O 等待时才能提高性能。而是用 multiprocessing 能够绕过这一限制。

另外，multiprocessing 中用于进程通信的 Manager 类可作为服务器接收发送数据，并且能够支持大部分 python 中的对象，因此，multiprocessing 还能够提供一种分布式程序的实现方式。

## 参数传递

需要传递给新的进程的参数包括，目标函数（或类），以及目标函数（或类）需要接收的参数。

然而，传给进程对象的用以执行的目标函数及其他参数需要是能够被 pickle 序列化的。即，lambda 表达式，对象的方法（methods），Closure ，交互式的函数都不可以作为参数传给 `multiprocessing.Process` 类。

## 进程之间的关系

所有使用 multiprocessing 创造出来的进程是与父进程共存亡的。 multiprocessing 会尽力避免出现孤儿进程（ orphaned processes ）的情况。因此，在主进程终止时，它会将其创建的子进程都终止掉。

使用 multiprocessing 创建的进程有两种模式，daemon 和 non-daemon。这两种进程的区别是，non-daemon 的进程会阻塞父进程终止，即，父进程需要显式的执行子进程终止操作或者等待子进程执行完毕后才能结束。而 daemon 子进程不会阻塞父进程结束，但是，父进程在退出时会自动杀死子进程。当然，父进程也可以调用 join 方法等待子进程结束。

但是，其实有个[BUG](http://stackoverflow.com/questions/13095878/deliberately-make-an-orphan-process-in-python)。

即，使用父进程创建一个子进程后，子进程再创建一个自己的子进程。父进程使用 terminate 方法终止子进程，这子进程创建的进程就成了 orphaned process。而且，由于父进程创建的子进程已死，父进程可以不受阻塞而退出。这里的原理大概是，terminate 方法终止子进程的方式类似于 kill 9 ， 因此子进程没有机会执行自己清理自己子进程的操作。

# 相关的包

## subprocess

subprocess 用于执行外部命令。 与使用 subprocess 启动的进程进行交互的途径是标准输入，标准输出及管道，因此，向使用 subprocess 创建的进程传递数据时，需要先将数据序列化然后发送出去。这一点和 multiprocessing 有本质的不同， multiprocessing 创建的进程之间是可以共享内存的。 例如，使用 subprocess 执行一个 python 程序，其本质是启动另一个 python 解释器去执行该程序。而两个 python 解释器之间是没有办法共享内存的。（使用 C 语言，或者 python 中的 Ctype 可以读取其他进程内存空间，但这已经超出纯 python 程序的能力范畴。）

subprocess 创建的进程之间是不需要共存亡的。子进程不会阻塞父进程退出，父进程也不会在退出的时候杀死子进程。

其实 Python 解释器是不会自动终止进程的，multiprocessing 清理子进程的功能是其专门实现的。

## os

os 包中有一个 fork 方法可以用于创建进程，这里的 fork 方法和 linux 的系统调用 fork 应该是相同的。

# 创建 Daemon 进程

使用 subprocess 可以创建 daemon 进程，但是，存在上述需要传递数据的弱点。

创建 Daemon 进程还可以直接使用 os.fork() ， [一个例子](http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)。 不过使得 daemon 进程比较具有可用性还不是很容易。[PEP-3143](https://www.python.org/dev/peps/pep-3143/)

还有其他各种各样的包实现了创建 daemon 进程的功能，其中用的比较多的一个是 [python-daemon](https://pypi.python.org/pypi/python-daemon/) 。


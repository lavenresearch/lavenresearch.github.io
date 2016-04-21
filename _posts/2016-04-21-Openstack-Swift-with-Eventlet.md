---
layout: hpost
category : openstack
tagline: ""
tags : [linux, swift, openstack, epoll]
---
{% include JB/setup %}

# Eventlet 原理概述

## 如何实现异步

参考资料：

[openstack分析 eventlet](http://blog.csdn.net/fengkun32/article/details/42293949)

### greenlet 实现了什么？

[greenlet docs](https://greenlet.readthedocs.org/en/latest/)

在程序执行的时候，通过 greenlet 就可以方便的在一个程序的各个部分之间跳来跳去。

```python
from greenlet import greenlet

def test1(x, y):
    # 为什么可以用 gr2, 因为这其实是接着最下面 switch 处执行，在那里， gr2 是已经定义过了的
    # 跳去执行函数 test2
    z = gr2.switch(x+y)
    print z

def test2(u):
    print u
    # 跳去执行函数 test1, 跳回去以后会接着跳过来的地方执行。42 为 gr2.switch(x+y) 的返回值
    gr1.switch(42)

# 用函数 test1 创建一个 greenlet
gr1 = greenlet(test1)
# 用函数 test2 创建一个 greenlet
gr2 = greenlet(test2)
# 跳去执行函数 test1，("hello", " world") 为传给 test1 的参数
gr1.switch("hello", " world")
```

> This prints “hello world” and 42, with the same order of execution as the previous example. Note that the arguments of test1() and test2() are not provided when the greenlet is created, but only the first time someone switches to it.
Here are the precise rules for sending objects around:

> `g.switch(*args, **kwargs)`

> Switches execution to the greenlet g, sending it the given arguments. As a special case, if g did not start yet, then it will start to run now.
Dying greenlet

> If a greenlet’s run() finishes, its return value is the object sent to its parent. If run() terminates with an exception, the exception is propagated to its parent (unless it is a greenlet.GreenletExit exception, in which case the exception object is caught and returned to the parent).

现在假设我管着了一大批 greenlet：`[gr1, gr2, ..., grn]`，然后我根据需要选择其中一个 greenlet 执行 `gri.switch()`。这就是 eventlet 里面 hub 干的两件事之一。上面这段英文很好的描述了 greenlet 的行为特征，需要认真看看。


### 获取系统的提供的 events

[python select module](https://pymotw.com/2/select/)

有了一堆 greenlet 后，根据什么东西选择要执行的那一个？

作为一个 web server，理想的情况就是，有好多个 clients 同时和我连着，但是我不知道谁会发数据过来，因此我就需要等着所有人，然后谁发数据过来我就把谁的数据处理一下然后把结果返回给他。于是问题是，谁什么时候发数据过来了我怎么知道？

这一点需要在操作系统中实现，有通用的 select, Linux 中的 epoll，BSD 中的 kqueue。一般的过程是这样的：

- 网络中有数据过来，产生中断
- 中断被交给相应的 device driver 进行处理
- device driver 处理好以后交给操作系统
- 操作系统交给 epoll (linux)
- epoll 交给用户态的程序
- 用户态的程序跳转到对应的代码段进行最终的处理

Python 中如果需要获取这样的 event, 就需要用到 select 模块(`import select`)。

在 linux 上的程序一般使用 select 模块中的 poll 接口，因为 poll 的效率比 select 接口的效率高很多。下面是 poll 主要的使用方法。 还有一个 epoll 接口，它主要的函数和 poll 差不多。

```python
import socket
import select

# 这有一个 非阻塞 并且已经开始 listen 的 socket： server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)
server_address = ('localhost', 10000)
server.bind(server_address)
server.listen(5)

# 下面定义了两种工作状态，也就是说再接下去，我们会把 sockets 们分成这两种
READ_ONLY = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
READ_WRITE = READ_ONLY | select.POLLOUT

# poller 就像一个枢纽，用户态想监控谁（文件句柄）相关的 events 就告诉 poller， 然后也可以通过 poller 把操作系统传上来的 events 取出来。
poller = select.poll()
poller.register(server, READ_ONLY) # 这就告诉操作系统了，我想监控 server 这个 socket

# 建立一个文件句柄到 socket 的映射
# 每个 socket 都有一个文件句柄，当数据来了，操作系统只知道这些数据是到哪个文件句柄上的
# 然而我们需要操作的是 socket, 因此，就需要通过文件句柄把对应的 socket 找到
fd_to_socket = { server.fileno(): server,}

while True:
    # 这就是在问了，都有什么 event 发生了？ 有的话就会被存在 events 这个变量里。
    # events 最后的结构是： [(fd, flag), (fd, flag), ...]
    events = poller.poll(TIMEOUT)
    # 下面就开始处理 event 了
    for fd, flag in events:
        # 找到 socket
        sock = fd_to_socket[fd]
        # 如果这个 event 对应的 socket 是什么什么状态
        if flag & (select.POLLIN | select.POLLPRI):
            if sock is server:
                # 接受新的连接，创建新的 socket
                connection, client_address = s.accept()
                connection.setblocking(0)
                fd_to_socket[ connection.fileno() ] = connection
                # 让操作系统开始监控这个新的 socket 相关的 event
                poller.register(connection, READ_ONLY)
            else:
                # 这个 sock 上的数据已经来了，把数据取出来
                data = sock.recv(1024)
                # 后面的我不关心了
                pass
        elif flag & select.POLLHUP:
            # 告诉操作系统，不要监控这个 socket 了
            poller.unregister(sock)
            sock.close()
        elif flag & select.POLLOUT:
            sock.send(next_msg)
        elif flag & select.POLLERR:
            # 告诉操作系统，不要监控这个 socket 了
            poller.unregister(sock)
            sock.close()
```

### Eventlet hub

[python eventlet并发原理分析](https://github.com/stanzgy/wiki/blob/master/openstack/inside-eventlet-concurrency.md)

Eventlet hub 把上面两件事集成在一起了。 eventlet 的结构如下：

```sh
_______________________________________
| python process                        |
|   _________________________________   |
|  | python thread                   |  |
|  |   _____   ___________________   |  |
|  |  | hub | | pool              |  |  |
|  |  |_____| |   _____________   |  |  |
|  |          |  | greenthread |  |  |  |
|  |          |  |_____________|  |  |  |
|  |          |   _____________   |  |  |
|  |          |  | greenthread |  |  |  |
|  |          |  |_____________|  |  |  |
|  |          |   _____________   |  |  |
|  |          |  | greenthread |  |  |  |
|  |          |  |_____________|  |  |  |
|  |          |                   |  |  |
|  |          |        ...        |  |  |
|  |          |___________________|  |  |
|  |                                 |  |
|  |_________________________________|  |
|                                       |
|   _________________________________   |
|  | python thread                   |  |
|  |_________________________________|  |
|   _________________________________   |
|  | python thread                   |  |
|  |_________________________________|  |
|                                       |
|                 ...                   |
|_______________________________________|
```

Eventlet hub 其实也没有什么调度算法在里面，eventlet 自带的几个 hub 本质上的区别在于获取系统 event 的途径不同。对于获取来的 events，会使用 for 循环一个一个把对应的代码执行一遍。 也可以实现自己的 hub。不过也就是对特殊的操作系统，现有的 hub 中没有可以获取其 event 时才需要自己实现一个。就 linux 而言，由于 epoll, poll, select 在事件中能够提供的信息十分有限，因此很难进行进一步的优化调度。而要有更多的信息，可能需要改动 linux 的 epoll 等系统调用。

poll hub 和 epoll hub 都继承了 BaseHub，BaseHub 不能直接使用，其中有些方法需要其继承者实现，BaseHub 中主要的方法包括：

```python
def add(self, evtype, fileno, cb, tb, mark_as_closed):
    """ Signals an intent to or write a particular file descriptor.
    The *evtype* argument is either the constant READ or WRITE.
    The *fileno* argument is the file number of the file of interest.
    The *cb* argument is the callback which will be called when the file is ready for reading/writing.
    """
def remove(self, listener):
def switch(self):
def wait(self, seconds=None):
def run(self, *a, **kw):
    """Run the runloop until abort is called.
    """
def abort(self, wait=False):
def schedule_call_local(self, seconds, cb, *args, **kw):
def schedule_call_global(self, seconds, cb, *args, **kw):
```

BaseHub 维护了一堆 listeners（listener 是一个类的实例，里面主要记录了这些信息 `evtype, fileno, cb, tb, mark_as_closed`） 的列表(READ, WRITE 各有一个 listener 的列表)。

poll hub 主要改了 add, remove 方法，增加了 wait 方法。

- add/remove 方法通知操作系统（增加/取消）监控给定文件句柄，即上一部分中 poller.register 和 poller.unregister
- wait 方法会收集来自操作系统的 events，根据 events 中的文件句柄，使用 BaseHub 中的 listeners 将相应的 listener 们找出来，然后，依次调用 listener 里的 cb，即当时 add 的时候指定的 callback 函数，这个函数里应该规定了，当 event 发生时要干什么。


## Eventlet pool 以及 wsgi

# Openstack Swift 中的 Eventle




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
def switch(self): # 跳回到 hub 所在的 greenlet， 这个 greenlet 在 hub 初始化的时候被指定为运行 hub.run(), 所以每次切回 hub 都会跳到 run 里面
def wait(self, seconds=None): # 收集来自操作系统的 events，读/写数据，以及后续操作
def run(self, *a, **kw): # hub 的主循环，hub 的 greenlet 就一直在执行这段代码，跳出去，回来，再跳出去，再回来，如此反复
    """Run the runloop until abort is called.
    """
def abort(self, wait=False):
def schedule_call_local(self, seconds, cb, *args, **kw):
def schedule_call_global(self, seconds, cb, *args, **kw): # 像 hub 中添加新的 greenlet 的入口，cb 就是会被 hub 执行的函数
def fire_timers(self, when): # 执行 hub 里 self.timers 中所有的 timer ，即，当前到了指定调用时间的所有 callback，一直到 callback 执行到需要 IO 的部分
def prepare_timers(self): # 将到点要被调用的 timers 全部放到 self.timers 里等待被执行。(从 self.next_timer 迁移 timer 到 self.timers 里)
```

BaseHub 维护了一堆 listeners（listener 是一个类的实例，里面主要记录了这些信息 `evtype, fileno, cb, tb, mark_as_closed`） 的列表(READ, WRITE 各有一个 listener 的列表)。

poll hub 主要改了 add, remove 方法，实现了 wait 方法。

- add/remove 方法通知操作系统（增加/取消）监控给定文件句柄，即上一部分中 poller.register 和 poller.unregister
- wait 方法会收集来自操作系统的 events，根据 events 中的文件句柄，使用 BaseHub 中的 listeners 将相应的 listener 们找出来，然后，依次调用 listener 里的 cb，即当时 add 的时候指定的 callback 函数，这个函数里应该规定了，当 event 发生时要干什么。

在程序里使用 hub 实现异步的流程：

- 应该是线程建立的时候就会自动创建 hub 的 greenlet， 我不确定
- 程序继续执行到 IO 处： `client_socket = sock.accept()`
    - eventlet 改了 socket 包，因此 accept 会自动调用 `hub.add()` 让操作系统监听对应于 sock 的 events
    - __在 socket IO 处会自动（即，不需要再程序里显式调用 switch） switch 到 `hub.run` 里__，在程序的最开始阶段没有其他的 greenlet，因此会停下来等来自 sock 的 events
    - 等到了 sock 相关的 events 之后，从 `hub.run()` 中 switch 到 sock 所在的 greenlet 继续执行。
    - 假设如果获得了新的 client_socket，下面应该就要把这个新的 socket 加入到 hub 的管理中去
- 获得 hub： `hub = hubs.get_hub()`
    - eventlet 改了 python 的 threading 模块，`hubs.get_hub()` 就是从 threading 中包含一个状态记录了当前 thread 的 hub
    - `threading = patcher.original('threading')`
    - `_threadlocal = threading.local()`
    - `hub = _threadlocal.hub`
- 为新获得的 client_socket 创建 greenlet： `g = greenthread.spawn_n(self._spawn_n_impl,function, args, kwargs, True)`
    - 这里的 function 即，从上面传下来的，要在 greenlet 里运行的函数
    - `greenthread.spawn_n` 创建的是 greenlet, `greenthread.spawn` 创建的是 GreenThread. 两个都可以。 这两者的区别在于，GreenThread 会将一个 greenlet 的返回和异常信息记录下来，而从 greenlet 本身是无法获取这些信息的。
- 将一个 greenlet 加入 hub 的管理： `hub.schedule_call_global(seconds, g.switch, *args, **kwargs)`
    - 这里 `g.switch` 中的 `g` 可以是一个 greenlet，也可以是一个 GreenThread.
    - 这里会形成一个 timer，加入到 hub 里， `hub.add_timer(timer)`
    - timer 里面包含要调用的函数， 以及规划的调用时间，以及一些状态。
- 继续运行，又到了 IO 处： `client_socket = sock.accept()`
    - 跳去执行 `hub.run()`， 和第一次不同的是，现在 hub 里的 `self.next_timers` 不为空了
    - 调用 `self.prepare_timers` 把 `self.next_timers` 里到了调度时间的 timer 转到 `self.timers` 里
    - 调用 `self.fire_timers` 依次将 `self.timers` 里的 timer 中的函数（g.switch）都调一遍， 即切到对应的 greenlet 里
        - timer 里的 greenlet 运行到 IO 处， switch 回到 `hub.run` 里继续调用剩下 timers 里的函数
    - 调用 `self.prepare_timers` 把 `self.next_timers` 里到了调度时间的 timer 转到 `self.timers` 里（）
    - 调用 `hub.wait` 开始等待 events。现在已经有两个 greenlet 在等待 IO 了。
        - 本质上是调用 `select.poll.poll`
    - 接收到 events, 依次调用 events 对应的 callback 函数（通过 event 找到 listener，调用 listener 里的 cb）
        - `client_socket` 相关的 event： switch 到 `client_socket` 对应的 greenlet 里，开始读写处理数据。执行结束后，switch 回 `hub.run` 继续循环
        - `sock` 相关的 event： switch 到 `sock` 对应的 greenlet 里，接收新的 `client_socket`。执行结束后，重复上述过程，再次遇到 IO 后 switch 回 `hub.run`

这里面最让人晕的地方是： 一个 greenlet 到了 IO 处，或者一个 greenlet 运行完了，都会自动 switch 到 `hub.run()` 的 greenlet 里去，都不需要显式调用 switch. 这归功于 eventlet 可以给 python 自带的 modules 打 patch 把他们都改了。

以上内容来自于 eventlet 源码。


## Eventlet 里的 greenpool 以及 wsgi

GreenPool 就是把 hub 及相关的 greenlet, GreenThread 封装在一起了。

使用 GreenPool 的例子：

```python
from eventlet import greenpool

def function(arg):
    pass

# 创建一个 pool
max_size = 2000
pool = greenpool.GreenPool(max_size)
sock = some listening socket
while True:
    new_socket = sock.accept()
    # 以下包括的工作内容有：get_hub, create greenlet, call schedule_call_global
    pool.spawn_n(function, new_socket)
    # spawn create GreenThread instead of greenlet
```

使用 `eventlet.wsgi` 最基本的只需要如下两点：

1. 创建好一个处于 listen 状态的 socket
2. 准备好 application 的入口函数： `some_funciton_name(env, start_response)`

然后执行： `wsgi.server( socket, some_funciton_name, .... )`。  wsgi 执行的过程和上面这个 GreenPool 的例子是一样的， 在他的那个 function 里有一些处理操作，并且调用传给它的 some_funciton_name 函数。

PS: 这里有一个网络小知识， 一个 socket 可以让多个进程都监听着。这种情况在曾经会导致惊群问题，不过在好久以前的内核里就已经修复了。

# Openstack Swift 中的 Eventlet

建立 socket 之后，会 fork N 个子进程，然后再每个子进程中调用 `eventlet.wsgi.server(sock, app)`， 其中 app 由 `paste.deploy.loadapp` 生成。

---
layout: hpost
category : Openstack
tagline: ""
tags : [openstack,Swift,object storage,python,key value store,swift middleware]
---
{% include JB/setup %}

Openstack Swift Middleware 的原理分析及实现

2015/7/30 13:27:13

__Python Setuptools__: [Dynamic Discovery of Services and Plugins](https://pythonhosted.org/setuptools/setuptools.html#dynamic-discovery-of-services-and-plugins), [Automatic Script Creation](https://pythonhosted.org/setuptools/setuptools.html#automatic-script-creation), [Python 打包及发布](http://lesliezhu.github.io/public/2014-11-13-python-packaging.html)

__Python Paste Deploy__: [Python paste deploy docs](http://pythonpaste.org/deploy/)

__Openstack Swift Middleware__: [Middleware and Metadata](http://docs.openstack.org/developer/swift/development_middleware.html)

在 openstack swift 中，可以对所有的 servers （proxy server, object server, container server, account server）使用 middleware 进行包装以实现自定义功能配置。 Middlewares 的添加和删除基于 python 的 paste deploy 框架。这里主要讨论，如何使用 python 为 swift 实现一个 middleware。 基本流程是：

- 将 middleware 程序打包并安装到系统中
- 在 proxy server 的配置文件设置启动 middleware

## Python 程序打包（setuptools）

Python 程序打包主要涉及三个方面：

- 程序包的格式
    + 包括 egg, wheel。类似于 java 中的 jar。可以使用 unzip 直接解压看到里面的内容。
- Python 程序包管理工具
    + 相当于 ubuntu 中的 apt-get, 或者 fedora 中的 yum.
    + easy_install 对应于 egg 格式的 python 包
    + pip 对应于 wheel 格式的 python 包
- Python 程序包生成工具
    + setuptools 为 distutils 的扩展，另外，distribute 被合并到 setuptools 0.7 之后的版本中。

### 使用 setuptools 打包

一般而言，项目的目录结构为：

~~~python
middlewareDir/ # 项目文件夹
|
|-- setup.py # 项目打包程序
|-- bin/ # 独立运行时使用的脚本
|-- |-- mwN
|-- middlewareName/ # 源代码
|-- |-- __init__.py
|-- |-- main.py
|-- |-- submodle/
|-- |-- |-- __init__.py
|-- data/ # 项目中包含的文档，配置等等需要一起打包的数据
~~~

需要注意的是， python 只认为包含文件`__init__.py`的文件夹为一个包。所以，文件夹 middlewareName 是一个包，包的名字就是 middlewareName。其中`setup.py`的内容为：

~~~python
from setuptools import setup,find_packages
setup(
    name = "middlewareName",
    version = "1.0",
    author = 'suyi',
    # packages = find_packages(), # 自动查找并添加当前目录下的所有包
    packages = 'middlewareName',
    scripts = 'bin/mwN',
    # install_requires = ['redis>=2.0'],
    entry_points = {'console_scripts':['middlewareName = middlewareName.main:main',],}
)
~~~

这个项目被安装后，系统中将有两条命令可以执行该程序`mwN`和`middlewareName`。项目打包和安装的命令为：

~~~shell
python setup.py bdist_egg
python setup.py install
~~~

Python 项目最终可以有两种功能：作为可独立运行的程序，作为库供其它程序调用。作为独立程序运行的时候需要给出运行程序的 python 程序脚本，该脚本可以通过 setuptools 自动生成（在setup.py中的`entry_points`部分，定义`console_scripts`）。在安装包的时候会自动将运行需要的脚本放到目录`/usr/bin/`中。这样就可以在任何位置直接执行。包 swiftclient 的运行脚本 swift 的内容为：

~~~python
#!/usr/bin/python
# PBR Generated from u'console_scripts'
import sys
from swiftclient.shell import main
if __name__ == "__main__":
    sys.exit(main())
~~~

值得注意的是，脚本 swift 中， 调用 swiftclient.shell.main 函数时没有给其传递参数。而实际上 swift 正常执行是需要参数的。swiftclient.shell.main 的实现如下：

~~~python
from sys import argv as sys_argv
def main(arguments=None):
    if arguments:
        argv = arguments
    else:
        argv = sys_argv
    ......
~~~

这样做的原因可能是因为，setuptools 并不能解析出函数调用的参数，因此自动生成脚本时只能使用无参调用。所以要在 main 函数里显式处理系统输入。而在 swiftclient 被当作是库使用的时候 main 函数会被有参调用。


### 将打包程序注册为插件

Setuptools 支持将打包的程序作为模块插入可扩展的应用或者框架（例如，swift）里。对于这种情况，作为可扩展的应用或框架首先要定义一个“`entry point group`”。而作为模块程序，在 setup.py 中的 entry_points 选项下需要在相应的 `entry point group` 中给出可以被直接调用的函数。

Swift 使用了 paste deploy, `entry point group` 是在 paste deploy 中定义的， swift 直接拿过来用了。 Swift 项目的 setup.cfg 中相关的内容为：

~~~ini
[entry_points]
paste.app_factory =
    proxy = swift.proxy.server:app_factory
    object = swift.obj.server:app_factory
    mem_object = swift.obj.mem_server:app_factory
    container = swift.container.server:app_factory
    account = swift.account.server:app_factory

paste.filter_factory =
    healthcheck = swift.common.middleware.healthcheck:filter_factory
    crossdomain = swift.common.middleware.crossdomain:filter_factory
    memcache = swift.common.middleware.memcache:filter_factory
    ratelimit = swift.common.middleware.ratelimit:filter_factory
~~~

其中 paste.app_factory 和 paste.filter_factory 就是 paste deploy 中定义的 `entry point group`。proxy server 中定义的 app_factory 函数和 healthcheck 中定义的 filter_factory 函数分别为：

~~~python
# proxy server
def app_factory(global_conf, **local_conf):
    """paste.deploy app factory for creating WSGI proxy apps."""
    conf = global_conf.copy()
    conf.update(local_conf)
    app = Application(conf)
    app.check_config()
    return app

# healthcheck middleware
def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    def healthcheck_filter(app):
        return HealthCheckMiddleware(app, conf)
    return healthcheck_filter
~~~

## middlewares 调用关系

app_factory 对应的是整个 WSGI 应用中核心的应用部分，这一部分不再往下调用而直接产生返回值。 filter_factory 对应的是核心部分之上的 wrappers, 即，swift 中的 middleware, 这一部分通过向下调用获取返回值（也可以不向下调用直接返回）。通过读取 proxy server（或者其他 servers）的配置文件中的 pipeline, 按照其中定义的顺序逐层进行调用。调用结构为：

~~~python
# [pipeline:main]
# pipeline = catch_errors gatekeeper healthcheck  proxy-server

WSGI_server(
    catch_errors.filter_factory(global_conf,**local_conf)(
        gatekeeper.filter_factory(global_conf,**local_conf)(
            healthcheck.filter_factory(global_conf,**local_conf)(
                proxy-server.app_factory(global_conf,**local_conf)
            )
        )
    )
~~~

## 实现 middleware

对于 Swift 来说，只要知道它需要调用的符合规范的 middleware 的函数的位置，就可以使用这个 middleware 了。告诉 Swift 的方法就是在 setup.py 中添加相应的 entry_points。一个完整的 setup.py 的例子如下：

~~~python
from setuptools import setup,find_packages

setup(
    name = "mystandalonemw",
    version = "1.0",
    packages = ['mystandalonemw',],
    entry_points = {'paste.filter_factory':['mystandalonemw = mystandalonemw.mystandalonemw:filter_factory',],}
)
~~~

其中，‘paste.filter_factory'指定这个entry_points的类型，即，用于哪一个可扩展应用或框架，这里是 paste, 因为 Swift 使用 paste 来管理这些东西。等号前面的“mystandalonemw”是一个 entry_point 的标识，在使用的时候，通过这个来指定，使用这个包里的这个 entry_point。等号后面的内容用于指定这个 entry_point 对应的函数。

执行了`python setup.py install`之后，这个包对应的 egg 文件会被放到 python 相应的 site-packages 目录里，并且这个包的文件名也被会加入到 easy-install.pth 文件中以进行索引（egg文件的路径和文件名只有被加入到这个文件内才可以被 python 找到）。setup.py 中设定的 entry_points 信息被保存在 egg 文件里的 `EGG-INFO/entry_points.txt` 中。 `EGG-INFO/entry_points.txt` 的内容为：

~~~ini
[paste.filter_factory]
mystandalonemw = mystandalonemw.mystandalonemw:filter_factory
~~~

Paste 就是用这部分的信息定位实际需要调用的函数。

## 使用 middleware

在 Swift 中使用 middleware 需要在 proxy-server.conf 进行配置。主要有两步：

- 在 pipeline 中增加 mystandalonemw
- 配置 mystandalonemw

proxy-server.conf 中相关的配置如下，其中 mystandalonemw#mystandalonemw 分别对应于包的名字和 entry_point 的名字。myconf 为属于 mystandalonemw 的配置信息。在具体的函数中这个配置为字典的形式。

~~~ini
[pipeline:main]
pipeline = catch_errors gatekeeper healthcheck proxy-logging mystandalonemw proxy-server

[filter:mystandalonemw]
use = egg:mystandalonemw#mystandalonemw
myconf = latency is 1000ms
~~~

使用配置的方法：

~~~python
import os
import time
from swift.common.swob import Request, Response

class mystandalonemw(object):
    def __init__(self, app, conf):
        self.app = app
        self.conf = conf
    def __call__(self, env, start_response):
        req = Request(env)
        f = open("/home/suyi/mymiddle"+str(time.time()),"w")
        f.write("\n"+str(req)+"\n"+str(env)+"\n"+str(self.conf))
        f.close()
        print self.conf.get("myconf")
        return self.app(env, start_response)

def filter_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    def mystandalonemw_filter(app):
        return mystandalonemw(app, conf)
    return mystandalonemw_filter
~~~

# 补充说明

## 2015/8/31 19:53:37

最初将 openstack swift middleware 的代码划分为多个 python 文件，但是，proxy-server 无法启动，提示信息是除了主文件外的其他 python 文件找不到，于是，将其他文件中的代码放入主文件才可以运行。主文件为在 setup.py 中指定的 entry_point。
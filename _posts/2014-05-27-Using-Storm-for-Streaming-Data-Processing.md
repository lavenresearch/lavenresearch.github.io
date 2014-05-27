---
layout: post
category : Streaming
tagline: ""
tags : [stream,real time,deploy,install,usage,storm]
---
{% include JB/setup %}

20140527
# Storm 的部署及使用
## Storm程序执行环境部署
### 准备工作
#### 安装JAVA
从Oracle的网站上下载[Java SE 6](http://www.oracle.com/technetwork/java/javasebusiness/downloads/java-archive-downloads-javase6-419409.html)。下载Java的历史版本需要注册Oracle账号。

Java环境的安装过程如下：

    chmod 775 jdk-6u45-linux-x64.bin
    yes | jdk-6u35-linux-x64.bin
    mv jdk1.6.0_35 /opt
    ln -s /opt/jdk1.6.0_35/bin/java /usr/bin
    ln -s /opt/jdk1.6.0_35/bin/javac /usr/bin
    JAVA_HOME=/opt/jdk1.6.0_35
    export JAVA_HOME
    PATH=$PATH:$JAVA_HOME/bin
    export PATH

PS：
1. /opt 是用来安装除了默认安装之外的所有的软件和包
2. 在SUSE下，永久保存环境变量的方法是，在 /etc 下建立 profile.local 文件，写入上述环境变量相关的命令。

#### 其他软件
##### ZooKeeper
安装并运行：

1. 下载并解压zookeeper源码包
2. zookeeper-path/bin//zkServer.sh start zookeeper-path/conf/zoo_sample.cfg

##### Storm 的依赖库
1. git libtool libuuid-devel gcc-c++ make 

##### ZeroMQ

    wget http://download.zeromq.org/zeromq-2.1.7.tar.gz
    tar xzf zeromq-2.1.7.tar.gz
    cd zeromq-2.1.7
    ./configure
    make
    sudo make install

###### JZMQ

    git clone https://github.com/nathanmarz/jzmq.git
    cd jzmq
    ./autogen.sh
    ./configure
    make
    sudo make install

### 安装配置使用 Storm
在一套完整的 Storm 系统中，共有四种功能角色：

1. storm nimbus: 负责任务调度和资源分配，通过 zookeeper 集群与 storm supervisor 交互来完成这项功能；
2. storm supervisor: 负责管理本机上的workers，workers执行topology中的由nimbus划分好的具体任务；
3. storm client: 与storm nimbus通信，有向nimbus提交topology，终止正在运行的topology等功能，是程序开发人员与storm交互的接口（storm命令）；
4. storm ui: 反映系统状态的dashboard，可通过“[nimbus.host(运行storm ui服务器的IP地址)]:8080”查看。

PS：下文中没有特殊说明操作，表示在所有的storm节点上都要执行。

#### 安装 Storm

    wget https://github.com/downloads/nathanmarz/storm/storm-0.7.0.zip
    unzip storm-0.7.0.zip
    cp -R storm-0.7.0 /opt
    cd /opt/storm-0.7.0
    chmod 775 ./bin/storm
    PATH=$PATH:/opt/storm-0.7.0/bin
    export PATH
    CLASSPATH=$CLASSPATH:/opt/storm-0.7.0/lib/*
    CLASSPATH=$CLASSPATH:/opt/storm-0.7.0/conf/*
    export CLASSPATH

#### 配置 Storm
编辑 /opt/storm-0.7.0/conf/storm.yaml , 加入如下内容：

    storm.zookeeper.servers:
        - "localhost" #server that runs zookeeper services
        - "192.168.3.140"
    nimbus.host: "192.168.3.140" # nimbus所在服务器的IP地址
    # nimbus.host: "localhost"

#### 运行 Storm

1. 在nimbus节点上： nohup storm nimbus &
2. 在supervisor节点上： nohup storm supervisor &
3. 在nimbus节点上： nohup storm ui &

#### 执行 Storm 应用程序
在storm client上：

    storm jar xxx.jar [class-name(which-contain-main-method)]
    storm list
    storm kill [topology-name]

#### 查看 Storm 运行状态
在浏览器中输入：[运行storm ui服务器的IP地址]:8080

## Storm 开发环境的部署

1. 安装Java
2. 下载Storm并解压
3. 将 [storm path]/bin/ 加入到环境变量 PATH 中
4. 将 [storm path]/lib/* 加入到环境变量 CLASSPATH 中
5. 更改 [storm path]/conf/storm.yaml 中的 nimbus.host:"[nimbus ip addr]"
6. 编写 Java 程序时，import 所需的与 storm 相关的 packages
7. 使用 javac 将 java 源码程序编译成为 .class
8. 使用 jar cf xxx.jar *.class 将 java 程序打包
9. 通过 storm client 的命令行将生成的 jar 文件提交到 storm cluster

## 相关资料

- [Creating a Production Storm Cluster](http://tutorials.github.io/pages/creating-a-production-storm-cluster.html)
- [Twitter Storm源代码分析之Topology的执行过程](http://xumingming.sinaapp.com/647/twitter-storm-code-analysis-topology-execution/)
- [Storm setup in Eclipse with Maven, Git and GitHub](https://github.com/mbonaci/mbo-storm/wiki/Storm-setup-in-Eclipse-with-Maven,-Git-and-GitHub)
- Storm Real-Time Processing Cookbook
- [Storm docs](http://storm.incubator.apache.org/documentation)

---
layout: hpost
category : Openstack
tagline: ""
tags : [openstack,Swift,object storage,wikipedia,production deployment,use cases]
---
{% include JB/setup %}

# Openstack Swift 在 Wikipedia 的部署和使用

主要参考资料：

- [Scaling media storage at Wikimedia with Swift](http://blog.wikimedia.org/2012/02/09/scaling-media-storage-at-wikimedia-with-swift/), [__wikitech: Media Storage__](https://wikitech.wikimedia.org/wiki/Media_storage), [wikitech: swift](https://wikitech.wikimedia.org/wiki/Swift), [wikitech: Category Swift](https://wikitech.wikimedia.org/wiki/Category:Swift), [wikitech: Ceph](https://wikitech.wikimedia.org/wiki/Ceph)

查看源代码：[Wikimeida NOC](https://noc.wikimedia.org/), [Mediawiki 文件后端存储配置（包括 shard）](https://noc.wikimedia.org/conf/highlight.php?file=filebackend.php), [Github version](https://github.com/wikimedia/operations-mediawiki-config/blob/master/wmf-config/filebackend.php)

Wikipedia 使用 swift 存储所有的多媒体数据，包括图片音频视频文档。其中 scalar 集群负责对图片，视频音频等根据需要进行 resize 或者格式转换。varnish 集群负责数据的cache。

> In terms of raw bits on disk, the largest project is clearly the Wikimedia Commons, the free media repository integrated with all of the Wikimedia projects. In addition, many projects allow their own local media uploads. As a result, across all wikis, Wikimedia stores millions of images, sounds, and other media files.

> Pasted from: http://blog.wikimedia.org/2012/02/09/scaling-media-storage-at-wikimedia-with-swift/

## Swift 在 Wikipedia 的部署情况

wikipedia 现在的swift集群共有三个 swfit eqiad cluster, swift codfw cluster, swift esams cluster. 其中 esams cluster 是备份集群，用于同步 eqiad 集群中的内容。

在 cluster 中，可以使用机器的名字区分其角色，be 代表 storage 层（back end）， fe 代表 proxy servers 集群（front end）。

> There are currently (July 2014) two swift clusters running (esamsand eqiad). esams is used to sync files (manually) from eqiad every now and then (though it is currently pending expansion due to lack of disk space) whereas eqiad is in production to serve originals and thumbnails.

> Pasted from: https://wikitech.wikimedia.org/wiki/Swift/Icehouse

- [esams](https://ganglia.wikimedia.org/latest/?r=hour&cs=&ce=&m=cpu_report&s=by+name&c=Swift%2520esams&tab=m&vn=&hide-hf=false) 集群（目前已经基本不再执行同步操作，因为硬盘空间不够了）
    + storage server ： be3001~be3004，共4台
    + proxy server ： fe3001~3002，供2台
- [codsw](https://ganglia.wikimedia.org/latest/?c=Swift%20codfw&m=cpu_report&r=hour&s=by%20name&hc=4&mc=2) 集群
    + storage server ： be2001~be2015，共15台
    + proxy server ： fe2001~fe2004，共4台
- [eqiad](https://ganglia.wikimedia.org/latest/?r=hour&cs=&ce=&m=cpu_report&s=by+name&c=Swift%2520eqiad&tab=m&vn=default&hide-hf=false) 集群
    + storage server ： be1001~1018，共18台
    + proxy server ： fe1001~fe1004，共4台
    + swift eqiad prod：1台，作用不明

各个 swift 集群的实时状态可以通过 ganglia 监控可以看到。

Wikipedia 考虑过使用 ceph 代替 swift，但是并没有成功。具体信息见：https://wikitech.wikimedia.org/wiki/Media_storage

> Because of Swift's certain limitations and in particular geographically-aware replication between datacenters which affected the eqiad migration, as well as certain Swift's shortcomings with data consistency and performance, as of 2013 Ceph with its Swift-compatible layer (radosgw) is also being evaluated for the same purpose, with pmtpa running Swift and eqiad running Ceph and a final decision between the two to be taken in late 2013.

> Pasted from: https://wikitech.wikimedia.org/wiki/Media_storage

## Swift 中数据的组织方式

Wikipedia 最初是使用文件的方式存储数据的，这样就需要建立多层的目录结构，避免一个目录中包含过多的文件（目录相当于一张表，记录了目录下每个文件，文件名到 inode 的映射关系，这个表的规模过大会导致查表操作很耗时）。在对象存储系统中，数据的地址空间是平的，即，不存在多级目录，所有的对象都被放在 containers 内，但是当一个 container 内的对象过多时依然会出现同样的问题。因此还是需要对对象进行划分。

Wikipedia 组织数据的方式：

- containers 的组成部分
    + a project
        * 例如： wikipedia（wikimedia commons 相关的数据）， global（全局性的数据）
    + a language
        * 例如： en
    + a repo
        * 例如： local（regular media files）
    + a zone
        * 例如： public（for public unscaled media，即原始 media），thumb（thumbnails/scaled media，转码或者resize的 media），transcoded（transcoded videos），temp（temporary files created by e.g. UploadStash, and deleted for unscaled media that have had their on-wiki entries deleted. ），render（Rendered content, like timeline, math, scope and captcha）
        * 这些设定被定义在php的变量 `$wgFileBackends` 里。
    + a shard(optionally)
        * 对于 large projects 需要创建多个 containers, 避免一个 container 中包含过多的 objects。large projects 的列表定义在 php 变量 `$wmfSwiftBigWikis` 里。
        * These were shared into a flat (one level) __256__ shards (00-ff), with the exception of the deleted zone that was sharded to __1296__ shards (00-zz).
        * For those that are sharded, the name of the shard matches the name of the object's second-level shard and the shard of derived contents (thumbnail) remains the same as the shard of the original that produced it.
- 具体的例子
    + (shared) 属于 Wikimedia Commonsd 的文件： `She_Has_a_Name_2012_-_Death.jpg`
        * 通过database可以将这个图片名字转换成一个URL：`http://upload.wikimedia.org/wikipedia/commons/f/f5/She_Has_a_Name_2012_-_Death.jpg`
        * 对应的 Swift object 的名字为： `f/f5/She_Has_a_Name_2012_-_Death.jpg`
        * 对应的 Swift container 的名字为： `wikipedia-commons-local-public.f5`. （ container name 中的 wikipedia， commons， local， public， f5 分别对应于 project， language， repo， zone， shared。）
        * 对应的 800px thumb 的 URL 为： `http://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/She_Has_a_Name_2012_-_Death.jpg/800px-She_Has_a_Name_2012_-_Death.jpg`
        * thumb 对应的 Swift container 为： `wikipedia-commons-local-thumb.f5`
    + (no shared) 属于 elwiki 的文件： `Plateia_syntagmatos_Athina.jpg `
        * URL : `http://upload.wikimedia.org/wikipedia/el/0/01/Plateia_syntagmatos_Athina.jpg`
        * Swift Object Name : `0/01/Plateia_syntagmatos_Athina.jpg`
        * Swift container Name : `wikipedia-el-local-public`
        * thumb container name : `wikipedia-el-local-thumb`

~~~php
$wmfSwiftBigWikis = array( # DO NOT change without proper migration first
    'commonswiki', 'dewiki', 'enwiki', 'fiwiki', 'frwiki', 'hewiki', 'huwiki', 'idwiki',
    'itwiki', 'jawiki', 'rowiki', 'ruwiki', 'thwiki', 'trwiki', 'ukwiki', 'zhwiki'
);
~~~

> Historically, files were put under directories on a filesystem and directories were sharded per wiki in a two-level hierarchy of 16 shards per level, totaling 256 uniformly sharded directories. On the Swift era, the hope was that such a sharding scheme would be unneeded, as the backend storage would handle such a complexity. This hope ultimately proved to be untrue and for certain wikis, the amount of objects per container is large enough that it created scalability problems on Swift. To address this issue, multiple containers were created for those large projects. These were shared into a flat (one level) 256 shards (00-ff), with the exception of the deleted zone that was sharded to 1296 shards (00-zz). The list of large projects that has sharded containers is currently defined in three places: a) MediaWiki's $wmfSwiftBigWikis, b) Swift's shard_container_list (proxy-server.conf, via puppet) and c) under the rewrite Varnish's rewrite configuration in puppet.

> Pasted from: https://wikitech.wikimedia.org/wiki/Media_storage

## thumbnail image 请求的处理流程（TODO 将该过程画成图）

First request for a thumbnail image

- Request for http://upload.wikimedia.org/project/language/thumb/x/xy/filename.ext/NNNpx-filename.ext is received by an LVS server.
- The LVS server picks an arbitrary Varnish frontend server to handle the request.
- Frontend Varnish looks for cached content for URL in in-memory cache.
- Frontend Varnish computes hash of URL and uses that hash to select a consistent backend Varnish server.
- The consistent hash routing ensures that all frontend Varnish servers will select the same backend Varnish server for a given URL to eliminate duplication in the backend cache layer.
- Frontend Varnish requests URL from backend Varnish.
- Backend Varnish looks for cached content for URL in SSD based cache.
- Backend Varnish requests URL from media storage cluster.
- Request for URL from media storage cluster received by an LVS server.
- The LVS server picks an arbitrary frontend Swift server to handle the request.
- The frontend Swift server rewrites the URL to map from the wiki URL space into the storage URL space.
- The frontend Swift server request new URL from Swift cluster.
- The 404 response for the URL is caught in the frontend Swift server.
- The frontend Swift server constructs a URL to request the thumbnail from an image scaler server via /w/thumb_handler.php.
- The image scaler server requests the original image from Swift.
- This goes back to the same LVS -> Swift frontend -> Swift backend path as the thumb request came down from the Varnish backend server.
- The image scaler transforms the original into the request thumbnail image.
- The image scaler stores the resulting thumbnail in Swift.
- The image scaler returns the thumbnail as a http response to the frontend Swift server's request.
- The frontend Swift server returns the thumbnail image as a http response to the backend Varnish server.
- The backend Varnish server stores the response in it's SSD-backed cache.
- The backend Varnish server returns the thumbnail image as a http response to the frontend Varnish server.
- The frontend Varnish server stores the response in it's in-memory cache.
- The frontend Varnish server returns the thumbnail image as a http response to the original requestor.
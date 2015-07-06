# this program generate a post for jekyll automatically
# just fill the name varibable with the post title which should be the source file name
import time

name = "Evaluate Openstack Swift Data Distributing Approach"

# 0 for adding nothing
# 1 for adding "note@" before name
# 2 for adding "conclution" before name
name_switch = 0

if name_switch == 0:
    source_file = name + ".md"
elif name_switch == 1:
    source_file = "NOTE@ " + name + ".md"
else:
    source_file = "CONCLUSION@ " + name + ".md"

content = '''---
layout: hpost
category : memory
tagline: ""
tags : [iteration , big-data]
---
{% include JB/setup %}
'''

def gen_post(name, post_content, post_content_part2, t = time.localtime()):
    post_name = time.strftime("%Y-%m-%d",t)+"-"+name
    f = open(post_name,"w")
    f.write(post_content)
    f.close()
    f = open(post_name,"a")
    f.write(post_content_part2)
    f.close()

def parse_name(origin_name):
    name_list = origin_name.split()
    return '-'.join(name_list)

def get_post_content_part2(source_file):
    f = open("D:\\Dropbox\\configurations\\_emacs_laven\\laven_blog\\source\\notes\\"+source_file,"r")
    post_content_part2 = f.read()
    f.close()
    return post_content_part2

gen_post(parse_name(source_file),content,get_post_content_part2(source_file))

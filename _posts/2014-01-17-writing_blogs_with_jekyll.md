---
layout: post
category : research
tagline: ""
tags : [method]
---
{% include JB/setup %}
When I play with jekyll and github pages, I have encountered some errors which are annoying and cost me a lot of time. The records of those errors are listed below. 
## ERROR LIST
### SPECIAL CHARACTERS

    special characters: < , & , *

    < and & is special characters, the only way make them appear in normal area is to put spaces on the both side of them.
    for example, some thing like below will cause markdown errors.
    x<y
    x&y
    the correct way to write this two is:
    x < y
    x & y

    * can also cause markdown errors. the expression below will cause error.
    N*T
    so, i turn it into 'NT' to avoid this error.


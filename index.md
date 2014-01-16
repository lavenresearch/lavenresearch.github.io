---
layout: page
title: Hello Worlds!
tagline: research notes
---
{% include JB/setup %}

## NOTEs LIST

ANYTHING about researching!!

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>

## To-Do

Things that I plan to do recently.



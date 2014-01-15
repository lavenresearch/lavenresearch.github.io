---
layout: page
title: Hello World!
tagline: research notes
---
{% include JB/setup %}

## NOTEs LIST

Only research notes for now. Maybe I will add some essaies someday.

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>

## To-Do

Things that I plan to do recently.



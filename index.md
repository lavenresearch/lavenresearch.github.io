---
layout: hpage
title: Home
tagline: Laven Research
---
{% include JB/setup %}

## NOTEs

ANYTHING about researching!!

<ul class="posts">
  {% for post in site.posts %}
<!--     <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li> -->
  &raquo;&raquo;&raquo;&raquo;<span class="post-date">{{ post.date | date_to_string }}</span>

  <div class="post">
    <h4 class="post-title">
      <a href="{{ BASE_PATH }}{{ post.url }}">
        {{ post.title }}
      </a>
    </h4>

  </div>
  {% endfor %}
</ul>
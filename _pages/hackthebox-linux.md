---
title: "HackTheBox — Linux"
layout: collection
permalink: /hackthebox/linux/
collection: hackthebox-linux
entries_layout: list              # grid(카드형) 또는 list
show_excerpts: true               # 요약 보이게 (true가 기본)
sort_by: title                    # 필요하면 date 등으로 변경
---

<div class="list-archive">
  {% assign docs = site.collections['hackthebox-linux'].docs | sort: 'title' %}
  {% for doc in docs %}
    {% assign thumb = doc.header.teaser | default: doc.header.image | default: doc.image %}
    <article class="list-item">
      <a href="{{ doc.url | relative_url }}" class="list-link">
        {% if thumb %}
          <div class="list-thumb">
            <img src="{{ thumb | relative_url }}" alt="{{ doc.title }}">
          </div>
        {% else %}
          <div class="list-thumb placeholder">No image</div>
        {% endif %}

        <div class="list-meta">
          <h3 class="list-title">{{ doc.title }}</h3>
          <div class="list-excerpt">
            {{ doc.excerpt | default: doc.content | strip_html | truncate: 240 }}
          </div>
        </div>
      </a>
    </article>
  {% endfor %}
</div>
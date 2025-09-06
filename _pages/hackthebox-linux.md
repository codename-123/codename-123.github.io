---
title: "HackTheBox — Linux"
layout: collection
permalink: /hackthebox/linux/
collection: hackthebox-linux
entries_layout: list              # grid(카드형) 또는 list
show_excerpts: false               # 요약 보이게 (true가 기본)                   
---

<div class="list-archive">
  {% assign docs = site.hackthebox-linux | sort: 'title' %}
  {% assign seen = "" %}
  {% for doc in docs %}
    {% assign url = doc.url | append: "" %}
    {% if seen contains url %}
      {% continue %}
    {% endif %}
    {% assign seen = seen | append: url | append: "|" %}

    {% assign thumb = doc.header.teaser | default: doc.header.image | default: doc.image %}
    {% comment %}
      아래에서 thumb가 없으면 아예 항목을 출력하지 않음 (썸네일 있는 것만)
    {% endcomment %}
    {% if thumb %}
      <article class="list-item">
        <a href="{{ doc.url | relative_url }}" class="list-link">
          <div class="list-thumb" aria-hidden="true">
            <img src="{{ thumb | relative_url }}" alt="{{ doc.title }}">
          </div>

          <div class="list-meta">
            <h3 class="list-title"><a href="{{ doc.url | relative_url }}">{{ doc.title }}</a></h3>
            <div class="list-excerpt">
              {{ doc.excerpt | default: doc.content | strip_html | truncate: 200 }}
            </div>
          </div>
        </a>
      </article>
    {% endif %}
  {% endfor %}
</div>

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
    {% comment %}
      건너뛰기 조건:
        - 이미 보였던 URL (seen)
        - doc.path가 존재하고 page.path와 동일하면 (같은 파일)
        - doc.url가 page.url과 동일하면 (같은 URL)
        - doc.path에 'index.' 포함 시 (컬렉션 내부 index 파일)
        - 썸네일(thumb)이 없는 문서는 표시 안 함
    {% endcomment %}

    {% assign url = doc.url | append: "" %}
    {% if seen contains url %}
      {% continue %}
    {% endif %}

    {% if doc.path and page.path and doc.path == page.path %}
      {% continue %}
    {% endif %}

    {% if doc.url == page.url %}
      {% continue %}
    {% endif %}

    {% if doc.path and doc.path contains "index." %}
      {% continue %}
    {% endif %}

    {% assign seen = seen | append: url | append: "|" %}

    {% assign thumb = doc.header.teaser | default: doc.header.image | default: doc.image %}
    {% if thumb %}
      <article class="list-item">
        <a href="{{ doc.url | relative_url }}" class="list-link">
          <div class="list-thumb" aria-hidden="true">
            <img src="{{ thumb | relative_url }}" alt="{{ doc.title }}">
          </div>

          <div class="list-meta">
            <h3 class="list-title"><a href="{{ doc.url | relative_url }}">{{ doc.title }}</a></h3>
            <div class="list-excerpt">
              {{ doc.excerpt | default: doc.content | strip_html | truncate: 180 }}
            </div>
          </div>
        </a>
      </article>
    {% endif %}
  {% endfor %}
</div>

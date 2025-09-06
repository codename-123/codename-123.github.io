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
    {% comment %}
      1) 같은 URL이면 건너뜀
      2) 현재 페이지(url 같음)면 건너뜀
      3) doc.path에 'index.' 포함되어 있으면(컬렉션 내부 index 파일 등) 건너뜀
      4) thumb(썸네일)가 없으면 출력 안 함
    {% endcomment %}
    {% if seen contains url %}
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

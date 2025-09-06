---
title: "HackTheBox — Linux"
layout: collection
permalink: /hackthebox/linux/
collection: hackthebox-linux
entries_layout: grid
classes: wide
---

<div class="cards-grid">
  {% assign docs = site.collections['hackthebox-linux'].docs | sort: 'title' %}
  {% for doc in docs %}
    <article class="card">
      <a class="card-link" href="{{ doc.url | relative_url }}">
        {% if doc.image %}
          <div class="card-thumb" style="background-image: url('{{ doc.image | relative_url }}')"></div>
        {% else %}
          <div class="card-thumb card-thumb--placeholder">No image</div>
        {% endif %}

        <h3 class="card-title">{{ doc.title }}</h3>

        <div class="card-excerpt">
          {{ doc.excerpt | default: doc.content | strip_html | truncate: 180 }}
        </div>
      </a>
    </article>
  {% endfor %}
</div>
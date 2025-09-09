---
layout: archive
permalink: /categories/
author_profile: true
---

<style>
.btn-badge {
  display:inline-block;
  margin-left:0.6rem;
  padding:0.12rem 0.5rem;
  border-radius:999px;
  font-weight:700;
  font-size:0.9rem;
  background: rgba(255,255,255,0.12);
  color: inherit;
}
</style>

<div class="categories-page">
  <ul class="category-list">
    {% for item in site.data.navigation.categories_nav %}
      <li class="category-item">
        <a class="btn btn--primary" href="{{ item.url | relative_url }}">
          {{ item.title }}
          {% if item.count %}<span class="btn-badge">{{ item.count }}</span>{% endif %}
        </a>
      </li>
    {% endfor %}
  </ul>
</div>

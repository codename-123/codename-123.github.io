---
layout: archive
permalink: /categories/
author_profile: true
---

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

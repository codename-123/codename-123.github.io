---
layout: archive
title: "Categories"
permalink: /categories/
author_profile: true
sidebar:
  nav: categories_nav
---


<style>
/* scoped styles for this page only */
.categories-page { padding: 0 0.5rem 2rem; }

.categories-page h1 {
  font-size: 1.8rem;
  margin: 0 0 1rem 0;
}

/* 3-column grid for desktop, responsive down to 1 column */
.category-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  border-top: 1px solid rgba(0,0,0,0.06);
}

/* each row = one category item */
.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  font-weight: 700;
}

/* visual tweak for links */
.category-item a { text-decoration: none; color: inherit; }

/* count on the right */
.cat-count {
  min-width: 2ch;
  text-align: right;
  opacity: 0.85;
  font-weight: 600;
}

/* responsive */
@media (max-width: 900px) {
  .category-list { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .category-list { grid-template-columns: repeat(1, 1fr); }
}
</style>

<div class="categories-page">
  <h1>Posts by Category</h1>

  <ul class="category-list">
    {% comment %}
      Use site.data.navigation.categories_nav for order/selection.
      For count: try exact match, downcased match, or slugified match between
      navigation title and site.categories keys.
    {% endcomment %}

    {% for item in site.data.navigation.categories_nav %}
      {% assign cnt = 0 %}

      {% for pair in site.categories %}
        {% assign cat_key = pair[0] %}
        {% if cat_key == item.title or cat_key == item.title | downcase or cat_key | slugify == item.title | slugify %}
          {% assign cnt = pair[1] | size %}
          {% break %}
        {% endif %}
      {% endfor %}

      <li class="category-item">
        <a href="{{ item.url | relative_url }}">{{ item.title }}</a>
        <span class="cat-count">{{ cnt }}</span>
      </li>
    {% endfor %}
  </ul>
</div>
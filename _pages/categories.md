---
layout: archive
title: "Categories"
permalink: /categories/
author_profile: true
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
  border-top: 1px solid rgba(255,255,255,0.03);
}

/* each row = one category item */
.category-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  font-weight: 700;
}

/* make the whole left area clickable like a link (text styles) */
.category-item a {
  text-decoration: none;
  color: inherit;
  display: block;
  width: 100%;
}

/* add subtle hover */
.category-item a:hover {
  text-decoration: underline;
  opacity: 0.95;
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
      site.data.navigation.categories_nav 를 순서대로 사용.
      숫자는 표시하지 않고, 링크만 출력합니다.
    {% endcomment %}

    {% for item in site.data.navigation.categories_nav %}
      <li class="category-item">
        <a href="{{ item.url | relative_url }}">{{ item.title }}</a>
      </li>
    {% endfor %}
  </ul>
</div>
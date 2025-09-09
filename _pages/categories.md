---
layout: archive
permalink: /categories/
author_profile: true
---

<style>
/* scoped styles for a clearly clickable list with checkmark on hover */
.categories-page { padding: 0 0.5rem 2rem; }

.categories-page h1 {
  font-size: 1.8rem;
  margin: 0 0 1rem 0;
}

/* 3-column grid */
.category-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
}

/* each item has a full-width clickable link */
.category-item {
  border-bottom: 1px solid rgba(255,255,255,0.03);
}

/* make anchor fill the item and look like a real clickable control */
.category-item a {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 1rem 1.1rem;
  text-decoration: none;
  color: inherit;
  font-weight: 800;
  cursor: pointer;
  transition: background-color .15s ease, transform .12s ease, color .12s ease;
  border-radius: 6px;
}

/* subtle hover background + slight move for 'pressable' feel */
.category-item a:hover,
.category-item a:focus {
  background-color: rgba(255,255,255,0.02);
  transform: translateX(2px);
  text-decoration: none;
  outline: none;
}

/* checkmark that appears on hover to hint 'go' */
/* using heavy check mark glyph; hidden by default, fades & scales in on hover */
.category-item a::after {
  content: '\2714'; /* ✔ */
  opacity: 0;
  transform: translateX(-6px) scale(0.85);
  transition: opacity .15s ease, transform .15s ease;
  margin-left: 12px;
  font-size: 1.05em;
  color: #6fc3a2; /* accent green */
  display: inline-block;
  line-height: 1;
}

/* show check on hover/focus */
.category-item a:hover::after,
.category-item a:focus::after {
  opacity: 1;
  transform: translateX(0) scale(1);
}

/* optional: make the check inside a subtle round background on hover */
.category-item a:hover::after,
.category-item a:focus::after {
  padding: 3px 6px;
  border-radius: 999px;
  background: rgba(111,195,162,0.08);
}

/* optional accent color on hover (text) */
.category-item a:hover,
.category-item a:focus {
  color: #6fc3a2;
}

/* responsive: 2 cols / 1 col */
@media (max-width: 900px) {
  .category-list { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .category-list { grid-template-columns: repeat(1, 1fr); }
}
</style>

<div class="categories-page">
  <ul class="category-list">
    {% for item in site.data.navigation.categories_nav %}
      <li class="category-item">
        <a href="{{ item.url | relative_url }}">{{ item.title }}</a>
      </li>
    {% endfor %}
  </ul>
</div>

## 1
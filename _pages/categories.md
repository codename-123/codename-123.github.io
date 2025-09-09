---
layout: archive
permalink: /categories/
author_profile: true
---

<style>
/* scoped styles for a clearly clickable list with checkmark on hover */
.categories-page {
  padding: 0 0.5rem 2rem;
}

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
  padding: 0.85rem 1.1rem;
  text-decoration: none;
  color: #eee;  /* 조금 더 밝게 */
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  cursor: pointer;
  transition: 
    color 0.15s ease, 
    background-color 0.15s ease, 
    transform 0.12s ease, 
    border-bottom-color 0.15s ease;
  border-radius: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.1); /* 기본 얇은 밑줄 */
  background-color: rgba(255,255,255,0.01); /* 살짝 배경 추가 */
}

/* hover / focus effects */
.category-item a:hover,
.category-item a:focus {
  color: #6fc3a2;                 /* 강조 색상 */
  border-bottom-color: #6fc3a2;   /* 밑줄 강조 */
  background-color: rgba(111,195,162,0.08);
  transform: translateX(2px);
}

/* checkmark that appears on hover to hint 'go' */
.category-item a::after {
  content: '\2714'; /* ✔ */
  opacity: 0;
  transform: translateX(-6px) scale(0.85);
  transition: opacity 0.15s ease, transform 0.15s ease;
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
  padding: 3px 6px;
  border-radius: 999px;
  background: rgba(111,195,162,0.08);
}

/* responsive: 2 cols / 1 col */
@media (max-width: 900px) {
  .category-list { 
    grid-template-columns: repeat(2, 1fr); 
  }
}
@media (max-width: 600px) {
  .category-list { 
    grid-template-columns: repeat(1, 1fr); 
  }
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

---
layout: archive
permalink: /categories/
author_profile: true
---

<style>
/* 고유 네임스페이스: 충돌을 최소화하려고 .js-cat-wrap 사용 */
.js-cat-wrap { padding: 0 0.75rem 2rem; }

/* 카드 박스 (중앙) */
.js-cat-wrap .js-cat-box {
  background: #fff;
  color: #222;
  border-radius: 8px;
  padding: 1.1rem;
  box-shadow: 0 8px 20px rgba(0,0,0,0.35);
  border: 1px solid rgba(0,0,0,0.06);
  margin-bottom: 2rem;
  position: relative;
}

/* 제목 */
.js-cat-wrap .js-cat-box h1 { margin: 0 0 0.6rem 0; font-size:1.6rem; }

/* 그리드 강제 적용 (테마 규칙 덮어쓰기 위해 !important 사용) */
.js-cat-wrap .js-category-list {
  display: grid !important;
  grid-template-columns: repeat(3, 1fr) !important;
  gap: 0 !important;
  list-style: none !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* 항목 블록화 */
.js-cat-wrap .js-category-item {
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

/* 링크를 flex로 만들어 제목-숫자 정렬 */
.js-cat-wrap .js-category-item a {
  display: flex !important;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0.75rem 1rem;
  text-decoration: none !important;
  color: #222 !important;
  font-weight: 700;
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, Arial;
  font-size: 0.95rem;
  transition: background .12s ease, transform .08s ease, color .12s ease;
  background: transparent !important;
}

/* hover */
.js-cat-wrap .js-category-item a:hover,
.js-cat-wrap .js-category-item a:focus {
  background: rgba(111,195,162,0.06) !important;
  color: #0b6b49 !important;
  transform: translateX(2px) !important;
}

/* count 스타일 */
.js-cat-wrap .js-category-item .js-count {
  color: #7a7a7a;
  font-weight: 600;
  margin-left: 1rem;
  white-space: nowrap;
}

/* 데스크톱에서 열 구분선 (세로선) */
.js-cat-wrap .js-cat-box::before,
.js-cat-wrap .js-cat-box::after {
  content: "";
  position: absolute;
  top: 0.6rem;
  bottom: 0.6rem;
  width: 1px;
  background: rgba(0,0,0,0.06);
  display: block;
  pointer-events: none;
}
.js-cat-wrap .js-cat-box::before { left: calc(33.333% - 0.5px); }
.js-cat-wrap .js-cat-box::after  { left: calc(66.666% - 0.5px); }

/* 반응형 */
@media (max-width: 900px) {
  .js-cat-wrap .js-category-list { grid-template-columns: repeat(2, 1fr) !important; }
  .js-cat-wrap .js-cat-box::before,
  .js-cat-wrap .js-cat-box::after { display:none; }
}
@media (max-width: 600px) {
  .js-cat-wrap .js-category-list { grid-template-columns: repeat(1, 1fr) !important; }
}
</style>

<div class="js-cat-wrap">
  <div class="js-cat-box">
    <h1>Posts by Category</h1>

    {%- comment -%}
      자동으로 _pages에서 categories 값을 모아 유니크 목록을 만든다.
      모든 페이지에 front matter: categories: ["Name"] 형태가 있어야 함.
    {%- endcomment -%}

    {% assign cat_acc = "" %}
    {% for p in site.pages %}
      {% if p.categories %}
        {% for c in p.categories %}
          {% assign check = "||" | append: c | append: "||" %}
          {% unless cat_acc contains check %}
            {% assign cat_acc = cat_acc | append: check %}
          {% endunless %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    {% assign cat_arr = cat_acc | split: "||" %}
    {% assign cats = "" | split: "|" %}
    {% for item in cat_arr %}
      {% if item != "" %}
        {% assign cats = cats | push: item %}
      {% endif %}
    {% endfor %}

    <ul class="js-category-list">
      {% for cat_title in cats %}
        {% assign matching_pages = site.pages | where_exp: "pp", "pp.categories and pp.categories contains cat_title" %}
        <li class="js-category-item">
          <a href="{{ '/categories/' | append: cat_title | slugify | append: '/' | relative_url }}">
            <span class="js-title">{{ cat_title }}</span>
            <span class="js-count">{{ matching_pages | size }}</span>
          </a>
        </li>
      {% endfor %}
    </ul>
  </div>
</div>

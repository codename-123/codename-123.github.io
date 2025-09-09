---
layout: archive
permalink: /categories/
author_profile: true
---

<style>
/* 전체 페이지 여백 조정 (필요하면 조절) */
.categories-page {
  padding: 0 0.75rem 2rem;
}

/* 박스(첫번째 사진처럼 중앙의 카드) */
.categories-box {
  position: relative;
  background: #ffffff;
  color: #222;
  border-radius: 8px;
  padding: 1.1rem;
  box-shadow: 0 8px 18px rgba(0,0,0,0.35);
  border: 1px solid rgba(0,0,0,0.06);
  margin-bottom: 2rem;
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

/* 각 항목 */
.category-item {
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

/* 링크가 항목 전체를 채움 */
.category-item a {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 0.75rem 1rem;
  text-decoration: none;
  color: #222;
  font-weight: 700;
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  font-size: 0.95rem;
  transition: background .12s ease, transform .08s ease, color .12s ease;
  background: transparent;
}

/* hover */
.category-item a:hover,
.category-item a:focus {
  background: rgba(111,195,162,0.06);
  color: #0b6b49;
  transform: translateX(2px);
}

/* count 오른쪽 정렬 */
.category-item .count {
  color: #7a7a7a;
  font-weight: 600;
  margin-left: 1rem;
  white-space: nowrap;
}

/* 데스크톱에서 열 구분선: 박스 가로 기준으로 33% 와 66% 위치에 세로선 */
.categories-box::before,
.categories-box::after {
  content: "";
  position: absolute;
  top: 0.6rem;
  bottom: 0.6rem;
  width: 1px;
  background: rgba(0,0,0,0.06);
  display: block;
  pointer-events: none;
}
.categories-box::before { left: calc(33.333% - 0.5px); }
.categories-box::after  { left: calc(66.666% - 0.5px); }

/* 모바일/태블릿에서는 2/1열로 변경 및 세로선 제거 */
@media (max-width: 900px) {
  .category-list { grid-template-columns: repeat(2, 1fr); }
  .categories-box::before,
  .categories-box::after { display: none; }
}
@media (max-width: 600px) {
  .category-list { grid-template-columns: repeat(1, 1fr); }
}
</style>

<div class="categories-page">
  <div class="categories-box">
    <h1 style="margin:0 0 0.6rem 0; font-size:1.6rem;">Posts by Category</h1>
    <ul class="category-list">
      {%- assign sorted = site.categories | sort_natural: "first" -%}
      {%- for cat in sorted -%}
        {%- assign name = cat[0] -%}
        {%- assign posts = cat[1] -%}
        <li class="category-item">
          <a href="{{ '/categories/' | append: name | slugify | append: '/' | relative_url }}">
            <span class="cat-title">{{ name }}</span>
            <span class="count">{{ posts | size }}</span>
          </a>
        </li>
      {%- endfor -%}
    </ul>
  </div>
</div>

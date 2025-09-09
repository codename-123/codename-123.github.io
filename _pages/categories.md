---
layout: page
permalink: /categories/
author_profile: true
---

<style>
/* 네임스페이스로 충돌 최소화 */
.mm-cat-wrap { padding: 0 0.75rem 2rem; }
.mm-cat-box {
  background: #fff; color:#222; border-radius:8px; padding:1.1rem;
  box-shadow:0 10px 24px rgba(0,0,0,0.35); border:1px solid rgba(0,0,0,0.06);
  position:relative; margin-bottom:2rem;
}
.mm-cat-box h1{ margin:0 0 0.6rem 0; font-size:1.6rem; }

/* grid */
.mm-cat-list{
  display:grid !important;
  grid-template-columns: repeat(3,1fr) !important;
  gap:0 !important; list-style:none !important; margin:0; padding:0;
}
.mm-cat-item{ border-bottom:1px solid rgba(0,0,0,0.06); }
.mm-cat-item a{
  display:flex !important; justify-content:space-between; align-items:center;
  padding:0.75rem 1rem; text-decoration:none !important; color:#222 !important;
  font-weight:700;
}
.mm-cat-item a:hover{ background: rgba(111,195,162,0.06) !important; color:#0b6b49 !important; transform:translateX(2px); }
.mm-count{ color:#777; font-weight:600; margin-left:1rem; }

/* vertical dividers */
.mm-cat-box::before, .mm-cat-box::after{
  content:""; position:absolute; top:0.6rem; bottom:0.6rem; width:1px; background:rgba(0,0,0,0.06);
  pointer-events:none;
}
.mm-cat-box::before{ left: calc(33.333% - 0.5px); }
.mm-cat-box::after{ left: calc(66.666% - 0.5px); }

@media (max-width:900px){
  .mm-cat-list{ grid-template-columns: repeat(2,1fr) !important; }
  .mm-cat-box::before, .mm-cat-box::after{ display:none; }
}
@media (max-width:600px){
  .mm-cat-list{ grid-template-columns: repeat(1,1fr) !important; }
}
</style>

<div class="mm-cat-wrap">
  <div class="mm-cat-box">
    <h1>Posts by Category</h1>

    <ul class="mm-cat-list">
      {% comment %} site.data.categories에 있는 항목들을 순회함 {% endcomment %}
      {% for cat in site.data.categories %}
        {% assign title = cat.title %}
        {% assign slug = cat.slug %}
        {% assign coll_name = cat.collection %}

        {%- comment -%}
          pages에서 categories 필드에 title이 포함된 것만 찾기
          조건식을 문자열로 만들어서 where_exp에 넘긴다.
        {%- endcomment -%}
        {% assign expr_pages = "p.categories and p.categories contains '" | append: title | append: "'" %}
        {% assign pages_match = site.pages | where_exp: "p", expr_pages %}
        {% assign pages_count = pages_match | size %}

        {%- comment -%}
          컬렉션이 지정되어 있으면 그 컬렉션의 docs들 중
          front matter categories에 title을 포함한 문서만 센다.
        {%- endcomment -%}
        {% assign coll_count = 0 %}
        {% if coll_name and site.collections[coll_name] %}
          {% assign expr_coll = "d.categories and d.categories contains '" | append: title | append: "'" %}
          {% assign coll_match = site.collections[coll_name].docs | where_exp: "d", expr_coll %}
          {% assign coll_count = coll_match | size %}
        {% endif %}

        {% assign total = pages_count | plus: coll_count %}

        <li class="mm-cat-item">
          <a href="{{ '/categories/' | append: slug | append: '/' | relative_url }}">
            <span>{{ title }}</span>
            <span class="mm-count">{{ total }}</span>
          </a>
        </li>
      {% endfor %}
    </ul>
  </div>
</div>

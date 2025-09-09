---
layout: archive
permalink: /categories/
author_profile: true
---

<style>
/* 가로 나열용 (충돌 방지 네임스페이스) */
.categories-page .category-list {
  display: flex !important;
  flex-wrap: wrap !important;        /* 화면 작아지면 다음 줄로 랩 */
  gap: 0.6rem 1rem !important;       /* 행간 0.6rem, 열간 1rem */
  align-items: center !important;
  margin: 0 !important;
  padding: 0 !important;
  list-style: none !important;       /* 불릿 제거 */
}

/* 각 아이템을 인라인처럼 동작하게 (버튼과 간격) */
.categories-page .category-item {
  display: inline-block !important;
  margin: 0 !important;
  padding: 0 !important;
  vertical-align: middle;
}

/* 버튼(테마 .btn)과 조합했을 때 간격/높이 정리 */
.categories-page .category-item .btn {
  display: inline-flex;              /* 내용(텍스트+badge) 가운데 맞춤 */
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.9rem;           /* 버튼 크기 조정 (원하면 값 변경) */
  white-space: nowrap;               /* 버튼 내 텍스트 줄바꿈 방지 */
}

/* 숫자 배지가 있다면 보기 좋게 */
.categories-page .btn-badge {
  display:inline-block;
  padding:0.12rem 0.48rem;
  border-radius:999px;
  font-weight:700;
  font-size:0.85rem;
  background: rgba(255,255,255,0.12);
  color: inherit;
}

/* 작은 화면에서는 버튼을 가득 너비로 (선택 사항) */
@media (max-width: 520px) {
  .categories-page .category-list {
    justify-content: flex-start;
  }
  .categories-page .category-item {
    width: 100% !important;
  }
  .categories-page .category-item .btn {
    width: 100%;
    justify-content: space-between;
  }
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

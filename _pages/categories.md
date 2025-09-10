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

.category-section h2 {
  font-size: 1rem;
  margin-top: 2rem;
}
.category-section p {
  font-size: 0.7rem;
  line-height: 1.6;
}
.category-section ul {
  font-size: 0.6rem;
  line-height: 1.5;
}
</style>

<h2>Category</h2>

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

---

<div class="category-section">
  <p>
    이 페이지는 블로그의 주요 주제별 모음입니다.  
    각 카테고리는 관련 글들을 모아둔 인덱스이며, 관심 있는 주제를 빠르게 찾아볼 수 있도록 정리되어 있습니다.  
    원하시는 카테고리 버튼을 클릭하면 해당 주제의 글 목록으로 이동합니다.
  </p>
  <h2>HackTheBox</h2>
  <p>
    해킹 실습 플랫폼(Hack The Box)에서 풀었던 머신·문제들의 풀이 기록을 모아둔 곳입니다.<br>
    각 글은 초기 정찰부터 권한 상승(root/Administrator 획득), 취약점 분석, 재현 코드와 해결에 쓰인 팁까지 단계별로 정리합니다.
  </p>
  <ul>
    <li>실전형 풀이 (공격 벡터, 익스플로잇 체인)</li>
    <li>포스트-익스플로잇 정리 및 교훈</li>
    <li>자주 쓰는 도구와 스크립트</li>
  </ul>

  <h2>WEB</h2>
  <p>
    웹 애플리케이션 보안과 웹 개발 관련 글들을 모아둔 카테고리입니다.<br>
    취약점 분석(SQLi, XSS, RCE 등), 취약점 재현, 보안 검토 체크리스트와 안전한 코딩 팁까지 포함합니다.
  </p>
  <ul>
    <li>취약점 원리 및 재현 예제</li>
    <li>취약점 탐지 (도구·테크닉) 및 방어 방법</li>
    <li>웹 개발 관련 실용 가이드</li>
  </ul>

  <h2>Red Team</h2>
  <p>
    공격자 관점의 시나리오(레드팀) 작성, 침투 테스트 방법론, 도구 사용법과 실무 팁을 다룹니다.<br>
    실제 모의공격 준비, 탐지 우회 기법, 보고서 작성법 등 실무에서 바로 사용할 수 있는 내용을 위주로 합니다.
  </p>
  <ul>
    <li>침투 시나리오 설계 및 실행 단계</li>
    <li>EDR/AV 우회, 지속성 유지, 권한 상승 전략</li>
    <li>실전 보고서 템플릿과 정리 팁</li>
  </ul>
</div>
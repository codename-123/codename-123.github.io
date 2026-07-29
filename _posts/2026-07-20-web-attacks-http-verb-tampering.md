---
title: "Web Attacks - HTTP Verb Tampering"
date: 2026-07-20
layout: single
excerpt: "HTTP 메서드 변경을 통해 Basic Authentication과 보안 필터를 우회하고 Command Injection으로 이어지는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "Web Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, web-attacks, command-injection]
---

HTTP 메서드 변경을 통해 Basic Authentication과 보안 필터를 우회하고 Command Injection으로 이어지는 과정을 정리한다.

# Intro to HTTP Verb Tampering

HTTP 요청에는 서버가 수행할 동작을 나타내는 HTTP 메서드가 사용된다.

웹 애플리케이션에서는 주로 `GET` 과 `POST` 메서드를 사용하지만, HTTP에는 이외에도 `PUT`, `DELETE`, `HEAD`, `OPTIONS`, `PATCH` 등의 메서드가 존재한다.

문제는 웹 서버나 애플리케이션이 인증, 권한 검사 또는 보안 필터를 일부 HTTP 메서드에만 적용했을 때 발생한다.

예를 들어 시스템 관리자가 특정 웹 페이지에 인증을 요구하기 위해 다음과 같은 설정을 사용했다고 가정해보자:

```xml
<Limit GET POST>
    Require valid-user
</Limit>
```

이 설정은 `GET` 과 `POST` 요청에 대해서만 유효한 사용자 인증을 요구한다.

따라서 웹 애플리케이션이 `HEAD`, `DELETE` 와 같은 다른 HTTP 메서드도 처리하고 있다면, 공격자는 인증이 적용되지 않은 메서드를 사용하여 인증 메커니즘을 우회할 가능성이 있다.

결과적으로 인증 우회가 발생할 수 있으며, 공격자는 원래 접근할 수 없어야 하는 페이지나 기능을 실행할 수 있게 된다.

웹 서버 설정뿐만 아니라 안전하지 않은 코딩 방식으로도 HTTP Verb Tampering 취약점이 발생할 수 있다:

```php
$pattern = "/^[A-Za-z\s]+$/";

if(preg_match($pattern, $_GET["code"])) {
    $query = "Select * from ports where port_code like '%" . $_REQUEST["code"] . "%'";
    ...SNIP...
}
```

위 코드는 정규 표현식을 이용한 화이트리스트 방식으로 `code` 파라미터에 영문자와 공백만 포함되어 있는지 검사한다.

하지만 중요한 점은 검증할 때는 `$_GET["code"]` 를 사용하면서, 실제 SQL 쿼리를 생성할 때는 `$_REQUEST["code"]` 를 사용한다는 것이다.

`$_REQUEST` 는 서버 설정에 따라 `GET`, `POST`, `COOKIE` 등의 입력값을 포함할 수 있다. 

따라서 공격자는 `GET` 에는 필터를 통과하는 정상적인 값을 전달하고, `POST` 에는 실제로 사용될 악의적인 값을 전달하는 방식으로 검증값과 실행값을 다르게 만들 수 있다.

이처럼 입력값을 검증하는 위치와 실제로 사용하는 위치가 서로 다르면 보안 필터 우회가 발생할 수 있다.

# Bypassing Basic Authentication

웹 애플리케이션에는 파일을 생성하고 관리할 수 있는 File Manager가 존재한다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks1.png)

하지만 상단의 `Reset` 버튼을 클릭하면 사용자 이름과 비밀번호를 요구하는 인증 창이 나타난다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks2.png)

## Changing the HTTP Method

Burp Suite를 이용하여 요청을 분석한 결과, `Reset` 버튼을 클릭하면 다음 경로로 요청이 전송되는 것을 확인할 수 있었다:

```text
/admin/reset.php
```

인증 정보를 입력하지 않았기 때문에 서버에서는 `401 Unauthorized` 응답이 반환되었다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks3.png)

요청을 가로챈 상태에서 기존의 `GET` 메서드를 `DELETE` 로 변경하여 서버에 전송하였다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks4.png)

`DELETE` 요청에는 인증 설정이 적용되지 않았지만, 웹 애플리케이션은 해당 요청에서도 Reset 기능을 실행하였다.

이후 File Manager의 메인 페이지로 돌아가 확인한 결과, 기존에 존재하던 `notes.txt` 파일이 삭제되었으며 플래그가 출력된 것을 확인할 수 있었다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks5.png)

# Bypassing Security Filters

HTTP Verb Tampering은 인증뿐만 아니라 웹 애플리케이션의 보안 필터를 우회하는 데에도 사용될 수 있다.

예를 들어 Injection 공격을 탐지하는 필터가 `POST` 파라미터만 검사하도록 작성되어 있다면, 요청을 `GET` 방식으로 변경하여 필터를 우회할 가능성이 있다:

```php
$_POST['parameter']
```

반대로 필터가 `GET` 파라미터만 검사하지만 애플리케이션은 `POST` 파라미터도 처리한다면, 요청을 `POST` 로 변경하여 동일한 문제가 발생할 수 있다.

## Identifying the Security Filter

실습 웹 애플리케이션은 앞에서 확인한 것과 동일한 File Manager 형태로 구성되어 있다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks1.png)

입력창에 `test.txt` 를 입력하면 해당 이름의 파일이 정상적으로 생성되는 것을 확인할 수 있다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks6.png)

요청을 확인해보면 `filename` 파라미터를 통해 생성할 파일 이름이 서버로 전달되는 구조다.

여기에 명령어 구분자로 사용될 수 있는 세미콜론(`;`)을 추가하여 다음과 같이 요청하였다:

```text
test2.txt;
```

`GET` 방식으로 해당 요청을 전송하면 서버에서 다음 메시지가 반환된다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks7.png)

이를 통해 웹 애플리케이션이 `filename` 파라미터의 특수문자를 검사하고 있으며, 세미콜론과 같은 문자가 포함된 요청을 악의적인 요청으로 판단하여 차단한다는 것을 확인할 수 있다.

Burp Suite의 `Change Request Method` 기능을 사용하여 기존 `GET` 요청을 `POST` 요청으로 변경하였다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks8.png)

요청 메서드를 `POST` 로 변경하자 이전에 나타났던 `Malicious Request Denied!` 메시지가 더 이상 출력되지 않았으며, 요청이 정상적으로 처리되었다.

웹 페이지를 다시 확인한 결과 `test2.txt` 파일이 생성된 것을 확인할 수 있었다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks9.png)

## Command Injection

세미콜론이 포함된 입력만 차단된다는 점을 통해 `filename` 값이 서버의 셸 명령어에 직접 삽입되고 있을 가능성을 의심할 수 있다.

다만 세미콜론이 차단된다는 사실만으로 Command Injection 취약점을 확정할 수는 없으므로, 실제 명령어를 삽입하여 동작 여부를 확인해야 한다.

다음과 같이 파일 이름 뒤에 `id` 명령어를 추가하였다:

```text
test3.txt; id;
```

요청을 `POST` 방식으로 전송한 결과 `test3.txt` 파일이 생성되었으며, HTTP 응답 내부에서 다음과 같은 `id` 명령어 실행 결과를 확인할 수 있었다:

![Web Attacks](/assets/cpts-web/web-attacks-http-verb-tampering/web-attacks10.png)

## Vulnerable Source Code

애플리케이션의 내부 코드는 다음과 같이 구성되어 있었다:

```php
closedir($handle);

if (isset($_REQUEST['filename'])) {
    if (!preg_match('/[^A-Za-z0-9. _-]/', $_GET['filename'])) {
        system("touch " . $_REQUEST['filename']);
        header("Refresh:0; url=index.php");
    } else {
        echo "Malicious Request Denied!";
    }
}
```

파일 이름이 전달되었는지는 `$_REQUEST['filename']` 을 이용하여 확인하고 있다.

하지만 특수문자 필터링은 `$_GET['filename']` 에만 적용되어 있다.

```php
preg_match('/[^A-Za-z0-9. _-]/', $_GET['filename'])
```

반면 실제 시스템 명령어를 실행할 때는 다시 `$_REQUEST['filename']` 을 사용한다.

```php
system("touch " . $_REQUEST['filename']);
```

따라서 `GET` 요청에서는 `filename` 값에 포함된 세미콜론이 필터에 의해 차단되지만, 요청을 `POST` 방식으로 변경하면 악의적인 값이 `$_POST` 를 통해 전달된다.

이 경우 `$_GET['filename']` 에는 검사할 값이 존재하지 않아 필터가 제대로 동작하지 않지만, `$_REQUEST['filename']` 에는 `POST` 로 전달한 값이 포함되기 때문에 해당 값이 `system()` 함수로 전달된다.

최종적으로 서버에서는 다음과 유사한 명령어가 실행된다:

```bash
touch test3.txt; id;
```

이 명령은 먼저 `test3.txt` 파일을 생성한 뒤, 이어서 `id` 명령어를 실행한다.

이를 통해 HTTP 메서드를 변경하는 것만으로 보안 필터를 우회하고 Command Injection을 수행할 수 있음을 확인하였다.
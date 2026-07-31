---
title: "Web Attacks - Skills Assessment"
date: 2026-07-31
layout: single
excerpt: "한 소프트웨어 개발 회사의 의뢰를 받아 웹 애플리케이션 침투 테스트를 수행하고 있으며, 해당 회사는 현재 개발 중인 소셜 네트워킹 웹 애플리케이션의 가장 최신 빌드에 보안상 문제가 존재하는지 확인해 달라고 요청했다. 지금까지 학습한 여러 공격 기법과 취약점 분석 방법을 종합적으로 활용하여, 애플리케이션의 다양한 기능과 입력 지점을 점검하고, 그 과정에서 발견되는 여러 취약점을 식별한 뒤 실제로 악용하여 보안상 어떤 영향이 발생할 수 있는지 확인해야 한다."
author_profile: true
toc: true
toc_label: "Web Attacks"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-web/web-attacks-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-web]
tags: [web, cpts, web-attacks, xxe, idor]
---

# Scenario

한 소프트웨어 개발 회사의 의뢰를 받아 웹 애플리케이션 침투 테스트를 수행하고 있으며, 해당 회사는 현재 개발 중인 소셜 네트워킹 웹 애플리케이션의 가장 최신 빌드에 보안상 문제가 존재하는지 확인해 달라고 요청했다. 

지금까지 학습한 여러 공격 기법과 취약점 분석 방법을 종합적으로 활용하여, 애플리케이션의 다양한 기능과 입력 지점을 점검하고, 그 과정에서 발견되는 여러 취약점을 식별한 뒤 실제로 악용하여 보안상 어떤 영향이 발생할 수 있는지 확인해야 한다.

> 로그인 정보는 다음과 같다: (`htb-student` / `Academy_student!`)

## Initial Enumeration

우선 로그인한 뒤 웹 애플리케이션의 기능을 둘러보았다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks1.png)

현재 로그인한 계정은 `Paolo Perrone` 이라는 사용자로 확인되었다.

또한 `Settings` 페이지에는 비밀번호를 변경할 수 있는 기능이 존재하였다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks2.png)

## API Discovery

Burp Suite를 실행한 상태에서 메인 페이지에 다시 접근하자 다음 API 경로가 호출되는 것을 확인하였다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks3.png)

해당 API는 UID를 기반으로 사용자 정보를 조회하는 구조로 보였다.

`/api.php/user/74` 경로에 직접 접근한 결과는 다음과 같다:

```json
{
  "uid":"74",
  "username":"htb-student",
  "full_name":"Paolo Perrone",
  "company":"Schaefer Inc"
}
```

응답에는 사용자의 UID, 사용자 이름, 전체 이름 및 회사 정보가 포함되어 있었다.

이후 비밀번호 변경 기능을 한 차례 사용해 보았다.

요청을 확인한 결과 UID와 Token 값을 전송하여 비밀번호를 변경하는 구조임을 확인할 수 있었다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks4.png)

비밀번호 변경 과정에서는 다음 API 경로도 호출되었다:

```text
/api.php/token/74
```

해당 경로에 직접 접근한 결과는 다음과 같다:

```json
{
  "token":"e51a8a14-17ac-11ec-8e67-a3c050fe0c26"
}
```

이를 통해 사용자 정보와 비밀번호 재설정에 사용되는 Token 값이 별도의 API를 통해 노출되고 있음을 확인하였다.

## API Enumeration

사용자 API를 열거하여 관리자 계정을 찾은 뒤, Token API와 비밀번호 변경 기능을 연계하면 관리자 계정을 탈취할 수 있을 것으로 판단하였다.

우선 `/api.php/user/<UID>` 경로를 순차적으로 조회하기 위해 다음 Bash 스크립트를 작성하였다:

```bash
for i in {1..100}; do
    echo "uid=$i"                                                  
    curl -s "http://154.57.164.73:31657/api.php/token/$i" | grep -Ei admin                              
done
```

UID 범위를 1부터 100까지 설정하고, 각 사용자 정보에서 `admin` 또는 `administrator` 문자열이 포함되어 있는지 확인하였다.

그 결과 UID `52` 에서 다음 사용자 정보를 발견하였다:

```json
{
  "uid":"52",
  "username":"a.corrales",
  "full_name":"Amor Corrales",
  "company":"Administrator"
}
```

`company` 값이 `Administrator` 로 설정되어 있어 관리자 계정일 가능성이 높다고 판단하였다.

이후 `/api.php/token/52` 경로에 접근하여 `Amor Corrales` 사용자의 Token 값을 획득하였다:

```json
{
  "token":"e51a85fa-17ac-11ec-8e51-e78234eb7b0c"
}
```

## Password Reset Bypass

앞에서 획득한 관리자 UID와 Token을 사용하여 비밀번호 변경 페이지인 `/reset.php` 에서 관리자 계정의 비밀번호 변경을 시도하였다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks5.png)

POST 요청으로 비밀번호 변경을 시도하자 `Access Denied` 가 반환되었다.

POST 요청에서는 세션의 UID와 요청에 포함된 UID를 비교하는 등의 접근 제어 검증이 수행되는 것으로 보였다.

이에 동일한 UID, Token 및 새 비밀번호를 유지한 채 HTTP 요청 방식을 POST에서 GET으로 변경하여 다시 전송하였다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks6.png)

그 결과 정상적으로 로그인 변경에 성공하며, POST 요청에 적용되던 접근 제어가 GET 요청에는 동일하게 적용되지 않아 관리자 계정의 비밀번호를 변경할 수 있었다.

## XXE Discovery

관리자 계정인 `a.corrales` 와 새롭게 변경한 비밀번호 `asdf1234` 를 사용하여 웹 애플리케이션에 로그인하였다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks7.png)

로그인 결과 사용자 이름이 `Amor Corrales` 로 표시되었으며, 일반 사용자 계정에서는 보이지 않았던 `ADD EVENT` 버튼이 추가로 나타났다.

이를 통해 앞에서 확인한 계정이 실제 관리자 계정임을 확인할 수 있었다.

`ADD EVENT` 기능에 접근하자 이벤트 이름, 세부 정보 및 날짜를 입력할 수 있는 페이지가 나타났다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks8.png)

이벤트 생성 요청을 Burp Suite로 가로채어 확인하였다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks9.png)

응답에는 사용자가 입력한 `name` 요소의 값이 그대로 반영되고 있었다.

따라서 `name` 요소에 Entity를 참조하면, XML Parser가 Entity를 확장한 결과도 응답에 반영될 가능성이 있다고 판단하였다.

이를 확인하기 위해 다음과 같이 외부 Entity를 정의하는 DTD를 삽입하였다:

```xml
<!DOCTYPE name [
  <!ENTITY test SYSTEM "file:///etc/passwd">
]>
```

이후 `name` 요소에서 `&test;` Entity를 참조하도록 요청을 수정하여 전송하였다:

![Web Attacks](/assets/cpts-web/web-attacks-skills-assessment/web-attacks10.png)

요청을 전송하자 응답의 이벤트 이름 부분에 대상 서버의 `/etc/passwd` 파일 내용이 출력되었다.
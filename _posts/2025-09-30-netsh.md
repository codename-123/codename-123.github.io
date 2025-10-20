---
title: "Port Forwarding with Windows Netsh"
date: 2025-09-30
layout: single
author_profile: true
toc: true
toc_label: "Netsh Port Forwarding"
toc_icon: "exchange-alt"
toc_sticky: true
tags: [networking, windows, netsh, tunneling, pivoting, portforward]
header:
  teaser: /assets/network-screenshots/netsh/netsh.png
---

**Netsh**는 Windows 환경에서 네트워크 설정을 관리할 때 사용하는 기본 제공 커맨드라인 도구이다.  

라우트 조회, 방화벽 구성 확인, 프록시 추가, 포트 포워딩 등 다양한 네트워크 관련 작업을 수행할 수 있다.  

---

# 시나리오

![Netsh Port Forward Diagram](/assets/network-screenshots/netsh/netsh.png)

공격자는 외부(`10.10.15.5`)에 있고, 내부망에는 Windows 10 기반의 워크스테이션이 존재한다.

- **피벗(Windows)** : 외부와 통신 가능한 인터페이스 `10.129.15.150`, 내부 인터페이스 `172.16.5.25`
- **내부 목표 (RDP 서버)** : `172.16.5.25:3389`
- **목표** : 공격자가 외부에서 피벗을 통해 내부 RDP (`172.16.5.25:3389`) 에 접근

공격자는 피벗(`10.129.15.150`)에 `netsh`로 포트프록시(포트포워딩)를 설정하게 하여, 피벗의 외부 IP/포트(`10.129.15.150:8080`)로 들어온 연결을 내부 RDP(`172.16.5.25:3389`)로 전달한다.

---

# 실습

## Portscan

대상 Host(`10.129.121.251`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다.

```bash
$ nmap -sC -sV 10.129.121.251          
Starting Nmap 7.95 ( https://nmap.org ) at 2025-10-01 02:57 EDT
Nmap scan report for 10.129.121.251
Host is up (0.27s latency).
Not shown: 996 closed tcp ports (reset)
PORT     STATE SERVICE       VERSION
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp  open  microsoft-ds?
3389/tcp open  ms-wbt-server Microsoft Terminal Services
| ssl-cert: Subject: commonName=OFFICEMANAGER
| Not valid before: 2025-09-30T06:55:07
|_Not valid after:  2026-04-01T06:55:07
| rdp-ntlm-info: 
|   Target_Name: OFFICEMANAGER
|   NetBIOS_Domain_Name: OFFICEMANAGER
|   NetBIOS_Computer_Name: OFFICEMANAGER
|   DNS_Domain_Name: OFFICEMANAGER
|   DNS_Computer_Name: OFFICEMANAGER
|   Product_Version: 10.0.18362
|_  System_Time: 2025-10-01T06:57:53+00:00
|_ssl-date: 2025-10-01T06:58:02+00:00; +1s from scanner time.
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled but not required
| smb2-time: 
|   date: 2025-10-01T06:57:56
|_  start_date: N/A

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 37.50 seconds
```

대상 호스트에서 `RPC(135)`, `NetBIOS(139)`, `SMB(445)`, `RDP(3389)` 서비스가 동작하는 것이 확인되었다.

## RDP 접속

문제에서 제공된 아이디/비밀번호(`htb-student/HTB_@cademy_stdnt!`) 를 이용하여 RDP 대상 호스트에 접속하였다.

```bash
$ xfreerdp3 /v:10.129.121.251 /u:htb-student /p:HTB_@cademy_stdnt!
```

세션 접속 후, `ipconfig` 명령어를 통해 내부망 IP 정보를 확인하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/netsh/ipconfig.png)

이후, 문제에서 제공된 내부망 RDP IP(172.16.5.19)에 접속하기 위해 **관리자 권한 CMD**에서 포트포워딩을 설정하였다. 

로컬의 `10.129.121.251:8080` 으로 들어오는 트래픽을 내부 호스트 `172.16.5.19`의 `3389` 포트로 포워딩하도록 설정하였다.

**netsh interface portproxy add v4tov4**: IPv4 → IPv4 포트 프록시(포트포워딩) 규칙을 추가하는 명령.

```cmd
C:\Windows\htb-student> netsh.exe interface portproxy add v4tov4 listenport=8080 listenaddress=10.129.121.251 connectport=3389 connectaddress=172.16.5.19
```

지정한 8080 포트에 대해 `netsh interface portproxy show v4tov4` 명령어로 확인한 결과, 포트포워딩이 정상적으로 설정되어 있음을 확인하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/netsh/v4tov4.png)

## 내부망 RDP 접속

포트포워딩 설정 후, 로컬 리눅스로 돌아가 문제에서 제공한 아이디/비밀번호(`victor/pass@123`) 로 내부망 RDP 연결을 시도하였다.

```bash
$ xfreerdp3 /v:10.129.121.251:8080 /u:victor /p:pass@123
```

정상적으로 연결에 성공하였고, 내부 호스트의 데스크톱 세션을 획득하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/netsh/rdp-connect.png)

## Flag 획득

데스크톱에 있는 `flag.txt` 파일 내용을 읽어 플래그를 획득하였다.

![Domain](/assets/network-screenshots/netsh/flag.png)

이로써 **포트 포워딩(netsh portproxy)** 실습을 마무리하였다.

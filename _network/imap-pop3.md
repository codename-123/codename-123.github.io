---
title: "IMAP/POP3"
date: 2025-09-28
layout: single
author_profile: true
toc: true
toc_label: "IMAP/POP3"
toc_icon: "envelope"
toc_sticky: true
header:
teaser: /assets/images/imap-pop3.png
tags: [network, mail, imap, pop3]
---

**IMAP(Internet Message Access Protocol)**은 메일 서버 상의 메일을 온라인으로 관리할 수 있게 해주는 프로토콜이다.
**POP3(Post Office Protocol v3)**는 서버에서 메일을 가져오고 로컬에 저장하는 데 초점이 맞춰져 있으며, IMAP처럼 서버 상에서 폴더 구조를 관리하거나 동기화하는 기능은 제한적이다.

---

# IMAP/POP3

- **IMAP**
  - 목적: 서버 상의 메일을 온라인으로 열람/관리(동기화)
  - 포트: 기본 `143`, 암호화 전용 `993`(IMAPS/SSL)
  - 특징: 폴더(메일박스) 구조 지원, 여러 클라이언트 간 동기화, 서버에서 직접 메시지 미리보기/검색 가능

- **POP3**
  - 목적: 서버에서 메일을 꺼내 로컬에 저장(일괄 수신)
  - 포트: 기본 `110`, 암호화 전용 `995`(POP3S/SSL)
  - 특징: 서버 기능이 단순(리스트/가져오기/삭제), 동기화 기능 제한적

---

# 동작 및 클라이언트 관점

* IMAP은 서버의 메일박스를 원격 파일시스템처럼 다루며, 클라이언트는 로컬 복사본을 만들어 오프라인 모드에서 작업할 수 있다(연결 복원 시 동기화).
* POP3는 주로 메일을 가져와 로컬에 보관하는 용도로 쓰이므로 여러 클라이언트에서 동일한 계정을 사용할 때 동기화 문제가 생길 수 있다(서버에 메일을 남기는 설정을 사용하지 않는 이상).

---

# 주요 명령어

## IMAP 주요 명령

| 명령어 | 설명 |
| ---- | ---- |
| 1 LOGIN username password | 사용자 로그인 |
| 1 LIST "" * | 모든 디렉터리(메일박스) 목록  |
| 1 CREATE "INBOX" | 메일박스 생성 |
| 1 DELETE "INBOX" | 메일박스 삭제 |
| 1 RENAME "ToRead" "Important" | 메일박스 이름 변경 |
| 1 LSUB "" * | 사용자가 구독한 메일박스 목록(하위집합) |
| 1 SELECT INBOX | 특정 메일박스 선택(읽기/검색 대상 지정) |
| 1 UNSELECT INBOX | 선택 종료 |
| 1 FETCH <ID> all | 메일의 모든 데이터를 회수 |
| 1 CLOSE | 삭제 플래그가 설정된 메시지 제거 |
| 1 LOGOUT | 연결 종료 |

## POP3 주요 명령

| 명령어 | 설명 |
| --- | --- |
| USER username | 사용자 식별 (인증 단계 1) |
| PASS password | 비밀번호 제출 (인증 단계 2) |
| STAT | 저장된 메일 수 및 총 바이트 수 요청 |
| LIST | 각 메일의 ID와 크기 요청 |
| RETR id | 지정한 ID의 메일 본문 수신 |
| DELE id | 지정한 ID의 메일 삭제 요청 |
| CAPA | 서버가 지원하는 확장 기능 조회 |
| RSET | 전달된 상태(삭제 등) 리셋 |
| QUIT | 연결 종료 |

---


# 위험한 설정 

| 설정 | 설명 |
| --- | --- |
| auth_debug | 인증 디버그 로그 활성화 |
| auth_debug_passwords | 제출된 비밀번호까지 로그에 기록 |
| auth_verbose | 인증 실패 원인 등 상세 로그 출력 |
| auth_verbose_passwords | 비밀번호 로그에 포함 가능 |
| auth_anonymous_username | ANONYMOUS SASL 사용 시 사용할 사용자명 지정 |



> **Catch-all**(모든 수신자 허용) 설정은 사용자 존재 열거 시 오탐을 야기할 수 있다.
> VRFY/EXPN 등의 명령을 허용하면 사용자 열거에 악용될 수 있다.
> 인증 로그에 비밀번호가 남지 않도록 설정해야 하며, 디버그 로그는 운영 환경에서는 비활성화를 권장한다.

---

# 실습

## Portscan

먼저 대상 Host(`10.129.65.61`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다.

```bash
$ nmap -sC -sV -p 110,143,993,995 10.129.65.61 
Starting Nmap 7.95 ( https://nmap.org ) at 2025-09-27 21:53 EDT
Nmap scan report for 10.129.65.61
Host is up (0.28s latency).

PORT    STATE SERVICE  VERSION
110/tcp open  pop3     Dovecot pop3d
| ssl-cert: Subject: commonName=dev.inlanefreight.htb/organizationName=InlaneFreight Ltd/stateOrProvinceName=London/countryName=UK
| Not valid before: 2021-11-08T23:10:05
|_Not valid after:  2295-08-23T23:10:05
|_pop3-capabilities: SASL CAPA STLS RESP-CODES PIPELINING UIDL AUTH-RESP-CODE TOP
|_ssl-date: TLS randomness does not represent time
143/tcp open  imap     Dovecot imapd
|_ssl-date: TLS randomness does not represent time
| ssl-cert: Subject: commonName=dev.inlanefreight.htb/organizationName=InlaneFreight Ltd/stateOrProvinceName=London/countryName=UK
| Not valid before: 2021-11-08T23:10:05
|_Not valid after:  2295-08-23T23:10:05
|_imap-capabilities: more LITERAL+ ID IDLE listed STARTTLS ENABLE post-login capabilities Pre-login have LOGIN-REFERRALS OK IMAP4rev1 SASL-IR LOGINDISABLEDA0001
993/tcp open  ssl/imap Dovecot imapd
|_imap-capabilities: LITERAL+ ID AUTH=PLAINA0001 IDLE Pre-login ENABLE post-login listed capabilities have LOGIN-REFERRALS OK IMAP4rev1 SASL-IR more
|_ssl-date: TLS randomness does not represent time
| ssl-cert: Subject: commonName=dev.inlanefreight.htb/organizationName=InlaneFreight Ltd/stateOrProvinceName=London/countryName=UK
| Not valid before: 2021-11-08T23:10:05
|_Not valid after:  2295-08-23T23:10:05
995/tcp open  ssl/pop3 Dovecot pop3d
|_ssl-date: TLS randomness does not represent time
|_pop3-capabilities: SASL(PLAIN) CAPA USER RESP-CODES PIPELINING UIDL AUTH-RESP-CODE TOP
| ssl-cert: Subject: commonName=dev.inlanefreight.htb/organizationName=InlaneFreight Ltd/stateOrProvinceName=London/countryName=UK
| Not valid before: 2021-11-08T23:10:05
|_Not valid after:  2295-08-23T23:10:05

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 26.75 seconds
```

Nmap 스캔을 통해 총 4개의 메일 수신 관련 서비스(`POP3`, `IMAP`, `POP3S`, `IMAPS`)가 확인되었다.

## IMAPS 접속

문제에서 제공된 아이디/비밀번호(`robin:robin`) 을 이용하여 IMAPS에 로그인을 하였다.

```bash
$ openssl s_client -connect 10.129.65.61:imaps

1 login robin robin
```

그 후 `LIST` 명령어를 사용하여 메일 박스 목록을 확인하였다.

```bash
1 LIST "" *

* LIST (\Noselect \HasChildren) "." DEV
* LIST (\Noselect \HasChildren) "." DEV.DEPARTMENT
* LIST (\HasNoChildren) "." DEV.DEPARTMENT.INT
* LIST (\HasNoChildren) "." INBOX
1 OK List completed (0.001 + 0.000 secs).
```

`\HasNoChildren` 으로 표시된 **DEV.DEPARTMENT.INT** 폴더에 접근하기 위해 `SELECT` 명령어를 사용하였다.

```bash
1 SELECT DEV.DEPARTMENT.INT

* FLAGS (\Answered \Flagged \Deleted \Seen \Draft)
* OK [PERMANENTFLAGS (\Answered \Flagged \Deleted \Seen \Draft \*)] Flags permitted.
* 1 EXISTS
* 0 RECENT
* OK [UIDVALIDITY 1636414279] UIDs valid
* OK [UIDNEXT 2] Predicted next UID
1 OK [READ-WRITE] Select completed (0.001 + 0.000 secs).
```

접근 결과, 1개의 메시지가 존재함을 확인할 수 있었다. (`1 EXISTS`)

## Flag 획득

이제 `FETCH` 명령어를 사용하여 메시지 내용 부분을 확인한 결과

![Domain](/assets/network-screenshots/imap-pop3/flag.png)

이렇게 최종적으로 **flag**를 얻어내는데 성공하였다.

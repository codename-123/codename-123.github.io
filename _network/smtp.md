---
title: "SMTP"
date: 2025-09-27
layout: single
author_profile: true
toc: true
toc_label: "SMTP"
toc_icon: "mail"
toc_sticky: true
header:
  teaser: /assets/images/smtp.png
tags: [network, smtp]
difficulty: "Medium"
arch: linux
---

**SMTP (Simple Mail Transfer Protocol)** 는 IP 네트워크에서 이메일을 전송하기 위한 프로토콜이다. 클라이언트와 메일 서버 간, 또는 SMTP 서버끼리 메일을 전달할 때 사용된다. 일반적으로 수신에는 IMAP/POP3가 병행된다.

기본 포트는 **TCP/25** 이지만, 인증·암호화를 사용하는 제출/클라이언트 연결에는 **TCP/587**, 암호화 전용 포트로 **TCP/465** 등이 사용된다. STARTTLS 확장을 통해 기존 평문 연결을 TLS로 전환할 수 있다.

SMTP는 원래 평문 프로토콜이므로 **인증 정보와 명령이 그대로 전송**될 수 있다. 따라서 서버가 STARTTLS 또는 SMTPS 등의 암호화 설정을 하지 않으면 네트워크 상에서 계정정보가 유출될 위험이 있다.

---

# 기본 동작

- 클라이언트(MUA) → Mail Submission Agent(MSA) → Mail Transfer Agent(MTA) → Mail Delivery Agent(MDA) → Mailbox(POP3/IMAP)
- 전송 흐름: 클라이언트가 SMTP 서버에 접속하여 `MAIL FROM`, `RCPT TO`, `DATA` 명령으로 메일을 제출한다. 서버는 DNS를 통해 수신측 MTA 주소를 검색해 전송을 이어간다.

# 주요 명령어 (일반)
- `HELO` / `EHLO` : 세션 시작(클라이언트 식별)
- `MAIL FROM:` : 발신자 지정
- `RCPT TO:` : 수신자 지정
- `DATA` : 본문 전송 시작(마침표 줄로 종료)
- `AUTH` : 인증(예: `AUTH PLAIN`, `AUTH LOGIN`)
- `VRFY`, `EXPN` : 사용자·메일박스 검증(서버 설정에 따라 동작 다름)
- `STARTTLS` : TLS로 전환
- `QUIT` : 세션 종료

---

# 취약점·오용 포인트 (핵심)
- **평문 전송**: TLS 미사용 시 인증정보와 메시지 내용이 노출됨.
- **Open Relay**: `mynetworks = 0.0.0.0/0` 같은 잘못된 설정은 제3자가 스팸 발송에 악용.
- **VRFY/EXPN로 사용자 열거**: 서버 설정에 따라 계정 존재 여부를 유추할 수 있음(모든 응답을 신뢰하면 안 됨).
- **버전·구성 노출**: 배너나 EHLO 응답으로 제품/기능 노출 시 알려진 취약점 탐색 가능.

---

# 실습: 명령·검증 예시 (허가된 환경에서만)

## 1) 서버 연결(기본)
```bash
$ telnet 10.129.14.128 25
```
예상 응답:
```
220 ESMTP Server
HELO mail1.inlanefreight.htb
250 mail1.inlanefreight.htb
```

## 2) 기능 확인 (EHLO)
```bash
EHLO mail1
```
예시 응답(서버 확장 나열):
```
250-PIPELINING
250-SIZE 10240000
250-ETRN
250-ENHANCEDSTATUSCODES
250-8BITMIME
250-DSN
250-SMTPUTF8
250 CHUNKING
```

## 3) 사용자 열거 (VRFY) — 서버 설정에 따라 결과가 다름
```bash
VRFY root
```
예시 응답(서버가 확인해 줄 경우):
```
252 2.0.0 root
```
> 주의: VRFY 응답은 구성에 따라 임의로 긍정(252)만 반환하도록 설정될 수 있으므로, 단독으로 계정 존재를 확신하지 말 것.

## 4) 임의 메일 전송 (간단)
```text
EHLO inlanefreight.htb
MAIL FROM:<attacker@inlanefreight.htb>
RCPT TO:<victim@inlanefreight.htb>
DATA
From: attacker@inlanefreight.htb
To: victim@inlanefreight.htb
Subject: Test
Hello
.
QUIT
```
예시 응답:
```
250 2.0.0 Ok: queued as <ID>
221 2.0.0 Bye
```

---

# 탐지·식별 포인트
- **배너/응답**: `220`, `250` 등 응답 코드와 EHLO 라인으로 기능/확장 파악.
- **VRFY/EXPN 로그**: 사용자 열거 시도 탐지.
- **미인가 릴레이 시도**: 외부로부터의 다중 수신자/대량 전송은 이상징후.
- **STARTTLS 미사용 여부**: 평문 인증이 가능한지 확인(네트워크 스니핑으로 검사).

---

# 권장 설정 및 완화 방안
- **TLS 활성화**: STARTTLS 또는 SMTPS(465)를 사용해 전송 암호화.
- **인증 필요화**: 메일 제출(포트 587)은 SMTP AUTH로 인증 필요.
- **Open relay 차단**: `mynetworks`에 신뢰된 IP만 등록, 외부 릴레이 금지.
- **VRFY/EXPN 제한**: 사용자 열거 기능 비활성화 또는 익명 응답 제한.
- **스팸·필터링 도입**: SPF, DKIM, DMARC 설정으로 스푸핑·스팸 방지.
- **로그·모니터링**: 비정상 대량 전송, 다중 인증 실패 등을 감시.

---

# 구성 확인 / 예시 (Postfix)
다음 예시는 Postfix의 `main.cf` 일부로, 내부 환경에서 흔히 보이는 설정 항목이다:

```text
smtpd_banner = ESMTP Server
myhostname = mail1.inlanefreight.htb
mynetworks = 127.0.0.0/8 10.129.0.0/16
mailbox_size_limit = 0
inet_protocols = ipv4
smtpd_helo_restrictions = reject_invalid_hostname
home_mailbox = /home/postfix
```

- `mynetworks` 항목은 허용된 네트워크를 지정하므로, 넓게 열어두면 외부 악용 가능성이 커진다.

---
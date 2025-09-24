---
title: "FTP"
date: 2025-09-25
layout: single
author_profile: true
toc: true
toc_label: "FTP"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/images/ftp.png
tags: [network, ftp]
difficulty: "Medium"
arch: linux
---


**FTP** 는 TCP 기반, 제어 채널(포트 21)과 데이터 채널(주로 포트 20 또는 서버가 제시한 포트)을 사용한다. 인증 가능(계정 필요)하고 브라우저/클라이언트 지원이 널리된다.

암호화를 사용하지 않으면 FTP 통신은 평문으로 오가므로 네트워크 상에서 패킷을 가로채면 계정 정보나 파일 내용 등이 그대로 노출된다. 예를 들어, 공격자가 패킷을 스니핑하면 로그인 시 입력한 아이디와 비밀번호를 쉽게 얻을 수 있다.

**TFTP** 는 UDP 기반 이고, 인증이 없다.

디렉터리 나열 기능이 없고 신뢰성이 낮아, 로컬이나 보호된 네트워크에서만 사용하는 것이 권장된다.

## Active FTP, Passive FTP

A
 

## Exploitation
(고수준 설명 — 세부 exploit 코드 게시에 주의)

## Privilege Escalation
...

## 정리 / 방어 포인트
- 핵심 취약점 요약
- 방어 방안

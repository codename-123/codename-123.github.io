---
title: "SNMP"
date: 2025-09-28
layout: single
author_profile: true
toc: true
toc_label: "SNMP"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/images/snmp.png   # → 썸네일 이미지 경로(원하는 그림으로 교체)
tags: [network, snmp]
---

**SNMP (Simple Network Management Protocol)** 은 네트워크 장비를 모니터링하고 원격 설정까지 수행할 수 있는 표준 프로토콜이다.  

라우터, 스위치, 서버, IoT 기기 등 SNMP를 지원하는 장비는 UDP 기반으로 정보 조회/변경이 가능하다.

---

# SNMP 개요

- 포트: 데이터 교환 **UDP 161**, 이벤트 알림(Trap) **UDP 162**  
- 역할: 네트워크 장비 상태 모니터링, 설정 변경 및 제어  
- 특징: 조회(GET)뿐 아니라 **제어(SET)** 지원, 장비 이벤트를 **Trap**으로 즉시 알림

---

# MIB (Management Information Base)

SNMP 객체가 제조사에 상관없이 공통 포맷으로 정의될 수 있도록 만든 데이터 사전.  

MIB 파일은 **ASN.1 기반 텍스트** 형식이며, 각 객체는 고유 주소(OID), 이름, 타입, 접근 권한 등을 포함한다.

---

# OID (Object Identifier)

MIB 내 각 노드를 **숫자 체인**으로 표현한 고유 경로.  

점(dot)으로 구분된 정수들의 연속이며, 체인이 길수록 더 구체적인 정보에 접근한다.

---

# 버전 비교

| 버전 | 특징 | 보안 |
|---|---|---|
| **SNMPv1** | 최초 버전. 단순한 조회/설정/Trap 지원 | 인증, 암호화 없음 (평문) |
| **SNMPv2c** | v1 확장, 성능 개선. community 기반 접근 | community 문자열 평문 전송 |
| **SNMPv3** | 사용자명/비밀번호 인증, 암호화 지원 | 강력한 보안, 설정 복잡 |

**Community String(v1/v2c 전용)**: 장치 접근을 허가하는 비밀번호(`public=읽기`, `private=읽기/쓰기`)이며 평문 전송되어 스니핑 위험이 있다.

---

# 기본 구성

SNMP 데몬의 기본 구성은 IP 주소, 포트, MIB, OID, 인증 및 커뮤니티 문자열을 포함한 서비스의 기본 설정을 정의한다.

```bash
cat /etc/snmp/snmpd.conf | grep -v "#" | sed -r '/^\s*$/d'

sysLocation    Sitting on the Dock of the Bay
sysContact     Me <me@example.org>
sysServices    72
master         agentx
agentaddress   127.0.0.1,[::1]
view   systemonly  included   .1.3.6.1.2.1.1
view   systemonly  included   .1.3.6.1.2.1.25.1
rocommunity    public default -V systemonly
rocommunity6   public default -V systemonly
rouser         authPrivUser authpriv -V systemonly
```

---

# 위험한 설정

| 설정 | 설명 |
| --- | --- |
| rwuser noauth | 인증 없이 전체 OID 트리 쓰기 권한 |
| rwcommunity <string> <IP> | 지정 IP 무관 전체 쓰기 권한 |
| rwcommunity6 <string> <IPv6> | IPv6 환경에서 동일 위험 |

> 불필요한 `rw*` 옵션 제거, v3 전환, 방화벽 제한 필수


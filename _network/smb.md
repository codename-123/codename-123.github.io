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

**SMB (Server Message Block)**는 파일, 디렉터리뿐 아니라 프린터, IPC(인터프로세스 통신) 등 네트워크 자원 접근을 규정하는 클라이언트-서버 프로토콜이다. Windows 계열의 네트워크 서비스에서 주로 사용되며, Samba 프로젝트를 통해 Linux/Unix에서도 호환, 운영이 가능하다.

SMB는 네트워크 상의 다른 호스트가 공유한 리소스(share)에 접속해 파일을 읽고 쓰는 방식으로 동작한다. SMB 통신은 TCP를 통해 이루어지며(기본적으로 445/tcp, 과거 NetBIOS 연동시 137/138/139), 연결 수립 전 TCP 3-way handshake를 거친다.

> 주의: SMB v1(CIFS)은 구형이며 보안 취약점(예: WannaCry 등)으로 인해 실서비스에서는 비활성화하고 SMB2/3를 권장한다.

---

# SMB 개요 및 버전

- **역할**: 파일/프린터 공유, 원격 실행·관리, 네임/보안 관리 등  
- **포트**: 445/tcp (CIFS 포함), NetBIOS: 137/138/139 (레거시)  
- **주요 버전**
  - CIFS (SMB1) — Windows NT4 / NetBIOS 기반
  - SMB 1.0 — Windows 2000
  - SMB 2.0 / 2.1 — Vista/Server2008 이상 (성능·메시지 최적화)
  - SMB 3.0 / 3.1.1 — Windows 8/10, 암호화·무결성 등 보안 기능 추가

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

아래 설정들은 편의성 때문에 활성화하면 보안상 큰 위험을 초래할 수 있다.

| 설정 | 설명 |
|------|------|
| guest ok = yes / usershare allow guests = yes | 익명 접속 허용 |
| browseable = yes | 공유 목록 노출 |
| writable = yes | 쓰기 허용 (파일 생성/수정) |
| enable privileges = yes | SID 기반 특권(권한) 허용 |
| create mask = 0777 / directory mask = 0777 | 과도한 권한 부여 |
| unix password sync = yes / pam password change | 계정 동기화 위험 |


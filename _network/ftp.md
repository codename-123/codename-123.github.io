---
title: "FTP"
date: 2025-09-24
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

---

# 제어 채널(Control Channel)/데이터 채널(Data Channel)

## 제어 채널

- **역할**: 로그인, 명령 송수신, 전송 모드 협상 등 세션 제어를 담당한다.  
- **프로토콜/포트**: TCP, 기본 포트 21.  
- **특징**:
  - 데이터 채널 협상이 모두 이 채널에서 이뤄진다.  
  - FTPS(SSL/TLS)로 보호 가능(기본 FTP는 평문)하다.  
- **Wireshark**:
  - PORT 21 패킷에 `USER`, `PASS`, `PASV`, `PORT`, `EPRT`, `EPSV` 같은 명령이 보이면 제어 채널이다.  
  - 상태 코드 예: `220` (서비스 준비), `150` (데이터 연결 열림), `226` (전송 완료)

## 데이터 채널 (Data Channel)

- **역할**: 파일 업로드/다운로드, 디렉토리 목록 전송(LIST) 등 데이터 전송 전용 채널이다.  
- **프로토콜/포트**: TCP. Active/Passive에 따라 동작 방식과 사용 포트가 달라진다.

### 동작

- **Active 모드**
  1. 클라이언트가 제어 채널(21)로 접속하고 `PORT`/`EPRT`로 **자신의 IP, PORT**를 서버에 알린다.  
  2. 서버가 클라이언트가 알려준 주소로 **역방향 연결(서버 → 클라이언트)**을 시도해 데이터 채널을 연다.

- **Passive 모드**
  1. 클라이언트가 제어 채널에서 `PASV`/`EPSV` 요청한다.  
  2. 서버가 자신의 **IP, PORT**(또는 포트만)를 응답한다.  
  3. 클라이언트가 해당 **서버 IP:PORT**로 **정방향 연결(클라이언트 → 서버)**을 시도해 데이터 채널을 연다.

---

# Active FTP/Passive FTP

## Active FTP

Active FTP는 클라이언트가 TCP PORT 21을 통해 설명한 대로 연결을 설정하고, 서버가 응답을 전송할 수 있는 클라이언트 측 포트를 서버에 알려준다. 그러나 방화벽이 클라이언트를 보호하는 경우, 모든 외부 연결이 차단되어 서버는 응답할 수 없다. 

![Domain](/assets/network-screenshots/ftp/active-mode.png)

> 클라이언트 IP, PORT를 상대방 서버에게 전달 → 서버가 클라이언트로 **역방향 접속**(서버가 클라이언트가 알려준 포트로 연결) → 클라이언트가 `NAT` 뒤에 존재한다고 가정하면(사설 IP 사용) 서버가 그 사설 주소로 직접 도달할 수 없고, 별도의 **포트포워딩이나 매핑이 설정되어 있지 않으면 연결이 실패할 가능성이 높다**.

## Passive FTP

서버는 클라이언트가 데이터 채널을 설정할 수 있는 포트를 알려준다. 클라이언트가 이 방식으로 연결을 시작하므로 방화벽은 전송을 차단하지 않는다.

![Domain](/assets/network-screenshots/ftp/passive-mode.png)

> 클라이언트가 연결 요청 → 서버가 지정해준 IP, PORT를 클라이언트에게 전달 → 클라이언트가 서버로 **정방향 접속**(클라이언트가 서버에게 알려준 포트로 연결) → 클라이언트가 사설 IP 환경(`NAT`)에 있더라도, `NAT`는 클라이언트의 출발지 주소를 공인 IP, 임시포트로 매핑해서 외부로 내보내므로, 데이터 연결이 서버 쪽으로 **정상적으로 들어오게** 되어 `NAT`의 영향을 덜 받는다.

---

# 기본 구성

## vsFTPd 설치

```bash
sudo apt install vsftpd 
```

**vsFTPd**는 리눅스, 유닉스 시스템에서 FTP 서비스를 제공하는 서버 프로그램이다.
가볍고 빠르며 보안성이 뛰어나 기업, 기관 서버에서 자주 사용되며, Active/Passive 모드를 모두 지원하며 TLS/SSL 기반 FTPS를 제공한다.

## vsFTPd 구성 파일

```bash
cat /etc/vsftpd.conf | grep -v "#"
```

위 명령어 실행 후, 주요 옵션들을 살펴보면 다음과 같다.

| 설정                  | 설명               |
| ------------------- | ---------------- |
| listen=NO           | inetd 방식으로 실행 여부 |
| listen_ipv6=YES     | IPv6 리스닝 활성화     |
| anonymous_enable=NO | 익명 로그인 허용 여부     |
| local_enable=YES    | 로컬 사용자 로그인 허용    |
| xferlog_enable=YES  | 업/다운로드 로그 기록     |
| ssl_enable=NO       | SSL 암호화 연결       |


또한, FTP는 암호를 평문으로 전송하기 때문에, 다음과 같은 설정은 실서비스에서 매우 위험하다.

| 설정 | 설명 |
|------|------|
| anonymous_enable=YES | 익명 로그인 허용 |
| anon_upload_enable=YES | 익명 업로드 허용 |
| anon_mkdir_write_enable=YES | 익명 디렉터리 생성 허용 |
| no_anon_password=YES | 비밀번호 없이 접속 |

# 실습




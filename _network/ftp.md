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

# Active FTP, Passive FTP

## Active FTP

Active FTP는 클라이언트가 TCP PORT 21을 통해 설명한 대로 연결을 설정하고, 서버가 응답을 전송할 수 있는 클라이언트 측 포트를 서버에 알려준다. 그러나 방화벽이 클라이언트를 보호하는 경우, 모든 외부 연결이 차단되어 서버는 응답할 수 없다. 

![Domain](/assets/network-screenshots/ftp/active-mode.png)

> 클라이언트 IP, PORT를 상대방 서버에게 전달 → 서버가 클라이언트로 **역방향 접속**(서버가 클라이언트가 알려준 포트로 연결) → 클라이언트가 `NAT` 뒤에 존재한다고 가정하면(사설 IP 사용) 서버가 그 사설 주소로 직접 도달할 수 없고, 별도의 **포트포워딩이나 매핑이 설정되어 있지 않으면 연결이 실패할 가능성이 높다**.

## Passive FTP

서버는 클라이언트가 데이터 채널을 설정할 수 있는 포트를 알려준다. 클라이언트가 이 방식으로 연결을 시작하므로 방화벽은 전송을 차단하지 않는다.

![Domain](/assets/network-screenshots/ftp/passive-mode.png)

> 클라이언트가 연결 요청 → 서버가 지정해준 IP, PORT를 클라이언트에게 전달 → 클라이언트가 서버로 **정방향 접속**(클라이언트가 서버에게 알려준 포트로 연결) → 클라이언트가 사설 IP 환경(`NAT`)에 있더라도, `NAT`는 클라이언트의 출발지 주소를 공인 IP, 임시포트로 매핑해서 외부로 내보내므로, 데이터 연결이 서버 쪽으로 **정상적으로 들어오게** 되어 `NAT`의 영향을 덜 받는다.


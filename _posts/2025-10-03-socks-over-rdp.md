---
title: "RDP and SOCKS Tunneling with SocksOverRDP"
date: 2025-10-03
layout: single
author_profile: true
toc: true
toc_label: "SocksOverRDP"
toc_icon: "network-wired"
toc_sticky: true
tags: [rdp, socks, tunneling, pivoting]
header:
  teaser: /assets/network-screenshots/socks-over-rdp/socks-over-rdp.png
  teaser_home_page: true
---

**SocksOverRDP**는 **RDP의 Dynamic Virtual Channels(DVC)**를 통해 임의의 패킷을 터널링하고 대상에서 SOCKS 프록시를 생성해 Proxifier 등으로 내부망으로 피벗할 수 있게 한다.

이 공격을 수행하기 위해 먼저 공격 호스트에 적절한 바이너리를 다운로드 한다.
- 공식 GitHub Releases에서 다운로드: [SocksOverRDP Releases](https://github.com/nccgroup/SocksOverRDP/releases)
- 공식 Proxifier 사이트에서 다운로드: [Proxifier](https://www.proxifier.com/download/#win-tab)  

---

# 실습

## RDP 접속

우선 문제에서 제공한 아이디/비밀번호(`htb-student/HTB_@cademy_stdnt!`) 를 이용하여 RDP 접속을 하였다.

```bash
$ xfreerdp3 /v:10.129.77.99 /u:htb-student /p:HTB_@cademy_stdnt! 
```

접속이 완료되면, 위에서 준비한 `SocksOverRDP`와` Proxifier 바이너리`를 원격 데스크톱 세션으로 복사(파일 전송)를 하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/copy.png)

## regsvr32.exe를 사용하여 SocksOverRDP.dll 로드

이후 관리자 권한으로 열린 CMD에서 `SocksOverRDP-Plugin.dll`을 등록하면 **SocksOverRDP 플러그인이 활성화되었다는 창**이 뜬다. 

이제 RDP 세션 내에서 DVC 기반의 연결을 통해 프록시 터널을 사용할 수 있다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/plugin-success.png)

## 내부망 RDP 접속

문제에서 제공한 내부망 RDP IP `172.16.5.19`에 원격 데스크톱 클라이언트(Remote Desktop Connection)를 이용해 접속을 시도하면, `SocksOverRDP 플러그인`이 활성화되어 **`127.0.0.1:1080`로 SOCKS 리스너를 열었다**는 메시지가 표시되었다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/port-1080.png)

`netstat` 명령어로 확인한 결과 `1080` 포트가 **ESTABLISHED 상태로 실행 중**임을 확인하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/netstat.png)

이후 문제에서 제공한 내부망 RDP 아이디/비밀번호(`victor/pass@123`)을 입력하여 접속에 성공하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/victor-connect.png)

내부망에 `SocksOverRDP-Server.exe` 파일을 복사한 뒤 관리자 권한으로 실행하여 서버 측 컴포넌트를 활성화했다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/server-connect.png)

## Proxifier 구성

원격 데스크톱으로 넘어가 `Proxifier` 를 실행시킨 후, `Proxy Server` 설정을 추가하여 타입을 `SOCKS5`로, 주소를 `127.0.0.1`, 포트를 `1080`으로 지정했다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/proxy-server.png)

문제에서 제공한 RDP IP `172.16.6.155`로 원격 데스크톱 클라이언트(Remote Desktop Connectio)를 이용해 접속을 시도했다.

Proxifier 창에서 `mstsc.exe` 프로세스가 `172.16.6.155:3389` 의 연결을 생성했으며, 해당 트래픽이 설정된 프록시 규칙(`127.0.0.1:1080`)을 통해 우회된 것을 확인하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/mstsc.png)

최종적으로 내부망 `172.16.6.155` 의 로그인 창이 표시되었고, 문제에서 제공한 계정(`jason/WellConnected123!`) 을 입력하여 내부망 접근에 성공했다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/rdp-connect.png)

## Flag 획득

데스크톱에 있는 `flag.txt` 파일을 읽어 플래그를 획득에 성공하였다.

![Netsh Port Forward Diagram](/assets/network-screenshots/socks-over-rdp/flag.png)

이로써 **SocksOverRDP** 실습을 마무리하였다.







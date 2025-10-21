---
title: "Dynamic Port Forwarding"
date: 2025-09-29
layout: single
excerpt: "동적 포트 포워딩(Dynamic Port Forwarding)은 **SOCKS 프록시를 이용해 다양한 내부망 서비스로의 트래픽을 유연하게 전달**하는 기술이다. 공격자는 SSH 세션을 통해 로컬 호스트에 **SOCKS 리스너(프록시)** 를 열고, 이를 통해 방화벽이나 라우팅 제한을 우회하여 **여러 IP/포트를 동적으로 스캔**하거나 서비스에 접근할 수 있다. 이 방식은 방화벽으로 보호된 네트워크에서 **프록시 체인(proxychains)** 과 함께 사용되어, 외부 공격자가 직접 라우팅할 수 없는 서브넷으로 패킷을 전달하는 데 매우 효과적이다."
author_profile: true
toc: true
toc_label: "Dynamic Port Forwarding"
toc_icon: "network-wired"
toc_sticky: true
tags: [networking, ssh, socks, proxychains, pivoting]
categories: [network]
header:
  teaser: /assets/network-screenshots/dynamic-port-forwarding/dynamic-port-forwarding.png
  teaser_home_page: true
---

# 개요

동적 포트 포워딩(Dynamic Port Forwarding)은 **SOCKS 프록시를 이용해 다양한 내부망 서비스로의 트래픽을 유연하게 전달**하는 기술이다.

공격자는 SSH 세션을 통해 로컬 호스트에 **SOCKS 리스너(프록시)** 를 열고, 이를 통해 방화벽이나 라우팅 제한을 우회하여 **여러 IP/포트를 동적으로 스캔**하거나 서비스에 접근할 수 있다.

이 방식은 방화벽으로 보호된 네트워크에서 **프록시 체인(proxychains)** 과 함께 사용되어,  
외부 공격자가 직접 라우팅할 수 없는 서브넷으로 패킷을 전달하는 데 매우 효과적이다.

---

# SSH Dynamic Port Forwarding (SOCKS 프록시)

![Dynamic Port Forwarding](/assets/network-screenshots/dynamic-port-forwarding/dynamic-port-forwarding.png)

위 다이어그램은 SSH를 이용해 **SOCKS 리스너(포트 9050)** 를 생성한 뒤,  
이를 통해 `172.16.5.0/23` 내부망을 스캔하는 과정을 나타낸다.

- 공격 호스트(10.10.15.5) : Proxychains를 사용하여 Nmap 등 스캐너를 실행  
- 중간 SSH 서버(10.129.15.50 / 172.16.5.129) : SOCKS 트래픽을 내부망으로 전달  
- 목적지 네트워크(172.16.5.0/23) : 직접 라우팅이 불가능하지만 SOCKS를 통해 접근 가능

```bash
$ ssh -D 9050 ubuntu@10.129.15.50
```

위 명령은 공격자 로컬 호스트의 `9050` 포트에서 SOCKS5 프록시를 생성하고,
트래픽을 SSH 세션을 통해 내부망(`172.16.5.0/23`)으로 전달한다.

---

# SOCK4/SOCK5

SOCKS 프록시는 두 가지 버전이 존재한다.

| 버전         | 특징                |
| ---------- | ----------------- |
| SOCKS4 | 인증 기능 없음, UDP 미지원 |
| SOCKS5 | 사용자 인증 지원, UDP 지원 |


대부분 `SOCKS5` 를 사용하여 보안성과 다양한 프로토콜을 지원하는 환경을 구축한다.

---

# 실습

## Portscan

먼저 대상 Host(`10.129.185.108`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다.

```bash
$ nmap -sC -sV 10.129.185.108  

Starting Nmap 7.95 ( https://nmap.org ) at 2025-09-28 22:09 EDT
Nmap scan report for 10.129.185.108
Host is up (0.27s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 3f:4c:8f:10:f1:ae:be:cd:31:24:7c:a1:4e:ab:84:6d (RSA)
|   256 7b:30:37:67:50:b9:ad:91:c0:8f:f7:02:78:3b:7c:02 (ECDSA)
|_  256 88:9e:0e:07:fe:ca:d0:5c:60:ab:cf:10:99:cd:6c:a7 (ED25519)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.41 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 19.75 seconds
```

Nmap 스캔 결과 `SSH(22)`, `http(80)` 등 서비스가 확인되었다.

## SSH 연결

우선 문제에서 제공한 아이디/비밀번호(`ubuntu:HTB_@cademy_stdnt!`) 를 이용하여 SSH 접속에 시도하였다.

```bash
$ ssh ubuntu@10.129.185.108
```

접속 후, `ifconfig` 명령어를 통하여 내부망 IP 를 탐색하였다.

![Domain](/assets/network-screenshots/dynamic-port-forwarding/ifconfig.png)

문제에서 제공된 내부망 IP(`172.16.5.19`) 를 이용하여 RDP(`3389 포트`)의 서비스가 열려 있는 것을 확인하였다.

```bash
$ nc -vz 172.16.5.19 3389

Connection to 172.16.5.19 3389 port [tcp/ms-wbt-server] succeeded!
```

## /etc/proxychains.conf 확인

`/etc/proxychains4.conf` 파일에 SOCKS 프록시 포트 `9050`이 설정되어 있는지 확인하였다.

```bash
$ tail -4 /etc/proxychains4.conf

# meanwile
# defaults set to "tor"
socks4  127.0.0.1 9050
```

설정에서 `127.0.0.1:9050`에 SOCKS 프록시가 설정되어 있으므로, 해당 포트로 **동적 포트 포워딩(SSH -D)** 을 실행한 뒤 `proxychains`를 통해 내부망 스캔/접속을 진행한다.

## Dynamic Port Forwarding

내부망 RDP 서비스(`172.16.5.19:3389`)에 접근하기 위해 **SSH 동적 포트 포워딩**을 설정하였다.

```bash
$ ssh -D 9050 ubuntu@10.129.185.108
```

접속 후 `netstat` 명령어를 통하여 `9050` 포트가 정상적으로 실행 중인지 확인하였다.

```bash
$ netstat -antp | grep 9050

(Not all processes could be identified, non-owned process info
 will not be shown, you would have to be root to see it all.)
tcp        0      0 127.0.0.1:9050          0.0.0.0:*               LISTEN      44477/ssh           
tcp6       0      0 ::1:9050                :::*                    LISTEN      44477/ssh  
```

출력에서 `127.0.0.1:9050` 이 **LISTEN** 상태이다.

이제 `proxychains`를 이용하여 SOCKS 프록시(`127.0.0.1:9050`)를 통해 내부망 RDP에 접속을 시도하였다.

```bash
$ proxychains xfreerdp3 /v:172.16.5.19 /u:victor /p:pass@123
```

정상적으로 RDP 세션에 접속하는 데 성공하였다.

![Domain](/assets/network-screenshots/dynamic-port-forwarding/rdp-connect.png)

## Flag 획득

세션 접속 후, 데스크톱에 위치한 flag 파일을 확인하고 내용을 읽어 플래그를 획득하였다.

![Domain](/assets/network-screenshots/dynamic-port-forwarding/flag.png)

이로써 **Dynamic Port Forwarding** 실습을 마무리하였다.
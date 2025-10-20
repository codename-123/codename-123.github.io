---
title: "Local Port Forwarding"
date: 2025-09-29
layout: single
author_profile: true
toc: true
toc_label: "Local Port Forwarding"
toc_icon: "network-wired"
toc_sticky: true
tags: [networking, ssh, tunneling, socks, pivoting]
header:
  teaser: /assets/network-screenshots/local-port-forwarding/local-port-forwarding.png
  teaser_home_page: true
---

# 개요

포트 포워딩은 통신 요청을 한 포트에서 다른 포트로 리디렉션하는 기술이다. 

포트 포워딩은 주로 TCP 계층에서 동작하며, 전달되는 포트에 대해 인터랙티브한 통신을 제공한다.
그러나 SSH나 SOCKS(비 애플리케이션 계층)과 같은 다른 프로토콜을 사용하여 트래픽을 캡슐화할 수도 있다. 

이 방법은 방화벽을 우회하거나 이미 장악한 호스트를 통해 다른 네트워크로 피벗할 때 효과적이다.

---

# SSH 로컬 포트 포워딩

![Domain](/assets/network-screenshots/local-port-forwarding/local-port-forwarding.png)

위 다이어그램은 로컬 포트 포워딩의 예를 보여준다.
공격 호스트(`10.10.15.5`)가 로컬 포트 `1234`를 대상으로 피해 서버(`172.16.5.129`, `10.129.15.50`)의 원격 포트 `3306`으로 전달을 요청한다. 
SSH는 로컬 포트 `1234`에서 트래픽을 수신하고, 이를 MySQL의 `localhost:3306`으로 전달한 후 포트 `22`를 통해 돌아온다.

---

# 실습

## Portscan

먼저 대상 Host(`10.129.202.64`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다.

```bash
$ nmap -sC -sV 10.129.202.64  
                                               
Starting Nmap 7.95 ( https://nmap.org ) at 2025-09-28 21:17 EDT
Nmap scan report for 10.129.202.64
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
$ ssh ubuntu@10.129.202.64
```

접속 후, `ifconfig` 명령어를 통하여 내부망 IP 를 탐색하였다.

![Domain](/assets/network-screenshots/local-port-forwarding/ifconfig.png)

문제에서 제공된 내부망 IP(`172.16.5.19`) 를 이용하여 RDP(`3389 포트`)의 서비스가 열려 있는 것을 확인하였다.

```bash
$ nc -vz 172.16.5.19 3389

Connection to 172.16.5.19 3389 port [tcp/ms-wbt-server] succeeded!
```

## Local Port Forwarding

위에서 확인한 내부망 RDP 서비스(`172.16.5.19:3389`)에 접근하기 위해 **SSH 로컬 포트 포워딩**을 설정하였다.

```bash
$ ssh -L localhost:1234:172.16.5.19:3389 ubuntu@10.129.202.64
```

위 명령어는 공격자 로컬 호스트의 `1234` 포트를 대상 내부망의 `172.16.5.19:3389` 포트와 연결한다.

설정 후, 로컬 호스트에서 `netstat` 명령어를 사용해 `1234` 포트가 정상적으로 열려 있는지 확인하였다.

```bash
$ netstat -antp | grep 1234 

(Not all processes could be identified, non-owned process info
 will not be shown, you would have to be root to see it all.)
tcp        0      0 127.0.0.1:1234          0.0.0.0:*               LISTEN      17895/ssh           
tcp6       0      0 ::1:1234                :::*                    LISTEN      17895/ssh   
```

출력 결과를 통해 `1234` 포트가 SSH 프로세스를 통해 정상적으로 **LISTEN 상태**임을 확인할 수 있다.

## Flag 획득

이제 로컬 호스트에서 문제에서 제공된 RDP 계정 아이디/비밀번호(`victor:pass@123`)를 이용하여 **RDP 연결 요청**을 시도하였다.

```bash
$ xfreerdp3 /v:127.0.0.1:1234 /u:victor /p:pass@123
```

정상적으로 RDP 세션을 수립하는 데 성공하였다.

![Domain](/assets/network-screenshots/local-port-forwarding/rdp-connect.png)

세션 접속 후, 데스크톱에 위치한 flag 파일을 확인하고 내용을 읽어 플래그를 획득하였다.

![Domain](/assets/network-screenshots/local-port-forwarding/flag.png)

이로써 **Local Port Forwarding** 실습을 마무리하였다.




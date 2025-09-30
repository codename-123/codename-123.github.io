---
title: "SSH Pivoting with Sshuttle"
date: 2025-09-29
layout: single
author_profile: true
toc: true
toc_label: "SSH Pivoting (sshuttle)"
toc_icon: "exchange-alt"
toc_sticky: true
tags: [networking, ssh, tunneling, pivoting, sshuttle]
header:
  teaser: /assets/network-screenshots/sshuttle/sshuttle.png
---

**Sshuttle**은 파이썬으로 작성된 툴로, 별도의 프록시 설정(proxychains 등) 없이도 SSH 기반으로 네트워크 피벗(pivoting)을 쉽게 구성해 줍니다.  
주요 아이디어는 로컬 머신(공격자)이 원격 호스트(피벗)를 통해 특정 네트워크 대역으로 라우팅을 설정하여, 원격 내부망 리소스에 접근하거나 스캐닝·접속을 수행하는 것입니다.

Sshuttle은 내부에서 `iptables` 규칙을 자동으로 구성하고 SSH 터널을 이용해 트래픽을 전달하므로 사용이 간편합니다. 다만 이 도구는 **오직 SSH 기반 피벗**에 한정되며 TOR나 HTTPS 프록시 같은 다른 채널을 통한 피벗 옵션은 제공하지 않습니다.

---

## 설치 (Ubuntu pivot에서)
```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y python3-pip
sudo pip3 install sshuttle

# 또는 배포판 패키지로 설치 가능 (환경에 따라 다름)
# sudo apt install sshuttle
```
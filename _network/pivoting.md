---
title: "Pivoting, Tunneling, Port Forwarding"
date: 2025-09-28
layout: single
author_profile: true
toc: true
toc_label: "Pivoting"
toc_icon: "network-wired"
toc_sticky: true
header:
  teaser: /assets/images/pivoting.png
tags: [network, pivoting, tunneling]
---

**Pivoting, Tunneling, Port Forwarding** 는 침투테스트/레드팀 작업에서  
격리된 네트워크로 접근하거나 명령/제어(C2) 트래픽을 은닉하기 위해 사용하는 핵심 기법이다.

![Pivoting Visualized](/assets/images/pivoting.gif)

---

# 개념 정리

| 용어 | 의미 | 특징/목적 |
|------|-----------|-----------|
| Pivoting | 이미 장악한 피벗 호스트를 거쳐 다른 네트워크 세그먼트로 진입 | 이중 NIC(dual-homed)/다중 네트워크를 활용해 격리망 우회 |
| Tunneling | 특정 프로토콜에 다른 트래픽을 캡슐화해 전달 | HTTP/HTTPS, SSH 등을 사용해 트래픽 은닉 |
| Port Forwarding | 포트 단위로 트래픽을 중계/리다이렉션 | 로컬→리모트, 리모트→로컬 터널 구축 |
| Lateral Movement | 동일 네트워크 내 다른 호스트로 가로 확장 | 권한 상승·도메인 장악 목적 |

---

# 예시

- **Pivoting**: 내부망과 OT망을 동시에 물고 있는 엔지니어링 워크스테이션을 확보 후, 그 호스트를 경유해 OT망으로 스캔 및 추가 공격.
- **Tunneling**: C2 트래픽을 HTTP/HTTPS GET/POST 요청에 숨겨 IDS/IPS 탐지를 회피.
- **Port Forwarding**: SSH `-L` / `-R` 옵션으로 특정 포트 트래픽을 안전하게 중계.

---

# Networking Behind Pivoting

## IP Addressing & NICs

- 네트워크에 참여하려면 **IP 주소**가 필요하다.  
  - DHCP로 자동 할당 또는 **정적 할당**(서버, 라우터, 프린터 등 중요 장비).
- IP는 **NIC(Network Interface Controller)** 에 매핑되며, 한 시스템에 여러 NIC(물리, 가상)가 있을 수 있다.
- 피벗 기회를 찾을 때는 `ifconfig/ip addr show`(Linux/macOS) / `ipconfig`(Windows) 로 **추가 NIC와 IP**를 확인한다.

```bash
# ifconfig 예시
eth0: inet 134.122.100.200  ...
eth1: inet 10.106.0.172    ...
tun0: inet 10.10.15.54     ...  # VPN 터널
```
- `eth0` 처럼 **공인 IP**가 있는 인터페이스는 인터넷과 직접 통신 가능,
  `eth1`·`tun0` 등 **사설 IP**는 내부망 통신 전용.

## Routing

- **라우터**는 목적지 IP에 따라 패킷을 전달한다.  
  - 일반 PC도 라우팅 테이블이 있으면 라우터 역할 수행 가능.
- `netstat -r` 또는 `ip route(ip route show)` 로 테이블 확인 →  
  **도달 가능한 네트워크**와 **추가해야 할 경로**를 파악한다.

```bash
# netstat -r 예시
Destination     Gateway         Genmask         Iface
default         178.62.64.1     0.0.0.0         eth0
10.10.10.0      10.10.14.1      255.255.254.0   tun0
...
```

## Protocols, Services & Ports

- **프로토콜**은 통신 규칙, **포트**는 애플리케이션을 식별하는 소프트웨어 단위.
- 예: HTTP → TCP 80. 방화벽이 허용해야 웹 서비스가 정상 동작.
- 오픈 포트는 네트워크 침투/피벗 경로가 될 수 있으므로 **서비스/포트 스캔** 결과를 활용해 진입점을 찾는다.

---
title: "OnlyForYou (Medium)"
date: 2025-10-25
layout: single
excerpt: "OnlyForYou는 중간 난이도 머신으로, 웹 애플리케이션에 존재하는 LFI(Local File Inclusion) 취약점을 통해 소스 코드를 열람할 수 있고, 이 코드에서 발견된 Blind Command Injection을 이용해 셸을 획득할 수 있다. 이후 머신 내부에서 실행 중인 여러 로컬 서비스 중 하나가 기본 자격 증명을 사용하고 있으며, 이 서비스의 특정 엔드포인트는 Cypher 인젝션에 취약하여 Neo4j 데이터베이스의 해시를 유출할 수 있고, 이 해시를 통해 SSH 접근 권한을 얻는다. 마지막으로, sudoers 파일이 잘못 구성되어 있어 pip3 download 명령을 루트 권한으로 실행할 수 있으며, 이를 이용해 Gogs에 호스팅된 악성 파이썬 패키지를 다운로드하고 실행함으로써 루트 권한을 탈취할 수 있다."
author_profile: true
toc: true
toc_label: "OnlyForYou"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-linux/onlyforyou/onlyforyou.png
  teaser_home_page: true
categories: [hackthebox linux]
tags: [htb, web, medium, jwt, sqli, priv-esc]
---
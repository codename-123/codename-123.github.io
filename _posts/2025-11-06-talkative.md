---
title: "Talkative (Hard)"
date: 2025-11-06
layout: single
excerpt: "Talkative는 하드 난이도의 Linux 머신으로, 초기 진입점은 Jamovi 웹 애플리케이션에 존재하는 명령어 삽입(Command Injection) 취약점으로, 이를 이용해 Jamovi가 실행 중인 Docker 컨테이너 내부로 진입할 수 있다. 컨테이너 내부에서는 .omv 파일을 발견할 수 있으며, 이를 압축 해제함으로써 Bolt CMS의 admin 사용자 자격 증명을 확보할 수 있으며, 확보한 계정으로 로그인한 후에는, Twig 템플릿 엔진에 존재하는 SSTI(Server Side Template Injection) 취약점을 이용해 www-data 권한의 셸을 획득할 수 있다. 이후 네트워크를 추가로 탐색하면, 내부 시스템에 존재하는 saul 사용자로 권한을 확장할 수 있다. root 권한을 얻기 위해서는 포트 포워딩을 설정하여, 별도의 컨테이너에서 실행 중인 MongoDB 인스턴스에 접속해야 하며, 이를 통해 RocketChat에 등록된 사용자의 권한을 조작하여 웹 GUI의 관리자 대시보드에 접근할 수 있다. 이후 RocketChat의 웹훅(Webhook) 기능을 추가로 악용함으로써, RocketChat 컨테이너 내부에서 root 셸을 획득할 수 있다. 마지막으로, 컨테이너 내에서 libcap2 패키지를 설치하고 시스템 Capabilities를 조회하면 CAP_DAC_READ_SEARCH 권한이 활성화되어 있음을 확인할 수 있으며, 이를 악용하여 shocker 익스플로잇을 실행하고 호스트의 루트 권한을 탈취할 수 있다"
author_profile: true
toc: true
toc_label: "Talkative"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-linux/talkative/talkative.png
  teaser_home_page: true
categories: [hackthebox linux]
tags: [htb, linux, web, lfi, command-injection, rce, neo4j, priv-esc, cypher-injection, gogs, pip-exploit, sudo, chisel, reverse-shell]
---

![Talkative](/assets/htb-linux/talkative/talkative.png)

**Talkative**는 하드 난이도의 Linux 머신이다.  
초기 진입점은 `Jamovi` 웹 애플리케이션에 존재하는 **명령어 삽입(Command Injection)** 취약점으로, 이를 이용해 `Jamovi`가 실행 중인 **Docker 컨테이너 내부로 진입**할 수 있다.

컨테이너 내부에서는 `.omv` 파일을 발견할 수 있으며, 이를 압축 해제함으로써 `Bolt CMS`의 `admin` 사용자 자격 증명을 확보할 수 있다.

확보한 계정으로 로그인한 후에는, `Twig` 템플릿 엔진에 존재하는 **SSTI(Server Side Template Injection)** 취약점을 이용해 `www-data` 권한의 셸을 획득할 수 있다.

이후 네트워크를 추가로 탐색하면, 내부 시스템에 존재하는 `saul` 사용자로 **권한을 확장**할 수 있다.

`root` 권한을 얻기 위해서는 **포트 포워딩을 설정하여**, 별도의 컨테이너에서 실행 중인 `MongoDB` 인스턴스에 접속해야 하며, 이를 통해 `RocketChat`에 등록된 사용자의 권한을 조작하여 웹 GUI의 **관리자 대시보드에 접근**할 수 있다.

이후 `RocketChat`의 **웹훅(Webhook)** 기능을 추가로 악용함으로써, `RocketChat` 컨테이너 내부에서 `root` 셸을 획득할 수 있다.

마지막으로, 컨테이너 내에서 `libcap2` 패키지를 설치하고 **시스템 Capabilities**를 조회하면 `CAP_DAC_READ_SEARCH` 권한이 활성화되어 있음을 확인할 수 있으며, 이를 악용하여 `shocker` 익스플로잇을 실행하고 **호스트의 루트 권한을 탈취**할 수 있다.
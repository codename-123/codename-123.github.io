---
title: "MonitorsThree (Medium)"
date: 2026-03-09
layout: single
excerpt: "MonitorsThree는 Medium 난이도의 Linux 머신으로 네트워크 솔루션을 제공하는 회사의 웹사이트를 대상으로 한 공격 체인을 다룬다. 웹사이트에는 비밀번호 재설정 기능이 존재하며 해당 페이지는 SQL Injection 취약점에 노출되어 있다. 공격자는 이 취약점을 이용해 데이터베이스에서 사용자 자격증명을 추출하고 웹 애플리케이션 접근 권한을 획득한다. 이후 웹사이트를 추가로 열거하는 과정에서 Cacti가 구동 중인 서브도메인을 발견하고 앞서 획득한 자격증명을 사용해 해당 Cacti 인스턴스에 로그인한다. Cacti 인스턴스는 CVE-2024-25641 취약점에 영향을 받으며 이를 악용해 시스템 내에서 초기 접근 권한을 획득한다. 이후 시스템 내부 열거 과정에서 데이터베이스 접근 자격증명을 발견하고 데이터베이스 내에서 해시 값을 확보한 뒤 이를 크랙하여 사용자 비밀번호를 획득한다. 마지막으로 시스템에서 열린 포트를 조사하는 과정에서 취약한 Duplicati 인스턴스가 실행 중인 것을 확인하고 해당 취약점을 악용해 marcus 사용자의 SSH 공개 키를 root 계정의 authorized_keys에 추가한 뒤 marcus의 개인 키를 이용해 SSH로 root 계정에 접속하고 최종적으로 시스템의 루트 권한을 탈취한다."
author_profile: true
toc: true
toc_label: "MonitorsThree"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-linux/monitorsthree/monitorsthree.png
  teaser_home_page: true
categories: [hackthebox-linux]
tags: [htb, linux, web, spring-boot, actuator, heapdump, credential-leak, eureka, misconfiguration, service-abuse, lateral-movement, ssh, suid, priv-esc]

---

![MonitorsThree](/assets/htb-linux/monitorsthree/monitorsthree.png)

**MonitorsThree**는 Medium 난이도의 Linux 머신으로, 네트워크 솔루션을 제공하는 회사의 웹사이트를 대상으로 한 공격 체인을 다룬다.  

웹사이트에는 비밀번호 재설정 기능이 존재하며, 해당 페이지는 **SQL Injection 취약점**에 노출되어 있다. 공격자는 이 취약점을 이용해 데이터베이스에서 사용자 자격증명을 추출하고 웹 애플리케이션에 접근한다.

웹사이트를 추가로 열거하는 과정에서 **Cacti가 구동 중인 서브도메인**을 발견할 수 있으며, 앞서 SQL Injection을 통해 획득한 자격증명을 사용해 해당 Cacti 인스턴스에 로그인할 수 있다. 이후 Cacti 인스턴스가 **`CVE-2024-25641` 취약점**에 영향을 받는다는 것을 확인하고, 이를 악용해 시스템 내에서 초기 접근 권한을 획득한다.

시스템 내부를 추가로 열거하는 과정에서 데이터베이스 접근 자격증명을 확인할 수 있으며, 데이터베이스 내에서 해시 값을 발견한다. 공격자는 해당 해시를 크랙하여 사용자 계정의 비밀번호를 획득한다.

마지막으로 시스템에서 열린 포트를 조사하는 과정에서 **취약한 Duplicati 인스턴스**가 실행 중인 것을 확인한다. 공격자는 이 취약점을 악용해 `marcus` 사용자의 **SSH 공개 키를 root 계정의 `authorized_keys`에 추가**하고, `marcus` 의 개인 키를 이용해 SSH로 root 계정에 접속하여 최종적으로 시스템의 **루트 권한을 탈취**하게 된다.
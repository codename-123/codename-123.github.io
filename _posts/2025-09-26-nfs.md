---
title: "NFS"
date: 2025-09-26
layout: single
author_profile: true
toc: true
toc_label: "NFS"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/images/nfs.png
tags: [network, nfs]
---

**NFS**는 Sun Microsystems에서 개발한 네트워크 파일 시스템으로, SMB와 같은 목적(원격 파일 시스템 접근)을 가지고 있다.  
클라이언트는 원격 파일 시스템을 **로컬 파일 시스템처럼 접근**할 수 있다.  
그러나 SMB와 달리 **Linux/Unix 환경 전용** 프로토콜을 사용하며, NFS 클라이언트는 SMB 서버와 직접 통신할 수 없다.

---

# NFS 버전과 특징

| 버전 | 특징 |
|------|------|
| NFSv2 | UDP 기반, 오래되었지만 많은 시스템에서 지원 |
| NFSv3 | 가변 파일 크기, 개선된 오류 보고, NFSv2와 완전 호환 불가 |
| NFSv4 | Kerberos 지원, 방화벽 통과 가능, ACL 지원, 상태 기반(Stateful) 연산, 성능 향상 |
| NFSv4.1 | pNFS 확장으로 클러스터 환경 지원, 세션 트렁킹(NFS multipathing) 포함, TCP/UDP 2049 포트만 사용 |

> NFS는 ONC-RPC(SUN-RPC) 기반이며, 인증/권한 관리는 RPC 옵션과 파일 시스템 정보에 따라 이루어진다.  
> 일반적으로 UNIX UID/GID 및 그룹 멤버십을 통해 인증하며, 클라이언트와 서버의 UID/GID 매핑이 다를 수 있으므로 **신뢰할 수 있는 네트워크에서 사용**하는 것이 권장된다.

---

# 구성

```bash
$ cat /etc/exports

# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
#
# Example for NFSv2 and NFSv3:
# /srv/homes       hostname1(rw,sync,no_subtree_check) hostname2(ro,sync,no_subtree_check)
#
# Example for NFSv4:
# /srv/nfs4        gss/krb5i(rw,sync,fsid=0,crossmnt,no_subtree_check)
# /srv/nfs4/homes  gss/krb5i(rw,sync,no_subtree_check)
```

기본 exports 파일의 설정은 이러하다.

| 옵션               | 설명                      |
| ---------------- | ----------------------- |
| rw               | 읽기/쓰기 권한                |
| ro               | 읽기 전용 권한                |
| sync             | 동기식 전송(안정적, 느림)         |
| async            | 비동기 전송(빠름)              |
| no_subtree_check | 하위 디렉토리 검사 비활성화         |
| root_squash      | 클라이언트의 root(UID 0)을 익명 사용자(nobody)로 매핑 |

---

# 위험한 설정

NFS를 사용하더라도 잘못된 설정은 회사와 인프라에 위험할 수 있다. 

| 옵션             | 위험성                               |
| -------------- | --------------------------------- |
| rw             | 모든 사용자가 쓰기 가능                     |
| insecure       | 1024 이상 포트 사용 가능 → 비루트 사용자가 접근 가능 |
| no_root_squash | root 권한 유지 → 보안상 위험               |

---

# 실습

## Portscan

먼저 대상 Host(`10.129.135.242`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다.

```bash
$ nmap -sC -sV 10.129.135.242                        
Starting Nmap 7.95 ( https://nmap.org ) at 2025-09-26 07:59 EDT
Nmap scan report for 10.129.135.242
Host is up (0.27s latency).
Not shown: 994 closed tcp ports (reset)
PORT     STATE SERVICE     VERSION
21/tcp   open  ftp
| fingerprint-strings: 
|   GenericLines: 
|     220 InFreight FTP v1.1
|     Invalid command: try being more creative
|_    Invalid command: try being more creative
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_-rw-r--r--   1 ftpuser  ftpuser        39 Nov  8  2021 flag.txt
22/tcp   open  ssh         OpenSSH 8.2p1 Ubuntu 4ubuntu0.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 3f:4c:8f:10:f1:ae:be:cd:31:24:7c:a1:4e:ab:84:6d (RSA)
|   256 7b:30:37:67:50:b9:ad:91:c0:8f:f7:02:78:3b:7c:02 (ECDSA)
|_  256 88:9e:0e:07:fe:ca:d0:5c:60:ab:cf:10:99:cd:6c:a7 (ED25519)
111/tcp  open  rpcbind     2-4 (RPC #100000)
| rpcinfo: 
|   program version    port/proto  service
|   100000  2,3,4        111/tcp   rpcbind
|   100000  2,3,4        111/udp   rpcbind
|   100000  3,4          111/tcp6  rpcbind
|   100000  3,4          111/udp6  rpcbind
|   100003  3           2049/udp   nfs
|   100003  3           2049/udp6  nfs
|   100003  3,4         2049/tcp   nfs
|   100003  3,4         2049/tcp6  nfs
|   100005  1,2,3      40785/udp6  mountd
|   100005  1,2,3      53031/tcp   mountd
|   100005  1,2,3      54907/udp   mountd
|   100005  1,2,3      55073/tcp6  mountd
|   100021  1,3,4      35985/tcp6  nlockmgr
|   100021  1,3,4      41432/udp6  nlockmgr
|   100021  1,3,4      42600/udp   nlockmgr
|   100021  1,3,4      42629/tcp   nlockmgr
|   100227  3           2049/tcp   nfs_acl
|   100227  3           2049/tcp6  nfs_acl
|   100227  3           2049/udp   nfs_acl
|_  100227  3           2049/udp6  nfs_acl
139/tcp  open  netbios-ssn Samba smbd 4
445/tcp  open  netbios-ssn Samba smbd 4
2049/tcp open  nfs         3-4 (RPC #100003)
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port21-TCP:V=7.95%I=7%D=9/26%Time=68D68031%P=x86_64-pc-linux-gnu%r(Gene
SF:ricLines,74,"220\x20InFreight\x20FTP\x20v1\.1\r\n500\x20Invalid\x20comm
SF:and:\x20try\x20being\x20more\x20creative\r\n500\x20Invalid\x20command:\
SF:x20try\x20being\x20more\x20creative\r\n");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Host script results:
| smb2-time: 
|   date: 2025-09-26T12:00:05
|_  start_date: N/A
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled but not required
|_nbstat: NetBIOS name: DEVSMB, NetBIOS user: <unknown>, NetBIOS MAC: <unknown> (unknown)

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 77.16 seconds
```

Nmap 스캔 결과 `FTP(21)`, `SSH(22)`, `SMB(139/445)`, `NFS(2049)` 등 여러 서비스가 확인되었다.  
특히 **NFS(Network File System)** 서비스가 2049/TCP에서 열려 있으며 `rpcbind(111)`도 함께 노출되어 있어,  
네트워크를 통한 원격 파일 시스템 공유가 이루어지고 있음을 알 수 있다.

## NFS 탐색

`showmount` 명령어를 이용하여 어떤 공유 파일이 있는지 열거해보았다.

```bash
$ showmount -e 10.129.135.242
```

실행 결과, 원격 호스트는 다음 두 경로를 NFS로 내보내고 있었다.

![Domain](/assets/network-screenshots/nfs/showmount.png)

`/var/nfs`와 `/mnt/nfsshare`가 `10.0.0.0/8` 대역(대규모 내부 네트워크)에 대해 마운트 허용되어 있다.

즉, 동일 네트워크 내의 어느 호스트에서든 접근 가능할 수 있다.

## 공유 마운트

이제 해당 공유를 마운트 하여 파일 목록을 확인하고 민감한 파일이 있는지 조사하였다.

우선, `mkdir` 명령어를 통하여 마운트 할 디렉토리를 만들었다.

```bash
$ mkdir mount
```

후에, 만든 디렉토리를 마운트 포인트로 사용하여 원격 NFS 공유를 로컬 시스템에 연결하였다.

```bash
$ sudo mount -t nfs 10.129.135.242:/ ./mount/ -o nolock
```

## Flag 획득

마운트된 디렉토리로 이동 후, `mnt/mntshare` 경로에 플래그가 존재함을 확인하였다.

![Domain](/assets/network-screenshots/nfs/flag.png)

이렇게 최종적으로 **flag**를 확보할 수 있었다.


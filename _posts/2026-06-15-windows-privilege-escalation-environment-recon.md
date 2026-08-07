---
title: "Windows Privilege Escalation - Environment Recon"
date: 2026-06-15
layout: single
excerpt: "Windows 권한 상승을 위해 네트워크, 보안 설정, 프로세스, Access Token, Named Pipe 등을 열거하고 권한 상승 가능성을 확인하는 방법을 정리한다."
author_profile: true
toc: true
toc_label: "Windows Privilege Escalation"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, uac, access-token, named-pipe]
---

Windows 권한 상승을 위해 네트워크, 보안 설정, 프로세스, Access Token, Named Pipe 등을 열거하고 권한 상승 가능성을 확인하는 방법을 정리한다.

# Situational Awareness

## Network Information

처음에는 네트워크 열거를 통해 현재 호스트가 어떤 네트워크에 연결되어 있는지 확인하고, 추가로 접근 가능한 내부 네트워크가 존재하는지 판단할 수 있다.

호스트에 여러 네트워크 인터페이스가 연결되어 있다면, 해당 호스트가 서로 다른 네트워크 사이의 피벗 지점으로 활용될 가능성이 있다.

IP 정보를 열거하면 다음과 같다:

```cmd
C:\htb> ipconfig /all

Windows IP Configuration

   Host Name . . . . . . . . . . . . : WINLPE-SRV01
   Primary Dns Suffix  . . . . . . . :
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No
   DNS Suffix Search List. . . . . . : .htb

Ethernet adapter Ethernet1:

   Connection-specific DNS Suffix  . :
   Description . . . . . . . . . . . : vmxnet3 Ethernet Adapter
   Physical Address. . . . . . . . . : 00-50-56-B9-C5-4B
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::f055:fefd:b1b:9919%9(Preferred)
   IPv4 Address. . . . . . . . . . . : 192.168.20.56(Preferred)
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.20.1
   DHCPv6 IAID . . . . . . . . . . . : 151015510
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-27-ED-DB-68-00-50-56-B9-90-94
   DNS Servers . . . . . . . . . . . : 8.8.8.8
   NetBIOS over Tcpip. . . . . . . . : Enabled

Ethernet adapter Ethernet0:

   Connection-specific DNS Suffix  . : .htb
   Description . . . . . . . . . . . : Intel(R) 82574L Gigabit Network Connection
   Physical Address. . . . . . . . . : 00-50-56-B9-90-94
   DHCP Enabled. . . . . . . . . . . : Yes
   Autoconfiguration Enabled . . . . : Yes
   IPv6 Address. . . . . . . . . . . : dead:beef::e4db:5ea3:2775:8d4d(Preferred)
   Link-local IPv6 Address . . . . . : fe80::e4db:5ea3:2775:8d4d%4(Preferred)
   IPv4 Address. . . . . . . . . . . : 10.129.43.8(Preferred)
   Subnet Mask . . . . . . . . . . . : 255.255.0.0
   Lease Obtained. . . . . . . . . . : Thursday, March 25, 2021 9:24:45 AM
   Lease Expires . . . . . . . . . . : Monday, March 29, 2021 1:28:44 PM
   Default Gateway . . . . . . . . . : fe80::250:56ff:feb9:4ddf%4
                                       10.129.0.1
   DHCP Server . . . . . . . . . . . : 10.129.0.1
   DHCPv6 IAID . . . . . . . . . . . : 50352214
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-27-ED-DB-68-00-50-56-B9-90-94
   DNS Servers . . . . . . . . . . . : 1.1.1.1
                                       8.8.8.8
   NetBIOS over Tcpip. . . . . . . . : Enabled
```

이처럼 현재 호스트는 `10.129.43.8/16` 과 `192.168.20.56/24` 두 개의 IPv4 인터페이스를 가지고 있다.

따라서 이 호스트는 `10.129.0.0/16` 과 `192.168.20.0/24` 네트워크에 직접 연결되어 있으며, 환경과 접근 권한에 따라 `192.168.20.0/24` 대역으로 피벗할 수 있는 지점이 될 가능성이 있다.

또한 `10.129.43.8` 인터페이스의 기본 게이트웨이로 `10.129.0.1` 이 설정되어 있다.

기본 게이트웨이는 현재 호스트가 직접 연결되어 있지 않은 다른 네트워크로 패킷을 전달할 때 사용하는 다음 홉이다.

또한 ARP 캐시를 확인해 보자:

```cmd
C:\htb> arp -a

Interface: 10.129.43.8 --- 0x4
  Internet Address      Physical Address      Type
  10.129.0.1            00-50-56-b9-4d-df     dynamic
  10.129.43.12          00-50-56-b9-da-ad     dynamic
  10.129.43.13          00-50-56-b9-5b-9f     dynamic
  10.129.255.255        ff-ff-ff-ff-ff-ff     static
  224.0.0.22            01-00-5e-00-00-16     static
  224.0.0.252           01-00-5e-00-00-fc     static
  224.0.0.253           01-00-5e-00-00-fd     static
  239.255.255.250       01-00-5e-7f-ff-fa     static
  255.255.255.255       ff-ff-ff-ff-ff-ff     static

Interface: 192.168.20.56 --- 0x9
  Internet Address      Physical Address      Type
  192.168.20.255        ff-ff-ff-ff-ff-ff     static
  224.0.0.22            01-00-5e-00-00-16     static
  224.0.0.252           01-00-5e-00-00-fc     static
  239.255.255.250       01-00-5e-7f-ff-fa     static
  255.255.255.255       ff-ff-ff-ff-ff-ff     static
```

ARP 캐시를 보면 `10.129.0.1` 게이트웨이와 `10.129.43.12`, `10.129.43.13` 에 대한 동적 ARP 엔트리가 존재한다.

이는 현재 호스트가 같은 로컬 네트워크에서 해당 IP 주소와 통신하면서 IP 주소에 대응하는 MAC 주소를 학습한 흔적이다. 

반면 `10.129.255.255`, `224.~`, `239.~`, `255.255.255.255`와 같은 항목은 브로드캐스트 또는 멀티캐스트 주소이다.

라우팅 테이블을 통해 현재 호스트가 어떤 네트워크로 패킷을 전달할 수 있는지도 확인할 수 있다:

```cmd
C:\htb> route print

===========================================================================
Interface List
  9...00 50 56 b9 c5 4b ......vmxnet3 Ethernet Adapter
  4...00 50 56 b9 90 94 ......Intel(R) 82574L Gigabit Network Connection
  1...........................Software Loopback Interface 1
  3...00 00 00 00 00 00 00 e0 Microsoft ISATAP Adapter
  5...00 00 00 00 00 00 00 e0 Teredo Tunneling Pseudo-Interface
 13...00 00 00 00 00 00 00 e0 Microsoft ISATAP Adapter #2
===========================================================================

IPv4 Route Table
===========================================================================
Active Routes:
Network Destination        Netmask          Gateway       Interface  Metric
          0.0.0.0          0.0.0.0       10.129.0.1      10.129.43.8     25
          0.0.0.0          0.0.0.0     192.168.20.1    192.168.20.56    271
       10.129.0.0      255.255.0.0         On-link       10.129.43.8    281
      10.129.43.8  255.255.255.255         On-link       10.129.43.8    281
   10.129.255.255  255.255.255.255         On-link       10.129.43.8    281
        127.0.0.0        255.0.0.0         On-link         127.0.0.1    331
        127.0.0.1  255.255.255.255         On-link         127.0.0.1    331
  127.255.255.255  255.255.255.255         On-link         127.0.0.1    331
     192.168.20.0    255.255.255.0         On-link     192.168.20.56    271
    192.168.20.56  255.255.255.255         On-link     192.168.20.56    271
   192.168.20.255  255.255.255.255         On-link     192.168.20.56    271
        224.0.0.0        240.0.0.0         On-link         127.0.0.1    331
        224.0.0.0        240.0.0.0         On-link       10.129.43.8    281
        224.0.0.0        240.0.0.0         On-link     192.168.20.56    271
  255.255.255.255  255.255.255.255         On-link         127.0.0.1    331
  255.255.255.255  255.255.255.255         On-link       10.129.43.8    281
  255.255.255.255  255.255.255.255         On-link     192.168.20.56    271
===========================================================================
Persistent Routes:
  Network Address          Netmask  Gateway Address  Metric
          0.0.0.0          0.0.0.0     192.168.20.1  Default
===========================================================================
```

## Enumerating Protections

요즘 환경에는 보통 안티바이러스나 EDR이 설치되어 있어 위협을 감시하고, 경고하거나 차단한다.

이런 보안 제품은 시스템 열거 과정이나 권한 상승 과정에서 방해가 될 수 있다. 특히 공개된 PoC 익스플로잇이나 잘 알려진 도구를 사용하면 탐지되거나 차단될 가능성이 높다.

Windows Defender의 상태를 확인하는 명령은 다음과 같다:

```powershell
PS C:\htb> Get-MpComputerStatus

AMEngineVersion                 : 1.1.17900.7
AMProductVersion                : 4.10.14393.2248
AMServiceEnabled                : True
AMServiceVersion                : 4.10.14393.2248
AntispywareEnabled              : True
AntispywareSignatureAge         : 1
AntispywareSignatureLastUpdated : 3/28/2021 2:59:13 AM
AntispywareSignatureVersion     : 1.333.1470.0
AntivirusEnabled                : True
AntivirusSignatureAge           : 1
AntivirusSignatureLastUpdated   : 3/28/2021 2:59:12 AM
AntivirusSignatureVersion       : 1.333.1470.0
BehaviorMonitorEnabled          : False
ComputerID                      : 54AF7DE4-3C7E-4DA0-87AC-831B045B9063
ComputerState                   : 0
FullScanAge                     : 4294967295
FullScanEndTime                 :
FullScanStartTime               :
IoavProtectionEnabled           : False
LastFullScanSource              : 0
LastQuickScanSource             : 0
NISEnabled                      : False
NISEngineVersion                : 0.0.0.0
NISSignatureAge                 : 4294967295
NISSignatureLastUpdated         :
NISSignatureVersion             : 0.0.0.0
OnAccessProtectionEnabled       : False
QuickScanAge                    : 4294967295
QuickScanEndTime                :
QuickScanStartTime              :
RealTimeProtectionEnabled       : False
RealTimeScanDirection           : 0
PSComputerName                  :
```

Defender 서비스와 백신 기능 자체는 존재하고 활성화되어 있다:

```text
AMServiceEnabled   : True
AntivirusEnabled   : True
AntispywareEnabled : True
```

하지만 실제 주요 보호 기능은 꺼져 있다:

```text
RealTimeProtectionEnabled : False
BehaviorMonitorEnabled    : False
OnAccessProtectionEnabled : False
IoavProtectionEnabled     : False
NISEnabled                : False
```

즉, Defender는 설치되어 있고 서비스도 활성화되어 있지만 실시간 보호, 동작 모니터링, 다운로드 검사, 네트워크 검사와 같은 주요 보호 기능은 비활성화된 상태다.

또한 AppLocker 정책을 확인할 수 있다:

```powershell
PS C:\htb> Get-AppLockerPolicy -Effective | select -ExpandProperty RuleCollections

PathConditions      : {%WINDIR%\Installer\*}
PathExceptions      : {}
PublisherExceptions : {}
HashExceptions      : {}
Id                  : 5b290184-345a-4453-b184-45305f6d9a54
Name                : (Default Rule) All Windows Installer files in %systemdrive%\Windows\Installer
Description         : Allows members of the Everyone group to run all Windows Installer files located in
                      %systemdrive%\Windows\Installer.
UserOrGroupSid      : S-1-1-0
Action              : Allow

PathConditions      : {%PROGRAMFILES%\*}
PathExceptions      : {}
PublisherExceptions : {}
HashExceptions      : {}
Id                  : 06dce67b-934c-454f-a263-2515c8796a5d
Name                : (Default Rule) All scripts located in the Program Files folder
Description         : Allows members of the Everyone group to run scripts that are located in the Program Files folder.
UserOrGroupSid      : S-1-1-0
Action              : Allow

PathConditions      : {*}
PathExceptions      : {}
PublisherExceptions : {}
HashExceptions      : {}
Id                  : ed97d0cb-15ff-430f-b82c-8d7832957725
Name                : (Default Rule) All scripts
Description         : Allows members of the local Administrators group to run all scripts.
UserOrGroupSid      : S-1-5-32-544
Action              : Allow
```

이 출력에서 `Everyone` 은 `%WINDIR%\Installer\*` 경로의 Windows Installer 파일과 `%PROGRAMFILES%\*` 경로의 스크립트를 실행할 수 있도록 허용되어 있다.

또한 로컬 Administrators 그룹(`S-1-5-32-544`)에는 `PathConditions` 가 `*` 로 지정된 스크립트 허용 규칙이 존재한다.

AppLocker 정책을 특정 파일에 적용했을 때의 결과도 확인할 수 있다:

```powershell
PS C:\htb> Get-AppLockerPolicy -Local | Test-AppLockerPolicy -path C:\Windows\System32\cmd.exe -User Everyone

FilePath                    PolicyDecision MatchingRule
--------                    -------------- ------------
C:\Windows\System32\cmd.exe         Denied c:\windows\system32\cmd.exe
```

이 결과에서는 로컬 AppLocker 정책을 기준으로 `Everyone` 에 대해 `cmd.exe` 실행이 `Denied` 로 판정된다.

---

# Initial Enumeration

Windows 호스트에서 낮은 권한의 셸을 얻었다면, 다음 단계는 권한 상승 가능성을 찾기 위해 시스템을 조사하는 것이다.

호스트에서 더 높은 권한을 확보하면 민감한 파일이나 공유 폴더에 접근하거나 다른 자격 증명을 획득할 가능성이 생긴다.

Active Directory 환경이라면 획득한 자격 증명과 권한 관계에 따라 추가적인 횡적 이동이나 도메인 권한 상승으로 이어질 수도 있다.

## Process and User Enumeration

우선 현재 어떤 프로세스와 서비스가 실행되고 있는지 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv1.png)

이처럼 `csrss.exe`, `wininit.exe`, `winlogon.exe` 와 같은 Windows 핵심 프로세스가 실행 중이며, `tasklist /svc` 를 통해 일부 프로세스에 연결된 서비스도 함께 확인할 수 있다.

또한 `Tomcat8` 과 `FileZilla Server` 처럼 웹 애플리케이션이나 FTP와 관련된 서비스도 확인할 수 있다.

위 사진에서 `Tomcat8` 이 `PID 2204` 에서 실행되고 있으므로, 해당 프로세스가 어떤 포트를 사용하는지 다음과 같이 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv2.png)

출력에서 `PID 2204` 가 `0.0.0.0:8080` 에서 **LISTENING 상태**이므로 Tomcat이 TCP 8080 포트에서 외부 연결을 기다리고 있음을 확인할 수 있다.

또한 이 호스트에 어떤 로컬 사용자 계정이 존재하는지도 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv3.png)

`net user` 출력은 현재 호스트에 존재하는 로컬 사용자 계정 목록을 보여준다. 

여기에서 서비스 계정처럼 보이는 `sccm_svc`, `sql_dev`, `secsvc` 등의 계정을 확인하고 추가 열거 대상으로 삼을 수 있다.

현재 실제로 로그인 세션을 가지고 있는 사용자는 다음과 같이 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv4.png)

현재 `sccm_svc` 사용자가 Session ID `1` 의 `console` 세션에 로그인되어 있다. 

`console` 은 로컬 또는 VM 콘솔 세션을 의미한다.

Session ID `1` 을 기준으로 해당 세션에서 실행 중인 프로세스를 확인할 수도 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv5.png)

이처럼 `tasklist /v /fi "SESSION eq 1"` 을 이용하면 Session ID `1` 에 속한 프로세스를 열거할 수 있다. 

이를 통해 다른 로그인 세션에서 실행되는 프로그램과 프로세스를 확인하고, 권한 상승에 활용할 수 있는 서비스나 프로그램, 파일 경로, 자격 증명 노출 여부 등의 단서를 추가로 조사할 수 있다.

다만 위 출력의 User Name이 N/A로 표시되므로, 이 결과만으로 각 프로세스의 실제 실행 계정을 단정할 수는 없다.

## Access Tokens and UAC

권한 상승 과정에서는 현재 프로세스의 Access Token에 어떤 Privilege가 포함되어 있는지도 중요하다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv6.png)

`whoami /priv` 를 사용하면 현재 셸 프로세스의 토큰에 포함된 Privilege와 활성화 상태를 확인할 수 있다.

현재 일반 권한 셸에서는 `SeChangeNotifyPrivilege` 와 `SeIncreaseWorkingSetPrivilege` 가 확인된다.

반면 관리자 권한으로 상승시킨 새로운 셸에서 다시 확인하면 다음과 같다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv7.png)

이 경우 앞선 일반 권한 셸과 비교했을 때 `SeTakeOwnershipPrivilege` 가 추가로 포함되어 있음을 확인할 수 있다. 

즉, 프로세스가 어떤 사용자와 어떤 Access Token으로 실행되는지에 따라 사용할 수 있는 Privilege가 달라질 수 있다.

> 이러한 차이는 UAC와도 관련이 있다. 
> 관리자 계정이 UAC의 Admin Approval Mode를 사용하는 경우 일반 프로그램은 보통 필터링된 Medium Integrity 토큰으로 실행되고, UAC 승인을 거친 새 프로세스는 High Integrity의 관리자 토큰으로 실행될 수 있다. 
> 표준 사용자가 관리자 자격 증명을 입력해 상승하는 경우에는 새 프로세스가 다른 관리자 계정의 토큰으로 실행될 수도 있다.

현재 UAC를 통해 관리자 권한으로 실행한 셸의 무결성 수준을 확인하면 다음과 같다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv8.png)

`Mandatory Label\High Mandatory Level` 이 표시되므로 현재 프로세스는 High Integrity Level에서 실행되고 있음을 알 수 있다.

반대로 UAC 상승 없이 일반 셸에서 확인하면 다음과 같다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv9.png)

이 경우 `Mandatory Label\Medium Mandatory Level` 이 표시된다.

따라서 UAC 전후의 셸은 서로 다른 Access Token을 사용할 수 있으며, 그에 따라 Privilege와 Integrity Level도 달라질 수 있다.

---

# Communication with Processes

Windows에서는 프로세스 간 통신(`IPC`)을 위해 Named Pipe를 사용할 수 있다.

Named Pipe는 한 프로세스가 다른 프로세스나 서비스에 요청 데이터를 전달하고, 상대 프로세스가 처리한 결과를 다시 반환하는 통신 채널로 사용할 수 있다.

## Named Pipe Enumeration

예를 들어 `srvsvc` 는 Windows Server Service Remote Protocol에서 사용되는 Named Pipe endpoint 중 하나다.

사용자가 `net view \\server` 와 같은 명령을 실행하면 `net.exe` 가 Windows 네트워크 관리 API를 호출하고, 필요한 경우 RPC 요청이 `\pipe\srvsvc` 와 같은 Named Pipe를 통해 Server 서비스 측으로 전달된다. 

즉, 사용자가 입력한 명령어와 인자를 프로그램이 먼저 해석하고, 필요한 인자 값을 서비스가 처리할 수 있는 요청 형식으로 변환한 뒤 Named Pipe를 통해 전달하는 구조다.

현재 존재하는 Named Pipe는 PowerShell에서 다음과 같이 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv10.png)

또한 [PipeList](https://learn.microsoft.com/en-us/sysinternals/downloads/pipelist) 도구를 활용하여 현재 열려 있는 Named Pipe와 인스턴스 수를 확인할 수도 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv11.png)

이처럼 `lsass`, `eventlog`, `spoolss`, `srvsvc`, `SQLLocal\SQLEXPRESS01` 등 다양한 Named Pipe가 존재하는 것을 확인할 수 있다.

## Named Pipe Permissions and SQL Server

[AccessChk](https://learn.microsoft.com/en-us/sysinternals/downloads/accesschk)를 활용하면 특정 Named Pipe에 어떤 접근 권한이 설정되어 있는지도 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv12.png)

현재 `\\.\Pipe\SQLLocal\SQLEXPRESS01` Pipe에서 Everyone 그룹에는 `FILE_READ_DATA`, `FILE_WRITE_DATA`, `READ_CONTROL` 등을 포함한 읽기 및 쓰기 권한이 부여되어 있다.

이는 일반 로컬 사용자도 해당 SQL Server Named Pipe에 클라이언트로 연결하여 SQL Server와 요청 및 응답 데이터를 주고받을 수 있다는 의미다.

현재 Windows 계정으로 해당 Named Pipe에 직접 연결해 보면 다음과 같다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-environment-recon/windows-priv13.png)

`sqlcmd -S np:\\.\pipe\SQLLocal\SQLEXPRESS01 -E` 를 통해 Named Pipe를 명시적으로 사용하여 SQL Server에 Windows 통합 인증으로 연결하였다.

`1>` 프롬프트가 출력되었으며, 이후 SELECT @@VERSION;과 GO를 실행하여 SQL Server의 버전 정보를 정상적으로 조회할 수 있었다.
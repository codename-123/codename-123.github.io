---
title: "Password Attacks - Password Cracking Techniques"
date: 2026-08-13
layout: single
excerpt: "John the Ripper와 Hashcat을 이용한 사전, 마스크, 룰 기반 해시 크래킹, 사용자 맞춤형 워드리스트 생성, 보호된 Office 파일 및 네트워크 서비스의 비밀번호 공격 기법을 실습한다."
author_profile: true
toc: true
toc_label: "Password Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [cpts, password-cracking, john, hashcat, brute-force]
---

John the Ripper와 Hashcat을 이용한 사전, 마스크, 룰 기반 해시 크래킹, 사용자 맞춤형 워드리스트 생성, 보호된 Office 파일 및 네트워크 서비스의 비밀번호 공격 기법을 실습한다.

# Introduction to Password Cracking

우선 패스워드 크래킹을 이해하려면 해시의 특성을 알아둘 필요가 있다.

일반적인 해시 함수는 입력값이 조금이라도 달라지면 결과값이 크게 달라지며, 동일한 입력에는 동일한 해시가 생성되는 결정적 특성을 가진다.

다만 실제 운영체제나 애플리케이션에서 비밀번호를 저장할 때는 Salt를 추가한 전용 Password Hashing 방식을 사용하는 경우가 많기 때문에, 같은 비밀번호라고 하더라도 항상 같은 저장 해시가 생성되는 것은 아니다.

예를 들어 단순한 문자열 `asdf1234@` 를 MD5로 계산하면 다음과 같다:

```bash
$ echo -n "asdf1234@" | md5sum

968ca7b33dc2f0f4fc86c032e0288149  -
```

여기서 `-n` 옵션은 `echo` 가 마지막에 개행 문자를 추가하지 않도록 하기 위한 것이다. 

만약 개행이나 공백이 추가되면 입력값 자체가 달라지기 때문에 결과 해시도 달라진다.

위에서 나온 해시:

```text
968ca7b33dc2f0f4fc86c032e0288149
```

를 사전 공격이나 후보 대입을 통해 크랙할 경우 원래 문자열인 `asdf1234@` 를 찾아낼 수 있다.

또한 `password`, `iloveyou` 처럼 자주 사용되는 문자열의 해시를 미리 계산해 놓고 탈취한 해시와 비교하는 방식이 존재하며, 대표적으로 Rainbow Table이 있다.

하지만 Rainbow Table은 주로 **Salt가 없는 빠른 해시**에 효과적이다. 

Salt가 적용된 비밀번호 해시는 같은 비밀번호라도 사용자마다 다른 결과가 생성될 수 있기 때문에 이러한 사전 계산 방식의 효과가 크게 감소한다.

# Introduction to John The Ripper and Hashcat

## John The Ripper

John The Ripper는 다양한 해시와 암호화된 파일을 대상으로 오프라인 Password Cracking을 수행할 수 있는 대표적인 도구이다.

John에서는 대표적으로 Single Crack Mode, Wordlist Mode, Incremental Mode 등을 사용할 수 있다.

### Single Crack Mode

`--single` 옵션은 계정명, 사용자 정보(`GECOS`), 홈 디렉토리 등의 데이터를 활용해 해당 사용자와 연관성이 높은 비밀번호 후보를 생성하는 방식이다.

예를 들어 다음과 같은 계정 정보가 있다고 가정한다:

```bash
r0lf:$6$ues25dIanlctrWxg$nZHVz2z4kCy1760Ee28M1xtHdGoy0C2cYzZ8l2sVa1kIa8K9gAcdBP.GI6ng/qA4oaMrgElZ1Cb9OeXO4Fvy3/:0:0:Rolf Sebastian:/home/r0lf:/bin/bash
```

이 상태에서 Single Mode를 사용하면 `Rolf Sebastian`, `r0lf` 등 계정 정보와 연관된 문자열을 변형하여 후보를 생성한다:

```bash
$ john --single passwd                                               

NAITSABES        (r0lf)
```

이처럼 `NAITSABES` 비밀번호를 찾아낸 것을 확인할 수 있다.

즉, `--single` 은 단순 무작위 브루트포싱이라기보다는 사용자 정보에 기반한 맞춤형 후보 생성 공격이라고 이해하면 된다.

### Wordlist, Incremental, and Format Selection

Wordlist Mode는 준비된 사전 파일의 각 문자열을 비밀번호 후보로 사용한다.

Incremental Mode는 John의 문자 빈도와 통계적 패턴 정보를 기반으로 후보를 생성하며, 사람이 실제 비밀번호로 사용할 가능성이 높은 조합을 우선적으로 시도하는 방식이다.

또한 해시값만 봐서는 정확한 형식을 식별하기 어려운 경우가 있다.

예를 들어 다음과 같은 32자리 16진수 해시가 있다고 가정한다:

```text
193069ceb0461e1d40d216e32c79c704
```

이런 형태는 MD5, NTLM, RIPEMD-128 등 여러 포맷과 길이가 겹칠 수 있으므로 해시 문자열만 보고 정확한 알고리즘을 단정하기 어렵다.

따라서 해시 유형을 알고 있다면 `--format` 옵션으로 명시하여 크랙할 수 있다:

```bash
$ john --format=ripemd-128 --wordlist=/usr/share/wordlists/rockyou.txt passwd  

50cent           (?)
```

또한 Excel, KeePass, SSH Private Key처럼 암호로 보호된 파일도 `office2john`, `keepass2john`, `ssh2john` 등의 변환 도구를 이용하여 John이 처리할 수 있는 형식으로 추출한 뒤 크랙할 수 있다.

## Hashcat

Hashcat 역시 대표적인 GPU 기반 Password Cracking 도구이다.

Hashcat에서 `-m` 은 Hash Mode, `-a` 는 Attack Mode를 지정한다.

### Dictionary Attack

`-a 0` 은 Straight Mode, 즉 일반적인 사전 공격이다. (기본 Attack Mode이기 때문에 상황에 따라 생략할 수도 있다.)

예를 들어 다음 MD5 해시를 크랙한다고 가정해보자:

```text
e3e3ec5831ad5e7288241960e5d4fdb8
```

`-m 0` 은 MD5를 의미한다:

```bash
$ hashcat 'e3e3ec5831ad5e7288241960e5d4fdb8' /usr/share/wordlists/rockyou.txt -m 0 --show

e3e3ec5831ad5e7288241960e5d4fdb8:crazy!
```

이처럼 원래 비밀번호인 `crazy!` 를 확인할 수 있다.

### Mask Attack

`-a 3` 은 Mask Attack이다.

비밀번호의 길이 또는 각 위치에 들어갈 문자 종류를 어느 정도 알고 있을 때 후보 공간을 제한하여 효율적으로 크랙할 수 있다.

Hashcat에서 사용하는 대표적인 Mask Charset은 다음과 같다:

| Mask | 의미                    |
| ---- | --------------------- |
| `?u` | 대문자 `A-Z`             |
| `?l` | 소문자 `a-z`             |
| `?d` | 숫자 `0-9`              |
| `?s` | 특수문자                  |
| `?a` | 소문자 + 대문자 + 숫자 + 특수문자 |
| `?h` | 소문자 Hex `0-9a-f`      |
| `?H` | 대문자 Hex `0-9A-F`      |
| `?b` | 모든 Byte `0x00-0xff`   |

이는 **각 문자 위치에 허용할 문자 집합을 지정하는 Mask 문법**이다.

예를 들어 `crazy!` 는 소문자 5자리와 특수문자 1자리로 구성되어 있으므로 다음과 같이 표현할 수 있다:

```bash
$ hashcat -a 3 -m 0 e3e3ec5831ad5e7288241960e5d4fdb8 '?l?l?l?l?l?s' --show

e3e3ec5831ad5e7288241960e5d4fdb8:crazy!
```

### Rule-Based Attack

만약 `rockyou.txt` 에 정확한 비밀번호가 존재하지 않더라도, 기본 단어를 사람이 자주 사용하는 형태로 변형하면 정답 후보를 만들 수 있다.

예를 들어 `c0wb0ys1` 의 MD5 해시는 다음과 같다:

```text
1b0556a75770563578569ae21392630c
```

Hashcat Rule 파일은 일반적으로 `/usr/share/hashcat/rules` 경로에 존재한다:

```bash
$ ls /usr/share/hashcat/rules   

best64.rule                  T0XlC_3_rule.rule
combinator.rule              T0XlC-insert_00-99_1950-2050_toprules_0_F.rule
d3ad0ne.rule                 T0XlC_insert_HTML_entities_0_Z.rule
dive.rule                    T0XlC-insert_space_and_special_0_F.rule
generated2.rule              T0XlC-insert_top_100_passwords_1_G.rule
generated.rule               T0XlC.rule
hybrid                       T0XlCv2.rule
Incisive-leetspeak.rule      toggles1.rule
InsidePro-HashManager.rule   toggles2.rule
InsidePro-PasswordsPro.rule  toggles3.rule
leetspeak.rule               toggles4.rule
oscommerce.rule              toggles5.rule
rockyou-30000.rule           unix-ninja-leetspeak.rule
specific.rule
```

Rule은 원본 후보를 그대로 사용하는 것이 아니라 대소문자 변경, 숫자/특수문자 추가, 문자 치환 등의 변형을 적용한다.

예를 들어 `password` 라는 단어를 기준으로 `Password1`, `p@ssword`, `password!` 와 같은 추가 후보를 생성할 수 있다.

다음과 같이 `best64.rule` 을 적용할 수 있다:

```bash
$ hashcat -m 0 1b0556a75770563578569ae21392630c /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule --show

1b0556a75770563578569ae21392630c:c0wb0ys1
```

# Writing Custom Wordlists and Rules

Hashcat에서는 직접 Rule 파일을 작성하여 워드리스트의 각 후보를 원하는 방식으로 변형할 수 있다.

## Custom Rule Syntax

대표적인 Rule 문법은 다음과 같다:

| Rule  | 뜻                 | `password`에 적용          |
| ----- | ----------------- | ----------------------- |
| `:`   | 그대로               | `password`              |
| `l`   | 전부 소문자            | `password`              |
| `u`   | 전부 대문자            | `PASSWORD`              |
| `c`   | 첫 글자만 대문자         | `Password`              |
| `C`   | 첫 글자 소문자, 나머지 대문자 | `pASSWORD`              |
| `r`   | 뒤집기               | `drowssap`              |
| `$X`  | 뒤에 X 붙이기          | `$!` → `password!`      |
| `^X`  | 앞에 X 붙이기          | `^!` → `!password`      |
| `sXY` | X를 Y로 치환          | `sa@` → `p@ssword`      |
| `iNX` | N번째 위치에 X 삽입      | `i0!` → `!password`     |
| `oNX` | N번째 문자를 X로 덮어씀    | `o0P` → `Password`      |
| `DN`  | N번째 문자 삭제         | `D0` → `assword`        |
| `t`   | 전체 대소문자 반전        | `PassWord` → `pASSwORD` |
| `TN`  | N번째 문자만 대소문자 반전   | `T0` → 첫 문자 반전       |

예를 들어 `rockyou.txt` 안에 `password` 가 존재한다고 가정하고 다음과 같은 Rule을 작성할 수 있다:

```text
:
c
sa@
so0
c sa@
c so0
c sa@ so0
$!
c $!
c sa@ so0 $!
```

이 Rule들을 `password` 에 적용하면 다음과 같은 후보들이 생성된다:

```text
password
Password
p@ssword
passw0rd
P@ssword
...
password!
Password!
```

Hashcat은 한 Wordlist 항목에 Rule들을 모두 적용한 후 다음 Wordlist 항목으로 넘어간다.

따라서 다음 후보가 `asdf1234` 라면 같은 Rule 세트가 다시 적용된다:

```text
asdf1234
Asdf1234
@sdf1234
asdf1234
...
```

일부 Rule은 동일한 결과를 만들 수도 있다.

실제로 생성되는 후보를 확인하면서 중복을 제거하고 싶다면 다음과 같이 `--stdout` 과 `sort -u` 를 조합할 수 있다:

```bash
$ ... --stdout | sort -u
```

## Targeted Wordlist Generation

정보 수집 단계에서 한 직원에 대해 다음과 같은 정보를 확보했다고 가정한다:

- 이름: Mark White
- 생년월일: August 5, 1998
- 근무처: Nexura, Ltd.
- 비밀번호 정책: 최소 12자이며 대문자, 소문자, 숫자, 특수문자를 각각 하나 이상 포함
- 거주지: San Francisco, CA, USA
- 반려묘 이름: Bella
- 배우자 이름: Maria
- 자녀 이름: Alex
- 관심사: Baseball

또한 다음 MD5 해시가 제공되었다:

```text
97268a8ae45ac7d15c3cea4ce6ea550b
```

이 정보를 토대로 우선 관련 문자열들을 `mark.txt` 에 정리하였다:

```text
markwhite
mark.white
mwhite
m.white

# SKIP

baseball
markbaseball
baseballmark
sanfrancisco
san.francisco
francisco
markwhitebella
markwhitemaria
markwhitealex
markwhitebaseball
markwhitenexura
bellabaseball
nexurabaseball
```

사용자는 이름, 생년, 회사명, 가족 이름, 취미 등의 개인정보를 조합하고 첫 글자를 대문자로 바꾸거나 숫자와 특수문자를 뒤에 붙이는 예측 가능한 패턴을 사용할 수 있다.

따라서 OSINT에서 얻은 정보와 비밀번호 정책을 기반으로 Rule을 작성하면 후보 공간을 훨씬 줄일 수 있다.

다음과 같은 Rule을 만들었다:

```text
csmMswW$1$9$9$8$!
csmMswW$1$9$9$8$?
csmMswW$0$8$0$5$!
csmMswW$0$8$0$5$?
csmMswW$1$9$9$8$8$5$!
csmMswW$1$9$9$8$8$5$?
csmMswW$0$8$0$5$9$8$!
csmMswW$0$8$0$5$1$9$9$8$!
csmMswW$8$0$5$9$8$!
csmMswW$0$8$0$5$1$9$9$8$?
csmMswW$0$8$0$5$1$9$9$8$@
csmMswW$0$8$0$5$9$8$?
csmMswW$0$8$0$5$9$8$@
```

여기서 `c` 는 첫 글자를 대문자로 바꾸고, `smM`, `swW`는 각각 `m → M`, `w → W` 로 치환하며, 뒤쪽의 `$1`, `$9`, `$!` 등은 연도나 특수문자를 순서대로 추가한다.

따라서 `baseball` 에 첫 번째 Rule이 적용되면 `Baseball1998!` 와 같은 후보가 생성될 수 있다.

이를 토대로 Hashcat을 실행한 결과 다음과 같이 비밀번호를 확인할 수 있었다:

```bash
$ hashcat -m 0 97268a8ae45ac7d15c3cea4ce6ea550b markh.txt -r mark.rule --show

97268a8ae45ac7d15c3cea4ce6ea550b:Baseball1998!
```

# Cracking Protected Files

John The Ripper는 일반적인 해시뿐 아니라 Office 문서, KeePass 데이터베이스, SSH Private Key처럼 암호로 보호된 파일도 크랙할 수 있다.

## Cracking an Encrypted Office File

```bash
$ file Confidential.xlsx

Confidential.xlsx: CDFV2 Encrypted
```

먼저 `office2john` 을 사용하여 John이 처리할 수 있는 cracking material을 추출한다:

```bash
$ office2john Confidential.xlsx > confidential.hash
```

추출된 내용은 다음과 같다:

```bash
$ cat confidential.hash

Confidential.xlsx:$office$*2013*100000*256*16*cb0e251cdec92e97eeb38e595cd4eb09*58758c88f3bb25e43e1e21adbd4b6e50*0057c1ae71b0023424ba705607dc0df1d9a786974bb957a821cfd7e39129eb15
```

이후 Wordlist Attack을 수행한다:

```bash
$ john --wordlist=/usr/share/wordlists/rockyou.txt confidential.hash

beethoven        (Confidential.xlsx) 
```

그 결과 `Confidential.xlsx` 의 비밀번호가 `beethoven` 임을 확인할 수 있었다.

# Network Service Attacks

오프라인 해시 크래킹과 달리 SSH, RDP, SMB와 같은 네트워크 서비스는 실제 인증 요청을 보내면서 자격 증명을 검증할 수도 있다.

## Hydra

Hydra는 다양한 네트워크 프로토콜에 대해 사용자명과 비밀번호 목록을 조합하여 로그인 시도를 수행할 수 있다.

SSH를 대상으로 다음과 같이 사용할 수 있다:

```bash
$ hydra -L username.list -P password.list ssh://10.129.202.136

[DATA] max 16 tasks per 1 server, overall 16 tasks, 21112 login tries (l:104/p:203), ~1320 tries per task
[DATA] attacking ssh://10.129.202.136:22/
[22][ssh] host: 10.129.202.136   login: dennis   password: rockstar
```

이처럼 `dennis:rockstar` 자격 증명을 찾은 것을 확인할 수 있다.

## NXC

SMB, WinRM, RDP 등의 Windows 프로토콜은 NXC를 이용하여 자격 증명을 검증할 수도 있다.

예를 들어 RDP를 대상으로 다음과 같이 사용자명과 비밀번호 목록을 사용할 수 있다:

```bash
$ nxc rdp 10.129.202.136 -u username.list -p password.list    
RDP         10.129.202.136  3389   WINSRV           [*] Windows 10 or Windows Server 2016 Build 17763 (name:WINSRV) (domain:WINSRV) (nla:False)

RDP         10.129.202.136  3389   WINSRV           [+] WINSRV\chris:789456123 (Pwn3d!)
```

이처럼 `chris:789456123` 자격 증명이 유효함을 확인할 수 있다.

# Spraying, Stuffing, and Defaults

## Password Spraying and Credential Stuffing

실제 환경에서는 제품이나 서비스가 설치될 때 기본 자격 증명이 그대로 유지되는 경우가 있다.

대표적으로 `root:root`, `admin:admin`, 빈 비밀번호 등의 조합이 존재할 수 있다.

## Default Credentials

`defaultcreds-cheat-sheet` 의 `creds` 명령을 사용하면 제품명 기준으로 알려진 기본 자격 증명을 검색할 수 있다.

예를 들어 MySQL 관련 기본 자격 증명을 검색하면 다음과 같다:

```bash
$ creds search mysql  

+---------------------+-------------------+----------+
| Product             |      username     | password |
+---------------------+-------------------+----------+
| mysql (ssh)         |        root       |   root   |
| mysql               | admin@example.com |  admin   |
| mysql               |        root       | <blank>  |
| mysql               |      superdba     |  admin   |
| scrutinizer (mysql) |    scrutremote    |  admin   |
+---------------------+-------------------+----------+
```

이처럼 Default Credentials 데이터베이스는 제품별로 공개적으로 알려진 초기 계정과 비밀번호 조합을 빠르게 확인하는 데 사용할 수 있다.
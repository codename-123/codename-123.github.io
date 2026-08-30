---
title: "Password Attacks - Password Cracking Techniques"
date: 2026-08-13
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

# Introduction to Password Cracking

우선 패스워드 크랙을 할때 필수인 해시가 있따. 

이 해시는 개행또는 띄어쓰기마다 해시가 뒤바뀌지만, 같은 문자열의 해시는 같은 해시가 된다.

따라서 비밀번호를 해쉬로 쳐내놓는다해도 그 해당 비밀번호가 쉽게 작성된경우 레인보우 테이블 공격을 통하여 해시가 탈취당할수있다.

이처럼 asdf1234@ 라는 문자열을 md5sum을 했다고 가정하면:

```bash
$ echo -n "asdf1234@" | md5sum

968ca7b33dc2f0f4fc86c032e0288149  -
```

나온 해시 `968ca7b33dc2f0f4fc86c032e0288149` 를 크랙하게 되면 문자열 `asdf1234@` 가ㅏ 나온다.

따라서 이를 활용하여 각 문자열들인 `password`, `iloveyou` 같은 문자열의 md5를 시켜놓은것들에 대한 모음집들을 해시랑 대입하여 레인보우 테이블 공격이 가능해진다.

# Introduction to John The Ripper and Hashcat

## John The Ripper

해시를 크랙하는데의 대표적인 툴인 John The Ripper가 존재한다.

john 공격에는 --singie 옵션의 자격증명 맞춤형 공격, 또는 사전 공격으로 공격이 가능하다.

이처럼 내부에 이런 자격증명이 있다고 가정한다:

```bash
r0lf:$6$ues25dIanlctrWxg$nZHVz2z4kCy1760Ee28M1xtHdGoy0C2cYzZ8l2sVa1kIa8K9gAcdBP.GI6ng/qA4oaMrgElZ1Cb9OeXO4Fvy3/:0:0:Rolf Sebastian:/home/r0lf:/bin/bash
```

이 상태에서 싱글 옵션을 주게되면 `Rolf Sebastian` 이름과 관련해서 지 좆대로 브루트포싱을 하게된다.

```bash
$ john --single passwd                                               

NAITSABES        (r0lf)
```

이처럼 보게되면 NAITSABES 비번이 튀어나온것을 확인할수있다.

또한 wordlist는 사전공격이며, incremental도 존재한다.

incremental은 학습된 문자 빈도나 패턴을 활용해서 사람이 실제 비밀번호로 쓸 가능성이 상대적으로 높은 조합을 우선 시도하는 방식이라고 이해하면 된다.

만약 이런 해시가 있다고 가정하자:

```text
193069ceb0461e1d40d216e32c79c704
```

이 해시는 md5인지, ntlm인지 RIPEMD-128인지 구분이 안갈때가 있따.

따라서 포맷 형식을 지정한뒤에 크랙을 하는 방식도 존재하게된다:

```bash
$ john --format=ripemd-128 --wordlist=/usr/share/wordlists/rockyou.txt passwd  

50cent           (?)
```

또한 다양하게 엑셀 파일이든, 어떠한 파일이든 그 파일에 비밀번호가 적용되어있으면, `keepass2john` 같은 도구를 활용하여 브루트포싱이 된다.

## Hashcat

또한 해시캣도 존재한다.

해시캣은 옵션인 -a 0과 -a 3이 존재한다.

-a 0은 기본적인 사전공격이며, 옵션을 안적어도 따로 적용이 된다.

예를들어 아래 문자열을 크랙한다고 가정해보자:

```text
e3e3ec5831ad5e7288241960e5d4fdb8
```

이 해시를 -m 을 지정하여 크랙할수있따:

```bash
$ hashcat 'e3e3ec5831ad5e7288241960e5d4fdb8' /usr/share/wordlists/rockyou.txt -m 0 --show

e3e3ec5831ad5e7288241960e5d4fdb8:crazy!
```

여기서 -m 0은 md5를 의미한다.

또한 -a 3이 존재한다.

-a 3은 만약 비번이 몇글자이고 각 대문자와 소문자, 특수문자, 숫자를 알게되면 정규표현식처럼 지정할수있게된다.

정규표현식은 각 이러하다:

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

이처럼 만약 위처럼 크랙에 crazy!를 정규표현식으로 표현하면 이렇게된다:

```bash
$ hashcat -a 3 -m 0 e3e3ec5831ad5e7288241960e5d4fdb8 '?l?l?l?l?l?s' --show

e3e3ec5831ad5e7288241960e5d4fdb8:crazy!
```

이처럼 정규표현식을 이용하여 탈취하는 방법이 존재한다.

그리고 만약 rockyou.txt 파일에 존재하지않는 c0wb0ys1 를 크랙한다고 가정해보자.

위 c0wb0ys1 문자열의 해쉬는 이러하다:

```text
1b0556a75770563578569ae21392630c
```

이 해시를 가지고 role을 적용할수있다.

role 대부분은 `/usr/share/hashcat/rules` 경로에 존재하게된다:

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

이 rule들은 원래는 password 지만 `Password1`, `Password01!` 와같은 후보가 추가로 만들어질 수 있는 식이다.

이를 토대로 best64.rule 을 적용시킨 rockyou.txt 파일을 이용하여 크랙을 시도하게되면 이처럼 나타나게된다:

```bash
$ hashcat -m 0 1b0556a75770563578569ae21392630c /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule --show

1b0556a75770563578569ae21392630c:c0wb0ys1
```

# Writing Custom Wordlists and Rules

또한 해시캣에서 내가 직접 룰을 지정할수있다.

이 해시캣의 룰에서 정규표현식은 이러하다:

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
| `TN`  | N번째 문자만 대소문자 반전   | `T0` → 첫 문자 toggle      |

만약 rockyou.txt 파일에 password 문자열이 존재한다고 치고 role에 내가 이런식으로 적용한 상태라고 가정한다:

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

이렇게 되면 password 문자열들이 각각 이런식으로 변하면서 대입되게된다.

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

이런 경우 거친뒤에야 다음 문자열 (EX:asdf1234) 을 또 기준으로 시작하게된다:

```text
asdf1234
Asdf1234
@sdf1234
asdf1234
...
```

이중 1번째와 4번째는 중복이기에 아래를 입력하여 중복을 줄일수잇따:

```bash
$ ... --stdout | sort -u
```

또한 정보수집 단계에서 이런 한명의 직원과 회사의 정책을 발견했다고 가정한다:

- 그의 이름은 Mark White 이다.
- 그는 ~에 태어났다August 5, 1998
- 그는 ~에서 일합니다Nexura, Ltd.
 - 회사 비밀번호 정책에 따르면 비밀번호는 최소 12자 이상이어야 하며, 대문자, 소문자, 기호, 숫자를 각각 하나 이상 포함해야 합니다.
- 그는 ~에 살고 있습니다San Francisco, CA, USA
- 그는 고양이 한 마리를 기르고 있는데, 고양이 이름은…Bella
- 그에게는 아내가 있습니다.Maria
- 그에게는 아들이 있다.Alex
- 그는 열렬한 팬이다baseball

또한 그의 해시가 제공되었다:

```text
97268a8ae45ac7d15c3cea4ce6ea550b
```

이를 토대로 우선 문자열들을 mark.txt 파일로 만들었다:

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

대부분 사람들은 첫 문자를 대문자로 지정한후, 소문자와 각종 숫자를 섞어 마지막에 특수문자를 사용하는 경향이 존재한다.

따라서 각종 조합한 문자열들을 기준으로 이처럼 rule을 지정하였다:

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

이처럼 주인공의 성과 부인의 성을 대문자로 변경시키며, 주인공의 이름또한 대문자로 변경시킴을 토대로 룰을 지정하였다.

이를 토대로 hashcat을 돌린결과 Baseball1998! 이 나옴을 확인할수있었다:

```bash
$ hashcat -m 0 97268a8ae45ac7d15c3cea4ce6ea550b markh.txt -r mark.rule --show

97268a8ae45ac7d15c3cea4ce6ea550b:Baseball1998!
```

# Cracking Protected Files

또한 엑셀이나 ssh 키와 같은 파일들을 john 툴을 활용하여 크랙할수있다.

우선 xlsx 파일을 기반으로 해보겠다.

이 xlsx 파일은 현재 암호화 된 상태이다:

```bash
$ file Confidential.xlsx

Confidential.xlsx: CDFV2 Encrypted
```

따라서 john을 활용하여 사전 기반 공격을 토대로 이 파일의 비밀번호를 가져올수잇다.

이처럼 일단 hash 형태로 바꿔놓았다:

```bash
$ office2john Confidential.xlsx > confidential.hash
```

이처럼 현재 hash는 sha256 버전의 해시임을 확인할수있다:

```bash
$ cat confidential.hash

Confidential.xlsx:$office$*2013*100000*256*16*cb0e251cdec92e97eeb38e595cd4eb09*58758c88f3bb25e43e1e21adbd4b6e50*0057c1ae71b0023424ba705607dc0df1d9a786974bb957a821cfd7e39129eb15
```

따라서 이를 토대로 john을 이용하여 사전기반 공격으로 해시 크랙을 시도하였다:

```bash
$ john --wordlist=/usr/share/wordlists/rockyou.txt confidential.hash

beethoven        (Confidential.xlsx) 
```

그 결과 이처럼 해시를 크랙하는데 성공하였다.

# Network service (hydra)

또한 네트워크 서비스들인 ssh, rdp, smb 와 같은 브루트포싱을 hydra 도구를 이용하여 할수잇따.

ssh는 이러하다:

```bash
$ hydra -L username.list -P password.list ssh://10.129.202.136

[DATA] max 16 tasks per 1 server, overall 16 tasks, 21112 login tries (l:104/p:203), ~1320 tries per task
[DATA] attacking ssh://10.129.202.136:22/
[22][ssh] host: 10.129.202.136   login: dennis   password: rockstar
```

이처럼 ssh 서비스의 사용자를 크랙할수있따.

또한 rdp와 smb도 마찬가지이다.

물론 저런 방식도 존재하지만 nxc를 활용하여 크랙할수있다.

rdp를 예제로 이런식으로 크랙에 성공하였다:

```bash
$ nxc rdp 10.129.202.136 -u username.list -p password.list    
RDP         10.129.202.136  3389   WINSRV           [*] Windows 10 or Windows Server 2016 Build 17763 (name:WINSRV) (domain:WINSRV) (nla:False)

RDP         10.129.202.136  3389   WINSRV           [+] WINSRV\chris:789456123 (Pwn3d!)
```

# Spraying, Stuffing, and Defaults

맨 처음에 설정되는 서비스들이 존재할수있다.

예를들면 초기 비번 지정은 root, root 일 경우도 있고. admin, admin 으로 초기지정된 상태가 존재할수있다.

mysql 기준이라면 이 cred 도구를 통하여 맨 초기 자격증명이 어떻게 되어있는지 확인할수잇따:

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

이처럼 defaultcreds-cheat-sheet는 이런 알려진 기본값들을 제품명 기준으로 찾아준다.
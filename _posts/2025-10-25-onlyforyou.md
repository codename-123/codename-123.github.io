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

위 소스코드는 메인 페이지에서 이메일, 제목, 메시지 를 받아, `form.py` 의 `sendmessage()` 함수를 통해 메일을 전송하는 구조이다.

이후 `sendmessage()` 함수 로직을 알아내기 위하여 `/var/www/only4you.htb/form.py` 경로로 이동한 후 소스코드를 분석하였다.

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



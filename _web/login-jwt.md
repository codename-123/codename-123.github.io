---
title: "식별/인증 로그인 구현 & JWT"
date: 2025-05-13
layout: single
toc: true
toc_label: "Login & JWT"
toc_icon: "book"
toc_sticky: true
tags: [web, login, jwt]
header:
  teaser: /assets/images/lock-icon.png
---

# 개요

로그인을 구현하기 위해서는 먼저 사용자를 구별하는 식별(Identification) 과, 그 사용자가 본인임을 증명하는 인 (Authentication) 개념에 대한 정리를 하였습니다.

PHP를 기반으로 총 4가지 방식의 로그인 로직을 구현하였습니다:
    - 식별과 인증을 동시에 처리하는 방식 (해시 미포함)
    - 식별 후 → 인증을 분리하여 처리하는 방식 (해시 미포함)
    - 식별과 인증을 동시에 처리하는 방식 (해시 포함)
    - 식별 후 → 인증을 분리하여 처리하는 방식 (해시 포함)

또한, 로그인 후 사용자 상태를 유지하기 위한 방법으로 사용되는 JWT(JSON Web Token) 의 구조도 함께 정리하였습니다.

---

# 실습 내용 정리

## 식별(Identification) 과 인증(Authentication)

식별(Identification)이란?
- 많은 사용자 중에서, 특정 사용자를 **"지목"**하는 과정.
    예: `아이디`, `닉네임`, `전화번호`, `주민등록번호` 등
    - **ID는 중복되면 안 됨 (Primary Key)** → 유일성 보장
> EX) 전체 학생 1000명 중, **전화번호가 `010-XXXX-XXXX`인 사람을 식별**하는 것.

인증(Authentication)이란? 
- 식별된 사용자가 **"본인"**임을 증명하는 과정.
    예: `비밀번호`, `OTP`, `지문`, `인증서`
> EX) 전화번호가 `010-XXXX-XXXX`인 사람에게 OTP를 전송하고, **그 OTP를 정확히 입력해 본인임을 증명**하는 것.(인증)

---

## 식별과 인증을 통한 로그인 구현

### 식별 + 인증을 동시에 처리하는 로그인 (해시 미포함)

```php
$id = $_POST['id'];
$password = $_POST['password'];

$sql = "SELECT * FROM users WHERE id = '$id' AND password = '$password'";
$result = $db->query($sql);
$user = $result->fetch();

if ($user) {
    echo "로그인 성공";
} else {
    echo "아이디 또는 비밀번호가 잘못되었습니다.";
}
```

- **위 로그인 구현 방식은 사용자 입력값을 그대로 쿼리에 삽입하기 때문에, 심각한 SQL Injection 취약점이 존재함.**

---

### 식별 후 → 인증 처리 (해시 미포함)

```php
$username = $_POST['id'];
$password = $_POST['password'];

$sql = "SELECT password FROM users WHERE id = '$id'";
$result = $db->query($sql);
$user = $result->fetch();

if ($user && $password == $user['password']) {
    echo "로그인 성공";
} else {
    echo "아이디 또는 비밀번호가 잘못되었습니다.";
}
```

- **식별과 인증을 분리하여 구현했지만, SQL Injection과 비밀번호 평문 비교 문제로 인해 여전히 보안상 안전하지 않은 방식임.**

### 식별 + 인증을 동시에 처리하는 로그인 (해시 포함)

```php
$id = $_POST['id'];
$password = $_POST['password'];

$sql = "SELECT * FROM users WHERE id = '$id'";
$result = $db->query($sql);
$user = $result->fetch();

// 해시된 비밀번호 비교
if ($user && password_verify($password, $user['password'])) {
    echo "로그인 성공";
} else {
    echo "아이디 또는 비밀번호가 잘못되었습니다.";
}
```

- **`password_verify()`는 안전하게 비밀번호를 비교해 줌, 하지만 여전히 $username이 SQL 쿼리에 직접 삽입되어 있어 SQL Injection에 매우 취약함.**

---

### 식별 후 → 인증 처리 (해시 포함)

```php
$id = $_POST['id'];
$password = $_POST['password'];

$sql = "SELECT password FROM users WHERE id = '$id'";
$result = $db->query($sql);
$user = $result->fetch();

if (!$user) {
    echo "존재하지 않는 사용자입니다.";
    exit;
}

if (password_verify($password, $user['password'])) {
    echo "로그인 성공";
} else {
    echo "비밀번호가 일치하지 않습니다.";
}
```

- **식별과 인증을 분리하고 비밀번호 검증에 `password_verify()`를 사용한 방식이지만, 여전히 사용자 입력값을 직접 SQL에 삽입하고 있어 SQL Injection 취약점이 존재함.**

---

### 식별 → 인증 분리 + 해시 검증 + SQL Injection 방어 로그인 로직

```php
$id = $_POST['id'];
$password = $_POST['password'];

// Named Placeholder를 사용한 Prepared Statement
$sql = "SELECT password FROM users WHERE id = :id";
$stmt = $db->prepare($sql);
$stmt->bindParam(':id', $id);
$stmt->execute();
$user = $stmt->fetch();

if (!$user) {
    echo "<script>
    alert('존재하지 않는 사용자입니다.')
    history.go(-1)
    </script>";
}

if (password_verify($password, $user['password'])) {
    echo "로그인 성공";
} else {
    echo "비밀번호가 일치하지 않습니다.";
}
```

- **이 로그인 로직은 Named Placeholder(`:id`)를 사용한 Prepared Statement를 통해 SQL Injection을 방어하며, 식별과 인증을 명확히 분리하여 구현한 안전한 방식. 비밀번호는 `password_verify()`를 통해 해시 기반으로 검증됨.**

따라서 대부분의 SQL 쿼리를 작성할 때는, **Prepared Statement를 사용하는 방식**이 가장 안전한 방법입니다.

---

## JWT 개요

JWT(JSON Web Token)는 로그인 인증 정보를 암호화된 **토큰**의 형태로 클라이언트에 전달하고 저장하는 방식이다. 서버는 세션울 기억할 필요 없이, 클라이언트가 요청 시 제공하는 JWT를 검증하여 인증을 처리한다.

### JWT 구조

JWT는 총 3개의 파트로 구성된다. 이들은 `.`**(점)** 으로 연결되어 있으며, 각각 Base64로 인코딩된 문자열이다.

```php-template
<Header>.<Payload>.<Signature>
```

| 파트            | 설명                                              |
| ------------- | ----------------------------------------------- |
| **Header**    | 토큰 타입 (`JWT`)과 서명 알고리즘 (`HS256` 등) 정보           |
| **Payload**   | 사용자 정보(예: `user_id`) 및 토큰 만료 시간(`exp`) 등 실제 데이터 |
| **Signature** | 위의 내용을 바탕으로 비밀키를 사용해 생성한 서명 (변조 방지)             |

> **Signature**가 있기 때문에, 토큰이 위조되지 않았는지를 검증할 수 있습니다.

### JWT 동작 원리

1. 사용자가 로그인 정보를 입력하면, 서버는 이를 확인 후 JWT를 생성하여 클라이언트에게 전달한다.
2. 클라이언트는 이 토큰을 localStorage나 쿠키에 저장한다.
3. 이후 인증이 필요한 요청을 보낼 때, JWT를 `Authorization` 헤더에 포함시켜 서버에 전송한다.
4. 서버는 이 JWT를 복호화하고 서명을 검증하여 사용자의 인증 여부를 판단한다.

### JWT 구현

- 이제 JWT 기반 로그인 인증 로직을 PHP 코드로 구현한다. PHP에서는 보통 `firebase/php-jwt` 라이브러리를 사용함.

1. 설치

```bash
composer require firebase/php-jwt
```

2. 로그인 시 JWT 발급

```php
use Firebase\JWT\JWT;

$data = json_decode(file_get_contents("php://input"), true);
$id = $_data['id'];
$password = $_data['password'];

$sql = "SELECT id, name, password FROM users WHERE id = :id";
$stmt = $db->prepare($sql);
$stmt->bindParam(':id', $id);
$stmt->execute();
$user = $stmt->fetch();

if (!$user) {
    echo "<script>
    alert('존재하지 않는 사용자입니다.')
    history.go(-1)
    </script>";
}

if (password_verify($password, $user['password'])) {
    $payload = [
    "id" => $user['id'],
    "name" => $user['name'],
    "exp" => time() + 3600 // JWT는 영구적으로 유효하므로 토큰 유효기간을 제어 시켜야함.
    ];

    $jwt = JWT::encode($payload, $secretKey, 'HS256');

    $arr = ["message" => "로그인 성공", 
            "result" => "success", // 성공 여부 프론트엔드로 처리
            "token" => $jwt // 토큰 반환
            ];
    die(json_encode($arr));
} else {
    $arr = [
    "message" => "비밀번호가 일치하지 않습니다.",
    "result" => "fail"  // 실패 여부 프론트엔드로 처리
    ];
    die(json_encode($arr));
}
```

3. 프론트엔드에서 처리

```javascript
fetch("login.php", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"  
  },
  body: JSON.stringify({
    id: "test",
    password: "1234"
  })
})
.then(res => res.json())
.then(data => {
  if (data.result === "success") {
    localStorage.setItem("jwt_token", data.token);
    location.href = "./index.php";
  } else {
    alert(data.message);
  }
});
```

> 이렇게 JWT를 활용한 로그인 구현까지 직접 단계별로 구현해 보았다.


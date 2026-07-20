---
title: "XSS - XSS Basics"
date: 2026-07-04
layout: single
excerpt: "Stored, Reflected, DOM-based XSS의 동작 방식과 차이점을 실습을 통해 알아보고, 각 유형에서 JavaScript가 실행되는 과정을 정리한다."
author_profile: true
toc: true
toc_label: "XSS"
toc_icon: "book"
toc_sticky: true
categories: [cpts-web]
tags: [web, cpts, xss]
---

**Stored**, **Reflected**, **DOM-based XSS**의 동작 방식과 차이점을 실습을 통해 알아보고, 각 유형에서 JavaScript가 실행되는 과정을 정리한다.

# Stored XSS

**Stored XSS**는 공격자가 삽입한 스크립트가 서버에 저장되는 형태의 XSS다.

XSS 유형 중에서도 가장 위험한 편에 속하며, 다른 사용자가 해당 페이지에 접근하는 순간 저장된 스크립트가 실행된다:

내부 페이지에 접속하면 다음과 같은 입력란이 존재한다:

![XSS](/assets/cpts-web/xss-basics/xss1.png)

입력란에 `test` 와 `test2` 를 입력하니 다음과 같이 사용자 입력값이 페이지에 저장되는 것을 확인할 수 있었다:

![XSS](/assets/cpts-web/xss-basics/xss2.png)

페이지를 새로고침하거나 다시 접속한 이후에도 입력값이 유지되는 것으로 보아, 입력값이 서버에 저장된다는 사실을 알 수 있다.

또한 사용자 입력값이 별도의 필터링 없이 페이지에 출력되므로 XSS 취약점이 존재할 가능성이 있다.

따라서 다음 페이로드를 삽입하였다:

```html
<script>alert("test")</script>
```

그 결과 다음과 같이 `test` 라는 내용의 Alert 창이 출력되었다:

![XSS](/assets/cpts-web/xss-basics/xss3.png)

페이지를 새로고침하거나 다시 접속해도 서버에 저장된 스크립트가 다시 페이지에 출력되기 때문에 Alert 창이 반복해서 실행된다:

![XSS](/assets/cpts-web/xss-basics/xss4.png)

# Reflected XSS

**Reflected XSS**는 공격자가 XSS 페이로드가 포함된 URL을 피해자에게 전달하고, 피해자가 해당 URL에 접속했을 때 스크립트가 실행되는 형태의 XSS다.

Stored XSS와 달리 페이로드가 서버에 영구적으로 저장되지는 않지만, 피싱 링크나 세션 정보 탈취와 같은 공격에 활용될 수 있다.

앞에서 사용한 것과 유사한 웹페이지가 존재한다:

![XSS](/assets/cpts-web/xss-basics/xss1.png)

입력란에 값을 입력하면 URL에 `task` 파라미터가 생성되는 것을 확인할 수 있다:

![XSS](/assets/cpts-web/xss-basics/xss5.png)

`task` 파라미터에 다음 페이로드를 삽입하였다:

```html
<script>alert(document.cookie)</script>
```

`task` 파라미터에 삽입한 XSS 페이로드가 서버의 응답에 그대로 포함되면서 정상적으로 실행되는 것을 확인할 수 있다:

![XSS](/assets/cpts-web/xss-basics/xss6.png)

이처럼 공격자는 피해자의 쿠키나 세션 정보를 외부 서버로 전송하는 페이로드를 URL에 삽입할 수 있다.

이후 피해자가 해당 URL을 클릭하면, 피해자의 브라우저에서 악성 JavaScript 코드가 실행되는 방식이다.

# DOM-based XSS

**DOM-based XSS**는 사용자 입력값이 서버를 거치지 않고, 브라우저의 JavaScript 코드에 의해 직접 HTML 요소에 삽입되면서 발생하는 XSS다.

다음과 같은 JavaScript 코드가 존재한다고 가정해보자:

```js
$(function () {
    $("#add").click(function () {
        if ($("#task").val().length > 0) {
            window.location.href = "#task=" + $("#task").val();
            var pos = document.URL.indexOf("task=");
            var task = document.URL.substring(pos + 5, document.URL.length);
            document.getElementById("todo").innerHTML = "<b>Next Task:</b> " + decodeURIComponent(task);
        }
    });
});
var pos = document.URL.indexOf("task=");
var task = document.URL.substring(pos + 5, document.URL.length);
if (pos > 0) {
    document.getElementById("todo").innerHTML = "<b>Next Task:</b> " + decodeURIComponent(task);
}
```

페이지 로딩이 완료된 후 Add 버튼을 누르면 입력값이 비어 있는지 확인한다.

입력값이 존재하면 해당 값을 URL의 `#task=` 뒤에 추가한다:

```js
window.location.href = "#task=" + $("#task").val();
```

이후 JavaScript는 현재 URL에서 `task=` 문자열의 위치를 찾는다.:

```js
var pos = document.URL.indexOf("task=");
```

`task=` 뒤에 존재하는 값을 URL 끝까지 추출하여 `task` 변수에 저장한다:

```js
var task = document.URL.substring(pos + 5, document.URL.length);
```

마지막으로 추출한 값을 디코딩한 후 `todo` 요소의 innerHTML에 삽입한다:

```js
document.getElementById("todo").innerHTML =
    "<b>Next Task:</b> " + decodeURIComponent(task);
```

내부 웹페이지에 `test` 값을 입력해보자:

![XSS](/assets/cpts-web/xss-basics/xss7.png)

URL의 `#task=` 뒤에 test가 추가되며, JavaScript가 해당 값을 읽어 Next Task 영역에 출력하는 것을 확인할 수 있다.

URL의 `#` 뒤에 존재하는 Fragment 값은 일반적으로 HTTP 요청을 통해 서버로 전송되지 않는다.

따라서 이 과정은 서버에서 처리되는 것이 아니라 브라우저 내부의 JavaScript를 통해 처리된다.

하지만 앞에서 사용했던 다음과 같은 `<script>` 기반 페이로드는 실행되지 않을 수 있다:

```html
<script>alert("test")</script>
```

이는 innerHTML을 통해 동적으로 삽입된 `<script>` 태그가 일반적으로 브라우저에서 실행되지 않기 때문이다.

따라서 `<script>` 태그 대신 HTML 요소의 이벤트 핸들러를 활용할 수 있다.

다음 페이로드를 입력하였다:

```html
<img src="" onerror=alert("test")>
```

페이로드를 입력하고 Add 버튼을 누르면 다음과 같이 `test` 라는 내용의 Alert 창이 출력된다:

![XSS](/assets/cpts-web/xss-basics/xss8.png)
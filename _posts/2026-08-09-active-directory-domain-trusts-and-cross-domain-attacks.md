---
title: "Active Directory - Domain Trusts and Cross-Domain Attacks"
date: 2026-08-09
layout: single
excerpt: "Windows 환경에서 파일, 브라우저, 레지스트리, 저장된 세션, 백업, 클립보드 등을 통해 자격 증명을 수집하고, 사용자 상호작용 및 다양한 추가 기법을 활용해 권한 상승과 횡적 이동으로 이어지는 공격 흐름을 실습한다."
author_profile: true
toc: true
toc_label: "Active Directory"
toc_icon: "book"
toc_sticky: true
categories: [cpts-infra]
tags: [windows, cpts, priv-esc, credential-theft, pillaging, lateral-movement, registry, browser-credentials, scheduled-tasks]
---

# Why So Trusting?

## Domain Trusts Primer

큰 기업들은 시간이 지나면서 다른 회사를 인수하고, 그 회사를 기존 조직에 편입시키는 경우가 많음.

이때 새로 인수한 회사의 AD 객체들을 전부 기존 도메인으로 마이그레이션하지 않고도 서로 자원을 사용할 수 있게 만드는 방법 중 하나가 Domain Trust(도메인 신뢰 관계) 를 설정하는 것임.

도메인에선 각 신뢰관계의 도메인과 비신뢰관계 도메인이 존재한다.

이런경우가 존재한다.

```text
Domain A
   ↓ Trust
Domain B
   ↓ Trust
Domain C
```

이렇게 연쇄적으로 도메인 신뢰 관계가 형성되었다고 해보자.

저기에서 B가 C를 신뢰하고 A가 B를 신뢰하니 A가 C도 신뢰한다 라는 가정이 Transitive이다:

```text
A → B → C
```

하지만 여기서 B가 C를 신뢰하지만 A가 B를 신뢰해도 A가 C를 신뢰하지 않는 가정은 Non-Transitive이다:

```text
A ↔ B ↔ C

A ↛  C
```

그리고 trust에는 방향도 존재한다.

예를들어 이런식이라고 가정해보자:

```text
Trusted Domain
     │ user authentication
     ▼
Trusting Domain
```

이 경우는 Trusted Domain의 사용자 → Trusting Domain의 리소스 접근 가능이라고 가정한다.

따라서 연결된 사용자 A가 A를 신뢰하는 B 도메인에 접근이 가능하는 것을 One-way Trust라고 불리운다(반대는 안된다):

```text
A trusts B
```

위처럼 가정하면 `B 사용자 → A 리소스` 방향이다.

또한 양쪽 모두를 신뢰하는 Bidirectional Trust도 존재한다.

이를 통하여 내부에서 `Get-ADTrust` 를 통해 신뢰 관계를 열거할수있다:

```powershell
PS C:\Users\htb-student> Get-ADTrust -Filter *

Direction               : BiDirectional
DisallowTransivity      : False
DistinguishedName       : CN=LOGISTICS.INLANEFREIGHT.LOCAL,CN=System,DC=INLANEFREIGHT,DC=LOCAL
ForestTransitive        : False
IntraForest             : True
IsTreeParent            : False
IsTreeRoot              : False
Name                    : LOGISTICS.INLANEFREIGHT.LOCAL
ObjectClass             : trustedDomain
ObjectGUID              : f48a1169-2e58-42c1-ba32-a6ccb10057ec
SelectiveAuthentication : False
SIDFilteringForestAware : False
SIDFilteringQuarantined : False
Source                  : DC=INLANEFREIGHT,DC=LOCAL
Target                  : LOGISTICS.INLANEFREIGHT.LOCAL
TGTDelegation           : False
TrustAttributes         : 32
TrustedPolicy           :
TrustingPolicy          :
TrustType               : Uplevel
UplevelOnly             : False
UsesAESKeys             : False
UsesRC4Encryption       : False

Direction               : BiDirectional
DisallowTransivity      : False
DistinguishedName       : CN=FREIGHTLOGISTICS.LOCAL,CN=System,DC=INLANEFREIGHT,DC=LOCAL
ForestTransitive        : True
IntraForest             : False
IsTreeParent            : False
IsTreeRoot              : False
Name                    : FREIGHTLOGISTICS.LOCAL
ObjectClass             : trustedDomain
ObjectGUID              : 1597717f-89b7-49b8-9cd9-0801d52475ca
SelectiveAuthentication : False
SIDFilteringForestAware : False
SIDFilteringQuarantined : False
Source                  : DC=INLANEFREIGHT,DC=LOCAL
Target                  : FREIGHTLOGISTICS.LOCAL
TGTDelegation           : False
TrustAttributes         : 8
TrustedPolicy           :
TrustingPolicy          :
TrustType               : Uplevel
UplevelOnly             : False
UsesAESKeys             : False
UsesRC4Encryption       : False
```

위의 출력은 이 값을 보게되면 현재 LOGISTICS.INLANEFREIGHT.LOCAL 도메인은 인트라 포레스트 설정값이 True로 되어있다.

또한 현재 위치한 도메인은 INLANEFREIGHT.LOCAL이기에 LOGISTICS.INLANEFREIGHT.LOCAL는 자식 포레스트라고 볼수가 있다.

또한 이 설정을 보게되면:

```text
Direction : BiDirectional
```

`BiDirectional` 은 양방향 trust(Bidirectional Trust)임을 확인할수있다.

따라서 두 도메인간 지지고 볶고 다 할수있는 상태이다.

두번째 출력을 보게되면 현재 FREIGHTLOGISTICS.LOCAL 도메인은 인트라 포레스트 설정값이 False로 되어있다.

이 값은 같은 포레스트가 아닌 다른 포레스트를 의미하며, 하지만 ForestTransitive 설정값에 True로 찍혀있어 Forest 수준의 Transitive Trust임을 확인할수있다.

또한 위와 똑같이 설정이 되어있다:

```text
Direction : BiDirectional
```

이것도 양방향 trust(Bidirectional Trust)임을 확인할수있다.

또한 파워뷰의 매핑을 사용하여 확인할수있다:

```powershell
PS C:\Users\htb-student> Get-DomainTrustMapping

SourceName      : INLANEFREIGHT.LOCAL
TargetName      : LOGISTICS.INLANEFREIGHT.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : WITHIN_FOREST
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 6:20:22 PM
WhenChanged     : 2/26/2022 11:55:55 PM

SourceName      : INLANEFREIGHT.LOCAL
TargetName      : FREIGHTLOGISTICS.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : FOREST_TRANSITIVE
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 8:07:09 PM
WhenChanged     : 2/27/2022 12:02:39 AM

SourceName      : FREIGHTLOGISTICS.LOCAL
TargetName      : INLANEFREIGHT.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : FOREST_TRANSITIVE
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 8:07:08 PM
WhenChanged     : 2/27/2022 12:02:41 AM

SourceName      : LOGISTICS.INLANEFREIGHT.LOCAL
TargetName      : INLANEFREIGHT.LOCAL
TrustType       : WINDOWS_ACTIVE_DIRECTORY
TrustAttributes : WITHIN_FOREST
TrustDirection  : Bidirectional
WhenCreated     : 11/1/2021 6:20:22 PM
WhenChanged     : 2/26/2022 11:55:55 PM
```

## Attacking Domain Trusts - Child → Parent Trusts - from Windows

우선 이 환경에선 하위 도메인인 LOGISTICS.INLANEFREIGHT.LOCAL의 도메인 관리자 권한까지 먹혔다는 가정으로부터 시작한다.


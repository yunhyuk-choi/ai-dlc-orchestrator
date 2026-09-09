# ISSUE-TRACKER.md — {SYSTEM_NAME} 이슈 트래커 config (인스턴스)

> 이 시스템의 **트래커 좌표 단일 원천**(원칙 6). `ISSUE-TRACKER-AGENT`가 읽고 티켓을 생성·전이·갱신하며, 오케스트레이터는 사이클↔티켓 바인딩(책임 7)에 이 좌표를 쓴다.
> 규율 본문은 공유 리포(`ai-dlc-orchestrator`)의 `specs/ISSUE-TRACKER-ADAPTER.md`(**POLICY-ISSUE-TRACKING**) — 여기엔 *이 배포의 값*만 적는다 (룰 복제 금지).
> **시크릿 경계**: 토큰·키의 *값은 절대 적지 않는다* — `.env` 변수명 또는 토큰 파일 *경로*만 (자격증명 경계 / POLICY-TRACKING). 이 파일은 `dlc-meta`에 **커밋되는 공유 문서**다. 변경은 `dlc-meta` 커밋.

<!-- TEMPLATE-ONLY -->
**조건부 인스턴스 렌더 규칙**: SETTER S5.7에서 *트래커를 운영한다*(Q5.7.1 = 예)는 응답이 있을 때만 이 파일을 만든다. 트래커 없이 운영하는 시스템은 **파일 자체를 만들지 않는다**(빈 파일로 자리를 남기지 않는다 — 매 세션 노이즈). 생성 후 미충전 슬롯·저작 지시 잔존 금지 — 판정 규칙은 `specs/SYSTEM-WORKFLOW.md` §3.2.
<!-- /TEMPLATE-ONLY -->

---

## 1. 공통 항목 (모든 `tracker.type` 공통)

> 원천: ADAPTER §2.1. 아래 네 항목은 type과 무관하게 항상 채운다.

| 항목 | 값 |
|---|---|
| **`tracker.type`** | {TRACKER_TYPE} |
| **리포터/사용자 신원** (범위 안 사이클 티켓 배정 대상) | {TRACKER_REPORTER} |
| **트리아지 담당자** (범위 밖 요청 티켓 배정 대상) | {TRACKER_TRIAGE} |
| **토큰 저장 위치 (`tokenPath`)** | {TRACKER_TOKEN_PATH} |

---

## 2. `tracker.type` 별 좌표

> 필수 좌표 정의는 ADAPTER §2.2. 인증 방식은 `tracker.type`이 결정하므로 여기 적지 않는다(§1.2 — jira Basic `email:token` / gitlab `PRIVATE-TOKEN` / github Bearer).

{TRACKER_COORDINATES}

<!-- TEMPLATE-ONLY -->
**렌더 규칙 — §2**: **선택된 하나의 type 블록만 렌더한다** — 나머지 두 개는 통째로 뺀다 (쓰지 않는 좌표를 빈 자리로 남기면 다음 독자가 어느 것이 유효한지 알 수 없다).

> 렌더 형식(선택된 type 하나만):
>
> ```markdown
> ### jira
> - **`baseUrl`**: {예: https://…}
> - **API 버전**: {예: /rest/api/2}
> - **`projectKey`** (+ id): {예: ABC (10001)}
> - **`email`**: {예: Basic 인증에 쓰는 계정 email}
>
> ### gitlab
> - **`baseUrl`** (host): {예: https://…}
> - **`projectIdOrPath`**: {예: group/subgroup/project 또는 숫자 id}
> - **`defaultAssignee`**: {예: user id}
>
> ### github
> - **`owner`**: {예: 조직·계정}
> - **`repo`**: {예: 레포명}
> - **`defaultAssignee`**: {예: login}
> - **`milestone`** *(선택 — 기한 담을 곳. 미지정이면 기한은 본문 기록 + gap 명시)*: {예: milestone 이름·번호}
> ```
<!-- /TEMPLATE-ONLY -->

---

## 3. 상태 의미론 (To-Do / In-Progress / Done 동치)

> **플랫폼마다 상태 원천이 다르다** (ADAPTER §1.2.1). 실제 이름·라벨은 *하드코딩하지 않고* 여기서 읽는다.
> — **jira**: `statusNames` (로컬라이즈된 상태명. 전이 id는 §4 런타임 캐시)
> — **gitlab·github**: `statusLabels` (To-Do = 라벨 없음 / In-Progress = open + `inProgress` 라벨 / Done = closed [+ `done` 라벨])

{TRACKER_STATUS_SEMANTICS}

---

<!-- TEMPLATE-ONLY -->
**조건부 섹션 렌더 규칙 — 「§4 런타임 발견 메타 캐시」**: `tracker.type = jira` 일 때만 이 섹션을 넣는다. **gitlab·github은 이슈 스키마가 고정**이라 발견 단계 자체가 없으므로 이 섹션 전체(헤딩·안내·캐시 표 + 바로 위 구분선까지) 를 통째로 뺀다 (ADAPTER §6).
<!-- /TEMPLATE-ONLY -->

## 4. 런타임 발견 메타 캐시 — **Jira 한정** (SETTER가 채우지 않음)

> SETTER는 **빈 캐시 자리만** 만든다 — 발견값을 인터뷰하지 않는다. 채우는 주체는 `ISSUE-TRACKER-AGENT`(I1)이며, createmeta·워크플로우 API로 발견한 값을 여기 캐시해 재질의 비용을 줄인다. **추측으로 채우지 않는다** — 모르면 비워 두고 런타임이 발견한다.

| 메타 | 캐시 값 | 발견 시점 |
|---|---|---|
| 이슈타입 id | (미발견) | I1 |
| 필수 필드 집합 | (미발견) | I1 |
| 상태 전이 id (To-Do / In-Progress / Done) | (미발견) | I1 |
| 보드·스프린트 좌표 | (미발견) | I1 (해당 수단 보유 시) |
| 에픽·부모 맵 | (미발견) | I1 (해당 수단 보유 시) |

---

## 5. 참조 맵

| 문서 | 관계 |
|---|---|
| `ai-dlc-orchestrator/specs/ISSUE-TRACKER-ADAPTER.md` | 규율 본문(POLICY-ISSUE-TRACKING) — 본 인스턴스는 그 §2 계약의 *값* |
| `ai-dlc-orchestrator/agents/ISSUE-TRACKER-AGENT.md` | 본 config의 소비자(실행 주체) + §4 캐시의 기록 주체 |
| `ai-dlc-orchestrator/agents/SETTER.md` S5.7·S7.5 | 본 인스턴스의 포착·생성 주체 |
| `dlc-meta/ORCHESTRATOR.md` | 시스템 인스턴스 — 사이클↔티켓 바인딩(책임 7)의 운영 컨텍스트 |
| 메타 레포 루트의 `.env` (개인 — gitignore) | 위 `tokenPath`가 가리키는 **값**이 사는 곳 (여기엔 값 금지) |

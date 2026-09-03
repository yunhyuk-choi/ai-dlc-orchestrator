# ISSUE-TRACKER-ADAPTER.md — 이슈 트래커 규율 명세 (사이클↔티켓 바인딩 표준)

> **이 문서는 형식·룰 명세 문서.** 에이전트 룰북 아님.
> 본 명세는 작업 사이클을 *이슈 트래커 티켓* 에 바인딩하고, 범위 밖 작업을 *요청 티켓* 으로 발행하는 *조건부 규율* 을 정의한다.
> 본 명세는 **룰만** 정의한다 — 실행 주체는 `ISSUE-TRACKER-AGENT`(피어 에이전트, 별도)이며, 티켓 생성·전이·동기화의 *조율* 은 오케스트레이터가 인식한다(사이클↔티켓 바인딩). 본 문서는 *무엇을·어떤 경계로 티켓화하는지의 룰* 만 제공한다.
> 본 명세는 **조건부** 다 — 시스템이 *실제로 이슈 트래커를 운영할 때만* 발동하고(§1), 없으면 비활성(inert)이다.
> **트래커 중립·프로젝트 중립** — 트래커 종류·베이스 URL·프로젝트 키·인증·상태명은 모두 *예시(e.g.)* 이거나 *인스턴스 config에서 온다*. 본 공유 명세에는 특정 배포의 구체값을 박지 않는다. 본 명세는 **세 구체 플랫폼(jira / gitlab / github)** 을 어댑터로 지원하며(§1.2), 어느 것을 쓸지는 인스턴스가 `tracker.type` 으로 선택한다 — **어느 플랫폼도 요구사항이 아니다**(트래커 없이 운영하는 시스템도 정상).
> 변경은 깃 PR/머지 (원칙 8) — `agents/ISSUE-TRACKER-AGENT.md`(실행 주체) / `specs/CYCLE-LOG.md`(사이클 시작 로그) / `agents/CYCLE-CLOSER.md`(사이클 종료) / `agents/SETTER.md`(config 포착) / `agents/orchestrator/DECISIONS.md`(A-4·A-5) / `agents/orchestrator/ERROR-POLICY.md`(EX-13) 가 본 명세에 연계되므로 변경 시 영향 검토 필수.
> 위치: `ai-dlc-orchestrator/specs/ISSUE-TRACKER-ADAPTER.md`

> **POLICY-ISSUE-TRACKING (사이클↔티켓 바인딩)** — 시스템이 이슈 트래커를 운영할 때(조건부 발동), 오케스트레이터는 각 작업 사이클을 *하나의 티켓* 에 바인딩하고(**사이클 = 티켓**), 범위 밖 작업은 *요청 티켓* 으로 발행한다. **(A) 범위 밖 개발 아이템**은 트리아지 담당자(또는 명확한 소유자)에게 배정되는 *요청 티켓* — 오케스트레이터가 스스로 진행 전이하지 않는다(소유 팀이 주도). **(B) 범위 안 작업**은 사이클 시작 시 티켓 생성(배정=설정된 사용자) + *즉시 In-Progress 전이(필수)*, 진행 중 진척·결정·산출물을 코멘트/설명으로 사이클 감사 로그와 동기화, 사이클 종료 시 Done 전이(CYCLE-CLOSER). **작은 후속**은 새 티켓을 만들지 않고 *관련 기존 티켓* 에 덧붙여 그 티켓의 브랜치에서 계속한다. **기한**은 크기로 자동 추정(S/M/L)한다 — 단, 이 추상 규율이 각 플랫폼(jira/gitlab/github)에서 *어떤 메커니즘으로 실현되는지는 §1.2 매핑표에 따른다*(상태·기한·부모·담당자의 실제 API·필드가 플랫폼마다 다름). 티켓 생성 전 *필수 필드 발견(create-metadata)은 Jira에만 적용* 하고(GitLab/GitHub은 고정 스키마), 트래커 API 토큰은 *시크릿 스토어(`.env`/토큰 파일 경로)에만* 둔다(공유 룰북·커밋 config에 금지).

---

## 1. 정체성 / 적용 조건 (조건부)

| 항목 | 내용 |
|---|---|
| 종류 | 형식·인터페이스 명세 문서 (에이전트 X) |
| 실행 주체 | `ISSUE-TRACKER-AGENT`(티켓 생성·전이·코멘트·설명 갱신·부모/스프린트 배선 수행 — 별도 피어 에이전트) / 오케스트레이터(사이클↔티켓 바인딩 인식·호출 조율) |
| 참조 주체 | `specs/CYCLE-LOG.md`(사이클 시작 로그·감사 동기화) / `agents/CYCLE-CLOSER.md`(사이클 종료 Done 전이) / `agents/SETTER.md`(config 포착) / `agents/orchestrator/DECISIONS.md`(A-4·A-5) / `agents/orchestrator/ERROR-POLICY.md`(EX-13) |
| 라벨 | **POLICY-ISSUE-TRACKING** (다른 파일이 본 규율을 이 라벨로 인용) |
| 위치 | `ai-dlc-orchestrator/specs/ISSUE-TRACKER-ADAPTER.md` |

### 1.1 적용 조건 (발동 vs 비활성)

본 어댑터는 **시스템이 이슈 트래커를 실제로 운영할 때만** 발동한다. 보유 여부는 *인스턴스 config에서 확인* 한다 — 추정하지 않는다.

| 탐지 신호 (예시 — 동치 수단 대체 가능) | 시사 |
|---|---|
| 인스턴스에 트래커 config 존재(`tracker.type` ∈ {jira,gitlab,github} + 그 type별 좌표·인증) | 트래커 보유 → §2~§8 발동 |
| config에 트리아지 담당자·리포터 신원 정의 | 요청/사이클 티켓 배정 대상 보유 → §3·§4 발동 |
| config에 상태명 매핑(To-Do/In-Progress/Done 동치) 정의 | 사이클↔티켓 생명주기 매핑 가능 → §5 발동 |

**탐지 결과 트래커 config가 없으면 본 어댑터는 비활성(inert)** — 해당 시스템의 사이클에서 §2~§8을 적용하지 않는다. (범용 전제: 이슈 트래커 없이 운영하는 시스템도 정상.) 트래커 config·발견된 런타임 메타(필드 id·이슈타입 id·상태명 등)는 인스턴스에 캐시해 재발견 비용을 줄인다.

---

## 1.2 지원 플랫폼 & 매핑 (jira / gitlab / github)

본 명세의 룰(§3~§8)은 **추상 오퍼레이션** 으로 기술된다. 각 추상 오퍼레이션이 실제 어느 API·필드로 실현되는지는 인스턴스가 선택한 `tracker.type ∈ {jira, gitlab, github}` 에 따라 아래 매핑표로 결정된다. `ISSUE-TRACKER-AGENT`는 `tracker.type` 으로 분기해 이 표를 실행하고, 오케스트레이터·본 명세는 *추상 층위* 만 다룬다.

| 추상 오퍼레이션 | Jira | GitLab Issues | GitHub Issues |
|---|---|---|---|
| **인증** | Basic `email:token` | 헤더 `PRIVATE-TOKEN: <token>` | 헤더 `Authorization: Bearer <token>` (`gho_`/`ghp_`) |
| **생성** | `POST /rest/api/2/issue` (+ createmeta로 필수필드 발견) | `POST /api/v4/projects/:id/issues` | `POST /repos/:owner/:repo/issues` |
| **상태 = 진행 중** | 워크플로우 전이(인스턴스 상태명) | `opened` 유지 + 상태 라벨(예 `in progress`) 부착 | `open` 유지 + 상태 라벨 부착 |
| **상태 = 완료** | 워크플로우 전이(완료) | `state_event=close` (+완료 라벨) | `state=closed` |
| **담당자** | `assignee.accountId` | `assignee_ids`(user id) | `assignees`(login) |
| **기한** | `duedate` | `due_date` | 네이티브 없음 → milestone 마감일 사용 또는 생략(capability gap 명시) |
| **부모/에픽** | `parent.key` | epic(그룹, premium) 또는 parent/label | sub-issues(신규) 또는 label/milestone |
| **스프린트/반복** | sprint 커스텀필드 | iteration(premium)/milestone | milestone / Projects |
| **코멘트** | `POST /issue/{key}/comment` | `POST /projects/:id/issues/:iid/notes` | `POST /repos/:o/:r/issues/:n/comments` |

### 1.2.1 플랫폼 능력(capability) 사실 — 규율 반영

- **상태 모델(state model)**: *워크플로우 전이 상태 기계* 를 갖는 것은 **Jira뿐** 이다. GitLab/GitHub은 open/closed 이진 상태만 있으므로, 추상 상태를 다음으로 매핑한다 — **To-Do = open(상태 라벨 없음)**, **In-Progress = open + 상태 라벨**, **Done = closed**. 이때 *상태 라벨 이름*(예: `in progress`, `done`)은 **하드코딩 금지 — 인스턴스 config(`statusLabels`)에서 배포별로 온다**. Jira의 상태명·전이 id 역시 인스턴스/런타임 발견에서 온다(§3.2).
- **기한(due date)**: Jira(`duedate`)·GitLab(`due_date`)은 이슈에 직접 기한을 지원한다. **GitHub은 이슈 네이티브 기한이 없다** → 크기 기반 기한 휴리스틱(§4)을 **milestone 마감일로 매핑**(config에 milestone 지정 시)하거나, 없으면 *본문에 기한을 기록* 하고 이 **capability gap을 명시** 한다. 크기 휴리스틱(S/M/L) *자체* 는 플랫폼 중립이며 변하지 않는다 — 실현 메커니즘만 다르다.
- **필수 필드 발견(create-metadata)**: **Jira에만 적용** 된다(§6). GitLab/GitHub은 이슈 스키마가 *고정* 이므로(title/description 중심) create-metadata 발견 단계가 없다.
- **부모/에픽·스프린트/반복**: 세 플랫폼 모두 개념은 있으나 실현이 다르다(에픽=Jira parent / GitLab premium epic / GitHub sub-issues·label). 상위 계층·반복 배선은 *config에 해당 수단이 포착됐을 때만* 수행하고, 미지원(예: premium 미보유)이면 label/milestone 등 *동치 수단으로 격하하거나 생략* 하고 gap을 기록한다.
- **불변 규율**: **두 갈래 규율(§3)·사이클↔티켓 생명주기(§5)·작은 후속 재사용(§3.3)** 은 *전부 플랫폼 중립* 이며 세 플랫폼에서 동일하다 — 오직 각 단계의 *실현 메커니즘*(위 표)만 플랫폼마다 다르다.

---

## 2. 트래커 중립 config 계약 (SETTER가 포착)

본 명세는 *어떤 트래커든* 다음 계약을 인스턴스 config에서 읽는다. 구체값은 *배포별* 이며 SETTER 인터뷰로 포착된다(§SETTER 참조). 공유 명세는 *계약의 형태* 만 규정한다. **인스턴스 파일의 *생김새*는 `templates/ISSUE-TRACKER.template.md` 가 단일 원천이다** — SETTER S7.5가 그 템플릿에서 `{메타 레포}/ISSUE-TRACKER.md` 를 생성한다(POLICY-TEMPLATE-ADHERENCE. 템플릿 없이 형식을 지어내면 사람마다 다른 모양이 나와 실행 주체가 좌표를 못 읽는다). **계약은 공통 항목 + `tracker.type` 별 좌표(coordinates)** 로 나뉜다 — `tracker.type` 이 무엇이냐에 따라 어떤 좌표가 필요한지가 결정된다(§1.2).

### 2.1 공통 항목 (모든 `tracker.type` 공통)

| config 항목 | 내용 | 시크릿? |
|---|---|---|
| **`tracker.type`** | `jira` / `gitlab` / `github` 중 하나 — 어느 어댑터·매핑(§1.2)을 쓸지 선택 | 아니오 |
| **리포터/사용자 신원** | 사이클 티켓(범위 안)의 배정 대상 = 설정된 사용자(플랫폼별 식별자 형태는 §1.2 담당자 행) | 아니오(계정 id/login) |
| **트리아지 담당자** | 범위 밖 요청 티켓의 배정 대상(또는 명확한 소유자) | 아니오(계정 id/login) |
| **토큰 저장 위치(`tokenPath`)** | `.env` 변수명 또는 토큰 파일 *경로* (값 아님) | **경로만** — 값은 시크릿 스토어 |

### 2.2 `tracker.type` 별 좌표 (셋 중 선택된 하나만)

| type | 필수 좌표 | 상태 의미론 원천 | 인증(§1.2) |
|---|---|---|---|
| **jira** | `baseUrl` · `projectKey` · `email` · `tokenPath` · `statusNames`(To-Do/In-Progress/Done 동치명) | 워크플로우 전이(상태명·전이 id) | Basic `email:token` |
| **gitlab** | `baseUrl`(host) · `projectIdOrPath` · `tokenPath` · `statusLabels{inProgress, done}` · `defaultAssignee` | open/closed + 상태 라벨(config) | `PRIVATE-TOKEN` 헤더 |
| **github** | `owner` · `repo` · `tokenPath` · `statusLabels{inProgress, done}` · `defaultAssignee` [· `milestone`] | open/closed + 상태 라벨(config) | `Authorization: Bearer` |

> **상태 의미론은 인스턴스 config에서 온다 — 플랫폼마다 다르기 때문이다.** Jira는 `statusNames`(로컬라이즈된 상태명·전이)로, GitLab/GitHub은 `statusLabels`(To-Do=라벨 없음 / In-Progress=`inProgress` 라벨 / Done=closed[+`done` 라벨])로 To-Do/In-Progress/Done *동치* 를 표현한다. 어느 경우든 실제 이름·값은 *하드코딩하지 않고* 인스턴스에서 읽는다(§1.2.1).
> **github `milestone`(선택)**: GitHub은 이슈 네이티브 기한이 없으므로, 크기 기반 기한(§4)을 담을 milestone을 config로 지정할 수 있다 — 미지정 시 기한은 본문에 기록하고 gap을 명시한다(§1.2.1 기한).
>
> **런타임 발견 메타**(Jira 한정 — 필드 id·이슈타입 id·상태 전이 id·보드/스프린트·에픽 맵)는 SETTER가 인터뷰로 채우지 않는다 — `ISSUE-TRACKER-AGENT`가 Jira create-metadata/워크플로우 API로 *런타임 발견* 하고 인스턴스 config에 캐시한다(§6). GitLab/GitHub은 스키마가 고정이라 이 발견 단계가 없다. 로컬라이즈된 상태명(예: "진행 중")·상태 라벨명도 인스턴스에서 온다.

---

## 3. 두 갈래 규율 (핵심)

본 명세의 핵심 — **작업이 오케스트레이터 자신의 손 안(in-scope)인지 밖(out-of-scope)인지로 티켓 처리가 갈린다.**

### 3.1 (A) 범위 밖 개발 아이템 → 요청 티켓

오케스트레이터의 *이번 사이클 손이 닿지 않는* 개발 아이템(예: 프론트엔드 사이클이 필요로 하는 백엔드 변경 — 다른 팀·다른 소유 영역):

- **요청 티켓 생성** — 배정 = **설정된 트리아지 담당자**(또는 명확한 소유자가 있으면 그 소유자).
- **설명 구성**: 배경(background) / 요청(request) / 수용 기준(acceptance criteria) / 관련 링크(related links — 발단이 된 사이클·MR·티켓).
- **자기 전이 금지** — 오케스트레이터는 이 티켓을 In-Progress로 *전이하지 않는다*. 소유 팀이 스스로 집어 진행한다(우리 손 밖 작업의 상태 진행은 소유자 몫).
- 이 티켓은 우리 사이클의 *산출물이자 핸드오프* — 발단 사이클 티켓(있으면)과 상호 링크한다.

### 3.2 (B) 범위 안 작업 → 사이클 = 티켓

오케스트레이터가 *이번 사이클에 직접 수행* 하는 작업:

| 시점 | 처리 |
|---|---|
| **사이클 START** | 티켓 **생성**(배정 = 설정된 사용자) **+ 즉시 In-Progress 상태로 전이 (이 전이는 필수)**. 생성과 전이는 사이클 개시와 묶인다(CYCLE-LOG `CYCLE-START` 시점) |
| **사이클 DURING** | 진척·결정·산출물(MR·커밋)을 티켓 코멘트/설명 갱신으로 기록 — *사이클 감사 로그(audit.md)와 동기화 유지*. 로그의 진실과 티켓의 진실이 어긋나지 않게(§7) |
| **사이클 CLOSE** | **Done 상태로 전이** — `CYCLE-CLOSER`가 사이클 종료 후처리 시 수행 |

- **In-Progress 전이 필수성**: 사이클 시작에서 생성만 하고 In-Progress 전이를 빠뜨리면 티켓이 "생성됨(To-Do)"에 머물러 *실제 진행 상태와 어긋난다*. 생성 직후 전이를 **반드시** 성사시킨다(전이 실패는 성공으로 보고 금지 — §ISSUE-TRACKER-AGENT 자체 체크).
- **상태명은 인스턴스에서**: To-Do/In-Progress/Done은 *의미* 이고, 실제 상태 *이름*(예: 로컬라이즈된 "진행 중")과 전이 id는 인스턴스 config / 런타임 발견에서 온다.

### 3.3 작은 후속 → 기존 티켓 재사용 (새 티켓 금지)

이미 진행 중인 사이클 티켓과 *같은 작업의 작은 연장·불가분 후속* 인 아이템:

- **새 티켓을 만들지 않는다.** *관련 기존 티켓* 에 추가 작업을 덧붙인다(설명 보강 또는 코멘트로 명시) 그리고 **그 티켓의 브랜치에서 계속** 작업한다.
- 판단 기준은 CYCLE-LOG §9.5.2 (a)/(b) 휴리스틱과 정합 — *독립 발의 가능하면* 별도(요청 티켓 또는 새 사이클 티켓), *직접 연장·불가분 후속이면* 기존 티켓 재사용.
- 이는 티켓 난립(사이클마다 사소한 티켓 폭증)을 막는다 — 티켓 1개 = 유의미한 작업 단위.

---

## 4. 기한 추정 (크기 기반 휴리스틱)

티켓 생성 시 **기한(due date)** 을 작업 *크기* 로 자동 추정한다. 크기는 범위(scope)로 판단한다.

| 크기 | 판단 기준(범위) | 기한 (시작일 기준) |
|---|---|---|
| **S** | 국소·단일 관심사, 좁은 변경 | ≈ 영업일 2–3일 |
| **M** | 다중 파일·중간 결합, 한 컴포넌트 범위 | ≈ 1주 |
| **L** | cross-repo·다중 결합·큰 표면 | ≈ 2주 |

- 시작일(start date) 기준으로 위 기간을 더해 기한을 산정한다. 일부 트래커는 *시작 날짜* 필드도 필수이므로(§6 필수 필드 발견) 시작일도 함께 설정할 수 있어야 한다.
- 크기 판단이 모호하면 보수적으로 한 단계 크게 잡되, 사이클 진행 중 재평가 가능(SCOPE-EXPANSION 시 기한도 갱신 후보 — CYCLE-LOG §9.5).
- 본 휴리스틱은 *가이드라인* 이다 — 트래커·팀이 다른 기한 정책을 config로 명시하면 그것을 우선한다.

---

## 5. 사이클↔티켓 생명주기 매핑

```
[사이클 START — CYCLE-LOG CYCLE-START]
    ↓  (범위 안이면)
[티켓 생성 (배정=사용자) + In-Progress 전이(필수)]   ← §3.2 START
    ↓
[사이클 DURING — 진척·결정·MR·커밋]
    ↓
[티켓 코멘트/설명 갱신 ↔ audit.md 동기화]           ← §3.2 DURING, §7
    ↓
[사이클 CLOSE — DP-8 / CYCLE-CLOSER]
    ↓
[Done 전이]                                          ← §3.2 CLOSE (CYCLE-CLOSER)
```

- **START 바인딩**: 사이클 티켓 키·URL을 사이클 감사(audit.md 메타·산출물)에 기록해 사이클과 티켓을 상호 추적한다.
- **CLOSE 전이 주체**: Done 전이는 `CYCLE-CLOSER`의 외부 액션(CC6)으로 수행 — 사이클 종료 판단(DP-8) 후처리에 포함된다.
- **범위 밖(A)** 요청 티켓은 이 생명주기를 *따르지 않는다* — 생성 후 트리아지 담당자에게 넘기고 우리는 전이하지 않는다(§3.1).

---

## 6. 필수 필드 안전성 (create-metadata 발견 — **Jira 한정**)

> **적용 범위**: 본 절은 **`tracker.type = jira` 에만 적용** 된다. **GitLab/GitHub은 이슈 스키마가 고정**(title/description 중심)이라 create-metadata 발견 단계가 없다 — 아래 절차를 건너뛰고 고정 스키마로 바로 생성한다.

Jira에서는 티켓 생성 *전에* 프로젝트의 **필수 필드를 create-metadata API로 발견** 한다 — 가정하지 않는다.

- 일부 Jira 프로젝트는 summary·issuetype·project 외에 *추가 필수 필드*(예: 시작 날짜·기한·기타 커스텀 필드)를 요구한다. 이를 채우지 않으면 생성이 거부된다.
- 발견 절차: Jira `createmeta` 로 대상 프로젝트·이슈타입의 필수 필드 집합을 질의 → 누락 필드를 페이로드에 포함. 발견된 필드 id·이슈타입 id·전이 id는 인스턴스 config에 **캐시**(재질의 비용 절감).
- 발견 실패·필드 불명 시 추측 금지 — 오케스트레이터에 확인 요청(불확실 시 추측 금지 — 공통 규칙).

---

## 7. 감사 로그 동기화 (POLICY-TRACKING 정합)

티켓의 코멘트/설명과 사이클 감사 로그(`audit.md`)는 *한 진실* 을 공유해야 한다.

- 진척·결정·산출물(MR·커밋)은 audit.md에 append-live로 기록되고(CYCLE-LOG §5.1), 그 *유의미한 마일스톤* 이 티켓 코멘트/설명으로 반영된다. 티켓이 로그보다 앞서거나 뒤처지지 않게 유지한다.
- audit.md가 *단일 원천* (원칙 6) — 티켓은 그 파생 뷰다. 둘이 어긋나면 audit.md를 기준으로 티켓을 맞춘다.
- 티켓 키·URL은 audit.md 메타/산출물에 기록해 사후 추적성을 보장한다.

---

## 8. 인증·시크릿 경계

- 트래커 API 토큰(값)은 **시크릿 스토어에만** — `.env` 변수 또는 토큰 파일 *경로* 로 참조한다. **공유 룰북·커밋되는 인스턴스 config·추적 파일에 토큰 값을 절대 두지 않는다**(POLICY-TRACKING — 개인/시크릿만 gitignore).
- 인증 *방식* 은 `tracker.type` 이 결정한다(§1.2 인증 행) — **jira = Basic `email:token`**, **gitlab = `PRIVATE-TOKEN` 헤더**, **github = `Authorization: Bearer`(`gho_`/`ghp_`)**. *방식* 과 토큰의 *위치*(변수명·파일 경로)는 인스턴스 config에 기록 가능하나, *값* 은 아니다.
- 토큰 발급·회전·권한 부여는 **사람 게이트** (자격증명 경계) — 에이전트는 토큰을 *읽고 사용* 만. *forbidden / unauthorized / insufficient-scope* 류는 **ERROR-POLICY EX-13** 로 진단(신원 → 스코프 → 역할).
- 비ASCII(한국어) 티켓 내용의 셸 경유 손상을 피하기 위해, 요청 페이로드는 *ASCII-safe JSON*(예: `ensure_ascii`)으로 만들어 HTTP 클라이언트에 stdin으로 넘기는 것을 권장한다(가이드라인 — POLICY-ENCODING 정합, 강제 아님).

---

## 9. 양방향 참조 맵

| 문서 | 본 명세와의 관계 |
|---|---|
| `agents/ISSUE-TRACKER-AGENT.md` (피어 에이전트, 별도) | 본 명세(룰)의 *실행 주체* — 티켓 생성·전이·코멘트·부모/스프린트 배선 수행 |
| `specs/CYCLE-LOG.md` §4~5 | 사이클 START 바인딩·audit.md 동기화(§5·§7)의 형식 원천 |
| `agents/CYCLE-CLOSER.md` CC6 | 사이클 종료 시 Done 전이 실행처(외부 액션) — 본 §3.2 CLOSE |
| `agents/SETTER.md` S5.7·S7.5 | 트래커 config 계약(§2)의 포착 주체(부트스트랩 인터뷰) + 인스턴스 생성 주체 |
| `templates/ISSUE-TRACKER.template.md` | 인스턴스 `dlc-meta/ISSUE-TRACKER.md` 의 **형식 단일 원천** (§2 계약의 렌더 형태) |
| `agents/orchestrator/ORCHESTRATOR-AGENT.md` 책임 7 | 사이클↔티켓 바인딩 인식·조율 — 본 §5 |
| `agents/orchestrator/DECISIONS.md` A-4 | 외부·비가역 행위 승인 — 티켓 생성·전이가 외부 쓰기이면 정합(대개 자율, 고영향 시 게이트) |
| `agents/orchestrator/DECISIONS.md` A-5 | 생산자→소비자 채택 순서 — 범위 밖 요청 티켓(A)이 생산자 작업일 때 순서 정합 |
| `agents/orchestrator/ERROR-POLICY.md` EX-13 | 트래커 인증·스코프 실패(신원→스코프→역할) — 본 §8 |
| `templates/REPO-MAP.template.md` `{REPO_PROFILES}` | 관련 MR·레포 컨텍스트 참조(설명 related links) 원천 |

---

## 변경 이력

본 명세 v1.0 — **POLICY-ISSUE-TRACKING 신설**: 작업 사이클을 이슈 트래커 티켓에 바인딩하고 범위 밖 작업을 요청 티켓으로 발행하는 *조건부·트래커 중립* 규율 — 두 갈래(범위 밖 요청 / 범위 안 사이클=티켓)·사이클↔티켓 생명주기·작은 후속 재사용·크기 기반 기한·필수 필드 발견·감사 동기화·시크릿 경계.

본 명세 v1.1 — **멀티 플랫폼 일반화(jira/gitlab/github)**: 룰을 *추상 오퍼레이션* 으로 재기술하고, 인스턴스가 `tracker.type ∈ {jira, gitlab, github}` 로 어댑터를 선택하도록 함. §1.2 지원 플랫폼 & 매핑표(인증·생성·상태·담당자·기한·부모/에픽·스프린트·코멘트) + capability 사실 신설. 능력 격차 명시 — 워크플로우 상태 기계는 Jira 전용(GitLab/GitHub은 open/closed + 상태 라벨), GitHub은 이슈 네이티브 기한 없음(milestone 또는 본문), create-metadata 발견은 Jira 전용. 상태 라벨명은 인스턴스 config(`statusLabels`)에서 온다. 두 갈래 규율·생명주기·작은 후속·크기 휴리스틱(S/M/L)은 플랫폼 중립 불변 — 실현 메커니즘만 상이. config 계약을 공통 항목 + type별 좌표(§2.1·§2.2)로 분리.

근거: CYCLE-CLOSER CC6(외부 액션 — 티켓)와 SETTER의 자격증명 부트스트랩이 *placeholder* 로만 존재해, 사이클과 트래커를 잇는 *조건부 규율* 이 비어 있었다. 본 어댑터가 그 층을 *범용·조건부* 로 메운다(트래커 없는 시스템에서는 비활성). v1.1에서 단일 트래커 가정을 걷어내고 세 구체 플랫폼을 대등한 어댑터로 지원한다.

가정한 cross-ref (오케스트레이터가 정합 검토 권장):
- **`agents/ISSUE-TRACKER-AGENT.md`** — 본 명세의 실행 주체인 피어 에이전트가 `tracker.type` 으로 분기해 §1.2 매핑을 실행.
- **인스턴스 트래커 config 파일 `dlc-meta/ISSUE-TRACKER.md`** — 구체 트래커값(`tracker.type` + type별 좌표·상태명/상태 라벨·에픽 맵·토큰 경로)의 인스턴스 단일 원천. SETTER S7.5가 `templates/ISSUE-TRACKER.template.md` 에서 생성·포착하고, ISSUE-TRACKER-AGENT가 (Jira 한정) 런타임 발견 메타를 캐시.
- 플랫폼·기술 명칭(Jira createmeta·GitLab `PRIVATE-TOKEN`·GitHub Bearer·에픽/iteration/milestone 등)은 §1.2에 명시된 검증 매핑이되, 어느 플랫폼도 요구사항이 아니다(인스턴스 선택).

향후 변경은 깃 PR/머지 (원칙 8).

# ISSUE-TRACKER-AGENT.md — 이슈 트래커 연동 실행 서브 에이전트 룰북

> 오케스트레이터가 *사이클을 티켓에 바인딩* 하거나 *범위 밖 요청 티켓* 을 발행할 때 호출하는 서브 에이전트 룰북.
> 핵심: 인스턴스 트래커 config + 시크릿 토큰을 읽어, 필수 필드를 발견한 뒤 **실제 티켓을 생성·전이·갱신** 하고, 사이클 감사 로그와 티켓을 동기화한다.
> 티켓팅 *룰·규율 정의* 본문은 `specs/ISSUE-TRACKER-ADAPTER.md`(**POLICY-ISSUE-TRACKING**)에 위임. 본 룰북은 그 룰을 *실행* 한다.
> 본 에이전트는 **조건부** — 시스템이 *실제로 이슈 트래커를 운영할 때만* 관련된다(트래커 config가 없는 시스템도 정상).
> **멀티 플랫폼 실행체** — 본 에이전트는 인스턴스 config의 `tracker.type ∈ {jira, gitlab, github}` 로 분기해, `specs/ISSUE-TRACKER-ADAPTER.md` §1.2 매핑표(인증·생성·상태·담당자·기한·부모/에픽·스프린트·코멘트)의 *플랫폼별 메커니즘* 을 실행한다. 추상 룰(두 갈래·생명주기·작은 후속·크기 기반 기한)은 세 플랫폼 공통이고, *실현 API·필드만* 플랫폼마다 다르다.
> 기술 명칭은 §1.2에 명시된 검증 매핑을 따르되, 어느 플랫폼도 요구사항이 아니다 — 인스턴스가 `tracker.type` 으로 선택한 것을 실행한다.
> 위치: `ai-dlc-orchestrator/agents/ISSUE-TRACKER-AGENT.md`

---

## 0. 컨텍스트

본 에이전트는 오케스트레이터의 *사이클↔티켓 바인딩* 조율(책임 7) 하에서 호출된다. 티켓팅 규율(POLICY-ISSUE-TRACKING)의 *실행* 을 담당한다.

```
[오케스트레이터 — 사이클↔티켓 바인딩 인식 (POLICY-ISSUE-TRACKING)]
    ↓  (트래커 config 보유 시 — 조건부)
[ISSUE-TRACKER-AGENT 호출 — 액션 단위]
    ├─ I0 사전조건·트래커 config·토큰 로드 (인스턴스 config + 시크릿 경로) — tracker.type 분기
    ├─ I1 (Jira 한정) 필수 필드·메타 발견 (create-metadata — 미캐시 시) / gitlab·github 건너뜀
    ├─ I2 액션 실행 (create / transition / comment·describe / parent-epic / sprint)
    ├─ I3 실행 후 정합성 검증 (실제 티켓 상태 조회 — 지상검증)
    └─ I4 보고
    ↓
[오케스트레이터에 4-튜플 보고]
```

호출 시점(오케스트레이터 책임 3):
- **사이클 START** — 범위 안: 티켓 생성 + In-Progress 전이(필수)
- **사이클 DURING** — 진척·결정·MR·커밋을 코멘트/설명 갱신(audit.md 동기화)
- **사이클 CLOSE** — Done 전이(CYCLE-CLOSER가 사이클 종료 후처리로 트리거)
- **애드혹** — 범위 밖 개발 아이템의 요청 티켓 발행(트리아지 담당자 배정)

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 서브 에이전트 룰북 (행위 주체 — 실제 티켓 쓰기를 *실행* 함) |
| 호출 주체 | 오케스트레이터 (사이클↔티켓 바인딩·요청 티켓 발행 판단 시) / CYCLE-CLOSER 경유(종료 Done 전이 — 원칙 7상 오케스트레이터 책임) |
| 수명 | **액션 단위** 호출. 한 사이클에서 START·DURING·CLOSE·애드혹마다 호출될 수 있음. 종료 후 컨텍스트 해제 |
| 사용자 채널 | 직접 통신 없음. 모든 보고·확인 요청은 *오케스트레이터를 통한다* |
| 조건성 | **조건부** — 시스템이 트래커를 실제로 운영할 때만 관련. 트래커 config가 없으면 본 에이전트는 비활성(호출 자체가 일어나지 않음) |
| 위치 | `ai-dlc-orchestrator/agents/ISSUE-TRACKER-AGENT.md` |

---

## 2. 책임 / 비책임

### 2.1 책임

1. **트래커 config·토큰 로드** — 인스턴스 트래커 config(`tracker.type` + type별 좌표: 베이스 URL/host·프로젝트 키·id·owner/repo·리포터/사용자 신원·트리아지 담당자·상태명 매핑(jira)/상태 라벨(gitlab·github)·인증 방식·토큰 위치) 읽기 + 시크릿 토큰을 config에 적힌 *경로·변수* 에서 읽기(값은 시크릿 스토어에서만). **`tracker.type` 으로 이후 모든 API·필드·인증을 분기**(§1.2 매핑표)
2. **(Jira 한정) 필수 필드·메타 발견** — **`tracker.type = jira` 일 때만** create-metadata/워크플로우 API로 대상 프로젝트·이슈타입의 *필수 필드 집합*·이슈타입 id·상태 전이 id를 발견(추측 금지). 발견 결과를 인스턴스 config에 **캐시**(재질의 절감). **GitLab/GitHub은 스키마 고정 → 이 단계 건너뜀**
3. **티켓 생성** — `tracker.type` 별 엔드포인트로 생성(jira `POST /rest/api/2/issue` / gitlab `POST /api/v4/projects/:id/issues` / github `POST /repos/:owner/:repo/issues`). 크기 기반 기한(S/M/L, POLICY-ISSUE-TRACKING §4) — jira `duedate`·gitlab `due_date`·**github은 네이티브 기한 없음 → milestone 또는 본문 기록(gap 명시)**. 배정 = *범위 안이면 사용자 / 범위 밖 요청이면 트리아지 담당자*(jira `assignee.accountId`·gitlab `assignee_ids`·github `assignees` login)
4. **상태 전이** — To-Do → In-Progress → Done을 `tracker.type` 별 메커니즘으로 실행: **jira = 워크플로우 전이(인스턴스 상태명·전이 id)** / **gitlab·github = open/closed + 상태 라벨(config `statusLabels`)** — In-Progress는 open 유지 + 상태 라벨 부착, Done은 close(gitlab `state_event=close` / github `state=closed`, +완료 라벨). **사이클 START의 In-Progress 전이는 필수 성사**, CLOSE의 Done 전이는 CYCLE-CLOSER 트리거
5. **코멘트·설명 갱신** — 진척·결정·산출물(MR·커밋)을 `tracker.type` 별 코멘트 엔드포인트(jira `POST /issue/{key}/comment` / gitlab `POST /projects/:id/issues/:iid/notes` / github `POST /repos/:o/:r/issues/:n/comments`)로 기록(audit.md 동기화). 범위 밖 요청 티켓은 배경/요청/수용 기준/관련 링크 구조로 작성
6. **부모 에픽·스프린트/반복 배선** — 부모/에픽(jira `parent.key` / gitlab epic(그룹 premium)·parent/label / github sub-issues·label/milestone)·스프린트/반복(jira sprint 커스텀필드 / gitlab iteration(premium)·milestone / github milestone·Projects) 배선. **미지원 수단(예: premium 미보유)이면 label/milestone 등 동치로 격하하거나 생략하고 gap 기록**(인스턴스 config에 해당 수단이 포착됐을 때만 수행)
7. **실행 후 정합성 검증 (POLICY-VERIFY)** — 생성·전이·갱신을 *자기 보고로 가정 금지*. 실제 티켓 상태를 조회해 확인(예: 생성된 키 존재·상태가 실제 In-Progress·배정 반영) + 오케스트레이터에 4-튜플 보고

### 2.2 비책임 (다른 에이전트·산출물에 위임)

| 영역 | 위임 대상 |
|---|---|
| 티켓팅 *룰·규율 정의* (두 갈래·생명주기·기한·재사용) | `specs/ISSUE-TRACKER-ADAPTER.md`(POLICY-ISSUE-TRACKING) — 본 에이전트는 그 룰을 *실행* 만 |
| 트래커 config 최초 포착(인터뷰) | `agents/SETTER.md` — 본 에이전트는 config를 *읽고 런타임 메타만 캐시* |
| 사이클 종료 판단(DP-8) + Done 전이 트리거 시점 | 오케스트레이터 / `agents/CYCLE-CLOSER.md`(CC6) |
| 사이클 감사 로그(audit.md) 형식·기록 | `specs/CYCLE-LOG.md` — 본 에이전트는 티켓을 그 진실에 *동기화* 만 |
| 범위 안/밖 판정·작은 후속 vs 새 티켓 판단 | 오케스트레이터(POLICY-ISSUE-TRACKING §3 휴리스틱 적용) — 본 에이전트는 지시받은 액션 실행 |
| 토큰 *값* 발급·회전·권한 부여 | 사람 게이트(자격증명 경계) — 본 에이전트는 *읽기·사용* 만 |

---

## 3. 핵심 원칙

- **POLICY-ISSUE-TRACKING 준수** — 티켓팅 룰·규율은 `specs/ISSUE-TRACKER-ADAPTER.md`가 단일 원천. 본 에이전트는 거기 정의된 룰을 *실행* 하며 룰을 자체 발명하지 않는다.
- **트래커·프로젝트 중립 + `tracker.type` 분기** — 베이스 URL·프로젝트 키·상태명·상태 라벨·에픽 맵·필드 id는 *전부 인스턴스 config 또는 (Jira 한정) 런타임 발견에서* 온다. 본 룰북에 특정 배포 구체값을 박지 않는다(공유 룰북 불가침). **어떤 API·인증·필드를 쓸지는 `tracker.type ∈ {jira, gitlab, github}` 로 분기**(§1.2 매핑표) — 추상 룰은 공통, 실현만 플랫폼별.
- **필수 필드 발견 선행 (Jira 한정 — 추측 금지)** — **`tracker.type = jira` 일 때만** 생성 전 create-metadata로 필수 필드를 발견한다. 어떤 필드가 필수인지 *가정하지 않는다*(일부 Jira 프로젝트는 시작 날짜 등 추가 필수). **GitLab/GitHub은 스키마 고정 → 발견 단계 없이 고정 스키마로 생성**.
- **In-Progress 전이 필수** — 범위 안 사이클 START는 생성만으로 끝나지 않는다. In-Progress 전이를 반드시 성사시킨다(전이 실패를 성공으로 보고 금지).
- **POLICY-VERIFY (실행 후 지상검증)** — "생성됨/전이됨"은 클레임이지 증거가 아니다. 실제 티켓 상태 조회로 확인하기 전에는 성공 보고 금지(VERIFICATION.md).
- **자격증명 경계** — 토큰 *값* 은 시크릿 스토어(`.env`/토큰 파일)에만. 발급·회전은 사람. 본 에이전트는 토큰을 *읽고 사용* 만. 스코프·권한 부족은 EX-13으로 진단.
- **비ASCII 안전 (POLICY-ENCODING 정합)** — 한국어 등 비ASCII 티켓 내용은 *ASCII-safe JSON*(예: `ensure_ascii`)으로 페이로드를 만들어 HTTP 클라이언트에 stdin으로 넘긴다(셸 UTF-8 손상 방지 — 가이드라인).
- **원칙 7 (오케스트레이터 호출 책임)** — 본 에이전트 직접 호출 X. 보고·확인은 오케스트레이터 경유.

---

## 4. 입출력

### 4.1 입력 (오케스트레이터로부터)

| 필드 | 내용 | 단일 원천 |
|---|---|---|
| **액션** | create / transition / comment·describe / parent-epic / sprint 중 하나(+ 범위 안/밖 구분) | 오케스트레이터 바인딩 판단(POLICY-ISSUE-TRACKING §3) |
| **사이클 컨텍스트** | 사이클 ID·인텐트 요약·영향 레포·크기(S/M/L)·산출물(MR·커밋)·관련 티켓 키(작은 후속·요청 링크) | audit.md / 오케스트레이터 |
| **트래커 config** | `tracker.type`(jira/gitlab/github) + type별 좌표(베이스 URL/host·프로젝트 키/id·owner/repo·리포터/사용자·트리아지 담당자·상태명 매핑(jira)/상태 라벨(gitlab·github)·인증 방식·토큰 위치)(+ Jira 캐시 런타임 메타) | 인스턴스 트래커 config(SETTER 포착) |

> **config 부재 전제**: 트래커 config가 없으면 본 에이전트는 *적용 대상이 아님* → 오케스트레이터에 "트래커 표면 없음" 보고 후 종료(조건부 비활성).

### 4.2 출력 (오케스트레이터에 보고 — 4-튜플 표준)

1. **생성/변경된 티켓 키·URL** — 액션 결과 티켓 식별자(키)·브라우저 URL + (전이 시) 새 상태 / (부모·스프린트 배선 시) 연결 결과. 사이클 티켓은 audit.md 메타에 기록되도록 함께 반환
2. **정합성 체크** — I3 실행 후 지상검증(POLICY-VERIFY) 실측 결과: 티켓 실재·상태 실제값·배정·필수 필드 충족 여부. In-Progress/Done 전이 성사 확인 포함
3. **원본 응답 요약** — 트래커 API 원본 응답의 핵심 요약(생성 키·상태 id·에러 본문 등). 인터뷰는 *없음*(자율 실행) — 대신 트래커 응답 원본
4. **권고 다음 단계** — 사이클 진행 시 코멘트 동기화 시점 / CLOSE 시 Done 전이(CYCLE-CLOSER) / 범위 밖 요청 티켓은 트리아지 담당자 핸드오프 안내 / 인증·스코프 부족 시 EX-13 분기 안내

---

## 5. 실행 절차

```
[페이즈 0] 사전조건·트래커 config·토큰 로드   → I0
[페이즈 1] (Jira 한정) 필수 필드·메타 발견 (미캐시 시) → I1
[페이즈 2] 액션 실행                           → I2
[페이즈 3] 실행 후 정합성 검증 (지상검증)      → I3
[페이즈 4] 보고                                → I4
```

### I0 — 사전조건 + 트래커 config·토큰 로드 (자동, 인터뷰 없음)

- 입력 3 필드 존재 확인(액션 · 사이클 컨텍스트 · 트래커 config).
- **트래커 config 로드 + `tracker.type` 확정** — `tracker.type`(jira/gitlab/github) + type별 좌표(베이스 URL/host·API 버전·프로젝트 키/id·owner/repo·리포터/사용자 신원·트리아지 담당자·상태명 매핑(jira)/상태 라벨(gitlab·github)·인증 방식·토큰 위치·(Jira 캐시) 런타임 메타). **이후 I1~I2의 발견·API·인증·필드는 전부 이 `tracker.type` 으로 분기**(§1.2 매핑표). config가 *없으면* 본 에이전트는 적용 대상이 아님 → 오케스트레이터에 "트래커 표면 없음" 보고 후 종료(조건부 비활성).
- **토큰 로드 + 인증 방식** — config에 적힌 *경로·변수* 에서 토큰을 읽는다(값은 시크릿 스토어에서만). 인증 헤더는 `tracker.type` 별(jira Basic `email:token` / gitlab `PRIVATE-TOKEN` / github `Authorization: Bearer`). 토큰 부재·읽기 실패는 EX-13 진단(추측 금지 — 발급은 사람).
- 실패 시 오케스트레이터에 보고 후 종료.

### I1 — 필수 필드·메타 발견 (Jira 한정 — POLICY-ISSUE-TRACKING §6)

- **`tracker.type = jira` 일 때만 수행** — **GitLab/GitHub은 이슈 스키마가 고정**(title/description 중심, 발견할 전이 id 없음 — 상태는 open/closed+라벨)이므로 **이 페이즈를 건너뛰고 바로 I2** 로 간다.
- (Jira) 캐시된 런타임 메타(필드 id·이슈타입 id·전이 id)가 있으면 재사용. 없거나 stale하면 **createmeta/워크플로우 API로 발견**.
- (Jira) 대상 프로젝트·이슈타입의 *필수 필드 집합* 을 질의 — summary·issuetype·project 외 *추가 필수 필드*(예: 시작 날짜·기한·커스텀 필드)를 식별. 상태 전이(To-Do→In-Progress→Done)의 전이 id도 발견.
- (Jira) 발견 결과를 인스턴스 config에 **캐시**. 발견 실패·필드 불명 시 추측 금지 — 오케스트레이터에 확인 요청.

### I2 — 액션 실행

지시된 액션에 따라 분기하고, **각 액션 안에서 다시 `tracker.type` 으로 §1.2 매핑을 실행**한다. **모든 쓰기 페이로드는 ASCII-safe JSON으로 stdin 경유**(비ASCII 손상 방지 — HTTP 클라이언트 일반 가이드).

| 액션 | 추상 처리 (플랫폼 공통) | `tracker.type` 별 실현 (§1.2) |
|---|---|---|
| **create (범위 안 사이클)** | 배정 = 설정된 사용자. 크기 기반 기한(+필요 시 시작 날짜). **생성 직후 In-Progress(필수)**. 필요 시 부모/에픽·스프린트 배선 | jira `POST /rest/api/2/issue`(필수 필드 충족) / gitlab `POST /api/v4/projects/:id/issues` / github `POST /repos/:owner/:repo/issues`. 담당자 jira `assignee.accountId`·gitlab `assignee_ids`·github `assignees`. 기한 jira `duedate`·gitlab `due_date`·**github milestone 또는 본문(gap)** |
| **create (범위 밖 요청)** | 배정 = 트리아지 담당자(또는 명확한 소유자). 설명 = 배경/요청/수용 기준/관련 링크. **In-Progress 전이 안 함**(소유 팀이 주도 — §3.1). 발단 사이클 티켓과 상호 링크 | 생성 엔드포인트는 위와 동일. 상태는 To-Do 유지(jira 초기 상태 / gitlab·github open, 상태 라벨 없음) |
| **transition** | In-Progress 또는 Done으로 상태 이동 | **jira** = 워크플로우 전이(인스턴스 상태명·전이 id) — 불가 전이면 추측 금지, 유효 전이 조회 후 재시도/보고. **gitlab·github** = In-Progress는 open 유지 + 상태 라벨(config `statusLabels.inProgress`) 부착 / Done은 close(gitlab `state_event=close`·github `state=closed`) + 완료 라벨(`statusLabels.done`) |
| **comment·describe** | 진척·결정·산출물(MR·커밋)을 코멘트/설명 갱신으로 기록(audit.md 동기화). 작은 후속은 *기존 티켓* 에 덧붙임(새 티켓 금지 — §3.3) | jira `POST /issue/{key}/comment` / gitlab `POST /projects/:id/issues/:iid/notes` / github `POST /repos/:o/:r/issues/:n/comments` |
| **parent-epic** | 상위 계층에 연결 | jira `parent.key` / gitlab epic(그룹 premium)·parent/label / github sub-issues·label/milestone. **미지원(예: premium 미보유)이면 label 등 동치로 격하·생략 + gap 기록** |
| **sprint** | 활성 반복·마일스톤에 추가 | jira sprint 커스텀필드 / gitlab iteration(premium)·milestone / github milestone·Projects. **미지원이면 milestone 등 동치로 격하·생략 + gap 기록** |

- **크기→기한**: POLICY-ISSUE-TRACKING §4 휴리스틱(S≈2–3영업일·M≈1주·L≈2주, 시작일 기준) — *플랫폼 중립*. 실현만 다름(github은 네이티브 기한 없음 → milestone 마감일 또는 본문 기록 + gap 명시). 크기는 입력 사이클 컨텍스트에서 옴.
- **상태 라벨명은 하드코딩 금지** — gitlab·github의 In-Progress/Done 라벨명은 인스턴스 config `statusLabels{inProgress, done}` 에서 온다(§1.2.1). jira 상태명·전이 id도 인스턴스/발견에서.
- 실제 API·엔드포인트·필드는 *선택된 `tracker.type` 의 것* — 본 에이전트는 config에 적힌 플랫폼에 *적응* 한다(특정 플랫폼 강제 X).

### I3 — 실행 후 정합성 검증 (POLICY-VERIFY — 지상검증)

액션 결과를 *자기 보고로 가정하지 않는다*. 실제 티켓 상태를 조회해 확인한다.

| 검증 대상 | 지상검증 (무엇을 직접 관측하나) |
|---|---|
| **생성** | 반환된 키로 티켓을 *다시 조회* 해 실재·프로젝트·이슈타입·필수 필드·배정·기한을 확인 |
| **전이** | 전이 후 티켓을 조회해 *실제로* In-Progress/Done인지 확인(전이 API 성공 코드가 아니라 *상태 자체*). jira = 워크플로우 상태값 / gitlab·github = open·closed **+ 상태 라벨 부착·제거 실측**(In-Progress면 `statusLabels.inProgress` 존재, Done이면 closed) |
| **코멘트·배선** | 코멘트 존재·부모/에픽·스프린트·milestone 소속을 조회로 확인. **github 기한이 milestone/본문으로 격하됐으면 그 사실도 확인·보고(gap)** |

- 티켓 쓰기는 외부·파급 행위이므로 검증 사다리(VERIFICATION.md §5)에서 **최소 L2(독립 검증)** — 쓰기 응답과 *다른 조회* 로 확인(같은 층위 재진술은 검증 아님).
- 검증 실패(상태 불일치·티켓 부재)면 성공으로 간주하지 말고 실패에 준해 오케스트레이터에 보고(특히 In-Progress 전이 누락).

### I4 — 보고 + 종료

- §6 자체 체크 수행 후 4-튜플로 오케스트레이터에 반환.
- 본 에이전트는 상태 보존 없음 — 다음 액션 시 새 컨텍스트. 이후 분기(다음 전이·동기화 시점)는 오케스트레이터 책임.

---

## 6. 자체 체크 항목

| 항목 | 통과 기준 |
|---|---|
| 입력 3 필드 + config 로드 | 액션 · 사이클 컨텍스트 · 트래커 config(`tracker.type` + type별 좌표·리포터/트리아지·상태명(jira)/상태 라벨(gitlab·github)·토큰 위치) 확보. config 없으면 "트래커 표면 없음" 종료 |
| `tracker.type` 분기 | 인증·엔드포인트·상태 메커니즘을 §1.2 매핑표대로 선택된 플랫폼(jira/gitlab/github)에 맞게 실행 |
| 필수 필드 발견 (Jira 한정) | jira일 때만 createmeta로 필수 필드·이슈타입 id·전이 id 발견(또는 유효 캐시 재사용) — 추측 금지. gitlab·github은 고정 스키마라 이 단계 없음 |
| 배정 정확성 | 범위 안 = 사용자 / 범위 밖 요청 = 트리아지 담당자 배정 반영 |
| In-Progress 전이 (범위 안 START) | 생성 후 In-Progress 전이 *성사* — 상태 조회로 확인(생성만으로 종료 금지) |
| Done 전이 (CLOSE) | CYCLE-CLOSER 트리거 시 Done 전이 성사 — 상태 조회로 확인 |
| 작은 후속 재사용 | 작은 후속은 새 티켓 미생성 — 관련 기존 티켓에 덧붙임(§3.3) |
| 기한·시작일 | 크기 기반 기한(S/M/L) + 필수면 시작 날짜 설정 |
| 실재 검증 (POLICY-VERIFY) | 생성·전이·배선을 *조회로 실측*(API 성공 코드가 아님) — 최소 L2 |
| 자격증명 경계 | 토큰 *값* 은 시크릿 스토어에서만 읽음, 추적 파일 미기록. 스코프·권한 부족 → EX-13 |
| 비ASCII 안전 | 페이로드 ASCII-safe JSON(stdin) — 한국어 내용 손상 없음 |

---

## 7. 양방향 참조 맵

| 문서 | 본 룰북과의 관계 |
|---|---|
| `specs/ISSUE-TRACKER-ADAPTER.md` (POLICY-ISSUE-TRACKING) | 티켓팅 *룰·규율 정의* 단일 원천 — 본 에이전트는 그 룰을 *실행* (I2) |
| `specs/CYCLE-LOG.md` §4~5 | 사이클 START 바인딩·audit.md 동기화 형식 — comment·describe 액션 원천 |
| `agents/CYCLE-CLOSER.md` CC6 | 사이클 종료 시 Done 전이 트리거처 — 본 transition(Done) 실행 |
| `agents/SETTER.md` | 트래커 config 포착 주체 — 본 에이전트는 그 config를 *읽음* |
| `agents/orchestrator/ORCHESTRATOR-AGENT.md` 책임 3·7 | 호출 주체 + 사이클↔티켓 바인딩 조율 |
| `specs/VERIFICATION.md` (POLICY-VERIFY) | 실행 후 티켓 상태 지상검증 + 보고 정직성 — I3·I4. 최소 L2 |
| `agents/orchestrator/DECISIONS.md` A-4 | 외부·비가역 티켓 쓰기가 고영향이면 승인 게이트 — I2 |
| `agents/orchestrator/ERROR-POLICY.md` EX-13 | 트래커 인증·스코프·역할 실패 진단(신원→스코프→역할) — I0·I2 |

---

## 8. 가정한 cross-ref (오케스트레이터 정합 검토 권장)

본 룰북은 다음을 *가정* 한다 — 해당 문서·필드가 아직 신설 중이면 정합 검토가 필요하다:

- **`specs/ISSUE-TRACKER-ADAPTER.md` (POLICY-ISSUE-TRACKING)** — 티켓팅 룰·규율 정의 명세. 본 에이전트의 실행 대상 룰셋.
- **인스턴스 트래커 config 파일 `dlc-meta/ISSUE-TRACKER.md`** — 구체 트래커값(`tracker.type` + type별 좌표·상태명(jira)/상태 라벨(gitlab·github)·에픽 맵·토큰 경로·리포터/트리아지 신원)의 인스턴스 단일 원천. SETTER S7.5가 `templates/ISSUE-TRACKER.template.md` 에서 생성·포착하고, 본 에이전트가 (Jira 한정) 런타임 발견 메타를 그 파일의 「런타임 발견 메타 캐시」 섹션에 캐시한다.
- **CYCLE-CLOSER CC6** — 사이클 종료 외부 액션(티켓)이 placeholder에서 *본 에이전트 Done 전이 호출* 로 구체화되는 것을 가정. 정합 시 CC6와 본 transition(Done)을 연결한다.

> 플랫폼·기술 명칭(Jira createmeta·GitLab `PRIVATE-TOKEN`·GitHub Bearer·에픽/iteration/milestone 등)은 §1.2(ADAPTER)에 명시된 검증 매핑이되, 어느 플랫폼도 요구사항이 아니다 — 인스턴스가 `tracker.type` 으로 선택. 향후 변경은 깃 PR/머지(원칙 8).

# SYSTEM-WORKFLOW.md — 시스템 레벨 워크플로우 (STEP 0~10)

> **이 문서는 형식·룰 명세 문서.** 에이전트 룰북 아님.
> Stage 1 `WORKFLOW.template.md`(레포 단위 기능 개발 워크플로우)를 *시스템 단위로 재포지셔닝*한 본문.
> 워크플로우 *실행·라우팅*은 ORCHESTRATOR-AGENT 책임(§4 → ROUTING.md 위임). 본 문서는 *각 STEP의 의미·산출물·체크포인트*만 정의.
> 변경은 깃 PR/머지 (원칙 8) — ROUTING.md §1·§3 / TERMINATION.md §1 / AWS-ADAPTER.md §7.2가 본 STEP 정의에 의존하므로 변경 시 영향 검토 필수.
> 위치: `ai-dlc-orchestrator/specs/SYSTEM-WORKFLOW.md`

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 형식·룰 명세 문서 (에이전트 X) |
| 실행 주체 | 오케스트레이터 (§4 라우팅 프레임워크 [3] 적용 워크플로우) |
| 참조 주체 | `agents/orchestrator/ROUTING.md` §1·§3 / `TERMINATION.md` §1 / `specs/AWS-ADAPTER.md` §7.2 / `specs/CYCLE-LOG.md` (STEP↔PROGRESS) |
| 원천 | Stage 1 `WORKFLOW.template.md` + AWS-ADAPTER §7.2 STEP↔AWS 매핑 |
| 동반 문서 | `DESIGN`(시스템 레벨 재포지셔닝) / `STACK`(시스템 레벨 재포지셔닝) / `CHECKLIST·CODING·FRAMEWORK`(AWS Extension 변환) |
| 위치 | `ai-dlc-orchestrator/specs/SYSTEM-WORKFLOW.md` |

**왜 에이전트가 아닌가**: 워크플로우는 *룰·형식*이고, 그 룰에 따라 STEP을 선택·실행·반복하는 *행위*는 오케스트레이터 책임. 본 문서는 ROUTING.md가 런타임에 참조하는 *STEP 카탈로그 단일 원천*.

---

## 2. 시스템 레벨 재포지셔닝 원리

Stage 1 `WORKFLOW.template.md`는 *단일 레포 내부*를 가정한 기능 개발 STEP 0~10이었음. 본 문서는 이를 *한 계층 끌어올려* 다중 레포 시스템 거버넌스 단위로 재정의 (D-Stage2-7).

| 계층 | STEP의 의미 |
|---|---|
| 레포 단위 (원본 Stage 1) | 한 레포 안에서 아이디어→분석→설계→코드→테스트→빌드→커밋→문서화 |
| **시스템 단위 (본 문서)** | 다중 레포에 걸친 분해·cross-repo 설계·**위탁 조율**·통합·통합테스트·시스템 빌드·커밋 코디네이션·진화 |

### 2.1 핵심 전환

- 레포 단위에서 "구현 코드 생성(STEP 4)"이던 중심 STEP이, 시스템 단위에서는 **STEP 4 = 각 레포 AWS 위탁(조율)**으로 추상화됨. 실제 in-repo 구현(요구사항·설계·코드·테스트·빌드)은 AWS AI-DLC가 수행하고, 우리는 *경계와 계약·통합*만 직접 담당.
- 원본 STEP 0의 *기능 명세서 산출*은 시스템에서 분리됨 — 시스템 STEP 0은 인텐트 수신·분류만, 상세 요구사항 명세는 **STEP 4의 AWS Inception(Requirements Analysis)으로 위임**.

### 2.2 승인 정책 재포지셔닝 (중요)

원본은 *모든 STEP에 "[승인 필요]" + "승인 없이 다음 단계 절대 금지"* 정책이었음. 시스템 레벨에서는 이를 **DP-* 기반 선택적 게이트**로 재포지셔닝:

- 단일 사용자·단일 레포 컨텍스트가 아니라 다중 레포·다중 위탁 컨텍스트이므로, 전 STEP 강제 승인은 인지 과부하 (D-Stage2-12 위배)
- 대신 6 factors·위험도로 *컨펌 지점을 선별* (DECISIONS.md DP-1~10). 큰 영향·비가역·추가 레포·진화 제안만 사용자 컨펌, 나머지는 자율 (AI 자율 실행 = 원칙 4)
- `execution-plan.md` 게이트(DP-3+DP-5)가 원본의 "단계별 승인"을 *계획 단위 일괄 승인*으로 대체

---

## 3. 공통 규칙 (시스템 레벨)

원본 `WORKFLOW.template.md` 공통 규칙의 시스템 재포지셔닝.

| 원본 규칙 | 시스템 레벨 |
|---|---|
| 불확실한 건 추측 말고 먼저 물어볼 것 | 불확실 시 추측 금지 — DP 컨펌 또는 꼬리질문. *독립·무관 질문 동시 투척 금지* (인지 과부하 방지 원칙) |
| 코드 생성 시 파일 경로 항상 명시 | 모든 산출물 경로 명시 (서브 4-튜플 첫 필드 / audit.md `Output`) |
| 기존 컴포넌트/모듈 재사용 우선 확인 | STEP 1 영향 분석에서 *재사용 가능 레포·컴포넌트 우선 확인* (REPO-MAP, 원칙 6) |
| 모든 응답은 `{RESPONSE_LANGUAGE}`로 | `dlc-meta/ORCHESTRATOR.md` 인스턴스의 응답 언어 설정 따름 |

**협업 git sync** (D-Stage4-1 — `dlc-meta` 공유 전제):
- **사이클 시작 시 `dlc-meta` pull** (인텐트 유형 무관 — *항상*. STEP 0가 변경·수정서 스킵되므로 STEP에 안 묶고 공통 규칙에 둠). 이유: 진화 입력(`index.md` B-①②③④)·audit·사이클 ID가 팀원 사이클로 갱신됨 — stale 시 DP-9 오판·ID 충돌.
- **영향 코드 레포 pull은 STEP 4 위탁 진입 직전** (영향 레포 확정 후 — STEP 1 이후). 그 레포만 최신화하고 AWS construction. (전체 일괄 pull은 낭비.)
- pull은 충돌을 *줄이지 없애진 않음* — STEP 9 "기준 브랜치 충돌 확인 후 병합" 가드 병존.
- **생산자→소비자 릴리스 순서 (cross-repo 착지 제약)**: 변경이 **생산자(공유 컴포넌트·라이브러리)**와 **소비자(들)**에 걸치면, 생산자를 *먼저* 릴리스·게시·검증한 뒤 소비자가 채택한다(소비자부터 바꾸면 동작 중 소비자가 깨짐 — 금지). 상세 규칙은 **STEP 9**, 정본 아키타입은 DECISIONS **A-5**, 릴리스 흐름은 `specs/CICD-RELEASE-ADAPTER.md`(`POLICY-RELEASE`).
- **시크릿은 `.env`에서 읽기만** (GitLab 토큰·Figma 키 등). 추적 파일(dlc-meta 포함)에 값 커밋 금지. 토큰 발급·접근제어 변경은 사람 (D-Stage4-2).
- **★ git fetch/pull 선행 (필수 — 오케스트레이터·전 서브 에이전트·AWS 위탁 모두 적용).** 브랜치 생성·커밋·푸시·MR 등 *모든* git 작업 전에 `git fetch origin --prune`로 원격 최신을 확인하고 **레포의 기본 브랜치(예: `main`/`master`) 기준**으로 분기한다. **팀 개발 전제 — 내가 작업하는 동안 다른 팀원이 머지할 수 있다**: 그래서 *작업을 시작하기 직전*과 *push 직전* 두 시점 모두에 fetch/pull로 원격 최신을 반영한다. 안 하면 stale base 위에서 작업해 충돌이 나거나 커밋이 누락된다. 푸시 출력에 `[new branch]`가 뜨면 *기존 갱신이 아니라 신규 생성* 신호 — 멈추고 머지 여부·열린 MR 존재를 점검한다. **머지되며 source branch가 자동삭제(`remove_source_branch`)된 브랜치에 추가 push 금지** — 커밋이 MR 없이 떠돌아 기본 브랜치에 누락된다. 공유 브랜치 force-push 금지. 오케스트레이터는 git을 건드리는 *모든 위탁 프롬프트 1단계에 이 fetch 선행을 명시*한다. (근거: 2026-06-09 stale base로 커밋 유실 사고.)

**디자인↔코드 동기화 방향** (design↔code sync direction): 시스템에 코드에 대응하는 **디자인 표면(design surface)** — 코드와 짝을 이루는 디자인 원천(예: 임의의 디자인 툴 안의 디자인 시스템 파일·보드, 혹은 별도 스펙 산출물) — 이 존재하면, 둘은 시간이 지나며 **어긋날(drift)** 수 있다. 그래서 그런 표면마다 **정규(canonical) 원천**과 **동기화 방향**(둘 중 무엇이 *이끌고* 무엇이 *따라가는지*)을 정한다. 이 정규·방향 결정은 사이클마다 **DECISIONS A-2(기준값 정규화)**에 따른다 — 자동 판정하지 않고 소유자·사람의 판단으로 정한다(항상 컨펌). 오케스트레이터는 한 사이클 동안 *정해진 방향으로* 둘을 일치시킨다(예: **코드가 정규면** 디자인을 코드에 맞춰 갱신, **디자인이 정규면** 그 반대). 디자인 표면은 *임의의* 디자인 툴·산출물을 가리키는 일반 개념이다(예: Figma 등은 어디까지나 *예시*). **어떤 디자인 표면이 실제로 존재하고 어디에 있는지**의 구체 명세는 레포 단위로 잡힌다(REPO-MAP — 별도 에이전트 담당).

### 3.1 공통 정책 (POLICY-* — 전 에이전트 공통 라벨)

> 본 §3.1은 시스템 전체 공통 정책의 *정본(단일 원천, 원칙 6)*. 다른 에이전트·템플릿은 아래 라벨(`POLICY-ENCODING`·`POLICY-TEMPLATE-ADHERENCE`·`POLICY-TRACKING`)로 본 정의를 참조한다. 위 *git fetch/pull 선행* 규칙도 본 공통 정책군에 속한다. **검증·지상검증 규율(`POLICY-VERIFY`)은 별도 명세 `specs/VERIFICATION.md`에 둔다 — 본 정책군의 "생성 후 검증·커밋 성사 검증" 요구를 일반화한 횡단 규율로, 같은 라벨 체계로 참조한다.** **릴리스·CI/CD 규율(`POLICY-RELEASE`)은 `specs/CICD-RELEASE-ADAPTER.md`, 실행 환경 배포 규율(`POLICY-DEPLOY`)은 `specs/DEPLOY-ADAPTER.md`에 둔다 — 둘 다 *조건부* 횡단 정책군(레포가 릴리스·배포를 가질 때만 발동)이며 같은 라벨 체계로 참조한다.**

- **POLICY-ENCODING (파일 인코딩·줄바꿈)** — 생성·구체화(materialize)되는 *모든* 파일은 **UTF-8 (BOM 없음)** 으로 기록한다(하드 규칙). **줄바꿈(EOL)은 대상 레포의 컨벤션을 따른다** — `.gitattributes`·`.editorconfig`·기존 파일에서 탐지하고, 단서가 없으면 LF를 기본으로 한다(범용 툴이므로 CRLF 컨벤션 레포도 존중). **로케일 의존 셸 출력(echo·리다이렉트·tee·기본 `Set-Content` 등)으로 비ASCII 내용을 절대 내보내지 말 것** — 일부 OS 콘솔(예: Windows CP949)이 멀티바이트 텍스트를 깨뜨린다(실제 손상 사례의 근인 — 이 방지가 본 정책의 핵심). 반드시 *직접 UTF-8 파일 쓰기*를 사용한다. 생성 후 각 파일을 **검증** — U+FFFD(치환문자)·비ASCII 영역의 떠도는 `?`·BOM이 있으면 손상으로 보고 재생성한다.
- **POLICY-TEMPLATE-ADHERENCE (템플릿 준수)** — 모든 "인스턴스" 산출물은 반드시 대응하는 `templates/*.template.md`에서 **생성**한다 (같은 경로 규약·섹션·변수 치환 유지). 템플릿이 있는 산출물을 자유 형식으로 손수 작성하는 것은 *결함*이다. 각 생성기는 자신의 *템플릿 → 인스턴스 경로* 매핑을 명시해야 한다.
- **POLICY-TRACKING (추적·공유 vs 개인)** — 생성 산출물을 **공유(SHARED)** 와 **개인(PERSONAL)** 으로 구분한다. *공유*(깃 추적 + 커밋해 팀 전체가 한 원천을 공유): 시스템 룰북 인스턴스(오케스트레이터 인스턴스·repo-map)와 각 레포의 생성된 규칙·컨벤션·체크리스트 문서 + 프로젝트 공유 에이전트 규칙 파일. *개인*(gitignore): 시크릿(`.env*`)과 머신 로컬 설정(예: 로컬 에이전트 설정). 생성기는 *개인 파일만* 무시하는 `.gitignore`를 쓰고(공유 규칙 디렉토리 통째 무시 금지), 공유 산출물을 git-add + 커밋(위 fetch 선행 적용)한 뒤 커밋 성사를 **검증**한다. 근거: 미추적 규칙 → 팀원이 컨벤션·목표에서 분기한다.

**현재 단계 명시 컨벤션** (원본 보존): 오케스트레이터는 사용자 보고 시 현재 STEP을 머리에 명시. 예: `[STEP 4 — 레포 AWS 위탁 진행 중]`. 다중 레포 병렬 시 `[STEP 4 — repo:api / repo:frontend 병렬]`.

---

## 4. STEP 0~10 마스터 표

| STEP | 이름 (시스템 레벨) | 주 호출 대상 | AWS 매핑 (AWS-ADAPTER §7.2) |
|---|---|---|---|
| 0 | 시스템 인텐트 수신·분류·초기화 | 오케스트레이터 / 사용자 | 없음 (AWS 트리거 안 함) |
| 1 | 시스템 분해 + 영향 매핑 | 오케스트레이터 | 우리 단독 (AWS Workspace Detection은 REPO-SETTER 시점 완료) |
| 2 | 시스템 설계 (cross-repo) | 오케스트레이터 | 우리 단독 |
| 3 | 피드백 반영 (HITL 게이트, 반복 가능) | 사용자 ↔ 오케스트레이터 | 우리 단독 |
| 4 | **각 레포 AWS 위탁** ★ | 각 레포 AWS 에이전트 | **메인 진입점 — AWS Inception + Construction** |
| 5 | 시스템 통합 (cross-repo) | 오케스트레이터 | 우리 단독 |
| 6 | 시스템 통합 테스트 | 오케스트레이터 | 우리 단독 + AWS Build and Test 흡수 |
| 7 | 시스템 빌드 | 오케스트레이터 | 우리 단독 |
| 8 | 보조 자료 (RFC/ADR 등, CONDITIONAL) | 오케스트레이터 | 우리 단독 (도구 의존, CONDITIONAL) |
| 9 | 다중 레포 커밋 | 오케스트레이터 / CYCLE-CLOSER | 우리 단독 |
| 10 | 사이클 로그·문서화 → 진화 | CYCLE-CLOSER | 우리 단독 |

---

## 5. 인텐트 유형별 STEP 적용 (ROUTING.md §1·§3.2 정합)

| 인텐트 유형 | 디폴트 STEP | 비고 |
|---|---|---|
| 시스템 부트스트랩 | STEP 무관 — SETTER 호출 | 부트스트랩 미완료 시 무조건 우선 |
| 새 기능 개발 | **STEP 0~10 풀 사이클** | Complexity ↑ → detail level ↑ |
| 변경·수정 | **STEP 1~9** (STEP 0 스킵) | Risk ↑ → STEP 6 강제. STEP 10 로깅은 원칙 5로 항상 수행 ※ |
| 분석·조사 | **STEP 1·2만** (코드 변경 없음) | STEP 2 후 결과 보고 → 자동 종료 (TERMINATION §1) |
| 진화·메타 | EVOLUTION 분기 | 별도 (Stage 3 큐) |
| 추가 레포 필요 | REPO-CREATOR 호출 (DP-7) 후 풀 사이클 | — |
| 사이클 종료 | STEP 무관 — CYCLE-CLOSER 호출 | — |

> ※ **정합성 노트(권장)**: ROUTING.md §1·§3.2는 변경·수정을 "STEP 1~9"로 표기. 원칙 5(사이클 로깅 의무)상 종료 로그(STEP 10)는 인텐트 유형 무관 수행되므로, 추후 ROUTING 표기를 "1~9 (+ STEP 10 종료 로그)"로 주석 보강 권장 (별도 PR).

**detail level**은 6 factors로 STEP별 깊이 조정 (ROUTING.md §3.3 위임).

---

## 6. STEP별 본문

각 STEP은 7필드 고정 포맷 + *동반 문서*·*재포지셔닝* 보조 라인. *체크포인트*의 DP/EX는 DECISIONS.md / ERROR-POLICY.md 카탈로그 ID.

### STEP 0 — 시스템 인텐트 수신·분류·초기화
- **목적**: 사용자 자연어 인텐트 수신, 7유형 분류, 사이클 개시. 신규 시스템·도메인이면 초기 컨텍스트 스캔.
- **입력**: 사용자 발화 (입력 채널 A) / REPO-MAP 부트스트랩 상태
- **활동**: (신규 시) 시스템 컨텍스트 스캔·REPO-MAP 최신화 → 인텐트 7유형 분류 (ROUTING §1) → 사이클 ID 생성 (CYCLE-LOG §3) → audit.md `CYCLE-START` 기록
- **호출 대상**: 오케스트레이터 직접 (모호 시 사용자 꼬리질문)
- **산출물**: 사이클 ID, 초기화된 audit.md, 인텐트 분류 결과
- **체크포인트**: DP-1 (인텐트 유형 분류) / EX-4 (응답 모호)
- **AWS 매핑**: 없음 — 시스템 진입점, AWS 트리거 안 함
- *동반 문서*: 원본 `{STEP_0_INIT_ACTIONS}` → 시스템 컨텍스트 스캔·REPO-MAP 최신화로 해소
- *재포지셔닝*: 레포 "기능 아이디어 구체화→명세서" 중 **명세서 산출은 STEP 4 AWS Inception(Requirements)으로 위임**. 시스템 STEP 0은 인텐트 수신·분류까지만. 변경·수정 등 운영 중 인텐트는 STEP 0 스킵.

### STEP 1 — 시스템 분해 + 영향 매핑
- **목적**: 인텐트를 작업 구조로 분해, 영향 레포·도메인·의존 그래프 산출
- **입력**: 분류된 인텐트(STEP 0), REPO-MAP (입력 채널 D)
- **활동**: ROUTING §2 영향 범위 분석 — 도메인 정·역방향 조회 + 의존 전이 탐색 + **의존 DAG 시각화**
- **호출 대상**: 오케스트레이터 직접
- **산출물**: 영향 레포 리스트 / 도메인 매핑 / 의존 DAG / 영향 분류(직접·의존·무영향)
- **체크포인트**: DP-2 (영향 범위 확정 — 5+ 레포 또는 의존 root 변경 시 컨펌)
- **AWS 매핑**: 우리 단독. 각 레포 AWS *Workspace Detection*은 REPO-SETTER 설치 시점에 이미 완료 → 재실행 안 함
- *재포지셔닝*: 레포 "기능 분석 & 매핑(코드 구조·유저플로우 시각화)" → 시스템 "연루 레포·cross-repo 의존 매핑·의존 그래프 시각화". 기존 자산 재사용 우선 확인(§3).

### STEP 2 — 시스템 설계 (cross-repo)
- **목적**: 레포 간 인터페이스·결합점·데이터 흐름 설계
- **입력**: STEP 1 영향 분석 산출물
- **활동**: 레포 경계 간 인터페이스 시그니처 정의, 결합점 식별, 의존 방향 확정. *단일 레포 내부 설계는 STEP 4에서 AWS 위탁*
- **호출 대상**: 오케스트레이터 직접
- **산출물**: cross-repo 설계 (인터페이스 시그니처, 결합점 목록, 데이터 형식)
- **체크포인트**: detail level = 6 factors Complexity (ROUTING §3.3)
- **AWS 매핑**: 우리 단독 (레포 내부 설계는 AWS Application/Functional Design으로 위임)
- *동반 문서*: 원본 STEP 2가 `@.claude/DESIGN.md` 따름 → 시스템 레벨 재포지셔닝된 `DESIGN`(시스템 설계 가이드) 따름
- *재포지셔닝*: 레포 "사전 설계 및 시각화" → 시스템 "레포 경계와 그 사이 계약 설계"

### STEP 3 — 피드백 반영 (HITL 게이트, 반복 가능)
- **목적**: STEP 1·2 산출물에 대한 사용자 피드백 수렴·반영
- **입력**: 사용자 컨펌·수정 요청 (입력 A)
- **활동**: 설계 조정, 영향 재평가. 멀티 초이스 + `[Answer]:` 태그. **수렴까지 반복 가능**
- **호출 대상**: 사용자 ↔ 오케스트레이터
- **산출물**: 확정 cross-repo 설계
- **체크포인트**: DP-6 (큰 변화 시) / EX-4 (모호 → 꼬리질문) / EX-5 (사용자 취소)
- **AWS 매핑**: 우리 단독
- *동반 문서*: 원본 STEP 3가 `@.claude/DESIGN.md` 따름 → 시스템 `DESIGN` 따름
- *재포지셔닝*: AWS 테넷 *Human in the loop*를 시스템 레벨 게이트로 배치. **분석·조사 인텐트는 STEP 2 후 보고로 종료 — STEP 3 진입 안 함**

### STEP 4 — 각 레포 AWS 위탁 ★
- **목적**: 확정 설계를 각 영향 레포에 분배, AWS AI-DLC로 in-repo 워크플로우 위탁
- **입력**: 확정 cross-repo 설계, execution-plan.md (DP-3 + DP-5 산출)
- **활동**: **각 영향 레포 pull(최신화) → 그 위에서** execution-plan.md 생성 → 사용자 게이트 → DAG 따라 AWS 트리거(병렬/직렬, AWS-ADAPTER §5 패턴) → aidlc-state.md 모니터링
  - *레포 pull* (D-Stage4-1): 영향 레포는 STEP 1서 확정됨. 위탁 직전 그 레포들만 pull해 AWS가 *최신 기준 브랜치* 위에서 construction. 로컬 경로는 REPO-MAP `원격`을 `.env` `{WORKSPACE_ROOT}`로 해석(없으면 clone).
- **호출 대상**: 각 레포 AWS 에이전트 (AWS-ADAPTER §5)
- **산출물**: 각 레포 `aidlc-docs/*` (요구사항·설계·코드·테스트)
- **체크포인트**: DP-3 (STEP 스킵·실행) / DP-5 (순서·병렬성) / execution-plan.md 게이트 / EX-2 (AWS 호출 실패) / EX-7 (실행 실패)
- **AWS 매핑**: **메인 진입점** — AWS Inception(요구사항·디자인) + Construction(코드·테스트·빌드) 전체 또는 일부
- *동반 문서*: 원본 STEP 4의 `@.claude/CHECKLIST.md 자가 검증` 및 코딩 규칙(CODING)·프레임워크 패턴(FRAMEWORK) → 모두 AWS Extension 템플릿(`templates/extensions/quality/checklist.template.md`·`coding/`·`framework/`)으로 변환되어 *레포 내부 AWS 워크플로우(Construction/Code Generation)에서 적용* (REPO-SETTER RP6 정상 적용 경로)
- *재포지셔닝*: 레포 "구현 코드 생성"을 시스템 단위에서 "위탁·조율"로 추상화. 실제 구현·자가 검증은 AWS + Extension이 수행

### STEP 5 — 시스템 통합 (cross-repo)
- **목적**: 각 레포 산출물을 cross-repo 결합점에서 통합
- **입력**: 각 레포 aidlc-docs 산출물 (입력 C)
- **활동**: 결합점 연결, 인터페이스 일치 확인 (시그니처·데이터 형식·의존 방향 일관성)
- **호출 대상**: 오케스트레이터 직접
- **산출물**: 통합된 cross-repo 결합
- **체크포인트**: DP-6 / EX-8 (결합점 검증 실패 → 영향 레포 재호출)
- **AWS 매핑**: 우리 단독
- *재포지셔닝*: 레포 "비즈니스 로직 결합(협업)" → 시스템 "cross-repo 결합점 통합". 레포 내부 로직 결합은 AWS 위탁(STEP 4)으로 흡수, 시스템 STEP 5는 *레포 간* 결합만 오케스트레이터 직접 수행

### STEP 6 — 시스템 통합 테스트
- **목적**: cross-repo 통합 동작 검증
- **입력**: STEP 5 통합 결과 + 각 레포 AWS *Build and Test* 결과 흡수
- **활동**: 시스템 레벨 통합 테스트 실행, 각 레포 단위 테스트(정상/에러/엣지/빈 상태) 결과 집계
- **호출 대상**: 오케스트레이터 직접
- **산출물**: 통합 테스트 결과
- **체크포인트**: **Risk ↑ 시 강제** (ROUTING §3.2) / EX-6 (정합성 실패) / EX-8
- **AWS 매핑**: 우리 단독 + AWS Build and Test 흡수
- *동반 문서*: 원본 STEP 6의 테스트 도구·명령어 `@.claude/STACK.md` → 시스템 레벨 `STACK` 따름. 레포 단위 케이스 작성·실행은 AWS Build and Test

### STEP 7 — 시스템 빌드
- **목적**: 통합 시스템 빌드·검증
- **입력**: STEP 6 통과 결과
- **활동**: 다중 레포 빌드 코디네이션, 빌드 오류 원인 설명 + 수정
- **호출 대상**: 오케스트레이터 직접
- **산출물**: 빌드 산출물
- **체크포인트**: Risk ↑ 시 강화 (ROUTING §3.3)
- **AWS 매핑**: 우리 단독 (AWS Operations 미구현 영역 일부 커버 — AWS-ADAPTER 부록)
- *동반 문서*: 원본 STEP 7의 빌드 명령어 `@.claude/STACK.md` → 시스템 `STACK` 따름

### STEP 8 — 보조 자료 (RFC/ADR 등, CONDITIONAL)
- **목적**: 시스템 레벨 보조 자료 생성 — cross-repo 의사결정 RFC/ADR 등
- **입력**: STEP 2~7 결정·설계
- **활동**: 중요 cross-repo 결정의 RFC/ADR 작성 (도구·Extension 의존)
- **호출 대상**: 오케스트레이터 직접
- **산출물**: RFC/ADR 등 보조 자료
- **체크포인트**: **CONDITIONAL** — Scope 좁거나 도구 비활성 시 통째로 스킵 (ROUTING §3.3 / 원본 옵셔널 정합)
- **AWS 매핑**: 우리 단독
- *동반 문서*: 원본 `{STEP_8_BODY}`(도구 의존 본문) → 활성 도구(문서 생성기 등)에 따라 보조 자료 본문 주입. **FRAMEWORK는 코딩 패턴이라 STEP 4 소속 — STEP 8과 무관**
- *재포지셔닝*: 레포 "보조 자료 생성(도구 의존)" → 시스템 "cross-repo 의사결정 기록". 명칭은 원본 "보조 자료"(일반) 유지, AWS-ADAPTER §7.2의 "RFC/ADR"은 대표 예시로 포섭

### STEP 9 — 다중 레포 커밋
- **목적**: 영향 레포 변경을 코디네이션해 커밋·머지
- **입력**: 빌드·테스트 통과 산출물
- **활동**: 다중 레포 커밋 코디네이션, 중간 커밋 권장, 기준 브랜치 충돌 확인 후 병합 (CYCLE-CLOSER가 시스템 레벨 자동화 — 외부 액션은 Stage 3+ placeholder)
- **호출 대상**: 오케스트레이터 직접 / CYCLE-CLOSER
- **산출물**: 각 레포 커밋·머지
- **체크포인트**: DP-7 인접 (커밋 전 최종 게이트)
- **AWS 매핑**: 우리 단독
- *동반 문서*: 원본 STEP 9의 브랜치·커밋 규칙 `@.claude/STACK.md` → 시스템 `STACK` 따름
- **★ 생산자→소비자 릴리스 게이트 (착지 순서 제약)**: 한 변경이 **생산자(공유 컴포넌트·라이브러리)**와 그것을 쓰는 **소비자(들)**에 걸칠 때, 생산자 변경을 **먼저 릴리스하고 게시(published)·검증**한 *뒤에야* 소비자가 새 버전을 채택한다. 소비자 쪽을 먼저 바꾸면(예: 로컬 우회·오버라이드 제거, 의존 버전 범프) 생산자가 아직 게시 전이라 **동작 중인 소비자가 깨진다** — 금지. 따라서 다중 레포 착지는 *생산자 레포 → 소비자 레포* 순으로 코디네이션하고, 생산자 변경이 해당 레포의 **기본 브랜치(예: `main`/`master`)에 머지·게시되어 검증된 것을 확인**한 다음 소비자 채택 커밋을 진행한다. 생산자 릴리스라는 *행위* 자체는 외부·비가역일 수 있어 별도 컨펌이 걸릴 수 있다(DECISIONS A-4). 채택 *순서*는 의존 그래프로 결정되는 자율 사항(DP-5). (근거·정본: DECISIONS **A-5 생산자→소비자 채택 순서**, 릴리스 흐름·`POLICY-RELEASE`는 `specs/CICD-RELEASE-ADAPTER.md`.)
- *비고*: 권한·공유 설정 변경은 본 시스템 범위 밖 (보안 경계)

### STEP 9.5 — 착지 후 배포 (조건부 sub-phase, STEP 번호 불변)

> **본 절은 STEP 0~10 마스터 표(§4)를 재번호하지 않는다** — STEP 9(커밋·머지)와 STEP 10(사이클 로그) *사이*에 끼는 **조건부 활동**일 뿐이다. 마스터 표·인텐트별 STEP 매핑(§5)·의존 문서(ROUTING/TERMINATION/AWS-ADAPTER/CYCLE-LOG의 STEP 번호 참조)는 그대로 두고, 본 절은 그 위에 *덧붙이는* 착지 보강이다. "9.5"는 *9와 10 사이의 조건부 단계*라는 표기일 뿐 새 마스터 STEP이 아니다.

- **발동 조건 (CONDITIONAL)**: STEP 9 커밋·머지 + 릴리스·퍼블리시(`POLICY-RELEASE` — 생산자→소비자 게이트 통과·검증)까지 끝난 *뒤*, **실행 환경에 배포할 표면이 있는 레포/시스템에서만** 발동한다. 배포 표면이 없으면(라이브러리·산출물만 퍼블리시하는 레포 등) 본 절은 비활성(inert) — 그대로 STEP 10으로 넘어간다. 발동 여부는 *탐지*한다(REPO-MAP 배포 프로파일·배포 매니페스트·환경 엔드포인트 등 — `specs/DEPLOY-ADAPTER.md` §1.1).
- **목적**: 검증된 릴리스 산출물을 *실행 중인 환경*에 올리는 착지 후속 단계. 릴리스(`POLICY-RELEASE`)는 "퍼블리시 + 레지스트리 존재 검증"에서 멈추므로, 그 검증된 산출물을 환경에 배포하는 후반부를 본 절이 메운다.
- **활동**: 오케스트레이터가 *검증된 릴리스 ref* 확보 후 **`DEPLOY-AGENT`를 호출**(원칙 7 — 모든 서브 호출은 오케스트레이터 책임)해 `specs/DEPLOY-ADAPTER.md`(`POLICY-DEPLOY`)의 규율로 배포한다:
  - **환경 모델·전략 적응** — 낮은 티어 → 높은 티어 승격, 레포가 포착한 배포 방식에 적응(예: 롤링·블루그린·카나리 — 전부 *예시*).
  - **실행 경계** — **non-prod 환경은 자율 배포**, **production(또는 비가역·고영향 타깃)은 사람 게이트(DECISIONS A-4)** — 에이전트는 준비·검증만 자율, 실제 prod 트리거는 *사람의 명시적 승인 후에만*. 일반 "진행해"는 prod 포괄 위임이 아님.
  - **배포 후 검증 (`POLICY-VERIFY`)** — 배포 성공을 자기 보고로 가정 금지. 실행 환경의 health/smoke를 *지상검증*(최소 L2 독립 검증)으로 실측.
  - **롤백** — 검증 실패 시 *직전 정상 상태(last good)*로 자동 롤백하고 롤백도 검증. prod 롤백은 안전 기본값으로 진행하되 사람에게 에스컬레이트.
- **호출 대상**: 오케스트레이터 → `DEPLOY-AGENT` (레포/환경 단위, 다중 환경 시 환경마다 호출 가능)
- **산출물**: 배포된 환경·릴리스 ref·전략, 배포 후 health/smoke 검증 실측 결과, (prod 시) 사람게이트 로그, (필요 시) 상위 환경 승격 제안
- **체크포인트**: **A-4 (prod 등 외부·비가역 배포 트리거 사람 승인 — 항상)** / DP-5 인접(채택·승격 순서는 의존 그래프 기반 자율) / EX-13 (배포 자격증명·스코프 부족 → 사람) / EX-14 (배포·롤백 실패 → 에스컬레이트)
- **AWS 매핑**: 우리 단독 (AWS Operations 미구현 영역 — 본 시스템 보강). 레포 내부 배포 스크립트 구현 자체는 STEP 4 AWS 위탁으로 흡수
- *재포지셔닝*: CI/CD *부착·통합*은 `agents/CICD-SETTER.md`(REPO-SETTER 셋업 시 또는 운영 중 재부착, `POLICY-RELEASE`), 실제 환경 *배포 실행*은 본 절의 `DEPLOY-AGENT`(`POLICY-DEPLOY`)가 담당 — *배선*과 *실행*의 책임 분리
- *비고*: 자격증명·권한 *값*의 발급·회전은 본 시스템 범위 밖 (사람 게이트, 보안 경계 — non-prod 자율 배포라도 자격증명 발급은 사람). 정본·상세 규율: `specs/DEPLOY-ADAPTER.md`(`POLICY-DEPLOY`), DECISIONS **A-4**(외부·비가역 승인)·**A-5**(생산자→소비자 채택 순서), 릴리스 흐름 `specs/CICD-RELEASE-ADAPTER.md`(`POLICY-RELEASE`), 실행 주체 `agents/DEPLOY-AGENT.md`, CI/CD 부착 `agents/CICD-SETTER.md`

### STEP 10 — 사이클 로그·문서화 → 진화
- **목적**: 사이클 종료 기록 최종화, 문서화, 진화 입력 데이터 적재
- **입력**: 사이클 전체 audit.md, 신규/변경 컴포넌트·스키마
- **활동**: 신규 API·변경 스키마 문서화 + 작업 완료 요약 → audit.md 최종화 + AWS audit 스냅샷 흡수 (CYCLE-LOG §9.2) → 진화 패턴 감지 (DP-9 후보)
- **호출 대상**: CYCLE-CLOSER (사이클 종료 후처리)
- **산출물**: 최종 audit.md, 문서 갱신, 진화 후보 (ORCHESTRATOR.md EVOLUTION 누적)
- **체크포인트**: DP-8 (종료 판단) / DP-9 (진화 능동 제안 — 항상 컨펌)
- **AWS 매핑**: 우리 단독
- *재포지셔닝*: 원본 "문서화(API·스키마·완료 요약)"에 **사이클 로그 최종화 + 진화 입력**(시스템 신규)을 결합
- *비고*: 원칙 5 — 종료 로그는 인텐트 유형 무관 수행. TERMINATION §1: **STEP 10 완료 = 워크플로우 사이클 종료 신호**

---

## 7. 템플릿 변수·동반 문서 매핑 (Stage 1 → 시스템)

원본 `WORKFLOW.template.md`가 참조하던 변수·동반 문서의 시스템 레벨 해소.

| 원본 참조 | 분류 (HANDOFF §2.5) | 시스템 레벨 해소 |
|---|---|---|
| `{RESPONSE_LANGUAGE}` | 변수 | `dlc-meta/ORCHESTRATOR.md` 응답 언어 설정 |
| `{STEP_0_INIT_ACTIONS}` | 변수 | STEP 0 시스템 컨텍스트 스캔·REPO-MAP 최신화 |
| `{STEP_8_BODY}` | 변수 | FRAMEWORK Extension 활성 시 본문 주입 |
| `@.claude/DESIGN.md` (STEP 2·3) | 시스템 레벨 유지·재포지셔닝 | 시스템 `DESIGN` 설계 가이드 |
| `@.claude/STACK.md` (STEP 6·7·9) | 시스템 레벨 유지·재포지셔닝 | 시스템 `STACK` 규칙 |
| `@.claude/CHECKLIST.md` (STEP 4) | AWS Extension 변환 | `templates/extensions/quality/checklist.template.md` (REPO-SETTER RP6 적용, STEP 4 내부) |
| (CODING / FRAMEWORK) | AWS Extension 변환 | `templates/extensions/coding/`·`templates/extensions/framework/` (STEP 4 내부 — 코드 생성 시점) |

---

## 8. 양방향 참조 맵

| 문서 | 본 명세와의 관계 |
|---|---|
| `agents/orchestrator/ORCHESTRATOR-AGENT.md` §4.1 [3] | 라우팅 프레임워크가 본 STEP 카탈로그 적용 |
| `agents/orchestrator/ROUTING.md` §1 | 인텐트→디폴트 STEP 매핑이 본 §5 정합 |
| `agents/orchestrator/ROUTING.md` §3 | STEP 선택(6 factors·detail level)이 본 STEP 0~10 참조 |
| `agents/orchestrator/DECISIONS.md` | 본 §6 체크포인트의 DP-* 카탈로그 원천 |
| `agents/orchestrator/ERROR-POLICY.md` | 본 §6 체크포인트의 EX-* 카탈로그 원천 |
| `agents/orchestrator/TERMINATION.md` §1 | STEP 10 완료 = 종료 신호 |
| `specs/AWS-ADAPTER.md` §7.2 | STEP↔AWS phase·stage 매핑 정본 (STEP 4 메인 진입점) |
| `specs/CYCLE-LOG.md` §8 | STEP 진행을 PROGRESS entry로 기록 |
| `agents/CYCLE-CLOSER.md` | STEP 9·10 시스템 레벨 후처리 |
| `specs/DEPLOY-ADAPTER.md`(POLICY-DEPLOY, 조건부) | STEP 9.5 착지 후 배포 규율 원천 (환경 모델·실행 경계·롤백) |
| `agents/DEPLOY-AGENT.md` | STEP 9.5 배포 실행 주체 (non-prod 자율 / prod 사람게이트 A-4) |
| `agents/CICD-SETTER.md` | CI/CD 부착·통합 실행자 (STEP 9.5 배선 측 — POLICY-RELEASE) |
| `templates/REPO-MAP.template.md` | STEP 1 영향 분석 입력 원천 |
| `DESIGN`(재포지셔닝) / `STACK`(재포지셔닝) | STEP 2·3 / STEP 6·7·9 동반 가이드 |
| `templates/extensions/*`(AWS Extension 템플릿) | STEP 4 레포 내부 적용 (코드 생성 시점) |

---

## 변경 이력

본 명세 v1.0 — **D-Stage2-18 (Layer C — SYSTEM-WORKFLOW.md 작성)**.

누적 결정:
- D-Stage2-7: STEP 0~10 시스템 레벨 재포지셔닝 + AWS 위탁(STEP 4) 결정
- D-Stage2-18: 본 문서 작성. 원본 `WORKFLOW.template.md` 대조 반영 — 공통 규칙·승인 정책(gate-everything→DP 선택 게이트)·동반 문서 참조·STEP 8 명칭(보조 자료)·STEP 0 명세서 AWS 위임 등

보강:
- 착지 후 배포 (STEP 9.5 조건부 sub-phase) 추가 — STEP 9 커밋·릴리스(POLICY-RELEASE) 이후 `DEPLOY-AGENT`(`POLICY-DEPLOY`) 배포: non-prod 자율 / prod 사람게이트(A-4) + 배포 후 지상검증(POLICY-VERIFY) + 롤백. **STEP 0~10 마스터 표 번호 불변**. §3.1에 POLICY-DEPLOY(+POLICY-RELEASE) 라벨 등록. §8 참조 맵에 DEPLOY-ADAPTER/DEPLOY-AGENT/CICD-SETTER 추가.

큐 (후속):
- 원본 STEP 0 명세서 포맷 일반화 ("원본 zip 그대로 유지 — 향후 일반화 후보" 메모) → AWS Inception Requirements 형식과 정합 검토 (Stage 3)
- ROUTING.md §1·§3.2 변경·수정 STEP 표기 "1~9 (+STEP 10)" 주석 보강 (별도 PR)
- AWS-ADAPTER.md §7.2 STEP 8 라벨 "RFC/ADR" → "보조 자료(RFC/ADR 등)" 정합 검토 (선택)

향후 변경은 깃 PR/머지 (원칙 8).

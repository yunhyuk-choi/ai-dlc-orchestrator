# AWS-ADAPTER.md — AWS AI-DLC 통합 인터페이스 명세

> **이 문서는 형식·인터페이스 명세 문서.** 에이전트 룰북 아님.
> 본 명세는 AWS `awslabs/aidlc-workflows` 와 우리 시스템 간 *통합 표준*.
> 실행 주체는 REPO-SETTER(설치) / 오케스트레이터(트리거·흡수). 본 문서는 *룰만* 정의.
> 변경은 깃 PR/머지 (원칙 8) — AWS 버전 변경 또는 우리 통합 정책 변경 시.

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 형식·인터페이스 명세 문서 (에이전트 X) |
| 실행 주체 | REPO-SETTER (설치·검증) / 오케스트레이터 (트리거·흡수·예외 전파) |
| 참조 주체 | REPO-SETTER.md / `agents/orchestrator/ERROR-POLICY.md` §5 / `agents/orchestrator/ROUTING.md` §6 / `agents/orchestrator/DECISIONS.md` §4 |
| 위치 | `ix-ai-dlc/specs/AWS-ADAPTER.md` |

**왜 어댑터인가**: 우리 시스템(시스템 레벨)과 AWS(레포 레벨) 사이 *번역·중개 레이어*. 양쪽 모두 자기 관습 유지하면서 통신 가능하도록.

---

## 2. AWS AI-DLC 개요

| 항목 | 내용 |
|---|---|
| 출처 | `awslabs/aidlc-workflows` (GitHub) |
| 라이선스 | MIT-0 (완전 자유 사용) |
| 비용 | AWS 계정·서비스 불필요. 룰셋은 단순 markdown 파일들. |
| 핵심 파일 | `aws-aidlc-rules/core-workflow.md` (항상 로드, 빌트인 에이전트 동작 override) |
| 디테일 | `aws-aidlc-rule-details/{common,inception,construction,operations,extensions}/` |
| 산출물 | 사용자 워크스페이스의 `aidlc-docs/` 디렉토리 |
| 에이전트 | IDE/에이전트 무관(agnostic) — Claude Code / Cursor / Kiro / Q Developer 등 모두 지원 |
| 통합 결정 | D-Stage2-7 (변형 B') — 시스템 레벨 = 우리, 레포 레벨 = AWS |

---

## 3. AWS 룰셋 설치 명세 (REPO-SETTER 위임처)

### 3.1 설치 위치 (각 레포)

```
{레포 루트}/
├── aidlc-rules/
│   ├── aws-aidlc-rules/
│   │   └── core-workflow.md
│   └── aws-aidlc-rule-details/
│       ├── common/
│       ├── inception/
│       ├── construction/
│       ├── operations/
│       └── extensions/             ← 우리 Stage 1 산출물 일부가 여기로 변환
└── aidlc-docs/                     ← AWS 산출물 영역 (설치 시점에는 비어있음)
```

### 3.2 설치 절차 (REPO-SETTER가 수행)

```
[1] aws-aidlc-version.txt 핀 읽기
       ↓
[2] awslabs/aidlc-workflows release에서 해당 버전 zip 다운로드
       ↓
[3] {레포 루트}/aidlc-rules/ 에 압축 해제
       ↓
[4] 우리 Stage 1 산출물 일부(CHECKLIST/CODING/FRAMEWORK)를 
   aidlc-rules/aws-aidlc-rule-details/extensions/ 로 변환·복사
   (POLICY-ENCODING — 아래 인코딩 주의 참조)
       ↓
[5] aidlc-docs/ 빈 디렉토리 생성
       ↓
[6] 정합성 검증 (§3.3 항목)
```

**인코딩 주의 (POLICY-ENCODING — 위 [4] 변환·복사에 필수)**:
변환·복사로 생성되는 모든 룰셋·Extension 파일은 **UTF-8 no-BOM + LF**로 출력한다. 비-ASCII(예: 한국어 산문)를 포함하므로 **직접 UTF-8 파일 쓰기**를 쓰고, 로케일 의존 콘솔·쉘 파이프라인(예: Windows CP949 등)으로 흘려보내지 않는다(mojibake 손상 위험). 복사 직후 생성 파일을 스캔해 손상 신호(U+FFFD `�` / 비-ASCII 자리의 `?` / BOM)를 탐지하고, 발견 시 재생성·재검증한다. (절차 본문은 REPO-SETTER RP6과 동일 — 단일 원천.)

### 3.3 설치 정합성 검증

REPO-SETTER가 설치 후 다음 항목 자체 체크:
- `aidlc-rules/aws-aidlc-rules/core-workflow.md` 존재
- `aidlc-rules/aws-aidlc-rule-details/` 4개 표준 서브폴더 존재 (common/inception/construction/extensions; operations는 placeholder 허용)
- 다운로드된 버전이 `aws-aidlc-version.txt` 핀과 일치
- `aidlc-docs/` 디렉토리 생성됨

실패 시 → EX-3 (룰셋 누락·버전 mismatch) 트리거.

---

## 4. AWS 버전 핀 메커니즘

### 4.1 위치 및 형식

위치: `ix-ai-dlc/aws-aidlc-version.txt`

형식 (단일 라인):
```
v0.1.7
```

또는 git commit hash 핀 가능:
```
commit:a3f8c9d2b1e5...
```

### 4.2 호환성 검사

- 운영 모드 진입 시 오케스트레이터가 *모든 영향 레포*의 설치 버전 확인
- 핀과 mismatch 발견 → EX-3 ABORT
- 사용자에게 REPO-SETTER 재실행 안내

### 4.3 업그레이드 절차

새 AWS 버전 적용 시:
```
[1] ix-ai-dlc/aws-aidlc-version.txt 갱신 (PR/머지)
       ↓
[2] EX-11 (외부 룰북 변경 감지) 트리거 — 오케스트레이터가 사용자에게 재로딩 컨펌
       ↓
[3] 영향 레포 각각에 REPO-SETTER 재실행 (룰셋 재설치)
       ↓
[4] 정합성 재검증
```

업그레이드는 *Stage 4 거버넌스 (PR 기반 룰북 진화)* 영역. 본 명세는 *메커니즘*만.

---

## 5. AWS 에이전트 트리거 인터페이스 (오케스트레이터 출력 C)

### 5.1 트리거 모델

AWS AI-DLC는 *별도 프로세스가 아니라* IDE/에이전트가 *core-workflow.md를 로드*해서 동작. 우리가 "AWS 에이전트 호출"이라 부르는 것은 실제로 *각 레포 컨텍스트에서 AWS 룰을 따라 작업하는 것*.

### 5.2 트리거 패턴

오케스트레이터가 AWS 워크플로우 진입 시 다음 형식:

```
[STEP 4 — 레포 {slug} AWS 위탁]
Context loaded: {레포 경로}/aidlc-rules/
Trigger phrase: "Using AI-DLC, {요청 본문}"
Initial phase: Inception / Construction / Operations
Initial stage: (Inception 진입 시 보통 Requirements Analysis)
Execution plan reference: {레포 경로}/aidlc-docs/execution-plan.md (있을 시)
```

AWS 룰이 "Using AI-DLC, ..." 패턴을 인식해 *core-workflow.md 적용 모드* 진입.

### 5.3 단일 STEP vs 풀 사이클 트리거

| 트리거 모드 | 사용 사례 |
|---|---|
| **풀 사이클** | 새 기능 — Inception → Construction → (Operations) 전체 |
| **단일 phase** | 변경·수정 — Construction만 (Inception 스킵) |
| **단일 stage** | 정밀 작업 — 특정 stage만 (예: Build and Test만) |

오케스트레이터가 DP-3 (STEP 스킵·실행) + DP-5 (호출 순서) 결과에 따라 결정.

---

## 6. AWS 산출물 흡수 인터페이스 (오케스트레이터 입력 C)

### 6.1 흡수 대상

각 영향 레포의 `aidlc-docs/` 안의 산출물:

| 파일 | 역할 | 우리 사용 |
|---|---|---|
| `audit.md` | 결정·예외 추적 | CYCLE-LOG.md §9 흡수 (스냅샷) |
| `aidlc-state.md` | phase·stage 진행 상태 | DP-6 응답 검토 입력 |
| `execution-plan.md` | 실행 계획 | DP-3 + DP-5 게이트 검토 (§7 참조) |
| `inception/*` | Inception phase 산출물 | 우리 STEP 1·2 검토용 |
| `construction/*` | Construction phase 산출물 | 우리 STEP 5·6·7 검토용 |

### 6.2 흡수 시점

| 시점 | 동작 |
|---|---|
| **AWS phase·stage 완료** | `aidlc-state.md` 갱신 감지 → DP-6 응답 검토 트리거 |
| **AWS 예외 발생** | `audit.md`에 FAILED entry → EX-2 또는 EX-7 트리거 |
| **사이클 종료 시** | 모든 영향 레포의 `audit.md` 스냅샷 흡수 (CYCLE-LOG.md §9.2) |

### 6.3 파싱 형식

AWS audit.md는 우리 audit.md와 *형식이 다름*. 흡수 시 변환:

| AWS 필드 | 우리 매핑 |
|---|---|
| Stage 이름 | PROGRESS entry로 변환 (CYCLE-LOG §8) |
| Decision entry | DP-* 매핑 시도 (해당 시) 또는 PROGRESS로 보존 |
| Exception entry | EX-* 매핑 시도 (해당 시) — 주로 EX-7 |
| User confirmation | `Confirm:` 필드로 보존 |

매핑 불가능한 AWS-고유 entry는 *그대로 보존* (PROGRESS 또는 별도 AWS-NATIVE entry로).

---

## 7. execution-plan.md 호환 변환

### 7.1 우리 → AWS 변환

오케스트레이터가 DP-3 + DP-5 결과를 AWS execution-plan.md 형식으로 산출 (각 영향 레포에):

```markdown
# Execution Plan — {cycle-id} — repo:{slug}

## Phases & Stages

### Inception
- [x] Workspace Detection — ALWAYS (이미 완료, brownfield 확인됨)
- [ ] Reverse Engineering — SKIP (이유: greenfield 영역만 작업)
- [x] Requirements Analysis — ALWAYS, detail level: HIGH
- [ ] User Stories — INCLUDE (이유: 사용자 워크플로우 명세 필요)
- [x] Workflow Planning — ALWAYS, detail level: MEDIUM
- [ ] Application Design — INCLUDE (이유: 신규 도메인)
- [ ] Units Generation — SKIP (이유: 단일 컴포넌트, 분해 불필요)

### Construction
- [ ] Functional Design — INCLUDE
- [ ] NFR Requirements — INCLUDE (Risk Level: HIGH)
- [ ] NFR Design — INCLUDE
- [ ] Infrastructure Design — SKIP (이유: 인프라 변경 없음)
- [ ] Code Generation — INCLUDE
- [ ] Build and Test — INCLUDE, detail level: HIGH

### Operations
- placeholder (AWS 미구현)

## 6 Factors Evaluation
- Request Clarity: HIGH
- Problem Complexity: MEDIUM
- Scope: MEDIUM (3 repos 영향)
- Risk Level: HIGH (운영 중 인증 시스템)
- Available Context: HIGH (brownfield, REPO-MAP 매핑 완성도 양호)
- User Preferences: 신중 검토 명시

## Dependencies
- Depends on: (없음)
- Depended by: api-gateway, frontend-shell

## Cluster
- Parallel group: [frontend, api] (의존 없음)
- Sequential after: db-migrations
```

### 7.2 매핑 표 — 우리 STEP ↔ AWS phase·stage

| 우리 STEP (시스템 레벨) | AWS phase·stage (각 레포) |
|---|---|
| STEP 0 — 시스템 인텐트 | (우리 단독, AWS 트리거 안 함) |
| STEP 1 — 시스템 분해 + 영향 매핑 | 우리 단독 + 각 레포 AWS *Workspace Detection*은 REPO-SETTER 시점에 이미 완료 |
| STEP 2 — 시스템 설계 (cross-repo) | 우리 단독 |
| STEP 3 — 피드백 반영 | 우리 단독 |
| STEP 4 — 각 레포 AWS 위탁 (코드 생성) | **AWS Inception (요구사항·디자인) + Construction (코드·테스트·빌드)** 전체 또는 일부 |
| STEP 5 — 시스템 통합 (cross-repo) | 우리 단독 |
| STEP 6 — 시스템 통합 테스트 | 우리 단독 + 각 레포 AWS *Build and Test* 결과 흡수 |
| STEP 7 — 시스템 빌드 | 우리 단독 |
| STEP 8 — 보조 자료 (RFC/ADR 등, CONDITIONAL) | 우리 단독 |
| STEP 9 — 다중 레포 커밋 | 우리 단독 |
| STEP 10 — 사이클 로그 → 진화 | 우리 단독 |

핵심: **STEP 4가 AWS 위탁의 메인 진입점**. 나머지 STEP은 우리 단독.

---

## 8. 예외 전파 (양방향)

ERROR-POLICY.md §5의 본격 명세.

### 8.1 AWS → 우리

| AWS 신호 | 우리 처리 |
|---|---|
| `aidlc-state.md` 상태 = FAILED | EX-7 (execution-plan.md 실행 실패) — 정책 B ASK |
| `aidlc-state.md` 미생성 또는 응답 없음 | EX-2 (AWS 호출 실패) — 정책 B ASK |
| `audit.md`에 FAILED entry | EX-7 트리거 |
| AWS 룰셋 누락 또는 핀 불일치 | EX-3 (룰셋 mismatch) — 정책 E ABORT |
| `aws-aidlc-version.txt` 변경 감지 | EX-11 (외부 룰북 변경) — 정책 B ASK |

### 8.2 우리 → AWS

| 우리 신호 | AWS 처리 |
|---|---|
| 트리거 취소 | AWS 에이전트에 *작업 중단 명시* (예: "Stop current stage and pause") |
| 재실행 명령 | `execution-plan.md` 갱신 후 AWS 재트리거 |
| 사이클 종료 (정상) | AWS phase·stage 완료 후 자연 종료 (별도 신호 X) |
| 사이클 종료 (예외) | AWS에 PAUSE 신호 (`aidlc-state.md`에 PAUSED 상태 기록 요청) |

### 8.3 EX-3 룰셋 mismatch 재설치 안내

EX-3 트리거 시 사용자 통지 표준:
```
⚠ AWS 룰셋 mismatch 감지
- 영향 레포: {slug}
- 핀 버전: {pin_version}
- 실제 버전: {actual_version or "missing"}

복구 방법:
1. REPO-SETTER 재실행 — 영향 레포에 AWS 룰셋 재설치
2. 또는 ix-ai-dlc/aws-aidlc-version.txt 핀 변경 (PR/머지 필요)

현재 사이클은 ABORT됩니다. 위 복구 후 새 사이클로 재시작.
```

---

## 9. 양방향 참조 맵

| 문서 | 본 명세와의 관계 |
|---|---|
| `agents/REPO-SETTER.md` | §3 룰셋 설치 절차 본 명세 따름 |
| `agents/orchestrator/ROUTING.md` §6 | §6 AWS 산출물 흡수 본 명세 따름 |
| `agents/orchestrator/DECISIONS.md` §4 | §7 execution-plan.md 게이트 형식 본 명세 따름 |
| `agents/orchestrator/ERROR-POLICY.md` §5 | §8 예외 전파 본격 명세 본 명세에 흡수 |
| `specs/CYCLE-LOG.md` §9 | AWS audit 흡수 형식 본 명세 §6.3 따름 |
| `ix-ai-dlc/aws-aidlc-version.txt` | §4 버전 핀 |
| `{각 레포}/aidlc-rules/*` | §3 설치 결과 |
| `{각 레포}/aidlc-docs/*` | §6 흡수 대상 |
| `awslabs/aidlc-workflows` (외부) | §2 원천 |

---

## 부록. AWS phase·stage 빠른 참조

### Inception (7 stages)
| Stage | ALWAYS / CONDITIONAL | 의미 |
|---|---|---|
| Workspace Detection | A | greenfield/brownfield 판단 |
| Reverse Engineering | C | brownfield 시 기존 코드 분석 |
| Requirements Analysis | A | 요구사항 수집·정리 |
| User Stories | C | 사용자 워크플로우 명세 |
| Workflow Planning | A | 어떤 Construction stage 실행할지 결정 |
| Application Design | C | 도메인 모델·아키텍처 설계 |
| Units Generation | C | 멀티 컴포넌트 → 병렬 Unit 분해 |

### Construction (5+ stages)
| Stage | 의미 |
|---|---|
| Functional Design | 기능 설계 |
| NFR Requirements | 비기능 요구사항 (성능·보안·확장성 등) |
| NFR Design | NFR 설계 |
| Infrastructure Design | 인프라 설계 |
| Code Generation | 코드 생성 |
| Build and Test | 빌드 + 테스트 |

### Operations
미구현 (AWS placeholder). 우리 시스템은 STEP 7~9가 일부 커버.

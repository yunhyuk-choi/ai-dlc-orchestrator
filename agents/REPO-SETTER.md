# REPO-SETTER.md — 레포별 셋업 서브 에이전트 룰북

> SETTER 또는 REPO-CREATOR가 호출하는 서브 에이전트 룰북.
> 각 레포 1회 — `.claude/CLAUDE.md` 생성 + AWS 룰셋 설치 + 정합성 검증.
> 위치: `ai-dlc-orchestrator/agents/REPO-SETTER.md`

---

## 0. 컨텍스트

본 에이전트는 SETTER(시스템 부트스트랩)의 **다음 단계** 또는 REPO-CREATOR(추가 레포 생성)의 **마무리 단계**로 호출된다.

```
[SETTER 완료]                  [REPO-CREATOR 완료]
    ↓                                ↓
[REPO-SETTER 호출 — 각 레포마다]    
    ├─ .claude/CLAUDE.md 생성     ← 우리 (시스템 컨텍스트 + AWS 위임)
    ├─ aidlc-rules/ 설치          ← AWS-ADAPTER.md §3 따라
    ├─ aidlc-docs/ 디렉토리 생성
    ├─ (조건부) CICD-SETTER 호출 권고 → 오케스트레이터  ← CI/CD 부착·통합 실행 (탐지·인터뷰 결과 전달)
    ├─ (조건부) REPO-MAP 레포 프로파일 기록 ← CI·릴리스·배포·자격증명·디자인·생산자/소비자
    └─ 정합성 검증
    ↓
[오케스트레이터에 4-튜플 보고]
```

`{공유리포}` = 클론된 `ai-dlc-orchestrator/` 디렉토리 절대 경로. 오케스트레이터가 전달.

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 서브 에이전트 룰북 |
| 호출 주체 | 오케스트레이터 (SETTER 또는 REPO-CREATOR 다음 흐름) |
| 수명 | 레포 단위 **1회**. 추가 레포는 REPO-CREATOR → REPO-SETTER 흐름 |
| 사용자 채널 | 직접 통신 없음. 모든 인터뷰는 *오케스트레이터를 통한다* |
| 위치 | `ai-dlc-orchestrator/agents/REPO-SETTER.md` |

---

## 2. 책임 / 비책임

### 2.1 책임

1. 레포 사전 조건 체크 (`.git/` 존재, 권한 등)
2. 레포 단위 인터뷰 수행 — 응답 언어, 프로젝트 메타데이터, **코드·깃 컨벤션**, **(조건부) 레포 프로파일**(CI·릴리스·**배포**·자격증명 사전조건·디자인 표면·생산자/소비자), 자동 탐지·추천 검증
3. `{레포}/.claude/CLAUDE.md` 생성 (`CLAUDE.template.md` 채움) + **repo-scope 동반 템플릿(`STACK`/`CODING`/`FRAMEWORK`) materialize**
4. AWS 룰셋 설치 — `AWS-ADAPTER.md §3` 절차 따름
5. `{레포}/aidlc-docs/` 빈 디렉토리 생성 (AWS 산출물 영역)
6. (조건부) Stage 1 산출물 Extension 적용 — *변환된 extension 템플릿이 `ai-dlc-orchestrator/templates/extensions/`에 준비된 경우만*
7. (조건부) 보유 시 레포 프로파일을 **REPO-MAP `{REPO_PROFILES}`** 해당 슬러그 서브섹션에 기록 (자격증명은 *이름·스코프만*, 값 금지)
8. (조건부) CI/CD 보유·필요로 판정되면 **CICD-SETTER 호출을 오케스트레이터에 권고·요청** (CI/CD 부착·통합 *실행* — 본 에이전트는 기록만 하지 않고 실행 주체 호출을 권고; 원칙 7 — 직접 피어 호출 X)
9. 정합성 자체 체크 + **공유 산출물 깃 트래킹(POLICY-TRACKING)** + 오케스트레이터에 4-튜플 보고

### 2.2 비책임 (다른 산출물에 위임)

| 영역 | 위임 대상 |
|---|---|
| 시스템 부트스트랩 (메타 레포·ORCHESTRATOR.md·REPO-MAP.md) | SETTER |
| 추가 레포 생성 (디렉토리 생성·git init) | REPO-CREATOR |
| AWS 룰셋 설치 절차 본문 | `specs/AWS-ADAPTER.md §3` |
| CI/CD 부착·통합 *실행* (파이프라인 분석·생성·게이트 통합) | `agents/CICD-SETTER.md` (피어 에이전트) — 본 에이전트는 *호출을 오케스트레이터에 권고*(원칙 7), 직접 부착 안 함 |
| 실행 환경 배포 *실행* | `agents/DEPLOY-AGENT.md` (피어) — 본 에이전트는 배포 프로파일만 *포착·기록*, 배포는 안 함 |
| Stage 1 산출물의 Extension 변환 자체 | 별도 큐 작업 (Stage 2 잔여) — REPO-SETTER는 *변환 결과를 적용*만 |
| 사이클 로깅 형식 | `specs/CYCLE-LOG.md` |
| 사이클 종료 후처리 | CYCLE-CLOSER |
| 코드 생성·테스트·빌드 | AWS AI-DLC (각 레포 `aidlc-rules/`) |

---

## 3. 핵심 원칙

- **원칙 1**: 호출 시점·책임 분리 — 레포별 셋업은 *레포마다 1회*. 시스템 부트스트랩(SETTER)·추가 생성(REPO-CREATOR)과 분리.
- **원칙 4**: AI 자율 실행, 사용자는 의미 결정만 — 인터뷰는 멀티초이스+`[Answer]:` 태그
- **원칙 6**: 단일 원천 — `.claude/CLAUDE.md` 내용은 `CLAUDE.template.md` + 인터뷰 응답에서 *파생*만
- **원칙 7**: 오케스트레이터 호출 책임 — 본 에이전트 직접 호출 X
- **원칙 8**: 공유 룰북·템플릿은 깃 단일 원천 — `CLAUDE.template.md` 변경은 PR/머지

---

## 4. 입출력

### 4.1 입력 (오케스트레이터로부터)

| 필드 | 내용 |
|---|---|
| 트리거 출처 | SETTER 다음 / REPO-CREATOR 다음 |
| `{공유리포}` 절대 경로 | 클론된 `ai-dlc-orchestrator/` |
| 대상 레포 절대 경로 | `{레포 경로}` |
| 레포 슬러그 | `REPO-MAP.md`의 레포 식별자 |
| 레포 메타 (기본) | 역할 / 도메인 / 의존 — REPO-MAP에서 파생 |
| AWS 버전 핀 | `aws-aidlc-version.txt` 값 |
| 사용자 인터뷰 응답 | RP1.x ~ RP3.6.x (인터뷰 결과 — 메타 + 컨벤션 + 조건부 레포 프로파일: CI·릴리스·**배포**·자격증명·디자인·생산자/소비자) |

### 4.2 출력 (오케스트레이터에 보고 — 4-튜플 표준)

1. **생성 파일 경로[]** (+ POLICY-TRACKING 커밋 해시)
   - `{레포}/.claude/CLAUDE.md`
   - `{레포}/.claude/STACK.md`·`CODING.md`·`FRAMEWORK.md` (RP5.5 동반 템플릿)
   - `{레포}/aidlc-rules/` (전체 트리)
   - `{레포}/aidlc-docs/` (빈 디렉토리)
2. **정합성 체크 결과** — §6 자체 체크 항목별 통과/실패
3. **인터뷰 응답 원본** — RP1.x ~ RP3.6.x 사용자 답변 (조건부 레포 프로파일 — CI·릴리스·배포·자격증명·디자인·생산자/소비자 포함)
4. **권고 다음 단계** — (조건부) **CICD-SETTER 호출 권고**(CI/CD 보유 시 — 모드 힌트 + 전달 입력, RP7.7) / (조건부) DEPLOY-AGENT 후속 배포 필요(배포 레포) / 다른 레포 REPO-SETTER 또는 운영 모드 진입

> 1번 생성·갱신 파일 목록에는 — **레포 프로파일을 보유한 경우** — `{메타 레포}/REPO-MAP.md`(프로파일 블록 `{REPO_PROFILES}`의 해당 슬러그 서브섹션 추가·갱신, RP7.6)도 포함된다.

---

## 5. 실행 절차

```
[페이즈 1] 사전 조건 체크          → RP0
[페이즈 2] 인터뷰                  → RP1 ~ RP3.6 (메타 + 컨벤션 + 조건부 레포 프로파일)
[페이즈 3] AWS 룰셋 설치           → RP4
[페이즈 4] 우리 .claude/ 생성       → RP5 + RP5.5 (동반 템플릿)
[페이즈 5] Extension 적용 (조건부) → RP6
[페이즈 6] 검증 & 보고             → RP7
[페이즈 7] 깃 트래킹 (공유 산출물)  → RP7.5
[페이즈 7.6] REPO-MAP 프로파일 기록 (조건부) → RP7.6
[페이즈 7.7] CICD-SETTER 호출 권고 (조건부) → RP7.7
[페이즈 8] 종료                    → RP8
```

### RP0 — 사전 조건 체크 (자동, 인터뷰 없음)

- 대상 레포 경로 존재 확인
- `{레포}/.git/` 존재 확인 (필수)
- `{레포}/.claude/` 또는 `{레포}/aidlc-rules/` 이미 존재 시 → 충돌 보고 (덮어쓰기 사용자 컨펌 필요)
- `{공유리포}/templates/CLAUDE.template.md` 존재 확인
- `{공유리포}/aws-aidlc-version.txt` 존재 확인
- 실패 시 오케스트레이터에 보고 후 종료

### RP1 — 응답 언어 인터뷰

| ID | 질문 | 기본/추천 |
|---|---|---|
| RP1.1 | 이 레포의 응답 언어? | 한국어 (시스템 디폴트 — `dlc-meta/ORCHESTRATOR.md`에서 추출) |

각 레포마다 *별도 응답 언어* 허용 (예: 프론트 = 한국어, 백엔드 글로벌팀 = 영어). 명시 없으면 시스템 디폴트.

### RP2 — 프로젝트 메타 인터뷰

> **인터뷰 전 자동 탐지 (RP2·RP3 공통 — 질문하기 전에 먼저 수행)**: 레포에 *이미 존재하는* 컨벤션 원천을 스캔해 사용자에게 "이게 맞나요/조정할까요?" 형태로 제시한다. 추측을 줄이고 사용자는 의미 결정만 한다 (원칙 4). 탐지 대상은 *예시이며 전수 목록 아님* — 레포 생태계에 맞게 확장:
>
> - 기존 에이전트 룰 파일 (예: `CLAUDE.md` / `AGENTS.md`)
> - 에디터·린트·포맷 설정 (예: `.editorconfig`, eslint/prettier/ruff/gofmt 등 린터·포매터 설정 파일)
> - 기여·스타일 가이드 (예: `CONTRIBUTING.*`, `STYLEGUIDE.*`)
> - 최근 커밋 메시지 패턴 (예: 컨벤셔널 커밋 접두사·이슈 키 규약 — 최근 N개 커밋 로그에서 추출)
> - 메타·스택에 영향 주는 매니페스트 (예: `package.json`, `requirements.txt`, `go.mod` 등 — RP2.x 자동 추천에 이미 사용)
> - **(조건부 — 레포 프로파일 신호)** 다음을 탐지해 RP3.6 *자동 추천*으로 흘려보낸다 (모두 *예시*, 전수 아님 — 동치 수단 대체 가능). **없으면 해당 프로파일 필드를 생략**(추측 금지 — POLICY-RELEASE §1.1 "탐지하되 추정 안 함"):
>   - **CI 설정 파일** (예: 임의 CI 시스템의 파이프라인·워크플로우 정의 파일) → CI 게이트 보유 신호. 본문에서 *차단(required) 게이트* + *사람 승인 게이트*(예: 시각회귀 리뷰 체크) 표식도 함께 스캔. 파이프라인에 **배포 스테이지·잡**이 정의돼 있으면 배포 보유 신호로도 흘려보낸다(아래 배포 항목).
>   - **퍼블리시·릴리스 잡/스테이지** 또는 **매니페스트의 레지스트리 좌표**(예: 퍼블리시 대상이 명시된 패키지 메타데이터) → 퍼블리시 산출물 보유 신호.
>   - **(조건부) 배포 설정·IaC 신호**(예: 인프라 정의 파일·배포 디스크립터·환경별 설정, CI의 배포 잡/스테이지, 환경 엔드포인트·헬스체크 경로 정의) → 실행 환경 배포 보유 신호. RP3.6 *배포* 질문 자동 추천으로 흘려보낸다. **없으면 배포 필드 생략**(라이브러리·산출물만 퍼블리시하는 레포는 정상 — POLICY-DEPLOY §1.1 "탐지하되 추정 안 함"). 배포 잡이 참조하는 자격증명·환경 변수 *이름·스코프*도 함께 스캔(값 금지).
>   - **디자인 표면 참조**(예: 임의의 디자인 툴·파일·보드 링크, 또는 별도 디자인·UX 스펙 산출물 경로) → 디자인↔코드 동기화 대상 후보.
>   - **CI 설정에 문서화된 자격증명·스코프 요구**(예: 잡이 참조하는 시크릿·변수 *이름*, 필요 스코프 주석) → 자격증명 사전조건 후보. **이름·스코프만 — 값은 절대 수집·기록 금지**.
>
> 탐지 결과는 RP2(메타)·RP3.5(컨벤션)·RP3.6(레포 프로파일) 질문의 *자동 추천 값*으로 흘려보낸다. 탐지 못 하면 빈 채로 질문(추측 금지). **탐지된 프로파일 신호는 사용자에게 "이게 맞나요?"로 제시해 확인받는다 (원칙 4).**

REPO-MAP에서 자동 추천 + 사용자 검증:

| ID | 질문 | 자동 추천 |
|---|---|---|
| RP2.1 | 프로젝트 풀네임 (PROJECT_FULL_NAME)? | `package.json` name·description / README 1번째 헤더 |
| RP2.2 | 프로젝트 짧은 이름 (PROJECT_NAME)? | 레포 슬러그 |
| RP2.3 | 프로젝트 설명 (PROJECT_DESCRIPTION)? | `package.json` description / README 1번째 단락 |
| RP2.4 | 런타임·스택 요약 (STACK_SUMMARY)? | `package.json` engines + dependencies / `requirements.txt` / `go.mod` 등 자동 추출 |

자동 추천 적합 시 → 멀티초이스 "그대로 사용" 옵션. 다를 시 → 사용자 입력.

### RP3 — 참조 파일 목록 결정

| ID | 질문 | 디폴트 |
|---|---|---|
| RP3.1 | `.claude/CLAUDE.md`에서 참조할 파일 목록? | "@.claude/CLAUDE.md, AWS는 `aidlc-rules/aws-aidlc-rules/core-workflow.md` 자동 로드" 기본. 추가 명시 가능 |

### RP3.5 — 컨벤션 인터뷰 (코드 / 깃)

> RP2 *인터뷰 전 자동 탐지* 결과를 자동 추천으로 제시 → 사용자 확인·조정. 탐지 못 한 항목은 빈 채로 질문(추측 금지). 응답은 RP5의 `{TOP_FORBIDDEN_RULES}`·컨벤션 변수와 RP5.5 repo-scope 템플릿 변수의 출처가 된다.

| ID | 질문 | 자동 추천 (탐지 원천) |
|---|---|---|
| RP3.5.1 | 이 레포의 **기존 코드 컨벤션**? (네이밍·포맷·구조·금지 패턴 등) | 탐지된 에디터·린트·포맷 설정 + CONTRIBUTING/STYLEGUIDE + 기존 에이전트 룰 파일에서 요약 |
| RP3.5.2 | 이 레포의 **깃/커밋 컨벤션**? (커밋 메시지 형식·브랜치 규칙 등) | 최근 커밋 메시지 패턴 + CONTRIBUTING에서 추출 |
| RP3.5.3 | 위 중 **가장 자주 어기는 절대 금지 규칙 N개** (`{TOP_FORBIDDEN_RULES}`)? | RP3.5.1·RP3.5.2에서 사용자가 핵심으로 표시한 항목 |

자동 추천 적합 시 → "그대로 사용" 멀티초이스. 다를 시 → 사용자 입력. **전부 미탐지·미응답이면** `{TOP_FORBIDDEN_RULES}`는 시스템 디폴트(또는 명시적 "없음")로 두되, *과거의 "best-effort 빈" 스텁이 아니라* 탐지·응답 결과를 우선 채운다.

### RP3.6 — 레포 프로파일 인터뷰 (CI·릴리스·배포·자격증명·디자인·생산자/소비자) — **조건부**

> **전부 조건부.** RP2 *인터뷰 전 자동 탐지*의 프로파일 신호를 자동 추천으로 제시 → 사용자 확인·조정 (원칙 4). **레포가 해당 항목을 보유하지 않으면 그 질문을 깔끔히 건너뛴다** — "없음"으로 두고 REPO-MAP 프로파일에서 해당 필드를 생략한다 (범용 툴 전제 — CI·릴리스·배포·디자인 표면이 없는 레포도 정상; POLICY-RELEASE §1.1 / POLICY-DEPLOY §1.1).
> 본 RP 응답은 **REPO-MAP의 레포 프로파일 블록(`{REPO_PROFILES}`)** 의 해당 슬러그 서브섹션으로 기록된다(아래 RP7.6). 연계: CI 게이트·릴리스·생산자/소비자·자격증명은 `specs/CICD-RELEASE-ADAPTER.md`(**POLICY-RELEASE**) / 배포 타깃·전략·환경 티어·prod 트리거·배포 자격증명은 `specs/DEPLOY-ADAPTER.md`(**POLICY-DEPLOY**) + prod 트리거 사람 게이트 **A-4**(DEPLOY-AGENT가 배포 시 소비) / 디자인 표면의 정규·동기화 방향은 `specs/SYSTEM-WORKFLOW.md` §3 + DECISIONS **A-2** / 채택 게이트는 **A-5** / 자격증명 스코프 진단은 **EX-13**.

| ID | 질문 | 자동 추천 (탐지 원천) | 미보유 시 |
|---|---|---|---|
| RP3.6.1 | 이 레포에 **CI/CD가 있는가**? 있으면 머지를 *차단(blocking)* 하는 필수 게이트(예: 빌드·테스트·린트)와 *사람 승인 게이트*(예: 시각회귀 리뷰)? | 탐지된 CI 설정 파일 + 차단·승인 게이트 표식 | "없음" → 필드 생략 |
| RP3.6.2 | 이 레포가 **산출물을 퍼블리시**하는가? 릴리스 방식(버전 범프·태그·CI 퍼블리시 등)과 대상 **레지스트리·엔드포인트**(검증용 좌표)? | 탐지된 퍼블리시·릴리스 잡 + 매니페스트 레지스트리 좌표 | "없음" → 필드 생략 |
| RP3.6.3 | 이 레포의 CI·릴리스·자동화가 요구하는 **자격증명의 이름·스코프·역할**? (예: 퍼블리시 쓰기 스코프, 상태 쓰기 스코프, 레지스트리 역할) — **이름·스코프만, 값 금지** | CI 설정에 문서화된 시크릿·변수 *이름*·스코프 주석 | "없음" → 필드 생략 |
| RP3.6.4 | 이 레포에 대응하는 **디자인 표면**(임의의 디자인 툴·파일·보드 또는 별도 스펙 산출물)이 있는가? 있으면 그 위치 + **정규(canonical) 원천**(코드 vs 디자인 등) + **동기화 방향**? | 탐지된 디자인·UX 스펙 참조 | "없음" → 필드 생략 |
| RP3.6.5 | 이 레포는 다른 레포가 소비하는 **공유 생산자**인가, 아니면 다른 레포 산출물의 **소비자**인가? (상대 슬러그 — A-5 채택 게이트 입력) | 매니페스트 의존(소비)·레지스트리 퍼블리시(생산) + REPO-MAP 의존 컬럼 | "독립" → 필드 생략 |
| RP3.6.6 | 이 레포가 **실행 환경에 배포**하는가? 배포하면 — **타깃**(어디로 — 예: 실행 환경·플랫폼) / **방식·전략**(예: rolling·blue-green·canary·recreate) / **환경 티어**(예: dev·staging·prod) / **prod 트리거 주체**(누가 prod 배포를 승인·트리거 — A-4 사람 게이트) / **배포 자격증명 이름·스코프**(예: 환경 접근 키·배포 권한 롤 — **이름·스코프만, 값 금지**)? | 탐지된 배포 설정·IaC·CI 배포 잡·환경 엔드포인트 + 배포 잡 참조 변수 이름 | "없음"(라이브러리·퍼블리시 전용) → 배포 필드 생략 |

- 자동 추천 적합 시 → "그대로 사용" 멀티초이스. 다를 시 → 사용자 입력. 보유하지 않는 항목은 **건너뛰고** REPO-MAP 프로파일에서 해당 필드를 생략한다(빈 자리 표시자 잔존 금지).
- **자격증명은 이름·스코프·역할만 — 값은 절대 인터뷰·기록하지 않는다.** 시크릿 *값*은 머신별 `.env`(gitignore)에만 존재한다 (POLICY-TRACKING / 자격증명 경계). 토큰 발급·스코프 부여·회전은 *사람 게이트* — REPO-SETTER가 값을 받지 않는다.
- **디자인 동기화 방향**은 사이클마다 A-2(항상 컨펌)로 재확인되는 결정이다 — 여기엔 *현재 합의된 기본*만 기록하며, 본 에이전트가 방향을 자동 판정하지 않는다(SYSTEM-WORKFLOW §3).
- **배포(RP3.6.6)**: 배포 프로파일은 **DEPLOY-AGENT가 배포 시점에 소비**한다(REPO-MAP `{REPO_PROFILES}` deploy 필드 — POLICY-DEPLOY). **prod 트리거 주체**는 *누가 prod 배포를 승인·트리거하는지* 를 기록하는 것 — production은 비가역·고영향이라 **A-4 사람 게이트**가 적용되며, 본 에이전트는 그 *주체만 포착*하고 배포 자체는 실행하지 않는다. 배포 자격증명도 **이름·스코프만**(발급·회전은 사람 — 자격증명 경계). 배포 신호가 없으면(라이브러리·퍼블리시 전용 레포) 배포 필드를 통째로 생략한다.

### RP4 — AWS 룰셋 설치

**`specs/AWS-ADAPTER.md §3.2` 절차 그대로 수행**:

```bash
# 1. 핀 버전 읽기
PIN_VERSION=$(cat {공유리포}/aws-aidlc-version.txt)

# 2. awslabs/aidlc-workflows 다운로드 (해당 버전)
# (실제 명령은 환경에 따라 — git clone --branch 또는 release zip)

# 3. {레포}/aidlc-rules/ 에 압축 해제
mkdir -p {레포}/aidlc-rules
# 다운로드된 룰셋 복사

# 4. {레포}/aidlc-docs/ 디렉토리 생성
mkdir -p {레포}/aidlc-docs
```

설치 후 `specs/AWS-ADAPTER.md §3.3` 정합성 검증 항목 실행.

### RP5 — 우리 `.claude/CLAUDE.md` 생성

- 원본 템플릿: `{공유리포}/templates/CLAUDE.template.md`
- 변수 채움:

| 변수 | 출처 |
|---|---|
| `{PROJECT_NAME}` | RP2.2 |
| `{PROJECT_FULL_NAME}` | RP2.1 |
| `{PROJECT_DESCRIPTION}` | RP2.3 |
| `{STACK_SUMMARY}` | RP2.4 |
| `{REFERENCE_FILES}` | RP3.1 |
| `{TOP_FORBIDDEN_RULES}` | RP3.5.3 (탐지+응답한 절대 금지 규칙). 전부 미탐지·미응답 시에만 시스템 디폴트/"없음" |

- 산출: `{레포}/.claude/CLAUDE.md`

**주의 (v3 단순화 결정)**: `.claude/CLAUDE.md`는 *시스템 컨텍스트 + AWS 위임 안내*만 담음. 레포 내부 워크플로우 본문은 *AWS AI-DLC 위임* — `.claude/CLAUDE.md`가 짧고 단순.

### RP5.5 — repo-scope 동반 템플릿 materialize (`.claude/` 컴패니언)

`.claude/CLAUDE.md`가 참조하는 *레포 단위* 동반 문서를 인터뷰 응답에서 materialize한다. 본 RP은 **레포 스코프로 판정된 템플릿만** 생성한다(아래 매핑). 시스템 스코프 템플릿은 본 RP 대상이 아니다(§아래 주의).

**template → instance 매핑 (레포 스코프)**:

| 원본 템플릿 (`{공유리포}/templates/`) | 인스턴스 경로 | 채움 변수 출처 |
|---|---|---|
| `STACK.template.md` | `{레포}/.claude/STACK.md` | `{STACK_TABLE}`·`{DIRECTORY_TREE}`·`{COMPONENT_HIERARCHY}`·`{FILE_LOCATION_RULES}`·`{TEST_RULES}`·`{EXTERNAL_INTEGRATIONS}`·`{VCS_RULES}` ← RP2.4(스택)·자동 탐지(디렉토리·매니페스트)·RP3.5.1(코드 컨벤션)·RP3.5.2(깃 컨벤션) |
| `CODING.template.md` | `{레포}/.claude/CODING.md` | `{CODING_RULES}` ← RP3.5.1 + 탐지된 린트·포맷·스타일 가이드 |
| `FRAMEWORK.template.md` | `{레포}/.claude/FRAMEWORK.md` | `{FRAMEWORK_PATTERNS}` ← RP2.4 스택에서 식별된 프레임워크 + RP3.5.1 |

- **생성 방식**: POLICY-ENCODING 준수 — 직접 UTF-8(no-BOM, LF) 쓰기 + materialize 후 손상 스캔·재생성(RP6 인코딩 절차와 동일). POLICY-TEMPLATE-ADHERENCE 준수 — 위 템플릿에서만 파생, 자유 작성 금지.
- 채울 값이 없는 변수는 빈 자리로 두지 말고 "해당 없음/미정"으로 명시(자리 표시자 `{...}` 잔존 금지 — RP7 체크).
- `{REFERENCE_FILES}`(RP3.1)에 위 생성된 동반 파일을 포함하도록 RP5 참조 목록과 정합 유지.

> **주의 — 시스템 스코프 판정(SETTER 위임)**: `WORKFLOW.template.md`와 `DESIGN.template.md`는 *레포 스코프가 아니라 시스템 스코프*로 판정해 본 RP5.5에서 제외했다. 근거: 레포 내부 워크플로우는 AWS AI-DLC에 위임(v3 단순화)되고, 두 템플릿은 시스템 레벨로 재포지셔닝되어 `specs/SYSTEM-WORKFLOW.md`(WORKFLOW) 및 시스템 `DESIGN` 가이드(STEP 2·3 동반)로 이미 흡수되었음(SYSTEM-WORKFLOW.md §6 참조). 이들의 인스턴스화는 시스템 부트스트랩(SETTER) 책임 — REPO-SETTER 범위 밖. SETTER-owner가 시스템 스코프로 처리할 것.

### RP6 — Stage 1 산출물 Extension 적용 (조건부 + 위험 ABORT)

**조건**: `{공유리포}/templates/extensions/` 안에 *변환된 Extension 템플릿*(`*.template.md`)이 존재하는 경우만.

| Extension 카테고리 | 변환 원천 (Stage 1) | 적용 대상 |
|---|---|---|
| `templates/extensions/quality/checklist.template.md` | CHECKLIST.template.md | `{레포}/aidlc-rules/aws-aidlc-rule-details/extensions/quality/` |
| `templates/extensions/coding/coding.template.md` (→ `{lang}/` materialize) | CODING.template.md (언어별 변종) | `{레포}/aidlc-rules/aws-aidlc-rule-details/extensions/coding/` |
| `templates/extensions/framework/framework.template.md` (→ `{name}/` materialize) | FRAMEWORK.template.md (프레임워크별 변종) | `{레포}/aidlc-rules/aws-aidlc-rule-details/extensions/framework/` |

Extension 변환은 D-Stage2-18에서 완료 (`templates/extensions/`, `*.template.md`). 본 RP6은 *변환 결과 적용*(`{lang}`/`{name}` materialize + 변수 채움 + 복사)만.

**인코딩 안전 materialize·복사 (POLICY-ENCODING 필수 준수)**:

materialize/복사로 생성되는 모든 파일(예: `extensions/quality/checklist.md` 등)은 **UTF-8 no-BOM + LF**로 출력한다.

- 템플릿 본문에 비-ASCII(예: 한국어 산문)가 포함되므로, **반드시 직접 UTF-8 파일 쓰기**로 생성한다. 변수 치환 결과를 **OS 콘솔·쉘 파이프라인으로 흘려보내지 말 것** — 로케일 의존 콘솔(예: Windows CP949 등)은 비-ASCII를 mojibake로 깨뜨린다.
- materialize 직후 **검증 단계**를 수행: 생성된 *모든* 파일을 스캔해 손상 신호 — U+FFFD(`�`) 치환문자 / 비-ASCII 자리의 엉뚱한 `?` / BOM 존재 — 를 탐지한다. 깨진 파일이 하나라도 있으면 **직접 UTF-8 쓰기로 재생성**하고 재검증한다. 재생성으로도 클린하지 않으면 ABORT(아래 위험 신호 분기 따름).
- 원천 템플릿은 그대로 두고, *생성된 인스턴스만* 검증·재생성 대상이다. (실제 사고: 깨끗한 템플릿은 멀쩡한데 생성된 `extensions/quality/checklist.md`가 CP949 mojibake로 떨어진 사례 — 콘솔 경유 쓰기가 원인.)

**상태별 분기**:

| 상태 | 처리 |
|---|---|
| **정상 미준비** (`{공유리포}/templates/extensions/` 디렉토리 없음 또는 비어 있음) | RP6 *스킵* — 로그에만 기록. 진행 |
| **정상 준비됨** (디렉토리 + 유효 파일 존재) | 정상 적용 |
| **위험 신호 감지** — 부분 손상 / 카테고리 일부만 존재 / 권한 불일치 / 버전 메타 불일치 | **ABORT** — EX-3 또는 신규 예외로 보고. 사용자 안내 후 새 사이클 권장 |

위험 신호 감지 = "위험하면 미리 끊어야" 원칙. 부분 적용보다 명시적 중단이 안전.

### RP7 — 정합성 자체 체크 + 오케스트레이터 보고

**자체 체크 항목**:
- `.claude/CLAUDE.md` 존재 + 변수 모두 채워졌나 (`{...}` 자리 표시자 남아 있지 않음)
- RP5.5 동반 템플릿(`.claude/STACK.md`·`CODING.md`·`FRAMEWORK.md`) 생성됨 + 변수 모두 채워짐(`{...}` 잔존 X)
- 생성·복사된 모든 파일 인코딩 클린 (POLICY-ENCODING — U+FFFD/엉뚱한 `?`/BOM 없음)
- AWS 룰셋 설치 정합성 (AWS-ADAPTER.md §3.3 항목)
- `aidlc-docs/` 빈 디렉토리 생성됨
- Extension 적용 시 — 적용 경로·파일 모두 존재
- AWS 버전 핀과 실제 설치 버전 일치 (mismatch 시 EX-3 예외 트리거)
- **(조건부) 레포 프로파일** — RP3.6에서 보유로 확인된 항목이 REPO-MAP `{REPO_PROFILES}` 해당 슬러그 서브섹션에 기록됨(RP7.6) + 빈 `{...}` 자리 표시자 잔존 X + **자격증명에 시크릿 *값*이 적히지 않음**(이름·스코프·역할만). 보유 항목 없으면 스킵 로그.

**오케스트레이터 보고 (4-튜플)**:
1. 생성 파일 절대 경로 목록 (조건부 — REPO-MAP 프로파일 갱신 포함, RP7.6)
2. 정합성 체크 결과 (항목별 통과/실패 + 실패 사유)
3. 인터뷰 응답 원본 (RP1.x ~ RP3.6.x — 조건부 레포 프로파일 포함)
4. 권고 다음 단계 — 다른 레포 REPO-SETTER 호출 또는 운영 모드 진입

### RP7.5 — 공유 산출물 깃 트래킹 (POLICY-TRACKING)

본 에이전트가 생성한 산출물은 **팀이 단일 원천을 공유해야 하는 SHARED 산출물** — 반드시 git-track + 커밋한다. (실제 사고: 트래킹 단계가 아예 없어 한 레포는 룰 디렉토리 전체를 gitignore해 팀원별로 룰이 갈라졌음.)

**[1] fetch 선행 (필수)**: 모든 git 작업 전에 `git fetch origin --prune`로 원격 최신을 확인하고 현재 기준 브랜치 위에서 작업한다. (SYSTEM-WORKFLOW.md §3 git sync 가드 정합 — stale base 커밋 유실 방지.)

**[2] `.gitignore` 조정 — 개인 파일만 무시**:
- 무시(개인): 시크릿(예: `.env*`), 머신 로컬 설정(예: 로컬 머신 한정 IDE/도구 설정)만.
- **절대 금지**: 공유 룰 디렉토리(예: `aidlc-rules/`) 또는 공유 동반 문서를 *통째로 무시*하는 패턴. 이미 그런 패턴이 있으면 제거·교정한다.

**[3] git-add + 커밋 (SHARED 산출물)**:
- `{레포}/aidlc-rules/` (AWS 룰셋 + 적용된 Extension)
- 프로젝트 공유 에이전트 룰 파일 `{레포}/.claude/CLAUDE.md`
- 생성된 컨벤션·체크리스트·동반 문서 (`.claude/STACK.md`·`CODING.md`·`FRAMEWORK.md`, 적용된 `extensions/quality/checklist.md` 등)
- (`aidlc-docs/`는 AWS 산출물 영역 — 트래킹 정책은 레포 관습 따름. 빈 디렉토리 유지가 필요하면 `.gitkeep`만.)

**[4] 커밋 검증 (필수)**: 커밋 후 `git log`/`git status`로 위 SHARED 산출물이 실제 커밋에 포함됐는지 확인한다. 누락·미스테이지 발견 시 재시도. 공유 브랜치 force-push 금지.

생성 파일 경로·커밋 해시를 RP7 4-튜플 첫 필드(생성 파일 경로[])와 함께 오케스트레이터에 보고한다.

### RP7.6 — REPO-MAP 레포 프로파일 기록 (조건부, POLICY-TRACKING)

> **조건부** — RP3.6에서 *보유로 확인된 프로파일 항목이 하나라도 있을 때만* 수행. 전부 "없음/독립"이면 본 RP을 스킵하고 로그에만 기록한다.

RP3.6 응답을 **`{메타 레포}/REPO-MAP.md`의 레포 프로파일 블록(`{REPO_PROFILES}`)** 에 *이 레포 슬러그* 서브섹션으로 기록한다. 이곳이 프로파일의 단일 원천 — `.claude/` 문서에 중복 기록하지 않는다(원칙 6; REPO-MAP이 도메인·레포 정보 단일 원천). 단, 디자인 표면·컨벤션이 `.claude/STACK.md`의 `{EXTERNAL_INTEGRATIONS}`/`{VCS_RULES}`와 자연히 겹치면 *교차 참조*만 두고 값 중복은 피한다.

- **원천 형식**: `{공유리포}/templates/REPO-MAP.template.md`의 "레포 프로파일" 블록 + `{REPO_PROFILES}` 서브섹션 형식(슬러그 헤딩 + 보유 필드만). POLICY-TEMPLATE-ADHERENCE — 템플릿 형식에서 생성, 자유 형식 금지.
- **기록 대상 필드** (보유한 것만, 없으면 *행 생략*): CI/CD(차단·사람 승인 게이트) / 릴리스·퍼블리시(방식·레지스트리 좌표) / **배포(타깃·방식/전략·환경 티어·prod 트리거 주체·배포 자격증명 이름·스코프 — 배포하지 않는 레포는 생략)** / 자격증명 사전조건(**이름·스코프·역할만**) / 디자인 표면(위치·정규 원천·동기화 방향) / producer·consumer(상대 슬러그). 연계: POLICY-RELEASE(`specs/CICD-RELEASE-ADAPTER.md`) §2·§4·§5·§6 / **POLICY-DEPLOY(`specs/DEPLOY-ADAPTER.md`) §2·§3·§4·§9 + DECISIONS A-4(prod 트리거 사람 게이트) — 이 필드는 DEPLOY-AGENT가 배포 시 소비** / SYSTEM-WORKFLOW §3 + DECISIONS A-2(디자인 동기화)·A-5(채택) / EX-13(자격증명 스코프).
- **배포 자격증명 경계**: 배포 자격증명도 **이름·스코프만** — 값 금지. prod 트리거 주체는 *사람 식별*(역할·주체)만 기록하며 본 에이전트가 prod 배포를 트리거하지 않는다(A-4는 배포 시점 DEPLOY-AGENT·오케스트레이터가 적용).
- **시크릿 경계 재확인**: 자격증명은 **이름·스코프·역할만**. **값은 절대 기록 금지** — 값은 머신별 `.env`(gitignore)에만 (POLICY-TRACKING / 자격증명 경계). REPO-MAP은 추적되는 공유 문서이므로 값이 새면 시크릿 누출이다.
- **쓰기 방식 (POLICY-ENCODING 필수)**: REPO-MAP은 공유 추적 문서 — 직접 UTF-8(BOM 없음) 쓰기, 줄바꿈은 대상 파일 컨벤션 따름, 로케일 의존 셸 출력 금지, 기록 후 손상(U+FFFD/`?`/BOM) 검증.
- **갱신 충돌 안전**: REPO-MAP은 팀 공유(`dlc-meta`) — **[1] git fetch 선행**(RP7.5 [1]과 동일 가드) 후 해당 슬러그 서브섹션을 *추가/갱신*하고, 다른 레포 서브섹션·핵심 표(`{REPO_TABLE}`)는 건드리지 않는다. 슬러그 서브섹션이 이미 있으면 *그 서브섹션만* 갱신(중복 헤딩 생성 금지). [3] git-add + 커밋 + [4] 커밋 검증은 RP7.5 절차와 동일(공유 산출물).

기록·갱신한 REPO-MAP 경로·커밋 해시를 RP7 4-튜플 첫 필드에 포함해 보고한다.

### RP7.7 — CICD-SETTER 호출 권고 (조건부)

> **조건부** — RP3.6.1에서 *CI/CD를 보유·필요로 판정한 경우에만* 수행. CI/CD가 없고 불필요한 레포는 본 RP을 스킵하고 로그에만 기록한다(범용 툴 전제 — POLICY-RELEASE §1.1).

CI/CD는 *기록만으로 끝나지 않는다* — 실제 **부착·통합 실행**이 필요하다. 그 실행 주체는 피어 에이전트 **`CICD-SETTER`**(레포별 CI/CD 부착·통합 실행자)다. **원칙 7(서브 에이전트는 피어를 직접 호출하지 않음)** 에 따라, 본 에이전트는 CICD-SETTER를 *직접 호출하지 않고* **오케스트레이터에 호출을 권고·요청**한다 — 오케스트레이터가 CICD-SETTER를 호출한다.

- **권고에 담을 입력** (CICD-SETTER §4.1 입력 형식): 대상 레포 슬러그·절대 경로 / `{공유리포}` / **RP3.6.1 CI 프로파일 탐지·인터뷰 결과**(기존 CI 설정·차단/사람 승인 게이트 신호) / 레포 스택 요약(RP2.4) / (판정됐으면) 기존-vs-신규-vs-사용자제공 모드 힌트.
- **모드 힌트 도출** (CICD-SETTER C1이 최종 판정하되, RP3.6.1·자동 탐지로 *권고 모드*를 함께 전달): 기존 CI 설정 *탐지됨* → **기존 통합(integrate)** / CI 설정 *없음* → **신규 부착(attach)** / 사용자가 설정 *직접 제공* → **사용자 제공 분석(analyze)**.
- **권고 위치**: RP7 4-튜플 4번(**권고 다음 단계**)에 "이 레포에 CICD-SETTER 호출 필요(모드 힌트 + 전달 입력)"로 담아 오케스트레이터에 보고한다. 오케스트레이터가 CICD-SETTER를 호출하면, CICD-SETTER가 REPO-MAP `{REPO_PROFILES}` CI/CD 필드를 *통합 결과로 보강*한다(RP7.6에서 본 에이전트가 부분 기록한 CI/CD 필드를 CICD-SETTER가 갱신 — 중복 헤딩 금지).
- **배포 후속**: 레포가 배포까지 한다면(RP3.6.6) CICD-SETTER 부착 후 배포 단계는 **DEPLOY-AGENT**가 별도 호출로 담당한다(파이프라인 *배선*은 CICD-SETTER, 실행 환경 *배포*는 DEPLOY-AGENT — 책임 분리). 본 에이전트는 그 후속 필요도 권고에 함께 명시할 수 있다.

> **AWS 룰셋 설치(RP4)와의 차이**: RP4는 *스펙 절차(AWS-ADAPTER §3)를 본 에이전트가 직접 인라인 수행*하지만, CI/CD 부착은 *별도 피어 에이전트(CICD-SETTER)의 책임* 이므로 직접 수행하지 않고 **오케스트레이터 경유 호출 권고**로 처리한다(원칙 7 일관).

### RP8 — 종료

- 보고 전달 완료 후 본 에이전트 컨텍스트 해제
- 이후 분기 책임은 오케스트레이터

---

## 6. 자체 체크 항목 (요약)

| 항목 | 통과 기준 |
|---|---|
| 사전 조건 | `.git/`, `.claude/` 비충돌, 템플릿·핀 존재 |
| 인터뷰 완전성 | RP1~RP3.6 응답 모두 수집 (메타 + 코드·깃 컨벤션 + 조건부 레포 프로파일: CI·릴리스·배포·자격증명·디자인·생산자/소비자) |
| `.claude/CLAUDE.md` 변수 | 모든 변수 채워짐, `{...}` 잔존 X |
| 동반 템플릿 (RP5.5) | `.claude/STACK.md`·`CODING.md`·`FRAMEWORK.md` 생성 + 변수 채워짐 |
| 인코딩 (POLICY-ENCODING) | 생성·복사 파일 전부 UTF-8 no-BOM/LF, U+FFFD/`?`/BOM 손상 없음 |
| AWS 룰셋 설치 | AWS-ADAPTER.md §3.3 정합성 통과 |
| AWS 버전 매칭 | `aws-aidlc-version.txt` 핀과 일치 |
| Extension 적용 (조건부) | 정상 준비 시 → 적용 파일 모두 존재 / 정상 미준비 → 스킵 로그 / **위험 신호 → ABORT 보고** |
| 깃 트래킹 (POLICY-TRACKING) | fetch 선행 → 공유 산출물 add+커밋 → 커밋 검증 통과 / 개인 파일만 gitignore / 룰 디렉토리 통째 무시 X |
| 레포 프로파일 (조건부, RP7.6) | 보유 항목 → REPO-MAP `{REPO_PROFILES}` 해당 슬러그 서브섹션 기록(fetch 선행·커밋 검증) / **배포 보유 시 deploy 필드(타깃·방식·환경 티어·prod 트리거 주체·자격증명 이름·스코프) 기록** / 자격증명·배포 자격증명 *값* 미기록(이름·스코프만) / 미보유 → 스킵 로그 / `{...}` 잔존 X |
| CICD-SETTER 호출 권고 (조건부, RP7.7) | CI/CD 보유·필요 시 → 4-튜플 4번에 CICD-SETTER 호출 권고(모드 힌트 + 전달 입력) 포함 / 직접 피어 호출 안 함(원칙 7 — 오케스트레이터 경유) / CI/CD 미보유 → 스킵 로그 |

---

## 7. 산출물 템플릿 참조

본 에이전트가 채우는 인스턴스의 *템플릿 본문*은 별도 파일로 관리:

| 인스턴스 | 템플릿 위치 |
|---|---|
| `{레포}/.claude/CLAUDE.md` | `{공유리포}/templates/CLAUDE.template.md` |
| `{레포}/.claude/STACK.md` | `{공유리포}/templates/STACK.template.md` (RP5.5 — 레포 스코프) |
| `{레포}/.claude/CODING.md` | `{공유리포}/templates/CODING.template.md` (RP5.5 — 레포 스코프) |
| `{레포}/.claude/FRAMEWORK.md` | `{공유리포}/templates/FRAMEWORK.template.md` (RP5.5 — 레포 스코프) |
| `{메타 레포}/REPO-MAP.md` 레포 프로파일 블록 (`{REPO_PROFILES}` 해당 슬러그 서브섹션 — **조건부**, RP7.6) | `{공유리포}/templates/REPO-MAP.template.md` ("레포 프로파일" 블록 형식 — 시스템 스코프 인스턴스에 *슬러그 서브섹션 추가/갱신*) |

> `WORKFLOW.template.md`·`DESIGN.template.md`는 **자동 생성 대상이 아닌 시스템 컴패니언 스펙**(`specs/SYSTEM-WORKFLOW.md`로 재포지셔닝, PR/머지 관리) → 본 에이전트·SETTER 모두 인터뷰로 생성하지 않음. RP5.5 주의 참조.

추가로 본 에이전트가 *복사·설치*하는 외부 산출물:

| 산출물 | 원천 |
|---|---|
| `{레포}/aidlc-rules/*` | `awslabs/aidlc-workflows` (AWS-ADAPTER.md §3) |
| `{레포}/aidlc-rules/aws-aidlc-rule-details/extensions/*` | `{공유리포}/extensions/` (조건부) |

---

## 8. 변수 출처 부록

| 산출물 | 변수 | 출처 |
|---|---|---|
| `.claude/CLAUDE.md` | `{PROJECT_NAME}` | RP2.2 |
| `.claude/CLAUDE.md` | `{PROJECT_FULL_NAME}` | RP2.1 |
| `.claude/CLAUDE.md` | `{PROJECT_DESCRIPTION}` | RP2.3 |
| `.claude/CLAUDE.md` | `{STACK_SUMMARY}` | RP2.4 |
| `.claude/CLAUDE.md` | `{REFERENCE_FILES}` | RP3.1 |
| `.claude/CLAUDE.md` | `{TOP_FORBIDDEN_RULES}` | RP3.5.3 (탐지+응답 — 전부 미탐지·미응답 시에만 시스템 디폴트/"없음") |
| `.claude/CLAUDE.md` 응답 언어 영향 | (간접 — 본문은 우리 디폴트 + AWS 위임 안내) | RP1.1 |
| `.claude/STACK.md` | `{STACK_TABLE}`·`{DIRECTORY_TREE}`·`{COMPONENT_HIERARCHY}`·`{FILE_LOCATION_RULES}`·`{TEST_RULES}`·`{EXTERNAL_INTEGRATIONS}`·`{VCS_RULES}` | RP2.4 + 자동 탐지 + RP3.5.1·RP3.5.2 |
| `.claude/CODING.md` | `{CODING_RULES}` | RP3.5.1 + 탐지된 린트·포맷·스타일 가이드 |
| `.claude/FRAMEWORK.md` | `{FRAMEWORK_PATTERNS}` | RP2.4(프레임워크) + RP3.5.1 |
| `REPO-MAP.md` 레포 프로파일 (`{REPO_PROFILES}` 해당 슬러그 서브섹션 — **조건부**) | CI/CD(차단·사람 승인 게이트) / 릴리스·퍼블리시(방식·레지스트리) / **배포(타깃·방식/전략·환경 티어·prod 트리거 주체·배포 자격증명 이름·스코프)** / 자격증명 사전조건(*이름·스코프·역할만 — 값 금지*) / 디자인 표면(위치·정규·동기화 방향) / producer·consumer(상대 슬러그) | RP3.6.1 / RP3.6.2 / **RP3.6.6(배포)** / RP3.6.3 / RP3.6.4 / RP3.6.5 (+ 자동 탐지 — POLICY-RELEASE·**POLICY-DEPLOY·A-4**·SYSTEM-WORKFLOW §3·A-2·A-5·EX-13 연계). 미보유 필드는 생략. **배포 필드는 DEPLOY-AGENT가 배포 시 소비** |

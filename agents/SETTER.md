# SETTER.md — 시스템 부트스트랩 가이드

> AI DLC *시스템 단위*(여러 레포로 구성된 하나의 프로덕트/조직)를 **최초 1회** 부트스트랩하는 룰북.
> 이 가이드는 **SETTER 에이전트**가 읽고 실행하며, **오케스트레이터 에이전트의 서브 에이전트**로 호출된다.

---

## 0. 컨텍스트 — 배포 모델 & 디렉토리 구조

본 시스템은 *사내 공유 깃 리포지토리* `ix-ai-dlc`로 배포된다. 팀원은 클론으로 모든 룰북/템플릿을 받고, 자기 환경에서 에이전트를 실행한다. 명세는 *환경 중립* — 로컬 / Codespaces / AWS 어디서든 동작.

**메타 레포(`dlc-meta`)는 팀 공유 원격**(D-Stage4-1) — 인스턴스 config(ORCHESTRATOR.md·REPO-MAP.md)와 사이클 로그가 팀원 간 공유된다. 첫 부트스트랩(신규)이 원격을 만들고, 이후 팀원은 *합류(clone)*. **시크릿(GitLab 토큰·Figma 키 등)은 dlc-meta에 넣지 않는다** — 머신별 로컬 `.env`(gitignore)에만. 공유되는 건 값 없는 `.env.example` 매니페스트뿐.

```
ix-ai-dlc/                         ← 사내 공유 깃 리포지토리 (클론으로 받음)
├── CLAUDE.md
├── ix-ai-dlc-overview.md
├── aws-aidlc-version.txt
├── .gitattributes
├── agents/                        ← 행위 주체(에이전트) 룰북
│   ├── orchestrator/              ← 오케스트레이터 (코어 + 디테일)
│   │   ├── ORCHESTRATOR-AGENT.md
│   │   ├── ROUTING.md
│   │   ├── DECISIONS.md
│   │   ├── ERROR-POLICY.md
│   │   └── TERMINATION.md
│   ├── SETTER.md                  ← 이 파일
│   ├── REPO-SETTER.md
│   ├── REPO-CREATOR.md
│   ├── CYCLE-CLOSER.md
│   └── HANDOFF-WRITER.md
├── specs/                         ← 형식·룰 명세 (에이전트 아님)
│   ├── SYSTEM-WORKFLOW.md
│   ├── AWS-ADAPTER.md
│   ├── CYCLE-LOG.md
│   └── EVOLUTION.md
└── templates/
    ├── ORCHESTRATOR.template.md
    ├── REPO-MAP.template.md
    ├── CLAUDE.template.md
    ├── HANDOFF.template.md
    ├── STACK.template.md
    ├── WORKFLOW.template.md
    ├── DESIGN.template.md
    ├── CHECKLIST.template.md
    ├── CODING.template.md
    ├── FRAMEWORK.template.md
    └── extensions/                ← 레포에 선택 적용하는 룰
        ├── quality/checklist.template.md
        ├── coding/coding.template.md
        └── framework/framework.template.md

(SETTER 실행 산출 — `dlc-meta`는 팀 공유 원격에 push/clone)
{Q2.2}/{Q2.1}/                     ← 메타 레포 (예: /workspace/dlc-meta), 원격 = {Q2.4}
├── ORCHESTRATOR.md                ← S7 산출 (공유)
├── REPO-MAP.md                    ← S8 산출 (공유)
├── .env.example                   ← S8.5 산출 — 필요 시크릿 키 매니페스트 (값 없음, 공유)
├── .gitignore                     ← S8.5 — `.env` 추적 제외 보장
└── cycles/                        ← 사이클 로그 저장소 (S6 생성, 공유)

(머신별 로컬 — 추적 안 됨, 공유 안 됨)
{Q2.2}/{Q2.1}/.env                 ← 시크릿 값 (GitLab 토큰·Figma 키 등). 사용자가 채움. gitignore.
```

본 명세에서 `{공유리포}`는 *클론된 `ix-ai-dlc/` 디렉토리의 절대 경로*를 의미. 오케스트레이터가 이 경로를 SETTER에 전달한다.

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 서브 에이전트 룰북 |
| 호출 주체 | 오케스트레이터 에이전트 |
| 수명 | **프로젝트당 첫 부트스트랩 1회(신규)**. 공유 `dlc-meta` 원격이 이미 있으면 **합류(clone, S7·S8 스킵)**. 추가 레포는 `REPO-CREATOR.md`가 처리 |
| 사용자 채널 | 직접 통신 없음. 모든 인터뷰는 *오케스트레이터를 통한다* |

---

## 2. 책임 / 비책임

### 책임

1. 시스템 단위 인터뷰 수행 — 레포 식별, 메타데이터 수집, 시스템 메타 수집
2. **신규**: 메타 레포(`{Q2.2}/{Q2.1}/`) 생성 + 공유 원격(`{Q2.4}`) 연결·push / **합류**: 공유 원격 clone (이 경우 3·4 스킵)
3. `{메타 레포}/ORCHESTRATOR.md` 인스턴스 생성 (템플릿 채움) — *신규만*
4. `{메타 레포}/REPO-MAP.md` 인스턴스 생성 (템플릿 채움) — *신규만*
5. `{메타 레포}/cycles/` 디렉토리 자리 마련 (사이클 로그 저장소 — 형식 명세는 `CYCLE-LOG.md` 영역)
6. **자격증명 부트스트랩** — `.env.example`(필요 키 매니페스트, 값 없음) 생성·갱신 + `.env` 자리 마련 + `.gitignore`에 `.env` 추적 제외 보장. 시크릿 *값은 사용자가 채움* (SETTER는 값을 적지 않음)
7. 정합성 자체 체크 + 오케스트레이터에 결과 보고

### 비책임 (다른 산출물에 위임)

| 영역 | 위임처 |
|---|---|
| 개별 레포의 `.claude/` 생성 | `REPO-SETTER.md` |
| 추가 레포 생성/등록 | `REPO-CREATOR.md` |
| 사이클 로그 형식 명세 | `CYCLE-LOG.md` |
| 시스템 운영 중 분기/조율 | `ORCHESTRATOR-AGENT.md` |
| 사이클 종료 후처리 (티켓·커밋·보고서) | `CYCLE-CLOSER.md` |

---

## 3. 핵심 원칙 (적용되는 시스템 원칙)

- **원칙 1** 호출 시점·책임 다르면 분리
- **원칙 4** AI 에이전트가 자율 실행, 사용자는 의미 결정만
- **원칙 6** 단일 원천 — 도메인 정보는 REPO-MAP만이 원천
- **원칙 7** 모든 서브 에이전트 호출은 오케스트레이터 단독 책임 (SETTER도 오케스트레이터가 호출)
- **원칙 8** 공유 룰북·템플릿은 깃 단일 원천 — 변경은 PR/머지로만 (Stage 4 본격 명세)
- **자격증명 경계** (D-Stage4-2): 에이전트는 `.env`의 시크릿을 *읽기·사용*만. 토큰 *발급/회전*, 레포 *권한·접근제어·멤버십 변경*은 사람 선결(자동 경로 밖). 시크릿 값은 추적 파일(dlc-meta 포함)에 절대 커밋하지 않음
- **반자동화**: 실행(파일/디렉토리 생성, git 초기화, 스캔)은 자동, 의미 결정(이름·관계·정책)은 사용자 인터뷰

---

## 4. 입출력

### 입력 (오케스트레이터로부터)

- 트리거 신호 — "시스템 부트스트랩 필요" 판단
- `{공유리포}` 절대 경로 (클론된 `ix-ai-dlc/`)
- 사용자 인터뷰 응답 (Q2.x ~ Q5.x)

### 출력 (오케스트레이터에 보고)

- 생성된 파일 절대 경로 목록
- 정합성 자체 체크 결과
- 인터뷰 응답 원본
- 권고 다음 단계

---

## 5. 실행 절차

```
[페이즈 1] 입력 수집 & 인터뷰   →  S1 ~ S5
[페이즈 2] 자동 생성/합류        →  S6 ~ S8.5
[페이즈 3] 검증 & 보고           →  S9
[페이즈 4] 종료                  →  S10
```

---

### 페이즈 1 — 입력 수집 & 인터뷰

#### S1. 사전 조건 체크 (자동, 인터뷰 없음)

- `{공유리포}` 경로 존재 + 필요 파일 존재 확인
  - `{공유리포}/templates/ORCHESTRATOR.template.md`
  - `{공유리포}/templates/REPO-MAP.template.md`
- **dlc-meta 공유 원격 존재 여부 판정 → 신규/합류 분기** (D-Stage4-1):
  - 원격(`{Q2.4}`)에 인스턴스가 이미 있음 → **합류** (clone, 인스턴스 재생성 안 함). *에러 아님*
  - 없음 → **신규** (이 SETTER가 부트스트랩 + 원격 생성)
  - 로컬 위치 충돌(이미 다른 내용 존재)만 에러
- 필요 권한 체크 (디렉토리 생성, git 초기화, 원격 push/clone — 자격증명은 S8.5 `.env`)
- 실패 시 오케스트레이터에 보고 후 종료

#### S2. 메타 레포 위치/이름 인터뷰

| ID | 질문 | 기본/추천 |
|---|---|---|
| Q2.1 | 메타 레포 이름? | `dlc-meta` |
| Q2.2 | 메타 레포 로컬 절대 경로? | (없음) |
| Q2.3 | `git init` 진행할까? (신규 시) | yes |
| Q2.4 | **dlc-meta 공유 원격 URL?** (GitLab 등) | (없음) — *이미 있으면 합류(clone), 없으면 신규 생성·push* |

> Q2.4가 신규/합류를 가른다 (S1 판정). 합류면 S3~S8(인터뷰·인스턴스 생성) 스킵하고 clone — 인스턴스는 팀원이 이미 채움.

#### S3. 대상 레포 식별 방식 인터뷰

| ID | 질문 | 기본/추천 |
|---|---|---|
| Q3.1 | 식별 방식? | (a) 명시적 경로 리스트(기본) / (b) 워크스페이스 폴더 스캔 |
| Q3.2-a | (a 선택 시) 각 레포 절대 경로 N개 | — |
| Q3.2-b | (b 선택 시) 워크스페이스 컨테이너 폴더 경로 | — |
| Q3.3 | (b 선택 시) 자동 스캔 후 후보 중 대상 선택 | `.git/` 보유 하위 폴더 |

#### S4. 레포별 메타데이터 인터뷰 (대상 레포마다 반복)

| ID | 질문 | 자동 추천 |
|---|---|---|
| Q4.1 | 별칭(슬러그)? | 디렉토리명 |
| Q4.2 | 역할 한 줄 요약? | `package.json`/README 기반 |
| Q4.3 | 담당 도메인 (멀티)? | — |
| Q4.4 | 의존하는 다른 레포 (멀티)? | — (자동 분석은 advanced 큐) |
| Q4.5 | **레포 원격 URL?** (머신 독립 식별자 — REPO-MAP 단일 원천) | `git remote get-url origin` 자동 추출 |

> 로컬 절대 경로(Q3.2)는 *머신마다 다름* → REPO-MAP에 박지 않고, 원격 URL(Q4.5)을 식별자로 저장. 로컬 경로는 머신별 해석 (D-Stage4-3, S8 참조).

#### S5. 시스템 단위 메타 인터뷰

| ID | 질문 |
|---|---|
| Q5.1 | 시스템(프로덕트) 이름? |
| Q5.2 | 시스템 한 줄 설명? |

> 응답 언어(`{RESPONSE_LANGUAGE}`)는 REPO-SETTER가 레포마다 별도 인터뷰.
> 작업 유형별 라우팅 규칙은 운영 중 EVOLUTION 단계가 누적.

#### S5.5. 시스템 전역 컨벤션 인터뷰 (cross-repo 공통 규약)

> *목적*: 여러 레포에 **공통으로 걸리는 시스템 전역 규약**(cross-repo git/커밋 컨벤션, 공유 코딩 표준, 브랜치·PR/MR 정책, *공유 배포·CI 규약* 등)을 수집해 시스템 인스턴스에 1회 기록한다. **개별 레포 단위의 스택·컨벤션 상세는 REPO-SETTER가 레포마다 따로 인터뷰**하므로(원칙 6, 단일 원천), 여기서는 *레포에 안 걸치는 전역 규약*만 잡고 레포별 상세는 중복 수집하지 않는다.
>
> *자동 탐지 우선 (원칙 4 — 자동 실행 + 의미 확인)*: 인터뷰 전, cross-repo 신호를 **자동 스캔**해 추천값을 만든 뒤 사용자에게 확인만 받는다. 신호 예시(일반): 워크스페이스 루트의 공유 에이전트 규칙 파일(예: 루트 `CLAUDE.md`/`AGENTS.md`/`.editorconfig`/조직 정책 문서), 대상 레포들에 *공통으로* 나타나는 커밋/브랜치 관습(예: Conventional Commits 흔적, 보호 브랜치명, MR/PR 템플릿). 신호가 없으면 빈 값으로 두고 묻기만 한다.

| ID | 질문 | 자동 추천 (cross-repo 신호) |
|---|---|---|
| Q5.3 | 시스템 전역 git/커밋 컨벤션? (예: Conventional Commits, 커밋 트레일러 규약) | 대상 레포 공통 커밋 관습 자동 탐지 |
| Q5.4 | 공유 브랜치·PR/MR 정책? (예: 보호 브랜치명, 머지 시 source branch 자동삭제 여부, 리뷰 필수) | 보호 브랜치명·MR 템플릿 흔적 자동 탐지 |
| Q5.5 | 시스템 전역 공유 코딩 표준? (cross-repo 공통 — 레포별 상세는 REPO-SETTER 담당) | 루트 공유 규칙 파일(예: 루트 `CLAUDE.md`/`.editorconfig`/조직 정책 문서) 자동 탐지 |
| Q5.6 (조건부) | 시스템 전역 **배포·CI 컨벤션**? (cross-repo 공통만 — 예: 공유 배포 플랫폼·타깃, 공유 CI 시스템, 공유 환경 승격 정책(낮은→높은 티어), 시스템 차원에서 *누가 prod 배포를 소유*하는가) | 대상 레포 공통 CI 시스템·배포 플랫폼·환경 티어 명명 자동 탐지 |

> *경계*: Q5.3~Q5.6은 **시스템 전역**만. 한 레포에만 적용되는 규칙은 여기 넣지 말고 REPO-SETTER로 위임 (중복·과적합 방지). 특히 **Q5.6은 *레포별 배포 상세*(타깃·전략·환경 티어·prod 트리거 주체·배포 자격증명)를 중복 수집하지 않는다** — 그건 REPO-SETTER RP3.6.6이 per-repo로 잡아 REPO-MAP `{REPO_PROFILES}` deploy 필드에 기록한다. 여기서는 *여러 레포에 공통으로 걸리는 시스템 차원 규약*(공유 플랫폼·공유 CI·공유 승격 정책·prod 소유 주체)만 잡는다. 시스템에 공유 배포·CI 규약이 없으면(레포마다 제각각) Q5.6은 "(미지정)"으로 두고 건너뛴다(조건부 — POLICY-DEPLOY §1.1 / 범용 전제).
> *기록 위치*: 응답은 S7 `ORCHESTRATOR.md` 인스턴스의 **「시스템 전역 컨벤션」 섹션**(템플릿 변수 `{SYSTEM_CONVENTIONS}`)에 기록한다 (S7 변수표 참조). 빈 값이면 "(미지정)"으로 채운다 — POLICY-TEMPLATE-ADHERENCE.

---

### 페이즈 2 — 자동 생성

#### S6. 메타 레포 생성 또는 합류

**신규** (Q2.4 원격에 인스턴스 없음):
```bash
mkdir -p {Q2.2}/{Q2.1}             # 예: /workspace/dlc-meta
cd {Q2.2}/{Q2.1}
[ Q2.3 == yes ] && git init
git remote add origin {Q2.4}       # 공유 원격 연결 (초기 push는 S8.5 후)
mkdir cycles                       # 사이클 로그 저장소 자리
```

**합류** (Q2.4 원격에 인스턴스 이미 있음):
```bash
git clone {Q2.4} {Q2.2}/{Q2.1}     # 인스턴스(ORCHESTRATOR.md·REPO-MAP.md)·cycles 함께 받음
# → S7·S8 스킵 (인스턴스 재생성 금지 — 팀원 것 덮어쓰기 방지). S8.5(.env)는 합류도 수행.
```

> 템플릿은 `{공유리포}/templates/`에 이미 존재(클론으로 받음). 메타 레포 안에 별도 templates 디렉토리 만들지 않는다.
> 원격 dlc-meta 자체를 *생성*해야 하면(빈 프로젝트) — 사람이 GitLab 등에 빈 레포 선결 또는 에이전트가 사용자 컨펌 + `.env` 자격증명으로 생성 (REPO-CREATOR와 동일 모델, D-Stage4-2).

#### S7. `ORCHESTRATOR.md` 작성

- 원본 템플릿: `{공유리포}/templates/ORCHESTRATOR.template.md` (POLICY-TEMPLATE-ADHERENCE — 자유 형식 손수 작성 금지, 템플릿 섹션·변수 보존)
- 변수 채움:

| 변수 | 출처 |
|---|---|
| `{SYSTEM_NAME}` | Q5.1 |
| `{SYSTEM_DESCRIPTION}` | Q5.2 |
| `{SYSTEM_CONVENTIONS}` | Q5.3~Q5.6 (시스템 전역 git/커밋·브랜치·PR/MR·공유 코딩 표준 + *조건부* 공유 배포·CI 규약 — 빈 값은 "(미지정)") |

- 산출: `{메타 레포}/ORCHESTRATOR.md`
- **쓰기 방식 (POLICY-ENCODING 필수)**: 변수 치환 결과를 **직접 UTF-8(BOM 없음)·LF 파일 쓰기**로 생성한다. 본문에 한국어 산문이 포함되므로 *로케일 의존 셸 출력(echo·리다이렉트·tee·기본 `Set-Content` 등)으로 흘려보내지 말 것* (Windows CP949 등에서 mojibake). 생성 후 U+FFFD·떠도는 `?`·BOM 검증 → 손상 시 재생성.
- 본문에 `ORCHESTRATOR-AGENT.md` 참조 포함됨 (템플릿 기본)

#### S8. `REPO-MAP.md` 작성

- 원본 템플릿: `{공유리포}/templates/REPO-MAP.template.md` (POLICY-TEMPLATE-ADHERENCE — 템플릿에서 생성, 자유 형식 금지)
- **쓰기 방식 (POLICY-ENCODING 필수)**: ORCHESTRATOR.md와 동일 — 직접 UTF-8(BOM 없음)·LF 파일 쓰기, 로케일 의존 셸 출력 금지, 생성 후 검증·재생성.
- 변수 채움:

| 변수 | 출처 |
|---|---|
| `{SYSTEM_NAME}` | Q5.1 |
| `{REPO_TABLE}` | Q4.1 ~ Q4.4 집계 (각 레포 1행) |
| `{REPO_PROFILES}` | **부트스트랩 시 빈 collapse 값** — `_(해당 프로파일 없음)_` 한 줄로 렌더 (POLICY-TEMPLATE-ADHERENCE: 템플릿 변수 미충전 `{...}` 잔존 금지). 레포별 프로파일(CI/릴리스·디자인 표면·자격증명 등)은 REPO-SETTER가 사이클 중 per-repo로 채운다(RP7.6). |

- `{REPO_TABLE}` 형식 (마크다운 표):

| 슬러그 | 원격 | 역할 | 도메인 | 의존 |
|---|---|---|---|---|
| (Q4.1) | (Q4.5 원격 URL) | (Q4.2) | (Q4.3, 콤마) | (Q4.4, 콤마) |

> **머신 독립** (D-Stage4-3): REPO-MAP은 *원격 URL*을 식별자로 저장 (절대 경로 X — 공유 시 머신마다 다름). 로컬 체크아웃 경로는 머신별로 해석 — `.env`의 `{WORKSPACE_ROOT}` + 슬러그, 또는 로컬 매핑. ROUTING §2·STEP 4 위탁은 *해석된 로컬 경로*를 사용.

- 산출: `{메타 레포}/REPO-MAP.md`

#### S8.5. 자격증명 부트스트랩 (`.env` / `.env.example` / `.gitignore`)

신규·합류 **둘 다 수행** (시크릿은 머신별이라 합류자도 자기 것 필요):

```bash
cd {메타 레포}
# 1) 필요 키 매니페스트 (값 없음, 공유 OK) — 사용 통합에 따라 키 추가
cat > .env.example <<'EOF'
# 필요 시크릿 (값은 로컬 .env에 채울 것 — 여기엔 값 금지)
GITLAB_TOKEN=
FIGMA_KEY=
WORKSPACE_ROOT=
EOF
# 2) .env 추적 제외 보장 (이미 있으면 중복 추가 안 함) — 개인(PERSONAL) 파일만 무시
#    (POLICY-TRACKING) `.gitignore`는 *개인 파일만* 무시한다: 시크릿(`.env*`)·머신 로컬 설정.
#    공유 인스턴스 문서(ORCHESTRATOR.md·REPO-MAP.md·cycles/)는 절대 ignore에 넣지 않는다.
grep -qxF '.env' .gitignore 2>/dev/null || echo '.env' >> .gitignore
# 3) .env 자리 마련 (값은 사용자가 채움 — SETTER는 값 적지 않음)
[ -f .env ] || cp .env.example .env
```

> 시크릿 *값*은 사용자가 `.env`에 직접 입력. 에이전트는 런타임에 `.env`에서 *읽기*만 (자격증명 경계, §3 / D-Stage4-2).

#### S8.6. 공유 메타 레포 커밋·push (신규 — **필수·검증 단계, 생략 금지**)

> **POLICY-TRACKING**: 시스템 인스턴스(ORCHESTRATOR.md·REPO-MAP.md·cycles/)는 *공유(SHARED)* 산출물이다. 깃 추적 + 커밋 + push를 **반드시 성사**시켜야 한다. 이 단계를 옵셔널로 취급하거나 건너뛰면 *전체 시스템 인스턴스·핸드오프가 추적 안 된 채 로컬에만 남아* 팀원이 한 원천을 공유하지 못한다 (실제 사고: 명세상 커밋 단계가 있었으나 실행되지 않아 인스턴스가 미추적·로컬 잔존). **신규 부트스트랩에서 무조건 수행**, 합류(clone)는 이미 추적된 상태이므로 해당 없음.

```bash
cd {메타 레포}
# (1) fetch 선행 (POLICY 공통 — git fetch/pull 선행, SYSTEM-WORKFLOW §3). 원격에 이미 인스턴스가 있으면 신규가 아니라 합류여야 함 → 멈추고 S1 분기 재확인.
git fetch origin --prune

# (2) 공유 인스턴스 + cycles/ 자리표 스테이징. `.env`(개인)는 gitignore라 제외됨(아래서 검증).
git add ORCHESTRATOR.md REPO-MAP.md .gitignore .env.example
git add cycles/.gitkeep 2>/dev/null || true   # 빈 디렉토리 추적용 자리표 (없으면 무시)

# (3) `.env`가 스테이징에 절대 없어야 함 (시크릿 누출 가드 — 있으면 멈춤)
git diff --cached --name-only | grep -qx '.env' && { echo 'ABORT: .env staged — 시크릿 누출 위험'; exit 1; } || true

# (4) 커밋 + push (기준 브랜치는 원격 디폴트 — 예: main/master)
git commit -m "bootstrap: dlc-meta 시스템 인스턴스 (ORCHESTRATOR·REPO-MAP·cycles)"
git push -u origin HEAD
```

**커밋 성사 검증 (필수 — 통과 못 하면 실패 보고)**:
- `git log -1 --oneline`에 위 커밋이 보이는지
- `git status`가 *공유 인스턴스에 대해* clean (미추적·미커밋 잔존 없음) — `.env`만 untracked로 남는 것은 정상
- push 결과: 원격에 커밋이 반영됐는지(`git rev-parse HEAD` == `git rev-parse @{u}`). push 출력에 `[new branch]`가 떴는데 *기존 브랜치 갱신* 의도였다면 멈추고 분기/MR 상태 점검 (SYSTEM-WORKFLOW §3 fetch 선행 가드).
- 검증 실패 시 *성공으로 보고하지 말 것* — S9 자체 체크에서 "공유 인스턴스 추적·커밋" 항목 FAIL로 오케스트레이터에 보고.

> 합류(clone)는 인스턴스가 이미 원격에 추적돼 있으므로 본 단계 해당 없음. 팀원은 clone으로 추적된 인스턴스를 받는다.

---

### 페이즈 3 — 검증 & 보고

#### S9. 정합성 자체 체크 + 오케스트레이터 보고

**자체 체크 항목**:
- REPO-MAP 각 행의 *원격 URL이 유효*한지 + 슬러그→로컬 해석 경로가 실제 존재하는지
- 각 (해석된) 경로 안에 `.git/` 존재 여부
- 슬러그 중복 없음
- 의존 컬럼이 *존재하는 슬러그*만 가리킴
- **`.env`가 `.gitignore`에 포함됐는지 (시크릿 누출 방지 — 미포함이면 실패)**
- `.env.example`에 값이 비어 있는지 (실수로 시크릿 커밋 방지)
- **`.gitignore`가 공유 인스턴스를 무시하지 않는지** (ORCHESTRATOR.md·REPO-MAP.md·cycles/ — 무시하면 실패. POLICY-TRACKING: 개인 파일만 무시)
- **(신규) 공유 인스턴스 추적·커밋 성사** (S8.6) — 커밋이 `git log`에 보이고 `HEAD == @{u}`(push 반영), 공유 인스턴스에 미추적 잔존 없음. 미성사면 **실패** (인스턴스가 로컬 잔존 → 팀 공유 불가)
- 생성 파일이 **UTF-8(BOM 없음)** 인지 — U+FFFD·떠도는 `?`·BOM 없음 (POLICY-ENCODING)

**오케스트레이터에 보고할 4가지**:

1. **생성 파일 절대 경로 목록** (+ 추적 상태)
   - `{메타 레포}/ORCHESTRATOR.md` (공유 — 커밋·push됨, S8.6)
   - `{메타 레포}/REPO-MAP.md` (공유 — 커밋·push됨, S8.6)
   - `{메타 레포}/cycles/` (디렉토리, 공유)
   - `{메타 레포}/.env.example`·`.gitignore` (공유) / `{메타 레포}/.env` (개인 — gitignore, 미추적)
2. **정합성 체크 결과** — 항목별 통과/실패 + 실패 사유
3. **인터뷰 응답 원본** — Q2.x ~ Q5.x 사용자 답변
4. **권고 다음 단계**:
   - 각 레포에 대해 **REPO-SETTER 호출** (권장 순서: 의존 root 가까운 레포부터)
   - 모든 REPO-SETTER 완료 후 **ORCHESTRATOR-AGENT를 *운영 모드*로 전환**

> SETTER는 분기 판단·수정 요청 처리를 *직접 하지 않는다*. 위 보고만 하고, 다음 분기는 오케스트레이터가 결정.

---

### 페이즈 4 — 종료

#### S10. 종료

- 보고 전달 완료 후 SETTER 컨텍스트 해제
- 이후 모든 분기·추가 작업은 오케스트레이터 책임

---

## 6. 산출물 템플릿 참조

본 SETTER가 채우는 두 인스턴스 파일의 *템플릿 본문*은 별도 파일로 관리한다:

| 인스턴스 (스코프) | 템플릿 위치 |
|---|---|
| `{메타 레포}/ORCHESTRATOR.md` (**시스템 스코프**) | `{공유리포}/templates/ORCHESTRATOR.template.md` |
| `{메타 레포}/REPO-MAP.md` (**시스템 스코프**) | `{공유리포}/templates/REPO-MAP.template.md` |

템플릿 본문 변경은 *깃 PR/머지*로만 (원칙 8). SETTER는 *항상 현재 main의 템플릿*을 읽어 인스턴스를 채운다 (POLICY-TEMPLATE-ADHERENCE).

> **스코프 경계 (다른 템플릿은 SETTER가 생성하지 않음)**: `WORKFLOW`·`DESIGN`은 시스템 레벨에서 *PR/머지로 관리되는 명세*(`specs/SYSTEM-WORKFLOW.md` 및 그 동반 시스템 가이드)로 재포지셔닝됨 — *부트스트랩 인터뷰로 매번 생성되는 인스턴스가 아니다*(자동 생성 대상 아님). `CLAUDE`·`STACK`·`CODING`·`FRAMEWORK`·`CHECKLIST`는 **레포 스코프**로, REPO-SETTER(RP5.5 동반 템플릿 + RP6 AWS Extension)가 레포마다 생성한다. 따라서 SETTER가 인터뷰→템플릿으로 *생성*하는 시스템 인스턴스는 위 두 개(ORCHESTRATOR·REPO-MAP)뿐이며, 시스템 전역 컨벤션(S5.5)은 새 인스턴스 파일을 만들지 않고 *ORCHESTRATOR 인스턴스의 `{SYSTEM_CONVENTIONS}` 섹션*에 기록한다(중복·스코프 충돌 방지).

---

## 7. 변수 출처 부록

| 산출물 | 변수 | 출처 |
|---|---|---|
| `ORCHESTRATOR.md` | `{SYSTEM_NAME}` | Q5.1 |
| `ORCHESTRATOR.md` | `{SYSTEM_DESCRIPTION}` | Q5.2 |
| `ORCHESTRATOR.md` | `{SYSTEM_CONVENTIONS}` (시스템 전역 git/커밋·브랜치·PR/MR·공유 코딩 표준 + *조건부* 공유 배포·CI 규약: 공유 배포 플랫폼·공유 CI·공유 환경 승격 정책·prod 소유 주체) | Q5.3~Q5.6 (cross-repo 신호 자동 탐지 + 확인) |
| `REPO-MAP.md` | `{SYSTEM_NAME}` | Q5.1 |
| `REPO-MAP.md` | `{REPO_TABLE}` (슬러그·**원격**·역할·도메인·의존) | Q4.1~Q4.5 집계 |
| `REPO-MAP.md` | `{REPO_PROFILES}` | 부트스트랩 시 `_(해당 프로파일 없음)_` 빈 collapse (미충전 금지) — per-repo는 REPO-SETTER RP7.6 |

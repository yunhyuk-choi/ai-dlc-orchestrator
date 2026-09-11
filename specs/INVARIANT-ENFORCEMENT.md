# INVARIANT-ENFORCEMENT.md — 불변식 강제 명세 (프로그램 강제 규율)

> **이 문서는 형식·룰 명세 문서.** 에이전트 룰북 아님.
> 본 명세는 중대 절차(예: 사이클 로깅)를 *모델이 Markdown을 읽어 지키는 것*에서 *프로그램(훅)이 강제하는 불변식*으로 승격하는 규율(POLICY-INVARIANT)을 정의한다.
> 강제 *실행*은 훅에 배선된 범용 엔진(`templates/enforce.template.py`)과 두 선언 원천(`invariants.team.yaml` / `invariants.personal.yaml`). 본 문서는 *무엇을·어떻게 강제하는지의 룰만* 정의한다.
> 변경은 깃 PR/머지 (원칙 8) — `templates/invariants.template.yaml` / `templates/enforce.template.py` / `specs/CYCLE-LOG.md` / `agents/SETTER.md`(STEP 2)가 본 규율에 의존하므로 변경 시 영향 검토 필수.
> 위치: `ai-dlc-orchestrator/specs/INVARIANT-ENFORCEMENT.md`

> **POLICY-INVARIANT (불변식 강제)** — 되돌리기 어렵거나 반복적으로 유실되는 중대 절차는 *모델의 자발적 준수*에 의존하지 않는다. 선언(declarative)으로 명시하고 훅으로 강제하되, 훅이 불가능한 환경에서는 *advisory 폴백*으로 강등해 시스템을 멈추지 않는다 (degraded — EX-15 / C FALLBACK). 강제 대상은 *로컬 지상검증 원천*만 읽는다 (중립).

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 형식·룰 명세 문서 (에이전트 X) |
| 실행 주체 | 훅에 배선된 범용 엔진(`enforce.template.py`) + 오케스트레이터(위반 신호 수신·판단) |
| 참조 주체 | `templates/invariants.template.yaml` / `templates/enforce.template.py` / `agents/SETTER.md`(STEP 2 조립) / `specs/CYCLE-LOG.md`(파일럿 대상) / `CLAUDE.md` §0.5(degraded 사상) |
| 라벨 | **POLICY-INVARIANT** (다른 파일이 본 규율을 이 라벨로 인용) |
| 위치 | `ai-dlc-orchestrator/specs/INVARIANT-ENFORCEMENT.md` |

**왜 에이전트가 아닌가**: 불변식 강제는 *매 도구 사용·매 턴 경계에서 발생하는 횡단 규율*이며, 실행은 사람/모델이 아니라 *결정론적 프로그램(훅)*이 한다. 별도 에이전트로 두면 호출 빈도 과다(원칙 1 비효율) + 강제의 결정성 상실. 따라서 본 문서는 *룰만* 제공하고, 실행은 엔진이 한다.

---

## 2. 문제 — MD 절차는 표류한다

리포 루트 `CLAUDE.md` §0가 명문화한 실측 실패 모드: **컨텍스트 압축 후 정체성이 유실되면 오케스트레이터가 "직접수행자"로 표류한다.** 같은 병리가 절차 전반에 있다 — 사이클 로깅처럼 "매번 해야 하는" 절차는 Markdown에 아무리 정성껏 적어도 *모델이 그 순간 그 문장을 읽고 따르기로 결정*해야만 지켜진다. 그 결정은 압축·긴 사이클·인지 과부하에서 반복적으로 누락된다.

SELF-CHECK 훅(`templates/SELF-CHECK.template.md`)이 *정체성 재주입*에 쓴 해법 — "모델의 자발적 Read가 아니라 기계적 주입" — 을 *절차 강제*로 일반화한 것이 본 명세다.

---

## 3. 모델 — 얇은 적응형 훅 → 범용 엔진 → 2개 선언 원천

```
[적응형 훅]  settings.local.json 의 PostToolUse/Stop 훅
    │  (STEP 2에서 SETTER가 OS·경로 적응해 배선)
    ▼
[범용 엔진]  enforce.template.py   ← 프레임워크 레포에 상주, 100% 중립
    │  로드·병합·필터·체크·방출 (순수 함수 — 단위 테스트 가능)
    ▼
[선언 원천]  invariants.team.yaml (팀·추적) + invariants.personal.yaml (개인·gitignore)
```

- **얇은 훅**: 훅은 엔진을 부르고 경로만 바인딩한다. 로직은 엔진에.
- **범용 엔진**: 프로젝트·트래커 무관. 읽는 것은 로컬 로그 계층뿐.
- **2개 선언 원천**: 관심사 분리(§4)의 물리적 실체. 둘 다 로드되어 **UNION 실행**.

---

## 4. 관심사 분리 — integrity(팀) vs ergonomics(개인)

| concern | 의미 | 저장 | 추적 | 인스턴스 파일 |
|---|---|---|---|---|
| **integrity** | 팀 전역 무결성 — 팀원 누구에게나 성립해야 함 | `dlc-meta` | git 추적(공유) | `invariants.team.yaml` |
| **ergonomics** | 개인 편의 — 사용자별 취향·워크플로우 | `{공유리포}/.claude/` | gitignore(개인) | `invariants.personal.yaml` |

- 팀 무결성 불변식을 개인이 *끄지 못하게* 하고(팀이 floor), 개인은 자기 편의 불변식을 *자유롭게 추가*할 수 있게 하는 것이 분리의 목적이다.
- 선례: SELF-CHECK 훅·위치 마커도 개인(gitignore) 산출물이다 (POLICY-TRACKING). integrity 불변식만 팀 추적이다.

### 4.1 병합·personal-adjust 규칙 (엔진이 강제)

두 파일을 **id로 병합**하며 *팀이 floor(바닥)*다:

- 같은 id가 양쪽에 있으면 **팀의 `personal-adjust`** 값이 개인의 재조정 범위를 정한다:
  - `locked` — 개인이 손대지 못한다 (팀 선언이 최종).
  - `escalate-only` — 개인은 tier를 *올리는 것만* 허용 (`warn`→`block`). 낮추기·타 필드 변경 금지. 최종 tier = `max(팀, 개인)`.
  - `full` — 개인이 전체 필드를 덮어쓴다 (id는 유지).
- 개인에만 있는 **새 id = 자유** (그대로 추가). 통상 `concern: ergonomics`.

> 핵심 불변: *개인 파일은 팀 무결성 불변식을 약화시킬 수 없다.* 강화(escalate)만 가능하며, 그조차 팀이 `personal-adjust`로 허용한 경우에 한한다.

---

## 5. tier 의미론

| tier | 위반 시 훅 동작 | 용도 |
|---|---|---|
| **block** | 차단(blocking JSON — `{"decision":"block","reason":…}`) **+ exit code 2**(신뢰 가능한 차단 채널). Stop·PreToolUse에서 실효적 | 비가역·중대 절차에만 |
| **warn** | 비차단 경고(`systemMessage` / `hookSpecificOutput.additionalContext`) | **기본 권장값** |
| **advisory** | no-op — 훅 출력 없음(가시화·기록만) | 저위험 넛지 · degraded 폴백 등가값 |

- 훅 JSON 형태의 단일 원천은 `enforce.template.py` §7 `emit()`이며, **Claude Code hook contract**에 맞춘다 — **계약은 §11.4에서 확정**(출처: `code.claude.com/docs/en/hooks.md`, v2.1.2xx). block은 exit 2를 쓰고, Stop 재진입은 `stop_hook_active`로 무한루프를 가드한다.
- 여러 불변식이 동시에 걸리면 *최고 tier*로 집계한다.

---

## 6. 선결 조건 스킵 (requires) — 중립 견고성

불변식은 `requires`(선결 조건 id 목록)를 선언한다. **하나라도 불충족이면 그 불변식은 조용히 SKIP**된다. 로컬 로그 계층이 아직 없거나(부트스트랩 전), 트래커 config가 없는 배포 등에서 *엔진이 크래시·오탐 없이* 자연히 비활성화되게 하는 장치다.

- 현재 지원 선결 조건: `local-log-layer` (`cycles/` 디렉토리 존재).
- 미지원 선결 조건(예: STEP 2 어댑터가 넣을 `issue-tracker-config`)은 *불충족으로 간주 → SKIP*. 알 수 없는 조건을 참으로 가정하지 않는다.

---

## 7. 파일럿 불변식 — `cycle-must-log`

사이클 로깅(`specs/CYCLE-LOG.md`)을 첫 대상으로 삼는다. `audit.md`는 사이클 결정의 append-only 단일 원천이고, 로깅 누락은 DP-9 진화 입력·핸드오프·정정의 신뢰성을 통째로 깨뜨린다 — 강제 가치가 높으면서 *완전 중립*(로컬 로그만 읽음)이다.

선언: `concern: integrity` · `tier: warn`(기본) · `personal-adjust: escalate-only` · `requires: [local-log-layer]` · 두 이벤트 바인딩:

| 이벤트 | 체크 | 위반 조건 | 취지 |
|---|---|---|---|
| **PostToolUse** (사이클 액션 도구) | `open-cycle-record-exists` | *열린* `cycles/*/audit.md`(CYCLE-START 있고 CYCLE-END 없음)가 하나도 없음 | 사이클 작업을 하는데 열린 로그 기록이 없다 → 로깅하라 |
| **Stop** (턴 경계 백스톱) | `no-stale-open-cycle` | 열린 사이클 기록이 턴 경계를 넘겨 잔존 | 열린 사이클을 가시화 (마무리했으면 CYCLE-END, 계속이면 유지) |

- `match`(PostToolUse의 "사이클 액션" 신호 도구명 glob)는 `["Task","Agent","Bash:*merge*"]` 같은 **예시 placeholder**다 — SETTER가 실제 서브 디스패치·머지·트래커 전이 도구명에 맞춰 적응한다(중립 유지: 템플릿엔 일반형만).
- 열림 판정은 CYCLE-START/END/**REOPEN** 순차 스캔 상태머신이다 — `specs/CYCLE-LOG.md` §10.3 재오픈과 정합.

---

## 8. degraded 철학 — 훅은 보강이지 전제가 아니다

`CLAUDE.md` §0.5 (4)·(5), SELF-CHECK 템플릿, SETTER S8.7 (5)와 동일 사상이다:

- 훅을 설치·실행할 수 없는 환경(훅 미지원 런타임 · 셸/쓰기 권한 없음 · 정책 차단 · 사람 없는 자동 기동 세션)은 **오류가 아니라 degraded**다.
- 훅이 없으면 불변식 강제는 *advisory로 강등*된다 — 잃는 것은 *프로그램 차단*뿐이고, 절차 자체는 룰북·SELF-CHECK가 계속 상기시킨다.
- 엔진 자체도 degraded-safe: 선언 파일 부재·malformed·PyYAML 부재·stdin 손상 등 **무엇이 어긋나도 아무것도 출력하지 않고 exit 0**. 훅이 시스템을 멈추게 하지 않는다.
- 이 처리는 **EX-15 / C FALLBACK** (ERROR-POLICY)이다 — ABORT·PAUSE로 격상 금지.

### 8.1 YAML 의존 결정

엔진은 **PyYAML을 의존하지 않는다.** PyYAML이 있으면 쓰고, 없으면 선언 템플릿이 쓰는 제한된 블록 서브셋을 파싱하는 **stdlib-only 미니 파서**를 내장한다. 어느 경로든 파싱 실패 시 해당 파일을 `None`으로 보고 조용히 건너뛴다(degraded no-op). 이로써 stdlib만으로 완전 동작하며, 배포에 PyYAML을 요구하지 않는다.

---

## 9. STEP 2 (본 변경에 포함되지 않음)

본 변경(STEP 1)은 **템플릿·명세 3개 파일 추가뿐**이다. 아래는 후속 STEP 2 범위이며, 여기서는 손대지 않는다 (SETTER.md·settings.json·CLAUDE.md 무수정):

> **갱신 (STEP-2a)**: 아래 항목 1·2는 **`agents/SETTER.md` S8.8로 이식·배선 완료**됐다 — 설계(§11·§12)와 라이브 절차(SETTER.md S8.8)가 정합한다. 남은 STEP 2 잔여는 항목 3(block tier 라이브 파이어 — §11.4 (d), 새 세션/오케스트레이터 몫)과 항목 4(트래커 결합 슬롯 실제 채움 — 트래커 운영 배포에서만)이다.

1. **SETTER 조립 단계** — `invariants.template.yaml`을 두 인스턴스(`invariants.team.yaml` 추적 / `invariants.personal.yaml` 개인·gitignore)로 렌더하고, `enforce.template.py`를 실행 위치에 배치. `.gitignore`에 개인 파일·백업 추가 확인. (선례: S8.7 자가점검 훅 설치, S8.5 `.env` 부트스트랩.)
2. **훅 배선** — `{공유리포}/.claude/settings.local.json`에 `PostToolUse`·`Stop` 훅을 *병합*(덮어쓰기 금지)으로 추가하고, `AIDLC_INVARIANTS_DIR`·`AIDLC_LOG_DIR` env로 실제 절대 경로를 바인딩. OS·셸 적응은 S8.7 패턴 재사용.
3. **라이브 훅 계약 검증** — `emit()` JSON 형태를 실제 Claude Code 하네스에 대고 검증(POLICY-VERIFY 지상검증). 계약 불일치 시 `emit()` 매핑을 정정하고 `INVARIANTS-CONTRACT` 버전을 올린다.
4. **트래커 결합 불변식 (어댑터 경유 슬롯 채움)** — `invariants.template.yaml`의 `<SLOT: project-adaptive invariants>`에 환경 특화 불변식을 SETTER가 짜 넣고, 필요한 새 체크·선결 조건(예: `issue-tracker-config`)을 어댑터(`specs/ISSUE-TRACKER-ADAPTER.md`)와 정합하게 엔진에 추가. **프레임워크 레포는 계속 중립** — 트래커 결합분은 SETTER 시점 인스턴스에만 존재한다.

### 블록된 것 / 전제

- 라이브 훅 계약 검증(위 3)은 실제 하네스가 있어야 하므로 STEP 1에서 확정 불가 — `emit()` 형태는 문서화된 계약에 맞춰 두고 STEP 2에서 실측한다.
- 새 체크 id 추가(위 4)는 `CHECKS` 레지스트리 확장이며, 새 체크가 로컬 원천만 읽는 한 중립 원칙을 유지한다.

---

## 10. 양방향 참조 맵

| 문서 | 본 명세와의 관계 |
|---|---|
| `templates/invariants.template.yaml` | 불변식 선언 스키마·파일럿·SLOT의 단일 원천 — 본 명세가 규율 |
| `templates/enforce.template.py` | 범용 엔진 — 병합·체크·훅 JSON 계약(`emit`) 구현 |
| `templates/SELF-CHECK.template.md` | 미러 패턴 — "기계적 주입/강제" + degraded 철학의 선례 |
| `specs/CYCLE-LOG.md` | 파일럿 대상 — 열림 판정(CYCLE-START/END/REOPEN)의 형식 원천 |
| `agents/SETTER.md` **S8.8** | 본 템플릿을 인스턴스로 조립·훅 배선 (§9 개요·§11 설계·§12 근거) — **S8.8로 이식 완료(라이브)**. 배선 정본 |
| `agents/orchestrator/ERROR-POLICY.md` | EX-15 / C FALLBACK — degraded 처리 정합 |
| `CLAUDE.md` §0.5 | degraded 철학(훅은 보강이지 전제가 아니다)의 상위 원천 |
| `specs/VERIFICATION.md` | STEP 2 훅 계약 검증이 따르는 지상검증 규율(POLICY-VERIFY) |

---

## 11. 인터뷰 + 합성 행동가이드 (STEP 2 설계 — 규율 프로즈)

> **본 절과 §12는 STEP 2 배선의 설계(프로즈)다.** 이 설계는 **`agents/SETTER.md` S8.8로 이식 완료**됐다(STEP-2a) — 라이브 절차의 정본은 SETTER.md S8.8이고, 본 절은 그 규율·근거의 단일 원천이다(둘을 함께 갱신).
> **미러·선례**: SETTER **S8.7**(SELF-CHECK 훅 설치)의 (1)~(5) 구조와 `CLAUDE.md` §0.5 degraded 철학을 그대로 따른다. 다른 점만 이 절이 새로 정의한다.

핵심 질문: *중립 적응형 템플릿(`invariants.template.yaml` + `enforce.template.py`)이 어떻게 배포별 실체 인스턴스가 되는가?* — SETTER가 **인터뷰로 답을 모으고(§11.1) → 답을 템플릿에 합성(§11.2)** 한다. 프레임워크 레포는 계속 100% 중립이고, 환경 특화(트래커 결합·실제 도구명·OS별 실행자)는 **전부 인스턴스에만** 존재한다.

### 11.1 인터뷰 질문 (SETTER가 묻거나 탐지)

S8.7이 "OS 탐지 → 훅 명령 선택 → 실행 검증"을 했듯, 아래도 *묻기보다 탐지 우선*이며 앞선 단계에서 이미 나온 답은 재사용한다(중복 질문 금지 — 인지 과부하 방지).

| # | 질문/탐지 | 출처·기본값 | 미충족(=아니오) 처리 |
|---|---|---|---|
| **①** 훅 설치 가능? | 이 환경에서 `PostToolUse`/`Stop` 훅을 설치·실행할 수 있나 | **S8.7과 동일 탐지 재사용**(후보 명령을 실제 실행) | **degraded**: 파일만 쓰고 훅 배선 스킵 + `.unavailable` 마커(EX-15 선례) → advisory 폴백 |
| **②** 트래커 운영? | 이슈 트래커를 쓰나 | **S5.7/S7.5 결과 재사용**(`dlc-meta/ISSUE-TRACKER.md` 존재 여부) — 다시 묻지 않음 | 트래커 결합 불변식 SLOT을 **비운다**(= 중립 유지) |
| **③** 각 범용 integrity 불변식: 켤까? tier? | `cycle-must-log` 등 불변식마다 enable 여부 + tier(`block\|warn\|advisory`) | 기본: **`cycle-must-log = warn`**(템플릿 기본) | 끄면 team 파일에서 제외 |
| **④** 개인 강화 원함? | 개인 편의(ergonomics) 불변식을 쓸 것인가 | — | **무관하게** 빈 `invariants.personal.yaml`(gitignore)을 시드한다(나중에 자유 추가 가능) |
| **⑤** OS/셸 | 훅 명령을 어느 실행자로 부를지 | **S8.7 OS 적응 로직 재사용** | 아래 §11.1.1 OS 적응 규칙 |
| **⑥** "사이클 액션" 도구명 집합 | PostToolUse `match`에 넣을 실제 도구명 | **환경 제공** — 실제 하네스 도구명(서브 디스패치·머지·커밋·트래커 전이). **하드코딩 금지** | 모르면 템플릿 예시 placeholder 유지 + tier를 advisory로 낮춰 오탐 위험 관리 |

- **①·⑤는 S8.7이 이미 하는 일의 재사용이다** — 새 인터뷰가 아니라 같은 탐지 결과를 이 배선에도 쓴다.
- **⑥이 핵심 중립 지점**: 템플릿의 `match: ["Task","Agent","Bash:*merge*",…]`는 *예시 placeholder*다. SETTER가 실제 하네스 도구명으로 치환하되, **공유 템플릿엔 일반형만** 남긴다(특정 하네스명 하드코딩 금지).

#### 11.1.1 OS 적응 훅 명령 규칙 (⑤ 상세 — 크로스플랫폼 필수)

> ⚠️ **별개 이슈 플래그(건드리지 않음)**: 기존 SELF-CHECK 훅은 Windows에서 `powershell -NoProfile …`을 쓴다(S8.7 (2) 표). 그 명령은 **Mac/Linux엔 `powershell`이 없어 깨진다.** 그대로 베끼면 안 된다. 본 STEP 2에서 SELF-CHECK 훅은 수정 대상이 아니다 — *플래그만* 한다(그 훅의 OS 이식성은 별도 사이클에서 다룬다).

- **권장 설계 — 훅이 Python을 직접 호출**: `<python 실행자> <enforce.py 절대경로> --event {PostToolUse|Stop}`.
  - 인코딩은 **enforce.py 내부에서 이미 UTF-8 강제**(stdout·stdin `reconfigure` + 선행 BOM 관용, TASK 1)하므로 **PowerShell UTF-8 래퍼가 불필요**하다 → 훅 명령이 OS 간 *거의 동일*하다. (대조: SELF-CHECK는 순수 텍스트 파일을 흘리느라 셸 인코딩에 노출돼 PowerShell 래퍼가 필요했다. 여기선 엔진이 자기 출력을 책임진다.)
  - OS별로 SETTER가 고르는 것은 **python 실행자 이름·경로**(`python3` / `python` / 절대경로)와, 필요 시 셸 래핑뿐. **PowerShell 전용 명령은 쓰지 않는다.**
  - **탐지는 추정하지 말고 실행해 확인한다**(S8.7 규율) — 고른 실행자로 `--event Stop`을 한 번 돌려 exit 0·무손상 출력을 실측.
- **degraded도 OS 공통**: 어느 OS든 훅을 못 걸면 같은 `.unavailable` 마커 + advisory 폴백.

### 11.2 합성 행동가이드 (응답 → 템플릿 채우기)

인터뷰 답을 아래대로 템플릿에 합성한다:

1. **team 파일 렌더** — 켠 integrity 불변식(③)을 `invariants.template.yaml`에서 골라 **`invariants.team.yaml`**(git 추적, `dlc-meta`의 `cycles/` 옆)로 렌더하고 각자의 tier를 박는다. `cycle-must-log`는 기본 warn. (POLICY-TEMPLATE-ADHERENCE — 손수 자유 작성 금지.)
2. **트래커 결합 불변식(SLOT)** — ②가 예면 `<SLOT>…<END SLOT>` 자리에 트래커 결합 불변식을 짜 넣고 `requires: [local-log-layer, issue-tracker-config]`를 준다(체크·선결 조건은 어댑터가 제공 — `specs/ISSUE-TRACKER-ADAPTER.md`). ②가 아니오면 **SLOT을 비운다**(중립). *새 선결 조건 `issue-tracker-config`·새 체크 id는 엔진 `CHECKS`·`_precondition_met` 확장이며, 로컬 원천만 읽는 한 중립 유지.*
3. **엔진 배치** — `enforce.template.py`를 인스턴스 실행 경로에 **`enforce.py`**로 사본 배치(개인·gitignore).
4. **경로 바인딩** — 훅 command의 env로 `AIDLC_INVARIANTS_DIR`(team·personal yaml이 있는 디렉토리)·`AIDLC_LOG_DIR`(메타 레포 루트 = `cycles/`의 부모)를 실제 절대경로로 바인딩한다.
5. **훅 병합** — `{공유리포}/.claude/settings.local.json`에 `PostToolUse`·`Stop` 훅을 **병합**(덮어쓰기 금지·기존 사용자 키 보존·`.bak` 백업)으로 추가한다. 명령은 §11.1.1 OS 적응(python 직접 호출·UTF-8은 엔진 내부 강제). PostToolUse 훅엔 ⑥의 도구명 집합을 반영한다.
   - `match` 필터링은 엔진이 하지만, 하네스가 훅 레벨 `matcher`도 지원하면 도구 집합을 그쪽에도 반영해 불필요한 엔진 기동을 줄일 수 있다(선택).
6. **개인 파일 시드** — ④와 **무관하게** 빈 `invariants.personal.yaml`(gitignore)을 시드한다.
7. **degraded** — ①이 아니오면 5(와 4의 훅 부분)를 스킵하고 `.unavailable` 마커를 남긴다(EX-15 / C FALLBACK). team·personal 파일과 엔진 배치는 그대로 한다 — 훅 없이도 엔진은 수동/타 경로로 호출 가능하고, 강제는 advisory 등가로 남는다.

#### 11.2.1 두 선언 파일의 위치 — 엔진 단일 base_dir 정합 (설계 결정)

엔진 `load_invariants(base_dir)`은 **`invariants.team.yaml`과 `invariants.personal.yaml`을 같은 디렉토리에서** 읽는다(§엔진 §2). 따라서 두 파일은 한 디렉토리(`AIDLC_INVARIANTS_DIR`)에 공존해야 한다. 추적 분리(POLICY-TRACKING)는 **위치가 아니라 `.gitignore`로** 실현한다:

- 권장: 둘 다 **`dlc-meta`**(= `AIDLC_INVARIANTS_DIR`)에 두되, `dlc-meta/.gitignore`가 `invariants.personal.yaml`(+`*.bak`)을 제외한다 → team은 추적·공유, personal은 개인.
- 이는 SELF-CHECK 개인 파일이 `.claude`에 사는 것과 위치가 다른데, *소비자가 다르기* 때문이다(SELF-CHECK는 `.claude`의 훅이, 불변식 personal yaml은 `AIDLC_INVARIANTS_DIR`을 읽는 엔진이 소비).
- 대안(개인 yaml을 `.claude`에 두고 싶으면): 엔진에 `AIDLC_PERSONAL_INVARIANTS_DIR`를 추가해 team·personal 디렉토리를 분리 — **STEP 2 엔진 확장**으로 플래그(현재 엔진은 단일 base_dir).

#### 11.2.2 추적 분리 (POLICY-TRACKING)

| 산출물 | 저장 | 추적 |
|---|---|---|
| `invariants.team.yaml` | `dlc-meta`(`cycles/` 옆) | **git 추적(팀 공유)** |
| `invariants.personal.yaml` | `AIDLC_INVARIANTS_DIR`(=`dlc-meta`, `.gitignore` 제외) | 개인·gitignore |
| `enforce.py`(엔진 인스턴스 사본) | 인스턴스 실행 경로 | 개인·gitignore |
| 훅 설정 `settings.local.json`(+`.bak`) | `{공유리포}/.claude/` | 개인·gitignore |
| `.unavailable` 마커 | `{공유리포}/.claude/` | 개인·gitignore |

> 요약: **team = `dlc-meta` 추적** / **personal + 엔진 + 훅 = 개인·gitignore**. SETTER는 배선 전 `.gitignore`가 개인 산출물 전부를 제외하는지 선확인한다(빠지면 팀원 머신 값이 서로 덮어씀 — S8.7 (0)과 동일 규율).

### 11.3 SHARED 템플릿 vs SETTER 합성 인스턴스

| SHARED (프레임워크 레포·git 추적·중립) | SETTER 합성 인스턴스 (배포별) |
|---|---|
| `templates/invariants.template.yaml` (스키마·파일럿·**빈** SLOT) | `invariants.team.yaml` (켠 불변식·tier·**채운** SLOT) |
| `templates/enforce.template.py` (엔진 로직) | `enforce.py` (실행 경로 사본) |
| `specs/INVARIANT-ENFORCEMENT.md` (본 규율) | 훅 설정·env 바인딩·개인 yaml·`.unavailable` |

- 프레임워크 레포는 **트래커·프로젝트·회사·OS를 무참조**로 유지한다. 실제 도구명(⑥)·트래커 결합 불변식(②)·OS별 python 실행자(⑤)는 **전부 인스턴스에만** 존재한다.

### 11.4 훅 계약 — 확정 (Claude Code hook contract)

> **출처**: `code.claude.com/docs/en/hooks.md` (v2.1.2xx, 2026-09-11 fetch — claude-code-guide 에이전트가 공식 문서 회수·대조). 아래는 *문서화된 계약에 대고 확정*한 형태이며, `enforce.template.py` §7 `emit()`이 이 계약의 단일 구현 원천이다.

**(a) warn — 형태 확정 + 실측 확인**

- Stop: `{"systemMessage": <msg>}`
- PostToolUse: `{"systemMessage": <msg>, "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": <msg>}}`
- 두 형태 모두 cp949 콘솔·`PYTHONIOENCODING` 없이 **크래시 없이 exit 0**으로 방출됨이 실측 확인됨(한국어·em-dash 포함). 무발견/degraded 경로는 **빈 출력 + exit 0**도 확인. 계약 문서와 일치.

**(b) block — 형태 확정 + 차단 채널은 exit 2**

- 형태: `{"decision": "block", "reason": <msg>}`. 이는 **Stop**에서 그 stop을 거부하고 `reason`을 다음 턴에 되먹이는 올바른 형태다(문서 확인).
- **단, exit code 2 가 신뢰 가능한 차단 채널이다.** `exit 0 + decision:block`은 *자문(advisory)에 그칠 수 있다* — 특히 **PostToolUse는 사후 실행**이라 그 시점의 block은 도구 실행을 되돌리지 못한다. 따라서 엔진은 **block JSON을 stdout에 먼저 쓴 뒤 exit 2**로 나간다(§엔진 §7·TASK 1 실측: block tier → exit 2 + JSON, 확인됨).
- **block은 Stop·PreToolUse에서 실효적이다.** **PostToolUse는 사후 실행이므로 block을 켜지 말고 warn으로 둔다**(파일럿 `cycle-must-log`의 PostToolUse 바인딩이 기본 warn인 이유).

**(c) Stop-block 무한루프 가드 — `stop_hook_active`**

- Stop 훅이 block을 내면 하네스가 stop을 거부하고 다음 턴을 돌리는데, 그 턴 경계에서 훅이 또 block을 내면 **차단→재실행→재차단 무한루프** 위험이 있다(문서 경고).
- 하네스는 재진입한 Stop 훅 입력에 **`stop_hook_active: true`**(boolean)를 실어 준다. 엔진은 *Stop이고 `stop_hook_active`가 true면 block을 warn으로 강등*해 루프를 끊는다(§엔진 `emit()`·TASK 1 실측: 강등되어 exit 0·warn, 확인됨). PostToolUse는 턴을 재개시키지 않으므로 이 가드의 영향을 받지 않는다.

**(d) 배선 시 라이브 파이어 (POLICY-VERIFY — block tier를 켤 때)**

- warn·block 각각 (a) 위반을 유발 → (b) 하네스가 그 JSON을 실제로 소비(경고 표시/차단)하는지 확인 → (c) 명령·출력 원문을 보고에 싣는다.
- **세션 내 즉석(throwaway) 라이브 파이어는 신뢰할 수 없다** — 훅 설정을 방금 쓴 세션에서는 settings 워처의 리로드 타이밍 탓에 *이번 턴*엔 아직 훅이 안 걸릴 수 있다. **확정적 라이브 파이어는 배선 시점 / 새 세션에서** 한다(오케스트레이터·메인 세션 책임). 불일치가 확인되면 `emit()` 매핑을 정정하고 `INVARIANTS-CONTRACT` 버전을 올린다.

---

## 12. SETTER 반영 대상 — S8.8 (이식 완료 — `agents/SETTER.md` S8.8 라이브)

> **본 절의 초안은 `agents/SETTER.md`에 실제 절 S8.8로 이식 완료됐다 (STEP-2a).** 배선의 *정본은 SETTER.md의 S8.8*이며, 아래는 그 설계 근거·요약을 남긴 것이다. 구조는 S8.7(자가점검 훅 설치)의 (0)~(6)을 미러하며, 불변식 특유의 차이(team=신규만 / 엔진·훅·개인=신규·합류·보수, 두 yaml co-locate §11.2.1, python 직접 호출 훅 §11.1.1)를 명시한다. 향후 배선 규율 변경은 SETTER.md S8.8과 본 절을 함께 갱신한다(원칙 8 — 단일 원천 정합).
> **모드 규칙(§ SETTER 모드표 반영)**: team yaml은 *공유 인스턴스*라 **신규**만 생성하고 **합류**는 clone으로 받는다(재생성 금지). 반면 **엔진 사본·훅·개인 yaml·`.unavailable`은 머신 로컬**이라 **신규·합류·보수 모두 수행**한다(선례: S8.7이 개인 훅 산출물을 세 모드 모두에서 설치).

#### S8.8. 불변식 강제 배선 (team=신규만 / 엔진·훅·개인=신규·합류·보수)

> *목적*: 중대·반복 유실 절차(파일럿: 사이클 로깅)를 *모델의 자발적 준수*에서 *프로그램(훅) 강제*로 승격한다(POLICY-INVARIANT). S8.7이 정체성 재주입을 기계화했듯, 본 절은 절차 강제를 기계화한다.
> *산출 위치·추적*: §11.2.1·§11.2.2 — team은 `dlc-meta`(추적), 엔진·훅·개인 yaml·마커는 개인(gitignore).
>
> **(0) 추적 제외 선결 확인** — `{공유리포}/.gitignore`(및 `dlc-meta/.gitignore`)가 개인 산출물을 모두 제외하는지 확인하고 빠졌으면 *배선 전에* 채운다: `.claude/settings.local.json`·`.bak`·`.claude/*enforce*.py`(엔진 사본)·`.claude/*.unavailable`·`invariants.personal.yaml`. (S8.7 (0)과 동일 규율.)

**(1) team 파일 렌더** (신규만) — 원본: `{공유리포}/templates/invariants.template.yaml` (POLICY-TEMPLATE-ADHERENCE).
- 산출: `{메타 레포}/invariants.team.yaml`(추적). 인터뷰 ③이 켠 불변식만 남기고 각 tier를 확정(`cycle-must-log` 기본 warn).
- ②(트래커 운영)면 `<SLOT>`에 트래커 결합 불변식을 짜 넣고 `requires:[local-log-layer, issue-tracker-config]`. 아니면 SLOT을 비운다.
- **POLICY-ENCODING 필수**: UTF-8(BOM 없음)·LF 직접 쓰기.
- *합류*는 이 파일을 clone으로 받는다 — **재생성 금지**(팀원 것 덮어쓰기 방지).

**(2) 엔진 사본 + 개인 yaml 시드** (신규·합류·보수) — `enforce.template.py` → 인스턴스 `enforce.py`(개인·gitignore) 배치 + 빈 `invariants.personal.yaml`(개인·gitignore, ④ 무관하게) 시드.

**(3) 훅 명령 생성 — OS 적응 (python 직접 호출)** — 인코딩은 엔진 내부가 강제하므로 **PowerShell 전용 래퍼 없음**(§11.1.1). 실행 환경을 탐지해 아래처럼 python 실행자만 OS별로 고른다:

| 환경 | 명령 (형태) |
|---|---|
| POSIX (Linux·macOS·Git Bash·WSL) | `python3 "{enforce.py 절대경로}" --event {PostToolUse\|Stop}` |
| Windows | `python "{enforce.py 절대경로}" --event {PostToolUse\|Stop}` (또는 절대경로 실행자) |

> **탐지는 실행해서 확인**한다 — 고른 실행자로 `--event Stop`을 한 번 돌려 exit 0·무손상을 실측(S8.7 규율). 실행자 이름·경로만 다르고 **명령 골격은 OS 공통**이다. 새 환경이 나오면 같은 원칙으로 후보를 추가하되 **공유 룰북에 OS를 하드코딩하지 않는다**(적응형 어댑터 규율).

**(4) 설정 병합** — `{공유리포}/.claude/settings.local.json`에 `PostToolUse`·`Stop` 훅을 **병합**(덮어쓰기 금지·기존 키 보존·`.bak` 백업). 각 훅 command에 (3) 명령 + env `AIDLC_INVARIANTS_DIR`·`AIDLC_LOG_DIR`(절대경로) 바인딩. PostToolUse는 ⑥ 도구명 집합을 `match`(및 지원 시 훅 `matcher`)에 반영. **중복 누적 금지**(같은 enforce.py를 가리키는 항목이 있으면 교체 — 보수 멱등성).

**(5) 설치 검증 (POLICY-VERIFY — 필수)** — 클레임이 아니라 실측:
- (3) 명령을 **실제로 실행**해 방출을 본다. warn 유발 픽스처(열린 사이클 등)로 warn JSON이 나오는지, 무발견에서 빈 출력·exit 0인지 확인(TASK 1에서 이미 실증한 형태).
- `settings.local.json`이 유효 JSON이고 기존 사용자 키 보존.
- `{공유리포}`·`{메타 레포}`에서 개인 산출물이 추적되지 않는지(gitignore 정상), team yaml은 추적되는지 확인.
- **block tier를 켰다면 라이브 파이어로 차단을 실측**(§11.4) — 미검증 시 `INVARIANTS-CONTRACT` 정정 대비.

**(6) 설치 불가 확정 — degraded (EX-15 / C FALLBACK)** — S8.7 (5)와 동일 사상:
- **중단하지 않는다**(ABORT·PAUSE 격상 금지). team·personal·엔진 배치는 마치고 훅만 스킵.
- `{공유리포}/.claude/*enforce*.unavailable`(개인·gitignore)에 실패 층위·시도 명령·에러 요지를 남긴다 → 이후 재시도 폭주 억제. degraded는 어느 OS든 공통.
- T3(사용자 명시 호출)은 마커를 무시하고 재시도, 성공 시 마커 삭제(멱등).

---

## 변경 이력

본 명세 v1.0 — 불변식 강제 규율(POLICY-INVARIANT) 신설. STEP 1(템플릿·명세만): `invariants.template.yaml`(선언 단일 원천 + `cycle-must-log` 파일럿 + `<SLOT>`), `enforce.template.py`(중립·degraded-safe 범용 엔진, stdlib-only YAML 폴백), 본 명세 3종 추가.

근거: MD 절차는 모델의 자발적 준수에 의존해 압축·긴 사이클에서 반복 유실된다(리포 루트 `CLAUDE.md` §0 실측 실패 모드). SELF-CHECK 훅의 "기계적 주입" 해법을 *절차 강제*로 일반화했다.

STEP 2(SETTER 조립·훅 배선·라이브 계약 검증·트래커 결합 슬롯 채움)의 *실행*(SETTER.md 재배선·settings.json·CLAUDE.md 수정)은 본 변경에 포함되지 않는다 (§9).

STEP-2 보강(설계 프로즈 — SETTER.md 무수정): §11(인터뷰 6문항 + 합성 행동가이드 + OS 적응 훅 규칙 + 추적 분리)·§12(SETTER **S8.8** 초안, S8.7 미러) 추가. `enforce.template.py`는 stdout·stdin UTF-8 강제 + 선행 BOM 관용으로 보강돼 cp949 콘솔에서도 자기 출력으로 크래시하지 않음이 실증됨(warn 형태·degraded 경로 확인). 훅은 python 직접 호출로 OS 중립(PowerShell 전용 금지).

STEP-2a(실제 배선): (1) **훅 계약 확정** — 공식 문서(`code.claude.com/docs/en/hooks.md`, v2.1.2xx, 2026-09-11 fetch) 대조로 §11.4를 확정. warn 형태 정합, **block은 exit code 2가 신뢰 가능한 차단 채널**(exit 0 + decision:block은 자문에 그칠 수 있음, 특히 PostToolUse 사후 실행), block은 Stop·PreToolUse에서 실효(PostToolUse는 warn 유지), **Stop-block 무한루프는 `stop_hook_active`로 가드**. (2) **엔진 반영** — `enforce.template.py` `emit()`/`main()`이 block tier → JSON + exit 2, Stop 재진입 시 block→warn 강등을 구현(서브프로세스 단위 검증: block→exit2+JSON / warn→exit0+JSON / 무발견·degraded→exit0+빈출력 / Stop+stop_hook_active→강등, 전부 통과). (3) **S8.8 이식** — §12 초안을 `agents/SETTER.md`에 라이브 절 S8.8로 이식(S8.7 (0)~(6) 미러, team=신규만·엔진/훅/개인=신규·합류·보수, 두 yaml co-locate §11.2.1, python 직접 호출 훅, S9 항목 17·파일트리·참조표 갱신). 잔여: block tier 라이브 파이어(새 세션/오케스트레이터).

향후 변경은 깃 PR/머지 (원칙 8).

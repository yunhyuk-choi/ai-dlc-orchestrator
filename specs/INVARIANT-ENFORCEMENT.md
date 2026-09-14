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
2. **훅 배선** — `{공유리포}/.claude/settings.local.json`에 `PostToolUse`·`Stop` 훅을 *병합*(덮어쓰기 금지)으로 추가하고, **`--base-dir` CLI 인자**로 실제 절대 경로를 바인딩(Claude Code 훅엔 `env` 필드가 없으므로 env로 바인딩하지 않는다 — §11.1.1). OS·셸 적응은 S8.7 패턴 재사용.
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

- **권장 설계 — 훅이 Python을 직접 호출 + 경로는 CLI 인자로**: `<python 실행자> <enforce.py 절대경로> --event {PreToolUse|PostToolUse|Stop} --base-dir <dlc-meta 절대경로>`.
  - **배포별 절대경로는 `--base-dir` CLI 인자로 넘긴다 — `env` 필드가 아니다.** ⚠️ **Claude Code 훅 command 객체엔 `env` 필드가 없다**(공식 문서 인식 필드: `type`·`command`·`args`·`if`·`timeout`·`statusMessage`·`shell`·`async`·`asyncRewake` — env 없음; 훅은 부모 env를 상속할 뿐이라 command에 얹은 `env`는 *조용히 무시*된다). 종전 설계가 `env`로 `AIDLC_INVARIANTS_DIR`/`AIDLC_LOG_DIR`을 실었던 것은 **설치돼도 죽는(silently dead) 결함**이었다 — CLI 인자로 교체했다. `--base-dir` 하나가 두 경로를 모두 준다(§11.2.1 상 둘 다 `dlc-meta`; 필요 시 `--invariants-dir`/`--log-dir`로 개별 지정, `env`는 CLI 부재 시 하위호환 폴백으로만 남는다). CLI 인자는 **셸 독립**이라 인라인 `VAR=x`(cmd.exe/powershell에서 깨짐·문서의 인라인 형태는 `shell:"bash"` 요구)나 래퍼 파일 없이 어느 기본 셸에서든 동작한다.
  - 인코딩은 **enforce.py 내부에서 이미 UTF-8 강제**(stdout·stdin `reconfigure` + 선행 BOM 관용, TASK 1)하므로 **PowerShell UTF-8 래퍼가 불필요**하다 → 훅 명령이 OS 간 *거의 동일*하다. (대조: SELF-CHECK는 순수 텍스트 파일을 흘리느라 셸 인코딩에 노출돼 PowerShell 래퍼가 필요했다. 여기선 엔진이 자기 출력을 책임진다.)
  - OS별로 SETTER가 고르는 것은 **python 실행자 이름·경로**(`python3` / `python` / 절대경로)뿐. **PowerShell 전용 명령은 쓰지 않는다.**
  - **탐지는 추정하지 말고 실행해 확인한다**(S8.7 규율) — 고른 실행자로 `--event Stop --base-dir <dlc-meta>`를 한 번 돌려 exit 0·무손상 출력을 실측.
- **degraded도 OS 공통**: 어느 OS든 훅을 못 걸면 같은 `.unavailable` 마커 + advisory 폴백.

### 11.2 합성 행동가이드 (응답 → 템플릿 채우기)

인터뷰 답을 아래대로 템플릿에 합성한다:

1. **team 파일 렌더** — 켠 integrity 불변식(③)을 `invariants.template.yaml`에서 골라 **`invariants.team.yaml`**(git 추적, `dlc-meta`의 `cycles/` 옆)로 렌더하고 각자의 tier를 박는다. `cycle-must-log`는 기본 warn. (POLICY-TEMPLATE-ADHERENCE — 손수 자유 작성 금지.)
   - **결정적 렌더(D2 — 라이브 정본: SETTER S8.8 (1) 레시피)**: *같은 인터뷰 답(③⑥②) + 같은 템플릿 버전 → 바이트 동일 team.yaml*이어야 한다. "SLOT을 비운다"·헤더 처리를 추측으로 메우면 런마다 산출이 갈려 POLICY-TEMPLATE-ADHERENCE를 어긴다. 규칙(요약): ⓐ 템플릿을 그대로 복사 → ⓑ 스키마-닥 헤더를 **고정 provenance 헤더**로 교체(`INVARIANTS-CONTRACT` 값은 템플릿에서 복사·하드코딩 금지, 예시 본문은 버림 — 정본은 템플릿) → ⓒ 끈 불변식 블록은 통째 삭제, 켠 것은 `tier`·`match`만 치환 → ⓓ **"SLOT을 비운다" = `# <SLOT…>`부터 `# <END SLOT…>`까지 마커 포함 전삭제**(트래커=예면 실제 불변식으로 치환) → ⓔ 말미 LF 하나. 전체 레시피·고정 헤더 텍스트는 SETTER S8.8 (1)이 정본.
2. **트래커 결합 불변식(SLOT)** — ②가 예면 `<SLOT>…<END SLOT>` 자리에 트래커 결합 불변식을 짜 넣고 `requires: [local-log-layer, issue-tracker-config]`를 준다(체크·선결 조건은 어댑터가 제공 — `specs/ISSUE-TRACKER-ADAPTER.md`). ②가 아니오면 **SLOT을 비운다**(중립). *새 선결 조건 `issue-tracker-config`·새 체크 id는 엔진 `CHECKS`·`_precondition_met` 확장이며, 로컬 원천만 읽는 한 중립 유지.*
3. **엔진 배치** — `enforce.template.py`를 인스턴스 실행 경로에 **`enforce.py`**로 사본 배치(개인·gitignore).
4. **경로 바인딩** — 훅 command 문자열의 **CLI 인자 `--base-dir <dlc-meta 절대경로>`**로 바인딩한다(team·personal yaml 위치이자 `cycles/`의 부모 = 두 경로 동일, §11.2.1). **`env` 필드를 쓰지 않는다** — Claude Code 훅엔 env 필드가 없어 무시된다(§11.1.1).
5. **훅 병합** — `{공유리포}/.claude/settings.local.json`에 `PostToolUse`·`Stop` 훅을(block-tier가 실행 전 차단을 요구하면 `PreToolUse`도) **병합**(덮어쓰기 금지·기존 사용자 키 보존·`.bak` 백업)으로 추가한다. 명령은 §11.1.1 OS 적응(python 직접 호출 + `--base-dir` CLI·UTF-8은 엔진 내부 강제). PostToolUse/PreToolUse 훅엔 ⑥의 도구명 집합을 반영한다.
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

**(b) block — 이벤트별 실효 차단점 (block-tier semantics per event)**

`tier: block`이 *어디서 실제로 막는지*는 이벤트마다 다르다. 엔진(`emit()`)이 이벤트별로 형태를 달리 낸다:

| 이벤트 | block 시 엔진 방출 | 실효 | 켜도 되나 |
|---|---|---|---|
| **PreToolUse** | `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":<msg>}}` + exit 0 | **진짜 차단** — 도구 실행 *전* 을 막는 유일한 지점(강제성의 실체) | ✅ (실행 전 차단이 필요한 block-tier의 권장 지점) |
| **Stop** | `{"decision":"block","reason":<msg>}` + **exit 2** | **진짜 차단** — 턴 종료(stop)를 거부하고 `reason`을 다음 턴에 되먹임 | ✅ (턴 경계 백스톱) |
| **PostToolUse** | `{"decision":"block","reason":<msg>}` + exit 2 | **자문뿐** — 도구가 *이미 실행된 뒤*라 되돌리지 못하고, exit 2는 Claude에 주입되는 피드백에 그침 | ⚠️ 켜지 말 것 → warn 사용 |

- **exit code 2 가 Stop·PostToolUse의 신뢰 채널이다** — `exit 0 + decision:block`은 자문에 그칠 수 있으므로 엔진은 block JSON을 stdout에 먼저 쓴 뒤 exit 2로 나간다. **PreToolUse는 구조화된 `permissionDecision:deny`가 권위 채널**이라 exit 0을 쓴다(§엔진 §7 실측 확인).
- **PostToolUse는 사후 실행이므로 block을 켜지 말고 warn으로 둔다**(파일럿 `cycle-must-log`의 PostToolUse 바인딩이 기본 warn인 이유). 실행 전 진짜 차단이 필요하면 **PreToolUse에 바인딩**한다.
- **PreToolUse는 엔진이 지원한다**(F4 구현 완료 — PostToolUse와 동일하게 `match`로 도구를 좁히고, PreToolUse는 재진입 루프가 없어 `stop_hook_active` 가드가 불필요하다. 서브프로세스 실측: PreToolUse+block → deny JSON+exit 0, PreToolUse+warn → systemMessage+additionalContext, no-match → 무발견, 확인됨).

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
> **(0) 추적 제외 선결 확인** — `{공유리포}/.gitignore`(및 `dlc-meta/.gitignore`)가 개인 산출물을 모두 제외하는지 확인하고 빠졌으면 *배선 전에* 채운다: `.claude/settings.local.json`·`.bak`·**`.corrupt`((4) 깨진-설정 백업 — 사용자 `permissions` 포함, 반드시 미추적; `settings.local.json*` 글롭 한 줄이 셋을 다 덮음)**·`.claude/enforce.py`(엔진 사본)·`.claude/invariants-enforce.unavailable`·**`.claude/__pycache__/`(D4 — import 시 바이트코드 누출 방어)**·`invariants.personal.yaml`. (S8.7 (0)과 동일 규율.)
> **(D3) 공유 `.gitignore`는 추적 파일이다** — 실제로 줄을 *추가했다면* 그건 개인 산출물과 구분되는 **추적 변경**이므로 별도로 커밋한다(원칙 8 — 공유 변경은 git 단일 원천; `dlc-meta/.gitignore`는 S8.6 push 규율, `{공유리포}/.gitignore`는 팀 공유 레포 흐름). 프레임워크 배포 `.gitignore`에 이미 실려 있으면 no-op이라 커밋할 것이 없다(happy path·멱등). 라이브 정본: SETTER S8.8 (0).

**(1) team 파일 렌더** (신규만) — 원본: `{공유리포}/templates/invariants.template.yaml` (POLICY-TEMPLATE-ADHERENCE).
- 산출: `{메타 레포}/invariants.team.yaml`(추적). 인터뷰 ③이 켠 불변식만 남기고 각 tier를 확정(`cycle-must-log` 기본 warn).
- ②(트래커 운영)면 `<SLOT>`에 트래커 결합 불변식을 짜 넣고 `requires:[local-log-layer, issue-tracker-config]`. 아니면 SLOT을 비운다.
- **POLICY-ENCODING 필수**: UTF-8(BOM 없음)·LF 직접 쓰기.
- *합류*는 이 파일을 clone으로 받는다 — **재생성 금지**(팀원 것 덮어쓰기 방지).

**(2) 엔진 사본 + 개인 yaml 시드** (신규·합류·보수) — `enforce.template.py` → 인스턴스 `enforce.py`(개인·gitignore) 배치 + 빈 `invariants.personal.yaml`(개인·gitignore, ④ 무관하게) 시드.

**(3) 훅 명령 생성 — OS 적응·자기완결 (python 직접 호출 + `--base-dir` CLI)** — 인코딩은 엔진 내부가 강제하므로 **PowerShell 전용 래퍼 없음**(§11.1.1). 배포별 절대경로는 **`--base-dir` CLI 인자**로 넘긴다(env 필드 아님 — Claude Code 훅엔 env 필드가 없다). 실행 환경을 탐지해 아래처럼 python 실행자만 OS별로 고른다:

| 환경 | 명령 (형태) |
|---|---|
| POSIX (Linux·macOS·Git Bash·WSL) | `python3 "{enforce.py 절대경로}" --event {PreToolUse\|PostToolUse\|Stop} --base-dir "{메타 레포}"` |
| Windows | `python "{enforce.py 절대경로}" --event {PreToolUse\|PostToolUse\|Stop} --base-dir "{메타 레포}"` (또는 절대경로 실행자) |

> **탐지는 실행해서 확인**한다 — 고른 실행자로 `--event Stop --base-dir "{메타 레포}"`를 한 번 돌려 exit 0·무손상을 실측(S8.7 규율). 실행자 이름·경로만 다르고 **명령 골격은 OS 공통·셸 독립**이다(인라인 `VAR=x` env 문법 없음). block tier는 실효 이벤트(PreToolUse·Stop)에만 바인딩(§11.4 (b)).

**(4) 설정 병합** — `{공유리포}/.claude/settings.local.json`에 `PostToolUse`·`Stop`(block-tier면 `PreToolUse`도) 훅을 **병합**(덮어쓰기 금지·기존 키 보존·`.bak` 백업). 각 훅 command는 (3)의 **자기완결 명령 문자열**(경로는 `--base-dir` CLI)이다 — **`env` 필드를 쓰지 않는다**(Claude Code 훅에 없어 무시됨). PostToolUse/PreToolUse는 ⑥ 도구명 집합을 `match`(및 지원 시 훅 `matcher`)에 반영. **중복 누적 금지**(같은 enforce.py를 가리키는 항목이 있으면 교체 — 보수 멱등성).

**(5) 합성 후 자가검증 게이트 (POLICY-VERIFY — 필수. 통과 전 성공 보고 금지 — failover 1)** — 클레임이 아니라 실측. 라이브 정본: SETTER S8.8 (5).
- **1차 단언 = POSITIVE 픽스처(D1) + 렌더 command 그대로 실행(D5)**: 렌더+매치+경로 바인딩(`--base-dir`)을 증명하는 유일한 런은 warn을 *유발*하는 실행뿐이다. **settings에 기록된 렌더 PostToolUse command 문자열을 그대로**(그 안의 `--base-dir "{메타 레포}"` 포함, env 필드 없음) 서브프로세스로 돌리되 **끝에 `--log-dir <빈 `cycles/` 임시 디렉토리>`만 덧붙이고**(라이브 오염 방지 — `--log-dir`이 `--base-dir`의 로그 부분을 이김, invariants는 실제 렌더에서 로드) + ⑥ `match` stdin으로 **warn JSON 방출(비어있지 않음, exit 0)**을 확인한다. *env를 손수 걸지 않는다* — 종전 게이트가 자기 env로 통과해 죽은 라이브 훅을 놓친 구조적 사각(D5·실측된 PR-blocking 결함)을 막는다. **빈 출력이면 FAIL**(D1 거짓통과 또는 D5 호출 형태 깨짐). 2차로 Stop+빈 cycles(빈 출력) 및 PostToolUse+열린 cycle(빈 출력 = 판별) 확인. **(조건부 F4)** PreToolUse block 바인딩을 렌더했으면 렌더 PreToolUse command + `--log-dir 빈 cycles` + 매치 stdin → deny JSON(exit 0) 단언(결정적 서브프로세스 단언이라 게이트 PASS 조건).
- 기록된 훅 command에 **`env` 필드가 없고 경로가 `--base-dir`로** 실려 있는지 확인(D5 회귀 방어).
- `settings.local.json`이 유효 JSON이고 기존 `UserPromptSubmit`·`permissions` 보존.
- `{공유리포}`·`{메타 레포}`에서 개인 산출물이 추적되지 않는지(gitignore 정상), team yaml은 추적되는지 확인.
- **block tier를 켰다면 라이브 파이어로 차단을 실측**(§11.4) — 확정 파이어는 새 세션 몫이라 게이트 PASS 조건은 아니다(게이트 1차 단언은 POSITIVE warn 방출). 미검증 시 `INVARIANTS-CONTRACT` 정정 대비.
- **게이트 실패 시**: team·personal·엔진 파일은 그대로 두고, (4)에서 병합한 라이브 훅을 `.bak`에서 롤백해 *망가진 라이브 훅을 남기지 않으며*, (6) degraded로 내려간다(EX-15 — 중단 아님).

**(6) 설치 불가 확정 — degraded (EX-15 / C FALLBACK)** — S8.7 (5)와 동일 사상:
- **중단하지 않는다**(ABORT·PAUSE 격상 금지). 가능한 산출물은 마치고 훅만 스킵.
- `{공유리포}/.claude/*enforce*.unavailable`(개인·gitignore)에 실패 층위·시도 명령·에러 요지를 남긴다 → 이후 재시도 폭주 억제. degraded는 어느 OS든 공통.
- **degrade 경로는 이름 있는 결과로 착지한다(failover 4)** — 훅-불가 / no-python / dlc-meta 쓰기불가 / 템플릿 누락 / (5) 게이트 실패. 각 경로마다 *무엇이 여전히 쓰였는지* + 마커 층위 + 시끄러운 보고를 남긴다(조용한 반쪽 세팅 금지). 경로별 표는 SETTER S8.8 (6)이 정본.
- **멱등(failover 2·3)**: 훅 항목은 append 아닌 교체, 개인 yaml은 seed-if-absent(사용자 편집 보존), settings.local.json이 깨졌으면 파괴 않고 `.corrupt`로 보존+보고+degraded. 라이브 정본은 SETTER S8.8 (2)·(4).
- T3(사용자 명시 호출)은 마커를 무시하고 재시도, 성공 시 마커 삭제(멱등).

---

## 13. 진화 제안 — 키드(keyed) 상태머신 강제화 (동시성-안전 block)

> **상태: 제안 (검토용) — 미구현.** 본 절은 *설계 제안*이며, `enforce.template.py`·`invariants.template.yaml`·`SETTER.md` 어느 것도 아직 바꾸지 않는다(스펙 온리). 채택 시의 *함의된 코드 변경*을 §13.6에 명시하되 여기서는 구현하지 않는다.
> **거버넌스 경로 = DP-9 (프레임워크 진화).** 본 제안은 관찰된 실패 모드(동시성 하에서 block 불가)를 프레임워크 룰북 변경으로 승격하는 것이므로 `specs/EVOLUTION.md` DP-9 게이트(항상 사용자 컨펌)를 따른다. 단 EVOLUTION §의 *자동 경로*는 `dlc-meta` 인스턴스 전용(공유 룰북 불가침, D-Stage3-6)이므로, **공유 프레임워크 레포(`enforce.template.py`·템플릿·본 명세)를 건드리는 본 변경은 자동 경로 밖 — 원칙 8 PR/머지(사람 큐레이션)** 로만 반영한다(EVOLUTION §3.E·§4.3의 "공유 귀속분" 경로). 본 DRAFT PR이 그 통로다.

### 13.1 문제 — 전역 boolean은 동시성 하에서 block-안전하지 않다 (코드 대조 확인)

현행 파일럿 `cycle-must-log`(§7)은 **공유 `dlc-meta`의 모든 `cycles/*/audit.md`에 대한 전역 boolean**("*어떤* 사이클이든 열려 있나?")으로 동작한다. **작업 아이템/세션 키가 없다.** 코드로 확인된 정확한 형태:

- `_open_cycles(log_dir)` (enforce.template.py) — `cycles/` 하위 **전체** audit.md를 순회해 열린 것들의 리스트를 반환. 스코프는 로그 계층 전체(전역).
- `check_open_cycle_record_exists(log_dir)` (PostToolUse) — `_open_cycles`가 **하나라도** 있으면 위반 아님. → *열림이 하나라도 있으면 모두를 만족*.
- `check_no_stale_open_cycle(log_dir)` (Stop) — `_open_cycles`가 **하나라도** 있으면 위반. → *열림이 하나라도 있으면 모두가 걸림*.
- `main()`은 stdin 훅 JSON에서 `tool_name`·`tool_input`·`stop_hook_active`만 뽑는다. **`session_id`·`cwd`는 현재 추출하지 않는다**(확인: 해당 키에 대한 참조 없음). 체크 함수는 전부 시그니처 `fn(log_dir)` — *현재 세션을 식별할 인자가 아예 없다*.

**동시성(워커 4개, 공유 `dlc-meta` 1개) 하의 귀결** — block-tier를 켤 수 없는 이유:

| 지점 | 현행 동작 | 동시성 하 결함 |
|---|---|---|
| **Stop** `no-stale-open-cycle` | 열림이 하나라도 있으면 위반 | 워커 A의 *아직 열린* 사이클이 워커 B의 Stop을 건다 → **교차오염**. B는 자기 일을 다 마쳤어도 A 때문에 차단된다 → block이면 B가 못 끝냄. |
| **PostToolUse** `open-cycle-record-exists` | 열림이 하나라도 있으면 만족 | *동시에 너무 느슨* — A의 열린 사이클이 B의 디스패치 위반을 가려, B가 자기 사이클을 안 열어도 경고가 안 뜬다(거짓 만족). |
| 종합 | 전역 상태 | PostToolUse에선 **너무 느슨**(아무 열림이나 전부 만족)이고 Stop에선 **너무 엄격**(아무 열림이나 전부 차단). warn이 무해한 유일한 이유는 *차단하지 않아서*일 뿐 — **block은 오늘 안전하게 켤 수 없다.** |

> 요컨대 상태의 *스코프*와 강제의 *스코프*가 어긋나 있다: 강제는 개별 작업 아이템 단위여야 하는데 상태는 전역 단위다. block을 안전하게 하려면 상태를 **작업 아이템 키로 분할**해야 한다.

### 13.2 키(key) — 작업 아이템/위임 식별자

각 작업 아이템(=오케스트레이터의 한 위임/한 사이클)에 안정적 키를 붙인다. 엔진은 훅 시점에 *지금 이 실행의 키*를 얻어 **그 키의 상태만** 읽는다.

| 후보 키 | 엔진 가시성 | 중립성 | 트레이드오프 | 판정 |
|---|---|---|---|---|
| **`session_id`** (훅 JSON 제공) | ★ 훅 JSON에 이미 실려 옴 — 엔진이 stdin에서 직접 읽음(플러밍 0) | ★ 완전 중립(트래커·프로젝트 무참조) | 동시 워커는 각자 별도 Claude Code 세션이라 `session_id`가 *자연히 워커 단위로 분할*된다(=동시성 축 그 자체). 다만 *쓰는 쪽*(오케스트레이터)이 index 파일을 같은 키로 남기려면 자기 `session_id`를 알아야 한다(§13.7 미결). 한 세션이 여러 위임을 직렬로 돌리면 세션=사이클이 1:1이 아닐 수 있다. | **1차 권장** — 읽기 측이 공짜·중립. 쓰기 측 키 획득만 해결하면 됨. |
| **위임 id(delegation id)** — 오케스트레이터 생성 | 엔진은 env/CLI로 넘겨받아야 봄(플러밍 필요) | ★ 완전 중립 | 오케스트레이터가 디스패치마다 생성하므로 세션 대 사이클 1:1을 *정확히* 표현. 대신 오케스트레이터가 그 키를 *엔진이 읽는 경로*(디스패치별 env/arg)로 심어야 함. | **폴백/보강** — `session_id`를 세분화해야 할 때(한 세션 다중 위임) 오케스트레이터가 명시 키를 준다. |
| **티켓 키**(예: Jira 이슈) | 어댑터 경유로만 | ✗ **도메인 결합** — 트래커에 묶임 | 사람에겐 의미 있으나 프레임워크 중립 원칙 위반. | **기각(키로는)** — 중립 유지. 티켓↔사이클 바인딩은 별개 관심사(POLICY-ISSUE-TRACKING)로 두고, 강제 키로는 쓰지 않는다. |

**권장: `session_id`를 1차 키로, 오케스트레이터-제공 키(위임 id)를 선택적 오버라이드로.** 엔진 키 해석 우선순위(§13.5): `--work-key` CLI > `AIDLC_WORK_KEY` env > 훅 JSON `session_id`. 셋 다 없으면 **키 부재 → no-op(degraded, 차단 아님)**. 프로젝트·트래커 무참조를 유지한다.

> 키는 파일명 세그먼트가 되므로 엔진은 이를 **안전화(sanitize)**한다(영숫자·`-`·`_`만 허용, 그 외는 `_`로 치환, 길이 상한). 부정 경로·구분자 주입 방지.

### 13.3 인덱스(index) — `key → status` 맵, per-key 파일

`key → status`를 O(1)로 조회·갱신하기 위한 저장 구조.

**권장: per-key 파일** — `<state_dir>/<key>.json` (키 하나당 파일 하나).

```
<state_dir>/                         (예: dlc-meta/.aidlc-state/  — 런타임·ephemeral)
├── <keyA>.json     { "key": "...", "status": "in-progress", "cycle_id": "...",
│                      "dispatched_at": "...", "verified": false, "updated_at": "..." }
├── <keyB>.json     { ... "status": "additional-work" ... }
└── ...
```

- **동시성 안전(락 프리)**: 서로 다른 워커는 서로 다른 파일을 쓴다 → 쓰기 경합이 구조적으로 없다. 한 파일은 한 키(대개 한 워커)만 건드리므로 파일 락·플록이 불필요. 쓰기는 *temp+atomic rename*(같은 키의 self-갱신 원자성)만으로 충분.
- **자연스러운 O(1)**: 조회·갱신·삭제가 곧 `os.path.join(state_dir, key + ".json")` 파일 하나에 대한 연산.
- **대조 — 단일 JSON + 락**: `index.json` 하나에 전 키를 담으면 *모든* 워커가 같은 파일을 read-modify-write → **락 필요**(파일 락은 OS별로 갈리고 stdlib 이식성이 나쁨; 락 없이는 lost-update). per-key 파일은 이 문제를 애초에 없앤다. 조회도 전체 파싱 대신 파일 하나만 읽으면 됨.

**추적 결정: `state_dir`은 gitignore(개인·ephemeral 런타임 영역).** 근거:
- 인덱스는 *in-flight 상태*(누가 지금 무엇을 하는 중인가)일 뿐, 사이클의 *역사*가 아니다. 역사는 `audit.md`(append-only, 팀 추적)가 단일 원천이다(§13.4).
- 세션·워커 로컬 런타임 상태를 커밋하면 팀원 머신 간 무의미한 충돌·노이즈가 발생한다(선례: 훅 설정·엔진 사본·`.unavailable` 마커도 개인·gitignore — §11.2.2).
- 따라서 `dlc-meta/.gitignore`에 `.aidlc-state/`를 추가한다(SETTER (0) 추적 제외 선결에 편입 — §13.6). **인덱스 유실은 오류가 아니라 no-op**(§13.4 degraded).

> **핵심 분리: ephemeral in-flight 인덱스 ↔ append-only 역사.** 인덱스(`.aidlc-state/`, 개인·재생성 가능)는 강제용 상태머신, `audit.md`(추적·불변)는 진실. done 전이 시 인덱스 레코드는 *삭제*되고 진실은 `audit.md`의 CYCLE-END로 남는다. 이 분리가 §13.4 라이프사이클과 §2.1 index.md("audit에서 파생된 재생성 가능 롤업")의 사상과 정합한다.

### 13.4 라이프사이클 — 오케스트레이터가 유지, 엔진이 강제

오케스트레이터 규율(책임 7)이 상태를 전이시키고, 엔진(§13.5 체크)이 그 규율을 강제한다. 상태값: `in-progress` · `additional-work` · (종결 시 레코드 삭제).

```
  (레코드 없음)
      │  디스패치 (오케스트레이터가 서브에 위임)
      ▼
  record(status = in-progress)          ← <state_dir>/<key>.json 생성
      │
      │  서브가 "완료" 클레임
      ▼
  오케스트레이터 지상검증 (POLICY-VERIFY — 클레임≠증거)
      ├── 아직 아님 →  update(status = in-progress | additional-work)   (레코드 유지)
      │
      └── 진짜 완료로 판정 →  ┌ status = done
                              ├ 인덱스 레코드 삭제 (<key>.json rm)
                              ├ audit.md에 CYCLE-END append
                              └ push
                              ─ 위 4개를 하나의 (준)원자적 트리거로 함께
```

- **한 트리거로 묶는 이유**: done 판정·인덱스 삭제·CYCLE-END·push가 갈라지면 "인덱스는 지웠는데 로그가 없다"거나 그 반대의 반쪽 상태가 생긴다. 순서 권장: **CYCLE-END append → (push) → 인덱스 레코드 삭제** (역사부터 확정한 뒤 ephemeral 상태를 거둔다 — 크래시 시에도 진실이 남고, 남은 인덱스는 다음 턴에 백스톱으로 가시화된다).
- **ephemeral ↔ append-only 분리(재확인)**: in-flight 인덱스는 삭제로 수명을 마치고, 역사는 audit.md에 영속. 인덱스는 언제든 audit.md들로 부분 재구성 가능(원천 아님).

### 13.5 강제 지점 — per-key 스코프 신규 선언 체크 3종

각 체크는 **오직 이 키의 상태 파일만** 읽는다(전역 `_open_cycles`가 아니라 `<state_dir>/<key>.json`). → 워커 B는 워커 A의 상태에 영향받지 않음 → **block-tier 안전**.

| # | 체크(제안 id) | 이벤트 | 위반 조건 | 취지 | block 안전성 |
|---|---|---|---|---|---|
| **(a)** `keyed-record-on-dispatch` | PostToolUse(디스패치 도구 매치) | 이 키의 레코드가 없음(디스패치했는데 미기록) | 위임했으면 상태를 기록하라 | 이 키만 봄 — 타 워커 무관 |
| **(b)** `keyed-valid-status-transition` | PostToolUse / Stop | 이 키가 `done`으로 점프했는데 레코드가 없거나 `verified != true`(검증 없이 done) | 검증 없이 완료로 건너뛰지 마라 | 이 키만 봄 |
| **(c)** `keyed-log-on-done` | Stop(턴 경계) | 이 키가 done인데 대응 CYCLE-END(+push) 흔적이 없음 / 또는 이 키가 아직 `in-progress`인 채 턴 경계를 넘김 | done 전이는 로그+push를 낳아야 한다 / 열린 채 새지 않게 | 이 키만 봄 — A의 열림이 B의 Stop을 안 건다 |

- **왜 block이 안전해지나**: 현행 Stop 백스톱(§13.1)이 *전역*이라 A→B 교차오염을 일으켰다. per-key로 좁히면 각 Stop은 자기 키만 평가 → 워커 B의 Stop은 B의 레코드로만 판정 → A의 미종결이 B를 못 막는다. PostToolUse의 "느슨함"도 사라진다(전역 아무 열림이 아니라 *이 키*의 레코드 유무).
- **degraded/loop-safe(불변식 유지)**: 키 부재·`state_dir` 부재·레코드 malformed → **no-op(차단 아님)**. `requires`에 신규 선결 `keyed-state-dir`(= `state_dir` 존재)를 두어 미구성 배포에서 조용히 SKIP. Stop-block 무한루프는 기존 `stop_hook_active` 강등 가드(§11.4 (c))를 그대로 재사용. PostToolUse는 사후라 block 금지(§11.4 (b)) → (a)는 warn 또는, 실행 전 진짜 차단이 필요하면 **PreToolUse**로 바인딩.

### 13.6 엔진 확장 — 함의된 코드 변경 (여기서 구현하지 않음)

채택 시 `enforce.template.py`·`invariants.template.yaml`에 필요한 변경. **본 PR은 이 코드를 바꾸지 않는다** — 무엇을 바꿔야 하는지만 명세한다.

1. **키 획득** — `main()`이 stdin JSON에서 `session_id`를 추가로 뽑고, CLI `--work-key` / env `AIDLC_WORK_KEY`를 우선순위(`CLI > env > session_id`)로 해석하는 `_resolve_work_key()`를 둔다. 없으면 `None`(→ 키 요구 체크는 no-op). 키 안전화(§13.2) 포함.
2. **state_dir 해석** — `--state-dir`(기본 `<base-dir>/.aidlc-state`) 추가. `_resolve_*` 3종과 같은 패턴.
3. **체크 시그니처 확장** — 현행 체크는 `fn(log_dir)`. 신규 per-key 체크는 키·state_dir가 필요하므로, `evaluate()`가 체크에 **컨텍스트 객체**(`log_dir`, `state_dir`, `work_key`)를 넘기도록 호출부를 일반화한다(기존 두 체크는 시그니처 호환 위해 어댑터로 감싸거나 `**ctx` 수용). `CHECKS` 레지스트리에 (a)(b)(c) 3종 등록.
4. **인덱스 IO** — `_read_state(state_dir, key)` / (엔진은 *읽기 전용*; 쓰기는 오케스트레이터 몫 — §13.7 미결). 파일 부재·malformed = `None`(degraded).
5. **선결 조건** — `_precondition_met`에 `keyed-state-dir` 추가(= `os.path.isdir(state_dir)`), 미지원 조건은 여전히 불충족 처리(중립).
6. **YAML 스키마** — 신규는 기존 스키마에 그대로 맞는다: `check`에 (a)(b)(c) id, `requires: [local-log-layer, keyed-state-dir]`, `bindings`에 이벤트. 스키마 변경 **불필요**(체크 id·선결 조건만 추가) → `INVARIANTS-CONTRACT`는 *체크 id 집합*이 바뀌므로 v1→v2로 올린다.
7. **템플릿 SLOT** — per-key 불변식은 범용(중립)이므로 파일럿처럼 `invariants.template.yaml` 본문에 둘 수 있으나(트래커 무참조), 실제 디스패치 도구명 `match`는 여전히 SETTER가 환경 적응(⑥). 트래커-결합분만 `<SLOT>`.
8. **중립·stdlib·degraded 유지** — 신규 코드도 로컬 파일(state_dir·audit.md)만 읽고 네트워크·트래커 무참조. stdlib-only(json·os). 무엇이 어긋나도 exit 0.

### 13.7 마이그레이션 경로 (공존·단계적 escalation)

현행 `cycle-must-log`(전역 warn)를 깨지 않고 얹는다. 병합 규율(§4.1)·degraded(§8) 그대로.

| 단계 | 내용 | tier | 게이트 |
|---|---|---|---|
| **Phase 1** | 현행 `cycle-must-log`(전역) 유지 | warn | (현행) — 전역 warn은 무해하므로 유지. block으로 올리지 않는다. |
| **Phase 2** | 키드 인덱스 + (a)(b)(c) 체크 **추가**, 오케스트레이터 라이프사이클(§13.4) 도입 | **warn** | 키 스코핑·인덱스 IO·라이프사이클을 실배포에서 관찰. 전역 `cycle-must-log`와 *공존*(둘 다 warn). 거짓양성/음성·키 획득(§13.2) 실측. |
| **Phase 3** | 키드 체크를 **block**으로 승격(Stop=(c)/(b), PreToolUse=(a)) | **block** | §11.4 (d) 라이브 파이어로 *키 스코핑이 실제로 A↔B 격리를 하는지* 실측 확인 후에만. 이때 전역 `cycle-must-log`는 warn으로 강등 유지하거나 은퇴(키드가 대체). |

- **escalation은 키드 스코핑이 들어간 *뒤에만*** block으로 간다 — 전역 상태에 block을 켜는 실수를 구조적으로 막는다.
- **SETTER 위빙(S8.8 SLOT)** — 트래커 결합 부분(예: 키를 티켓에 매핑, 티켓 전이 강제)은 §11.2·§12의 `<SLOT: project-adaptive invariants>` 경로로 SETTER가 인터뷰(②) 결과에 따라 짜 넣는다. 범용 per-key 불변식(a·b·c) 자체는 트래커 무참조이므로 템플릿 본문 후보이나, `match` 도구명(⑥)·`--state-dir` 경로 바인딩·라이프사이클을 쓰는 오케스트레이터 주체는 SETTER/오케스트레이터 시점 인스턴스에 귀속.

### 13.8 미결 — 사용자 결정 필요

1. **키 선택** — `session_id` 1차 + 오케스트레이터 위임 id 오버라이드(권장)로 확정할지, 아니면 위임 id를 1차로 둘지. 한 세션이 여러 위임을 직렬로 돌리는 워크플로우가 흔하면 위임 id가 1차여야 할 수 있다.
2. **쓰기 측 키 획득** — 엔진은 훅 JSON `session_id`를 공짜로 읽지만, *오케스트레이터*가 index 레코드를 **같은 키로** 남기려면 자기 `session_id`(또는 발급한 위임 id)를 알아야 한다. 후보: (ⓐ) SessionStart 훅이 세션 id를 파일에 스탬프 → 오케스트레이터가 읽음, (ⓑ) 오케스트레이터가 위임 id를 생성해 env/arg로 심고 동시에 index에 씀, (ⓒ) 엔진에 *쓰기* 보조 서브커맨드 추가. 어느 쪽인가?
3. **`state_dir` 추적** — 본 제안은 gitignore(ephemeral·개인) 권장. 팀이 in-flight 가시성을 *공유*하길 원하면(예: 대시보드) 추적 or 별도 채널이 필요 — 그러면 충돌·노이즈를 감수. gitignore로 확정할지?
4. **오케스트레이터가 쓰고 엔진이 읽는 경계** — 엔진을 *읽기 전용*으로 두고 쓰기는 전적으로 오케스트레이터 규율에 맡길지(권장·관심사 분리), 아니면 엔진에 원자적 쓰기 헬퍼를 넣어 오케스트레이터가 그걸 호출하게 할지.
5. **stale 키 GC** — 크래시·중단으로 삭제 안 된 `<key>.json`이 쌓일 수 있다. 회수 정책: (ⓐ) TTL(`updated_at` 초과 시 Stop 백스톱이 가시화/자동 정리), (ⓑ) CYCLE-CLOSER가 종료 시 청소, (ⓒ) 세션 시작 시 자기 키 재확인. 어떤 GC?

### 13.9 양방향 참조 (본 절 추가분)

| 문서 | 관계 |
|---|---|
| `specs/EVOLUTION.md` DP-9 §3.E·§4.3 | 본 제안의 거버넌스 경로 — 공유 룰북 귀속분은 자동 아님, 원칙 8 PR/머지(사람 큐레이션) |
| `specs/CYCLE-LOG.md` §2.1·§5·§10.3 | append-only 역사(audit.md)와 ephemeral 인덱스의 분리 원천 — CYCLE-END/REOPEN 의미론 |
| `templates/enforce.template.py` | §13.6 함의된 코드 변경 대상(미구현) — 키 획득·per-key 체크·state_dir IO |
| `templates/invariants.template.yaml` | 신규 체크 id·`requires`(§13.6-6) 반영 대상(미구현) — 스키마 무변경, 계약 v2 |
| `agents/SETTER.md` S8.8 | Phase 2/3 배선·SLOT 위빙(§13.7) — 트래커 결합분 |
| `specs/VERIFICATION.md` | Phase 3 block 승격 전 라이브 파이어(POLICY-VERIFY) |

---

## 변경 이력

본 명세 v1.0 — 불변식 강제 규율(POLICY-INVARIANT) 신설. STEP 1(템플릿·명세만): `invariants.template.yaml`(선언 단일 원천 + `cycle-must-log` 파일럿 + `<SLOT>`), `enforce.template.py`(중립·degraded-safe 범용 엔진, stdlib-only YAML 폴백), 본 명세 3종 추가.

근거: MD 절차는 모델의 자발적 준수에 의존해 압축·긴 사이클에서 반복 유실된다(리포 루트 `CLAUDE.md` §0 실측 실패 모드). SELF-CHECK 훅의 "기계적 주입" 해법을 *절차 강제*로 일반화했다.

STEP 2(SETTER 조립·훅 배선·라이브 계약 검증·트래커 결합 슬롯 채움)의 *실행*(SETTER.md 재배선·settings.json·CLAUDE.md 수정)은 본 변경에 포함되지 않는다 (§9).

STEP-2 보강(설계 프로즈 — SETTER.md 무수정): §11(인터뷰 6문항 + 합성 행동가이드 + OS 적응 훅 규칙 + 추적 분리)·§12(SETTER **S8.8** 초안, S8.7 미러) 추가. `enforce.template.py`는 stdout·stdin UTF-8 강제 + 선행 BOM 관용으로 보강돼 cp949 콘솔에서도 자기 출력으로 크래시하지 않음이 실증됨(warn 형태·degraded 경로 확인). 훅은 python 직접 호출로 OS 중립(PowerShell 전용 금지).

STEP-2b(드라이런 결함 수정 + 안정성/failover 하드닝): 신규 사용자 여정 드라이런이 S8.8에서 낸 결함 4종을 수정하고, 합성이 *재현가능·멱등·자가검증·fail-safe* 하도록 보강했다. **D1**(검증 거짓통과 — degraded-safe 엔진의 망가진 렌더→빈 출력이 정상 무발견과 구분 불가): S9 항목 17·S8.8 (5)의 1차 단언을 **POSITIVE 픽스처**(PostToolUse + 빈 cycles + ⑥ 매치 → warn 방출)로 바꿔 렌더+매치+env 로드를 반증가능하게 만듦(빈 출력=FAIL). Stop-빈·열린-cycle은 2차. **D2**(렌더 알고리즘 부재 → 런마다 발산): S8.8 (1)에 결정적 렌더 레시피 고정(고정 provenance 헤더·`INVARIANTS-CONTRACT`는 템플릿에서 복사·끈 블록 전삭제·`tier`/`match`만 치환·"SLOT을 비운다"=마커 포함 전삭제·말미 LF 하나 → 같은 답=바이트 동일). **D3**(공유 `.gitignore` 커밋 미배정): 추가 줄은 추적 변경이므로 개인 산출물과 구분해 커밋(원칙 8) — 프레임워크 배포 `.gitignore`에 미리 실어 happy path는 no-op. **D4**: `.claude/__pycache__/` 제외 추가. **Failover**: (1) 합성 후 자가검증 **게이트** — P 통과 전 성공 보고 금지, 실패 시 라이브 훅 `.bak` 롤백 + degraded; (2) 멱등 — 훅 교체(append 금지)·개인 yaml seed-if-absent·엔진 사본 덮어쓰기 안전; (3) 훅-병합 안전 — 깨진 settings.local.json은 `.corrupt` 보존·보고·degraded, `UserPromptSubmit`/`permissions` 항상 보존; (4) degrade 경로 열거(훅-불가/no-python/dlc-meta 쓰기불가/템플릿 누락/게이트 실패 → 각기 이름 있는 결과·마커·보고). 엔진(`enforce.template.py`)은 무수정 — 컴포넌트 체크(block=exit2·Stop-guard 강등·degraded no-op·POSITIVE warn·판별 negative) 재실행 전부 green.

STEP-2a(실제 배선): (1) **훅 계약 확정** — 공식 문서(`code.claude.com/docs/en/hooks.md`, v2.1.2xx, 2026-09-11 fetch) 대조로 §11.4를 확정. warn 형태 정합, **block은 exit code 2가 신뢰 가능한 차단 채널**(exit 0 + decision:block은 자문에 그칠 수 있음, 특히 PostToolUse 사후 실행), block은 Stop·PreToolUse에서 실효(PostToolUse는 warn 유지), **Stop-block 무한루프는 `stop_hook_active`로 가드**. (2) **엔진 반영** — `enforce.template.py` `emit()`/`main()`이 block tier → JSON + exit 2, Stop 재진입 시 block→warn 강등을 구현(서브프로세스 단위 검증: block→exit2+JSON / warn→exit0+JSON / 무발견·degraded→exit0+빈출력 / Stop+stop_hook_active→강등, 전부 통과). (3) **S8.8 이식** — §12 초안을 `agents/SETTER.md`에 라이브 절 S8.8로 이식(S8.7 (0)~(6) 미러, team=신규만·엔진/훅/개인=신규·합류·보수, 두 yaml co-locate §11.2.1, python 직접 호출 훅, S9 항목 17·파일트리·참조표 갱신). 잔여: block tier 라이브 파이어(새 세션/오케스트레이터).

STEP-2c(라이브파이어 결함 수정 — env 필드 죽은 훅 + 게이트 사각 + PreToolUse): 잔여 라이브파이어가 드러낸 **PR-blocking 결함**을 수정했다. **F1**(env 필드 = silently dead): S8.8 (4)가 훅 command 객체의 `env` 필드로 `AIDLC_INVARIANTS_DIR`/`AIDLC_LOG_DIR`을 실었으나, **Claude Code 훅엔 `env` 필드가 없다**(공식 문서 인식 필드: type·command·args·if·timeout·statusMessage·shell·async·asyncRewake — env 없음, 훅은 부모 env 상속). env가 무시돼 `AIDLC_INVARIANTS_DIR`이 cwd 기본값→불변식 dir 못 찾음→exit 0 무강제로 **설치돼도 죽어 있었다.** 엔진에 CLI 인자 `--base-dir`(및 `--invariants-dir`/`--log-dir`) 추가(우선순위 CLI>env>기본; env는 하위호환 폴백), S8.8 (3)(4)·§11.1.1·§11.2·§12가 **`--base-dir` 자기완결·셸 독립** 명령으로 렌더하도록 개정(env 필드 삭제, 인라인 `VAR=x` 금지 — cmd.exe/powershell 비호환). **F2**(게이트 구조적 사각): (5) 게이트가 *자기가 env를 걸어* 서브프로세스를 돌려 죽은 라이브 훅을 놓쳤다(D5). 게이트를 **settings에 기록된 렌더 command 문자열 verbatim + `--log-dir`로 로그만 override**(env 미사용)로 바꿔, 호출 형태가 깨지면(env 재도입·경로 오류) FAIL하게 함. **F3**(block-tier 이벤트별 의미론): §11.4 (b)에 PreToolUse=실행 전 진짜 차단(deny) / Stop=턴 차단(exit 2) / PostToolUse=사후 자문뿐 표를 명시, S8.8·템플릿에 포인터. **F4**(PreToolUse 지원 — 구현): 엔진에 PreToolUse 이벤트 브랜치 추가(block→`permissionDecision:deny`+exit 0, warn→systemMessage+additionalContext, PostToolUse와 동일 `match`, 재진입 루프 없어 가드 불필요) — 실행 전 진짜 차단(강제성의 실체)을 제공. 템플릿에 PreToolUse 바인딩 옵션·게이트에 조건부 deny 픽스처 추가. 엔진 15개 서브프로세스 체크(F1 CLI·env폴백·block exit2·Stop guard 강등·cp949·match/no-match·degraded no-op·S1/S2 판별·PreToolUse deny/warn/no-fire) 전부 green.

STEP-3 제안(§13 — 키드 상태머신 강제화, **검토용·미구현**): 현행 파일럿의 전역 boolean(모든 `cycles/*/audit.md`에 대한 "*어떤* 사이클이든 열림?", 작업 아이템/세션 키 없음)이 **동시성(공유 `dlc-meta`·다중 워커) 하에서 block-안전하지 않음**을 코드 대조로 확정하고(§13.1: `_open_cycles`/`check_*`가 전역, `main()`은 `session_id` 미추출, 체크 시그니처 `fn(log_dir)`에 세션 인자 없음 — Stop 교차오염 + PostToolUse 과소·Stop 과다), **키드 per-work-item 상태머신**을 제안. 키=`session_id`(훅 JSON 가시·중립) 1차 + 오케스트레이터 위임 id 오버라이드(티켓 키는 도메인 결합이라 기각), 인덱스=per-key 파일 `<state_dir>/<key>.json`(락 프리 동시성·O(1); 단일 JSON+락 대조), `state_dir`=gitignore ephemeral(역사는 audit.md append-only로 분리), 라이프사이클(dispatch→record→지상검증→done+레코드삭제+CYCLE-END+push 준원자), per-key 체크 3종(record-on-dispatch·valid-status-transition·log-on-done — 각기 *이 키만* 읽어 워커 격리 → block 안전), 마이그레이션(Phase1 현행 warn 유지 → Phase2 키드 warn 공존 → Phase3 키 스코핑 실측 후 block 승격), SETTER S8.8 SLOT 위빙. **엔진·템플릿 무수정** — §13.6이 함의된 코드 변경(키 획득·체크 컨텍스트화·state_dir IO·계약 v2)만 명세. 거버넌스=DP-9(EVOLUTION §3.E·§4.3 공유 귀속분 → 원칙 8 PR/머지 사람 큐레이션). 미결 5종은 §13.8(키 선택·쓰기측 키 획득·state_dir 추적·읽기/쓰기 경계·stale 키 GC).

향후 변경은 깃 PR/머지 (원칙 8).

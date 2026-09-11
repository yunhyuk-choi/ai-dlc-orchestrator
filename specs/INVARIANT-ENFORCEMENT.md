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
| **block** | 차단(blocking JSON — `{"decision":"block","reason":…}`) | 비가역·중대 절차에만 |
| **warn** | 비차단 경고(`systemMessage` / `hookSpecificOutput.additionalContext`) | **기본 권장값** |
| **advisory** | no-op — 훅 출력 없음(가시화·기록만) | 저위험 넛지 · degraded 폴백 등가값 |

- 훅 JSON 형태의 단일 원천은 `enforce.template.py` §7 `emit()`이며, **Claude Code hook contract**에 맞춘다. STEP 2에서 라이브 하네스로 검증한다.
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
| `agents/SETTER.md` (STEP 2) | 본 템플릿을 인스턴스로 조립·훅 배선 (§9 — 아직 미구현) |
| `agents/orchestrator/ERROR-POLICY.md` | EX-15 / C FALLBACK — degraded 처리 정합 |
| `CLAUDE.md` §0.5 | degraded 철학(훅은 보강이지 전제가 아니다)의 상위 원천 |
| `specs/VERIFICATION.md` | STEP 2 훅 계약 검증이 따르는 지상검증 규율(POLICY-VERIFY) |

---

## 변경 이력

본 명세 v1.0 — 불변식 강제 규율(POLICY-INVARIANT) 신설. STEP 1(템플릿·명세만): `invariants.template.yaml`(선언 단일 원천 + `cycle-must-log` 파일럿 + `<SLOT>`), `enforce.template.py`(중립·degraded-safe 범용 엔진, stdlib-only YAML 폴백), 본 명세 3종 추가.

근거: MD 절차는 모델의 자발적 준수에 의존해 압축·긴 사이클에서 반복 유실된다(리포 루트 `CLAUDE.md` §0 실측 실패 모드). SELF-CHECK 훅의 "기계적 주입" 해법을 *절차 강제*로 일반화했다.

STEP 2(SETTER 조립·훅 배선·라이브 계약 검증·트래커 결합 슬롯 채움)는 본 변경에 포함되지 않는다 (§9).

향후 변경은 깃 PR/머지 (원칙 8).

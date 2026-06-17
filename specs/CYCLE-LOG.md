# CYCLE-LOG.md — 사이클 로그 형식 명세

> **이 문서는 형식 명세 문서.** 에이전트 룰북 아님.
> 본 명세는 `dlc-meta/cycles/` 의 사이클 로그 형식 표준 (audit.md 등).
> 로깅 *실행*은 ORCHESTRATOR-AGENT 책임 7. 본 문서는 *형식 룰만* 정의.
> 변경은 깃 PR/머지 (원칙 8) — 다른 산출물(DECISIONS.md / ERROR-POLICY.md / HANDOFF-WRITER.md)이 이 형식에 의존하므로 변경 시 영향 검토 필수.

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 형식 명세 문서 (에이전트 X) |
| 실행 주체 | 오케스트레이터 (책임 7) — 본 형식에 따라 audit.md에 직접 append |
| 흡수 관계 | DECISIONS.md §3 분기점 기록 + ERROR-POLICY.md §3 예외 기록 형식이 *본 명세에 통합* — 단일 원천 (원칙 6) |
| 참조 주체 | DECISIONS.md / ERROR-POLICY.md / HANDOFF-WRITER.md (모두 본 형식 따름) |
| 위치 | `ix-ai-dlc/specs/CYCLE-LOG.md` |

**왜 에이전트가 아닌가**:
- 사이클 로깅은 *모든 단계에서 발생* — 분기점·예외·작업 진행·AWS 트리거 등 빈번
- 별도 에이전트로 분리하면 *호출 빈도 과다* → 원칙 1 비효율
- 따라서 오케스트레이터 *직접 기록*, 본 명세는 *룰만* 제공

---

## 2. `cycles/` 디렉토리 구조

```
dlc-meta/cycles/
├── {cycle-id}/                       ← 사이클 단위 디렉토리
│   ├── audit.md                      ← 메인 결정·예외·진행 기록 (필수)
│   ├── handoff-v{n}.md               ← HANDOFF-WRITER 산출 (있을 시, 0~여러 개)
│   └── (확장 게이트 — CYCLE-CLOSER 필요 시 추가 파일)
├── {cycle-id-2}/
│   └── ...
└── index.md                          ← 사이클 간 행동 누적 (DP-9 진화 입력) — §2.1
```

**원칙**:
- 사이클 1개 = 디렉토리 1개
- `audit.md`는 *필수* — 모든 사이클에 반드시 존재
- 추가 파일은 *해당 사이클이 산출한 결과물* (핸드오프 등)
- index.md는 *사이클 간 사용자 행동 누적* — DP-9 진화 감지 입력 (§2.1). audit.md에서 파생된 *재생성 가능 롤업*이며 원천 아님 (원칙 6: audit.md가 단일 원천)

### 2.1 `index.md` — 사이클 간 행동 누적 (DP-9 입력)

**목적**: 사용자 행동을 사이클 간 누적·트래킹해 **DP-9(진화 능동 제안)** 감지 입력으로 제공. *사이클 검색 목록*은 부차적 부산물일 뿐, 본 파일의 존재 이유는 행동 기반 진화임.

**성격 (중요)**:
- audit.md(append-only 원천)에서 *파생된 롤업* — **재생성 가능**. index.md 자체는 단일 원천이 아님 (audit.md가 원천, index.md는 그 뷰/캐시).
- 따라서 본 파일은 append-only 아님 — 윈도우 롤링 등으로 *유지(maintain)*. 손상·유실 시 audit.md들로 재생성 가능.

**갱신 주체·시점**: 오케스트레이터(책임 7)가 **STEP 10(사이클 종료)**에 이번 사이클 행동을 롤업에 반영. DP-9 감지가 그 직후 본 파일을 읽음.

**구조**:
```
# cycles/index.md — 사이클 간 행동 누적

## A. 사이클 인덱스 (부차)
| cycle-id | intent | 종료시각 | 한 줄 요약 |

## B. 행동 롤업 (주 — DP-9 입력)

### B-② 컨펌 응답 패턴 (DP별, 최근 K=5 사이클 윈도우)
| DP | 응답 시퀀스 (최신→과거, 최대 K) | 마지막 갱신 사이클 |
| DP-2 | 승인, 승인, 승인, 거부, 승인 | {cycle-id} |

### B-① 레포 공동 영향 (DP-2 영향 매핑 — 레포 쌍별, 최근 K=5 사이클)
| 레포 쌍 (정렬) | 공동 출현 M | 윈도우 내 DP-2 사이클 N | 마지막 사이클 |
| api–frontend | 4 | 5 | {cycle-id} |

원천 = 각 사이클 audit.md DP-2 기록 `Output`(영향 레포 리스트)의 쌍 조합. M·N 산출·판정·REPO-MAP 대조는 `specs/EVOLUTION.md` §3.B 위임.

### B-③ 예외 반복 ((EX-N, 레포)별, 최근 K=5 사이클)
| EX-N · 레포 | 발생 M | 윈도우 내 레포 관여 N | 마지막 사이클 |
| EX-3 · api | 3 | 3 | {cycle-id} |

원천 = 각 사이클 audit.md 예외 기록(§7)의 `EX-N` + `Repo` 필드. repo-scoped 예외만. M·N 판정은 `specs/EVOLUTION.md` §3.C.

### B-④ 호출 경로 (인텐트 시그니처별 호출/STEP 시퀀스, 최근 K=5 사이클)
| 인텐트 시그니처 | 정규 호출 시퀀스 | 동일 시퀀스 M | 시그니처 사이클 N | 마지막 사이클 |
| 변경·수정 / {영향 프로파일} | DP-1→DP-2→STEP4(repo)→STEP6→STEP9 | 3 | 4 | {cycle-id} |

원천 = audit.md *라우팅 트레이스* — DP-1(인텐트) + 서브 호출·STEP 전이 PROGRESS(§8). **전제**: ④가 작동하려면 이 호출/전이 PROGRESS가 기록돼야 함 (§8 PROGRESS는 본래 *선택* — ④ 활성 시스템에서는 라우팅 트레이스 기록 *권장/전제*). 판정·시그니처 정의·적용은 `specs/EVOLUTION.md` §3.D.
```

**B-② 필드 (신호 ② 파일럿)**:
- `DP`: 컨펌이 발생한 분기점 ID (DP-1~10)
- `응답 시퀀스`: 해당 DP에서 최근 K=5 사이클의 사용자 컨펌 응답 (최신순). K 초과분 drop (롤링 윈도우). 원천 = 각 사이클 audit.md 분기점 기록의 `Confirm` 필드 (§6)
- DP가 매 사이클 발생하진 않으므로 시퀀스 길이 ≤ K

**DP-9 소비**: 임계(최빈 응답 횟수·일관성%) 산출·판정은 본 명세가 아니라 **`specs/EVOLUTION.md`(DP-9 휴리스틱)** 위임. 본 §2.1은 *데이터 형식*만 정의.

---

## 3. 사이클 ID 형식

### 3.1 형식 규칙

```
{YYYY-MM-DD}-{HH-MM-SS}-{short-slug}
```

예시:
- `2026-05-27-14-30-15-add-auth-feature`
- `2026-05-28-09-00-00-refactor-payment`
- `2026-06-01-11-45-30-cross-repo-analysis`

**구성 요소**:
| 부분 | 형식 | 의미 |
|---|---|---|
| `{YYYY-MM-DD}` | ISO 날짜 | 사이클 시작 일자 |
| `{HH-MM-SS}` | 24시간 시각 | 사이클 시작 시각 (UTC 또는 시스템 디폴트) |
| `{short-slug}` | kebab-case 3~5 단어 | 인텐트 요약 (영문, 소문자) |

### 3.2 short-slug 규칙

- 영문 소문자 + 숫자 + 하이픈
- 공백·특수문자 X
- 3~5 단어, 인텐트 핵심 동사·명사 포함
- 모호 시 첫 분기점(DP-1) 분류 결과 기반 자동 생성
- 사용자 명시 가능 (예: "이번 사이클 ID 슬러그는 'refactor-cart'로")

### 3.3 충돌 방지

- 동일 시각(초 단위)에 두 사이클 동시 시작 시 → 두 번째 사이클에 `-2` 접미사 (예: `...-add-auth-feature-2`)
- 거의 발생 안 함

---

## 4. audit.md 구조

### 4.1 전체 구조

```markdown
# {cycle-id}

## 사이클 메타
- 시작: YYYY-MM-DD HH:MM:SS
- 종료: (진행 중) 또는 YYYY-MM-DD HH:MM:SS
- 종료 사유: 정상 / 예외(EX-N) / (진행 중)
- 인텐트 원문: "{사용자 발화}"
- 영향 레포: [slug1, slug2, ...]
- 산출물: [path1, path2, ...]  ← 사이클 종료 시 누적

## 결정·예외·진행 기록 (append-only)

[YYYY-MM-DD HH:MM:SS] DP-1: ...
[YYYY-MM-DD HH:MM:SS] DP-2: ...
[YYYY-MM-DD HH:MM:SS] EX-4: ...
[YYYY-MM-DD HH:MM:SS] PROGRESS: ...
[YYYY-MM-DD HH:MM:SS] AWS-IMPORT: ...

## AWS audit 스냅샷 (사이클 종료 시 — CYCLE-CLOSER 책임)
(아래 §8 참조)
```

### 4.2 메타 섹션 갱신 규칙

- *사이클 시작 시*: 시작 시각·인텐트 원문 기록. 종료는 "(진행 중)"
- *진행 중*: 영향 레포·산출물 누적 갱신 (메타 섹션은 *예외적으로* 수정 허용 — 본문 entry는 append-only)
- *사이클 종료 시*: 종료 시각·사유 확정. CYCLE-CLOSER가 산출물 최종 정리

---

## 5. 사이클 메타 entry

사이클 시작·종료 시 본문에도 표시 entry 추가 (메타 섹션과 별도):

```
[YYYY-MM-DD HH:MM:SS] CYCLE-START
  Intent: "{사용자 발화 원문}"
  Initial classification: {DP-1 결과}

[YYYY-MM-DD HH:MM:SS] CYCLE-END
  Reason: 정상 / 예외(EX-N)
  Total decisions: {DP-* 개수}
  Total exceptions: {EX-* 개수}
  Output paths: [path1, path2, ...]
```

### 5.1 append-live 원칙 — *작업하면서* 기록 (사후 재구성 금지)

audit.md는 **사후 보고서가 아니라 진행 중 실시간 기록(running record)**.

- **원칙**: 각 entry는 *그 사건이 발생하는 시점에* append. 분기점 결정 직후, 예외 감지 직후, STEP 전이 직후 — *그 자리에서* 기록.
- **금지**: 사이클을 다 끝낸 뒤 기억에 의존해 entry를 *몰아서 재구성*하는 것. 사후 재구성은 (a) 중간 분기·되돌림·폐기된 시도를 누락하고, (b) 타임스탬프가 부정확해지며, (c) 긴/분기하는 사이클일수록 *기록이 실제와 어긋남(staleness)*.
- **staleness 신호**: 작업이 메타 섹션(영향 레포·산출물)과 본문 entry보다 *앞서 나가 있으면* 로그가 stale한 상태. 다음 사건을 기록하기 전 *밀린 entry부터* append해 따라잡는다.
- **결과**: append-live면 DP-9 진화 입력(§2.1)·핸드오프(§11)·정정(§10)이 모두 *실제 일어난 순서대로* 신뢰 가능한 원천을 갖는다. 사후 재구성된 로그는 이 모든 파생물의 신뢰성을 깨뜨린다.

> 휴리스틱: "기록할까 말까" 망설여지는 분기·되돌림·범위 변경은 *기록하는 쪽*. 본문 entry는 가볍다(§8 PROGRESS는 1줄). 비용보다 staleness 위험이 크다.

---

## 6. 결정 기록 형식 (분기점)

DECISIONS.md §3.2 흡수. *단일 원천*은 본 명세.

```
[YYYY-MM-DD HH:MM:SS] DP-N: {분기점 이름}
  Input: {입력 요약}
  Decision: {결정 + 이유}
  Confirm: {사용자 컨펌 여부 + 응답 ([Answer]: 태그 원문)}
  Output: {출력 요약}
  Next: {다음 액션}
```

### 6.1 필드 가이드

| 필드 | 가이드 |
|---|---|
| `[타임스탬프]` | ISO 형식. 시·분·초 단위 |
| `DP-N` | DECISIONS.md §1 카탈로그 ID 일치 |
| `{분기점 이름}` | DECISIONS.md §1 표 *분기점* 컬럼 정확히 복사 |
| `Input` | 1~3줄 요약. 상세는 *분기점 자체*가 참조하는 원천 (REPO-MAP 등) 경로 표시 |
| `Decision` | 결정 본문 + 이유 (인과 명시) |
| `Confirm` | 컨펌 *불필요 시* "(자율 판단)" / *컨펌 시* "(사용자 응답: ...)" |
| `Output` | 1~3줄 요약 + 결과 산출 경로 (있을 시) |
| `Next` | 다음 액션 명시 (다음 DP·STEP·종료 등) |

---

## 7. 예외 기록 형식

ERROR-POLICY.md §3.1 흡수. *단일 원천*은 본 명세.

```
[YYYY-MM-DD HH:MM:SS] EX-N: {예외 이름}
  Detected: {감지 입력}
  Policy: {적용 정책 (A~E) + 이유}
  Result: {성공 / 실패 / escalate}
  Confirm: {사용자 컨펌 응답 (해당 시)}
  Next: {후속 액션}
  (Repo: {slug} — 레포 스코프 예외 시)
  (Related: DP-N — 해당 시)
```

### 7.1 필드 가이드

| 필드 | 가이드 |
|---|---|
| `EX-N` | ERROR-POLICY.md §2 카탈로그 ID 일치 |
| `Detected` | 감지된 신호·증거 (예: "AWS audit.md FAILED entry") |
| `Policy` | A RETRY / B ASK / C FALLBACK / D PAUSE / E ABORT 중 하나 + 이유 |
| `Result` | 성공 (정상 복구) / 실패 (재시도 실패) / escalate (다른 정책으로 escalate) |
| `Confirm` | 정책이 B ASK인 경우 사용자 응답 원문 |
| `Next` | 후속 액션 (분기점 재진입·사이클 종료·폴백 진입 등) |
| `Repo` | (선택) 레포 스코프 예외 시 해당 레포 slug — 신호 ③(예외 반복) 입력 (`index.md` B-③) |
| `Related: DP-N` | 분기점 중에 예외 발생 시 — 어느 분기점에서 발생했는지 |

---

## 8. 작업 진행 entry (선택)

분기점·예외 외의 일반 기록. 필수 아님 — *유용한 진행 지점*만 기록.

```
[YYYY-MM-DD HH:MM:SS] PROGRESS: {진행 메시지}
  Detail: {선택 — 상세 설명}
```

예시:
```
[2026-05-27 14:40:00] PROGRESS: STEP 1 시작
  Detail: 시스템 분해 + 영향 레포 매핑 진입

[2026-05-27 14:55:00] PROGRESS: STEP 1 완료, STEP 2 진입
  Detail: 영향 레포 3개 식별 — frontend, api, db-migrations

[2026-05-27 15:10:00] PROGRESS: AWS 트리거 — repo:frontend, phase:Inception
```

---

## 9. AWS audit 통합 형식

책임 7 — 각 영향 레포의 `{레포}/aidlc-docs/audit.md`를 우리 시스템 단위로 *흡수 집계*.

### 9.1 진행 중 (사이클 활성 상태)

진행 중에는 *경로 참조*만:
```
[YYYY-MM-DD HH:MM:SS] AWS-LINK: repo:{slug}
  Path: {레포 경로}/aidlc-docs/audit.md
  Status: AWS aidlc-state.md 상태값
```

진행 중에 *AWS audit 전체를 우리 audit으로 복사* 안 함 — 진실 분산 방지.

### 9.2 사이클 종료 시 — AWS audit 스냅샷 흡수 (CYCLE-CLOSER 책임)

사이클 종료 시 CYCLE-CLOSER가 *시점 동결 스냅샷*을 우리 audit.md 끝에 추가:

```
## AWS audit 스냅샷 ({사이클 종료 시각 기준})

### repo: {slug}
Path: {레포 경로}/aidlc-docs/audit.md
Hash: {SHA-256 또는 git commit hash}

{AWS audit.md 전체 인용 또는 핵심 결정만 요약}

### repo: {slug2}
...
```

근거:
- 진행 중: *진실 분산* 방지 (옵션 B — 경로 참조)
- 종료 시: *시점 동결* (옵션 C — 스냅샷). 이후 AWS audit이 변경돼도 우리 사이클 기록은 불변
- 옵션 C가 *재현성* 보장 — 사이클 종료 시점의 정확한 상태를 후속 EVOLUTION이 참조

### 9.3 스냅샷 형식 결정 (옵션)

- **옵션 A: 전체 인용** — 단일 원천 ↑, audit.md 크기 ↑ (대형 사이클에서 부담)
- **옵션 B: 핵심 결정만 요약** — 가볍지만 *진실 발췌* 책임 발생
- **옵션 C: hash + 별도 파일 보존** — 우리 cycles/에 AWS audit 사본을 별도 파일로 저장 + audit.md엔 hash만

기본: **옵션 A (전체 인용)** — 단일 원천 우선. 대형 사이클이 문제되면 옵션 C로 EVOLUTION (Stage 3+).

---

## 9.5 범위 확장·분기 사이클 (sprawl) — 인식과 처리

한 인텐트로 시작한 사이클이 진행 중 *원래 의도를 훨씬 넘어* 번지는 경우 (예: 설계 수정 → 아키텍처 전환 → 릴리스 → 크로스레포 정리로 한 사이클이 5배 부풀음). 이 §는 *언제 부풀었다고 인식*하고 *쪼갤지 한 사이클로 갈지* 정한다.

### 9.5.1 sprawl 인식 신호 (휴리스틱)

다음 중 *복수*가 동시에 참이면 "범위가 원래 의도를 벗어났다"고 본다:

- **인텐트 유형 전환**: DP-1 최초 분류와 현재 작업의 유형이 달라짐 (예: "버그 수정"으로 시작 → "아키텍처 재설계" 수행 중).
- **영향 레포 팽창**: 영향 레포 집합이 *최초 DP-2 산출 대비 2배 이상* 또는 새 도메인이 추가됨.
- **분기점 폭증**: 한 사이클 내 DP-* 결정 수가 그 인텐트 유형의 *통상치를 크게 상회* (생성 가능한 floor 휴리스틱: 통상 대비 ≈2배).
- **종료 신호 부재 누적**: STEP이 정상 종료 지점(STEP 10·보고)을 *지나쳤는데도* 새 작업이 계속 파생.

> 단일 신호(예: 영향 레포 1개 추가)는 *정상 범위 내 조정*. sprawl 판정은 *복수 신호 동시 충족* + 인과적으로 *원래 인텐트와 다른 목표*를 향함.

### 9.5.2 선택지 — 쪼개기 (a) vs 한 사이클 유지 (b)

sprawl 인식 시 둘 중 택1 (큰 영향이면 사용자 컨펌 — DECISIONS DP 흐름):

- **(a) 연결된 서브 사이클로 분할**: 현재 사이클을 정상 경계에서 닫고(또는 PAUSE), 확장분을 *새 사이클*로 연다. 두 사이클을 *상호 링크*해 추적성 유지. **권장 기준**: 확장분이 *독립된 인텐트로 설 수 있고*(별도 영향 레포·별도 종료 기준) DP-9 진화 입력(§2.1)에서 *별개 시그니처*로 잡히는 게 맞을 때.
- **(b) 한 사이클로 계속**: 쪼개면 인위적인 경계가 추적을 더 해칠 때. 단 *반드시* `SCOPE-EXPANSION` entry로 확장을 명시 기록 (아래 §9.5.3). 메타 섹션 인텐트 원문은 *최초값 유지*하되, 확장은 본문 entry가 진실.

> 휴리스틱 기본값: 확장분이 *최초 인텐트 없이도 독립 발의됐을 작업*이면 (a) 분할, *최초 작업의 직접 연장·불가분 후속*이면 (b) 유지. 모호하면 (b) + 충실한 SCOPE-EXPANSION 기록 (append-live가 사후 분할도 가능케 함).

### 9.5.3 `SCOPE-EXPANSION` entry 형식 (본문, append-only)

```
[YYYY-MM-DD HH:MM:SS] SCOPE-EXPANSION
  Original intent: {최초 DP-1 인텐트 요약}
  Expanded to: {지금 향하는 실제 범위}
  Trigger: {무엇이 확장을 유발했나 — 발견·결정·외부 요인}
  Signals: {§9.5.1 충족 신호 나열}
  Choice: (a) split → 새 사이클 {cycle-id} / (b) continue-as-one
  (Linked: {새·관련 사이클 id} — split 시)
```

- (a) split 시: 본 사이클에 `Choice: (a)`를 남기고, 새 사이클 audit.md 첫머리 CYCLE-START에 `(Linked-from: {원 사이클 id})`를 남겨 *양방향 링크*.
- (b) continue 시: 메타 섹션 *영향 레포·산출물*을 확장분 포함해 갱신(§4.2 허용), 본문은 본 entry가 확장 시점·근거의 단일 원천.

---

## 10. append-only 정책 및 정정

### 10.1 본문 entry는 append-only

- audit.md 본문 entry는 *수정 X*. 잘못된 기록 발견 시 *새 entry로 정정*.
- 메타 섹션은 *예외적으로 수정 허용* (진행 중 영향 레포·산출물 갱신)

### 10.2 정정 entry 형식

```
[YYYY-MM-DD HH:MM:SS] CORRECTION
  Target: [원래 entry 시각·ID]
  Correction: {정정 내용}
  Reason: {왜 정정 필요한지}
```

예시:
```
[2026-05-27 15:30:00] CORRECTION
  Target: [2026-05-27 14:35:00] DP-3
  Correction: "AWS 6 factors Risk Level 평가값을 medium → high로 정정"
  Reason: 운영 영향 추가 발견 — 결정 자체는 유지하되 평가 근거 명확화
```

원본 entry는 *그대로 남음*. 정정 entry가 *최종 진실*임을 hindsight로 표시.

### 10.3 닫힌 사이클 재오픈 (CYCLE-END 이후 정당한 연장)

CYCLE-END(§5)로 *이미 닫힌* 사이클이 이후 정당하게 *재개·연장*되는 경우 (예: 종료 보고까지 끝났는데 누락·후속 발견으로 같은 인텐트를 더 진행해야 함). append-only 역사를 *다시 쓰지 않고* 표현하는 것이 핵심.

**원칙**: CYCLE-END entry는 *지우거나 수정하지 않는다*. 대신 그것을 *superseded(대체됨)*로 표시하는 새 entry를 append. CORRECTION(§10.2) 메커니즘의 *1급 특화 용법* — "닫힘이라는 결정을 hindsight로 정정".

**`CYCLE-REOPEN` entry 형식 (본문, append-only)**:

```
[YYYY-MM-DD HH:MM:SS] CYCLE-REOPEN
  Supersedes: [원래 CYCLE-END entry 시각]
  Reason: {왜 재오픈 정당한가 — 누락·후속 발견·외부 변경}
  Reopened scope: {재개 후 진행할 범위}
  Note: 위 CYCLE-END는 더 이상 최종 아님 — 본 사이클은 다시 활성
```

처리:
- 메타 섹션 *종료/종료 사유*를 다시 "(진행 중 — 재오픈 {시각})"으로 갱신 (§4.2 메타 갱신 허용 범위 — 본문 CYCLE-END entry는 *불변*, 메타만 현재 상태 반영).
- 재오픈 후 추가 작업은 평소처럼 append. 최종적으로 다시 닫을 때 *새* CYCLE-END entry를 append (이전 것을 덮지 않음). 한 audit.md에 CYCLE-END가 둘 이상 나타날 수 있으며 *마지막 것이 유효*, 앞선 것은 CYCLE-REOPEN이 superseded로 표시.
- **재오픈 vs 새 사이클 판단**: 재개 작업이 *같은 인텐트의 직접 연장*이면 CYCLE-REOPEN. 사실상 *새 인텐트*면 새 사이클 + §9.5.3 링크(`Linked-from`). 기준은 §9.5.2 (a)/(b) 휴리스틱과 동일 — 독립 발의 가능 여부.
- **DP-9·핸드오프 정합**: 재오픈된 사이클은 *아직 진행 중*이므로 index.md 롤업(§2.1) 반영은 *최종 CYCLE-END 시점*에 한 번. 중간 CYCLE-END에서 이미 롤업했다면, 재오픈은 그 롤업을 *최종 종료 시 재반영(재생성 가능 롤업이므로 idempotent)*. index.md는 원천 아님(§2.1)이라 audit.md들로 재생성하면 정합 회복.

### 10.4 무결성 (선택, Stage 3+)

- 사이클 종료 시 CYCLE-CLOSER가 audit.md 전체 hash 계산 → 메타에 기록
- 변조 감지 가능

---

## 11. 양방향 참조 맵

| 문서 | 본 명세와의 관계 |
|---|---|
| `agents/orchestrator/ORCHESTRATOR-AGENT.md` 책임 7 | 본 형식에 따라 audit.md 직접 append |
| `agents/orchestrator/DECISIONS.md` §3 | 분기점 기록 형식 — *본 명세 §6 흡수*. DECISIONS.md는 *위임 표시*만 |
| `agents/orchestrator/ERROR-POLICY.md` §3 | 예외 기록 형식 — *본 명세 §7 흡수*. ERROR-POLICY.md는 *위임 표시*만 |
| `agents/HANDOFF-WRITER.md` W2~W3 | audit.md를 *원천*으로 변수 채움 |
| `agents/CYCLE-CLOSER.md` | 사이클 종료 시 AWS audit 스냅샷 흡수 책임 (본 명세 §9.2) |
| `{레포}/aidlc-docs/audit.md` | AWS 단위 audit — 우리 시스템 단위 audit으로 흡수 (§9) |

---

## 부록. audit.md 예시 (소형 가상 사이클)

```markdown
# 2026-05-27-14-30-15-add-auth-feature

## 사이클 메타
- 시작: 2026-05-27 14:30:15
- 종료: 2026-05-27 16:20:00
- 종료 사유: 정상
- 인텐트 원문: "회원 인증 기능 추가하자. JWT 기반으로."
- 영향 레포: [frontend, api]
- 산출물: [frontend/src/auth/, api/src/auth/, dlc-meta/cycles/.../handoff-v1.md]

## 결정·예외·진행 기록

[2026-05-27 14:30:30] CYCLE-START
  Intent: "회원 인증 기능 추가하자. JWT 기반으로."
  Initial classification: 새 기능 개발

[2026-05-27 14:31:00] DP-1: 인텐트 유형 분류
  Input: "회원 인증 기능 추가하자. JWT 기반으로."
  Decision: 새 기능 개발 — JWT 기반 인증
  Confirm: (자율 판단 — 명확)
  Output: 인텐트 유형 = 새 기능 개발
  Next: DP-2 영향 범위 분석

[2026-05-27 14:32:00] DP-2: 영향 범위 확정
  Input: REPO-MAP 도메인 조회 "auth"
  Decision: 영향 레포 = [frontend, api]. db-migrations는 의존 영향 없음
  Confirm: (큰 영향 아님 — 자율)
  Output: {frontend, api}
  Next: DP-3 STEP 선택

[2026-05-27 14:35:00] PROGRESS: STEP 1·2 완료, STEP 3 진입

[2026-05-27 14:40:00] DP-3: STEP 스킵·실행
  Input: AWS 6 factors 평가
  Decision: STEP 0~10 풀 사이클. STEP 8 옵셔널.
  Confirm: (사용자 응답: "ㅇㅋ 진행")
  Output: execution-plan.md 생성
  Next: DP-5 호출 순서

[2026-05-27 14:42:00] AWS-LINK: repo:api
  Path: api/aidlc-docs/audit.md
  Status: in-progress (Inception)

[2026-05-27 15:00:00] EX-4: 사용자 응답 모호
  Detected: "토큰 만료는?" 단답
  Policy: 꼬리질문 — 명확화 진행
  Result: 성공 — 응답 명확화
  Confirm: (사용자 응답: "15분 access, 7일 refresh")
  Next: DP-6 응답 검토

[2026-05-27 16:15:00] CYCLE-END
  Reason: 정상
  Total decisions: 8
  Total exceptions: 1
  Output paths: [frontend/src/auth/, api/src/auth/]

## AWS audit 스냅샷 (2026-05-27 16:15:00 기준)

### repo: frontend
Path: frontend/aidlc-docs/audit.md
Hash: a3f8c9d2...
{AWS audit.md 전체 인용 — 옵션 A}

### repo: api
...
```

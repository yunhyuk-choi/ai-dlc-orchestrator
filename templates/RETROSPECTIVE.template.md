# RETROSPECTIVE.template.md — 사이클 회고 템플릿

> 사이클별 회고 문서의 *단일 원천* (원칙 6).
> 사이클 종료 절차(TERMINATION §4.4) 정식 단계에서 채워 `dlc-meta/cycles/{cycle-id}/retrospective.md`로 산출.
> 목적: 이번 사이클의 *서술적 교훈*(룰북 갭·반복 마찰·검증 미스)을 구조화해 **진화(EVOLUTION / DP-9)** 입력으로 라우팅 (§3.E 신호 ⑤).
> 입도는 사이클 성격에 따라 *경량 ↔ 충실*. 사소 사이클은 슬롯 비우거나 "(없음)"으로 1줄 마감 — 강제 장문 금지.
> 변경 시 깃 PR/머지 (원칙 8).

---

# RETROSPECTIVE — {CYCLE_ID}

## 메타

| 항목 | 내용 |
|---|---|
| 사이클 ID | {CYCLE_ID} |
| 인텐트 원문 | {CYCLE_INTENT} |
| 영향 레포 | {AFFECTED_REPOS} |
| 종료 사유 | {CLOSE_REASON} |
| 입도 | {DEPTH}  (경량 / 충실) |
| 작성 시점 | {WRITTEN_AT} |

---

## 1. 잘된 것 (KEEP)

> 의도대로 매끄럽게 흘러간 것. 유지·강화할 패턴. 경량 사이클은 1줄 가능.

{WHAT_WORKED}

---

## 2. 실패·예상보다 어려웠던 것 (FAILED / HARDER)

> 막힌 지점·재시도·되돌림·예상 밖 난도. audit.md `EX-*` / `CORRECTION` / `SCOPE-EXPANSION` / `CYCLE-REOPEN` entry 참조.

{WHAT_FAILED}

---

## 3. 프레임워크·룰북 갭 (GAPS → 어느 파일이 메우나)

> "이 절차·규칙이 *없어서* 헤맸다"를 구체적으로. 각 갭마다 *그것을 메울 파일*을 지목 (진화 적용처 분기의 핵심 — §3.E).
> 형식 권장: 갭 한 줄 — `→ 메울 파일: {경로·섹션}` (인스턴스 `ORCHESTRATOR.md`/`REPO-MAP` 또는 공유 룰북).

{RULEBOOK_GAPS}

---

## 4. (재)발견된 환경 gotcha

> 다시 밟은 환경·도구 함정 (예: 셋업 전제·버전 충돌·경로 가정). 반복되면 ⑤ 가중.

{ENV_GOTCHAS}

---

## 5. 검증 미스 (VERIFICATION MISSES)

> 정합성 체크·검토 게이트가 *놓친 것*. 어떻게 빠져나갔고 무엇을 봤어야 했나.

{VERIFICATION_MISSES}

---

## 6. 제안 룰북 변경 (→ EVOLUTION 입력)

> **이 섹션이 DP-9(EVOLUTION §3.E)의 직접 입력.** 각 제안마다: 무엇을 / 어느 파일에 / 인스턴스인가 공유인가.
> 인스턴스 귀속(`ORCHESTRATOR.md`·`REPO-MAP`)은 DP-9 자동 게이트, 공유 룰북 귀속은 사람-큐레이션 큐(원칙 8)로만.
> 비어 있으면 "(제안 없음 — 지목할 갭 없었음)" — false negative 아님.

{PROPOSED_RULEBOOK_CHANGES}

---

## 부록. 템플릿 사용 가이드 (요약)

종료 절차(TERMINATION §4.4)에서 채움. 입도는 사이클 성격에 맞춰:
- **경량** (예외 0·범위 안정·기존 라우팅): §1·§6만 최소 채움, 나머지 "(없음)".
- **충실** (예외·sprawl·재오픈·새 인텐트 유형·룰북 갭 체감): 전 슬롯 채움. 특히 §3 갭·§6 제안 명시.

변수 분류:
- **작은 단위**: `{CYCLE_ID}` / `{CYCLE_INTENT}` / `{AFFECTED_REPOS}` / `{CLOSE_REASON}` / `{DEPTH}` / `{WRITTEN_AT}`
- **블록 단위**: `{WHAT_WORKED}` / `{WHAT_FAILED}` / `{RULEBOOK_GAPS}` / `{ENV_GOTCHAS}` / `{VERIFICATION_MISSES}` / `{PROPOSED_RULEBOOK_CHANGES}`

채움 데이터 소스(audit.md entry)·라우팅 절차는 `ix-ai-dlc/agents/orchestrator/TERMINATION.md` §4.4, 진화 소비는 `ix-ai-dlc/specs/EVOLUTION.md` §3.E 참조.

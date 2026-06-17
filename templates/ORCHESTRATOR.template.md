# ORCHESTRATOR.md — {SYSTEM_NAME}

> 시스템 라우팅 *인스턴스*. 오케스트레이터 에이전트가 읽고 작업 라우팅에 사용.
> 동작 규칙은 공유 리포(`ai-dlc-orchestrator`)의 `agents/orchestrator/ORCHESTRATOR-AGENT.md` 참조.

---

## 시스템 개요

- **이름**: {SYSTEM_NAME}
- **설명**: {SYSTEM_DESCRIPTION}

---

## 시스템 전역 컨벤션 (cross-repo 공통)

> SETTER S5.5에서 수집한 **시스템 전역 규약**. 여러 레포에 공통으로 걸리는 git/커밋 컨벤션·브랜치·PR/MR 정책·공유 코딩 표준만 기록 (단일 원천, 원칙 6).
> *개별 레포 단위* 스택·컨벤션 상세는 각 레포 `.claude/CLAUDE.md`(REPO-SETTER 담당) — 여기 중복 기록 금지.
> 미지정 항목은 "(미지정)"으로 둔다. 변경은 `dlc-meta` 커밋(POLICY-TRACKING).

{SYSTEM_CONVENTIONS}

---

## 레포 인벤토리

상세는 `@./REPO-MAP.md` 참조.
도메인 ↔ 레포 매핑은 REPO-MAP의 도메인 컬럼에서 정/역방향 조회 (단일 원천 — 원칙 6).

---

## 누적 라우팅 패턴

> DP-9(신호 ④ — 호출 경로)에서 감지·**사용자 승인된** 라우팅 단축 패턴이 이 섹션에 누적된다.
> 이곳은 진화의 *적용 결과 측* — **감지 입력이 아님** (감지는 로그 `index.md` B-④; 관심사 분리, D-Stage3-1).
> 형식·판정·등록 절차는 `ai-dlc-orchestrator/specs/EVOLUTION.md` §3.D 위임.

엔트리 형식:

| 인텐트 시그니처 `(유형, 영향 도메인 집합)` | 정규 호출 시퀀스 | 근거 (M/N · 승인 사이클) | 상태 |
|---|---|---|---|
| {예: 변경·수정 / {auth, api}} | {예: DP-1→DP-2→STEP4(repo)→STEP6→STEP9} | {예: 4/5 · 2026-..-cycle} | advisory |

- **상태 = advisory**: 등록된 단축은 *디폴트 힌트*이며 런타임이 재평가 가능 (라우팅 경직·과적합 방지).
- 변경(추가·수정·제거)은 DP-9 승인 + `dlc-meta` 루틴 커밋 (D-Stage3-6 — 공유 룰북 불가침). 

(아직 누적된 패턴 없음)

---

## 컨펌 정책 오버라이드

> DP-9(신호 ② — 컨펌 응답 패턴)에서 감지·**사용자 승인된** *이 프로젝트의* 컨펌 정책 조정이 누적된다.
> 공유 `ai-dlc-orchestrator/agents/orchestrator/DECISIONS.md`의 컨펌 디폴트는 **불변** — 여기는 프로젝트 로컬 오버라이드 (D-Stage3-6: 프로젝트별 학습이 전 프로젝트로 새지 않게).
> 형식·판정은 `ai-dlc-orchestrator/specs/EVOLUTION.md` §3.A 위임.

엔트리 형식:

| DP | 오버라이드 | 최빈 응답 `a*` | 근거 (m/n · 승인 사이클) |
|---|---|---|---|
| {예: DP-2} | {예: 자율 전환 / 디폴트=a*} | {예: 승인} | {예: 4/5 · 2026-..-cycle} |

- 변경은 DP-9 승인 + `dlc-meta` 루틴 커밋.

(아직 오버라이드 없음)

---

## 예외 정책 오버라이드

> DP-9(신호 ③ — 예외 반복)에서 감지·**사용자 승인된** (EX, 레포) 특화 처리가 누적된다.
> 공유 `ai-dlc-orchestrator/agents/orchestrator/ERROR-POLICY.md`의 디폴트는 **불변** — 여기는 프로젝트 로컬 오버라이드 (D-Stage3-6).
> 형식·판정은 `ai-dlc-orchestrator/specs/EVOLUTION.md` §3.C 위임.

엔트리 형식:

| (EX, 레포) | 특화 처리 | 근거 (M/N 재발률 · 승인 사이클) |
|---|---|---|
| {예: (EX-3, api)} | {예: 재시도 전 버전 핀 재검증} | {예: 4/5 · 2026-..-cycle} |

- 변경은 DP-9 승인 + `dlc-meta` 루틴 커밋. (REPO-SETTER 재점검은 일회성 액션 — 여기 기록 안 함.)

(아직 오버라이드 없음)

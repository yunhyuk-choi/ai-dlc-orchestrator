# HANDOFF.template.md — 핸드오프 문서 템플릿

> 시스템 단위 핸드오프 문서의 *단일 원천* (원칙 6).
> EX-9 트리거 시 HANDOFF-WRITER가 본 템플릿을 채워 `dlc-meta/cycles/{cycle-id}/handoff-v{n}.md`로 산출.
> 변수 채움 매핑·실행 절차는 `ai-dlc-orchestrator/agents/HANDOFF-WRITER.md` 본문 참조.
> 본 템플릿은 변경 시 깃 PR/머지 (원칙 8).

---

# HANDOFF {VERSION} — {SYSTEM_NAME} 시스템 부트스트랩 작업

> 이전 세션 컨텍스트 한계 대비 작업 이관용 문서.
> {PREVIOUS_VERSION} → {VERSION} 핵심 변경: {LATEST_CHANGE_SUMMARY}.
> 이 문서 하나로 새 세션이 self-contained하게 작업을 이어갈 수 있어야 함.

---

## 메타

| 항목 | 내용 |
|---|---|
| 버전 | {VERSION} |
| 작성일 | {WRITTEN_DATE} |
| 직전 버전 | {PREVIOUS_VERSION} |
| 트리거 사유 | {TRIGGER_REASON} |
| 응답 언어 | {RESPONSE_LANGUAGE} |
| 사용자 선호 | {USER_PREFERENCES} |

---

## 1. 프로젝트 정체성

> 프로젝트 식별·메타 모델·핵심 위치 설명. 시스템 자체 정의.

{PROJECT_IDENTITY}

---

## 2. 이전 결정 유지

> 이전 버전들에서 확정되어 *현재까지 유지되는 결정 사항*. 새 버전마다 누적된다.
> 첫 핸드오프(v1)에는 비어 있음 — "(아직 누적된 이전 결정 없음 — 첫 핸드오프)".
> 각 결정은 D-* 식별자와 함께. 본문 구성은 결정의 성격에 따라 자유 (표·다이어그램·서술).

{CORE_DECISIONS_RETAINED}

---

## 3. ★★ {VERSION} 핵심 변경

> 이번 버전에서 새로 확정된 결정·산출물·구조 변경. 새 세션이 가장 먼저 인지해야 할 부분.
> 다음 버전에서는 §2 "이전 결정 유지"로 이관된다.

{LATEST_DECISION_HIGHLIGHT}

---

## 4. 현재 진행 상황

> Stage별 ✓/진행/대기 상태. 트리 또는 체크리스트 형식.
> Stage 1, Stage 2, Stage 3, Stage 4 (시스템 부트스트랩 → 운영 → 진화 → 거버넌스).

{PROGRESS_STATUS}

---

## 5. 다음 작업

> 다음 세션이 진행해야 할 *구체 작업*. 작업 이름·산출물·진행 순서·합의된 방식.
> 큐와 다름 — *지금 즉시 진행할 한 작업*에 집중.

{NEXT_ACTION_GUIDE}

---

## 6. 큐 (변경·추가 반영)

> 잔여 작업 + 이번 사이클에서 신규 발생 항목 + 이번 사이클에서 해소된 항목 3 카테고리.
> 형식 권장:
>   - 6.1 유지된 큐
>   - 6.2 v{VERSION} 신규 큐
>   - 6.3 해소된 항목 (v{VERSION}에서 제거)

{QUEUE}

---

## 7. Decision Log

> 누적 결정 사항 표. ID / 결정 / 상태(✓/진행/대기).
> 새 결정은 *이번 버전*에서 강조 표시 (예: 굵게).

{DECISION_LOG_TABLE}

---

## 8. 새 세션 첫 한마디 가이드

> 새 세션 시작 시 사용자가 보낼 권장 한마디 + Claude 응답 가이드.
> 작성된 그대로 사용자가 복사·붙여넣기 가능한 형태.

새 세션 시작 시 사용자가 보낼 권장 한마디:

> {NEW_SESSION_FIRST_MESSAGE}

Claude는 응답으로:

{CLAUDE_RESPONSE_GUIDE}

---

## 9. 첨부해야 할 파일

> 다음 세션용 첨부 파일 목록. 필수 / 작업 시 참조 / 옵션 3 카테고리 권장.
> 산출물 디렉토리 구조 그대로 명시 (예: `orchestrator/ORCHESTRATOR-AGENT.md`).

{REQUIRED_ATTACHMENTS}

---

## 부록. 템플릿 사용 가이드 (요약)

본 템플릿은 HANDOFF-WRITER가 자동 채움. 수동 작성도 가능 (Stage 2 본격 진행 전 dogfooding 시기).

변수 분류:
- **작은 단위** (단일 값): `{VERSION}` / `{WRITTEN_DATE}` / `{PREVIOUS_VERSION}` / `{TRIGGER_REASON}` / `{RESPONSE_LANGUAGE}` / `{USER_PREFERENCES}` / `{SYSTEM_NAME}` / `{LATEST_CHANGE_SUMMARY}`
- **블록 단위** (섹션 채움): `{PROJECT_IDENTITY}` / `{CORE_DECISIONS_RETAINED}` / `{LATEST_DECISION_HIGHLIGHT}` / `{PROGRESS_STATUS}` / `{NEXT_ACTION_GUIDE}` / `{QUEUE}` / `{DECISION_LOG_TABLE}` / `{NEW_SESSION_FIRST_MESSAGE}` / `{CLAUDE_RESPONSE_GUIDE}` / `{REQUIRED_ATTACHMENTS}`

채움 데이터 소스 매핑·실행 절차는 `ai-dlc-orchestrator/agents/HANDOFF-WRITER.md` 본문에서 본격 명세.

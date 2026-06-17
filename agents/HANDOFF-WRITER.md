# HANDOFF-WRITER.md — 핸드오프 문서 생성 서브 에이전트 룰북

> EX-9 (컨텍스트 한도 임박) 또는 명시 요청 시 오케스트레이터가 호출하는 서브 에이전트.
> 본 룰북은 `ai-dlc-orchestrator/agents/HANDOFF-WRITER.md`에 위치.
> 동작 정책 본문은 `ai-dlc-orchestrator/agents/orchestrator/ERROR-POLICY.md` §4 참조.

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 서브 에이전트 룰북 |
| 호출 주체 | 오케스트레이터 에이전트 (직접 호출 불가) |
| 수명 | 호출당 1회. 산출 후 컨텍스트 해제 |
| 트리거 | EX-9 (컨텍스트 한도 임박) / 사용자 명시 요청 / 사이클 종료 시 옵션 / 수동 안전 백업 |
| 위치 | `ai-dlc-orchestrator/agents/HANDOFF-WRITER.md` |
| 사용자 채널 | 직접 통신 없음. 결과는 오케스트레이터 통해 사용자에게 전달 |

---

## 2. 책임 / 비책임

### 2.1 책임

1. 트리거 사유 분류 (EX-9 / 명시 요청 / 사이클 종료 옵션 / 수동 백업)
2. 현재 사이클 상태 + audit.md 누적 + 시스템 상태 수집
3. **`templates/HANDOFF.template.md`를 로드해** 그 섹션·변수를 채움 (POLICY-TEMPLATE-ADHERENCE — 템플릿에서 생성, 손수 자유 작성 금지)
4. **템플릿의 정본 경로** `dlc-meta/cycles/{cycle-id}/handoff-v{n}.md`로 산출 (플랫 경로·임의 경로 금지)
5. 정합성 자체 체크 + 오케스트레이터에 4-튜플 반환

### 2.2 비책임 (다른 에이전트·산출물에 위임)

| 영역 | 위임 대상 |
|---|---|
| HANDOFF 트리거 판단 | 오케스트레이터 (DP-10·EX-9) |
| 핸드오프 포맷 정의 | `HANDOFF.template.md` (단일 원천, 원칙 6) |
| 사이클 로그 형식 명세 | CYCLE-LOG.md |
| 사용자 통지 | 오케스트레이터 (출력 채널 A) |
| 결정 분류·해석 | 본 에이전트 단독 책임 X — audit.md를 *그대로 기록한 정보*에서 추출만 |

---

## 3. 핵심 원칙

- **원칙 1**: 호출 시점·책임 분리 — 핸드오프 작성은 *드물고 큰 컨텍스트 작업*이라 별도 분리
- **원칙 4**: AI 자율 실행, 사용자는 의미 결정만 — 트리거 판단은 오케스트레이터, 본 에이전트는 실행만
- **원칙 6**: 단일 원천 — 변수 채움 데이터는 audit.md / REPO-MAP / 시스템 상태에서 *파생*만, 신규 생성 X
- **원칙 7**: 오케스트레이터 호출 책임 — 사용자가 직접 본 에이전트 호출 X

---

## 4. 입출력

### 4.1 입력 (오케스트레이터로부터)

| 필드 | 내용 |
|---|---|
| 트리거 사유 | EX-9 / 명시 요청 / 사이클 종료 옵션 / 수동 백업 |
| 현재 사이클 ID | `dlc-meta/cycles/{cycle-id}/` |
| 시스템 상태 스냅샷 경로 | `dlc-meta/ORCHESTRATOR.md` + `REPO-MAP.md` |
| 이전 핸드오프 버전 | `{PREVIOUS_VERSION}` (없으면 — 첫 핸드오프) |
| 이번 사이클 최신 결정 강조 | 오케스트레이터가 식별한 *이번 사이클*의 신규·중요 D-* 항목 |
| 새 세션 첫 한마디 컨텍스트 | 오케스트레이터가 인지한 *다음 작업*의 진입 메시지 후보 |

### 4.2 출력 (오케스트레이터에 보고 — 4-튜플 표준)

1. **생성 파일 경로[]** — `dlc-meta/cycles/{cycle-id}/handoff-v{n}.md`
2. **정합성 체크 결과** — §7 자체 체크 항목별 통과/실패 + 실패 사유
3. **인터뷰 응답 원본** — 본 에이전트는 사용자 인터뷰 *없음*. 빈 객체 반환
4. **권고 다음 단계** — 사용자에게 다운로드 안내 + 다음 세션 시작 가이드

---

## 5. 실행 절차

```
[페이즈 1] 입력 수집 & 사유 분류   →  W1
[페이즈 2] 데이터 수집              →  W2
[페이즈 3] 변수 채움 & 산출         →  W3 ~ W4
[페이즈 4] 검증 & 보고              →  W5
[페이즈 5] 종료                     →  W6
```

### W1 — 트리거 사유 분류

오케스트레이터로부터 받은 트리거 사유를 분류:
| 사유 | 처리 특이점 |
|---|---|
| EX-9 컨텍스트 한도 | 가장 일반적. 진행 중 사이클 PAUSE 상태로 기록 |
| 사용자 명시 요청 | 사이클 상태 변경 없이 핸드오프만 산출 |
| 사이클 종료 시 옵션 — 정상 | `TERMINATION.md` §2 정상 종료 신호와 함께. 사이클 정상 종료 보고와 함께 |
| 사이클 종료 시 옵션 — 예외 | `TERMINATION.md` §3 예외 종료 신호 (EX-5/EX-1·EX-2 escalate/EX-3/EX-6 등). 부분 진행 결과 보존 강조 |
| 수동 안전 백업 | 큰 분기점 결정 직후. 사이클 상태 변경 없음 |

### W2 — 데이터 수집

다음 6 원천에서 데이터 수집 (원칙 6 — 단일 원천 파생):
| 원천 | 채울 변수 후보 |
|---|---|
| `dlc-meta/cycles/{cycle-id}/audit.md` | `{DECISION_LOG_TABLE}` (해당 사이클 부분) / `{CORE_DECISIONS_RETAINED}` (이전 결정 분류) / `{LATEST_DECISION_HIGHLIGHT}` 후보 |
| `dlc-meta/ORCHESTRATOR.md` | `{PROJECT_IDENTITY}` 일부 / `{SYSTEM_NAME}` |
| `dlc-meta/REPO-MAP.md` | `{PROJECT_IDENTITY}` 보강 / `{PROGRESS_STATUS}` 레포 영향 부분 |
| 이전 핸드오프(`handoff-v{n-1}.md`) | `{CORE_DECISIONS_RETAINED}` 누적 / `{QUEUE}` 직전 상태 / `{DECISION_LOG_TABLE}` 직전 표 |
| 오케스트레이터가 명시한 *이번 사이클 신규·중요 D-*항목* | `{LATEST_DECISION_HIGHLIGHT}` 본문 |
| 오케스트레이터가 명시한 *다음 작업 진입 메시지* | `{NEW_SESSION_FIRST_MESSAGE}` / `{NEXT_ACTION_GUIDE}` |

### W3 — 변수 매핑

**먼저 `ai-dlc-orchestrator/templates/HANDOFF.template.md`(현재 기본 브랜치의 것)를 통째로 로드한다** (POLICY-TEMPLATE-ADHERENCE). 산출물은 이 템플릿 본문에서 *생성*하며, 템플릿의 모든 섹션(메타·§1~§9·부록)과 변수 자리(`{...}`)를 그대로 보존한 채 값만 치환한다. 템플릿을 무시하고 핸드오프를 자유 형식으로 손수 작성하는 것은 *결함*이다.

`HANDOFF.template.md`의 변수를 채움. 매핑표:

| 변수 | 분류 | 데이터 소스 | 채움 방식 |
|---|---|---|---|
| `{VERSION}` | 작은 | 이전 핸드오프 버전 + 1 (`v{n}`) | 자동 산정 |
| `{WRITTEN_DATE}` | 작은 | 시스템 시간 | 자동 (YYYY-MM-DD) |
| `{PREVIOUS_VERSION}` | 작은 | 입력 필드 | 직접 매핑 |
| `{TRIGGER_REASON}` | 작은 | W1 분류 결과 | 직접 매핑 |
| `{RESPONSE_LANGUAGE}` | 작은 | `dlc-meta/ORCHESTRATOR.md` 또는 시스템 디폴트 | 직접 매핑 |
| `{USER_PREFERENCES}` | 작은 | `dlc-meta/ORCHESTRATOR.md` 누적 패턴 + 최근 사이클 audit | 요약 추출 |
| `{SYSTEM_NAME}` | 작은 | `dlc-meta/ORCHESTRATOR.md` `{SYSTEM_NAME}` 또는 `REPO-MAP.md` | 직접 매핑 |
| `{LATEST_CHANGE_SUMMARY}` | 작은 | `{LATEST_DECISION_HIGHLIGHT}` 한 줄 요약 | 추출 |
| `{PROJECT_IDENTITY}` | 블록 | `dlc-meta/ORCHESTRATOR.md` + `REPO-MAP.md` | 블록 구성 |
| `{CORE_DECISIONS_RETAINED}` | 블록 | 이전 핸드오프 §2 + §3 (이번 버전 §3가 다음 버전 §2로 이관) | 누적 통합 |
| `{LATEST_DECISION_HIGHLIGHT}` | 블록 | 오케스트레이터 명시 신규·중요 D-* + audit.md 해당 entry | 블록 구성 |
| `{PROGRESS_STATUS}` | 블록 | `dlc-meta/ORCHESTRATOR.md` 진행 상태 + 사이클 audit | 트리 구성 |
| `{NEXT_ACTION_GUIDE}` | 블록 | 오케스트레이터 명시 *다음 작업* | 블록 구성 |
| `{QUEUE}` | 블록 | 이전 핸드오프 §6 + 이번 사이클 audit (신규/해소 식별) | 3 카테고리 분류 |
| `{DECISION_LOG_TABLE}` | 블록 | 이전 핸드오프 §7 + 이번 사이클 신규 D-* | 누적 표 |
| `{NEW_SESSION_FIRST_MESSAGE}` | 블록 | 오케스트레이터 명시 진입 메시지 후보 | 인용 형식 |
| `{CLAUDE_RESPONSE_GUIDE}` | 블록 | 오케스트레이터 명시 *다음 작업* 기반 자동 생성 | 블록 구성 |
| `{REQUIRED_ATTACHMENTS}` | 블록 | 이번 사이클 생성 산출물 + 작업 시 참조 산출물 + 옵션 분류 | 3 카테고리 분류 |

### W4 — 산출

```bash
mkdir -p dlc-meta/cycles/{cycle-id}
출력 파일: dlc-meta/cycles/{cycle-id}/handoff-v{n}.md   ← 템플릿 정본 경로. 변경 금지
```

- HANDOFF.template.md 변수 모두 채워진 결과를 단일 마크다운으로 저장
- **경로 가드**: 반드시 템플릿 정본 경로 `dlc-meta/cycles/{cycle-id}/handoff-v{n}.md`에 쓴다. 플랫 경로(예: 리포 루트의 `handoff.md`)나 임의 경로에 쓰면 *결함* (POLICY-TEMPLATE-ADHERENCE 위반 — 과거 실제 사고 사례).
- **인코딩 가드**: 파일은 UTF-8(BOM 없음)·LF로, 직접 파일 쓰기로 저장한다 (POLICY-ENCODING — 로케일 의존 셸 출력 금지). 저장 후 U+FFFD·BOM 손상 검증.
- 빈 변수 발견 시 → §6 정합성 자체 체크 실패로 처리

### W5 — 정합성 자체 체크 + 오케스트레이터 보고

§7 체크 항목 수행. 결과를 오케스트레이터에 4-튜플 형식으로 반환.

### W6 — 종료

- 컨텍스트 해제
- 본 에이전트는 *상태 보존 없음*. 다음 호출은 새 컨텍스트.

---

## 6. 자체 체크 항목

### 6.0 템플릿 준수 (POLICY-TEMPLATE-ADHERENCE)

- 산출물이 `templates/HANDOFF.template.md`에서 *생성*됐나 (손수 자유 작성 아님)
- 템플릿의 모든 섹션(메타·§1~§9·부록)이 *하나도 누락 없이* 그대로 존재하나
- 템플릿의 모든 변수 자리가 빠짐없이 처리됐나 (드롭된 섹션·변수 0개)
- 산출 경로가 정본 경로 `dlc-meta/cycles/{cycle-id}/handoff-v{n}.md`인가 (플랫·임의 경로 아님)
- 파일 인코딩 UTF-8(BOM 없음)·LF인가, 손상문자(U+FFFD)·BOM 없나 (POLICY-ENCODING)

### 6.1 변수 채움 완전성

- 작은 단위 변수 8개 모두 채워졌나
- 블록 단위 변수 10개 모두 채워졌나 (빈 경우 명시적 *"(없음)"* 또는 *"(아직 누적된 항목 없음)"* 허용)
- 자리 표시자 `{...}`가 결과 파일에 남아 있지 않은지

### 6.2 단일 원천 정합성 (원칙 6)

- 변수 값이 모두 *원천에서 파생* — 본 에이전트가 신규 생성한 정보 없음
- 신규 정보 발견 시 → 오케스트레이터에 *보고만*, 핸드오프에는 포함 X

### 6.3 self-contained 검증

- §1 정체성으로 시스템이 뭔지 식별 가능
- §2 + §3로 *현재까지 결정 사항* 모두 인지 가능
- §4 진행 상황으로 어디까지 왔는지 명확
- §5 다음 작업으로 *바로 진행 가능*
- §8 첫 한마디로 사용자가 *복사·붙여넣기로 시작* 가능
- §9 첨부 목록으로 *필수 파일* 빠짐 없이 식별

### 6.4 호환성

- 변수 형식 `{NAME}` 준수 (다른 우리 템플릿과 일관)
- 마크다운 렌더링 깨짐 없음
- audit.md 호환 (D-* 식별자 유지)

---

## 7. 산출물 템플릿 참조

본 에이전트가 채우는 인스턴스의 *템플릿 본문*은 별도 파일로 관리:

| 인스턴스 | 템플릿 위치 |
|---|---|
| `dlc-meta/cycles/{cycle-id}/handoff-v{n}.md` | `ai-dlc-orchestrator/templates/HANDOFF.template.md` |

템플릿 본문 변경은 *깃 PR/머지*로만 (원칙 8). 본 에이전트는 *항상 현재 main의 템플릿*을 읽어 인스턴스를 채운다.

---

## 8. 변수 채움 데이터 소스 부록

W3 매핑표 요약 — 빠른 참조용:

| 데이터 소스 | 주요 채움 변수 |
|---|---|
| `dlc-meta/cycles/{cycle-id}/audit.md` | DECISION_LOG_TABLE / LATEST_DECISION_HIGHLIGHT / QUEUE 신규·해소 식별 |
| `dlc-meta/ORCHESTRATOR.md` | PROJECT_IDENTITY / SYSTEM_NAME / RESPONSE_LANGUAGE / USER_PREFERENCES / PROGRESS_STATUS |
| `dlc-meta/REPO-MAP.md` | PROJECT_IDENTITY 보강 / PROGRESS_STATUS 레포 부분 |
| 이전 `handoff-v{n-1}.md` | CORE_DECISIONS_RETAINED 누적 / QUEUE 유지 / DECISION_LOG_TABLE 누적 |
| 오케스트레이터 입력 | LATEST_DECISION_HIGHLIGHT 본문 / NEXT_ACTION_GUIDE / NEW_SESSION_FIRST_MESSAGE / CLAUDE_RESPONSE_GUIDE |
| 시스템 시간 | WRITTEN_DATE |
| 자동 산정 | VERSION (이전 + 1) / LATEST_CHANGE_SUMMARY (LATEST_DECISION_HIGHLIGHT 추출) |

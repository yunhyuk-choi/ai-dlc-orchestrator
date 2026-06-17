# CYCLE-CLOSER.md — 사이클 종료 후처리 서브 에이전트 룰북

> 오케스트레이터가 사이클 종료 판단(DP-8) 시 호출하는 서브 에이전트 룰북.
> 핵심: audit.md 최종화 + AWS audit 스냅샷 흡수 + 사용자 보고 데이터 준비.
> 위치: `ai-dlc-orchestrator/agents/CYCLE-CLOSER.md`
> 호출 흐름·종료 신호 본문은 `ai-dlc-orchestrator/agents/orchestrator/TERMINATION.md` §4 참조.

---

## 0. 컨텍스트

본 에이전트는 사이클 종료 시점에 호출:

```
[정상 종료 신호 — TERMINATION.md §2 / 예외 종료 신호 — TERMINATION.md §3]
    ↓
[DP-8 사이클 종료 판단 — 오케스트레이터]
    ↓
[CYCLE-CLOSER 호출 — 컨텍스트 4 필드 전달]
    ├─ 사이클 메타 최종화 (audit.md 메타 섹션 + CYCLE-END entry)
    ├─ AWS audit 스냅샷 흡수 (CYCLE-LOG.md §9.2)
    ├─ (선택) audit.md 무결성 hash 계산
    ├─ 사용자 보고용 요약 생성 (TERMINATION.md §7 형식)
    └─ 외부 액션 (티켓·커밋·보고서) — 조건부, Stage 3+ 진화 영역
    ↓
[오케스트레이터에 4-튜플 보고]
    ↓
[오케스트레이터가 사용자에게 사이클 요약 보고]
```

---

## 1. 정체성

| 항목 | 내용 |
|---|---|
| 종류 | 서브 에이전트 룰북 |
| 호출 주체 | 오케스트레이터 (DP-8 결정 후) |
| 수명 | 사이클당 1회. 종료 후 컨텍스트 해제 |
| 사용자 채널 | 직접 통신 없음. 보고는 오케스트레이터 통해 |
| 위치 | `ai-dlc-orchestrator/agents/CYCLE-CLOSER.md` |

---

## 2. 책임 / 비책임

### 2.1 책임

1. 사이클 메타 최종화 — `audit.md` 메타 섹션 + CYCLE-END entry 기록
2. AWS audit 스냅샷 흡수 — `CYCLE-LOG.md §9.2` 따라
3. (선택) audit.md 무결성 hash 계산 — Stage 3+ 본격
4. 사용자 보고용 요약 데이터 생성 — `TERMINATION.md §7` 형식
5. 종료 사유별 분기 처리 (정상 / PAUSE / ABORT 간소화)
6. 정합성 자체 체크 + 오케스트레이터에 4-튜플 보고

### 2.2 비책임 (다른 에이전트·산출물에 위임)

| 영역 | 위임 대상 |
|---|---|
| 사이클 종료 판단 (DP-8) | 오케스트레이터 |
| 종료 신호 분류 (정상 / 예외) | `TERMINATION.md` §2~3 |
| 사용자에게 직접 보고 | 오케스트레이터 (책임 6) — 본 에이전트는 *보고 데이터 준비*만 |
| 사이클 로그 형식 명세 | `specs/CYCLE-LOG.md` |
| AWS audit 흡수 본문 형식 | `specs/CYCLE-LOG.md §9.2` |
| 외부 시스템 호출 본격 명세 (티켓·메신저 등) | Stage 3+ 큐 (현재는 placeholder) |
| 핸드오프 산출 | HANDOFF-WRITER (별도 트리거) |

---

## 3. 핵심 원칙

- **원칙 1**: 호출 시점·책임 분리 — 사이클 종료 시점에만 호출
- **원칙 4**: AI 자율 실행 — 종료 후처리는 *자율 수행*. 사용자 컨펌은 *오케스트레이터가 종료 판단 시점에 이미 받음*
- **원칙 5**: 사이클 로깅 의무 — CYCLE-END entry 누락 X
- **원칙 6**: 단일 원천 — 보고 데이터는 audit.md에서 *파생*만, 신규 생성 X
- **원칙 7**: 오케스트레이터 호출 책임

---

## 4. 입출력

### 4.1 입력 (오케스트레이터로부터 — 4 필드 + 확장 게이트)

> TERMINATION.md §4.1 정의 그대로.

| 필드 | 내용 | 단일 원천 |
|---|---|---|
| **사이클 ID** | 종료할 사이클 식별자 | `dlc-meta/cycles/{cycle-id}/` 디렉토리명 |
| **종료 사유** | 정상 / 예외 분류 + 구체 사유 (EX-N) | DP-8 결정 기록 또는 EX-N |
| **영향 레포·산출물 목록** | 사이클 중 영향 레포 + 생성·수정 파일 | audit.md 누적 결정 추적 |
| **audit.md 경로** | 결정 추적 데이터 원천 | `dlc-meta/cycles/{cycle-id}/audit.md` |

**확장 게이트** (TERMINATION.md §4.2):
> 본 룰북 작성 시 추가 필드 필요성 검토 결과 — **4 필드 충분**. 모든 다른 정보는 audit.md / REPO-MAP / ORCHESTRATOR.md에서 *파생 가능* (원칙 6).
> 향후 외부 액션 (티켓·커밋·보고서) 본격 명세 시 추가 필드 필요할 수 있음 — Stage 3+ EVOLUTION 큐.

### 4.2 출력 (오케스트레이터에 보고 — 4-튜플 표준)

1. **생성 파일 경로[]**
   - 최종화된 `audit.md` (수정 — 메타 갱신·CYCLE-END entry·AWS 스냅샷)
   - (외부 액션 산출 시) 티켓·커밋·보고서 경로 (Stage 3+)
2. **정합성 체크 결과** — §6 자체 체크 항목별 통과/실패
3. **인터뷰 응답 원본** — 본 에이전트는 사용자 인터뷰 *없음*. 빈 객체 반환
4. **권고 다음 단계** — `TERMINATION.md §7` 형식의 사용자 보고용 데이터 + 다음 사이클 대기 권장

---

## 5. 실행 절차

```
[페이즈 1] 입력 검증 + 종료 사유 분류  → CC1
[페이즈 2] audit.md 최종화             → CC2
[페이즈 3] AWS audit 스냅샷 흡수       → CC3
[페이즈 4] (선택) 무결성 hash          → CC4
[페이즈 5] 사용자 보고 데이터 생성     → CC5
[페이즈 6] 외부 액션 (조건부)          → CC6
[페이즈 7] 검증 & 보고                 → CC7
[페이즈 8] 종료                        → CC8
```

### CC1 — 입력 검증 + 종료 사유 분류

입력 4 필드 검증 + 종료 사유 분류:

| 사유 분류 | 처리 모드 |
|---|---|
| 정상 (TERMINATION.md §2 신호) | **풀 모드** — 모든 페이즈 수행 |
| 예외 D PAUSE (EX-5 등) | **풀 모드** + PAUSE 메타 기록 — 재개 가능 명시 |
| 예외 E ABORT, 진행률 ≥ 30% | **간소화 모드** — CC2·CC3·CC5만, CC4·CC6 스킵 |
| 예외 E ABORT, 진행률 < 30% | **즉시 종료 모드** — CC2만 (audit.md에 ABORT entry만), CC3~CC6 스킵 |

진행률 산정:
- 실행된 STEP 수 / 계획된 STEP 수 (audit.md PROGRESS entry 카운트)
- 또는 사용자 명시 진행률
- 정확한 산식은 Stage 3+ EVOLUTION에서 정제. 본 룰북은 *대략 휴리스틱*

### CC2 — audit.md 최종화

`{audit.md 경로}` 파일의 *append-only* 본문은 그대로 두고, *예외적 수정 허용 영역*(메타 섹션) 갱신 + CYCLE-END entry 추가:

**메타 섹션 갱신** (CYCLE-LOG.md §4.2):
```markdown
## 사이클 메타
- 시작: {기존 유지}
- 종료: {현재 시각}                  ← 갱신
- 종료 사유: {정상 / 예외(EX-N)}      ← 갱신 (입력 필드)
- 인텐트 원문: {기존 유지}
- 영향 레포: {입력 필드 — 최종 확정}  ← 갱신
- 산출물: {입력 필드 — 최종 확정}     ← 갱신
```

**CYCLE-END entry 추가** (CYCLE-LOG.md §5):
```
[YYYY-MM-DD HH:MM:SS] CYCLE-END
  Reason: 정상 / 예외(EX-N)
  Total decisions: {DP-* 개수 — audit.md 파싱}
  Total exceptions: {EX-* 개수 — audit.md 파싱}
  Output paths: [path1, path2, ...]
```

### CC3 — AWS audit 스냅샷 흡수

`CYCLE-LOG.md §9.2` 절차 그대로:

각 영향 레포의 `{레포}/aidlc-docs/audit.md`를 *시점 동결 스냅샷*으로 우리 audit.md 끝에 추가:

```markdown
## AWS audit 스냅샷 ({사이클 종료 시각 기준})

### repo: {slug}
Path: {레포 경로}/aidlc-docs/audit.md
Hash: {SHA-256 또는 git commit hash}

{AWS audit.md 전체 인용 — 옵션 A 기본}

### repo: {slug2}
...
```

기본: **옵션 A (전체 인용)** — 단일 원천 우선 (CYCLE-LOG.md §9.3).

### CC4 — (선택) 무결성 hash 계산

> Stage 3+ 본격. 현재는 *수행 가능 시 실행*, 미지원 시 스킵.

audit.md 전체에 대해 SHA-256 계산 → 메타 섹션에 기록:
```markdown
## 사이클 메타
- ...
- audit hash: {SHA-256}                 ← 갱신 (Stage 3+)
- hash 계산 시각: {현재 시각}            ← 갱신
```

추후 변조 감지 가능.

### CC5 — 사용자 보고 데이터 생성

`TERMINATION.md §7` 형식 따라 데이터 준비. 오케스트레이터가 *사용자에게 직접 보고* (책임 6) — 본 에이전트는 *데이터만 준비*.

**정상 종료** (`§7.1`):
- 사이클 ID / 처리한 인텐트 / 영향 레포 / 주요 산출물 / 결정 추적 발췌 / 사용자 컨펌 응답 요약 / audit.md 경로 / 다음 권장

**예외 종료** (`§7.2`):
- 사이클 ID / 종료 사유(EX-N) / 처리한 인텐트 / 완료 진행률 / 부분 산출물 / audit.md 경로 / 재개 방법

생성 방식: audit.md를 파싱해 위 필드 추출. 새 정보 생성 X (원칙 6).

### CC6 — 외부 액션 (조건부, Stage 3+ placeholder)

**현재는 placeholder.** 향후 다음 외부 액션이 책임 범위에 들어올 수 있음:
- 티켓 생성 (Jira / Linear / GitHub Issues 등)
- 커밋·머지 (다중 레포 코디네이션 — STEP 9의 시스템 레벨 자동화)
- 보고서 작성 (PDF / 사내 위키 등)

본 룰북 v1.0에서는:
- 외부 액션 *책임 범위 명시*만 (구체 호출 절차 X)
- 외부 도구 어댑터 (MCP 등) 통합은 *Stage 3+ EVOLUTION*

조건부 실행:
- 외부 어댑터가 *준비된 경우*에만 수행
- 미준비 시 — *권고 다음 단계*에 "외부 액션 수동 진행 권장" 명시

### CC7 — 정합성 자체 체크 + 오케스트레이터 보고

§6 자체 체크 항목 수행. 4-튜플로 오케스트레이터에 반환.

### CC8 — 종료

- 컨텍스트 해제
- 본 에이전트는 *상태 보존 없음*. 다음 사이클 종료 시 새 컨텍스트.

---

## 6. 자체 체크 항목

| 항목 | 통과 기준 |
|---|---|
| 입력 4 필드 완전성 | 사이클 ID / 종료 사유 / 영향 레포·산출물 / audit.md 경로 모두 존재 |
| audit.md 존재 + 쓰기 가능 | 입력 경로의 audit.md 파일 접근 가능 |
| 메타 섹션 갱신 | 종료 시각·사유 갱신됨, 인텐트·시작 시각 보존됨 (수정 X) |
| CYCLE-END entry 추가 | 본문 마지막에 entry 1개 append됨 |
| AWS 스냅샷 (정상·PAUSE 모드) | 영향 레포 각각의 audit.md 인용됨, hash 기록됨 |
| 보고 데이터 완전성 | TERMINATION.md §7 형식 필드 모두 채워짐 (또는 명시적 "(없음)") |
| append-only 정합성 | 본문 기존 entry 수정 X (CYCLE-LOG.md §10) |
| 모드 분기 정확성 | 종료 사유에 맞는 모드 (풀/간소화/즉시 종료)로 페이즈 실행 |

---

## 7. 종료 모드별 페이즈 매트릭스

빠른 참조:

| 페이즈 | 정상 / D PAUSE | E ABORT 30%+ | E ABORT <30% |
|---|---|---|---|
| CC1 입력 검증·분류 | ✓ | ✓ | ✓ |
| CC2 audit 최종화 | ✓ | ✓ | ✓ (ABORT entry만) |
| CC3 AWS 스냅샷 흡수 | ✓ | ✓ | 스킵 |
| CC4 무결성 hash | ✓ (조건부) | 스킵 | 스킵 |
| CC5 보고 데이터 | ✓ | ✓ | ✓ (간소) |
| CC6 외부 액션 | ✓ (조건부) | 스킵 | 스킵 |
| CC7 검증·보고 | ✓ | ✓ | ✓ |

---

## 8. 양방향 참조 맵

| 문서 | 본 룰북과의 관계 |
|---|---|
| `agents/orchestrator/ORCHESTRATOR-AGENT.md` 책임 9 | 호출 주체 |
| `agents/orchestrator/TERMINATION.md` §2~3 | 종료 신호 분류 위임처 |
| `agents/orchestrator/TERMINATION.md` §4.1 | 입력 4 필드 정의 위임처 |
| `agents/orchestrator/TERMINATION.md` §4.2 | 확장 게이트 정책 위임처 |
| `agents/orchestrator/TERMINATION.md` §7 | 사용자 보고 데이터 형식 위임처 |
| `specs/CYCLE-LOG.md` §4~5 | audit.md 메타·CYCLE-END entry 형식 |
| `specs/CYCLE-LOG.md` §9.2 | AWS audit 스냅샷 흡수 절차 |
| `specs/CYCLE-LOG.md` §10 | append-only 정합성 |
| `agents/HANDOFF-WRITER.md` | 별도 트리거 — 본 에이전트와 무관 |

---

## 9. Stage 3+ 진화 후보

본 룰북 v1.0에서 *미명세된 영역* — 향후 EVOLUTION 후보:

| 영역 | 메모 |
|---|---|
| **외부 액션 (CC6)** | 티켓·커밋·보고서 외부 도구 통합. MCP 어댑터 또는 별도 인터페이스 |
| **진행률 산정 휴리스틱** | 30% 기준의 정확한 산식 — STEP 수 / 토큰 / 시간 등 |
| **무결성 hash 본격 도입** | CC4의 표준화 + 변조 감지 메커니즘 |
| **사이클 통계 누적** | CYCLE-END 메타데이터의 *시스템 단위 누적* — DP-9 진화 제안 입력 강화 |
| **부분 산출물 명시 형식** | 예외 종료 시 부분 산출물의 *완성도 표시* 표준 |
| **CYCLE-CLOSER 호출 컨텍스트 확장** | 4 필드 → 5+ 필드 (외부 액션 정보 등) — §4.1 확장 게이트 발동 시점 |

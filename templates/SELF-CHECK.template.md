# SELF-CHECK.template.md — 오케스트레이터 세션 자가점검 주입문 (단일 원천)

> **인스턴스 산출물의 템플릿** (POLICY-TEMPLATE-ADHERENCE). SETTER(S8.7)가 이 템플릿에서 머신 로컬 주입문 파일 `{공유리포}/.claude/orchestrator-selfcheck.txt`(개인 — gitignore)을 생성하고, 같은 디렉토리 `settings.local.json`의 `UserPromptSubmit` 훅이 **매 프롬프트마다** 그 파일을 stdout으로 흘린다.
> 훅 stdout은 런타임이 컨텍스트에 주입한다 — *모델의 자발적 Read가 아니라 기계적 주입*이라, 컨텍스트 압축이 무엇을 지우든 다음 턴에 되살아난다.
> 위치: `ai-dlc-orchestrator/templates/SELF-CHECK.template.md`

---

## 0. 왜 이 템플릿이 필요한가

정체성 보장에는 층위가 둘이고, 서로를 대체하지 못한다:

| 층위 | 수단 | 보장 범위 | 한계 |
|---|---|---|---|
| **로드** | 리포 루트 `CLAUDE.md`의 `@` 임포트 | 세션 시작 시 코어 룰북 전개 — 기계적 | 세션 시작 *1회*. 임포트가 압축 후 재전개되는지는 런타임 미보장 |
| **지속** | 본 템플릿에서 나온 `UserPromptSubmit` 훅 | *매 프롬프트* 재주입 | 짧아야 한다 (매 턴 비용) · **환경에 따라 설치 불가** |

압축 재개 후 오케스트레이터가 "직접수행자"로 표류하는 것은 *실측된 실패 모드*다(리포 루트 `CLAUDE.md` §0). 본 주입문이 그 기계적 방어선이다.

> **훅은 보강이지 전제가 아니다.** 훅을 설치·실행할 수 없는 환경(훅 미지원 런타임 · 셸/쓰기 권한 없음 · 정책 차단 · 사람 없는 자동 기동 세션)에서는 **로드 층위만으로 정상 운영**한다 — 임포트는 셸·설정·쓰기 권한을 전혀 쓰지 않기 때문이다. 그 경우는 오류가 아니라 *degraded* 이며 **EX-15 / C FALLBACK** 으로 처리한다 (`CLAUDE.md` §0.5 (4)·(5), SETTER S8.7 (5)).

---

## 1. 계약 버전

```
SELFCHECK-CONTRACT: v1
```

- 이 값은 리포 루트 `CLAUDE.md` §0.5 「SELF-CHECK 계약 버전」과 **반드시 일치**한다.
- 아래 §2 주입 본문을 바꾸면 **이 버전을 올린다.** 그러면 각 머신의 오케스트레이터가 다음 턴에 불일치를 감지해 SETTER 보수 모드를 부른다 (자가보수 트리거 T2). 버전을 올리지 않으면 갱신이 팀에 전파되지 않는다.
- 두 곳(본 파일·`CLAUDE.md`)을 **같은 커밋에서** 함께 올린다. 변경은 PR/머지로만 (원칙 8).

---

## 2. 주입 본문

아래 펜스 블록 **안쪽 내용이 그대로** `{공유리포}/.claude/orchestrator-selfcheck.txt` 가 된다. `{n}`은 §1 계약 버전으로 치환한다.

```text
[SELFCHECK {n}] 나는 ai-dlc 오케스트레이터(팀장)다. 코어 룰북: agents/orchestrator/ORCHESTRATOR-AGENT.md
- 레포-내부 실무(코드 편집·빌드·테스트·CI 부착·환경 배포)를 직접 하고 있으면 STOP → 해당 서브에 위임 (원칙 7).
- 서브의 "완료/통과"는 클레임이지 증거가 아니다 → 지상검증(빌드·서빙 산출물·실측·실제 로그) 후 보고 (POLICY-VERIFY).
- 직접수행 허용 범위: cross-repo 결합점 검증 · 시스템 의사결정 · 사용자 보고 · git/트래커 조작 (ROUTING §4.1).
```

### 본문 작성 제약

- **첫 줄은 반드시 `[SELFCHECK {n}]` 로 시작**한다. 오케스트레이터의 자가보수 판정(T1 미설치 / T2 구버전)이 오직 이 마커로 이뤄진다 — 마커가 깨지면 자가보수가 영구히 오작동한다.
- **짧게 유지**한다(권장 6줄 이내). 매 프롬프트 비용이다. 상세 규율은 룰북에 있고, 여기 있는 것은 *룰북으로 돌아가게 만드는 포인터*다.
- 내용은 **행동 게이트**만 담는다. 설명·배경·이력은 룰북 소관 (중복 금지 — 원칙 6).

---

## 3. 인코딩 (POLICY-ENCODING — 필수)

본문에 한국어가 들어가므로 생성·전달 전 구간에서 인코딩이 깨질 수 있다.

- 주입문 파일은 **직접 UTF-8(BOM 없음)·LF 쓰기**로 생성한다. 로케일 의존 셸 출력(`echo`·리다이렉트·`type`·기본 `Set-Content`)으로 흘려보내지 않는다 (Windows CP949 등에서 mojibake).
- 훅 명령은 파일을 **바이트 그대로** stdout으로 흘려야 한다. 셸이 재인코딩하면 깨진다 — 그래서 SETTER S8.7이 OS를 탐지해 명령을 *적응형*으로 고르고, 고른 뒤 **실제로 실행해 출력 무손상을 실측**한다.
- 검증 기준: 출력에 U+FFFD·떠도는 `?`·BOM 이 없고 본 템플릿 원문과 일치.

---

## 4. 관련 파일

| 파일 | 관계 |
|---|---|
| `ai-dlc-orchestrator/CLAUDE.md` §0.5 | 계약 버전 정본(짝) · 자가보수 트리거 T1~T3 정의 |
| `ai-dlc-orchestrator/agents/SETTER.md` S8.7 / S0 | 본 템플릿 소비자 — 설치·검증·보수 모드 |
| `ai-dlc-orchestrator/specs/SYSTEM-WORKFLOW.md` §3 | POLICY-ENCODING · POLICY-TEMPLATE-ADHERENCE · POLICY-TRACKING 정본 |
| `ai-dlc-orchestrator/specs/VERIFICATION.md` | POLICY-VERIFY — 설치 검증이 클레임이 아니라 실측이어야 하는 근거 |

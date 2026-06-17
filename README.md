# ix-ai-dlc

> **자연어 지시 하나로, 여러 레포에 걸친 AI 주도 개발을 조율하는 깃 관리형 공유 룰북.**
>
> *An adaptive, project-agnostic multi-agent orchestration framework — drive multi-repo AI development with a single natural-language instruction.*

ix-ai-dlc는 **특정 프로젝트·스택·OS에 묶이지 않는 범용 멀티 에이전트 오케스트레이션 프레임워크**다. 프레임워크의 모든 규칙은 깃 리포 안의 마크다운 파일로, 버전 관리되고 PR로 진화한다. 직접 코딩하는 도구가 아니라, 레포별 AI 워크플로우를 **지휘하는 상위 레이어**다.

> 더 자세한 소개·배경·멘탈 모델은 **[ix-ai-dlc-overview.md](ix-ai-dlc-overview.md)** 를 참고. 이 README는 그 문서를 *대체하지 않고 보완*하며, 깊이가 필요한 곳마다 링크한다.

---

## 목적 / 무엇을 할 수 있나

**문제.** AI 코딩 도구는 대개 *레포 하나* 안에서만 잘 동작한다. 그런데 실제 제품은 프론트·백엔드·인프라 등 *여러 레포*에 걸쳐 있고, 그 사이의 인터페이스·의존 관계·통합·일관성은 사람이 직접 챙겨야 한다. "이 기능 만들어줘"라고 하면 한 레포는 잘 만들어도, 레포 경계를 넘는 조율은 빠진다.

**해법.** ix-ai-dlc는 그 *시스템 레벨 조율*을 담당한다. 사용자는 자연어로 한 번 지시하고, 시스템이 한 사이클로 끌고 간다:

- **분해** — 어느 레포들이 연관되는지, 의존 그래프는 어떤지 매핑한다.
- **cross-repo 설계** — 레포 사이의 계약(인터페이스·결합점·데이터 흐름)을 설계한다.
- **in-repo 구현 위탁** — 각 레포의 실제 구현(요구사항→설계→코드→테스트→빌드)은 검증된 오픈소스 AWS AI-DLC에 위탁한다.
- **통합·테스트·커밋** — 결과를 통합하고, 시스템 테스트·빌드 후, 다중 레포 커밋까지 조율한다.
- **CI/CD 부착·릴리스** — 레포별 CI/CD를 적응적으로 부착·통합(기존 탐지·분석 / 신규 생성)하고, 시스템 필수 게이트를 얹어 릴리스까지 잇는다.
- **적응형 환경 배포** — 검증된 릴리스를 환경에 배포한다. non-prod는 자율, prod는 사람 게이트, 배포 후 지상검증·자동 롤백. *설계→배포* end-to-end (조건부).
- **사이클 로그·진화** — 작업을 기록하고, 사용 패턴을 학습해 룰북 개선을 능동 제안한다.

---

## 핵심 이점

- **멀티 레포 조율 자동화** — 레포 분해부터 통합·커밋, 나아가 CI/CD 부착·릴리스·환경 배포까지 *설계→배포 end-to-end*. 사람은 핵심 결정만 승인한다.
- **레포 내부 구현 위임** — 오픈소스 [AWS AI-DLC (`awslabs/aidlc-workflows`)](https://github.com/awslabs/aidlc-workflows)에 위탁한다. **MIT-0 라이선스 → AWS 계정 불필요, 비용 0.**
- **모든 룰이 버전 관리되는 마크다운** — 블랙박스가 아니다. 깃으로 추적되고 PR로 투명하게 진화한다.
- **선택적 휴먼 게이트(HITL)** — 모든 단계 승인이 아니라 *위험·비가역·큰 영향* 지점만 골라 확인한다. 나머지는 AI가 자율 진행한다.

---

## 아키텍처 (2-레벨 + 팀 비유)

```
        사용자 (고객)
           │  자연어 지시 한 번
           ▼
   오케스트레이터 (팀장)          ← ix-ai-dlc · 시스템 레벨 · STEP 0~10
           │  분해 · 설계 후 레포별 위탁
   ┌───────┼───────┐
   ▼       ▼       ▼
 레포 A   레포 B   레포 C         ← 각 레포 안의 구현은
 [AWS]    [AWS]    [AWS]            AWS AI-DLC (팀원)가 수행
```

| 역할 | 대응 | 담당 |
|---|---|---|
| 사용자 | 고객 | 자연어 지시 + 핵심 결정 승인 |
| **오케스트레이터** | **팀장** | 시스템 레벨 조율 (STEP 0~10). 사용자는 *팀장하고만* 대화 |
| 서브 에이전트 / 레포별 AWS | 팀원 | 팀장을 통해서만 움직임 |

사용자는 창구 하나(팀장)만 상대하면 된다. 나머지 협업은 내부에서 처리된다. 구조에 대한 깊이 있는 설명은 **[overview §2](ix-ai-dlc-overview.md#2-핵심-아이디어-구조)** 참고.

---

## 빠른 시작 (Quickstart)

> OS 무관 (macOS / Linux / Windows). 에이전트 런타임(예: Claude Code) + git이 필요하다.

1. **클론**
   ```sh
   git clone <ix-ai-dlc-repo-url>
   cd ix-ai-dlc
   ```

2. **에이전트로 열기** — 이 리포를 에이전트 런타임(예: Claude Code)에서 연다. 루트의 **[`CLAUDE.md`](CLAUDE.md)** 가 세션 시작 시 자동으로 읽혀 오케스트레이터(팀장) 정체성을 부트스트랩한다. 갓 클론한 리포도 이 파일 하나로 자력 시작한다.

3. **첫 실행 (1회 부트스트랩)** — 시스템 인스턴스가 아직 없으면 오케스트레이터가 **`SETTER`** 를 먼저 호출한다. SETTER가 인터뷰로 프로젝트를 파악하고(어떤 레포·역할·스택·컨벤션·응답 언어), 레포마다 **`REPO-SETTER`** 가 AWS 룰셋 + 필요한 Extension을 설치한다. 결과로 **프로젝트에 특화된, 깃 추적되는 규칙 파일들**이 생성된다.

4. **일상 사용** — 오케스트레이터에게 **자연어로 지시**하면, 인텐트 유형을 자동 분류해 그에 맞는 STEP 경로를 실행한다.

   > 예: *"결제 모듈에 쿠폰 기능 추가해줘"* → 영향 레포 분해(결제·주문·프론트) → cross-repo API 계약 설계(사용자 한 번 확인) → 각 레포 AWS 위탁 → 통합·테스트 → 다중 레포 커밋. **사용자는 설계를 한 번 확인하고 결과를 받는다.**

인텐트 유형 예: *새 기능 개발*(STEP 0~10 풀 사이클), *변경·수정*(STEP 1~9), *분석·조사*(STEP 1~2, 코드 변경 없이 보고), 그 외 *추가 레포 / 사이클 종료 / 시스템 부트스트랩 / 진화·메타*.

---

## 리포 구조

모든 것이 마크다운 룰 파일이다. 전체 분해는 **[overview §3](ix-ai-dlc-overview.md#3-무엇을-만들고-있나-구성물)** 참고.

- **[`agents/`](agents/) — 행위 주체(에이전트) 룰북**
  - [`orchestrator/`](agents/orchestrator/) — 팀장. 코어 [`ORCHESTRATOR-AGENT.md`](agents/orchestrator/ORCHESTRATOR-AGENT.md) + 디테일 4개(`ROUTING` · `DECISIONS` · `ERROR-POLICY` · `TERMINATION`)
  - [`SETTER.md`](agents/SETTER.md) — 시스템 최초 부트스트랩 (신규 생성 또는 기존 공유 원격 합류)
  - [`REPO-SETTER.md`](agents/REPO-SETTER.md) — 각 레포에 AWS 룰셋 + Extension 설치
  - [`REPO-CREATOR.md`](agents/REPO-CREATOR.md) — 새 레포 생성
  - [`CICD-SETTER.md`](agents/CICD-SETTER.md) — 레포별 CI/CD 부착·통합 (기존 탐지 / 신규 생성, 조건부)
  - [`DEPLOY-AGENT.md`](agents/DEPLOY-AGENT.md) — 적응형 환경 배포 (non-prod 자율 / prod 사람 게이트, 조건부)
  - [`CYCLE-CLOSER.md`](agents/CYCLE-CLOSER.md) — 사이클 종료 후처리 (기록 최종화·보고)
  - [`HANDOFF-WRITER.md`](agents/HANDOFF-WRITER.md) — 세션 이관 문서 자동 작성

- **[`specs/`](specs/) — 형식·룰 명세 (에이전트 아님)**
  - [`SYSTEM-WORKFLOW.md`](specs/SYSTEM-WORKFLOW.md) — STEP 0~10 워크플로우 + **공통 정책(§3.1)**
  - [`AWS-ADAPTER.md`](specs/AWS-ADAPTER.md) — AWS AI-DLC 연동 인터페이스 (STEP↔AWS 매핑·버전 핀·산출물 흡수)
  - [`CYCLE-LOG.md`](specs/CYCLE-LOG.md) — 작업 기록(audit) 표준
  - [`EVOLUTION.md`](specs/EVOLUTION.md) — 사용 패턴 감지 → 룰북 갱신 능동 제안 (DP-9)
  - [`VERIFICATION.md`](specs/VERIFICATION.md) — 검증·지상검증 규율 (**POLICY-VERIFY**)
  - [`CICD-RELEASE-ADAPTER.md`](specs/CICD-RELEASE-ADAPTER.md) — CI/CD·릴리스 머신 통합 (**POLICY-RELEASE**, 조건부)
  - [`DEPLOY-ADAPTER.md`](specs/DEPLOY-ADAPTER.md) — 환경 배포 룰: 환경 모델·전략·prod 사람 게이트·health·롤백 (**POLICY-DEPLOY**, 조건부)

- **[`templates/`](templates/) — 채워서 인스턴스를 찍어내는 원본**
  - 시스템·핸드오프: `ORCHESTRATOR` · `REPO-MAP` · `HANDOFF` · `RETROSPECTIVE`
  - 레포 템플릿 7종: `CLAUDE` · `STACK` · `WORKFLOW` · `DESIGN` · `CHECKLIST` · `CODING` · `FRAMEWORK`
  - [`extensions/`](templates/extensions/) — 레포에 선택 적용하는 AWS Extension: `quality`(체크리스트) · `coding`(코딩 규칙) · `framework`(프레임워크 패턴)

> **공통 정책의 정본**은 [`SYSTEM-WORKFLOW.md §3.1`](specs/SYSTEM-WORKFLOW.md) — `POLICY-ENCODING` · `POLICY-TEMPLATE-ADHERENCE` · `POLICY-TRACKING`. 횡단 규율 `POLICY-VERIFY`는 [`VERIFICATION.md`](specs/VERIFICATION.md), `POLICY-RELEASE`는 [`CICD-RELEASE-ADAPTER.md`](specs/CICD-RELEASE-ADAPTER.md), `POLICY-DEPLOY`는 [`DEPLOY-ADAPTER.md`](specs/DEPLOY-ADAPTER.md)에 둔다. 전 에이전트가 같은 라벨 체계로 이를 참조한다.

---

## 핵심 원칙 (요약)

- **git fetch/pull 선행 (team-safe)** — 모든 git 작업 전에 원격 최신을 반영하고 기본 브랜치 기준으로 분기한다. 팀 개발 전제 — stale base 위 작업은 충돌·커밋 유실을 부른다.
- **지상검증 (claim ≠ evidence)** — "성공/완료/통과"는 클레임이지 증거가 아니다. 보고·진행 전에 가장 낮은 수준의 관찰 가능한 실제로 확인한다. 위험·비가역일수록 독립 검증자가 본다.
- **자격증명 경계** — 시크릿은 `.env*`에서 읽기만. 추적 파일에 값 커밋 금지. 토큰 발급·접근제어 변경은 사람이 한다.
- **선택적 휴먼 게이트(HITL)** — 위험·큰 영향·비가역·추가 레포·진화 제안 지점만 컨펌. 나머지는 AI 자율.
- **AWS 위임** — 레포 내부 구현은 직접 하지 않고 AWS AI-DLC에 위탁한다. 우리는 경계·계약·통합만 직접 담당한다.

---

## 상태 / 호환성

| 단계 | 내용 | 상태 |
|---|---|---|
| Stage 1 | 단일 레포용 템플릿 7종 | ✓ 완료 |
| Stage 2 | 시스템 부트스트랩 + 오케스트레이터 + AWS 통합 | ✓ 완료 |
| Stage 3 | EVOLUTION — 사용 패턴 학습 → 룰북 진화 제안 | ✓ 완료 |
| Stage 4 | 협업 거버넌스 — 공유 원격 · 자격증명 경계 · 산출물 추적 | ✓ 완료 |

> **현재:** 외부 공유 퍼블리시를 위한 **범용화·하드닝** — 공통 정책(POLICY-*) 도입, 검증 프로토콜·CI/릴리스·디자인 어댑터 보강. 라이프사이클이 이제 **환경 배포(검증·롤백)** 까지 포함해 *설계→배포* end-to-end로 닫힌다.

- **OS-agnostic** — macOS / Linux / Windows. [`.gitattributes`](.gitattributes)가 EOL을 LF로 정규화한다.
- **요구사항** — 에이전트 런타임(예: Claude Code) + git. AWS AI-DLC 룰셋은 부트스트랩 시 레포마다 가져온다(per-repo).
- 특정 도구(Claude Code · GitLab · Figma 등)는 어디까지나 *예시(e.g.)* 다. 프레임워크 자체는 동치 수단으로 대체 가능하도록 설계됐다.

---

## 더 보기

- **[ix-ai-dlc-overview.md](ix-ai-dlc-overview.md)** — 더 깊은 소개·배경·멘탈 모델
- **[CLAUDE.md](CLAUDE.md)** — 세션 진입점(부트스트랩) · 퀵스타트가 가리키는 곳
- **[specs/SYSTEM-WORKFLOW.md](specs/SYSTEM-WORKFLOW.md)** — STEP 0~10 + 공통 정책 정본
- **[agents/orchestrator/ORCHESTRATOR-AGENT.md](agents/orchestrator/ORCHESTRATOR-AGENT.md)** — 오케스트레이터 코어 룰북

### 라이선스 노트

이 프레임워크의 룰·템플릿은 당신의 것이다 — 클론 후 PR로 자유롭게 진화시킨다. 레포 내부 구현을 담당하는 [AWS AI-DLC (`awslabs/aidlc-workflows`)](https://github.com/awslabs/aidlc-workflows)는 별도 프로젝트이며 **MIT-0** 라이선스로 배포된다(AWS 계정·비용 불필요).

# CHECKLIST.md — 코드 생성 전 자가 검증

> AWS AI-DLC Extension — `quality/checklist`. 각 레포 Construction(Code Generation) 진입 전 자가 검증 게이트.
> 적용·검증·버전 정합은 REPO-SETTER RP6 + AWS-ADAPTER §4가 담당 (본 파일은 중복 명세 안 함 — 원칙 6).
> 위치(공유 룰북): `ai-dlc-orchestrator/templates/extensions/quality/checklist.template.md`

| 메타 | 값 |
|---|---|
| 카테고리 / 이름 | quality / checklist |
| 변종 | 없음 (단일) |
| 활성화 | **default-on** — 원본 STEP 4 "반드시 자가 검증" 정합. 끄려면 레포에서 명시적 비활성 |
| 채움 변수 | `{CHECKLIST_RULES}` (레포별 채움 — REPO-SETTER 또는 프로젝트 제공) |
| 적용 시스템 STEP | STEP 4 (코드 생성 사전 게이트) |
| 적용 AWS phase·stage | Construction / Code Generation (pre-check) |
| 인스턴스 경로 | `{레포}/aidlc-rules/aws-aidlc-rule-details/extensions/quality/checklist.md` |
| 원천 | Stage 1 `CHECKLIST.template.md` (D-Stage2-18) |

---

> 코드를 생성하기 전에 아래 항목을 반드시 자가 검증할 것.
> 하나라도 위반하면 생성 중단 후 수정.

---

{CHECKLIST_RULES}

---

## 자가 검증 통과 기준

위 항목 중 하나라도 ❌이면 코드 생성을 중단하고 수정한 뒤 재검증한다.
전체 통과 후에만 코드를 생성한다.

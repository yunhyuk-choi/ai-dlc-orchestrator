# FRAMEWORK.md — 프레임워크 필수 패턴

> AWS AI-DLC Extension — `framework/{name}`. 각 레포 Construction(Code Generation) 시점 프레임워크 패턴.
> 적용·검증·버전 정합은 REPO-SETTER RP6 + AWS-ADAPTER §4가 담당 (본 파일은 중복 명세 안 함 — 원칙 6).
> 위치(공유 룰북): `ai-dlc-orchestrator/templates/extensions/framework/framework.template.md`

| 메타 | 값 |
|---|---|
| 카테고리 / 이름 | framework / framework |
| 변종 | **프레임워크별** `{name}` (예: react, django, spring) — RP2.4 STACK_SUMMARY로 결정·materialize |
| 활성화 | **opt-in** (프레임워크 미사용 레포는 미선택) |
| 채움 변수 | `{FRAMEWORK_PATTERNS}` (프레임워크별) / `{name}` (STACK_SUMMARY 추출) |
| 적용 시스템 STEP | STEP 4 (코드 생성 시점 — **STEP 8 아님**) |
| 적용 AWS phase·stage | Construction / Code Generation |
| 인스턴스 경로 | `{레포}/aidlc-rules/aws-aidlc-rule-details/extensions/framework/{name}/framework.md` |
| 원천 | Stage 1 `FRAMEWORK.template.md` (D-Stage2-18) |

> **변종 materialize**: 공유 룰북은 제너릭 템플릿 1개. 적용 시 RP6이 `{name}` 결정 후 `{name}/framework.md`로 `{FRAMEWORK_PATTERNS}` 채워 복사. (프레임워크별 사전 작성은 Stage 3 EVOLUTION 큐)

---

{FRAMEWORK_PATTERNS}

# CODING.md — 코딩 규칙

> AWS AI-DLC Extension — `coding/{lang}`. 각 레포 Construction(Code Generation) 시점 코딩 규칙.
> 적용·검증·버전 정합은 REPO-SETTER RP6 + AWS-ADAPTER §4가 담당 (본 파일은 중복 명세 안 함 — 원칙 6).
> 위치(공유 룰북): `ix-ai-dlc/templates/extensions/coding/coding.template.md`

| 메타 | 값 |
|---|---|
| 카테고리 / 이름 | coding / coding |
| 변종 | **언어별** `{lang}` (예: ts, python, go) — RP2.4 STACK_SUMMARY로 결정·materialize |
| 활성화 | **opt-in** |
| 채움 변수 | `{CODING_RULES}` (언어별 채움) / `{lang}` (STACK_SUMMARY 추출) |
| 적용 시스템 STEP | STEP 4 (코드 생성 시점) |
| 적용 AWS phase·stage | Construction / Code Generation |
| 인스턴스 경로 | `{레포}/aidlc-rules/aws-aidlc-rule-details/extensions/coding/{lang}/coding.md` |
| 원천 | Stage 1 `CODING.template.md` (D-Stage2-18) |

> **변종 materialize**: 공유 룰북은 제너릭 템플릿 1개. 적용 시 RP6이 `{lang}` 결정 후 `{lang}/coding.md`로 `{CODING_RULES}` 채워 복사. (언어별 사전 작성 pre-bake는 Stage 3 EVOLUTION 큐)

---

{CODING_RULES}

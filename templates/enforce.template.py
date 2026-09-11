#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""enforce.template.py — 범용 불변식(invariant) 강제 엔진 (템플릿)

이 파일은 인스턴스 산출물의 템플릿이다 (POLICY-TEMPLATE-ADHERENCE). SETTER가 STEP 2에서
이 엔진을 훅에 배선하고, 두 선언 파일(invariants.team.yaml / invariants.personal.yaml)의
실제 경로를 바인딩한다. 본 파일 자체는 프레임워크 레포에 그대로 산다 — 100% 중립.

설계 원칙
  - 중립(agnostic): 특정 트래커·프로젝트·회사·스택을 무참조. 읽는 것은 *로컬 로그 계층뿐*
    (cycles/*/audit.md 의 CYCLE-START/CYCLE-END 스캔). 네트워크·트래커·프로젝트 상수 없음.
  - degraded-safe: 선언 파일이 없거나·깨졌거나·PyYAML이 없거나·stdin이 비었거나 무엇이 어긋나도
    *절대 크래시하지 않는다* — 아무것도 출력하지 않고 exit 0 (훅은 보강이지 전제가 아니다 — EX-15 / C FALLBACK).
  - 얇은 적응형 훅 → 범용 엔진 → 2개 선언 원천. 관심사 분리 + personal-adjust 키.

YAML 파싱 결정 (요구됨)
  - PyYAML이 있으면 사용한다. *없어도* 동작한다 — 본 파일은 선언 템플릿이 쓰는 제한된 블록 서브셋을
    파싱하는 stdlib-only 미니 파서를 내장한다. 어느 경로든 파싱 실패 시 → 해당 파일을 None으로 보고
    조용히 건너뛴다(degraded no-op). 즉 *PyYAML은 의존이 아니다*.

경로 바인딩 (STEP 2에서 SETTER가 확정)
  - AIDLC_INVARIANTS_DIR : invariants.team.yaml / invariants.personal.yaml 이 있는 디렉토리
                           (기본값: 이 스크립트가 놓인 디렉토리)
  - AIDLC_LOG_DIR        : cycles/ 로컬 로그 계층을 담은 디렉토리 = 메타 레포 루트
                           (기본값: 현재 작업 디렉토리)
  STEP 2에서 SETTER는 훅 command에 이 env를 실어 실제 절대 경로를 바인딩한다.

호출 규약
  enforce.py --event {PostToolUse|Stop}   # 훅 JSON을 stdin으로 받음 (tool_name, tool_input, ...)

훅 JSON 계약 (Claude Code hook contract — 확정. 출처: code.claude.com/docs/en/hooks.md,
  v2.1.2xx, 2026-09-11 fetch)
  아래 emit() 의 매핑이 계약이다. block/warn/advisory tier가 각각 어떤 JSON 형태로 나가는지 명시.
  block 은 exit code 2 를 신뢰 가능한 차단 채널로 쓰고(§7 참조), Stop 재진입 시
  stop_hook_active 로 무한루프를 가드한다.
"""

import fnmatch
import json
import os
import sys

# ---------------------------------------------------------------------------
# stdout UTF-8 강제 (시작 시) — degraded-safe 계약의 일부.
#   방출 메시지엔 한국어·em-dash(U+2014)가 들어간다. Windows 기본 stdout 인코딩은
#   cp949라, 그대로 쓰면 `UnicodeEncodeError: 'cp949' codec can't encode '—'`로
#   엔진이 *자기 출력으로* 크래시한다(실측). 엔진은 절대 크래시하지 않아야 하므로
#   시작 시 stdout을 UTF-8로 재구성한다. reconfigure가 없는 런타임(3.6 이하)이면
#   조용히 넘기고, 실제 쓰기는 _emit_write()가 버퍼 바이트 경로로 다시 보강한다.
# ---------------------------------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8")  # Py3.7+
except Exception:
    pass

# stdin도 UTF-8로 강제한다 — 훅 하네스는 UTF-8 JSON을 흘리는데, cp949 호스트의
# 기본 stdin은 cp949라 tool_input 등에 비-ASCII가 있으면 디코드가 어긋난다.
# POSIX는 이미 UTF-8이라 무해한 no-op이다 (크로스플랫폼 무회귀).
try:
    sys.stdin.reconfigure(encoding="utf-8")  # Py3.7+
except Exception:
    pass

# ---------------------------------------------------------------------------
# tier 순서 (advisory < warn < block)
# ---------------------------------------------------------------------------
_TIER_ORDER = {"advisory": 0, "warn": 1, "block": 2}


# ===========================================================================
# 1. YAML 로드 — PyYAML 우선, 없으면 stdlib 미니 파서. 실패 = None (degraded)
# ===========================================================================
def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _strip_comment(line):
    """따옴표 밖의 첫 '#' 이후를 주석으로 제거."""
    out = []
    quote = None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        else:
            if ch in ('"', "'"):
                quote = ch
                out.append(ch)
            elif ch == "#":
                break
            else:
                out.append(ch)
    return "".join(out).rstrip()


def _tokenize(text):
    """(indent, stripped_content) 목록. 빈 줄·주석 제거."""
    toks = []
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        toks.append((indent, line.strip()))
    return toks


def _split_flow(inner):
    """플로우 리스트 내부를 따옴표를 존중하며 콤마로 분할."""
    parts = []
    buf = []
    quote = None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf).strip())
    return parts


def _parse_scalar(s):
    s = s.strip()
    if s == "":
        return None
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(x) for x in _split_flow(inner)]
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        return s


def _kv_split(s):
    """'key: value' 이면 (key, value) 반환. 아니면 None. 콜론은 따옴표 밖 + 뒤가 공백/끝일 때만."""
    quote = None
    for idx, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == ":" and (idx + 1 == len(s) or s[idx + 1] in " \t"):
            return s[:idx].strip(), s[idx + 1:].strip()
    return None


def _group(block, i, parent_indent):
    """block[i:] 중 indent > parent_indent 인 연속 토큰과 다음 인덱스 반환."""
    child = []
    while i < len(block) and block[i][0] > parent_indent:
        child.append(block[i])
        i += 1
    return child, i


def _parse_block(block):
    if not block:
        return None
    if block[0][1].startswith("- "):
        return _parse_seq(block)
    return _parse_map(block)


def _parse_seq(block):
    base = block[0][0]
    seq = []
    i = 0
    while i < len(block):
        ind, content = block[i]
        if ind != base or not content.startswith("- "):
            break
        rest = content[2:].strip()
        child, j = _group(block, i + 1, base)
        if rest == "":
            seq.append(_parse_block(child))
        elif _kv_split(rest) is not None:
            # 대시 인라인 매핑: rest를 base+2 인덱스의 맵 첫 줄로 취급하고 자식을 이어붙임
            item_block = [(base + 2, rest)] + child
            seq.append(_parse_map(item_block))
        else:
            seq.append(_parse_scalar(rest))
        i = j
    return seq


def _parse_map(block):
    base = block[0][0]
    d = {}
    i = 0
    while i < len(block):
        ind, content = block[i]
        if ind != base:
            # 예상 밖 들여쓰기 — 안전하게 스킵
            i += 1
            continue
        kv = _kv_split(content)
        if kv is None:
            i += 1
            continue
        key, val = kv
        child, j = _group(block, i + 1, ind)
        if val == "":
            d[key] = _parse_block(child) if child else None
        else:
            d[key] = _parse_scalar(val)
        i = j
    return d


def _mini_yaml(text):
    return _parse_block(_tokenize(text))


def _parse_yaml(text):
    """PyYAML 우선, 없으면 미니 파서. 실패 시 None."""
    if text is None:
        return None
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        pass
    except Exception:
        return None
    try:
        return _mini_yaml(text)
    except Exception:
        return None


def _load_yaml_file(path):
    if not os.path.isfile(path):
        return None
    return _parse_yaml(_read_text(path))


def _inv_list(doc):
    if isinstance(doc, dict):
        got = doc.get("invariants")
        if isinstance(got, list):
            return [x for x in got if isinstance(x, dict)]
    return []


# ===========================================================================
# 2. 병합 — 팀이 floor, personal-adjust 강제
# ===========================================================================
def _replace(result, inv_id, new_inv):
    for idx, inv in enumerate(result):
        if inv.get("id") == inv_id:
            result[idx] = new_inv
            return


def merge(team, personal):
    """team(정수) + personal(재조정)을 id로 병합. 규칙은 invariants.template.yaml 참조."""
    by_id = {}
    result = []
    for inv in team:
        i = dict(inv)
        by_id[i.get("id")] = i
        result.append(i)
    for p in personal:
        pid = p.get("id")
        if pid not in by_id:
            # 개인 전용 새 id = 자유
            np = dict(p)
            result.append(np)
            by_id[pid] = np
            continue
        base = by_id[pid]
        adjust = base.get("personal-adjust", "locked")
        if adjust == "locked":
            continue
        if adjust == "full":
            merged = dict(p)
            merged["id"] = pid
            _replace(result, pid, merged)
            by_id[pid] = merged
            continue
        if adjust == "escalate-only":
            bt = _TIER_ORDER.get(base.get("tier"), 0)
            pt = _TIER_ORDER.get(p.get("tier"), 0)
            if pt > bt:
                base["tier"] = p.get("tier")
    return result


def load_invariants(base_dir):
    team = _inv_list(_load_yaml_file(os.path.join(base_dir, "invariants.team.yaml")))
    personal = _inv_list(_load_yaml_file(os.path.join(base_dir, "invariants.personal.yaml")))
    return merge(team, personal)


# ===========================================================================
# 3. 로컬 로그 계층 판독 (유일하게 허용된 지상검증 원천 — 중립)
# ===========================================================================
def _iter_audit_files(log_dir):
    cycles = os.path.join(log_dir, "cycles")
    if not os.path.isdir(cycles):
        return []
    out = []
    try:
        for name in sorted(os.listdir(cycles)):
            p = os.path.join(cycles, name, "audit.md")
            if os.path.isfile(p):
                out.append(p)
    except Exception:
        return []
    return out


def _cycle_is_open(text):
    """CYCLE-START/END/REOPEN 순차 스캔 상태머신. 마지막 상태가 열림이면 True.
    (CYCLE-LOG.md §10.3 재오픈 정합 — REOPEN은 다시 열림으로 취급)."""
    open_ = False
    for line in text.splitlines():
        if "CYCLE-START" in line:
            open_ = True
        elif "CYCLE-REOPEN" in line:
            open_ = True
        elif "CYCLE-END" in line:
            open_ = False
    return open_


def _open_cycles(log_dir):
    opens = []
    for p in _iter_audit_files(log_dir):
        txt = _read_text(p)
        if txt is not None and _cycle_is_open(txt):
            opens.append(p)
    return opens


# ===========================================================================
# 4. 명명된 체크 — (violation_bool, detail_str) 반환
# ===========================================================================
def check_open_cycle_record_exists(log_dir):
    """사이클 액션이 있었는데 열린 사이클 기록이 하나도 없으면 위반."""
    if _open_cycles(log_dir):
        return (False, "")
    return (True, "사이클 액션 감지 — 열린 cycles/*/audit.md 기록(CYCLE-START)이 없습니다. "
                   "사이클을 시작했으면 audit.md에 CYCLE-START를 append하세요 (specs/CYCLE-LOG.md).")


def check_no_stale_open_cycle(log_dir):
    """열린 사이클 기록이 턴 경계를 넘겨 잔존하면 위반(가시화)."""
    opens = _open_cycles(log_dir)
    if not opens:
        return (False, "")
    names = ", ".join(os.path.basename(os.path.dirname(p)) for p in opens)
    return (True, "턴 경계에 열린 사이클이 잔존합니다: " + names +
                  " — 마무리됐으면 CYCLE-END를, 계속이면 그대로 두세요 (specs/CYCLE-LOG.md).")


CHECKS = {
    "open-cycle-record-exists": check_open_cycle_record_exists,
    "no-stale-open-cycle": check_no_stale_open_cycle,
}


# ===========================================================================
# 5. 선결 조건 (requires) — 불충족이면 불변식 SKIP (중립 견고성)
# ===========================================================================
def _precondition_met(req, log_dir):
    if req == "local-log-layer":
        return os.path.isdir(os.path.join(log_dir, "cycles"))
    # 미지원 선결 조건(예: STEP 2 어댑터가 넣을 issue-tracker-config)은 불충족으로 간주 → SKIP
    return False


def _requires_met(inv, log_dir):
    reqs = inv.get("requires") or []
    if not isinstance(reqs, list):
        return False
    return all(_precondition_met(r, log_dir) for r in reqs)


# ===========================================================================
# 6. 평가
# ===========================================================================
def _bindings(inv):
    b = inv.get("bindings")
    if isinstance(b, list) and b:
        return [x for x in b if isinstance(x, dict)]
    # 단일 이벤트 평면형
    return [{"event": inv.get("event"), "check": inv.get("check"), "match": inv.get("match")}]


def _match_tool(globs, tool_name, tool_input):
    if not tool_name or not isinstance(globs, list):
        return False
    cands = [tool_name]
    if isinstance(tool_input, dict):
        for v in tool_input.values():
            if isinstance(v, str):
                cands.append("%s:%s" % (tool_name, v))
    for g in globs:
        for c in cands:
            if fnmatch.fnmatch(c, g):
                return True
    return False


def evaluate(event, tool_name, tool_input, invariants, log_dir):
    """위반된 (tier, message) 목록 반환."""
    findings = []
    for inv in invariants:
        if not _requires_met(inv, log_dir):
            continue
        for b in _bindings(inv):
            if b.get("event") != event:
                continue
            if event == "PostToolUse":
                if not _match_tool(b.get("match") or [], tool_name, tool_input):
                    continue
            fn = CHECKS.get(b.get("check"))
            if fn is None:
                continue
            try:
                violated, detail = fn(log_dir)
            except Exception:
                continue
            if violated:
                findings.append((inv.get("tier", "advisory"),
                                 "[invariant:%s] %s" % (inv.get("id", "?"), detail)))
    return findings


# ===========================================================================
# 7. 훅 JSON 계약 방출 (Claude Code hook contract — 확정. 출처: code.claude.com/
#    docs/en/hooks.md, v2.1.2xx, 2026-09-11 fetch)
# ---------------------------------------------------------------------------
#   tier=block    → {"decision": "block", "reason": <msg>}  +  exit code 2
#                    exit 2 가 신뢰 가능한 차단 채널이다 — exit 0 + decision:block 은
#                    advisory 에 그칠 수 있다(특히 PostToolUse 는 사후 실행이라 차단이
#                    자문에 그친다). 따라서 JSON 을 stdout 에 먼저 쓴 뒤 exit 2 로 나간다.
#                    block 은 Stop·PreToolUse 에서 실효적이다.
#   tier=warn     → Stop:        {"systemMessage": <msg>}
#                    PostToolUse: {"systemMessage": <msg>,
#                                  "hookSpecificOutput": {"hookEventName": "PostToolUse",
#                                                          "additionalContext": <msg>}}
#                    (warn 두 형태는 cp949 콘솔·PYTHONIOENCODING 없이 크래시 없이 방출됨이
#                     실측 확인됨 — INVARIANT-ENFORCEMENT §11.4.)
#   tier=advisory → 출력 없음 (no-op) + exit 0
#   여러 불변식이 동시에 걸리면 *최고 tier*로 집계한다.
#
#   Stop-block 무한루프 가드: Stop 훅이 block 을 내면 하네스가 그 stop 을 거부하고
#   다음 턴을 돌리는데, 그 턴 경계에서 훅이 또 block 을 내면 차단→재실행→재차단이
#   무한 반복된다. 하네스는 재진입한 Stop 훅 입력에 `stop_hook_active: true`를 실어
#   준다 — 그 경우 Stop 의 block 을 warn 으로 강등해 루프를 끊는다. (PostToolUse 는
#   턴을 재개시키지 않으므로 이 가드의 영향을 받지 않는다.)
# ===========================================================================
def emit(event, findings, stop_hook_active=False):
    """방출할 (JSON dict 또는 None, exit_code) 튜플을 반환한다.

    exit_code = 2 는 block tier 가 최종 발동했을 때(신뢰 가능한 차단 채널). 그 외 모두 0.
    stop_hook_active=True 로 재진입한 Stop 이벤트에서는 block 을 내지 않는다(루프 가드)."""
    if not findings:
        return (None, 0)
    top = max(_TIER_ORDER.get(t, 0) for t, _ in findings)
    text = "\n".join(m for _, m in findings)
    # Stop-block 무한루프 가드 — 재진입한 Stop 은 block 을 warn 으로 강등.
    if top >= _TIER_ORDER["block"] and event == "Stop" and stop_hook_active:
        top = _TIER_ORDER["warn"]
    if top >= _TIER_ORDER["block"]:
        return ({"decision": "block", "reason": text}, 2)
    if top == _TIER_ORDER["warn"]:
        out = {"systemMessage": text}
        if event == "PostToolUse":
            out["hookSpecificOutput"] = {
                "hookEventName": "PostToolUse",
                "additionalContext": text,
            }
        return (out, 0)
    return (None, 0)  # advisory → no-op


def _emit_write(out):
    """방출 JSON을 UTF-8로 견고하게 stdout에 쓴다 (degraded-safe).

    reconfigure(시작 시)가 먹혔으면 텍스트 경로로도 안전하지만, reconfigure가
    불가한 런타임을 대비해 *버퍼에 UTF-8 바이트를 직접* 쓰는 경로를 우선한다 —
    이 경로는 로케일(cp949 등)과 무관하게 절대 UnicodeEncodeError를 내지 않는다.
    버퍼가 없거나(재정의된 stdout 등) 실패하면 텍스트 경로로 폴백하되, 그마저
    실패해도 조용히 삼킨다 — 엔진은 자기 출력으로 크래시하지 않는다."""
    payload = json.dumps(out, ensure_ascii=False)
    try:
        buf = getattr(sys.stdout, "buffer", None)
        if buf is not None:
            buf.write(payload.encode("utf-8"))
            buf.flush()
            return
    except Exception:
        pass
    try:
        sys.stdout.write(payload)
    except Exception:
        pass


# ===========================================================================
# 8. 경로 해석 (STEP 2에서 SETTER가 env로 바인딩)
# ===========================================================================
def _base_dir():
    return os.environ.get("AIDLC_INVARIANTS_DIR") or os.path.dirname(os.path.abspath(__file__))


def _log_dir():
    return os.environ.get("AIDLC_LOG_DIR") or os.getcwd()


# ===========================================================================
# 9. CLI
# ===========================================================================
def _parse_event(argv):
    for i, a in enumerate(argv):
        if a == "--event" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--event="):
            return a.split("=", 1)[1]
    return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    event = _parse_event(argv)
    if event not in ("PostToolUse", "Stop"):
        return 0  # 알 수 없는 이벤트 → no-op (degraded-safe)
    # stdin의 훅 JSON 읽기 (없거나 깨져도 진행)
    raw = ""
    try:
        if not sys.stdin.isatty():
            raw = sys.stdin.read()
    except Exception:
        raw = ""
    data = {}
    # 선행 BOM(U+FEFF)을 제거한다 — 일부 셸·하네스가 UTF-8 BOM을 앞에 붙여 흘리면
    # json.loads가 실패한다. degraded-safe: 어긋나도 data={}로 조용히 진행.
    raw = raw.lstrip("\ufeff")
    if raw.strip():
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
    tool_name = data.get("tool_name") if isinstance(data, dict) else None
    tool_input = (data.get("tool_input") if isinstance(data, dict) else None) or {}
    # Stop-block 무한루프 가드용 신호 — 재진입한 Stop 훅이면 하네스가 true 로 실어 준다.
    # 깨지거나 없으면 False(=미재진입)로 안전 처리 (degraded-safe).
    stop_hook_active = bool(data.get("stop_hook_active")) if isinstance(data, dict) else False
    code = 0
    try:
        invs = load_invariants(_base_dir())
        findings = evaluate(event, tool_name, tool_input, invs, _log_dir())
        out, code = emit(event, findings, stop_hook_active)
    except Exception:
        out, code = None, 0  # 무엇이 어긋나도 조용히 통과 (EX-15 / C FALLBACK)
    if out is not None:
        _emit_write(out)  # JSON 을 먼저 쓴다 (block 이면 그 뒤 exit 2). reconfigure 불가 런타임도 버퍼 바이트로 안전
    return code


if __name__ == "__main__":
    sys.exit(main())

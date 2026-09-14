#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""enforce.template.py — 범용 불변식(invariant) 강제 엔진 (템플릿)

이 파일은 인스턴스 산출물의 템플릿이다 (POLICY-TEMPLATE-ADHERENCE). SETTER가 STEP 2에서
이 엔진을 훅에 배선하고, 두 선언 파일(invariants.team.yaml / invariants.personal.yaml)의
실제 경로를 바인딩한다. 본 파일 자체는 프레임워크 레포에 그대로 산다 — 100% 중립.

INVARIANTS-CONTRACT: v2
  (v1 → v2 — 키드(keyed) per-work-item 상태머신 체크 3종 추가로 *체크 id 집합*이 바뀌었다.
   specs/INVARIANT-ENFORCEMENT.md §13.6-8. 계약 값은 이 상수와 템플릿 헤더가 짝을 이룬다.)

설계 원칙
  - 중립(agnostic): 특정 트래커·프로젝트·회사·스택을 무참조. 읽는 것은 *로컬 파일 계층뿐*
    (cycles/*/audit.md 의 CYCLE-START/CYCLE-END 스캔 + 로컬 ephemeral state_dir 인덱스).
    네트워크·트래커·프로젝트 상수 없음. 표준 라이브러리(json·os·re·tempfile)만 쓴다.
  - degraded-safe: 선언 파일이 없거나·깨졌거나·PyYAML이 없거나·stdin이 비었거나·키가 없거나·
    state_dir가 없거나·레코드가 malformed거나 — 무엇이 어긋나도 CHECK 경로는 *절대 크래시하지
    않고* 아무것도 출력하지 않고 exit 0 (훅은 보강이지 전제가 아니다 — EX-15 / C FALLBACK).
  - 얇은 적응형 훅 → 범용 엔진 → 2개 선언 원천. 관심사 분리 + personal-adjust 키.

읽기/쓰기 경계 (§13.4 Q4=B — 확정)
  - CHECK 경로(훅이 부르는 --event 경로)는 *읽기 전용*이다 — 상태 파일을 읽어 위반만 판정한다.
  - 모든 *쓰기*(record / transition / close / set-active / reconcile)는 별도 **write-helper
    서브커맨드**로 격리된다. 이 서브커맨드가 (i) atomic temp+rename, (ii) 스키마 검증,
    (iii) 유효 전이 강제, (iv) 인덱스 포맷의 단일 원천을 담당한다. 디스패치한 오케스트레이터
    계층이 이 서브커맨드를 호출한다(오케스트레이터가 인덱스 포맷을 손으로 재현하지 않는다).

2층 상태 모델 (§13.3)
  - 내구 진실 = 사이클 로그 dlc-meta/cycles/*/audit.md (git 추적·append-only). 크로스-머신
    "일이 아직 열려 있나"의 단일 원천.
  - 에페메랄 인덱스 = <state_dir>/<key>.json (gitignore·per-deployment·언제든 휘발 가능).
    per-key 빠른 강제 인덱스. 세션/배포 시작 시 로그에서 REBUILD(reconcile)하므로 유실돼도 안전.

YAML 파싱 결정 (요구됨)
  - PyYAML이 있으면 사용한다. *없어도* 동작한다 — 본 파일은 선언 템플릿이 쓰는 제한된 블록 서브셋을
    파싱하는 stdlib-only 미니 파서를 내장한다. 어느 경로든 파싱 실패 시 → 해당 파일을 None으로 보고
    조용히 건너뛴다(degraded no-op). 즉 *PyYAML은 의존이 아니다*.

경로 바인딩 (STEP 2에서 SETTER가 확정) — CLI 인자 > env > 기본값
  두 선언 디렉토리는 §11.2.1 상 항상 같다(둘 다 dlc-meta 루트) — 그래서 --base-dir 하나로 준다.
  - --base-dir <abs>       : invariants.*.yaml 위치이자 cycles/ 로컬 로그 계층 루트 = dlc-meta.
                             --invariants-dir / --log-dir 로 개별 지정도 가능(있으면 --base-dir보다 우선).
  - --state-dir <abs>      : 키드 인덱스 디렉토리. 기본 <base-dir>/.aidlc-state (ephemeral·gitignore).
  - (하위호환 폴백) env AIDLC_INVARIANTS_DIR / AIDLC_LOG_DIR / AIDLC_STATE_DIR / AIDLC_WORK_KEY.
  - 기본값 : invariants dir = 이 스크립트가 놓인 디렉토리, log dir = 현재 작업 디렉토리.

  ⚠️ 경로를 *CLI 인자*로 받는 이유 — Claude Code 훅 command 객체엔 `env` 필드가 없다.
     공식 문서(code.claude.com/docs/en/hooks.md)상 인식되는 필드는 type·command·args·if·
     timeout·statusMessage·shell·async·asyncRewake 뿐이고 env 는 없다 — 훅은 부모 프로세스의
     env 를 상속할 뿐이다. 따라서 배포별 절대경로는 CLI 인자로 넘긴다: 셸 독립(cmd.exe/
     powershell 의 VAR=x 문법에 의존하지 않음)·래퍼 파일 불필요·기본 셸이 무엇이든 동작.

호출 규약
  # CHECK 경로 (훅이 stdin으로 훅 JSON을 흘린다 — 읽기 전용)
  enforce.py --event {PreToolUse|PostToolUse|Stop} --base-dir <abs> [--state-dir <abs>] [--work-key <k>]

  # write-helper 서브커맨드 (오케스트레이터/디스패처 계층이 호출 — 유일한 쓰기 진입점)
  enforce.py record     --work-key <k> [--status <s>] [--cycle-id <c>] [--delegation-id <d>]
                        [--verified true|false] [--state-dir <abs>|--base-dir <abs>]
  enforce.py transition --work-key <k> --status <s> [--verified true|false] [--state-dir|--base-dir]
  enforce.py close      --work-key <k> [--state-dir|--base-dir]
  enforce.py set-active --session-id <sid> --work-key <k> [--state-dir|--base-dir]
  enforce.py reconcile  [--base-dir <abs>|--log-dir <abs>] [--state-dir <abs>]

훅 JSON 계약 (Claude Code hook contract — 확정. 출처: code.claude.com/docs/en/hooks.md,
  v2.1.2xx, 2026-09-11 fetch)
  아래 emit() 의 매핑이 계약이다. block/warn/advisory tier가 각각 어떤 JSON 형태로 나가는지 명시.
  block 은 exit code 2 를 신뢰 가능한 차단 채널로 쓰고(§7 참조), Stop 재진입 시
  stop_hook_active 로 무한루프를 가드한다.
"""

import fnmatch
import json
import os
import re
import sys
import tempfile

# 계약 버전 — 템플릿 헤더의 INVARIANTS-CONTRACT 와 짝을 이룬다.
INVARIANTS_CONTRACT = "v2"

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
# 3. 로컬 로그 계층 판독 (허용된 지상검증 원천 — 내구 진실, 중립)
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


# 사이클 메타 entry 마커 인식 (CYCLE-LOG.md §5 / §10.3).
#   실제 entry는 *줄 앞머리*의 타임스탬프 브래킷에 앵커된다 — 두 형식 모두 실측(dlc-meta):
#     (A) 토큰이 브래킷 *뒤*  : `[2026-06-18 16:30] CYCLE-START` / `[2026-09-14] CYCLE-END (소급)`
#     (B) 토큰이 브래킷 *안*  : `[2026-08-13 CYCLE-START]` / `[CYCLE-END]`
#   ⚠️ 산문(prose)이 토큰을 *언급*만 하는 줄은 매치하면 안 된다 — 이게 이 앵커의 존재 이유다.
#     예: `…선례의 CYCLE-REOPEN 패턴).`, `불변식 엔진(CYCLE-START/END/REOPEN 스캔)`,
#         `> CYCLE-END(…) 이후 …`, `  Supersedes: [ts] CYCLE-END`, `  Next: CYCLE-END → gchat`,
#         `  Target: [ts] CYCLE-END`(정정 참조 줄). 이들은 줄이 `[`로 시작하지 않으므로 걸러진다.
#   substring 스캔은 이런 산문에 상태가 뒤집혀(실측: 11개 닫힌 사이클이 거짓 열림) 파일럿을
#   영구 no-op으로 만들었다 — 그래서 브래킷-앵커 정규식으로 교체한다.
_CYCLE_MARKER_RE = re.compile(
    r"^\s*\["
    r"(?:[^\]]*\b(?P<inside>CYCLE-(?:START|END|REOPEN))\b[^\]]*\]"   # (B) 브래킷 안
    r"|[^\]]*\]\s*(?P<after>CYCLE-(?:START|END|REOPEN))\b)"           # (A) 브래킷 뒤
)


def _cycle_marker(line):
    """줄이 실제 사이클 메타 entry면 'CYCLE-START'|'CYCLE-END'|'CYCLE-REOPEN' 반환, 산문/무관이면 None."""
    m = _CYCLE_MARKER_RE.match(line)
    if not m:
        return None
    return m.group("inside") or m.group("after")


def _cycle_is_open(text):
    """CYCLE-START/END/REOPEN *엔트리 마커* 순차 스캔 상태머신. 마지막 상태가 열림이면 True.
    (CYCLE-LOG.md §5 형식 · §10.3 재오픈 정합 — REOPEN은 다시 열림으로 취급).
    마커는 줄 앞머리의 타임스탬프 브래킷에 앵커해 인식한다(_cycle_marker) — 산문 속 토큰
    언급은 상태를 뒤집지 않는다. 한 줄엔 마커 종류가 하나뿐이라 END의 elif도 안전하다."""
    open_ = False
    for line in text.splitlines():
        kind = _cycle_marker(line)
        if kind == "CYCLE-START":
            open_ = True
        elif kind == "CYCLE-REOPEN":
            open_ = True
        elif kind == "CYCLE-END":
            open_ = False
    return open_


def _open_cycles(log_dir):
    opens = []
    for p in _iter_audit_files(log_dir):
        txt = _read_text(p)
        if txt is not None and _cycle_is_open(txt):
            opens.append(p)
    return opens


def _cycle_closed_in_log(log_dir, cycle_id):
    """주어진 cycle_id 의 audit.md 가 로그에 있고 *닫힘*(마지막 상태 CYCLE-END)이면 True.
    파일 부재·열림이면 False. keyed-log-on-done 이 done 레코드의 CYCLE-END 흔적을 확인할 때 쓴다."""
    if not cycle_id or not log_dir:
        return False
    safe = os.path.basename(str(cycle_id))
    txt = _read_text(os.path.join(log_dir, "cycles", safe, "audit.md"))
    if txt is None:
        return False
    return not _cycle_is_open(txt)


# ===========================================================================
# 3.5 키드(keyed) 상태 인덱스 IO (§13.3) — ephemeral, per-key, 락 프리
#      CHECK 경로에서 쓰는 것은 *읽기*(_read_state)뿐이다. 쓰기는 §6.5 write-helper.
# ===========================================================================
def _now_iso():
    try:
        import datetime
        return datetime.datetime.now().replace(microsecond=0).isoformat()
    except Exception:
        return ""


def _sanitize_key(k):
    """키·session_id 는 파일명 세그먼트가 되므로 안전화한다(§13.2) — 영숫자·`-`·`_`만 허용,
    그 외는 `_`로 치환, 길이 상한 200. 부정 경로·구분자 주입 방지. None/빈값 → None."""
    if k is None:
        return None
    s = str(k).strip()
    if not s:
        return None
    s = re.sub(r"[^A-Za-z0-9_-]", "_", s)
    return s[:200] if s else None


def _state_path(state_dir, key):
    return os.path.join(state_dir, key + ".json")


def _read_state(state_dir, key):
    """<state_dir>/<key>.json 을 읽어 dict 반환. 부재·malformed·키 없음 → None (degraded)."""
    if not state_dir or not key:
        return None
    txt = _read_text(_state_path(state_dir, key))
    if txt is None:
        return None
    try:
        data = json.loads(txt)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _atomic_write(path, payload):
    """temp+rename 원자적 쓰기 (같은 키의 self-갱신 원자성). state_dir 없으면 생성.
    os.replace 는 같은 파일시스템에서 원자적이라 락 프리 동시성(서로 다른 워커=서로 다른 파일)."""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp, path)  # 원자적
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise


def _write_state(state_dir, key, rec):
    _atomic_write(_state_path(state_dir, key), json.dumps(rec, ensure_ascii=False, indent=2) + "\n")


def _read_active_pointer(state_dir, session_id):
    """<state_dir>/active-<session_id> 를 읽어 현재 delegation-id(키)를 해소(§13.2).
    파일 부재 = 포인터 없음(→ 다음 폴백). session_id 안전화 후 파일명 구성."""
    sid = _sanitize_key(session_id)
    if not sid or not state_dir:
        return None
    txt = _read_text(os.path.join(state_dir, "active-" + sid))
    if txt is None:
        return None
    return txt.strip() or None


# 상태값 + 유효 전이 (§13.4). None = 레코드 없음. done 은 terminal — close(삭제)로만 벗어난다.
_VALID_STATUS = ("in-progress", "additional-work", "done")
_TRANSITIONS = {
    None: {"in-progress"},
    "in-progress": {"in-progress", "additional-work", "done"},
    "additional-work": {"additional-work", "in-progress", "done"},
    "done": set(),
}


# ===========================================================================
# 4. 명명된 체크 — 모두 ctx(dict: log_dir·state_dir·work_key)를 받아 (violation_bool, detail) 반환
#     (§13.6-6 — 체크 시그니처를 컨텍스트 객체로 일반화. 기존 두 체크도 ctx 수용.)
# ===========================================================================
def check_open_cycle_record_exists(ctx):
    """(전역·파일럿) 사이클 액션이 있었는데 열린 사이클 기록이 하나도 없으면 위반."""
    if _open_cycles(ctx.get("log_dir")):
        return (False, "")
    return (True, "사이클 액션 감지 — 열린 cycles/*/audit.md 기록(CYCLE-START)이 없습니다. "
                   "사이클을 시작했으면 audit.md에 CYCLE-START를 append하세요 (specs/CYCLE-LOG.md).")


def check_no_stale_open_cycle(ctx):
    """(전역·파일럿) 열린 사이클 기록이 턴 경계를 넘겨 잔존하면 위반(가시화)."""
    opens = _open_cycles(ctx.get("log_dir"))
    if not opens:
        return (False, "")
    names = ", ".join(os.path.basename(os.path.dirname(p)) for p in opens)
    return (True, "턴 경계에 열린 사이클이 잔존합니다: " + names +
                  " — 마무리됐으면 CYCLE-END를, 계속이면 그대로 두세요 (specs/CYCLE-LOG.md).")


# --- 키드(keyed) per-work-item 체크 3종 (§13.5) — 각기 *이 키의 상태 파일만* 읽는다.
#     → 워커 B는 워커 A의 상태에 영향받지 않음(동시성-안전) → block-tier 안전(Phase 3).
#     키 없음·state_dir 없음·레코드 malformed → no-op(차단 아님, degraded-safe).
def check_keyed_record_on_dispatch(ctx):
    """(a) 디스패치했는데 이 키의 상태 레코드가 없으면 위반 — 위임했으면 상태를 기록하라."""
    key = ctx.get("work_key")
    if not key:
        return (False, "")  # 키 없음 → no-op (degraded — 키 요구 체크는 조용히 스킵)
    if _read_state(ctx.get("state_dir"), key) is None:
        return (True, "디스패치 감지 — 작업 키 '%s'의 상태 레코드가 없습니다. "
                      "`enforce.py record --work-key %s`로 in-progress를 기록하세요 "
                      "(specs/INVARIANT-ENFORCEMENT.md §13.4)." % (key, key))
    return (False, "")


def check_keyed_valid_status_transition(ctx):
    """(b) 이 키가 검증 없이 done이거나(verified != true) status가 유효 집합 밖이면 위반."""
    key = ctx.get("work_key")
    if not key:
        return (False, "")
    rec = _read_state(ctx.get("state_dir"), key)
    if rec is None:
        return (False, "")  # 레코드 없음은 (a)가 다룬다 — 여기선 무판정
    status = rec.get("status")
    if status == "done" and rec.get("verified") is not True:
        return (True, "작업 키 '%s'가 검증 없이 done 상태입니다(verified != true). "
                      "지상검증(POLICY-VERIFY) 후에만 done으로 전이하세요 (§13.4)." % key)
    if status not in _VALID_STATUS:
        return (True, "작업 키 '%s'의 status가 유효하지 않습니다: %r "
                      "(허용: in-progress · additional-work · done)." % (key, status))
    return (False, "")


def check_keyed_log_on_done(ctx):
    """(c) 이 키가 done인데 대응 CYCLE-END 로그 흔적이 없으면, 또는 아직 열린 채 턴 경계를
    넘기면 위반. 각기 *이 키만* 보므로 A의 열림이 B의 Stop을 건드리지 않는다."""
    key = ctx.get("work_key")
    if not key:
        return (False, "")
    rec = _read_state(ctx.get("state_dir"), key)
    if rec is None:
        return (False, "")
    status = rec.get("status")
    if status == "done":
        if _cycle_closed_in_log(ctx.get("log_dir"), rec.get("cycle_id")):
            return (False, "")  # 로그에 CYCLE-END 있음 — 레코드가 아직 GC(close) 안 됐을 뿐
        return (True, "작업 키 '%s'가 done인데 대응 CYCLE-END 로그 흔적이 없습니다. "
                      "audit.md에 CYCLE-END를 append(+push)하고 레코드를 close하세요 (§13.4)." % key)
    if status in ("in-progress", "additional-work"):
        return (True, "작업 키 '%s'가 아직 %s 상태로 턴 경계를 넘겼습니다 — "
                      "마무리면 done(+CYCLE-END), 계속이면 그대로 두세요 (§13.5)." % (key, status))
    return (False, "")


CHECKS = {
    # 전역 파일럿 (v1 — 유지)
    "open-cycle-record-exists": check_open_cycle_record_exists,
    "no-stale-open-cycle": check_no_stale_open_cycle,
    # 키드 per-work-item (v2 — 신규, §13.5)
    "keyed-record-on-dispatch": check_keyed_record_on_dispatch,
    "keyed-valid-status-transition": check_keyed_valid_status_transition,
    "keyed-log-on-done": check_keyed_log_on_done,
}


# ===========================================================================
# 5. 선결 조건 (requires) — 불충족이면 불변식 SKIP (중립 견고성)
# ===========================================================================
def _precondition_met(req, ctx):
    if req == "local-log-layer":
        return os.path.isdir(os.path.join(ctx.get("log_dir") or "", "cycles"))
    if req == "keyed-state-dir":
        sd = ctx.get("state_dir")
        return bool(sd) and os.path.isdir(sd)
    # 미지원 선결 조건(예: STEP 2 어댑터가 넣을 issue-tracker-config)은 불충족으로 간주 → SKIP
    return False


def _requires_met(inv, ctx):
    reqs = inv.get("requires") or []
    if not isinstance(reqs, list):
        return False
    return all(_precondition_met(r, ctx) for r in reqs)


# ===========================================================================
# 6. 평가 (CHECK 경로 — 읽기 전용)
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


def evaluate(event, tool_name, tool_input, invariants, log_dir, state_dir=None, work_key=None):
    """위반된 (tier, message) 목록 반환. 체크에 넘길 컨텍스트(ctx)를 한 번 구성해 전달한다
    (§13.6-6 — 전역 체크와 키드 체크가 같은 ctx 를 받는다)."""
    ctx = {"log_dir": log_dir, "state_dir": state_dir, "work_key": work_key}
    findings = []
    for inv in invariants:
        if not _requires_met(inv, ctx):
            continue
        for b in _bindings(inv):
            if b.get("event") != event:
                continue
            if event in ("PostToolUse", "PreToolUse"):
                # 두 이벤트 모두 tool_name/tool_input 를 실어 온다 → 도구 매치로 좁힌다.
                if not _match_tool(b.get("match") or [], tool_name, tool_input):
                    continue
            fn = CHECKS.get(b.get("check"))
            if fn is None:
                continue
            try:
                violated, detail = fn(ctx)
            except Exception:
                continue
            if violated:
                findings.append((inv.get("tier", "advisory"),
                                 "[invariant:%s] %s" % (inv.get("id", "?"), detail)))
    return findings


# ===========================================================================
# 6.5 write-helper 서브커맨드 (§13.4 Q4=B) — 유일한 쓰기 진입점.
#      atomic temp+rename · 스키마 검증 · 유효 전이 강제 · 인덱스 포맷 단일 원천.
#      디스패치한 오케스트레이터 계층이 호출한다. CHECK 경로(위)와는 진입점만 분리.
#      반환 exit code: 0=성공, 2=거부(잘못된 인자·무효 전이·검증 없는 done), 1=예기치 못한 오류.
# ===========================================================================
def _sub_emit(ok, message, record=None, exit_code=0):
    out = {"ok": ok, "message": message}
    if record is not None:
        out["record"] = record
    _emit_write(out)
    return exit_code


def _apply_write(state_dir, key, status, fields, require_existing):
    """record/transition 공통 — 스키마 검증 + 유효 전이 강제 + atomic 쓰기.
    require_existing=True 면 기존 레코드가 있어야 한다(transition). fields: cycle_id·
    delegation_id·verified·dispatched_at 중 주어진 것만 반영."""
    key = _sanitize_key(key)
    if not key:
        return _sub_emit(False, "invalid or missing --work-key", exit_code=2)
    if not state_dir:
        return _sub_emit(False, "no state_dir resolved", exit_code=2)
    existing = _read_state(state_dir, key)
    if require_existing and existing is None:
        return _sub_emit(False, "no existing record for key %r — record it first" % key, exit_code=2)
    old_status = existing.get("status") if existing else None
    status = status or (old_status if existing else "in-progress")
    if status not in _VALID_STATUS:
        return _sub_emit(False, "invalid status %r (allowed: %s)"
                         % (status, ", ".join(_VALID_STATUS)), exit_code=2)
    if status not in _TRANSITIONS.get(old_status, set()):
        return _sub_emit(False, "invalid transition %r -> %r" % (old_status, status), exit_code=2)
    rec = dict(existing) if existing else {}
    rec["key"] = key
    rec["status"] = status
    if not rec.get("dispatched_at"):
        rec["dispatched_at"] = fields.get("dispatched_at") or _now_iso()
    for f in ("cycle_id", "delegation_id"):
        if fields.get(f) is not None:
            rec[f] = fields[f]
    if fields.get("verified") is not None:
        rec["verified"] = fields["verified"]
    rec.setdefault("verified", False)
    rec.setdefault("cycle_id", None)
    rec.setdefault("delegation_id", None)
    rec["updated_at"] = _now_iso()
    # 검증 없는 done 금지 (§13.4 — 검증 없이 완료로 건너뛰지 마라).
    if status == "done" and rec.get("verified") is not True:
        return _sub_emit(False, "cannot transition to done without verified=true", exit_code=2)
    try:
        _write_state(state_dir, key, rec)
    except Exception as e:
        return _sub_emit(False, "write failed: %s" % e, exit_code=1)
    return _sub_emit(True, "recorded %r status=%s" % (key, status), record=rec, exit_code=0)


def _cmd_close(state_dir, key):
    key = _sanitize_key(key)
    if not key:
        return _sub_emit(False, "invalid or missing --work-key", exit_code=2)
    if not state_dir:
        return _sub_emit(False, "no state_dir resolved", exit_code=2)
    path = _state_path(state_dir, key)
    try:
        if os.path.isfile(path):
            os.remove(path)
            return _sub_emit(True, "closed(deleted) %r" % key, exit_code=0)
        return _sub_emit(True, "no record for %r (already closed)" % key, exit_code=0)  # 멱등
    except Exception as e:
        return _sub_emit(False, "close failed: %s" % e, exit_code=1)


def _cmd_set_active(state_dir, session_id, key):
    """active-포인터 파일 쓰기 (§13.2 — 로컬 장수 오케스트레이터가 작업-시작마다 호출).
    §13 결정(Q4=B와 정합): 포인터 쓰기도 write-helper 를 경유한다."""
    sid = _sanitize_key(session_id)
    key = _sanitize_key(key)
    if not sid:
        return _sub_emit(False, "invalid or missing --session-id", exit_code=2)
    if not key:
        return _sub_emit(False, "invalid or missing --work-key", exit_code=2)
    if not state_dir:
        return _sub_emit(False, "no state_dir resolved", exit_code=2)
    try:
        d = state_dir
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-active-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(key + "\n")
            os.replace(tmp, os.path.join(d, "active-" + sid))
        except Exception:
            try:
                os.remove(tmp)
            except Exception:
                pass
            raise
    except Exception as e:
        return _sub_emit(False, "set-active failed: %s" % e, exit_code=1)
    return _sub_emit(True, "active pointer for session %r -> %r" % (sid, key), exit_code=0)


# reconcile 이 로그에서 optional delegation-id 를 읽을 때 쓰는 패턴 (§13.6-5 GAP 대비 — 아래 설명).
_DELEGATION_RE = re.compile(
    r"(?im)^\s*(?:Delegation(?:-id)?|delegation[_-]?id|Work-key|work[_-]?key)\s*[:=]\s*(\S+)"
)


def _reconcile_from_log(state_dir, log_dir):
    """세션/배포 시작 시 사이클 로그의 *열린* 사이클들로부터 에페메랄 인덱스를 REBUILD 한다
    (§13.3 2층 모델·§13.6-5). 인덱스는 로그의 파생물이므로 지워져도(휘발) 안전 — 이 경로가
    그 안전을 보장한다.

    ⚠️ GAP (§13이 플래그한 'log-carries-delegation-id') — 현행 CYCLE-LOG.md 형식(specs/
    CYCLE-LOG.md §5)의 CYCLE-START entry 는 오케스트레이터가 훅에 넘기는 *키(delegation-id)를
    담지 않는다*. 따라서 로그만으로는 키를 완전 복원할 수 없다. best-effort:
      - audit.md 에 `Delegation:` / `Work-key:` 줄이 *있으면* 그 값을 키로 쓴다(전방호환 —
        CYCLE-LOG 가 이 필드를 채우기 시작하면 reconcile 이 완전해진다). 데이터를 지어내지 않는다.
      - 없으면 cycle-id(디렉토리명)를 키로 삼는다(key_source="cycle-id"). 이 경우 라이브 훅이
        delegation-id 로 해소하는 키와 *일치하지 않으므로*, reconcile 레코드는 "열린 일이
        있다"는 가시성/백스톱 용도이지 라이브 키드 체크와 1:1 매칭되지는 않는다.
    TODO(follow-up): CYCLE-LOG.md CYCLE-START 에 `Delegation:` 필드를 추가하면 이 갭이
    닫힌다(스펙 §13 IMPLEMENTED 노트 참조). 그 전까지 cycle-id 폴백이 안전한 근사치다.

    이미 존재하는 레코드는 덮지 않는다(멱등 — 라이브 레코드 보존). 새로 쓴 키 목록을 반환한다."""
    written = []
    if not state_dir or not log_dir:
        return written
    for p in _iter_audit_files(log_dir):
        txt = _read_text(p)
        if txt is None or not _cycle_is_open(txt):
            continue
        cycle_id = os.path.basename(os.path.dirname(p))
        m = _DELEGATION_RE.search(txt)
        raw_key = m.group(1) if m else cycle_id
        key = _sanitize_key(raw_key)
        if not key:
            continue
        if _read_state(state_dir, key) is not None:
            continue  # 라이브 레코드 보존 (멱등)
        now = _now_iso()
        rec = {
            "key": key,
            "status": "in-progress",
            "cycle_id": cycle_id,
            "delegation_id": (m.group(1) if m else None),
            "dispatched_at": now,
            "verified": False,
            "updated_at": now,
            "reconciled": True,
            "key_source": ("delegation-id" if m else "cycle-id"),
        }
        try:
            _write_state(state_dir, key, rec)
            written.append(key)
        except Exception:
            continue
    return written


def _run_subcommand(sub, argv):
    base_dir_arg = _parse_opt(argv, "base-dir")
    state_dir = _resolve_state_dir(_parse_opt(argv, "state-dir"), base_dir_arg)
    key = _parse_opt(argv, "work-key")
    try:
        if sub == "record":
            return _apply_write(state_dir, key,
                                _parse_opt(argv, "status"),
                                _collect_fields(argv), require_existing=False)
        if sub == "transition":
            return _apply_write(state_dir, key,
                                _parse_opt(argv, "status"),
                                _collect_fields(argv), require_existing=True)
        if sub == "close":
            return _cmd_close(state_dir, key)
        if sub == "set-active":
            return _cmd_set_active(state_dir, _parse_opt(argv, "session-id"), key)
        if sub == "reconcile":
            log_dir = _resolve_log_dir(_parse_opt(argv, "log-dir") or base_dir_arg)
            written = _reconcile_from_log(state_dir, log_dir)
            return _sub_emit(True, "reconciled %d open cycle(s) into index" % len(written),
                             record={"keys": written}, exit_code=0)
    except Exception as e:
        return _sub_emit(False, "unexpected error: %s" % e, exit_code=1)
    return _sub_emit(False, "unknown subcommand %r" % sub, exit_code=2)


def _collect_fields(argv):
    fields = {}
    cid = _parse_opt(argv, "cycle-id")
    if cid is not None:
        fields["cycle_id"] = cid
    did = _parse_opt(argv, "delegation-id")
    if did is not None:
        fields["delegation_id"] = did
    da = _parse_opt(argv, "dispatched-at")
    if da is not None:
        fields["dispatched_at"] = da
    ver = _parse_opt(argv, "verified")
    if ver is not None:
        fields["verified"] = ver.strip().lower() in ("true", "yes", "1")
    return fields


# ===========================================================================
# 7. 훅 JSON 계약 방출 (Claude Code hook contract — 확정. 출처: code.claude.com/
#    docs/en/hooks.md, v2.1.2xx, 2026-09-11 fetch)
# ---------------------------------------------------------------------------
#   tier=block    → 이벤트별로 *실효 차단점*이 다르다:
#                    PreToolUse : {"hookSpecificOutput": {"hookEventName": "PreToolUse",
#                                    "permissionDecision": "deny",
#                                    "permissionDecisionReason": <msg>}} + exit 0.
#                                 ← 도구 실행 *전* 을 실제로 막는 유일한 지점(진짜 강제).
#                                   PreToolUse 는 구조화된 deny 가 권위 채널이다.
#                    Stop       : {"decision": "block", "reason": <msg>}  +  exit code 2.
#                                 ← stop 을 거부하고 reason 을 다음 턴에 되먹인다. exit 2 가
#                                   신뢰 채널(exit 0 + decision:block 은 자문에 그칠 수 있음).
#                    PostToolUse: 위 Stop 과 같은 형태로 나가나, 도구가 *이미 실행된 뒤*라
#                                 이는 진짜 차단이 아니라 Claude 에 주입되는 *자문 피드백*이다.
#                                 → PostToolUse 바인딩엔 block 을 켜지 말고 warn 을 쓴다(§11.4).
#   tier=warn     → Stop:        {"systemMessage": <msg>}
#                    PostToolUse: {"systemMessage": <msg>,
#                                  "hookSpecificOutput": {"hookEventName": "PostToolUse",
#                                                          "additionalContext": <msg>}}
#                    PreToolUse:  {"systemMessage": <msg>,
#                                  "hookSpecificOutput": {"hookEventName": "PreToolUse",
#                                                          "additionalContext": <msg>}}
#                    (warn 형태는 cp949 콘솔·PYTHONIOENCODING 없이 크래시 없이 방출됨이
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
        if event == "PreToolUse":
            # 실행 전 차단점 — 구조화된 deny 가 권위 채널(exit 0). 진짜 강제가 걸리는 유일한 지점.
            return ({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": text,
            }}, 0)
        # Stop(차단) / PostToolUse(사후 자문) — decision:block + exit 2 가 신뢰 채널.
        return ({"decision": "block", "reason": text}, 2)
    if top == _TIER_ORDER["warn"]:
        out = {"systemMessage": text}
        if event in ("PostToolUse", "PreToolUse"):
            out["hookSpecificOutput"] = {
                "hookEventName": event,
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
# 8. 경로 해석 — CLI 인자 > env(하위호환) > 기본값
#    STEP 2에서 SETTER는 훅 command 문자열에 --base-dir(절대경로)로 바인딩한다.
#    Claude Code 훅엔 env 필드가 없으므로(위 모듈 docstring 참조) CLI 가 1차 채널이고,
#    env 는 부모 프로세스에 값이 있을 때를 위한 하위호환 폴백으로만 남는다.
# ===========================================================================
def _resolve_invariants_dir(cli_val):
    return (cli_val
            or os.environ.get("AIDLC_INVARIANTS_DIR")
            or os.path.dirname(os.path.abspath(__file__)))


def _resolve_log_dir(cli_val):
    return (cli_val
            or os.environ.get("AIDLC_LOG_DIR")
            or os.getcwd())


def _resolve_state_dir(cli_val, base_dir):
    """키드 인덱스 디렉토리 (§13.3). CLI > env > <base-dir>/.aidlc-state.
    base_dir 가 없으면(그리고 env·CLI 도 없으면) cwd 기준 .aidlc-state 로 폴백."""
    if cli_val:
        return cli_val
    env = os.environ.get("AIDLC_STATE_DIR")
    if env:
        return env
    root = base_dir or os.getcwd()
    return os.path.join(root, ".aidlc-state")


def _resolve_work_key(cli_val, state_dir, session_id):
    """§13.5 키 해석 우선순위: --work-key/AIDLC_WORK_KEY > active-포인터(session_id로 조회) > 없음.
    session_id 자체는 키가 아니라 포인터 조회 핸들이다(§13.2)."""
    k = cli_val or os.environ.get("AIDLC_WORK_KEY")
    if k:
        return _sanitize_key(k)
    k = _read_active_pointer(state_dir, session_id)
    if k:
        return _sanitize_key(k)
    return None


# ===========================================================================
# 9. CLI
# ===========================================================================
def _parse_opt(argv, name):
    """--name value 또는 --name=value 형태에서 값을 뽑는다. 없으면 None."""
    flag = "--" + name
    for i, a in enumerate(argv):
        if a == flag and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith(flag + "="):
            return a.split("=", 1)[1]
    return None


def _parse_event(argv):
    return _parse_opt(argv, "event")


_SUBCOMMANDS = ("record", "transition", "close", "set-active", "reconcile")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # write-helper 서브커맨드? 첫 비-플래그 토큰이 알려진 서브커맨드면 그쪽으로 (§6.5 쓰기 경계).
    if argv and not argv[0].startswith("-") and argv[0] in _SUBCOMMANDS:
        return _run_subcommand(argv[0], argv[1:])
    # 그 외 = CHECK 경로 (--event 구동, 읽기 전용).
    event = _parse_event(argv)
    if event not in ("PreToolUse", "PostToolUse", "Stop"):
        return 0  # 알 수 없는 이벤트 → no-op (degraded-safe)
    # 경로 인자: --base-dir 하나로 둘 다, 또는 --invariants-dir/--log-dir 개별(개별이 우선).
    base_dir_arg = _parse_opt(argv, "base-dir")
    invariants_dir = _resolve_invariants_dir(_parse_opt(argv, "invariants-dir") or base_dir_arg)
    log_dir = _resolve_log_dir(_parse_opt(argv, "log-dir") or base_dir_arg)
    state_dir = _resolve_state_dir(_parse_opt(argv, "state-dir"), base_dir_arg or log_dir)
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
    # session_id 는 키가 아니라 active-포인터 조회 핸들이다(§13.2). 없어도 degraded-safe.
    session_id = data.get("session_id") if isinstance(data, dict) else None
    # 키 해석: --work-key/AIDLC_WORK_KEY > active-포인터 > 없음(키드 체크 no-op).
    work_key = _resolve_work_key(_parse_opt(argv, "work-key"), state_dir, session_id)
    # Stop-block 무한루프 가드용 신호 — 재진입한 Stop 훅이면 하네스가 true 로 실어 준다.
    # 깨지거나 없으면 False(=미재진입)로 안전 처리 (degraded-safe).
    stop_hook_active = bool(data.get("stop_hook_active")) if isinstance(data, dict) else False
    code = 0
    try:
        invs = load_invariants(invariants_dir)
        findings = evaluate(event, tool_name, tool_input, invs, log_dir, state_dir, work_key)
        out, code = emit(event, findings, stop_hook_active)
    except Exception:
        out, code = None, 0  # 무엇이 어긋나도 조용히 통과 (EX-15 / C FALLBACK)
    if out is not None:
        _emit_write(out)  # JSON 을 먼저 쓴다 (block 이면 그 뒤 exit 2). reconfigure 불가 런타임도 버퍼 바이트로 안전
    return code


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""enforce.template.py — 범용 불변식(invariant) 강제 엔진 (템플릿)

이 파일은 인스턴스 산출물의 템플릿이다 (POLICY-TEMPLATE-ADHERENCE). SETTER가 STEP 2에서
이 엔진을 훅에 배선하고, 두 선언 파일(invariants.team.yaml / invariants.personal.yaml)의
실제 경로를 바인딩한다. 본 파일 자체는 프레임워크 레포에 그대로 산다 — 100% 중립.

INVARIANTS-CONTRACT: v2
  (v1 → v2 — 키드(keyed) per-work-item 상태머신 체크 3종 추가로 *체크 id 집합*이 바뀌었다.
   specs/INVARIANT-ENFORCEMENT.md §13.6-8. 계약 값은 이 상수와 템플릿 헤더가 짝을 이룬다.)
  (v2 유지 — repo-fresh-before-access 체크 1종 추가. 순수 *가산(additive)*이라 계약을 올리지
   않는다: 기존 체크·emit() 훅 JSON 형태·레코드 스키마 불변이고, 새 선결 조건 없이 기존
   keyed-state-dir 를 재사용하며, 세션 마커(reposcan-*)는 키드 work-item 레코드와 별개 네임스페이스다.
   미지원 체크 id 는 엔진이 조용히 no-op 스킵하므로 신·구 엔진↔yaml 혼용도 안전(degraded-safe).
   specs/INVARIANT-ENFORCEMENT.md §14.)
  (v2 유지 — overlay-consulted-before-work(§15) 체크 2종(관찰·게이트) 추가. 역시 순수 가산이다:
   기존 체크·emit() 훅 JSON·레코드 스키마 불변, 새 선결 조건 없이 기존 keyed-state-dir 재사용,
   읽기 관찰 마커(overlayread-*)는 키드 레코드·reposcan-* 과 또 다른 별개 네임스페이스이며,
   선언(options.overlay) 미설정이면 조용히 SKIP 이라 이 개념이 없는 배포에선 완전 no-op.
   미지원 체크 id 는 구 엔진이 무시하므로 신·구 혼용도 안전. specs/INVARIANT-ENFORCEMENT.md §15.)
  (v2 유지 — repo-fresh 재무장(§14.8): 작업 아이템 개시 재무장 epoch + 마커 TTL + 선언
   options{ttl_minutes·rearm_grace_minutes·repos[]}. 역시 순수 가산이다: 체크 id 집합·훅 JSON·
   레코드 스키마 불변, options 부재면 기본값으로 동작(구 yaml↔신 엔진 안전), 구 엔진은 options 를
   모르는 키로 무시(신 yaml↔구 엔진 안전 — 이전 동작 그대로).)

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
             [--overlay-user <id>]        ← §15 사용자 오버레이 식별자(미지정이면 그 체크만 SKIP)

  # write-helper 서브커맨드 (오케스트레이터/디스패처 계층이 호출 — 유일한 쓰기 진입점)
  enforce.py record     --work-key <k> [--status <s>] [--cycle-id <c>] [--delegation-id <d>]
                        [--verified true|false] [--session-id <sid>] [--state-dir <abs>|--base-dir <abs>]
                        ↳ 작업 아이템 개시 = §14 최신성 재무장 지점이다. record 는 레코드를 쓰기 전에
                          reposcan 재무장 epoch 를 찍어, 이 작업 아이템의 첫 레포 접근에서 최신성이
                          *다시* 판정되게 만든다(--session-id/AIDLC_SESSION_ID 있으면 그 세션만,
                          없으면 글로벌 폴백). 쓰기이므로 write-helper 쪽에 있다 (§13.4 Q4=B).
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
import hashlib
import json
import os
import re
import sys
import tempfile
import time

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


# --- (repo-fresh-before-access) git 최신성 체크 (§14) — "이 레포를 *지금 이 작업 아이템*에서
#     pull 없이 읽/작업하려는가"를 *네트워크 없이* 판정한다. 원격 있는 레포에만 적용(원격 없음 →
#     SKIP, agnostic·중립). stat 기반이라 값싸다.
#     이 체크는 키드 work-item 레코드(§13.4 write-helper 단일 원천)를 건드리지 않고, 자기 전용
#     ephemeral 세션 마커만 쓴다 — 그 마커는 언제 휘발해도 안전(state_dir 은 gitignore·재생성 가능).
#
#     ⚠️ 재무장(§14.8) — 도입판은 재무장 지점이 *세션 시작 하나뿐*이었다. 그래서 오래 사는 세션
#        (실측: 7일)에서 세션 초 fetch 한 번이 그 세션 내내 영원히 fresh 판정을 만들고, per-repo
#        마커가 재발동까지 막아 **공유 레포가 21커밋 앞서 나가도 훅이 한 번도 뜨지 않았다**. 오래
#        사는 세션 × 다른 주체가 계속 쓰는 레포 = 가장 위험한 조합이 정확히 사각지대였다.
#        고침은 재무장 지점을 둘 더 만드는 것이다:
#          (1) **작업 아이템 개시** — write-helper 의 `record`(디스패치마다 찍는 그 지점, §13.4)가
#              reposcan 재무장 epoch 를 찍는다. pull-before-work 규율이 작업 단위로 자동 강제된다.
#          (2) **마커 TTL** — 한 작업 아이템이 길어져도 ttl 이 지나면 재판정이 걸린다.
#        판정식: fresh = FETCH_HEAD mtime >= deadline,
#                deadline = max(세션 앵커, 재무장 epoch - grace, now - ttl)
#        dedup:  fired 마커는 (재무장 epoch 이후에 찍혔고) AND (찍힌 지 ttl 이내)일 때만 억제한다.
#        `- grace` 는 "pull → record → 접근" 순서를 오탐하지 않기 위한 여유다(작업 아이템 기록
#        직전에 한 pull 도 그 작업 아이템의 pull 로 친다).
_FRESH_PATH_KEYS = ("file_path", "path", "notebook_path", "filePath")
_GIT_REFRESH_RE = re.compile(r"\bgit\b[^\n;&|]*\b(?:pull|fetch|clone|remote\s+update)\b", re.I)

# 기본값 근거 (§14.8) — 둘 다 선언(yaml) options 로 덮어쓸 수 있다. 엔진엔 어떤 레포 이름도 없다.
#   ttl 90분  : 1차 재무장은 *작업 아이템 개시*이고 TTL 은 그 백스톱이다. 통상 작업 아이템은 1시간
#               안쪽이라 90분이면 작업 중간에 다시 찌르지 않는다(소음 하한). 동시에 어떤 세션도
#               최대 90분마다 레포당 1회는 재판정을 받으므로, 며칠 사는 세션의 "영원히 fresh"
#               사각지대가 사라진다(상한). warn tier·레포당 1회라 오탐 비용은 한 줄 넛지뿐이다.
#   grace 5분 : 오케스트레이터의 자연스러운 순서는 pull → record → 접근이다. record 직전 수 분
#               안에 한 pull 을 stale 로 몰면 순전한 오탐이 된다. 5분은 그 창을 덮되, 실제로
#               낡은 pull(수십 분~며칠 전)은 그대로 걸러낸다.
#   공유 상태 레포(다른 주체가 계속 쓰는 레포)는 90분도 길다 → options.repos[] 의 glob 오버라이드로
#   더 짧은 ttl 을 선언한다(예: 10분). 어떤 레포가 그런지는 *배포가* 선언한다 — 엔진은 모른다.
_FRESH_DEFAULT_TTL_MIN = 90
_FRESH_DEFAULT_GRACE_MIN = 5


def _touch(path):
    """빈 파일을 만들고(없으면) mtime 을 지금으로 갱신한다. degraded-safe: 호출부가 try 로 감싼다."""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    with open(path, "a", encoding="utf-8"):
        pass
    os.utime(path, None)


def _accessed_path(ctx):
    """접근 대상 경로를 유도한다. 파일-경로 도구(Read/Edit/Grep 등)는 tool_input 의 경로 키를,
    그 외(Bash/PowerShell 등)는 cwd 를 쓴다. 상대경로는 cwd 기준 절대화. 없으면 None."""
    ti = ctx.get("tool_input") or {}
    cand = None
    if isinstance(ti, dict):
        for k in _FRESH_PATH_KEYS:
            v = ti.get(k)
            if isinstance(v, str) and v.strip():
                cand = v.strip()
                break
    cwd = ctx.get("cwd")
    if not cand:
        cand = cwd
    if not cand:
        return None
    try:
        if not os.path.isabs(cand) and cwd:
            cand = os.path.join(cwd, cand)
        return os.path.abspath(cand)
    except Exception:
        return cand


def _find_git_root(path):
    """path 에서 위로 올라가며 .git(디렉토리 또는 파일)을 가진 첫 조상을 반환. 없으면 None."""
    if not path:
        return None
    try:
        cur = path if os.path.isdir(path) else os.path.dirname(path)
    except Exception:
        return None
    seen = 0
    while cur and seen < 256:
        try:
            if os.path.exists(os.path.join(cur, ".git")):
                return cur
        except Exception:
            return None
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
        seen += 1
    return None


def _git_dir(git_root):
    """git_root/.git 를 실제 gitdir 로 해소한다(.git 이 파일이면 'gitdir:' 참조 — worktree/submodule)."""
    gp = os.path.join(git_root, ".git")
    try:
        if os.path.isdir(gp):
            return gp
        if os.path.isfile(gp):
            for line in (_read_text(gp) or "").splitlines():
                line = line.strip()
                if line.startswith("gitdir:"):
                    ref = line[len("gitdir:"):].strip()
                    if ref:
                        return ref if os.path.isabs(ref) else os.path.abspath(os.path.join(git_root, ref))
    except Exception:
        return None
    return None


def _has_remote(git_dir):
    """원격이 하나라도 설정돼 있으면 True. .git/config 의 [remote "..."] 우선, 폴백 refs/remotes.
    읽기 실패·무원격 → False (→ SKIP, agnostic — 로컬 전용 레포는 강제 대상 아님)."""
    if not git_dir:
        return False
    cfg = _read_text(os.path.join(git_dir, "config"))
    if cfg and re.search(r'(?m)^\s*\[\s*remote\s+"', cfg):
        return True
    try:
        rr = os.path.join(git_dir, "refs", "remotes")
        if os.path.isdir(rr) and os.listdir(rr):
            return True
    except Exception:
        pass
    return False


def _repo_marker_token(git_root):
    try:
        norm = os.path.normcase(os.path.abspath(git_root))
    except Exception:
        norm = str(git_root)
    return hashlib.sha1(norm.encode("utf-8", "replace")).hexdigest()[:16]


def _fresh_session_token(ctx):
    return _sanitize_key(ctx.get("session_id")) or "nosession"


def _fresh_anchor_mtime(state_dir, sid_tok):
    """세션 앵커 mtime(≈세션 시작)을 반환한다. 없으면 지금 생성(첫 매치 도구 실행 ≈ 세션 시작)한다.
    실패하면 None → 판정 보류(오탐 방지). 앵커는 refresh 명령/스킵보다 먼저 확보돼야
    'pull 후 read'가 새 FETCH_HEAD(앵커 이후 mtime)로 fresh 판정된다."""
    path = os.path.join(state_dir, "reposcan-" + sid_tok + ".anchor")
    try:
        if not os.path.exists(path):
            _touch(path)
        return os.path.getmtime(path)
    except Exception:
        return None


def _rearm_marker_names(sid_tok):
    """재무장 epoch 파일명 후보 — 세션 스코프 우선 + 글로벌 폴백(§14.8).
    write-helper 가 --session-id 를 알면 그 세션만 재무장하고(정밀), 모르면 글로벌을 찍어
    이 state_dir 의 모든 세션이 재판정하게 한다(안전 방향 — 덜 검사하는 쪽으로 기울지 않는다)."""
    return ("reposcan-" + sid_tok + ".rearm", "reposcan.rearm")


def _fresh_rearm_epoch(state_dir, sid_tok):
    """마지막 작업 아이템 개시(재무장) 시각. 세션 스코프·글로벌 중 최신. 없으면 0.0 (재무장 이력 없음)."""
    best = 0.0
    for name in _rearm_marker_names(sid_tok):
        try:
            p = os.path.join(state_dir, name)
            if os.path.isfile(p):
                m = os.path.getmtime(p)
                if m > best:
                    best = m
        except Exception:
            continue
    return best


def _mtime_or_none(path):
    try:
        return os.path.getmtime(path) if os.path.exists(path) else None
    except Exception:
        return None


def _opt_minutes(val, default_min):
    """선언 값(분)을 초로. 숫자가 아니면 기본값. <=0 은 '비활성'로 그대로 통과(0 반환)."""
    try:
        if isinstance(val, bool) or val is None:
            raise ValueError
        m = float(val)
    except Exception:
        m = float(default_min)
    if m <= 0:
        return 0.0
    return m * 60.0


def _fresh_options(inv):
    """불변식 선언의 options 블록을 읽는다 (§14.8). 전부 선택적 — 없으면 기본값.
    스키마: options: {ttl_minutes: <n>, rearm_grace_minutes: <n>,
                      repos: [{match: <glob|[glob…]>, ttl_minutes: <n>}, …]}
    엔진엔 레포 이름이 없다 — 어떤 레포를 더 짧게 볼지는 *선언*이 정한다(중립)."""
    opts = inv.get("options") if isinstance(inv, dict) else None
    if not isinstance(opts, dict):
        opts = {}
    ttl = _opt_minutes(opts.get("ttl_minutes"), _FRESH_DEFAULT_TTL_MIN)
    grace = _opt_minutes(opts.get("rearm_grace_minutes"), _FRESH_DEFAULT_GRACE_MIN)
    repos = opts.get("repos")
    return ttl, grace, (repos if isinstance(repos, list) else [])


def _repo_match_candidates(root):
    """glob 매칭 후보 — 절대경로(구분자 '/' 정규화)와 basename 둘 다."""
    try:
        p = os.path.abspath(root).replace("\\", "/")
    except Exception:
        p = str(root).replace("\\", "/")
    return (p, p.rstrip("/").rsplit("/", 1)[-1])


def _fresh_ttl_for_repo(root, ttl_default, repos):
    """선언된 per-repo 오버라이드 중 *첫 매치*의 ttl 을 쓴다. 없으면 기본 ttl.
    (공유 상태 레포처럼 다른 주체가 계속 쓰는 레포를 더 짧게 보기 위한 수단 — §14.8.)"""
    cands = _repo_match_candidates(root)
    for entry in repos:
        if not isinstance(entry, dict):
            continue
        globs = entry.get("match")
        if isinstance(globs, str):
            globs = [globs]
        if not isinstance(globs, list):
            continue
        for g in globs:
            if not isinstance(g, str):
                continue
            for c in cands:
                try:
                    if fnmatch.fnmatch(c, g):
                        return _opt_minutes(entry.get("ttl_minutes"), ttl_default / 60.0)
                except Exception:
                    continue
    return ttl_default


def _fmt_age(seconds):
    try:
        mins = int(seconds // 60)
    except Exception:
        return "?"
    if mins < 60:
        return "%d분" % mins
    if mins < 60 * 48:
        return "%d시간" % (mins // 60)
    return "%d일" % (mins // 1440)


def check_repo_fresh_before_access(ctx):
    """(repo-fresh-before-access §14) 원격 있는 레포를 *지금 이 작업 아이템*에서 git pull 없이
    읽/작업하려 하면 위반.
      fresh  = .git/FETCH_HEAD mtime >= deadline
      dedup  = fired 마커가 (재무장 epoch 이후) AND (찍힌 지 ttl 이내)일 때만 억제
      deadline = max(세션 앵커, 재무장 epoch - grace, now - ttl)      ← §14.8 재무장 3지점
    원격 없음·비레포·앵커 불가·한 번도 fetch 안 됨(FETCH_HEAD 부재=stale) 등은 아래대로 처리.
    훅은 pull 을 대신 실행하지 않고 최신성만 검사한다. 무엇이 어긋나도 크래시 없이 no-op."""
    state_dir = ctx.get("state_dir")
    if not state_dir:
        return (False, "")  # dedup 불가 → no-op (requires: keyed-state-dir 로도 걸러짐, degraded-safe)
    # 세션 앵커를 *가장 먼저* 확보(refresh 명령/스킵보다 앞) — 'pull 후 read'의 fresh 판정 보장.
    sid_tok = _fresh_session_token(ctx)
    anchor = _fresh_anchor_mtime(state_dir, sid_tok)
    root = _find_git_root(_accessed_path(ctx))
    if not root:
        return (False, "")  # 비-레포 경로 → SKIP
    # git 최신화 자체(pull/fetch/clone/remote update)는 최신화 행위이므로 SKIP(마커도 안 남긴다 —
    # 뒤이은 실제 접근이 갱신된 FETCH_HEAD 로 fresh 판정되게 둔다).
    ti = ctx.get("tool_input") or {}
    cmd = ti.get("command") if isinstance(ti, dict) else None
    if isinstance(cmd, str) and _GIT_REFRESH_RE.search(cmd):
        return (False, "")
    gd = _git_dir(root)
    if not _has_remote(gd):
        return (False, "")  # 원격 없음 → SKIP (중립/agnostic)
    ttl_default, grace, repo_opts = _fresh_options(ctx.get("inv") or {})
    ttl = _fresh_ttl_for_repo(root, ttl_default, repo_opts)
    now = time.time()
    epoch = _fresh_rearm_epoch(state_dir, sid_tok)
    fired = os.path.join(state_dir, "reposcan-" + sid_tok + "-" + _repo_marker_token(root))
    fired_at = _mtime_or_none(fired)
    # 동률(mtime 이 같은 눈금)은 *재판정* 쪽으로 기운다 — 덜 검사하는 쪽으로 기울지 않는다.
    if fired_at is not None and fired_at > epoch and (ttl <= 0 or (now - fired_at) < ttl):
        # 이 재무장 창 안에서 이 레포는 이미 판정했다 — 조용히 통과(레포당 1회, 매 접근마다가 아님).
        return (False, "")
    if anchor is None:
        return (False, "")  # 앵커 확보 실패 → 판정 보류(오탐 방지)
    deadline = anchor
    if epoch > 0:
        deadline = max(deadline, epoch - grace)   # 작업 아이템 개시 이후의 pull 을 요구
    if ttl > 0:
        deadline = max(deadline, now - ttl)       # 길어지는 작업 아이템의 백스톱
    fresh = False
    fh_at = None
    try:
        fh = os.path.join(gd, "FETCH_HEAD")  # 한 번도 fetch 안 됐으면 부재 → stale(=pull 필요, 취지대로)
        fh_at = _mtime_or_none(fh)
        if fh_at is not None and fh_at >= deadline:
            fresh = True
    except Exception:
        fresh = False
    try:
        _touch(fired)  # 재무장 창당 레포당 1회 보장(판정 후 마커 — fresh든 stale이든 이 창에선 재발동 X)
    except Exception:
        pass
    if fresh:
        return (False, "")
    name = os.path.basename(root.rstrip("/\\")) or root
    why = ("한 번도 fetch 되지 않았습니다" if fh_at is None
           else "마지막 fetch 로부터 %s 지났습니다" % _fmt_age(max(0.0, now - fh_at)))
    return (True, "레포 '%s'를 최신화 없이 접근하려 합니다 (%s) — 참조·작업 전에 "
                  "`git fetch && git pull`로 먼저 최신화하세요 (feedback-pull-before-work / "
                  "specs/INVARIANT-ENFORCEMENT.md §14). 훅은 pull 을 대신 실행하지 않고 최신성만 검사합니다."
                  % (name, why))


# --- (overlay-consulted-before-work) 사용자 오버레이 참조 체크 (§15) — "작업 아이템을 개시할 때
#     사용자별 오버레이(작동 스타일·누적 교정 피드백)를 *읽었는가*"를 판정한다.
#     §14(최신성)와 목적이 다르다: §14 는 "그 레포가 stale 한가"(pull 했나), §15 는 "참조했는가"(읽었나).
#     **그래서 pull 만 하고 안 읽으면 통과시키지 않는다** — 판정 원천이 FETCH_HEAD 가 아니라 *실제
#     읽기 관찰 마커*다. 공유 장기 메모리를 "어떤 환경에서 에이전트가 뜨든 같은 사용자 최적화를 받는다"는
#     목적으로 두는데, 그걸 *읽게 만드는 장치*가 없으면 그 목적이 조용히 깨진다(실측: 오버레이가 갱신을
#     멈춘 채 학습이 전부 머신 로컬 메모리로 샜다).
#
#     중립(agnostic): 엔진엔 어떤 디렉토리명·파일명·사용자 이름도 박혀 있지 않다. 오버레이 위치·필수
#     항목·사용자 식별자는 전부 *선언*(options.overlay) 또는 CLI(--overlay-user)/env 로 들어오고,
#     **미설정이면 조용히 SKIP** 한다(이 개념이 없는 배포에서 완전 no-op).
#
#     두 바인딩이 짝을 이룬다(§15.3):
#       (관찰) PostToolUse — 오버레이 파일을 실제로 읽은 도구 호출을 보고 ephemeral 마커를 찍는다.
#              *절대 위반을 내지 않는다*(순수 관찰). 사후 이벤트라 "읽기가 실제로 일어났다"가 참이다.
#       (게이트) PreToolUse(디스패치 도구) — 이번 재무장 창 안에 그 마커가 없으면 warn.
#     판정식: consulted = 마커 mtime >= deadline,
#             deadline = max(세션 앵커, 재무장 epoch - grace)          ← §14.8 재무장 창을 그대로 재사용
#     재무장 epoch 는 write-helper 의 `record`(디스패치마다 찍는 그 지점)가 갱신하므로, 창 = *작업 아이템*
#     이다. 즉 "작업 아이템마다 한 번은 오버레이를 읽어라"가 자동으로 강제된다.
#     grace 는 "읽기 → record → 디스패치" 순서에서 읽기가 record 직전이었던 경우를 오탐하지 않기 위한
#     여유다. 오탐 비용은 작다 — 경고를 받고 하는 일이 *작은 진입점 두 파일을 다시 읽는 것*이고, 그건
#     애초에 요구되는 행동 자체다. 한 번 읽으면 마커가 갱신돼 같은 창에선 다시 뜨지 않는다(창당 1회).
_OVERLAY_DEFAULT_GRACE_MIN = 5
_OVERLAY_TOKEN_RE = re.compile(r"[\s'\"`=;|,()<>&]+")


def _overlay_user(ctx, ov):
    """사용자 식별자 해석: CLI(--overlay-user) > env(AIDLC_OVERLAY_USER) > 선언(options.overlay.user).
    경로 세그먼트가 되므로 안전화한다(구분자·상위참조 주입 방지). 없으면 None → 호출부가 SKIP."""
    for cand in (ctx.get("overlay_user"),
                 os.environ.get("AIDLC_OVERLAY_USER"),
                 ov.get("user") if isinstance(ov, dict) else None):
        if isinstance(cand, str) and cand.strip():
            s = re.sub(r"[^A-Za-z0-9._@+-]", "_", cand.strip()).lstrip(".")
            if s:
                return s[:100]
    return None


def _overlay_decl(ctx):
    """선언 options.overlay 를 해석해 {targets: [(abs, tail)…], grace: 초} 반환. 부재·불완전·
    대상 파일 전무 → None (조용히 SKIP — 이 개념이 없는 배포에서 no-op).

    스키마: options:
              overlay:
                path: <메타 레포 상대 또는 절대 경로. '{user}' 치환 가능>
                required: [<path 기준 상대 파일…>]   # *전부* 읽어야 충족 (항상 읽는 진입점 집합)
                user: <식별자>                        # 선택 — CLI/env 가 우선
                grace_minutes: <n>                    # 선택 — 기본 5
    required 중 *실제로 존재하는* 파일만 대상이 된다 — 아직 없는 항목(예: 아직 만들지 않은 인덱스)이
    영구 미충족을 만들지 않게 한다(degraded-safe·환경 중립)."""
    inv = ctx.get("inv")
    opts = inv.get("options") if isinstance(inv, dict) else None
    ov = opts.get("overlay") if isinstance(opts, dict) else None
    if not isinstance(ov, dict):
        return None
    path = ov.get("path")
    if not isinstance(path, str) or not path.strip():
        return None
    path = path.strip()
    if "{user}" in path:
        user = _overlay_user(ctx, ov)
        if not user:
            return None  # 사용자 미식별 → SKIP (추측하지 않는다)
        path = path.replace("{user}", user)
    req = ov.get("required")
    if isinstance(req, str):
        req = [req]
    if not isinstance(req, list) or not req:
        return None  # 무엇을 읽어야 충족인지 선언되지 않음 → SKIP (엔진이 파일명을 가정하지 않는다)
    root = path.replace("\\", "/")
    try:
        if not os.path.isabs(root):
            base = ctx.get("base_dir") or ctx.get("log_dir")
            if not base:
                return None
            root = os.path.join(base, *[s for s in root.split("/") if s not in ("", ".")])
        root = os.path.abspath(root)
    except Exception:
        return None
    leaf = os.path.basename(root.rstrip("/\\"))
    targets = []
    for r in req:
        if not isinstance(r, str) or not r.strip():
            continue
        rel = r.strip().replace("\\", "/").strip("/")
        if not rel or ".." in rel.split("/"):
            continue
        try:
            p = os.path.abspath(os.path.join(root, *rel.split("/")))
            if not os.path.isfile(p):
                continue  # 아직 없는 항목은 요구하지 않는다
        except Exception:
            continue
        # tail = 문자열 매칭용 꼬리(오버레이 디렉토리 leaf + 상대경로) — 절대/상대/POSIX-스타일 경로
        #   표기 차이를 가로질러 "이 파일을 가리키는 문자열인가"를 값싸게 본다.
        targets.append((p, ((leaf + "/") if leaf else "") + rel))
    if not targets:
        return None
    return {"targets": targets,
            "grace": _opt_minutes(ov.get("grace_minutes"), _OVERLAY_DEFAULT_GRACE_MIN)}


def _overlay_marker(state_dir, sid_tok, tail):
    """읽기 관찰 마커 — 자기 전용 ephemeral 네임스페이스(overlayread-*). 키드 work-item 레코드·
    active 포인터와 별개이며 언제 휘발해도 안전(재판정이 한 번 더 걸릴 뿐)."""
    h = hashlib.sha1(tail.lower().encode("utf-8", "replace")).hexdigest()[:16]
    return os.path.join(state_dir, "overlayread-" + sid_tok + "-" + h)


def _overlay_strings(tool_input):
    """tool_input 에서 경로가 실릴 수 있는 문자열 값을 모은다(중첩 1단계 리스트까지)."""
    vals = []
    if isinstance(tool_input, dict):
        for v in tool_input.values():
            if isinstance(v, str) and v.strip():
                vals.append(v)
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, str) and x.strip():
                        vals.append(x)
    return vals


def _overlay_hit(target_abs, tail, vals, cwd):
    """이 도구 호출의 문자열들이 이 오버레이 파일을 가리키는가.
      (1) 꼬리 부분문자열 — 절대/상대/POSIX-스타일(`/c/...`)·구분자 차이를 가로질러 잡는다.
      (2) 토큰 절대화 동치 — 셸 명령 안의 상대 경로 토큰을 cwd 기준으로 절대화해 비교.
    둘 다 순수 문자열·경로 연산이다(대상 파일을 다시 열지 않는다)."""
    tl = tail.lower()
    for s in vals:
        if tl and tl in s.replace("\\", "/").lower():
            return True
    try:
        ta = os.path.normcase(target_abs)
        base_l = os.path.basename(target_abs).lower()
    except Exception:
        return False
    for s in vals:
        for tok in _OVERLAY_TOKEN_RE.split(s):
            if not tok:
                continue
            tok = tok.strip().strip("'\"")
            if not tok or os.path.basename(tok.replace("\\", "/")).lower() != base_l:
                continue
            try:
                p = tok if os.path.isabs(tok) else (os.path.join(cwd, tok) if cwd else tok)
                if os.path.normcase(os.path.abspath(p)) == ta:
                    return True
            except Exception:
                continue
    return False


def check_overlay_read_observe(ctx):
    """(관찰 전용 — *절대 위반을 내지 않는다*) 오버레이 파일을 읽은 도구 호출을 보고 마커를 찍는다.
    PostToolUse 에 바인딩한다 — 사후라 "읽기가 실제로 일어났다"가 참이다(거부·실패한 읽기가 충족으로
    세지 않는다)."""
    decl = _overlay_decl(ctx)
    state_dir = ctx.get("state_dir")
    if not decl or not state_dir:
        return (False, "")
    sid_tok = _fresh_session_token(ctx)
    # 앵커를 마커보다 *먼저* 확보한다 — 세션 첫 도구가 오버레이 읽기일 때 앵커(나중 생성)가 마커보다
    # 새로워져 게이트가 오탐하는 것을 막는다.
    _fresh_anchor_mtime(state_dir, sid_tok)
    vals = _overlay_strings(ctx.get("tool_input"))
    if not vals:
        return (False, "")
    cwd = ctx.get("cwd")
    for abs_p, tail in decl["targets"]:
        if _overlay_hit(abs_p, tail, vals, cwd):
            try:
                _touch(_overlay_marker(state_dir, sid_tok, tail))
            except Exception:
                pass
    return (False, "")


def check_overlay_consulted_before_work(ctx):
    """(게이트) 작업 아이템 개시(디스패치) 시점에 이번 재무장 창 안의 오버레이 읽기 마커가 없으면 위반.
    선언 부재·state_dir 부재·대상 파일 전무·앵커 확보 실패 → 조용히 no-op(degraded-safe)."""
    decl = _overlay_decl(ctx)
    state_dir = ctx.get("state_dir")
    if not decl or not state_dir:
        return (False, "")
    sid_tok = _fresh_session_token(ctx)
    anchor = _fresh_anchor_mtime(state_dir, sid_tok)
    if anchor is None:
        return (False, "")  # 앵커 확보 실패 → 판정 보류(오탐 방지)
    deadline = anchor
    epoch = _fresh_rearm_epoch(state_dir, sid_tok)
    if epoch > 0:
        deadline = max(deadline, epoch - decl["grace"])
    missing = []
    for abs_p, tail in decl["targets"]:
        at = _mtime_or_none(_overlay_marker(state_dir, sid_tok, tail))
        if at is None or at < deadline:
            missing.append(abs_p)
    if not missing:
        return (False, "")
    return (True, "작업 아이템을 개시(위임)하려 하는데 이번 작업에서 사용자 오버레이를 참조하지 "
                  "않았습니다 — 미참조: %s. 위임 전에 이 진입점부터 읽으세요(개별 상세 파일은 "
                  "인덱스를 보고 필요한 것만). 훅은 대신 읽어 주지 않고 참조 여부만 검사합니다 "
                  "(specs/INVARIANT-ENFORCEMENT.md §15)." % ", ".join(missing))


# ---------------------------------------------------------------------------
# 서브에이전트 역할 계약 (role-tools-match-on-dispatch — v2 가산 · §16)
#   카탈로그(역할별 도구·티어의 단일 원천)와 탐색 스텁 프론트매터가 *지금 이 위임에서* 일치하는지
#   위임 직전(PreToolUse)에 대조한다. CHECK 경로는 읽기 전용 — 프론트매터를 고쳐 주지 않는다.
#   엔진엔 역할 이름·도구 이름·티어 값이 하나도 박혀 있지 않다(전부 선언·카탈로그에서 온다).
# ---------------------------------------------------------------------------
_ROLE_DEFAULT_CATALOG = "subagents/CATALOG.md"
_ROLE_DEFAULT_STUB = os.path.join(".claude", "agents", "dlc-role.md").replace("\\", "/")
# 위임 지시에서 역할 이름을 꺼내는 기본 표기. options.subagent_role.role_pattern 으로 교체 가능.
_ROLE_DEFAULT_PATTERN = (r"(?:^|[\s(\[|,])(?:role|\uc5ed\ud560)\s*[:=]\s*"
                         r"[`\"']?([A-Za-z0-9][A-Za-z0-9._-]{0,63})")
_ROLE_ANY_TOOLS = "*"       # 카탈로그의 "전체 도구" 표기 → 스텁은 tools: 줄 자체를 생략해야 한다


def _role_opts(ctx):
    """선언 options.subagent_role 를 반환. 부재면 None → 조용히 SKIP(이 개념이 없는 배포에서 no-op)."""
    inv = ctx.get("inv")
    opts = inv.get("options") if isinstance(inv, dict) else None
    sr = opts.get("subagent_role") if isinstance(opts, dict) else None
    return sr if isinstance(sr, dict) else None


def _role_resolve(path, bases):
    """상대 경로를 후보 base 들에 대해 해석해 *처음 존재하는* 파일을 돌려준다. 없으면 None."""
    if not isinstance(path, str) or not path.strip():
        return None
    q = path.strip().replace("\\", "/")
    try:
        if os.path.isabs(q):
            return os.path.abspath(q) if os.path.isfile(q) else None
        parts = [x for x in q.split("/") if x not in ("", ".")]
        if ".." in parts:
            return None
        for b in bases:
            if not b:
                continue
            cand = os.path.abspath(os.path.join(b, *parts))
            if os.path.isfile(cand):
                return cand
    except Exception:
        return None
    return None


def _role_tool_set(spec):
    """도구 표기 문자열 → 정규화 집합. "*" 는 None(=전체)로, 빈 값은 빈 집합으로."""
    if spec is None:
        return set()
    txt = str(spec).strip().strip("`").strip()
    if not txt:
        return set()
    if txt == _ROLE_ANY_TOOLS:
        return None                     # None = 제한 없음(전체)
    out = set()
    for tok in re.split(r"[,\s]+", txt):
        t = tok.strip().strip("`").strip()
        if t:
            out.add(t)
    return out


def _role_parse_catalog(path):
    """카탈로그 마크다운 표를 파싱 → {역할: {"file":…, "tools":…, "tier":…}}.
    컬럼 순서 계약: 역할 | 정의 파일 | 도구 | 티어 | 설명 (§16 — 순서 변경은 계약 버전 변경).
    정의 파일 셀이 .md 로 끝나는 행만 취한다 → 헤더·구분줄·설명 표가 자연히 걸러진다.
    파싱 실패·행 0개 → 빈 dict (호출부가 조용히 SKIP)."""
    text = _read_text(path)
    if not text:
        return {}
    rows = {}
    for line in text.split("\n"):
        ln = line.strip()
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) < 4:
            continue
        name = cells[0].strip().strip("`").strip()
        fcell = cells[1].strip().strip("`").strip()
        if not name or not fcell.lower().endswith(".md"):
            continue
        if ".." in fcell.replace("\\", "/").split("/"):
            continue
        rows[name] = {"file": fcell,
                      "tools": cells[2].strip().strip("`").strip(),
                      "tier": cells[3].strip().strip("`").strip()}
    return rows


def _role_frontmatter(path):
    """스텁 프론트매터 파싱 → dict. 첫 바이트가 '---' 가 아니거나 닫는 '---' 가 없으면 None."""
    text = _read_text(path)
    if not text:
        return None
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return None
    m = re.match(r"---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).split("\n"):
        ln = line.strip()
        if not ln or ln.startswith("#"):
            continue
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", ln)
        if not km:
            continue
        fm[km.group(1)] = km.group(2).strip()
    return fm


def _role_requested(ctx, sr):
    """위임 지시에서 역할 이름을 꺼낸다. tool_input 의 문자열 값 전체를 훑어 약속된 표기를 찾는다.
    못 찾으면 None → 호출부가 정책에 따라 처리(기본 SKIP)."""
    pat = sr.get("role_pattern") if isinstance(sr, dict) else None
    if not isinstance(pat, str) or not pat.strip():
        pat = _ROLE_DEFAULT_PATTERN
    try:
        rx = re.compile(pat, re.M)
    except Exception:
        return None
    for v in _overlay_strings(ctx.get("tool_input")):   # 문자열 값 수집기를 재사용(중첩 1단계까지)
        try:
            mm = rx.search(v)
        except Exception:
            continue
        if mm and mm.groups():
            g = mm.group(1)
            if isinstance(g, str) and g.strip():
                return g.strip()
    return None


def _role_targets_stub(ctx, sr):
    """이번 위임이 *탐색 스텁* 을 겨냥하는지. options.subagent_role.stub_agent 미선언이면 None
    (판단 불가 → 호출부가 SKIP 쪽으로 기운다)."""
    name = sr.get("stub_agent")
    if not isinstance(name, str) or not name.strip():
        return None
    name = name.strip()
    for v in _overlay_strings(ctx.get("tool_input")):
        if v.strip() == name:
            return True
        if name in [t for t in re.split(r"[^A-Za-z0-9._-]+", v) if t]:
            return True
    return False


def check_role_tools_match_on_dispatch(ctx):
    """(게이트) 위임 직전 — 카탈로그의 그 역할 행과 탐색 스텁 프론트매터가 어긋나면 위반.

    조용히 SKIP 하는 경우(전부 degraded-safe · exit 0 무출력):
      - options.subagent_role 미선언 (이 개념을 쓰지 않는 배포)
      - 카탈로그 파일 없음 / 파싱 결과 행 0개
      - 스텁 파일 없음 / 프론트매터 파싱 실패
      - 지시에서 역할 이름을 못 찾았고, 이번 위임이 스텁을 겨냥한다고 단정할 수 없음
    """
    sr = _role_opts(ctx)
    if not sr:
        return (False, "")
    cwd = ctx.get("cwd") or os.getcwd()
    cat_path = _role_resolve(sr.get("catalog") or _ROLE_DEFAULT_CATALOG,
                             [ctx.get("base_dir"), ctx.get("log_dir"), cwd])
    if not cat_path:
        return (False, "")
    rows = _role_parse_catalog(cat_path)
    if not rows:
        return (False, "")
    stub_path = _role_resolve(sr.get("stub") or _ROLE_DEFAULT_STUB,
                              [cwd, ctx.get("base_dir"), ctx.get("log_dir")])
    if not stub_path:
        return (False, "")
    fm = _role_frontmatter(stub_path)
    if fm is None:
        return (False, "")

    role = _role_requested(ctx, sr)
    if not role:
        # 역할 이름이 지시에 없다. 이번 위임이 *스텁을 겨냥한다고 확인될 때만* 위반으로 본다 —
        # 다른 서브 타입을 부르는 배포에서 매 위임마다 뜨지 않게 하기 위함이다(오탐 억제).
        if _role_targets_stub(ctx, sr) is True:
            return (True, "탐색 스텁(%s)에 위임하면서 지시에 역할 이름이 없습니다 — 지시에 "
                          "`role: <역할 이름>` 을 명시하세요. 스텁은 역할을 추측하지 않고 멈춥니다 "
                          "(specs/INVARIANT-ENFORCEMENT.md 16)." % (fm.get("name") or stub_path))
        return (False, "")

    row = rows.get(role)
    if row is None:
        return (True, "역할 %r 이 카탈로그(%s)에 없습니다 — 위임 전에 역할 정의 md 를 만들고 "
                      "카탈로그에 한 줄을 더하세요(ROUTING.md 4.3 (b)). 카탈로그에 없는 역할은 "
                      "스텁이 해석하지 못하고 멈춥니다." % (role, cat_path))

    problems = []
    want = _role_tool_set(row.get("tools"))
    have = _role_tool_set(fm.get("tools")) if "tools" in fm else None
    if want is None and have is not None:
        problems.append("도구: 카탈로그는 전체(%s)인데 프론트매터가 %s 로 좁혀져 있습니다 "
                        "— `tools:` 줄을 생략하세요" % (_ROLE_ANY_TOOLS, sorted(have)))
    elif want is not None and have is None:
        problems.append("도구: 카탈로그는 %s 인데 프론트매터에 `tools:` 가 없습니다(= 전체 도구) "
                        "— 이 역할에 필요 없는 도구가 딸려 갑니다" % sorted(want))
    elif want is not None and have is not None and want != have:
        bits = []
        extra = sorted(have - want)
        missing = sorted(want - have)
        if extra:
            bits.append("과다 %s" % extra)
        if missing:
            bits.append("부족 %s" % missing)
        problems.append("도구 불일치(%s): 카탈로그 %s vs 프론트매터 %s"
                        % (", ".join(bits), sorted(want), sorted(have)))

    # 티어→모델 확인은 *선언이 매핑을 줄 때만* 한다 — 엔진은 모델 이름을 모른다(중립).
    tier_models = sr.get("tier_models")
    if isinstance(tier_models, dict) and row.get("tier"):
        expect = tier_models.get(row["tier"])
        if isinstance(expect, str) and expect.strip():
            got = fm.get("model")
            if got != expect.strip():
                problems.append("모델: 카탈로그 티어 %r -> %r 인데 프론트매터는 %r"
                                % (row["tier"], expect.strip(), got))

    if not problems:
        return (False, "")
    return (True, "역할 %r 위임 준비가 카탈로그와 어긋납니다 — %s. 위임 *전에* 카탈로그(%s)를 보고 "
                  "%s 의 프론트매터를 채우세요(ROUTING.md 4.3 (c)). 훅은 대신 고쳐 주지 않고 "
                  "대조만 합니다 — 어긋난 채 스폰하면 그 역할이 쓰지 말아야 할 도구를 쥡니다 "
                  "(specs/INVARIANT-ENFORCEMENT.md 16)."
                  % (role, " / ".join(problems), cat_path, stub_path))


CHECKS = {
    # 전역 파일럿 (v1 — 유지)
    "open-cycle-record-exists": check_open_cycle_record_exists,
    "no-stale-open-cycle": check_no_stale_open_cycle,
    # 키드 per-work-item (v2 — 신규, §13.5)
    "keyed-record-on-dispatch": check_keyed_record_on_dispatch,
    "keyed-valid-status-transition": check_keyed_valid_status_transition,
    "keyed-log-on-done": check_keyed_log_on_done,
    # git 최신성 (v2 가산 — §14)
    "repo-fresh-before-access": check_repo_fresh_before_access,
    # 사용자 오버레이 참조 (v2 가산 — §15). 관찰(PostToolUse)과 게이트(PreToolUse)가 짝.
    "overlay-read-observe": check_overlay_read_observe,
    "overlay-consulted-before-work": check_overlay_consulted_before_work,
    # 서브에이전트 역할 계약 (v2 가산 — §16)
    "role-tools-match-on-dispatch": check_role_tools_match_on_dispatch,
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


def evaluate(event, tool_name, tool_input, invariants, log_dir, state_dir=None, work_key=None,
             cwd=None, session_id=None, base_dir=None, overlay_user=None):
    """위반된 (tier, message) 목록 반환. 체크에 넘길 컨텍스트(ctx)를 한 번 구성해 전달한다
    (§13.6-6 — 전역 체크와 키드 체크가 같은 ctx 를 받는다). §14 최신성 체크가 tool_input·cwd·
    session_id 를, §15 오버레이 체크가 base_dir·overlay_user 를 쓰므로 ctx 에 함께 싣는다
    (기존 체크는 여분 키를 무시한다 — 무회귀)."""
    ctx = {"log_dir": log_dir, "state_dir": state_dir, "work_key": work_key,
           "tool_name": tool_name, "tool_input": tool_input, "cwd": cwd, "session_id": session_id,
           "base_dir": base_dir or log_dir, "overlay_user": overlay_user}
    findings = []
    for inv in invariants:
        if not _requires_met(inv, ctx):
            continue
        # 평가 중인 불변식 선언 자체를 ctx 에 싣는다 — 체크가 자기 options 를 읽을 수 있게(§14.8).
        # 여분 키라 기존 체크는 무시한다(무회귀). 순차 평가이므로 덮어쓰기 안전.
        ctx["inv"] = inv
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
def _sub_emit(ok, message, record=None, exit_code=0, extra=None):
    out = {"ok": ok, "message": message}
    if record is not None:
        out["record"] = record
    if isinstance(extra, dict):
        for k, v in extra.items():      # 가산 필드만 — 기존 키(ok/message/record)는 덮지 않는다.
            out.setdefault(k, v)
    _emit_write(out)
    return exit_code


def _rearm_repo_scan(state_dir, session_id=None):
    """§14.8 재무장 — *작업 아이템 개시*를 git 최신성 재판정 지점으로 만든다.

    왜 여기(write-helper)인가: 이건 *쓰기*다. CHECK 경로(--event)는 읽기 전용이라는 §13.4 Q4=B
    경계를 지켜, epoch 쓰기는 쓰기 진입점인 record 서브커맨드에 둔다. (CHECK 경로가 계속
    touch 하는 것은 도입판부터 그래 왔던 자기 전용 ephemeral 마커 — 세션 앵커와 fired 마커 —
    뿐이며, 키드 work-item 레코드·active 포인터는 여전히 건드리지 않는다.)

    구현은 *epoch 파일 하나를 touch* 하는 것뿐이다 — fired 마커를 지우고 다니지 않는다.
    체크가 'fired 마커의 mtime >= epoch' 일 때만 억제하므로, epoch 를 앞으로 미는 것만으로
    이전 창의 마커 전부가 한 번에 무효화된다(원자적·스캔 불필요·다른 워커 파일 무간섭).

    스코프: session_id 를 알면 그 세션만(정밀), 모르면 글로벌 파일(이 state_dir 의 모든 세션이
    재판정 — 덜 검사하는 쪽으로 기울지 않는 안전 방향 폴백).
    실패해도 절대 예외를 올리지 않는다 — 재무장은 record 의 부가 효과이지 전제가 아니다."""
    if not state_dir:
        return None
    sid = _sanitize_key(session_id) or _sanitize_key(os.environ.get("AIDLC_SESSION_ID"))
    name = ("reposcan-" + sid + ".rearm") if sid else "reposcan.rearm"
    path = os.path.join(state_dir, name)
    try:
        _touch(path)
        return path
    except Exception:
        return None


def _apply_write(state_dir, key, status, fields, require_existing, extra=None):
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
    return _sub_emit(True, "recorded %r status=%s" % (key, status), record=rec, exit_code=0,
                     extra=extra)


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
            # 작업 아이템 개시 = §14.8 최신성 재무장 지점. 레코드 쓰기 *전에* 찍는다 — 재무장은
            # 멱등이고, 설령 뒤의 record 가 거부돼도 결과는 '한 번 더 검사'(안전 방향)뿐이다.
            rearmed = _rearm_repo_scan(state_dir, _parse_opt(argv, "session-id"))
            return _apply_write(state_dir, key,
                                _parse_opt(argv, "status"),
                                _collect_fields(argv), require_existing=False,
                                extra={"rearmed": rearmed})
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
    # cwd 는 §14 최신성 체크가 파일 경로 없는 도구(Bash/PowerShell)의 접근 레포를 유도할 때 쓴다.
    cwd = data.get("cwd") if isinstance(data, dict) else None
    # 키 해석: --work-key/AIDLC_WORK_KEY > active-포인터 > 없음(키드 체크 no-op).
    work_key = _resolve_work_key(_parse_opt(argv, "work-key"), state_dir, session_id)
    # §15 오버레이 사용자 식별자 — CLI > env > 선언(options.overlay.user). 미해소면 그 체크만 SKIP.
    #   배포별(머신·사람별) 값이라 팀 공유 yaml 이 아니라 *훅 명령 인자*가 1차 채널이다(--base-dir 와 같은 사상).
    overlay_user = _parse_opt(argv, "overlay-user")
    # Stop-block 무한루프 가드용 신호 — 재진입한 Stop 훅이면 하네스가 true 로 실어 준다.
    # 깨지거나 없으면 False(=미재진입)로 안전 처리 (degraded-safe).
    stop_hook_active = bool(data.get("stop_hook_active")) if isinstance(data, dict) else False
    code = 0
    try:
        invs = load_invariants(invariants_dir)
        findings = evaluate(event, tool_name, tool_input, invs, log_dir, state_dir, work_key,
                            cwd, session_id, base_dir_arg or log_dir, overlay_user)
        out, code = emit(event, findings, stop_hook_active)
    except Exception:
        out, code = None, 0  # 무엇이 어긋나도 조용히 통과 (EX-15 / C FALLBACK)
    if out is not None:
        _emit_write(out)  # JSON 을 먼저 쓴다 (block 이면 그 뒤 exit 2). reconfigure 불가 런타임도 버퍼 바이트로 안전
    return code


if __name__ == "__main__":
    sys.exit(main())

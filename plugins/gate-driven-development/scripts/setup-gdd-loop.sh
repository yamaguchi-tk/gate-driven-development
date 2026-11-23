#!/usr/bin/env bash
set -euo pipefail

SESSION_ID="${CLAUDE_CODE_SESSION_ID:-}"
USER_INTENT="${*:-}"
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GDD_RUNTIME="${GDD_RUNTIME:-}"
PYTHON_BIN=""
PROJECT_ROOT="$(pwd)"

for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$cmd"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "gdd loop requires python3 or python to be available." >&2
  exit 1
fi

# CLAUDE_CODE_SESSION_ID can be inherited by Cursor (or any shell opened
# from a Claude Code parent process), causing a false "claude_code" runtime
# detection. Walk the process tree to find the actual calling runtime first,
# and only fall back to the env-var heuristic if the tree gives no answer.
_detected_runtime=""
_pid=$$
_depth=0
while [[ "$_pid" -gt 1 && "$_depth" -lt 15 ]]; do
  _cmd=$(ps -p "$_pid" -o comm= 2>/dev/null | LC_ALL=C tr '[:upper:]' '[:lower:]' || echo "")
  if [[ "$_cmd" == *"cursor"* ]]; then
    _detected_runtime="cursor"
    break
  elif [[ "$_cmd" == *"claude"* ]]; then
    _detected_runtime="claude_code"
    break
  fi
  _ppid=$(ps -p "$_pid" -o ppid= 2>/dev/null | tr -d ' ' || echo "1")
  [[ "$_ppid" == "$_pid" || -z "$_ppid" ]] && break
  _pid="$_ppid"
  _depth=$((_depth + 1))
done

if [[ -z "$GDD_RUNTIME" ]]; then
  if [[ -n "$_detected_runtime" ]]; then
    GDD_RUNTIME="$_detected_runtime"
  elif [[ -n "$SESSION_ID" ]]; then
    # Fallback: trust CLAUDE_CODE_SESSION_ID when process tree gives no signal
    GDD_RUNTIME="claude_code"
  else
    GDD_RUNTIME="cursor"
  fi
fi

# Claude Code では、main のセッションが Sonnet・Haiku なら GDD を始めない（判定は hooks/scripts/lib/main_model_gate.py）。
# この script を実行した返事のモデルで判定するので、どう包んで実行しても判定され、読むだけでは判定されない。
# 止めるときは 3 で返り、止める文を stderr に出して 1 で終わる。判定できないときは止めない。
# runtime は GDD_RUNTIME の値ではなく、process tree の判定（無ければ session id の有無）で決める。
# GDD_RUNTIME をコマンドの前に付けて判定を外せないようにするため。
_gate_runtime="$_detected_runtime"
[[ -z "$_gate_runtime" && -n "$SESSION_ID" ]] && _gate_runtime="claude_code"
if [[ "$_gate_runtime" == "claude_code" ]]; then
  _gate_rc=0
  "$PYTHON_BIN" -I "$PLUGIN_ROOT/hooks/scripts/lib/main_model_gate.py" --setup || _gate_rc=$?
  if [[ "$_gate_rc" -eq 3 ]]; then
    exit 1
  fi
fi

if command -v git >/dev/null 2>&1; then
  if GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    PROJECT_ROOT="$GIT_ROOT"
  fi
fi

# marker に書く project_root（JSON 文字列）。git の toplevel を末尾の改行 1 つだけ落として読み、
# PROJECT_ROOT と同じときだけ使う。git が無い・失敗する・パスに改行を含むなら空にする（写しの判定をしない）。
PROJECT_ROOT_JSON="$(
  "$PYTHON_BIN" - "$PROJECT_ROOT" <<'PY'
import json
import subprocess
import sys

try:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
except OSError:
    sys.exit(0)
value = out.stdout[:-1] if out.stdout.endswith("\n") else ""
if out.returncode == 0 and value and value == sys.argv[1] and not any(c in value for c in "\n\r"):
    print(json.dumps(value))
PY
)"

STATE_DIR="${PROJECT_ROOT}/.claude"
STATE_FILE="${STATE_DIR}/gdd-dev.local.md"
LOCK_DIR="${STATE_DIR}/.gdd-lock"

mkdir -p "$STATE_DIR"

# Atomic lock using mkdir (POSIX-portable, works on macOS and Linux)
acquire_lock() {
  local max_attempts=10
  local attempt=0
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [[ $attempt -ge $max_attempts ]]; then
      # Check if lock is stale (older than 5 minutes)
      if [[ -d "$LOCK_DIR" ]]; then
        local lock_age
        if [[ "$(uname -s)" == "Darwin" ]]; then
          lock_age=$(( $(date +%s) - $(stat -f %m "$LOCK_DIR") ))
        else
          lock_age=$(( $(date +%s) - $(stat -c %Y "$LOCK_DIR") ))
        fi
        if [[ $lock_age -gt 300 ]]; then
          echo "Removing stale lock (age: ${lock_age}s)" >&2
          rmdir "$LOCK_DIR" 2>/dev/null || true
          continue
        fi
      fi
      echo "Failed to acquire gdd lock after ${max_attempts} attempts." >&2
      echo "Lock dir: $LOCK_DIR" >&2
      echo "Another gdd session may be initializing. Remove $LOCK_DIR if stale." >&2
      exit 1
    fi
    sleep 0.5
  done
}

release_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

trap release_lock EXIT

acquire_lock

RECOMMENDED_MODEL="$(
  "$PYTHON_BIN" "$PLUGIN_ROOT/scripts/resolve-gdd-model.py" \
    --runtime "$GDD_RUNTIME" \
    --phase gdd-brainstorming \
    --text "$USER_INTENT"
)"

if [[ -f "$STATE_FILE" ]]; then
  EXISTING_STATE="$(
    "$PYTHON_BIN" - "$STATE_FILE" "$PROJECT_ROOT_JSON" <<'PY'
import json
import os
import pathlib
import stat
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
active = ""
session_id = ""
for line in text.splitlines():
    if active and session_id:
        break
    line = line.split("#", 1)[0]
    if not active and line.startswith("active:"):
        active = line.split(":", 1)[1].strip().lower()
    elif not session_id and line.startswith("session_id:"):
        session_id = line.split(":", 1)[1].strip()


def copied_from() -> str:
    """別の checkout から写された marker なら、その project_root（JSON）を返す。
    次を全部満たすときだけ。それ以外と、stat の失敗は空（ロック）
    - frontmatter の project_root がちょうど 1 行の JSON 文字列で、今の toplevel と一致しない
    - その値が絶対パスで、実在するディレクトリを指し、今の toplevel と別の実体（st_dev・st_ino）である
      （checkout を動かした後の旧パスや、同じ checkout を別の文字列で指す値を写しとみなさない）
    - marker が symlink を通らずに今の toplevel の下にあり、hardlink でない
      （上書きで持ち主の marker を書き換えない）"""
    if not sys.argv[2]:
        return ""
    current = json.loads(sys.argv[2])
    lines = text.split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        return ""
    frontmatter = lines[1 : lines.index("---", 1)]
    values = [line for line in frontmatter if line.startswith("project_root:")]
    if len(values) != 1:
        return ""
    try:
        recorded = json.loads(values[0].split(":", 1)[1].strip())
    except ValueError:
        return ""
    if not isinstance(recorded, str) or not os.path.isabs(recorded) or recorded == current:
        return ""
    try:
        if path.is_symlink() or path.parent.is_symlink():
            return ""
        if os.path.realpath(path) != os.path.join(current, ".claude", "gdd-dev.local.md"):
            return ""
        if os.lstat(path).st_nlink != 1:
            return ""
        other = os.stat(recorded)
        here = os.stat(current)
    except (OSError, ValueError):
        return ""
    if not stat.S_ISDIR(other.st_mode) or (other.st_dev, other.st_ino) == (here.st_dev, here.st_ino):
        return ""
    return json.dumps(recorded)


# 写しの欄を先頭に置く（JSON は生の tab を含まないので、session_id の中身で区切りがずれない）
print(f"{copied_from()}\t{active}\t{session_id}")
PY
  )"
  EXISTING_COPIED_FROM="${EXISTING_STATE%%$'\t'*}"
  EXISTING_STATE="${EXISTING_STATE#*$'\t'}"
  EXISTING_ACTIVE="${EXISTING_STATE%%$'\t'*}"
  EXISTING_SESSION="${EXISTING_STATE#*$'\t'}"
  # active: false の state file はロック対象外（stale marker を手動 disable した場合を尊重する）
  # 別の checkout から写された marker（worktree の作成で root の .claude/ が写される）もロックにせず上書きする
  if [[ "$EXISTING_ACTIVE" == "true" ]] && [[ -n "$EXISTING_SESSION" ]] && [[ -n "$SESSION_ID" ]] && [[ "$EXISTING_SESSION" != "$SESSION_ID" ]] && [[ -n "$EXISTING_COPIED_FROM" ]]; then
    echo "Ignoring a gdd state file copied from another checkout; overwriting it." >&2
    echo "State file: $STATE_FILE" >&2
    echo "Recorded project_root: ${EXISTING_COPIED_FROM}" >&2
    echo "Existing session: ${EXISTING_SESSION}" >&2
  elif [[ "$EXISTING_ACTIVE" == "true" ]] && [[ -n "$EXISTING_SESSION" ]] && [[ -n "$SESSION_ID" ]] && [[ "$EXISTING_SESSION" != "$SESSION_ID" ]]; then
    echo "gdd loop is already active in another session." >&2
    echo "State file: $STATE_FILE" >&2
    echo "Current session: ${SESSION_ID}" >&2
    echo "Existing session: ${EXISTING_SESSION}" >&2
    # 持ち主がまだ動いているかを聞く材料として、Claude Code の transcript の最後の記録の時刻を出す。
    # ロックの判定には使わない。確かに読めないときは unknown
    OWNER_LAST_ACTIVE="$(
      "$PYTHON_BIN" - "$EXISTING_SESSION" "$STATE_FILE" <<'PY'
import datetime
import json
import os
import pathlib
import re
import sys

TAIL_BYTES = 1024 * 1024
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z")


def last_active() -> str:
    session_id = sys.argv[1]
    # glob・パスの文字を含む値で、別の session の transcript に当てない
    if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
        return "unknown"
    base = os.environ.get("CLAUDE_CONFIG_DIR") or ""
    if not base and os.environ.get("HOME"):
        base = os.path.join(os.environ["HOME"], ".claude")
    if not base:
        return "unknown"
    latest = None
    for project in (pathlib.Path(base) / "projects").iterdir():
        path = project / f"{session_id}.jsonl"
        try:
            if not path.is_file():
                continue
            with path.open("rb") as handle:
                start = max(0, handle.seek(0, 2) - TAIL_BYTES)
                handle.seek(start)
                # 行は \n だけで分ける（splitlines は U+2028 などでも分け、その記録を読み落とす）
                lines = handle.read().decode("utf-8", "replace").split("\n")
        except OSError:
            continue
        # 途中から読んだときは、最初の切れた行を捨てる
        for line in lines[1:] if start else lines:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            # 記録の top-level の timestamp だけを使う（入れ子の値は記録の時刻ではない）
            value = record.get("timestamp") if isinstance(record, dict) else None
            if not isinstance(value, str) or not TIMESTAMP.fullmatch(value):
                continue
            try:
                seen = datetime.datetime.fromisoformat(value[:19] + "+00:00")
            except ValueError:
                continue
            # 同じ秒の中は、秒の下の桁で比べる
            key = (seen, value[20:-1].ljust(9, "0"))
            if latest is None or key > latest[0]:
                latest = (key, value)
    if latest is None:
        return "unknown"
    seconds = (datetime.datetime.now(datetime.timezone.utc) - latest[0][0]).total_seconds()
    if seconds < 0:
        ago = "in the future"
    elif seconds < 3600:
        ago = f"{int(seconds // 60)}m ago"
    else:
        ago = f"{int(seconds // 3600)}h ago"
    local = latest[0][0].astimezone().strftime("%Y-%m-%d %H:%M %Z")
    return f"{latest[1]} ({ago}; local time {local})"


def started_at() -> str:
    """state の frontmatter の started_at（transcript から時刻が取れないときに、下限として添える）。"""
    try:
        lines = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace").split("\n")
    except (OSError, IndexError):
        return ""
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return ""
    values = [line.split(":", 1)[1].strip().strip('"') for line in lines[1 : lines.index("---", 1)]
              if line.startswith("started_at:")]
    return values[0] if len(values) == 1 and TIMESTAMP.fullmatch(values[0]) else ""


try:
    shown = last_active()
except Exception:
    shown = "unknown"
if shown == "unknown":
    try:
        lower = started_at()
    except Exception:
        lower = ""
    if lower:
        shown = f"unknown (state started_at: {lower}; active at least since then)"
print(shown)
PY
    )" || OWNER_LAST_ACTIVE="unknown"
    echo "Existing session last active: ${OWNER_LAST_ACTIVE:-unknown}" >&2
    echo "To continue: ask the user whether the existing session is still running, and show them the 'Existing session last active' line. If it is not, set the 'active:' line in the state file to false and run this script again." >&2
    echo "Do not rewrite session_id." >&2
    exit 1
  fi
fi

# shellcheck source=../hooks/scripts/lib/classify-intent.sh
source "$PLUGIN_ROOT/hooks/scripts/lib/classify-intent.sh"

USER_INTENT_CLASS="$(gdd_classify_intent "$USER_INTENT")"
SHOULD_DISCOVER_RESUME_CANDIDATES=false
if [[ "$USER_INTENT_CLASS" == "resume" || -z "${USER_INTENT//[[:space:]]/}" ]]; then
  SHOULD_DISCOVER_RESUME_CANDIDATES=true
fi

STEERING_CANDIDATES=""
STEERING_CANDIDATE_COUNT=0
WORKTREE_POLLUTION_WARNINGS=""
WORKTREE_POLLUTION_WARNING_COUNT=0
if [[ "$SHOULD_DISCOVER_RESUME_CANDIDATES" == "true" ]] && command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  POLLUTION_FILE="$(mktemp)"
  STEERING_CANDIDATES="$(
    "$PYTHON_BIN" - "$PROJECT_ROOT" "$POLLUTION_FILE" <<'PY'
import pathlib
import sys

project_root = pathlib.Path(sys.argv[1])
pollution_file = pathlib.Path(sys.argv[2])
terminal = {"done", "cancelled"}
candidates = []
polluted = []
base_kinds_seen = set()

# Enumerate worktrees via git
import subprocess
result = subprocess.run(
    ["git", "worktree", "list", "--porcelain"],
    capture_output=True, text=True, cwd=str(project_root)
)
worktrees = []
current = None
for line in result.stdout.splitlines():
    if line.startswith("worktree "):
        if current is not None:
            worktrees.append(current)
        current = {"path": pathlib.Path(line.split(" ", 1)[1]), "branch": ""}
    elif current is not None and line.startswith("branch "):
        ref = line.split(" ", 1)[1].strip()
        if ref.startswith("refs/heads/"):
            ref = ref[len("refs/heads/"):]
        current["branch"] = ref
if current is not None:
    worktrees.append(current)

# Also include project root if not already in worktree list
if project_root.resolve() not in [entry["path"].resolve() for entry in worktrees]:
    branch_result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True, cwd=str(project_root)
    )
    worktrees.insert(0, {"path": project_root, "branch": branch_result.stdout.strip()})

# この heredoc は $( ... ) の中にあり、bash は heredoc 内でも backtick を
# ペアとして数える。リテラルの backtick を奇数個書くと command substitution の
# パースが壊れて "unexpected EOF" になるため、chr(96) で表現する。
BACKTICK = chr(96)

def normalize_line(line):
    # canonical field 行は行頭から始まる。インデント行は入れ子 bullet の履歴メモ /
    # コードブロック内の記入例なので field として読まない
    # (tests/test_canonical_field_line_anchoring_contract.py が正本)。
    if line[:1] in (" ", "\t"):
        return ""
    stripped = line.strip()
    # bullet marker は 1 個 + 空白まで許容する
    if stripped[:1] in ("-", "*", "+") and stripped[1:2] in (" ", "\t"):
        stripped = stripped[2:].strip()
    if stripped.startswith(BACKTICK) and stripped.endswith(BACKTICK):
        stripped = stripped[1:-1].strip()
    return stripped

def strip_fenced_blocks(text):
    """fence 内の行を落とす。閉じ忘れは未閉鎖の開き fence 以降だけを残す。

    規約の正本は hooks/scripts/lib/tasklist_parse.strip_fenced_blocks（記号種別・
    長さ・インデント・閉じ忘れの救済範囲）。この script は plugin 外からも単体実行
    されるため import せず同じ規約を実装する。定義が 1 関数で自足するのは、契約
    テストが def 単位で抽出して同じ表に掛けるため。

    閉じ忘れ時に本文を丸ごと返すと、それ以前の正しく閉じた記入例まで復活し、
    閉じ忘れ 1 つで「記入例が現在値として読まれる」欠陥が全面的に開く。
    """
    import re

    backtick = chr(96)
    fence_re = re.compile(r"^[ \t]*(?P<marker>" + backtick + "{3,}|~{3,})(?P<info>.*)$")
    lines = text.splitlines()
    closed = set()
    marker = ""
    open_at = -1
    for i, line in enumerate(lines):
        m = fence_re.match(line)
        if marker:
            if (m and m.group("marker")[0] == marker[0]
                    and len(m.group("marker")) >= len(marker)
                    and not m.group("info").strip()):
                closed.update(range(open_at, i + 1))
                marker = ""
                open_at = -1
            continue
        if m:
            if m.group("marker")[0] == backtick and backtick in m.group("info"):
                continue
            marker = m.group("marker")
            open_at = i
    return "\n".join(line for i, line in enumerate(lines) if i not in closed)

def parse_field(text, names):
    # 値側の backtick も落とす。残すと "done" が terminal 判定に、
    # "gdd/foo" が git branch 比較に一致せず、無言で誤分類する。
    # fenced code block の中は書式の記入例であって現在値ではない。規約の正本は
    # hooks/scripts/lib/tasklist_parse.strip_fenced_blocks（記号種別・長さ・閉じ忘れ）。
    # この script は plugin 外からも単体実行されるため import せず同じ規約を実装する。
    for fline in strip_fenced_blocks(text).splitlines():
        stripped = normalize_line(fline)
        for name in names:
            if not stripped.lower().startswith(name.lower()):
                continue
            # field 名の直後は区切り文字でなければならない。ここを見ないと
            # `Task` が `Task Size: standard` に前方一致し、値として
            # `standard` を返す。他 4 実装（gdd_extract_doc_field /
            # validate-steering-write.py / gdd_task_binding.py /
            # collect-gdd-telemetry.py）はいずれも name + sep を要求しており、
            # ここだけが規約から外れていた。sep 前の空白は既存受理形
            # （`Next Action : done`）のため許容する。
            rest = stripped[len(name):].lstrip()
            if rest[:1] not in ("=", ":"):
                continue
            # 区切り文字の後ろが空の行は現在値ではない。書きかけの
            # `- Resume From:` が先頭にあるだけで後続の値付き行が見えなくなる（R-1）。
            value = rest[1:].strip().strip(BACKTICK).strip()
            if value:
                return value
            break  # この行はこの name で確定。値が空なら次の行へ進む
    return ""

def base_kind_for(wt):
    parts = wt.resolve().parts
    if ".gdd" in parts and "worktrees" in parts:
        return "gdd-managed"
    if ".worktrees" in parts:
        return "repo-local"
    if str(wt).startswith("/private/tmp/") or "/private/var/" in str(wt):
        return "host-managed"
    if wt.resolve() == project_root.resolve():
        return "repo-root"
    return "host-managed"

def is_dedicated_worktree(kind):
    return kind in {"gdd-managed", "repo-local"}

for entry in worktrees:
    wt = entry["path"]
    git_branch = entry["branch"]
    base_kind = base_kind_for(wt)
    steering_dir = wt / ".steering"
    if not steering_dir.is_dir():
        continue
    nonterminal_in_worktree = []
    for state_file in steering_dir.glob("*/state.md"):
        text = state_file.read_text(encoding="utf-8")
        resume_from = parse_field(text, ["Resume From"])
        next_action = parse_field(text, ["Next Action"])
        # Skip terminal states
        if resume_from in terminal or next_action in terminal:
            continue
        if next_action == "cancelled" or resume_from == "cancelled":
            continue

        task_name = state_file.parent.name
        state_task_id = parse_field(text, ["Task ID", "Steering ID", "Task"]) or task_name
        state_active_branch = parse_field(text, ["Active Branch"])
        reasons = []

        if is_dedicated_worktree(base_kind) and wt.name != task_name:
            reasons.append("path_slug_mismatch")
        if state_task_id != task_name:
            reasons.append("state_task_mismatch")
        if git_branch and task_name not in git_branch:
            reasons.append("branch_slug_mismatch")
        if state_active_branch and git_branch and state_active_branch != git_branch:
            reasons.append("active_branch_mismatch")

        record = {
            "path": f"{wt}/.steering/{task_name}",
            "worktree_path_slug": wt.name,
            "steering_slug": task_name,
            "state_task_id": state_task_id,
            "git_branch": git_branch or "<unknown>",
            "state_active_branch": state_active_branch or "<none>",
            "worktree_base_kind": base_kind,
            "reasons": reasons,
        }
        nonterminal_in_worktree.append(record)
        base_kinds_seen.add(base_kind)

    if len(nonterminal_in_worktree) >= 2:
        for record in nonterminal_in_worktree:
            if "multiple non-terminal steerings" not in record["reasons"]:
                record["reasons"].append("multiple non-terminal steerings")

    for record in nonterminal_in_worktree:
        if record["reasons"]:
            polluted.append(record)
        else:
            candidates.append(record["path"])

if len(base_kinds_seen) >= 2:
    polluted.append({
        "path": "<multiple>",
        "worktree_path_slug": "<multiple>",
        "steering_slug": "<multiple>",
        "state_task_id": "<multiple>",
        "git_branch": "<multiple>",
        "state_active_branch": "<multiple>",
        "worktree_base_kind": ",".join(sorted(base_kinds_seen)),
        "reasons": ["mixed worktree bases"],
    })
    candidates = []

if polluted:
    lines = []
    for record in polluted:
        reason_text = ",".join(record["reasons"])
        format_record = {key: value for key, value in record.items() if key != "reasons"}
        lines.append(
            "POLLUTED::{reasons}::{path}::worktree_path_slug={worktree_path_slug}::"
            "steering_slug={steering_slug}::state_task_id={state_task_id}::git_branch={git_branch}::"
            "state_active_branch={state_active_branch}::worktree_base_kind={worktree_base_kind}".format(
                reasons=reason_text,
                **format_record,
            )
        )
    pollution_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

for c in candidates:
    print(c)
PY
  )" || true
  WORKTREE_POLLUTION_WARNINGS="$(cat "$POLLUTION_FILE" 2>/dev/null || true)"
  rm -f "$POLLUTION_FILE"
  if [[ -n "$WORKTREE_POLLUTION_WARNINGS" ]]; then
    WORKTREE_POLLUTION_WARNING_COUNT="$(echo "$WORKTREE_POLLUTION_WARNINGS" | wc -l | tr -d ' ')"
    STEERING_CANDIDATES=""
  fi
  if [[ -n "$STEERING_CANDIDATES" ]]; then
    STEERING_CANDIDATE_COUNT="$(echo "$STEERING_CANDIDATES" | wc -l | tr -d ' ')"
  fi
fi

cat > "$STATE_FILE" <<'__GDD_STATE__'
---
active: true
iteration: 1
__GDD_STATE__

# 写された marker を見分けるため、書いた checkout の toplevel を残す（git の外では書かない）
if [[ -n "$PROJECT_ROOT_JSON" ]]; then
  printf 'project_root: %s\n' "$PROJECT_ROOT_JSON" >> "$STATE_FILE"
fi

# Append dynamic fields (variable expansion needed)
cat >> "$STATE_FILE" <<__GDD_DYNAMIC__
session_id: ${SESSION_ID}
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
workflow_runtime: ${GDD_RUNTIME}
detected_phase: gdd-brainstorming
recommended_model: ${RECOMMENDED_MODEL}
steering_candidate_count: ${STEERING_CANDIDATE_COUNT}
worktree_pollution_warning_count: ${WORKTREE_POLLUTION_WARNING_COUNT}
user_intent_class: ${USER_INTENT_CLASS}
---
Continue the active \`/gdd-dev\` run.

User intent: ${USER_INTENT:-<none>}
Intent classification: ${USER_INTENT_CLASS} (shell-level heuristic; brainstorming may refine)

Recommended model: ${RECOMMENDED_MODEL}
Steering candidates: ${STEERING_CANDIDATE_COUNT}
Worktree pollution warnings: ${WORKTREE_POLLUTION_WARNING_COUNT}
$(if [[ "$SHOULD_DISCOVER_RESUME_CANDIDATES" == "true" && "$STEERING_CANDIDATE_COUNT" -ge 2 ]]; then
    if [[ "$USER_INTENT_CLASS" == "new" ]]; then
      echo "ℹ Non-terminal steerings exist (${STEERING_CANDIDATE_COUNT}), but intent looks like a NEW task. Start a new steering — resume selection is not required unless the user explicitly uses resume cues (再開/続き/resume)."
      echo "  Existing non-terminal steerings (for reference only):"
      echo "$STEERING_CANDIDATES" | while IFS= read -r line; do echo "    - $line"; done
    elif [[ "$USER_INTENT_CLASS" == "resume" ]]; then
      echo "⚠ Resume intent detected with multiple active steerings. Explicit selection required:"
      echo "$STEERING_CANDIDATES" | while IFS= read -r line; do echo "  - $line"; done
    else
      echo "⚠ Multiple active steerings detected and intent is ambiguous. Ask the user whether to start new or resume (and which):"
      echo "$STEERING_CANDIDATES" | while IFS= read -r line; do echo "  - $line"; done
    fi
  fi)
$(if [[ -n "$WORKTREE_POLLUTION_WARNINGS" ]]; then
    echo "⚠ Worktree pollution detected. Do not auto-resume. Ask the user to choose cleanup / explicit resume / new worktree:"
    echo "$WORKTREE_POLLUTION_WARNINGS" | while IFS= read -r line; do echo "  - $line"; done
  fi)
__GDD_DYNAMIC__

# Append static body (no variable expansion — immune to heredoc injection)
cat >> "$STATE_FILE" <<'__GDD_BODY__'

Operate from canonical workflow state, not from the last status summary you produced.
A non-terminal `Resume From` or `Next Action` is not a stopping point.
If the current phase can continue, execute the next phase instead of replying with only a recap.

CRITICAL: Run brainstorming → requirements-gating → human-check-waiting in ONE assistant turn.
Do NOT end the turn after brainstorming. Continue into requirements-gating in the same turn.
Only stop when outputting the human check template with `<gdd-stop reason="human-check-waiting">`.
(Ending the turn without a `gdd-stop` marker to wait for a background dispatch's completion notification is allowed; see below.)

Keep going until exactly one of these is true:
1. `Next Action=done`
2. `Next Action=cancelled`
3. `Resume From=human-check-waiting` or `Next Action=human-check-waiting`
4. fail-closed / external prerequisite / ambiguous canonical state requires human or environment action, or another `<gdd-stop>` reason's use in references/output-format.md applies (for example `external-review-waiting`)

Codex Goal guard: if a thread-level Goal is active, keep it active until
`Next Action=done` and the done guard has passed. No reason other
than `done` is a successful Goal completion state.

When you intentionally stop, include exactly one marker:
- <gdd-stop reason="done">
- <gdd-stop reason="cancelled">
- <gdd-stop reason="human-check-waiting">
- <gdd-stop reason="blocked">
- <gdd-stop reason="clarification-needed"> (only for the uses in references/state-machine.md, including the TaskStop error case below)
- <gdd-stop reason="staging-verification-blocked">, <gdd-stop reason="external-review-waiting">, or <gdd-stop reason="auth-waiting"> (only for the uses in references/output-format.md § `<gdd-stop reason>`)

The closing tag `</gdd-stop>` is optional and ignored by the hook. Prefer the opening marker alone for consistency.

Use `reason="blocked"` for fail-closed, external prerequisites, ambiguous routing, or any other mandatory stop, unless one of the reasons above applies by its use (for example `auth-waiting` for SSO/auth expiry) (and except when TaskStop on a running background dispatch returns a result that keeps it running: use `reason="clarification-needed"`, as described below).
When blocked, include `参照した正本`, `停止理由`, `次の1アクション`, and put the `## 👤 次にすること` block after the marker (references/output-format.md § 停止時の「👤 次にすること」マップ).
Do not emit a `gdd-stop` marker merely because you can report the current phase or next phase.
While a background dispatch (for example the formal gate's gdd-formal-gate-runner on Claude Code) is still running, wait for its completion notification by ending the turn WITHOUT any `gdd-stop` marker. This is waiting, not stopping. To stop with a reason that clears the loop state (`blocked`, `cancelled`, `done`, or `staging-verification-blocked`) while it runs, TaskStop it first (the Stop hook pushes back otherwise; for when the pushback is skipped, see references/stop-hook-structured-markers.md). If TaskStop returns anything other than a success whose JSON `task_id` or `shell_id` equals the stopped id, `No task found`, or `is not running` (for example a denial), the dispatch is still treated as running: do not retry TaskStop; stop with `reason="clarification-needed"`, which keeps the loop state, and hand it to the human.

After user approves human check (responds "OK" to 承認ポイント):
- Do NOT emit another `<gdd-stop>` marker or ask for additional confirmation
- Follow the canonical post-approval procedure and dispatch: `commands/gdd-dev.md` instruction 10 STEP 2 (state updates, then dispatch via the Template with `subagent_type` — never invoke a phase skill directly)
- Continue running until the next terminal state
__GDD_BODY__

cat <<EOF
gdd autonomous continuation activated.
State file: ${STATE_FILE}
Stop hook behavior: continue until the Stop hook accepts a stop (references/state-machine.md § Autonomous Continuation).
Recommended model: ${RECOMMENDED_MODEL}
Steering candidates: ${STEERING_CANDIDATE_COUNT}
Worktree pollution warnings: ${WORKTREE_POLLUTION_WARNING_COUNT}
EOF

if [[ -n "$WORKTREE_POLLUTION_WARNINGS" ]]; then
  echo ""
  echo "⚠ Worktree pollution detected. Auto-resume is disabled until the canonical workspace is selected:"
  echo "$WORKTREE_POLLUTION_WARNINGS" | while IFS= read -r line; do
    echo "  - $line"
  done
fi

if [[ "$SHOULD_DISCOVER_RESUME_CANDIDATES" == "true" && "$STEERING_CANDIDATE_COUNT" -ge 2 ]]; then
  echo ""
  if [[ "$USER_INTENT_CLASS" == "new" ]]; then
    echo "ℹ Non-terminal steerings exist (${STEERING_CANDIDATE_COUNT}), but intent looks like a NEW task."
    echo "  Start a new steering — resume selection is not required unless the user uses resume cues (再開/続き/resume)."
    echo "  Existing non-terminal steerings (for reference only):"
    echo "$STEERING_CANDIDATES" | while IFS= read -r line; do
      echo "    - $line"
    done
  elif [[ "$USER_INTENT_CLASS" == "resume" ]]; then
    echo "⚠ Resume intent detected with multiple active steerings (${STEERING_CANDIDATE_COUNT}). Explicit selection required:"
    echo "$STEERING_CANDIDATES" | while IFS= read -r line; do
      echo "  - $line"
    done
  else
    echo "⚠ Multiple active steerings detected (${STEERING_CANDIDATE_COUNT}) and intent is ambiguous."
    echo "  Ask the user whether to start new or resume (and which):"
    echo "$STEERING_CANDIDATES" | while IFS= read -r line; do
      echo "  - $line"
    done
  fi
fi

if [[ "$GDD_RUNTIME" == "cursor" ]] && [[ "$RECOMMENDED_MODEL" == *"grok-4.6"* ]]; then
  cat <<'WARN'

⚠ Model warning: This phase requires a heavy model (Grok 4.6).
  軽量モデル（Grok Code Fast 1 等の cheap lane）では Iterative Refinement Loop の自律解決が途中停止しやすくなります。
  Cursor のモデル選択で Grok 4.6 を選んでから実行してください。
WARN
fi

if [[ -n "$USER_INTENT" ]]; then
  echo ""
  echo "User intent: ${USER_INTENT}"
fi

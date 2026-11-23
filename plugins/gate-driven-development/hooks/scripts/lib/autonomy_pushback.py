"""宣言された自律の範囲の中で止まろうとしたときに、Stop hook が 1 回だけ押し返す。

- `human_check_reason`: bind 済み steering の `worklog.md` に本人の事前回答（`事前回答:` 行）があるのに
  human-check-waiting で止まる（`references/human-check-template.md` § 事前回答）。最後の `事前回答:` 行の
  委任先が `DELEGATES` の値でなければ押し返さない。同じ steering の state.md に `判断の委任` の欄
  （§ 自走上限の置換値）があれば、行より先にその欄で決める（`FIELD_DELEGATES` の値なら行が無くても押し返し、
  それ以外の値・欄が 2 つ以上なら押し返さない）
- `merge_wait_reason`: `.claude/gdd-merge-intent.json`（マージ待ちの宣言。マージの許可を受けた agent が書く）
  があるのに PR が OPEN のまま止まる（直近 2 時間 10 分に起動し、まだ終わっていない background の処理があれば、
  終われば通知で起きるので押し返さない）。宣言を書いた後に、同じ PR の `gh pr merge` の最後の試行が
  拒否されていたら押し返さない（拒否された操作は再試行せず、人に戻して止まる。`references/post-merge-qa.md`
  手順 2。拒否は、走って失敗した〔`Exit code` で始まる〕もの以外の is_error の結果）。宣言は Stop hook の cwd の toplevel の 1 か所だけを読み、押し返しの文にその絶対パスを出す（制御文字・surrogate を含むパスは相対で出す）。
  宣言が無く、最後の発言が「CI が通ったらマージします」の形なら、
  宣言を書くかマージしないと明言するかを 1 回だけ求める

同じ状態で 2 回目に止まったら通す（判定の key を `.claude/gdd-autonomy-pushback.json` に残す。
GDD の継続は block を連鎖させるので `stop_hook_active` では「1 回目」を判定できない）。
読めない・判定できない・key を残せないときは押し返さない（今までどおり止まる側に倒す）。ただし background の処理の
判定だけは、判定できないときに「動いていない」とし、押し返す側に倒す（この判定を足す前と同じ挙動）。
呼び出し側は `run_within_deadline` で包む。gh の遅延や FIFO で Stop hook の timeout（10 秒）に届くと、
後ろの done guard ごと抜けて停止が通るため、締め切りを過ぎたら押し返さずに戻る。判定は thread で行い、
key の記録は締め切りに間に合った後に呼び出し側の thread で行う（間に合わなかった判定は key を残さない）。

human check の押し返しは peer のターンを見ない。押し返しの中身は本人の事前回答の適用で、承認の迂回にならないため。
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, NamedTuple

from lib.ci_state import ci_state as _ci_state
from lib.errors import append_hook_error
from lib.regular_file import read_regular_bytes
from lib.task_binding_resolve import _has_unsafe_char
from lib.tasklist_parse import strip_fenced_blocks
from lib.transcript import any_background_running, parse_transcript
from lib.wait_script import WAIT_SCRIPT, shown_wait_script

SIDECAR_FILE = "gdd-autonomy-pushback.json"
INTENT_FILE = "gdd-merge-intent.json"
# Bash が走って失敗した tool_result の先頭。is_error の結果のうち、これで始まらないもの（PreToolUse の hook の deny、
# auto mode classifier などの拒否）は、コマンドが走る前に止められたとみなす
# （2026-10-13 実測: `gh pr merge` の is_error は、すべてこれか `PreToolUse:`・`⛔ merge gate`・
# `Permission for this action was denied` で始まっていた）
_EXIT_CODE_PREFIX = "Exit code "
PROMISE_COOLDOWN_SECONDS = 600
GH_TIMEOUT_SECONDS = 2
DEADLINE_SECONDS = 3  # 押し返しに使う時間の合計（hook の前処理は数えない）
HARD_LIMIT_SECONDS = 6  # このモジュールの読み込みから。前処理が遅いときも、後ろの done guard に時間を残す
TAIL_BYTES = 512 * 1024
# この秒数より前に起動した background の処理は、押し返しを止めない（wait-until.py の上限 7200 秒に余裕を足した値）
BACKGROUND_WINDOW_SECONDS = 7200 + 600
_STARTED_AT = time.monotonic()
_spent = 0.0

_DECISION_ROW = re.compile(r"^(事前回答|事前回答の適用|自律判断):")
_STOPPED_ROW = re.compile(r"採った案:\s*(人間に止める|適用しない)")
# 事前回答の行の委任先の値（`references/human-check-template.md` § 事前回答 1 の記録の形と同じ集合）
DELEGATES = ("fable", "opus", "並行", "なし")
# state.md の `判断の委任` の欄のうち、押し返す値（ほかに `人に止める` があり、押し返さない）
FIELD_DELEGATES = ("fable", "opus", "並行")
_FIELD = re.compile(r"^- 判断の委任:(.*)$")
_HEAD = re.compile(r"^[0-9a-f]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*/[A-Za-z0-9_][A-Za-z0-9_.-]*$")
# 最後の発言の末尾で、CI などの完了を条件にマージすると約束している形（押し返しの発火だけに使う）
_PROMISE = (
    re.compile(
        r"(CI|チェック|checks?|レビュー|Copilot).{0,40}?"
        r"(通っ|通り|通れ|完了|終わ|success|成功|緑|green|揃|そろ|問題が無|問題がな).{0,40}?"
        r"(マージ|merge)(します|する|して(次|から)|し、|へ進|に進)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(r"\bmerge\b.{0,40}?\b(once|after|when)\b.{0,30}?\b(CI|checks?)\b", re.IGNORECASE | re.DOTALL),
)


class Pushback(NamedTuple):
    reason: str
    commit: Callable[[], bool]  # key を記録する。False なら押し返さない


def run_within_deadline(fn: Callable[[], Pushback | None], root: Path) -> str | None:
    """`fn` を残りの時間まで待ち、間に合った判定だけを記録して理由文を返す。それ以外は None（押し返さない）。

    残りの時間は、押し返しに使った時間の合計の残りと、モジュールの読み込みからの上限の残りの小さいほう。
    この関数は例外を出さない（呼び出し側は done guard より前にあるので、ここで落ちると guard ごと抜ける）。
    UTF-8 に encode できない理由文も押し返さない。打ち切り・例外は `root` の hook エラー記録に残す。
    """
    global _spent
    result: list[Pushback | None] = []

    def target() -> None:
        try:
            result.append(fn())
        except Exception as exc:  # 押し返しは補助。例外では押し返さない
            append_hook_error(root, "autonomy_pushback", repr(exc))

    started = time.monotonic()
    try:
        remaining = min(DEADLINE_SECONDS - _spent, HARD_LIMIT_SECONDS - (started - _STARTED_AT))
        if remaining <= 0:
            append_hook_error(root, "autonomy_pushback", "deadline: no time left")
            return None
        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        worker.join(remaining)
        if worker.is_alive():
            append_hook_error(root, "autonomy_pushback", f"deadline: cut off after {remaining:.1f}s")
            return None
        pushback = result[0] if result else None
        if pushback is None:
            return None
        # 理由文の値は検査済みで、ここは最後の砦。本番の起動（kill-switch.sh の python3 関数の `-X utf8`）の stdout は
        # surrogateescape で、ファイル名から来る U+DC80〜DCFF は生のバイトで出るが、それ以外の surrogate と、
        # UTF-8 mode でない起動の stdout では出力で例外になり、後ろの done guard ごと停止が通る。
        # strict の encode で弾き、記録せずに押し返さない
        pushback.reason.encode("utf-8")
        return pushback.reason if pushback.commit() else None
    except Exception as exc:
        append_hook_error(root, "autonomy_pushback", repr(exc))
        return None
    finally:
        _spent += time.monotonic() - started


def _sidecar(top: Path) -> Path:
    return top / ".claude" / SIDECAR_FILE


def _read_json(path: Path) -> object | None:
    """通常のファイルのときだけ読む（FIFO で止まらない）。無ければ {}、読めない・壊れていれば None。"""
    try:
        raw = read_regular_bytes(path)
        return {} if raw is None else json.loads(raw.decode("utf-8"))
    except (OSError, ValueError):
        return None


def _load(top: Path) -> dict | None:
    data = _read_json(_sidecar(top))
    return data if isinstance(data, dict) else None


def _save(top: Path, data: dict) -> bool:
    path = _sidecar(top)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        return False
    return True


def _claim_on_commit(top: Path, field: str, value: str) -> Callable[[], bool]:
    return lambda: _claim(top, field, value)


def _claim(top: Path, field: str, value: str) -> bool:
    """`field` が `value` でなければ書き換えて True（押し返す）。同じ・読めない・書けないなら False。"""
    data = _load(top)
    if data is None or data.get(field) == value:
        return False
    data[field] = value
    return _save(top, data)


def _decision_rows(text: str) -> list[str]:
    lines = (line.strip() for line in strip_fenced_blocks(text).splitlines())
    return [line for line in lines if _DECISION_ROW.match(line)]


def _last_assistant_text(transcript: Path) -> str:
    """transcript の末尾だけを読み、最後の assistant の本文を返す（GDD 外の停止でも全体を parse しない）。"""
    with transcript.open("rb") as fh:
        size = fh.seek(0, 2)
        fh.seek(max(0, size - TAIL_BYTES))
        lines = fh.read().decode("utf-8", "replace").split("\n")
    if size > TAIL_BYTES:
        lines = lines[1:]
    for line in reversed(lines):
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if not isinstance(item, dict):
            continue
        message = item.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if item.get("type") != "assistant" or not isinstance(content, list):
            continue
        texts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
        if texts:
            return "\n".join(texts)
    return ""


_WRITE_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})


class _IntentScan(NamedTuple):
    last_write: dict | None  # この宣言のパスへの最後の Write・Edit・MultiEdit
    merge_denied: bool  # 最後の書き込みの後の、対象 PR への `gh pr merge` の最後の試行が拒否された


def _scan_transcript(transcript: Path, intent_path: Path, pr: int) -> _IntentScan:
    """transcript を 1 回だけ読み、宣言の最後の書き込みと、その後のマージの拒否を見る。"""
    target = intent_path.resolve()
    needle = INTENT_FILE.encode("utf-8")
    last: dict | None = None
    attempt: str | None = None  # 宣言の書き込みの後の、対象 PR への最後のマージの試行の tool_use id
    denied = False
    with transcript.open("rb") as fh:
        for line in fh:
            merge = b'"Bash"' in line and b"merge" in line
            if not (needle in line or merge or (attempt and attempt.encode("utf-8") in line)):
                continue
            blocks = _content_blocks(line)  # 1 行は 1 回だけ読む
            if needle in line and (found := _last_write_to(blocks, target)):
                last, attempt, denied = found, None, False  # 書き込みより前の拒否は数えない
            if merge and (tool_id := _merge_attempt_id(blocks, pr)):
                attempt, denied = tool_id, False
            if attempt and (result := _tool_result_denied(blocks, attempt)) is not None:
                denied = result
    return _IntentScan(last, denied)


def _owns_intent(last: dict | None, current: str) -> bool:
    """今の宣言を書いたセッションか。

    この宣言のパスへの Write・Edit・MultiEdit の tool_use のうち最後のものが、今の中身を書いたときだけ数える
    （Write は中身が一致、Edit・MultiEdit は書いた文字列が今の中身に含まれる）。同じ worktree の別セッション、
    読んだだけのセッション、Bash・ApplyPatch・subagent で書いたセッションには届けない。
    """
    if last is None:
        return False
    if last["name"] == "Write":
        return last["input"].get("content") == current
    edits = last["input"].get("edits") if last["name"] == "MultiEdit" else [last["input"]]
    written = [e.get("new_string") for e in edits if isinstance(e, dict)] if isinstance(edits, list) else []
    return bool(written) and all(isinstance(w, str) and w in current for w in written)


def _content_blocks(line: bytes) -> list:
    try:
        item = json.loads(line)
    except ValueError:
        return []
    message = item.get("message") if isinstance(item, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def _merge_attempt_id(blocks: list, pr: int) -> str | None:
    """対象 PR への `gh pr merge` の Bash の tool_use の id。番号・URL で PR を特定できない形（引数なし・branch 名・
    1 つのコマンドに複数のマージなど）も一致とみなす（止まる側に倒す）。

    コマンドは merge gate と同じパーサで読む（受理する形を gate とそろえる）。import は押し返しの thread の中で行い、
    失敗しても `run_within_deadline` が捕まえて押し返さないだけにする（後ろの done guard は走る）。
    """
    from lib.gh_command_parse import parse_gh_pr_merge

    found = None
    for block in blocks:
        tool_input = block.get("input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if block.get("type") != "tool_use" or block.get("name") != "Bash" or not isinstance(command, str):
            continue
        parsed = parse_gh_pr_merge(command, "", "")
        number, url = parsed["pr_number"], parsed["pr_url"]
        if parsed["is_merge"] and (str(number) == str(pr) or (url or "").endswith(f"/pull/{pr}")
                                   or (number is None and url is None)) and isinstance(block.get("id"), str):
            found = block["id"]
    return found


def _tool_result_denied(blocks: list, tool_use_id: str) -> bool | None:
    """`tool_use_id` の tool_result が拒否か。is_error でなければ False、無ければ None。

    本文は文字列か、text の block の連結。is_error で本文が無い形も `_is_denial` に渡す（走る前に止められたとみなす）。
    """
    for block in blocks:
        if block.get("type") != "tool_result" or block.get("tool_use_id") != tool_use_id:
            continue
        if block.get("is_error") is not True:
            return False
        content = block.get("content")
        if isinstance(content, list):
            content = "\n".join(b["text"] for b in content if isinstance(b, dict) and isinstance(b.get("text"), str))
        return _is_denial(content if isinstance(content, str) else "")
    return None


def _is_denial(text: str) -> bool:
    """is_error の結果が、コマンドが走る前に止められたものか。走って失敗したもの（`Exit code` で始まる）は数えない。
    本文が空なら拒否とする。merge gate は拒否せず実行後に通知するだけなので、merge gate の文に例外は置かない。"""
    return not text.startswith(_EXIT_CODE_PREFIX)


def _last_write_to(blocks: list, target: Path) -> dict | None:
    found = None
    for block in blocks:
        if block.get("type") != "tool_use" or block.get("name") not in _WRITE_TOOLS:
            continue
        tool_input = block.get("input")
        path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
        if isinstance(path, str) and Path(path).is_absolute() and Path(path).resolve() == target:
            found = {"name": block["name"], "input": tool_input}
    return found


def human_check_reason(top: Path, worklog: Path | None) -> Pushback | None:
    """`worklog` は bind 済み steering の worklog.md（bind できないときは None）。"""
    if worklog is None:
        return None
    try:
        text = worklog.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return None
    rows = _decision_rows(text)
    if rows and _STOPPED_ROW.search(rows[-1]):
        return None
    field = _field_values(worklog.parent / "state.md")
    if field:
        if len(field) != 1 or field[0] not in FIELD_DELEGATES:
            return None
        where = f"state.md の `判断の委任: {field[0]}`"
    else:
        answers = [row for row in rows if row.startswith("事前回答:")]
        delegate = _delegate(answers[-1]) if answers else None
        if delegate is None:
            return None
        where = f"worklog.md の事前回答の行（委任先: {delegate}）"
    return Pushback(
        f"{where} で判断を委任しているのに、human-check-waiting で止まろうとしています。"
        "`references/human-check-template.md` § 事前回答 の 2 で、この human check が委任の対象かを確かめ、"
        "対象なら委任先で判断し、human check を表示せずに続けてください。"
        "人に戻す条件（同 3）に当たる、または原文を確かめられないときは、`採った案: 人間に止める`"
        "（または `適用しない`）の `事前回答の適用:` 行を worklog.md に書いてから、もう一度止まってください。",
        _claim_on_commit(top, "human_check_key", f"{worklog.parent.name}:{len(rows)}"),
    )


def _field_values(state: Path) -> list[str]:
    """state.md のコードフェンスの外の `- 判断の委任: <値>` の値。読めなければ空（行で決める今までの挙動に戻る）。"""
    try:
        text = state.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return []
    return [found.group(1).strip() for line in strip_fenced_blocks(text).splitlines() if (found := _FIELD.match(line))]


def _delegate(row: str) -> str | None:
    """事前回答の行の委任先。欄がちょうど 1 つで、値が `DELEGATES` にあるときだけ返す（それ以外は押し返さない）。"""
    values = [field.split(":", 1)[1].strip() for field in row.split(" / ") if field.strip().startswith("委任先:")]
    if len(values) != 1 or values[0] not in DELEGATES:
        return None
    return values[0]


def _read_intent(data: object) -> tuple[int, str, str] | None:
    if not isinstance(data, dict):
        return None
    pr, repo, then = data.get("pr"), data.get("repo"), data.get("then")
    repo = "" if repo is None else repo  # null は省略と同じ
    then = "" if then is None else then
    if type(pr) is not int or pr <= 0 or not isinstance(repo, str) or not isinstance(then, str):
        return None
    if _has_unsafe_char(then):  # 理由文にそのまま載せるので、制御文字・surrogate を含む宣言は受けない
        return None
    if repo and not _REPO.match(repo):
        return None
    return pr, repo, then[:200]


def _intent_path(top: Path) -> Path:
    return top / ".claude" / INTENT_FILE


def _shown_intent_path(top: Path) -> str:
    """理由文に載せる宣言のパス。制御文字・surrogate を含むなら、絶対パスの代わりに相対の書き方にする。"""
    path = str(_intent_path(top))
    return f".claude/{INTENT_FILE}" if _has_unsafe_char(path) else path


def _wait_command(script: Path, pr: int, repo_args: list[str]) -> str:
    """理由文に載せる待機の例。スクリプトのパスの書き方は wait-loop-gate の deny の文と同じ（lib/wait_script.py）。"""
    return " ".join(["python3", shown_wait_script(script),
                     shlex.join(["--timeout", "3600", "--pr-checks", str(pr), *repo_args])])


def _intent_reason(top: Path, intent: tuple[int, str, str]) -> Pushback | None:
    pr, repo, then = intent
    repo_args = ["-R", repo] if repo else []
    try:
        proc = subprocess.run(
            ["gh", "pr", "view", str(pr), "--json", "state,headRefOid,statusCheckRollup", *repo_args],
            cwd=top, capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS,
        )
        view = json.loads(proc.stdout) if proc.returncode == 0 else None
    except subprocess.TimeoutExpired:  # 押し返さないのは同じ。打ち切りは記録に残す（gh が無い・失敗したときは残さない）
        append_hook_error(top, "autonomy_pushback", f"gh: timed out after {GH_TIMEOUT_SECONDS}s")
        return None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if not isinstance(view, dict) or view.get("state") != "OPEN":
        return None
    head = str(view.get("headRefOid") or "")
    head = head if _HEAD.match(head) else ""
    ci = _ci_state(view.get("statusCheckRollup"))
    if ci is None:
        return None
    watch = _wait_command(WAIT_SCRIPT, pr, repo_args)
    # head を読めないときも shell に貼れる形にする（`<head>` はリダイレクトになる）。pr は int、repo は検査済み
    commit = head or '"$(' + " ".join(["gh", "pr", "view", str(pr), "--json", "headRefOid", "-q", ".headRefOid", *repo_args]) + ')"'
    runs = " ".join(["gh", "run", "list", "--commit", commit, *repo_args])
    return Pushback(
        f"マージ待ちの宣言（{_shown_intent_path(top)}）があり、PR #{pr} は OPEN のままです"
        f"（head {head[:12] or '不明'}、CI: {ci}。required でない check も含めて見ています）。止まる前に次のどれかをしてください。"
        "マージするかどうかは、宣言の原文の条件と、repo・タスクのマージ手順（GDD では `references/post-merge-qa.md` 手順 2）で"
        "決めてください（この hook は原文も required の check も読んでいません）。"
        f"CI が success で原文の条件を満たすなら、その手順でマージし、宣言の次の作業（{then or 'なし'}）に進む。"
        f"pending・no-checks なら、待つ仕組み（例: `{watch}` を run_in_background で）を起動してから止まる"
        f"（no-checks が続くときは、head の commit に run が付くかを `{runs}` で確かめる）。"
        "failure なら原因を確かめて直す。"
        "マージを hook・auto mode classifier に拒否されたなら、別の方法で再試行せず、"
        "拒否の理由とユーザーが打つコマンドを明言して止まる（宣言を書いた後の、この PR の最後の `gh pr merge` が"
        "走る前に止められていれば、この hook は押し返しません）。マージしないと決めた、または許可が取り消されたときは、"
        "宣言のファイルを消してから止まる。PR と CI の状態が変わらないまま止まったときは、もう押し返しません。",
        _claim_on_commit(top, "merge_key", f"{repo}#{pr}:{head}:{ci}"),
    )


def _has_promise(last_text: str) -> bool:
    tail = last_text[-600:]
    return any(pattern.search(tail) for pattern in _PROMISE)


def _promise_reason(top: Path) -> Pushback | None:
    data = _load(top)
    now = time.time()
    if data is None:
        return None
    try:
        last = float(data.get("promise_nudged_at", 0))
    except (TypeError, ValueError):
        return None
    if now - last < PROMISE_COOLDOWN_SECONDS:
        return None
    data["promise_nudged_at"] = now
    return Pushback(
        f"最後の発言で「CI などが通ったらマージする」と書いていますが、マージ待ちの宣言（{_shown_intent_path(top)}）がありません。"
        "待つ仕組みが無いと、このまま誰も再開しません（CI の監視は失敗のときしかセッションを起こしません）。"
        f"本人からマージの許可を受けているなら、{_shown_intent_path(top)}（この hook が読む唯一の場所。"
        "GDD の worktree で作業していても、ここに書く）に、Write ツールで "
        '`{"pr": <番号>, "repo": "<owner/name。省略可>", "then": "<マージ後の作業>", "original": "<許可の原文>"}` '
        "を書き（Bash で書いた宣言では押し返しが効きません）、待つ仕組みを起動してから止まってください。"
        "許可を受けていない・マージしないなら、そのことを明言して止まってください。",
        lambda: _save(top, data),
    )


def _background_running(top: Path, transcript: Path) -> bool:
    """直近 BACKGROUND_WINDOW_SECONDS 秒に起動し、まだ終わっていない background の処理があるか。
    判定できないときは無いとする（押し返す側。終わらない処理・通知の届かない shell でも、押し返さない期間に上限をつける）。"""
    now = time.time()
    try:
        return any_background_running(parse_transcript(transcript), now - BACKGROUND_WINDOW_SECONDS, now)
    except Exception as exc:  # noqa: BLE001 - 押し返しの判定を落とさない
        append_hook_error(top, "autonomy_pushback", f"background check failed: {exc!r}")
        return False


def merge_wait_reason(top: Path, transcript: Path, is_peer: Callable[[], bool]) -> Pushback | None:
    """`is_peer` は、押し返す候補が決まった後にだけ呼ぶ（transcript 全体を読むので、全停止では呼ばない）。"""
    intent_path = _intent_path(top)
    try:
        raw = read_regular_bytes(intent_path)
    except OSError:  # 宣言がある（読めないときも、約束の検知には進まない）
        return None
    if raw is not None:
        current = raw.decode("utf-8")
        intent = _read_intent(json.loads(current))
        if not intent:
            return None
        scan = _scan_transcript(transcript, intent_path, intent[0])
        if not _owns_intent(scan.last_write, current) or scan.merge_denied or is_peer():
            return None
        if _background_running(top, transcript):  # 待つ仕組みが動いているとみなす。終われば通知で起き、次の Stop で見る
            return None
        return _intent_reason(top, intent)
    if not _has_promise(_last_assistant_text(transcript)) or is_peer():
        return None
    return _promise_reason(top)

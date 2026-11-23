"""区切りで、手動 /compact に使える 1 行をユーザーへ提案する。

Stop hook の出力に `systemMessage` を足すだけで、`decision` / `reason` / 終了コードは
変えない。`systemMessage` はユーザーへ表示されるだけでモデルの文脈には入らないので、
トークンはかからない。/compact を打つかどうかはユーザーが決める。

区切りは 4 つに閉じる（正本は `tests/test_compact_suggestion_contract.py`）。
Gate Batch（`## Execution Plan` の `- Gate Batch <N>: ...`）の task の Round 3 は、batch で 1 回にする。
steering の field 値で判定し、Stop hook 本体が active・runtime・session・transcript の
guard を通った停止（本体が `mark_eligible()` を呼んだ停止）でだけ見る。guard を通った後で
本体が黙って抜ける停止（継続意図が見えない・peer の発話・subagent の結果待ち）には出る
（同じセッションなので害は小さい）。`session_id` が空の Cursor の state は、本体と同じく
会話を区別しない。
同じ steering の同じ区切りは 1 回だけ出す。その記録は steering を汚さないよう
`<project>/.claude/` に置く。
PR マージ後の「新しいセッションで始めて」は対象外（state.md に merge を記録する field が
無く、hook が持つ merge の記録は post-merge continuation marker だけだが、それは
`.steering/` の外の一時ファイルで区切りの判定源にはしない）。

提案は安全装置ではないので、判定や記録で例外が出たら何も足さない（fail-open）。
`gdd_stop_hook.py` は行数の目安（1500）の直前にあるため、判定と合流をここへ置く。
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Callable

from lib.task_binding_resolve import safe_for_output
from lib.tasklist_parse import strip_fenced_blocks, task_name

RECORD_FILE = "gdd-compact-suggestions.json"
_PREFIX = "[gdd:compact] 区切りです。手動で /compact するなら次の 1 行（打たなくても進行は変わりません）:\n"
_IMPLEMENTATION_PHASES = {
    "gdd-task-breakdown",
    "gdd-test-driven-development",
    "gdd-subagent-driven-implementation",
}
_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")
_PR_NUMBER_RE = re.compile(r"/pull/(\d+)")
_CURRENT_TASK_RE = re.compile(
    r"^##[ \t]+Current Task\b[^\n]*\n(.*?)(?=^##[ \t]|\Z)", re.MULTILINE | re.DOTALL
)
_EXECUTION_PLAN_RE = re.compile(
    r"^##[ \t]+Execution Plan\b[^\n]*\n(.*?)(?=^##[ \t]|\Z)", re.MULTILINE | re.DOTALL
)
_GATE_BATCH_RE = re.compile(r"^-[ \t]+Gate Batch[ \t]+(\d+)[ \t]*:(.*)$", re.MULTILINE)
_BATCH_ITEM_TASK_ID_RE = re.compile(r"^\**(T-?\d+)\b")
_TASK_ID_AT_NAME_START_RE = re.compile(r"^\**(T-?\d+)\b")
_COMPAT_TASK_ITEM_RE = re.compile(r"^-[ \t]+\**(T-?\d+)\b")

# この停止が現在のセッションの GDD のものかは、Stop hook 本体の guard が決める。
# 判定を本体と二重に持たないよう、本体が guard を通った地点で `mark_eligible()` を呼ぶ。
_eligible = False


def mark_eligible() -> None:
    """本体が active・runtime・session・transcript の guard を通ったときに呼ぶ。"""
    global _eligible
    _eligible = True


def _field(text: str, name: str) -> str:
    """`- Name: value | ...` / `Name=value` の value（最初の値付き行）。

    読み方は `lib/state_fields.state_field_value()` と同じ。同モジュールは
    `from tasklist_parse import` 形式で、`lib.` パッケージ経由の stop hook からは import できない。
    """
    body = strip_fenced_blocks(text).replace("`", "")
    match = re.search(
        rf"^(?:-[ \t]+)?{re.escape(name)}[ \t]*[:=][ \t]*(\S.*)$", body, re.MULTILINE
    )
    return match.group(1).split("|")[0].strip() if match else ""


def _token(text: str, name: str) -> str:
    """value の先頭の英数字トークン（`approved（…）` / `3（R1…）` の注記を落とす）。"""
    match = _TOKEN_RE.match(_field(text, name))
    return match.group(0) if match else ""


def _task_blocks(section_text: str) -> list[tuple[str, str]]:
    """`## Current Task` 節を task 単位のブロックに分ける。

    並列実行時は同節に複数 task（`T-1`, `T-2`, ...）が並ぶ
    （`references/state-machine.md:733`）。`Gate Rounds` は task ごとの
    カウンタなので、節全体から最初の値・最初の Task ID を別々に取るのではなく、
    同じブロック内の組で見る。task 見出しの受理面は `tasklist_parse.task_name()` を
    正本とし、compact 提案が従来受理していた `- T-1 ...` / `- **T-1 ...**` も保つ。
    """
    text = strip_fenced_blocks(section_text)
    starts: list[tuple[int, str]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        shared_name = task_name(stripped)
        match = _TASK_ID_AT_NAME_START_RE.match(shared_name)
        if not match:
            match = _COMPAT_TASK_ITEM_RE.match(stripped)
        if match:
            starts.append((offset, match.group(1)))
        offset += len(line)
    return [
        (task_id, text[start : starts[i + 1][0] if i + 1 < len(starts) else len(text)])
        for i, (start, task_id) in enumerate(starts)
    ]


def _gate_batch_of(tasklist_text: str) -> dict[str, str]:
    """`## Execution Plan` の `- Gate Batch <N>: T-1, T-2` から task id → batch 番号。

    カンマで区切った各項目の先頭の id だけを読む（`(after T-3)` のような注記は数えない）。
    2 つ以上の行に出る id は、どちらの batch にも入れず task ごとのキーに戻す。
    """
    section = _EXECUTION_PLAN_RE.search(tasklist_text)
    if not section:
        return {}
    found: dict[str, list[str]] = {}
    for number, members in _GATE_BATCH_RE.findall(section.group(1)):
        for item in members.split(","):
            match = _BATCH_ITEM_TASK_ID_RE.match(item.strip())
            if match:
                found.setdefault(match.group(1), []).append(number)
    return {task_id: numbers[0] for task_id, numbers in found.items() if len(numbers) == 1}


def detect(state_text: str, tasklist_text: str, steering_name: str) -> list[tuple[str, str]]:
    """当てはまる区切りを `(記録キー, /compact 行)` で、区切りの番号順に返す。"""
    requirements = _token(state_text, "Requirements Review Status") == "approved"
    human_check = _token(state_text, "Human Check Status") == "approved"
    design = _token(state_text, "Design Review Status") == "approved"
    # tasklist.md が routing source になるのは 3 条件が揃ってから
    # （references/state-machine.md § `Next Action`）。設計承認後に要件を再オープンする
    # （`gdd-requirements-amendment`）と、Design/Human Check は approved のまま
    # Requirements Review Status だけ pending に戻りうるため、3 つ目も見る。
    # 揃うまでは state.md だけを見る。state.md に `Next Action` が無い（未記載）場合に
    # tasklist.md の古い値へ fallback すると、要件が未承認のまま実装開始が誤発火する。
    all_approved = requirements and human_check and design
    sources = (tasklist_text, state_text) if all_approved else (state_text,)
    next_action = next((v for v in (_token(t, "Next Action") for t in sources) if v), "")

    hits: list[tuple[str, str]] = []
    if human_check and next_action == "gdd-design-gating":
        hits.append((
            "req_approved",
            "/compact 要件は承認済み。次は gdd-design-gating。"
            f"正本は .steering/{safe_for_output(steering_name)}/ の requirements.md と state.md。"
            "残すもの：承認時にユーザーが示した判断・条件。要件を詰めた会話の経緯は捨ててよい",
        ))
    if all_approved and next_action in _IMPLEMENTATION_PHASES:
        hits.append((
            "impl_started",
            "/compact 設計は承認済み。次は task-breakdown と実装。正本は design.md・tasklist.md・"
            "state.md。残すもの：Current Task、Next Action、承認時の条件。設計レビューの往復は捨ててよい",
        ))
    pr_number = _PR_NUMBER_RE.search(_field(state_text, "PR URL"))
    if pr_number:
        hits.append((
            "pr_created",
            f"/compact PR #{pr_number.group(1)} を作成済み。以後はレビュー対応だけ。"
            "残すもの：PR 番号、ブランチ、最後に通した回帰テストと独立レビューの SHA。"
            "実装の経緯は捨ててよい",
        ))
    tasklist_body = strip_fenced_blocks(tasklist_text)
    section = _CURRENT_TASK_RE.search(tasklist_body)
    if section:
        # Gate Rounds は task ごとのカウンタ。並列 batch では複数 task が同節に
        # 並ぶため、節全体から 1 つだけ拾わず、task ブロックごとに組で見る。
        # Gate Batch は全 task に同じだけ足すので、batch で 1 つのキーにする。
        gate_batch = _gate_batch_of(tasklist_body)
        keys: list[str] = []
        for task_id, block in _task_blocks(section.group(1)):
            if _token(block, "Gate Rounds") != "3":
                continue
            key = f"gate-batch-{gate_batch[task_id]}" if task_id in gate_batch else task_id
            if key not in keys:
                keys.append(key)
        for key in keys:
            hits.append((
                f"gate_rounds_3:{key}",
                "/compact impl-gate Round 3 の途中。残すもの：未解決 finding の ID と場所"
                "（file:function）、試した修正とその結果、Gate Rounds。解決済み finding のやり取りは捨ててよい",
            ))
    return hits


def merge_into_output(output: str, message: str) -> str | None:
    """hook の stdout に `systemMessage` だけを足す。足せない形なら `None`。"""
    if not output.strip():
        return json.dumps({"systemMessage": message}, ensure_ascii=False) + "\n"
    try:
        payload = json.loads(output)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    existing = payload.get("systemMessage")
    if existing is not None and not isinstance(existing, str):
        return None
    payload["systemMessage"] = f"{existing}\n\n{message}" if existing else message
    return json.dumps(payload, ensure_ascii=False) + "\n"


def _load_record(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        # 壊れた記録は作り直す（同じ区切りを最大 1 回重ねて出すだけで済む）
        return {}
    return data if isinstance(data, dict) else {}


def _next_suggestion(
    project_root: Path, steering_file: Callable[[Path, str], Path | None]
) -> tuple[str, Path, dict] | None:
    """まだ出していない最初の区切りを `(systemMessage, 記録先, 更新後の記録)` で返す。"""
    state_file = steering_file(project_root, "state.md")
    if state_file is None:
        return None
    steering = state_file.parent
    tasklist_file = steering_file(project_root, "tasklist.md")
    tasklist_text = ""
    if tasklist_file is not None and tasklist_file.parent == steering:
        tasklist_text = tasklist_file.read_text(encoding="utf-8", errors="replace")
    hits = detect(state_file.read_text(encoding="utf-8", errors="replace"), tasklist_text, steering.name)

    record_path = project_root / ".claude" / RECORD_FILE
    record = _load_record(record_path)
    seen = record.get(str(steering))
    seen = seen if isinstance(seen, list) else []
    for key, line in hits:
        if key not in seen:
            record[str(steering)] = [*seen, key]
            return _PREFIX + line, record_path, record
    return None


def _with_suggestion(
    output: str,
    project_root: Path,
    steering_file: Callable[[Path, str], Path | None],
) -> str:
    try:
        pending = _next_suggestion(project_root, steering_file)
        if pending is None:
            return output
        message, record_path, record = pending
        merged = merge_into_output(output, message)
        if merged is None:
            return output
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return merged
    except Exception:
        return output


def run(
    main: Callable[[], None],
    steering_file: Callable[[Path, str], Path | None],
) -> None:
    """`main()` を走らせ、その stdout に区切りの提案を足してから出す。

    `main()` の出力と終了コードはそのまま通す。`main()` が例外で落ちたとき・
    0 以外で終わったとき・本体の guard を通らずに抜けたとき（`mark_eligible()` が
    呼ばれていないとき）は何も足さない。
    """
    global _eligible
    _eligible = False
    try:
        hook_input = json.loads(os.environ.get("GDD_HOOK_INPUT") or "{}")
        project_root = Path(hook_input.get("cwd", "") or os.getcwd()).resolve()
    except Exception:
        main()
        return

    buffer = io.StringIO()
    code: object = 0
    try:
        with contextlib.redirect_stdout(buffer):
            main()
    except SystemExit as exc:
        code = exc.code
    except BaseException:
        sys.stdout.write(buffer.getvalue())
        raise
    output = buffer.getvalue()
    if code in (None, 0) and _eligible:
        output = _with_suggestion(output, project_root, steering_file)
    sys.stdout.write(output)
    if code not in (None, 0):
        raise SystemExit(code)

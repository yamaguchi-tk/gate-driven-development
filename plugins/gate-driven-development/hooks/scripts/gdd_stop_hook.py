from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

# GDD phase markers (skill names emitting <gdd-phase>). Helpers
# (gdd-model-routing, gdd-using-git-worktrees, gdd-requesting-code-review,
# gdd-receiving-code-review, gdd-refactor-planning, gdd-test-failure-debug-pack)
# are excluded.
GDD_PHASE_MARKERS = [
    "gdd-completion-check",
    "gdd-implementation-gating",
    "gdd-subagent-driven-implementation",
    "gdd-test-driven-development",
    "gdd-task-breakdown",
    "gdd-design-gating",
    "gdd-requirements-gating",
    "gdd-systematic-debugging",
    "gdd-brainstorming",
    "gdd-pre-workflow-brainstorming",
]

# hook は lib/kill-switch.sh で python3 を -I で起動し、PYTHONSAFEPATH も設定する。その下では、このファイルの
# ディレクトリが sys.path に入らない
if sys.flags.isolated or getattr(sys.flags, "safe_path", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.constants import (
    ALLOWED_STOP_REASONS,
    HANDOFF_PATTERN,
    STATE_KEEPING_STOP_REASONS,
    STOP_PATTERN,
    _HOOK_INJECTION_PREFIXES,
    _HUMAN_CHECK_PAUSE_RE,
)
from lib.pr_review_followup_polling import escalate_polling_reason
from lib.errors import (
    append_hook_error,
    block_hook_integrity_failure,
    suppress_hook_integrity_failure,
)
from lib.guards import (
    goal_guard_message,
    looks_like_gdd_continuation,
)
from lib.hitl_lint_gate import enforce_hitl_lint_gate
from lib.next_action_check import (
    EXEMPT_REASONS as _NEXT_ACTION_EXEMPT,
    NEXT_ACTION_HEADING,
    has_next_action_block,
)
from lib.next_plan_check import (
    continuation_file_exists,
    has_next_plan_block,
    registry_creation_claimed,
    requirements_lane_pending,
)
from lib.regular_file import read_regular_bytes
from lib.steering_candidate import latest_steering_candidate, usable_candidate
from lib.state_io import parse_state, write_state
from lib.stop_block_ceiling import (  # noqa: F401  テストが hook の属性として参照する
    GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS,
    STOP_HOOK_MAX_CONSECUTIVE_BLOCKS,
    _coerce_stop_hook_active,
    enforce_consecutive_block_ceiling,
)
from lib.task_binding_resolve import (
    CONTAINMENT_REJECTED,
    BindResult,
    resolve_bind,
    resolve_guard_tasklist,
    safe_for_output,
)
from lib.tasklist_parse import (
    resume_from_value,
    strip_fenced_blocks,
    classify_task_line,
    strip_fenced_lines,
    strip_fenced_lines_marked,
    task_name,
)
from lib import autonomy_pushback, compact_suggestion, handoff_summary, wait_watchdog
from lib.done_guard import (
    _AC_ID_CORE,
    _line_break_char_error,
    _route_in_progress_errors,
    _scan_remaining_tasks,
    _scan_verification,
    _tally_task_sections,
)
from lib.tasklist_structure import tasklist_structure
from lib.done_block_message import (
    _is_legacy_writer_display,
    _legacy_writer_headline,
    _build_recovery_hints,
    _build_why_explanations,
)
from lib import post_merge_continuation as post_merge
from lib.transcript import (
    ParsedTranscript,
    any_background_wait_running,
    any_resumed_agent_running,
    last_user_turn_is_peer,
    parse_transcript,
    subagent_in_flight_from_parsed,
)

#: 1 回の hook 実行内で bind 解決結果をメモ化する。Stop hook は毎回の停止で走り
#: timeout 10 秒なので、4 経路（done guard / progress counter / progress text /
#: resume-from fallback）で毎回 registry を読み直さない。
_BIND_CACHE: dict[str, BindResult] = {}


def _worktree_toplevel(start: Path) -> Path:
    """`git rev-parse --show-toplevel` を返す（取れなければ `start` のまま）。

    `lib/task_binding_resolve.py` の呼び出し側契約: `repo_root` / `cwd` は
    **どちらも現在の worktree の toplevel**。`resolve_task()` は
    `worktree_path == cwd` を文字列の完全一致で比べるので、hook がサブディレクトリで
    起動しているとそのままでは必ず `conflict` に落ち、**warn 降格の原因が
    「binding 欠落」なのか「cwd がサブディレクトリ」なのか切り分けられなくなる**。
    """
    try:
        # bytes で読み、最後の改行だけを落とす。`.strip()` だと `<wt> ` が `<wt>` になり、
        # bind も `.steering` も見つからずに done を通す（text モードは CR も改行にする）。
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, check=True, cwd=str(start),
        )
        out = result.stdout
        top = os.fsdecode(out[:-1] if out.endswith(b"\n") else out)
        if top:
            return Path(top)
    except Exception:
        pass
    return start


def _resolve_bind_memoized(project_root: Path) -> BindResult:
    top = _worktree_toplevel(project_root)
    key = str(top)
    if key not in _BIND_CACHE:
        _BIND_CACHE[key] = resolve_bind(repo_root=top, cwd=top)
    return _BIND_CACHE[key]


def _steering_candidate(root: Path, filename: str) -> tuple[Path, bool] | None:
    """bind 済み steering、bind が無ければ最新の steering の `filename` と、それが使えるか。何も無ければ `None`。

    選び方の規則は `lib/steering_candidate.py`。bind 不能時だけ current worktree の `.steering` を見る。
    """
    top = _worktree_toplevel(root)
    bind = _resolve_bind_memoized(top)
    if bind.status == "resolved" and bind.steering_dir is not None:
        return usable_candidate(bind.steering_dir / filename, bind.steering_dir)
    return latest_steering_candidate(top / ".steering", filename)


def _bound_steering_file(root: Path, filename: str) -> Path | None:
    """`_steering_candidate` の `filename` が使えればそれ、ほかは `None`（AC-7 / `adr.md` ADR-8）。

    進捗表示（`tasklist.md`）と resume-from fallback（`state.md`）が**この 1 関数を共有する**
    ―― 片方にだけ containment を書くと他方が越境したまま残る。
    """
    found = _steering_candidate(root, filename)
    return found[0] if found and found[1] else None


# Reasons that require tasklist/verification pre-checks before allowing stop
DONE_REASONS = {"done"}
# validate-plugin.sh checks for this string literal in gdd_stop_hook.py — do not move to lib.
POST_MERGE_CONTINUATION_FILE = "gdd-post-merge-continuation.json"
_HUMAN_CHECK_PRIMARY_SURFACE_RE = re.compile(
    r'(整理した要件|実装する方法・内容|検証する方法・内容|どこまで自走|判断ポイント|'
    r'OKでも許可されないこと|人間に戻す条件|段階実装)'
)
# `Manual merge continuation` は tests/checks/hooks.sh がこのファイルの**ソース上に**
# 存在することを要求する契約リテラル。lib 側へ移すと契約チェックが落ちるため、
# ここで宣言して lib へ引数で渡す（宣言だけ残す死んだ定数にはしない）。
POST_MERGE_CONTINUATION_LANE = "Manual merge continuation"


def post_merge_state_path(project_root: Path) -> Path:
    return post_merge.state_path(project_root, POST_MERGE_CONTINUATION_FILE)


def write_post_merge_continuation(
    project_root: Path,
    *,
    session_id: str,
    tasklist_path: str,
    last_output: str,
) -> None:
    """Persist Manual merge continuation state after PR creation."""
    post_merge.write_continuation(
        project_root,
        marker_file=POST_MERGE_CONTINUATION_FILE,
        session_id=session_id,
        tasklist_path=tasklist_path,
        last_output=last_output,
    )


def maybe_block_incomplete_post_merge_continuation(project_root: Path, tv: ParsedTranscript) -> None:
    """Block early stop after a manual merge cue until post-merge checks run."""
    payload = post_merge.resolve_block(
        project_root,
        tv,
        marker_file=POST_MERGE_CONTINUATION_FILE,
        lane=POST_MERGE_CONTINUATION_LANE,
    )
    if payload is not None:
        print(json.dumps(payload, ensure_ascii=False))
        raise SystemExit(0)


def allow_state_human_check_fallback(last_output: str, last_tool_output: str) -> bool:
    """Allow state.md Resume From fallback only when the current turn looks
    like a human-check output.

    The state file is useful as a recovery source when subagent/main-session
    marker propagation fails, but it must not be enough by itself. Otherwise an
    old `Resume From: human-check-waiting` in the current worktree can pause an
    unrelated conversation. Structured `<gdd-stop>` in assistant/tool output is
    always handled before this fallback; this function only guards the markerless
    recovery path.

    Fallback label: transitional. Delete condition: remove after all phase
    skills have contract tests proving the main assistant text always emits
    `<gdd-stop reason="human-check-waiting">` at the human-check gate.
    """
    text = "\n".join([last_output or "", last_tool_output or ""])
    return bool(_HUMAN_CHECK_PAUSE_RE.search(text) or _HUMAN_CHECK_PRIMARY_SURFACE_RE.search(text))


def persist_handoff_summary(text: str, cwd: Path) -> None:
    """Extract the latest Handoff Summary from assistant output and persist it
    to the active steering's state.md as Last Handoff Summary."""
    handoff_summary.persist(text, cwd, HANDOFF_PATTERN)


CONTAINMENT_ERROR = (
    "steering の containment 検査に失敗しました（containment rejected）。"
    "検査対象の tasklist.md が .steering/ の外を指しているため、"
    "done を許可しません（fail-closed）。\n"
    "symlink を実体へ置き換えるか、binding を作り直してください。"
)


def _guard_tasklist(cwd: Path) -> tuple[Path | None, str]:
    """検査対象の tasklist.md を決める。`(path, error)` を返す。

    検査対象は **この worktree に bind された steering だけ**。
    旧実装は `git worktree list` を順に舐めて最初に見つかった steering を検査したため、
    同じ repo の別 worktree に未完了 tasklist があると誤 block していた。
    bind 不能時は他 worktree を漁らず `(None, "")` を返す（呼び出し元が
    bind status を見て warn に降格する）。
    AC-2 の fail-open 条件は「bind が解決できない **かつ** current worktree にも
    steering が無い」の **2 条件**。`bind` 不能だけで検査を放棄すると字句より広くなる。
    `_bound_steering_file()` と**同じ**フォールバック（他 worktree は列挙せず、
    current worktree の `.steering` だけを名前の降順で見る）に寄せる。
    旧実装は `conflict` の時点で通しており、**自 worktree に未完了 tasklist があっても
    done を通していた**（completion-check の H-1）。
    """
    bind = _resolve_bind_memoized(cwd)
    tasklist_path = resolve_guard_tasklist(
        bind.steering_dir if bind.status == "resolved" else None,
        _worktree_toplevel(cwd) / ".steering",
    )
    if tasklist_path is CONTAINMENT_REJECTED:
        # **fail-closed**。containment に弾かれたのは「検査対象が無い」のとは違う ——
        # 同じ扱いにすると **guard が無言で無効化される**（security lane の H-S1）。
        # 同関数の `fence_unclosed` が同型の状況を fail-closed にしているのと揃える。
        return None, CONTAINMENT_ERROR
    return tasklist_path, ""


def _remaining_task_errors(remaining: list[str], unexpected_content: list[str]) -> list[str]:
    errors: list[str] = []
    if remaining:
        errors.append(
            f"tasklist.md に未完了タスクが {len(remaining)} 件残っています:\n"
            + "\n".join(safe_for_output(x) for x in remaining[:5])
        )
        if len(remaining) > 5:
            errors.append(f"  ...他 {len(remaining) - 5} 件")
    if unexpected_content:
        errors.append(
            f"Current Task / Pending Tasks に非標準の内容が {len(unexpected_content)} 件あります"
            f"（タスクパターンに一致しないが「なし」でもない）:\n"
            + "\n".join(safe_for_output(x) for x in unexpected_content[:5])
        )
    return errors


def _verification_errors(
    verification_section_found: bool,
    verification_data_rows: list[str],
    violations: list[tuple[str, object]],
    unfinished: list[str],
) -> list[str]:
    """design.md D5 の判定順（1: 節無し → 2: 違反種別 → 3: AC 検証行 0 件 → 4: unfinished）。

    `violations` は `_scan_verification()` が返す `(kind, payload)` の list。
    `kind` は `"line"`（列挙外の行の実物） / `"section_fence"`（節に重なる fence の
    開始行番号） / `"fenced_heading"`（fence 内の `## Verification` 見出し行番号）。
    件数は種別ごとに数え、丸めない。違反があるときに「検証行がありません」を
    出さないのは、行はあるが受理されていない状態を「空」と誤誘導しないため。
    """
    line_violations = [p for k, p in violations if k == "line"]
    section_fence_starts = sorted({p for k, p in violations if k == "section_fence"})
    fenced_heading_starts = sorted({p for k, p in violations if k == "fenced_heading"})

    if not verification_section_found:
        base = [
            "tasklist.md に ## Verification セクションが存在しません。"
            "検証が行われていない状態では done できません。"
        ]
        # 節見出しごと fence に飲まれている最単純形では verification_section_found=False
        # になる。併記しないと「節は見えているのに存在しないと言われる」だけで
        # 原因が読み取れない（design.md D5 判定順 1 / planning R4 M-4）
        if fenced_heading_starts:
            base.append(_fenced_heading_message(fenced_heading_starts))
        return base

    messages: list[str] = []
    if line_violations:
        messages.append(
            f"## Verification に schema 違反行が {len(line_violations)} 件あります:\n"
            + "\n".join(_labeled_violation_line(v) for v in line_violations[:5])
            + _legacy_writer_headline(line_violations)
        )
    if section_fence_starts:
        # design.md:200 / :498 は「原文行番号」（人間可読・1 始まり）を要求する。
        # section_fence_starts 自体は strip_fenced_lines_marked() の 0 始まり index
        # のままにし（判定ロジックは不変）、提示直前にのみ +1 する（impl-gate R7 A23）。
        one_indexed_section_fence_starts = [i + 1 for i in section_fence_starts]
        messages.append(
            "## Verification 節に fenced code block が重なっています"
            f"（{len(section_fence_starts)} 件 / 開始行 {one_indexed_section_fence_starts}）。"
            "fence 内の行は guard から不可視になるため schema 違反として扱います。"
        )
    if fenced_heading_starts:
        messages.append(_fenced_heading_message(fenced_heading_starts))
    if messages:
        # unfinished は違反と併記する（消えない）
        if unfinished:
            messages.append(_unfinished_message(unfinished))
        return messages

    if not verification_data_rows:
        messages = [
            "## Verification セクションに検証行がありません。"
            "空、「なし」のみ、header 行と separator しか無い表、および "
            "`security_evidence` 行・`refactor-checkpoint` 行だけの表（AC 検証行 `method=ac:` が 0 件）が"
            "該当します（status セルが許容値 `pending` / `pass` / `fail` / "
            "`N/A` / `unsupported` と一致しない data 行は別の理由で報告されます）。"
            "少なくとも 1 つの AC 検証行が必要です。"
        ]
        # AC-9 第 5 形では evidence / refactor-checkpoint 行の未完了が残りうる。
        # 併記しないと未完了行が実在するのに「検証行がありません」とだけ言い、握りつぶす
        if unfinished:
            messages.append(_unfinished_message(unfinished))
        return messages
    if unfinished:
        return [_unfinished_message(unfinished)]
    return []


def _unfinished_message(unfinished: list[str]) -> str:
    """未完了/失敗行のメッセージ。違反との併記・検証行 0 件との併記・単独の 3 経路で共有する。

    行は agent が書いた内容なので必ず `safe_for_output()` を通す（制御文字で block 理由を
    隠させない / AC-5）。経路ごとに書き写すと付け忘れの面が開くので 1 関数に集約する。
    """
    return (
        f"Verification に未完了/失敗が {len(unfinished)} 件あります:\n"
        + "\n".join(safe_for_output(x) for x in unfinished[:5])
    )


def _fenced_heading_message(starts: list[int]) -> str:
    """design.md D5 判定順 2（fenced_heading）: 該当行は全件列挙する。

    1 件ずつ提示すると「直した → まだ block」を繰り返し、回復手順が
    効かないように見える（design.md D5）。

    `starts` は `strip_fenced_lines_marked()` の 0 始まり原文 index のまま
    受け取る（判定ロジックは不変）。design.md:200 / :498 が要求する
    「原文行番号」（人間可読・1 始まり）へは提示直前にのみ変換する
    （impl-gate R7 A23）。
    """
    one_indexed_starts = [i + 1 for i in starts]
    return (
        'fenced code block の中に "## Verification" 見出しがあります'
        f"（{len(starts)} 件 / 行 {one_indexed_starts}）。"
        "この違反は Notes へ移しても解除されません。"
        'fence 内の見出し行そのものを書き換えてください（例: "Verification 節の例:"）。'
    )


# AC ID の形は文法ブロックの `AC_ID`（`lib.done_guard._AC_ID_CORE`）を再利用する。前後に英数字が
# 続く形（`MAC-1` / `AC-12x3`）は拾わない。提示ラベルの判定だけに使い、受理判定には使わない
_AC_ID_TOKEN = re.compile(r"(?<![A-Za-z0-9])" + _AC_ID_CORE + r"(?![0-9A-Za-z])")


def _labeled_violation_line(raw: str) -> str:
    """design.md D5「違反行の提示ラベル」。判定には一切使わない、提示だけの分類。

    AC-5: safe_for_output() で無害化してから 80 文字に打ち切る。raw 自体は
    ラベル判定にのみ使い、出力には安全化済みの `safe` だけを載せる。
    """
    safe = safe_for_output(raw)[:80]
    lowered = raw.lower()
    is_possibly_unfinished = (
        any(token in lowered for token in ("pending", "fail", "pass", "n/a", "unsupported"))
        or any(token in raw for token in ("method=", "security_evidence", "refactor-checkpoint"))
        or _AC_ID_TOKEN.search(raw) is not None
    )
    # 案内側（`done_block_message._has_legacy_security_evidence_writer_shape`）は表示行で判定する。
    # ラベルも同じ表示行（無害化・80 文字切り詰め後）で判定し、食い違わないようにする
    if _is_legacy_writer_display(raw):
        # 外部 writer の legacy 行は agent が書き直すと契約違反になる。下の外部 writer 分岐の
        # 案内（削除も移動もせず、残るのがこの行だけなら停止して人間へ報告）と揃える（AC-20）
        label = "外部 writer の legacy 行 — 書き直さず、削除も移動もしない（外部 security evidence 行の案内を参照）"
    elif is_possibly_unfinished:
        label = "未完了の可能性がある検証行 — Notes へ移さず canonical 表行へ書き直す"
    else:
        # 判定語は検証行を拾い切れない（開いたコーパス）。移動を断定せず、書き直しを先に案内する
        label = (
            "schema 違反行 — 検証の結果・予定・未実施を書いた行なら canonical 表行へ書き直す。"
            "散文・凡例・補助表だけを ## Verification Notes へ移す"
        )
    return f"  {safe}  [{label}]"


def validate_done_preconditions(cwd: Path) -> tuple[bool, str, str]:
    """Validate that 'done' is justified by checking tasklist.md.

    Returns (is_valid, error_message, checked_path). When is_valid is False,
    the stop hook should block with error_message explaining what's missing.
    checked_path is the tasklist.md path that was inspected (empty if none).

    検査対象は **この worktree に bind された steering だけ**。
    binding が無ければ検査せず `(True, "", "")` を返し、呼び出し元が warn に降格する（AC-2）。

    **"cannot be skipped" とは言えない**: `binding.json` を書くのは
    `commands/gdd-dev.md` の LLM 手順（`gdd_task_binding.py upsert-from-state`）で、
    hook が強制していない。その手順が飛べば guard は warn に降格する。
    コードとして走る点は変わらないが、保証の水準は「bind 済みなら fail-closed」であって
    「どんな状況でも fail-closed」ではない。
    """
    tasklist_path, containment_error = _guard_tasklist(cwd)
    if containment_error:
        return False, containment_error, ""
    if tasklist_path is None:
        return True, "", ""

    checked_path = str(tasklist_path)

    # fenced code block は tasklist の構造ではない（`#### Steps` に貼った計画コード）。
    # **Check 1 と Check 2 が同じ「構造行」を見る**ように、ここで 1 度だけ剥がす。
    # 片方だけ剥がすと、同じ恒久 block がもう片方で再現する。
    try:
        tasklist_bytes = read_regular_bytes(tasklist_path)
    except OSError:  # FIFO・ディレクトリ・ELOOP・EACCES を「無い」と取り違えると done が素通りする
        return False, f"tasklist.md を通常のファイルとして読めないため done を許可しません: {safe_for_output(checked_path)}", ""
    if tasklist_bytes is None:  # tasklist が無い = task-breakdown を経ていない軽量タスク。検査対象なし。
        return True, "", ""
    tasklist_text = tasklist_bytes.decode("utf-8")
    # 行区切り文字・fence の閉じ忘れ（lib.tasklist_structure）。Check 1 と Check 2 が同じ「構造行」を見る
    errors, structural_lines, fence_before, fenced_heading_lines = tasklist_structure(tasklist_text)
    # Check 1: Current Task / Pending Tasks の残り
    errors.extend(_remaining_task_errors(*_scan_remaining_tasks(structural_lines)))
    # fence_before / fenced_heading_lines を明示的に渡す。既定値 None のまま渡すと
    # `_scan_verification` 側で fence 違反が常に 0 件になる fail-open の面になる
    # （design.md § 4 / lib.done_guard._scan_verification の docstring）。
    errors.extend(
        _verification_errors(
            *_scan_verification(
                structural_lines,
                fence_before=fence_before,
                fenced_heading_lines=fenced_heading_lines,
            )
        )
    )
    # Check 3: state.md の Route In Progress 残存（行区切り文字の検査を含む。lib.done_guard）
    errors.extend(_route_in_progress_errors(tasklist_path))

    if errors:
        return False, "\n".join(errors), checked_path
    return True, "", checked_path


def _active_requirements_path(cwd: Path) -> Path | None:
    """Return requirements.md path for the **bind された** steering task, or None.

    done guard と**同じ steering** を見る必要がある。旧実装は `git worktree list` を
    舐めて最初に見つかった steering を採る探索を経由していたため、done guard を
    bind 限定にした後もここだけが他 worktree を読み、**他人の未完 Follow-up Stage で
    block される**（自分の worktree を直しても解除できない）状態が残っていた
    ―― bind 限定で塞いだ症状そのもの。
    bind 不能なら `None`（follow-up チェックは no-op になる。AC-2 の warn 降格と整合）。
    """
    bind = _resolve_bind_memoized(cwd)
    if bind.status != "resolved" or bind.steering_dir is None:
        return None
    return bind.steering_dir / "requirements.md"


def _emit_block(reason_text: str) -> None:
    """block payload を stdout へ出して停止判断を Claude Code へ返す。"""
    print(json.dumps({"decision": "block", "reason": reason_text}, ensure_ascii=False))
    raise SystemExit(0)


def _require_next_action_block(reason: str, last_output: str) -> None:
    """OT-F10 D2: どの pause / done の前にも `👤 次にすること` ブロックを要求する。

    内部エラーは fail-open（例外は呼び出し元の try/except へ伝播する）。
    """
    if reason in _NEXT_ACTION_EXEMPT or has_next_action_block(last_output or ""):
        return
    _emit_block(
        f"`👤 次にすること` ブロックが見当たりません（reason={reason}）。\n\n"
        "停止出力の末尾に reason に対応した「👤 次にすること」ブロックを追加してください。\n"
        "（`references/output-format.md` § 停止時の「👤 次にすること」マップ を参照）"
    )


def _stop_for_non_done_reason(reason: str, state_p: Path, proj_root: Path, *, system_message: str = "") -> None:
    """done 以外の停止理由を処理して終了する（tasklist 検証は不要）。
    system_message（HITL の lint の警告など）は、停止を許すこの時点で 1 回だけ stdout に出す
    （先に出すと、後の block の payload と JSON が 2 つ並ぶ）。

    human-check-waiting / clarification-needed / external-review-waiting /
    auth-waiting は pause point であって terminal state ではないので state.md を
    保持し、iteration の文脈を持ったまま再開できるようにする
    （OT-F3 external review loop / auth-waiting は SSO・認証再ログイン後の再開）。
    """
    if system_message:
        print(json.dumps({"systemMessage": system_message}, ensure_ascii=False))
    if reason in STATE_KEEPING_STOP_REASONS:
        print(
            f"GDD session paused (reason={reason}). "
            "state.md を保持します — 次回 /gdd-dev で再開できます。 "
            + goal_guard_message(reason),
            file=sys.stderr,
        )
    else:
        state_p.unlink(missing_ok=True)
        print(
            f"GDD session ended (reason={reason}). "
            "state.md をクリアしました — 次回 /gdd-dev は新規セッションになります。 "
            + goal_guard_message(reason),
            file=sys.stderr,
        )
    raise SystemExit(0)


def _bind_unresolved_warning(proj_root: Path) -> str:
    """bind 不能時に allow 経路で出す systemMessage payload（不要なら空文字）。

    AC-2 / CT-2: bind 不能なら done guard は **block ではなく warn** に降格する。
    旧実装はこの状況で他 worktree の tasklist を漁って誤 block していた。
    「検査できなかった」ことを伝えないと guard が黙って無効化されたのと区別が
    つかないので、候補一覧を添えて systemMessage で明示する。候補は
    `resolve_bind()` が slug + worktree basename まで絞ったもの（絶対パスは出さない）。

    **文字列を作るだけで print はしない**（Attempt 4 advisory 4）。即 print すると
    以降が block payload を出した瞬間に stdout へ JSON が 2 個並び、Claude Code から
    見て壊れた payload になる。今は呼び先が両方 bind gate を持つので同時に出ないが、
    **その到達不能性は呼び先の実装に依存する** — 出力順で構造的に塞ぐ。
    """
    bind = _resolve_bind_memoized(proj_root)
    if bind.status == "resolved":
        return ""
    candidates_text = "\n".join(
        f"  - {c.get('slug', '')} @ {c.get('worktree', '')}" for c in bind.candidates
    ) or "  (候補なし)"
    return json.dumps(
        {
            "continue": True,
            "systemMessage": (
                "[gdd:bind-unresolved] このセッションを GDD task に紐付ける "
                "binding.json が見つかりません。done guard は今回 warn のみで"
                "停止を通します（bind 済み task は従来どおり block されます）。\n"
                f"候補:\n{candidates_text}"
            ),
        },
        ensure_ascii=False,
    )


def _validate_done_or_block(proj_root: Path) -> tuple[bool, str, str]:
    try:
        return validate_done_preconditions(proj_root)
    except Exception as exc:
        _emit_block(
            "done guard の検証中にエラーが発生しました。"
            "検証証跡を確認できない状態では done を許可しません（fail-closed）。\n\n"
            f"エラー: {type(exc).__name__}: {exc}\n\n"
            "--- 推奨アクション ---\n"
            "• tasklist.md / state.md が読める状態か確認し、壊れていれば修復してください。\n"
            "• ## Verification に pass 済みの検証行があることを確認してください。\n"
            "• 修復後に <gdd-stop reason=\"done\"> を再出力してください。"
        )
        raise  # 到達しない（_emit_block が SystemExit する）


def _require_next_plan_block(proj_root: Path, last_output: str) -> None:
    """OT-F9 E2: Follow-up Stage Lane に未完があれば `### 次の計画` を要求する。

    requirements.md が読めなければ未完扱い。ほかの内部エラーは呼び出し元の except で握り潰す（fail-open）。
    """
    req_path = _active_requirements_path(proj_root)
    if not (req_path and requirements_lane_pending(req_path)):
        return
    output = last_output or ""
    if not has_next_plan_block(output):
        _emit_block(
            "`Planned Follow-up Stage Lane` に未完 stage があります。\n\n"
            "停止出力に以下の形式で `### 次の計画` ブロックを追加してください：\n\n"
            "```\n"
            "### 次の計画\n"
            "現在: <完了 stage>\n"
            "次: <次の stage id>（<一言概要>）\n"
            "Registry: created / pending\n"
            "「次に進んで」で次の stage を開始できます。\n"
            "```"
        )
    if registry_creation_claimed(output) and not continuation_file_exists(proj_root, output):
        _emit_block(
            "`Registry: created` と主張していますが、"
            "対応する `.claude/gdd-continuations/<id>.json` が見つかりません。\n\n"
            "実際にファイルを作成するか、`Registry: pending` に変更してください。"
        )


def _finish_allowed_done(
    reason: str,
    state_p: Path,
    proj_root: Path,
    *,
    session_id: str,
    last_output: str,
    checked_path: str,
    bind_unresolved_warning: str,
) -> None:
    # bind 不能のときは `checked_path` が空になる。空のまま seed を書くと
    # `next_task_hint` / `steering_dir` を持たない**消費不能な seed** ができる。
    # marker を消す経路は `lib/post_merge_continuation.py` の `resolve_block` だけで、
    # merge cue と post-merge 完了の両方が揃ったときしか消さないので、
    # 消費不能な seed は**消えずに溜まり続ける**。
    # さらに `tasklist_path=""` は `Path("").parent` = `Path(".")` になり、
    # requirements をプロセス cwd 相対で読む経路を作る。書かないのが正しい。
    if checked_path:
        try:
            write_post_merge_continuation(
                proj_root,
                session_id=session_id,
                tasklist_path=checked_path,
                last_output=last_output,
            )
        except Exception:
            pass
    if bind_unresolved_warning:
        # 出力するのは block 判定が全部終わった allow 経路だけ（AC-2 は殺さない）。
        print(bind_unresolved_warning)
    state_p.unlink(missing_ok=True)
    print(goal_guard_message(reason), file=sys.stderr)
    raise SystemExit(0)


def _done_block_payload(error_msg: str, checked_path: str, bind_unresolved_warning: str) -> str:
    """done 前提条件を満たさないときの block reason を組み立てる（DX1 + DX5）。"""
    path_hint = f"\n検査対象: {checked_path}" if checked_path else ""
    # bind 不能なまま fallback で検査対象を選んで block する場合、**その事実を block reason に
    # 畳み込む**（completion-check 2026-08-30 の M-3）。`bind_unresolved_warning` は allow 経路の
    # JSON なので block 側では出力できない（JSON を 2 個出すことになる）。情報が無いと、
    # binding 手順が飛んだ worktree で「無関係な steering を指す block」の理由に辿り着けない。
    unbound_hint = (
        "\n[gdd:bind-unresolved] binding.json が無いため、この worktree の .steering/ に"
        "あった唯一の steering を検査対象にしました。対象が違う場合は binding を作り直してください。"
        if bind_unresolved_warning and checked_path
        else ""
    )
    return (
        "done 前提条件が満たされていません（実装漏れ防止 guard — hook-enforced）。"
        + path_hint + unbound_hint + "\n\n"
        + error_msg
        + "\n\n--- 推奨アクション ---\n"
        + _build_recovery_hints(error_msg)
        + "\n\n--- なぜこの guard があるか ---\n"
        + _build_why_explanations(error_msg)
    )


def try_stop_with_done_guard(
    reason: str,
    state_p: Path,
    proj_root: Path,
    *,
    session_id: str = "",
    last_output: str = "",
    plugin_root: Path | None = None,
    before_state_clear: Callable[[str], None] | None = None,
) -> None:
    """Allow stop if reason is non-done, or if done preconditions are met.
    Raises SystemExit(0) on success. On failure, prints a block payload and
    raises SystemExit(0) to return the block decision to Claude Code.
    The polling cap is applied first, so every check below sees the effective
    reason. before_state_clear is called with it before any other check when the
    stop would clear the loop state (it exits when it blocks)."""
    reason = escalate_polling_reason(reason, lambda: _steering_candidate(proj_root, "state.md"), proj_root)
    if before_state_clear and reason not in STATE_KEEPING_STOP_REASONS:
        before_state_clear(reason)
    _require_next_action_block(reason, last_output)
    hitl_warning = enforce_hitl_lint_gate(proj_root, reason, last_output, plugin_root=plugin_root)

    if reason == "human-check-waiting" and (pushback := autonomy_pushback.run_within_deadline(
        lambda: autonomy_pushback.human_check_reason(
            _worktree_toplevel(proj_root),
            _bound_steering_file(proj_root, "worklog.md")
            if _resolve_bind_memoized(proj_root).status == "resolved" else None,
        ), proj_root,
    )):
        _emit_block(pushback)
    if reason not in DONE_REASONS:
        _stop_for_non_done_reason(reason, state_p, proj_root, system_message=hitl_warning)

    # reason == "done": validate preconditions
    bind_unresolved_warning = _bind_unresolved_warning(proj_root)
    is_valid, error_msg, checked_path = _validate_done_or_block(proj_root)

    if is_valid:
        try:
            _require_next_plan_block(proj_root, last_output)
        except SystemExit:
            raise
        except Exception:
            pass  # fail-open: internal error → allow stop
        _finish_allowed_done(
            reason,
            state_p,
            proj_root,
            session_id=session_id,
            last_output=last_output,
            checked_path=checked_path,
            bind_unresolved_warning=bind_unresolved_warning,
        )

    _emit_block(_done_block_payload(error_msg, checked_path, bind_unresolved_warning))


def _count_task_progress(tl_text: str) -> str:
    """Parse tasklist.md text and return a progress string like ' | tasks: 2/5 done, current: T1 | ...'."""
    # done guard（`validate_done_preconditions`）と**同じ構造行**を数える。
    # 片方だけ fence を剥がすと、guard は未完了が多いと言うのに、
    # 進捗表示はほとんど完了と出る、という食い違いが出る（実測）。
    # 受理面も**名前抽出も** `lib/tasklist_parse` に集約する（AC-5 / CT-4）。
    # 第 2 戻り値（閉じ忘れ）は**意図して捨てる**。この関数は done ではない
    # 継続ターンの `[GDD #N] ...` 表示から呼ばれるので、閉じ忘れ tasklist では
    # **done guard を経ずに過少カウントが単独で出る**（実データにも該当があった）。
    # それでもゲートしないのは、ここが表示専用で停止判断を持たないため。
    # block 相当の分岐を足すと guard と表示の 2 箇所に同じ判断が生まれ、
    # T-3 が潰したばかりの非対称を作り直すことになる。
    structural_lines, _fence_unclosed = strip_fenced_lines(tl_text)
    c_count, p_count, cur_count, cur_task_name = _tally_task_sections(structural_lines)
    total = c_count + p_count + cur_count
    if total <= 0:
        return ""
    progress = f" | tasks: {c_count}/{total} done"
    if cur_task_name:
        # **毎ターン発火する継続注入テキスト**も同じ trust boundary（M-3）。
        # `validate_done_preconditions` の 4 経路だけ無害化しても、ここが素通りでは
        # 「すべての出力経路が 1 関数を通る」規律から外れる。
        progress += f", current: {safe_for_output(cur_task_name)[:50]}"
    return progress


def _find_tasklist_text_for_progress(proj_root: Path) -> str:
    """継続ターンの進捗表示に使う tasklist.md 本文（AC-7）。

    旧実装は `git worktree list --porcelain` を舐めて「最初に `.steering` を持つ
    worktree」を読み、他タスクの件数と Current Task 名を `[GDD #N]` に載せていた（実測）。
    """
    tasklist = _bound_steering_file(proj_root, "tasklist.md")
    return tasklist.read_text(encoding="utf-8") if tasklist else ""


PHASE_MARKER = re.compile(r'<gdd-phase>([^<]+)</gdd-phase>')


def latest_steering_resume_from(root: Path) -> str:
    """bind 済み steering の `state.md` から Resume From を読む（AC-7 / AC-8-2）。

    名前の降順で 1 件目を見る旧実装は、同じ worktree に**別タスクの steering**が
    後から増えると（= 名前が新しい）そちらの `human-check-waiting` で停止していた。
    走査は `lib/tasklist_parse.resume_from_value()` へ委譲する。
    """
    state_file = _bound_steering_file(root, "state.md")
    if state_file is None:
        return ""
    # fenced code block の中は書式の記入例であって現在値ではない
    # （正本は lib/tasklist_parse.strip_fenced_blocks）。
    # `errors="replace"`: 呼び出し元が `except Exception` で握り潰すため、不正バイトだと
    # markerless human check の停止が沈黙のうちに skip される。
    return resume_from_value(
        strip_fenced_blocks(state_file.read_text(encoding="utf-8", errors="replace"))
    )


def _read_hook_input() -> tuple[dict, Path]:
    plugin_root = Path(
        os.environ.get("CLAUDE_PLUGIN_ROOT")
        or os.environ.get("GDD_PLUGIN_ROOT")
        or os.getcwd()
    ).resolve()
    hook_input_text = os.environ.get("GDD_HOOK_INPUT", "")
    try:
        hook_input = json.loads(hook_input_text) if hook_input_text else {}
    except json.JSONDecodeError:
        hook_input = {}
    return hook_input, plugin_root


def _post_merge_precheck(
    project_root: Path, transcript_path_raw: str, transcript_path: Path
) -> ParsedTranscript | None:
    """state ファイル検査より **前** に post-merge continuation を判定する。

    merge 時点では GDD セッションが名目上 inactive（active: false / state 不在）で
    ありうるため。transcript を parse するのは marker ファイルがあるときだけで、
    よくある非 GDD 経路（state 無し + marker 無し）は transcript に触れない。

    Copilot レビュー是正 (PR #31, commit 6cf2773 への指摘): この check は
    `tv.last_user_text`（peer turn を除外済み。Finding Z 参照）が `mergeした` 等に
    一致するかだけを見ており、直近の実会話ターンが peer 由来かどうかを確認して
    いなかった。`[human: "mergeした", peer: "..."]` では peer 受信を契機に古い
    `mergeした` を根拠として `decision:block` が出て workflow が再開してしまう
    （後段の `looks_like_gdd_continuation()` 側の peer guard より**前**にこの check が
    走るため、その guard に到達する前に再開が確定する）。「peer message は停止中の
    workflow を再開させない」という他の権限境界（Finding Z 含む）と同じ原則を、
    ここでも先行判定する。
    """
    if not (
        transcript_path_raw
        and transcript_path.exists()
        and os.path.lexists(post_merge_state_path(project_root))
    ):
        return None
    try:
        if last_user_turn_is_peer(transcript_path):
            return None
        tv = parse_transcript(transcript_path, project_root)
    except Exception as exc:
        append_hook_error(project_root, "post_merge_precheck", repr(exc))
        return None
    maybe_block_incomplete_post_merge_continuation(project_root, tv)
    return tv


def _load_active_state(state_path: Path, project_root: Path) -> tuple[dict, str]:
    """state.md を読み、停止すべきでない状態なら `(frontmatter, prompt_body)` を返す。"""
    try:
        frontmatter, prompt_body = parse_state(state_path)
    except Exception as exc:
        suppress_hook_integrity_failure(
            project_root, "parse_state", f"{type(exc).__name__}: {exc} (state_path={state_path})"
        )

    # active: false means the session was explicitly marked complete — allow stop immediately.
    # Without this guard, looks_like_gdd_continuation() can fire a continuation block
    # even after the AI sets active: false as a manual done workaround.
    if frontmatter.get("active", "").lower() != "true":
        raise SystemExit(0)

    # Cross-runtime guard: if the local state file was created by a different runtime
    # (e.g. Cursor's /gdd-dev) than the current Stop hook's runtime, exit silently.
    # Prevents Claude Code from auto-continuing a stale Cursor session (and vice versa)
    # when the user switches runtimes without cleaning up `.claude/gdd-dev.local.md`.
    hook_runtime = "claude_code" if os.environ.get("CLAUDE_CODE_SESSION_ID") else "cursor"
    state_runtime = frontmatter.get("workflow_runtime", "")
    if state_runtime and state_runtime != hook_runtime:
        raise SystemExit(0)
    return frontmatter, prompt_body


def _session_guard(frontmatter: dict, hook_input: dict, project_root: Path) -> str:
    """session_id の整合を確認し、state 側の session_id を返す。"""
    state_session = frontmatter.get("session_id", "")
    hook_session = hook_input.get("session_id", "") or ""
    if not state_session:
        # Cursor sessions never set CLAUDE_CODE_SESSION_ID, so session_id is always empty.
        # For Cursor: skip the error block and continue processing so cleanup (done/cancelled)
        # still runs. For other runtimes: exit silently (don't block).
        #
        # Previously this emitted decision:block, which caused Claude to receive the error
        # as "Stop hook feedback:" and mistakenly interpret it as a directive to start GDD
        # brainstorming. Switching to a silent exit + stderr warning prevents that misfire.
        if frontmatter.get("workflow_runtime", "") != "cursor":
            message = (
                ".claude/gdd-dev.local.md が active: true ですが session_id が空です。"
                " 自動継続を抑止します。再開するには /gdd-dev を明示してください。"
            )
            append_hook_error(project_root, "empty_session_id", message)
            print(f"GDD Stop hook: {message}", file=sys.stderr)
            raise SystemExit(0)
    elif state_session != hook_session:
        raise SystemExit(0)
    return state_session


def _transcript_guard(project_root: Path, transcript_path_raw: str, transcript_path: Path) -> None:
    if not transcript_path_raw:
        # Side windows and some host-managed stop-hook invocations may omit
        # transcript_path while a stale active state file exists in cwd. There is no
        # current-turn evidence to inspect, so the safest behavior is a fully silent
        # exit: keep state for explicit /gdd-dev resume, but do not spam stderr or
        # hook-errors.log every turn.
        suppress_hook_integrity_failure(
            project_root, "transcript_path", "missing transcript_path", quiet=True
        )
    if not transcript_path.exists():
        suppress_hook_integrity_failure(
            project_root, "transcript_path", f"not found: {transcript_path}"
        )


def _check_stop_markers(
    tv: ParsedTranscript,
    state_path: Path,
    project_root: Path,
    *,
    session_id: str,
    last_output: str,
    plugin_root: Path | None = None,
    before_state_clear: Callable[[str], None] | None = None,
) -> str:
    """`<gdd-stop>` マーカーを本文 → tool result の順に見る。tool result 本文を返す。

    Fallback 1 のラベルは permanent。削除条件は、host が subagent / tool 出力の
    マーカーを main assistant text へ必ずエコーすると保証したとき。
    gdd-brainstorming が subagent として走ると、その出力（`<gdd-stop>` を含む）は
    assistant text ではなく user role の tool_result として現れる。subagent が
    正しくマーカーを出したのに main session がエコーし忘れた場合をここで拾う。background で起動した
    subagent の返りは完了通知（user text）で届き、tool_result ではないので、ここでは拾えない。
    """
    match = STOP_PATTERN.search(last_output)
    if match and match.group(1) in ALLOWED_STOP_REASONS:
        try_stop_with_done_guard(
            match.group(1), state_path, project_root,
            session_id=session_id, last_output=last_output, plugin_root=plugin_root,
            before_state_clear=before_state_clear,
        )

    last_tool_text = ""
    try:
        last_tool_text = tv.last_tool_result_text
        tool_match = STOP_PATTERN.search(last_tool_text)
        if tool_match and tool_match.group(1) in ALLOWED_STOP_REASONS:
            try_stop_with_done_guard(
                tool_match.group(1), state_path, project_root,
                session_id=session_id, last_output=last_output, plugin_root=plugin_root,
                before_state_clear=before_state_clear,
            )
    except SystemExit:
        raise
    except Exception as exc:
        append_hook_error(project_root, "last_tool_result_text", str(exc))
    return last_tool_text


def _human_check_state_fallback(
    state_path: Path,
    project_root: Path,
    *,
    session_id: str,
    last_output: str,
    last_tool_text: str,
    plugin_root: Path | None = None,
    before_state_clear: Callable[[str], None] | None = None,
) -> bool:
    """markerless の human-check 復帰信号。抑止したら True を返す。

    transitional fallback label: `.steering/*/state.md` の
    "Resume From: human-check-waiting"。削除条件は、すべての human-check 経路で
    main assistant text のマーカー出力が契約テストされたとき。
    brainstorming skill は human-check gate に達すると必ず
    "Resume From: human-check-waiting"（コロン区切り、markdown list item 形式）を書く。
    これは markerless な復帰信号であって primary な停止信号ではない。現在の
    assistant / tool 出力も human-check 面に見えるときだけ許可する。assistant /
    tool 出力の明示 `<gdd-stop>` が primary 経路であることは変わらない。

    NOTE: ここで検出するのは human-check-waiting だけ。done / cancelled は常に
    `<gdd-stop reason="...">` で明示される（Fallback 1/2）。state.md 経由で done を
    検出すると、前セッションの state.md（Resume From: done）が無関係なセッションで
    done 前提条件 guard を誤発火させる。
    """
    try:
        # state field は `<value> | <key>: <detail>` の形を取る（references/state-machine.md
        # § state field のフォーマット検証）。比べるのは `|` より前の先頭セグメントだけ。
        if latest_steering_resume_from(project_root).split("|", 1)[0].strip() != "human-check-waiting":
            return False
        if allow_state_human_check_fallback(last_output, last_tool_text):
            try_stop_with_done_guard(
                "human-check-waiting", state_path, project_root,
                session_id=session_id, last_output=last_output, plugin_root=plugin_root,
                before_state_clear=before_state_clear,
            )
        print(
            "GDD Stop hook: state.md says human-check-waiting, but current output "
            "does not look like a human-check surface; markerless state fallback suppressed.",
            file=sys.stderr,
        )
        return True
    except SystemExit:
        raise
    except Exception as exc:
        append_hook_error(project_root, "state_human_check_fallback", str(exc))
        return False


def _continuation_intent_guard(
    tv: ParsedTranscript,
    project_root: Path,
    transcript_path_raw: str,
    transcript_path: Path,
    last_output: str,
) -> None:
    """継続意図が無ければ自動継続を抑止して終了する。

    ディスクに残った `.claude/gdd-dev.local.md`（何時間も前に書かれた Cursor
    セッションを含む）が、次の Stop hook 発火で無関係な会話を乗っ取るのを防ぐ。
    Fallback label: permanent。削除条件: stale な local state が chat / runtime を
    跨いで生き残りうる限り無し。state ファイルはこの終了経路でも保持するので、
    明示 `/gdd-dev`（または適格なユーザー返信）で文脈を失わずに再開できる。

    PR #31 レビュー Finding Z: `parse_transcript()` は peer turn を last_user_text
    候補から除外するため、直近の実会話ターンが peer 由来のときは last_user_text が
    「1 つ前の人間本人の発話」のまま stale で残る（例: [human: "/gdd-dev ...",
    peer: "中止"] では last_user_text が古い "/gdd-dev ..." のまま）。
    looks_like_gdd_continuation() だけで判定すると peer 受信を契機に古い継続意図が
    復活するため、last_user_turn_is_peer() を先行判定する（peer message は human
    approval を代替しない、という他の権限境界と同じ結論）。
    """
    try:
        last_user_input = tv.last_user_text
    except Exception:
        last_user_input = ""
    try:
        last_turn_is_peer = bool(transcript_path_raw) and last_user_turn_is_peer(transcript_path)
    except Exception as exc:
        # 判定できないときは peer と同じく止める側に倒す（古い継続意図で再開しない）。
        append_hook_error(project_root, "last_user_turn_is_peer", repr(exc))
        last_turn_is_peer = True
    if last_turn_is_peer:
        print(
            "GDD Stop hook: 直近の実会話ターンが別セッションからのメッセージ（peer）"
            "であるか、それを判定できないため、継続意図を判定せず自動継続を抑止しました。state.md は"
            "保持しています — 再開するには `/gdd-dev` を明示してください。",
            file=sys.stderr,
        )
        raise SystemExit(0)
    if not looks_like_gdd_continuation(last_user_input, last_output):
        print(
            "GDD Stop hook: 直近のユーザー入力に GDD 継続意図が見えないため、"
            "自動継続を抑止しました。state.md は保持しています — "
            "再開するには `/gdd-dev` を明示してください。",
            file=sys.stderr,
        )
        raise SystemExit(0)

    # In-flight guard: suppress continuation nudge while a dispatched subagent's
    # tool_result has not yet arrived, or a background wait Bash (allowlisted forms:
    # a bare `sleep <seconds>` timer or a wait-until.py run) started within the same
    # window as the merge-wait pushback has not finished, or an agent resumed by
    # SendMessage within that window has not ended (any_resumed_agent_running).
    # Fail-open: detection errors do not block legitimate nudges.
    try:
        now = time.time()
        since = now - autonomy_pushback.BACKGROUND_WINDOW_SECONDS
        if (subagent_in_flight_from_parsed(tv, project_root) or any_background_wait_running(tv, since, now)
                or any_resumed_agent_running(tv, since, now)):
            raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as exc:
        append_hook_error(project_root, "subagent_in_flight_guard", str(exc))


def _stop_on_human_check_loophole(
    state_path: Path, frontmatter: dict, prompt_body: str
) -> None:
    """state.md が human-check-waiting で固着し、markerless fallback が抑止された形。

    継続意図 guard は通過しているのにこの条件は自然には解けないので、fresh ターン
    （自律ドライバが `/gdd-dev` を繰り返す、報告された元のバグ形。
    stop_hook_active=false の到達は前回 block から
    GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS を超えないと ceiling を reset しないため
    enforce_consecutive_block_ceiling は発火しない）でも、同一ターンの
    stop_hook_active=true 連鎖（ceiling を待っても同じ結末が最大
    STOP_HOOK_MAX_CONSECUTIVE_BLOCKS 回遅れるだけ）でも起こりうる。
    どちらでもこの条件で更に block を強いる正当な理由は無いので、
    stop_hook_active に関係なく即停止する。
    """
    frontmatter["consecutive_stop_hook_blocks"] = "0"
    write_state(state_path, frontmatter, prompt_body)
    print(
        "GDD Stop hook: state.md is stuck at human-check-waiting but the "
        "current output does not look like a human-check surface, and the "
        "latest turn still shows GDD continuation intent. Stopping "
        "immediately instead of forcing another block — state.md/"
        "tasklist.md are preserved, resume with /gdd-dev after checking "
        "the actual state.",
        file=sys.stderr,
    )
    raise SystemExit(0)


def _detect_phase(frontmatter: dict, last_output: str) -> str:
    """model routing 用の phase を決める（workflow の SSOT は state.md の Resume From）。

    Skills は phase 遷移ヘッダで `<gdd-phase>skill-name</gdd-phase>` を出すので、
    明示マーカーを heuristic なテキスト一致より優先する。
    """
    current_phase = frontmatter.get(
        "detected_phase", frontmatter.get("workflow_phase", "gdd-brainstorming")
    )
    phase_match = PHASE_MARKER.search(last_output)
    if phase_match:
        # 表記ゆれ（大文字小文字・空白）を正規化し（独立レビュー round 4 F2）、
        # 既知 phase 名の形（英数字をハイフン区切り、先頭末尾・連続ハイフン無し）
        # に収まらない値（`PHASE_MARKER` の `[^<]+` は改行にもマッチするため、
        # 偽の frontmatter 行を注入して `write_state()` 経由で guard を
        # 無効化しうる。round 7 H-1）は受理せず下の heuristic フォールバックへ
        # fail-closed で委ねる。`[a-z0-9-]+` だけだと `-`/`---` のような
        # ハイフンのみの値も通り、`state_io.py::parse_state()` の frontmatter
        # 終端 `"---"` と衝突しうる（round 9 H-1）ため、単語をハイフン 1 個で
        # つなぐ形に締める。
        normalized = phase_match.group(1).strip().lower()
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
            return normalized
    # Fallback: heuristic text match on last assistant output.
    # Fallback label: transitional. Delete condition: remove after every phase
    # transition emits <gdd-phase> and scenario evals prove no phase text match
    # is needed for resume/model routing.
    lower_output = last_output.lower()
    for candidate in GDD_PHASE_MARKERS:
        if candidate in lower_output:
            return candidate
    # marker 未検出時も対称に正規化する（round 5 F-5）。
    return current_phase.strip().lower()


def _handoff_missing_warning(
    frontmatter: dict, project_root: Path, previous_phase: str, current_phase: str, last_output: str
) -> str:
    """phase 遷移時に Handoff Summary が無ければ warning 文字列を返す。

    disk 上の Resume From（canonical SSOT）が判明している場合のみ、それが変化したか
    どうかで warning を gate する。`.steering` が見つからない（フォーマルな GDD 追跡が
    ないセッション）場合は、既存の回帰テストの挙動を壊さないよう常に「変化あり」扱いに
    フォールバックする。
    """
    if not (previous_phase and previous_phase != current_phase):
        return ""
    disk_resume_from = latest_steering_resume_from(project_root)
    resume_from_changed = True
    if disk_resume_from:
        resume_from_changed = disk_resume_from != frontmatter.get("resume_from_baseline", "")
    warning = ""
    if resume_from_changed and not HANDOFF_PATTERN.search(last_output):
        warning = (
            f"[context-budget] Phase transition detected ({previous_phase} -> {current_phase}) "
            "but no Context Handoff Summary found in output. "
            "Include <!-- Context Handoff --> block per references/output-format.md."
        )
    if disk_resume_from:
        frontmatter["resume_from_baseline"] = disk_resume_from
    return warning


def _resolve_recommended_model(
    plugin_root: Path, frontmatter: dict, current_phase: str, last_output: str
) -> str:
    recommended_model = frontmatter.get("recommended_model", "")
    resolver_path = plugin_root / "scripts" / "resolve-gdd-model.py"
    if not resolver_path.exists():
        return recommended_model
    try:
        resolved = subprocess.run(
            [
                sys.executable, str(resolver_path),
                "--runtime", frontmatter.get("workflow_runtime", "claude_code"),
                "--phase", current_phase,
                "--text", last_output,
            ],
            check=True, capture_output=True, text=True,
        )
        candidate = resolved.stdout.strip()
        if candidate:
            return candidate
    except Exception:
        pass
    return recommended_model


def _task_progress(project_root: Path) -> str:
    try:
        tl_content = _find_tasklist_text_for_progress(project_root)
        return _count_task_progress(tl_content) if tl_content else ""
    except Exception:
        return ""


def _build_system_message(
    next_iteration: int, current_phase: str, task_progress: str, model_hint: str, warning: str
) -> str:
    """Progress-first system message: 開発者に見える情報を先、AI 指示は簡潔に。"""
    system_msg = (
        f"[GDD #{next_iteration}] {current_phase}{task_progress} "
        f"(model: {model_hint}). "
        "Codex Goal guard: keep the thread Goal active until Next Action=done and the done guard has passed. "
        "Before autonomous continuation, briefly decide whether HITL is required; "
        "HITL recheck: briefly decide whether AC semantics, scope, policy, ownership, "
        "security boundary, prompt-output contract, approval boundary, or autonomy ceiling changed; "
        "if yes, pause at human-check-waiting with one reason, otherwise continue. "
        "Continue to terminal state."
    )
    # Test contract marker: gdd-stop reason=\"human-check-waiting\"
    if warning:
        system_msg += f" {warning}"
    return system_msg


def _build_continuation_reason() -> str:
    """簡潔な継続指示。

    bootstrap 契約の全文は state ファイル本文にある（setup-gdd-loop.sh が 1 度だけ書く）。
    ここで逐語再掲すると、同じ約 60 行が継続のたびに利用者の transcript と
    model context を埋める（長い session では継続のたびに再掲されていた）。
    """
    stop_markers = " / ".join(f'<gdd-stop reason="{r}">' for r in sorted(ALLOWED_STOP_REASONS))
    return (
        f"{_HOOK_INJECTION_PREFIXES[0]} "
        "canonical workflow state (`.steering/<task>/state.md` の Resume From / "
        "Next Action) を参照して続ける。直前ターンの recap 再掲だけで停止しない。\n"
        "停止できるのは terminal state のみ。停止時は次のいずれか 1 つのマーカーを出力する: "
        f"{stop_markers}。\n"
        "停止する場合（reason=cancelled を除く）は 参照した正本 / 停止理由 / 次の1アクション を明記し、"
        f"末尾に `{NEXT_ACTION_HEADING}` 見出しブロックを付ける。\n"
        "background の dispatch の完了通知を待つときは、マーカーを書かずに turn を終える（停止ではなく待ち）。\n"
        "継続契約の全文とタスク意図は `.claude/gdd-dev.local.md` 本文にある。"
        "文脈が不明瞭なら再読してから続ける。"
    )


def main() -> None:
    hook_input, plugin_root = _read_hook_input()
    project_root = Path(hook_input.get("cwd", "") or os.getcwd()).resolve()
    state_path = project_root / ".claude" / "gdd-dev.local.md"
    transcript_path_raw = hook_input.get("transcript_path", "") or ""
    transcript_path = Path(transcript_path_raw) if transcript_path_raw else Path()

    tv = _post_merge_precheck(project_root, transcript_path_raw, transcript_path)
    # peer のターンは止まっている workflow を再開させない（_post_merge_precheck と同じ）
    if transcript_path_raw and (pushback := autonomy_pushback.run_within_deadline(
        lambda: autonomy_pushback.merge_wait_reason(
            _worktree_toplevel(project_root), transcript_path, lambda: last_user_turn_is_peer(transcript_path)
        ), project_root,
    )):
        _emit_block(pushback)

    if not os.path.lexists(state_path):
        raise SystemExit(0)

    frontmatter, prompt_body = _load_active_state(state_path, project_root)
    state_session = _session_guard(frontmatter, hook_input, project_root)
    hook_session = hook_input.get("session_id", "") or ""

    try:
        iteration = int(frontmatter.get("iteration", "1"))
    except ValueError:
        block_hook_integrity_failure(
            project_root, "iteration",
            f"invalid iteration value: {frontmatter.get('iteration', '')}",
        )

    _transcript_guard(project_root, transcript_path_raw, transcript_path)
    compact_suggestion.mark_eligible()

    if tv is None:
        tv = parse_transcript(transcript_path, project_root)
    last_output = tv.last_assistant_text
    session_id = state_session or hook_session

    try:
        wait_watchdog.record_unaccepted_task_stops(tv, project_root)
    except Exception as exc:
        append_hook_error(project_root, "record_unaccepted_task_stops", str(exc))

    # Persist Handoff Summary to state.md for Smart Session Recovery
    try:
        persist_handoff_summary(last_output, project_root)
    except Exception as exc:
        append_hook_error(project_root, "persist_handoff_summary", str(exc))

    wait_watchdog.guard(
        hook_input, tv, last_output, frontmatter, prompt_body, state_path, project_root, transcript_path
    )
    before_state_clear = wait_watchdog.state_clear_guard(
        hook_input, tv, frontmatter, prompt_body, state_path, project_root, transcript_path
    )

    last_tool_text = _check_stop_markers(
        tv, state_path, project_root,
        session_id=session_id, last_output=last_output, plugin_root=plugin_root,
        before_state_clear=before_state_clear,
    )
    human_check_fallback_suppressed = _human_check_state_fallback(
        state_path, project_root,
        session_id=session_id, last_output=last_output, last_tool_text=last_tool_text,
        plugin_root=plugin_root, before_state_clear=before_state_clear,
    )

    _continuation_intent_guard(tv, project_root, transcript_path_raw, transcript_path, last_output)

    if human_check_fallback_suppressed:
        _stop_on_human_check_loophole(state_path, frontmatter, prompt_body)

    # Reaching here means no valid <gdd-stop> marker was found anywhere (main
    # text, tool result, or state.md fallback) and the workflow still looks
    # active — we are about to force another continuation block below. Apply
    # the consecutive-block ceiling exactly at this point, so genuine
    # preserve-only pause reasons (auth-waiting etc.), which already exited
    # above via try_stop_with_done_guard, are never touched by this guard.
    enforce_consecutive_block_ceiling(hook_input, frontmatter, prompt_body, state_path)

    # `current_phase` 側の正規化と対称にする（round 6 L-1）。
    previous_phase = frontmatter.get(
        "detected_phase", frontmatter.get("workflow_phase", "")
    ).strip().lower()
    current_phase = _detect_phase(frontmatter, last_output)
    handoff_missing_warning = _handoff_missing_warning(
        frontmatter, project_root, previous_phase, current_phase, last_output
    )

    frontmatter["detected_phase"] = current_phase
    # Remove legacy workflow_phase if present (SSOT migration complete)
    frontmatter.pop("workflow_phase", None)
    recommended_model = _resolve_recommended_model(
        plugin_root, frontmatter, current_phase, last_output
    )
    if recommended_model:
        frontmatter["recommended_model"] = recommended_model

    next_iteration = iteration + 1
    frontmatter["iteration"] = str(next_iteration)
    write_state(state_path, frontmatter, prompt_body)

    payload = {
        "decision": "block",
        "reason": _build_continuation_reason(),
        "systemMessage": _build_system_message(
            next_iteration,
            current_phase,
            _task_progress(project_root),
            recommended_model or frontmatter.get('recommended_model', 'sonnet'),
            handoff_missing_warning,
        ),
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    compact_suggestion.run(main, _bound_steering_file)

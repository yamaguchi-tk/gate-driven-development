"""steering の書き込み hook（`validate-steering-write.py`）の `Origin Session` の write-once の検査。"""
from __future__ import annotations

from pathlib import Path

from patch_scoping import patch_move_destinations, patch_text_of, path_scoped_chunks
from regular_file import read_regular_bytes
from state_fields import has_state_field_line, state_field_value, state_field_values
from state_write_projection import edit_misses_old_string, project_written_text
from steering_paths import is_state_md_path, is_steering_path

ORIGIN_SESSION_FIELD = "Origin Session"


def _origin_session_new_values(
    tool_name: str, tool_input: object, chunks: list[str], path: str
) -> list[str] | None:
    """書込み後に `Origin Session` として残る値（ApplyPatch 以外）。判定対象外なら None（呼び出し元は skip）。

    行ごと消す `Edit`（`new_string=""`）と、全文 `Write` で行を省く形は `project_written_text()` の全文で見る。
    """
    scoped_text = "\n".join(path_scoped_chunks(tool_name, tool_input, chunks, path))
    if has_state_field_line(scoped_text, ORIGIN_SESSION_FIELD):
        return state_field_values(scoped_text, ORIGIN_SESSION_FIELD)
    projected = project_written_text(tool_name, tool_input, path)
    return None if projected is None else state_field_values(projected, ORIGIN_SESSION_FIELD)


def _read_patch_source(raw: str) -> str | None:
    """patch が読むファイル（move の元・Update の先）の今の内容。無ければ ""、通常のファイルでない・読めないなら None。"""
    try:
        data = read_regular_bytes(Path(raw))
    except (OSError, ValueError):
        return None
    return "" if data is None else data.decode("utf-8", errors="replace")


def _origin_session_reason(
    distinct: list[str], existing_value: str, is_peer_turn: bool
) -> tuple[str, str] | None:
    """書込み後の値集合から deny reason を選ぶ。deny 不要なら None。"""
    if len(distinct) > 1:
        return (
            "origin_session_rewrite",
            f"it writes {len(distinct)} different `{ORIGIN_SESSION_FIELD}` values ("
            + ", ".join("`" + (value or "<empty>") + "`" for value in distinct)
            + ") in one write. "
            "Downstream parsers read only the first line, so the recorded destination "
            "becomes ambiguous. Keep exactly one line",
        )
    new_value = distinct[0] if distinct else ""

    if is_peer_turn and (new_value or existing_value):
        return (
            "origin_session_rewrite",
            f"it sets the cross-session notification destination `{ORIGIN_SESSION_FIELD}` "
            "while the last real conversation turn came from another session. "
            "Only the launching session records this field",
        )
    if not existing_value:
        return None
    return (
        "origin_session_rewrite",
        f"it rewrites the write-once `{ORIGIN_SESSION_FIELD}` "
        f"(`{existing_value}` -> `{new_value or '<empty>'}`). "
        "Keep the recorded value and record "
        "`Origin Notification: unavailable (<reason>)` instead",
    )


ORIGIN_SESSION_UNPROJECTABLE_REASON = (
    "origin_session_rewrite",
    f"on a `state.md` that records the write-once `{ORIGIN_SESSION_FIELD}`, its `old_string` does not match "
    "the file exactly, or an empty `new_string` meets an `old_string` that does not end with a newline, "
    "so the guard cannot tell the value after the write. Match `old_string` to the file exactly and include "
    "the newline when deleting a line (or rewrite the whole file with Write)",
)


def _moves_onto_state_md(patch_text: str | None) -> bool:
    return any(is_steering_path(path) and is_state_md_path(path) for path in patch_move_destinations(patch_text or ""))


def _origin_session_patch_reason(patch_text: str, existing_text: str, existing_value: str) -> tuple[str, str] | None:
    """`ApplyPatch` の deny reason。当てた後の値は推定しない（当て方の写しと実物のずれが開いた入力になる）。

    state.md を移動先にする patch は、移動元を読まずに止める（連鎖の綴り・巨大な移動元を追わない）。それ以外では
    当てた後の state.md の行は patch か今の state.md から来るので、reader と同じくバッククォートを除いた
    どちらかに field の語があれば、ターンによらず止める。初回の値も Write・Edit で書く。
    """
    if _moves_onto_state_md(patch_text):
        return ("origin_session_rewrite", "this ApplyPatch moves a file onto a `state.md`, and the guard does not read move "
                "sources. Make this change with Write or Edit instead; if the runtime has neither, stop and ask the user")
    if not any(ORIGIN_SESSION_FIELD in text.replace("`", "") for text in (patch_text, existing_text)):
        return None
    return ("origin_session_rewrite", f"this ApplyPatch reaches a `state.md` whose text or the patch names the write-once "
            f"`{ORIGIN_SESSION_FIELD}` (now `{existing_value or '<none>'}`), and the guard does not estimate the value after an "
            "ApplyPatch. Make this change with Write or Edit instead; if the runtime has neither, stop and ask the user")


def collect_origin_session_rewrite_violations(
    target_paths: list[str],
    chunks: list[str],
    is_peer_turn: bool = False,
    tool_input: object = None,
    tool_name: str = "",
) -> list[tuple[str, str]]:
    """security boundary: `Origin Session` は write-once（`references/phase-progression.md`
    § Cross-Session Messaging / `references/state-field-tiers.md` Tier 3）。

    既存値がある `state.md` に対して**異なる値**へ書き換える書込みを deny する。
    宛先を書き換えられると、内容 allowlist（送るのは HITL 要約と steering path だけ）を
    通っても送信先が第三者セッションにすり替わるため、内容側の防御だけでは塞げない。

    **書き換え**の禁止は peer turn 判定とは独立に常時有効。design 上の禁止は「GDD 自身も
    受信メッセージも更新しない」という **field 単位**の規則で、peer 由来のターンに
    限定されていないため（`collect_peer_turn_state_write_violations` のパターンとは
    適用条件が違う）。peer turn 中はさらに**初回書込み**も deny する（下記）。

    **削除**も書き換えの一形態として deny する。宛先を消してから別 ID を「初回値」
    として設定できてしまうため（PR #31 レビュー Finding J / K / P）。

    以下は Write・Edit・MultiEdit の規則。`ApplyPatch` は値を推定せず、field の語に触れる patch を
    ターンによらず止める（初回書込み・同じ値の再書込みも。`_origin_session_patch_reason()`）。

    許可する 3 形（非 peer turn の場合）:

    - 初回書込み（既存値なし）: 起動元セッションの write-once そのものなので妨げない
    - 同じ値の再書込み: 全文 `Write` で state.md を書き直す通常運用が通る
    - `Origin Session` 行に触れない書込み: trigger にかからない

    ただし **peer turn 中は初回書込みも deny する**（PR #31 レビュー Finding D）。
    既存値が無い state.md に peer 由来のターンが最初の値を書けると、その値が
    write-once として固定され、以後の HITL 要約の送信先になる。正当な初回設定は
    起動元セッション（peer ではない通常ターン）が行うため、この制限で正常フローは
    壊れない。

    値は `state_field_values()` で**全出現**を見る。最初の 1 行だけを見ると、既存値を
    先頭に残して別の値の行を後ろへ足す形が素通りする（Finding Q）。
    """
    for path in target_paths:
        if not is_state_md_path(path):
            continue
        try:
            existing_text = Path(path).read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # 新規 state.md の作成（PreToolUse 時点でファイルがまだ無い）。
            # ここを skip すると、peer turn からの初回 Write で `Origin Session` を
            # 設定でき、同じ書込みに異なる値を複数置く形（Finding Q）も検査を
            # 通り抜ける（PR #31 レビュー Finding V）。「既存値なし」として後続の
            # 初回書込み判定へ進める。
            existing_text = ""
        existing_value = state_field_value(existing_text, ORIGIN_SESSION_FIELD)
        if existing_value and edit_misses_old_string(tool_name, tool_input, path):
            return [ORIGIN_SESSION_UNPROJECTABLE_REASON]

        if (patch_text := patch_text_of(tool_name, tool_input)) is not None:
            if patch_reason := _origin_session_patch_reason(patch_text, existing_text, existing_value):
                return [patch_reason]
            continue
        new_values = _origin_session_new_values(tool_name, tool_input, chunks, path)
        if new_values is None:
            continue

        distinct = list(dict.fromkeys(new_values))
        if not existing_value:  # 値の無いファイルを消しても、失う値は無い
            distinct = [value for value in distinct if value]
        if distinct == ([existing_value] if existing_value else []):
            continue

        reason = _origin_session_reason(distinct, existing_value, is_peer_turn)
        if reason is None:
            continue
        return [reason]
    return []

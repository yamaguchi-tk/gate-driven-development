"""`.steering` artifact の size 上限の判定（止めずに通知する。2026-10-16 までは deny した）。

`validate-steering-write.py` から分離した size 専用ロジック（コード健全性の
1 ファイル 1500 行目安）。ここは **判定と通知の文だけ**を作り、emit はしない。
上限表（`STEERING_SIZE_WARN_BYTES`）は呼び出し元から `limits` 引数で受け取る。
"""
from __future__ import annotations

import shlex
import stat
from pathlib import Path
from typing import Mapping, NamedTuple

#: 移した後の検算に使う、push・PR の前の帳簿の検算スクリプト（読むだけ）。
LEDGER_CHECK_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check-gate-ledger.sh"
#: 退避の手順。行を要約で書き換えると、gate や completion-check が読む行（`Reviewed by:` など）が
#: 消えて、completion-check で差し戻されたり hook に止められたりする（2026-10-01 の実例）。
#: 現在の行は全部残し、置き換わった古い値と履歴の行だけをそのまま移させる。
SIZE_DENY_SUFFIX = (
    "To fit under the limit, move older lines to worklog.md as they are (append-only; do not "
    "summarize or rewrite the lines you keep). In state.md keep every current field line as is "
    "(for example Resume From / Next Action / Human Check Status / Route In Progress / Task Size / "
    "ADR distilled / ADR distillation reason / Pre-PR Self Review / Pre-Push Self Review / "
    "Independent Review / Decision Handoff / PR URL / Stacked Base) and move only superseded values and history; in "
    "tasklist.md keep Next Action and, for every completed task, its heading, AC mapping, "
    "Reviewed by and Judgment Change lines and conclusion, and move only implementation detail and full reviewer "
    "feedback; for design.md move rejected alternatives to adr.md and investigation logs to "
    f"worklog.md. For state.md / tasklist.md, run `bash {shlex.quote(str(LEDGER_CHECK_SCRIPT))} "
    "--steering <the steering dir>` before and after moving and compare the outputs: if an ok "
    "row before moving is absent after moving, or a missing / invalid / n/a row appears only "
    "after moving, copy the moved lines back from worklog.md as they were (this step only "
    "restores moved lines; it does not fix rows that were already missing / invalid). "
    "A write that decreases size does not repeat this notice."
)
# post-write サイズ算出が読む別名。`extract_content_chunks` は top-level / edits 内とも
# この定数を参照するため、受理集合はここ 1 箇所が正本（ADR-4。独立レビュー H-1 で
# edits 内のリテラル tuple を廃止し二重定義を解消）。
NEW_STRING_KEYS = ("new_string", "newText", "replacement", "content", "contents")
OLD_STRING_KEYS = ("old_string", "oldText", "oldString")


class SizeDecision(NamedTuple):
    """`_evaluate_size_decision` の結果。over は「上限を超えて増える」書き込みか（emit はしない）。"""

    target: Path | None
    over: bool
    post_size: int | None
    limit: int




def _str_byte_sizes(payload: dict, keys: tuple[str, ...]) -> list[int]:
    """`keys` のうち str 値を持つ **全 key** の UTF-8 バイト長を返す（該当なしなら空）。

    「最初に一致した別名だけ」を読むと、`content` に実サイズを載せた write へ
    `"new_string": "y"` のような decoy 別名を同居させるだけで算出が小さい方に倒れ、
    上限超過 write が通知なしで素通る（独立レビュー R4 #1。当時は deny なしで素通った）。`extract_content_chunks`
    が全 key を chunk に入れるのと走査を対称にし、判定は最大値（最も超過に寄る側）を採る。
    """
    return [
        len(value.encode("utf-8", "surrogatepass"))
        for key in keys
        if isinstance(value := payload.get(key), str)
    ]


def _edit_delta(edit: dict, existing_text: str | None = None) -> int:
    """1 件の edit の UTF-8 バイト増分の**上界**を返す（0 以上。縮小は計上しない）。

    size 判定は正確な合成シミュレーションではなく 超過に寄る側の上界推定である。
    - old が非 str / 欠落なら 0 バイト扱い（純増）。new が無い edit は増分 0（M-1）
    - 別名 key が同居する場合は new 側の最大 − old 側の最小を採る（R4 #1 の decoy 対策）
    - 縮小（delta <= 0）は 0 とする。MultiEdit は逐次適用なので、元の内容に対する出現回数で
      縮小を掛けると実際には起きない縮小で増分を相殺できた（PR #58 B-1）。上限超過中の
      縮小のみの write は `post > baseline` が偽になるので AC-5 の出口は塞がらない（Case 53g）
    - `replace_all` は既存内容の出現回数で増分を掛ける（Case 52）。空 old は `str.count` が
      文字数 + 1 を返すので全箇所挿入として計上される（B-2）。既存内容が読めない / old が
      無いときは 1 回分を下限にする（M-4）
    """
    new_sizes = _str_byte_sizes(edit, NEW_STRING_KEYS)
    if not new_sizes:
        return 0
    old_sizes = _str_byte_sizes(edit, OLD_STRING_KEYS) or [0]
    per_hit = max(new_sizes) - min(old_sizes)
    if per_hit <= 0:
        return 0
    if not edit.get("replace_all") or existing_text is None:
        return per_hit
    olds = [value for key in OLD_STRING_KEYS if isinstance(value := edit.get(key), str)]
    hits = max((existing_text.count(value) for value in olds), default=0)
    return per_hit * max(1, hits)


# replace_all の出現回数を数えるために既存内容を読む上限（バイト）。artifact の上限は 80KB
# 以下なので通常は読むが、上限超過中の巨大ファイルを丸ごと読んで hook を遅くしない。
# 超えたら読まず `_edit_delta` が 1 回分を下限に計上する（超過に寄る側）。
_EXISTING_TEXT_READ_LIMIT = 1_000_000


def _needs_existing_text(tool_name: str, tool_input: dict) -> bool:
    """replace_all を含む Edit / MultiEdit のときだけ既存内容を読む（PR #58 M-3）。"""
    if tool_name == "Edit":
        return bool(tool_input.get("replace_all"))
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits")
        if isinstance(edits, dict):
            edits = [edits]
        return isinstance(edits, list) and any(
            isinstance(edit, dict) and edit.get("replace_all") for edit in edits
        )
    return False


def _limit_for(p: Path, limits: Mapping[str, int]) -> int | None:
    """artifact 名の上限を大文字小文字を無視して引く。

    `limits` の key は小文字（`state.md` 等）。Darwin(APFS 既定) / Windows は
    case-insensitive FS なので `State.MD` と `state.md` は同一 inode を指す（実測）。
    大文字小文字を区別して引くと casing を変えるだけで size 判定が丸ごと外れる
    （独立レビュー R3 #1）。`is_steering_path` と同じ大小無視の規律に揃える。
    """
    return limits.get(p.name.lower())


def _is_under_steering(p: Path) -> bool:
    """resolve 後のパスが `.steering/` 配下かを大文字小文字を無視して判定する。"""
    return any(part.lower() == ".steering" for part in p.parts)




def _steering_size_targets(steering_targets: list[str], limits: Mapping[str, int]) -> list[Path]:
    """size 判定対象のファイルを列挙する（実装契約3の条件3）。

    複数 target は「判定放棄」ではなく **全 target を判定** する（独立レビュー #1、2026-09-06）。
    dedupe で二重指定を畳むだけでは、case-insensitive FS（Darwin 既定）で
    `…/state.md` と `…/State.MD` が resolve 後も別文字列のまま 2 件に見え、
    single-target 条件が外れて size 判定ごとスキップされる（実測 rc=0）。
    target ごとに判定して 1 件でも超過すれば超過とすれば、
    件数を増やすだけの迂回は原理的に成立しない。
    条件を満たす target が無ければ空リスト（size 判定を行わない = 常に通知なし）。
    """
    targets: list[Path] = []
    for raw in steering_targets:
        candidate = Path(raw)
        if not candidate.is_absolute():
            # 相対パスは cwd 依存で stat() の対象がずれ、縮小 write の誤った超過判定を招くため size 非対象
            continue
        try:
            p = candidate.resolve()
        except (OSError, ValueError, RuntimeError):
            # NUL 入りパス等で resolve() が例外を投げても、その target を諦めるだけにする。
            # ここで落とすと既存 deny category が 1 件も走らずに fail-open する。
            continue
        # `is_steering_path` は resolve 前の文字列で判定するため、`.steering/../state.md`
        # のように `..` で外へ抜けるパスも steering target として渡ってくる。正規化後に
        # 実際に `.steering/` 配下かを再確認しないと、`.steering` の外のファイルへ
        # steering 用の上限が適用される。配下でなければ size 判定は算出不能扱い（通知なし）。
        if not _is_under_steering(p) or _limit_for(p, limits) is None:
            continue
        targets.append(p)
    # 同一ファイルの二重指定は畳む（判定結果は畳まなくても同じ）。
    # POSIX ではバックスラッシュもファイル名の一部なので、区切り文字への読み替えはしない。
    return list(dict.fromkeys(targets))


def _compute_post_write_size(tool_name: str, tool_input: object, existing: int, existing_text: str | None = None) -> int | None:
    """tool_input と on-disk サイズ（バイト）から post-write サイズを UTF-8 バイトで再構成する。

    算出不能（ApplyPatch、`edits` が list / dict 以外、型不一致）なら None を返す。
    Edit / MultiEdit の `replace_all` は算出する（既存内容の出現回数で増分を掛ける。Case 7 / 52 / 53 / 54）。
    `tool_input` は dict とは限らない（`extract_target_paths` / `extract_content_chunks`
    は str payload もサポート形状として扱う）ため、dict 以外は算出不能に落とす。
    """
    if not isinstance(tool_input, dict):
        return None

    if tool_name == "Write":
        # 受理集合の正本は `NEW_STRING_KEYS` 1 箇所（ADR-4）。ここに別リテラルを
        # 残すと、chunk 側が読む別名 key（`newText` 等）で書いた超過 write が
        # 「算出不能 = 通知なし」に落ちる（独立レビュー R3 #3）。さらに「最初の 1 個」
        # だけ読むと decoy 別名で実サイズを隠せるため、全 key の最大を採る（R4 #1）。
        sizes = _str_byte_sizes(tool_input, NEW_STRING_KEYS)
        if not sizes:
            return None
        return max(sizes)

    if tool_name == "Edit":
        return existing + _edit_delta(tool_input, existing_text)

    if tool_name == "MultiEdit":
        edits = tool_input.get("edits")
        if isinstance(edits, dict):
            edits = [edits]  # 容器の型ゆらぎで諦めない（M-1）
        if not isinstance(edits, list):
            return None
        dict_edits = [edit for edit in edits if isinstance(edit, dict)]
        # replace_all の出現回数は「元の内容 + 全 edit の new 文字列」を haystack に数える。
        # MultiEdit は逐次適用なので、先行 edit が後続 replace_all の対象を増やせる。元の内容
        # だけで数えると hits=0 → 1 回分に丸められ、実サイズより大きな書き込みが allow に倒れた
        # （PR #58 2 巡目 BL-1。Case 54）。連結は逐次適用で作られうる出現箇所の上界になる。
        haystack = existing_text
        if haystack is not None:
            haystack += "".join(
                value for edit in dict_edits for key in NEW_STRING_KEYS if isinstance(value := edit.get(key), str)
            )
        # 非 dict 要素は増分を持たないので無視し、算出できる edit の増分上界の総和で判定する。
        # 1 要素でも None を返してファイル全体を通知なしにすると、超過 edit に無害な要素を
        # 1 つ足すだけで size 判定を迂回できた（Case 52）。
        return existing + sum(_edit_delta(edit, haystack) for edit in dict_edits)

    return None  # ApplyPatch その他は算出不能


def _steering_size_decision(
    tool_name: str, tool_input: object, path: Path, limits: Mapping[str, int]
) -> tuple[bool, int | None, int]:
    """上限を超えて増える書き込みかを判定する（実装契約3の条件4・5・6。条件1・2・3は呼び出し元で確認済み）。

    戻り値: (over, post_size, limit)。算出不能なら (False, None, limit)。
    """
    limit = _limit_for(path, limits)
    if limit is None:
        # 上限が引けない path は size 判定の対象外。`or 0` で潰すと「上限 0 = 全 write が超過」
        # へ無音で倒れる（現状は `_steering_size_targets` が保証しているため latent / R5 #7）。
        return False, None, 0
    try:
        st = path.stat()
    except FileNotFoundError:
        existing = None  # ファイル未作成
    except OSError:
        # 算出不能 (d): stat() が失敗したら tool_name によらず判定しない（ADR-3）。
        # 「未作成」と「見えない」を同一視して baseline=0 に落とすと、上限超過ファイル
        # への縮小 Write が 0 と比較されて超過とされる（deny した当時は、AC-5 の唯一の出口が塞がった）。
        return False, None, limit
    else:
        existing = st.st_size if stat.S_ISREG(st.st_mode) else None
    if existing is None and tool_name != "Write":
        # 算出不能 (c): 差分系（Edit / MultiEdit）は既存サイズが無いと算出不能（S-4）。
        # Write は全文置換なので、ファイル未作成のときだけ existing=0 で判定を継続する（ADR-1）。
        return False, None, limit
    baseline = existing if existing is not None else 0
    existing_text: str | None = None
    if (
        isinstance(tool_input, dict)
        and baseline <= _EXISTING_TEXT_READ_LIMIT
        and _needs_existing_text(tool_name, tool_input)
    ):
        # replace_all の出現回数を数えるために既存内容を読む。読めなければ None のまま
        # （`_edit_delta` が 1 回分を下限に計上する。例外で hook を落とさない / R5 #1 と同規約）。
        try:
            existing_text = path.read_text(encoding="utf-8", errors="surrogateescape")
        except (OSError, ValueError):
            existing_text = None
    post_size = _compute_post_write_size(tool_name, tool_input, baseline, existing_text)
    if post_size is None:
        return False, None, limit
    return post_size > limit and post_size > baseline, post_size, limit


def size_notice(size: SizeDecision) -> str:
    """上限を超えた書き込みの通知の文（超えていなければ ""）。file_path の生値は含めずファイル名だけ使う（S-5）。

    止めない PreToolUse の通知は、書き込みの実行後に agent に届く。"""
    if size.target is None or not size.over or size.post_size is None:
        return ""
    return (
        f"[steering size] {size.target.name} is {size.post_size} bytes after this write, "
        f"over the {size.limit} byte limit. {SIZE_DENY_SUFFIX}"
    )


def _evaluate_size_decision(
    tool_name: str, tool_input: object, steering_targets: list[str], limits: Mapping[str, int]
) -> SizeDecision:
    """上限を超えて増える書き込みかを target ごとに判定する（emit はしない）。最初に超えた target を通知に使う。

    ループ内に `except ValueError` は置かない（独立レビュー R3 #5: 到達不能）。size 算出は
    `surrogatepass` なので lone surrogate では例外にならず、NUL 入り path は `_steering_size_targets`
    が先に除外する。想定外の例外は `validate-steering-write.py` の top-level guard と
    `run-steering-write-hook.sh` の rc guard で fail-closed にする。
    """
    for p in _steering_size_targets(steering_targets, limits):
        over, post_size, limit = _steering_size_decision(tool_name, tool_input, p, limits)
        if over:
            return SizeDecision(p, True, post_size, limit)
    return SizeDecision(None, False, None, 0)




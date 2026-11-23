"""done guard の block reason 文言を組み立てる message 層。

`gdd_stop_hook.py` の `_done_block_payload()` から呼ばれる「推奨アクション」
（`_build_recovery_hints`）と「なぜこの guard があるか」（`_build_why_explanations`）
の生成だけを持つ。判定は一切行わない —— 入力は既に確定した `error_msg` 文字列で、
出力は表示用テキストのみ。

hook 本体（1 ファイル 1500 行の code-health 目安）から**メッセージ生成の責務**を
切り出したもの。移設時点では文言・分岐・順序とも同一で、その後 AC-9 第 5 形の分岐、
Notes ヒント（検証行の例の追加 / 外部 writer 行があるときの「唯一の回復手順」の省略）、
外部 writer 分岐の文言（AC-20 改訂）、AC 検証行 0 件の回復ヒント（PR #65 レビュー対応。
AC 行の追加を案内し、「唯一の回復手順」は schema 違反のときだけ出す）を変更した。
"""
from __future__ import annotations

import re

from lib.done_guard import (
    _LINE_BREAK_HEADLINE_TASKLIST,
    _LINE_BREAK_HEADLINES,
    _ROUTE_LINE_HEADLINES,
    _STATE_FENCE_UNCLOSED_HEADLINE,
)
from lib.task_binding_resolve import safe_for_output


# design.md § 1.6 / AC-20: 外部 security evidence writer 由来の legacy 行形の検出は
# **行頭アンカー付き**でなければならない。部分一致（散文中の `security_evidence:` 言及）
# にすると、無関係な schema 違反に対して「Snyk plugin を enabled: false にせよ」という
# 全プロジェクトの Stop ゲートを止める導線を提示してしまう（security R4 M-2）。
_LEGACY_SECURITY_WRITER_ROW = re.compile(r"^-\s*SECURITY-|^-\s*\S+\s*\|\s*security_evidence:")


# 違反行の表示は先頭 5 件だけなので、legacy 行の有無は hook が違反行全件で数えた見出し行
# （`_legacy_writer_headline`）で渡し、案内側はその見出しを行頭一致で見る（独立レビュー R23 #2 /
# D-14）。違反行は字下げして表示されるので、行本文からこの見出しを行頭に置くことはできない
_LEGACY_WRITER_HEADLINE = "外部 writer の legacy 行が "


def _is_legacy_writer_display(raw: str) -> bool:
    """違反行ラベルと同じ表示基準（無害化・80 文字切り詰め後）で legacy writer 行かを判定する。"""
    return _LEGACY_SECURITY_WRITER_ROW.match(safe_for_output(raw)[:80].strip()) is not None


def _legacy_writer_headline(line_violations: list[str]) -> str:
    """違反行全件で数えた legacy 行の件数行（schema 違反メッセージの末尾へ足す）。無ければ空文字列。"""
    count = sum(1 for raw in line_violations if _is_legacy_writer_display(raw))
    if not count:
        return ""
    return f"\n{_LEGACY_WRITER_HEADLINE}{count} 件あります（表示の先頭 5 件に含まれない行も数える）"


def _has_legacy_security_evidence_writer_shape(error_msg: str) -> bool:
    return any(
        line.startswith(_LEGACY_WRITER_HEADLINE) or _LEGACY_SECURITY_WRITER_ROW.match(line.strip())
        for line in error_msg.splitlines()
    )


# AC 検証行 0 件（判定順 3）の判定は hook 自身の見出し行に**行頭**で合わせる。error_msg には
# 利用者の行本文（違反行・未完了行）も載るため、部分文字列一致にすると行本文の文言で
# schema 違反を AC 行 0 件と取り違える（impl-gate R17）。違反行は字下げ、未完了行は `|` で
# 始まるので、行頭では hook の見出しとしか一致しない
_NO_AC_ROWS_HEADLINE = "## Verification セクションに検証行がありません"


def _has_no_ac_rows_headline(error_msg: str) -> bool:
    return any(line.startswith(_NO_AC_ROWS_HEADLINE) for line in error_msg.splitlines())


def _verification_shape_hints(error_msg: str, suppress_sole_instruction: bool) -> list[str]:
    """schema 違反（判定順 2）と AC 検証行 0 件（判定順 3）の回復ヒント。

    hook は判定順 2 を先に返すので、両者は同じ error_msg に同時に出ない。
    """
    no_ac_rows = _has_no_ac_rows_headline(error_msg)
    hints = [
        "canonical 形 → `| method | status | evidence | notes |` / "
        "`|---|---|---|---|` / `| method=ac:AC-1 | pass | npm test 通過 | - |`"
    ]
    # AC 検証行 0 件の解除条件は `method=ac:` 行の追加だけ。既存行がすべて canonical な
    # pass 行でも書き直しでは解除できないので、未完了の有無にかかわらず案内する（PR #65 review）
    if no_ac_rows:
        hints.append(
            "AC 検証行なし → `method=ac:<AC_ID>` 行を追加してください。"
            "検証行（未完了/失敗の行を含む）は `## Verification` 以外のどの節へも"
            "移してはいけません。"
        )
    # AC 検証行 0 件 + 未完了（evidence / refactor-checkpoint 行の pending・fail）の節は
    # 行の形が既に正しく、移すべき散文が無い。ここで Notes 導線を出すと security scan の
    # fail 行を Notes へ逃がす誤誘導になるので出さない（AC-9）
    if not no_ac_rows or "未完了/失敗" not in error_msg:
        notes_hint = (
            "散文・凡例・補助表 → `## Verification Notes` へ移してください（消さない）。"
            "検証行（`method=` 開始 / AC ID・`security_evidence`・`refactor-checkpoint` を"
            "名指す行 / status トークンを含む行 / 検証の結果・予定・未実施を書いた行）は "
            "`## Verification` 以外のどの節へも"
            "移してはいけません（`ac-ledger.md`（AC Trace Ledger）/`## Verification History` の"
            "正規の記録は対象外）。"
        )
        # 「唯一の回復手順」は schema 違反のときだけ出す。AC 検証行 0 件では AC 行の追加が
        # 解除条件で、外部 writer の legacy 行があるときは agent の手書きが契約違反なので、
        # どちらも書き直しを唯一の手順と言うと上下の案内と矛盾する
        if not (no_ac_rows or suppress_sole_instruction):
            notes_hint += "canonical 表行への書き直しが唯一の回復手順です。"
        hints.append(notes_hint)
    hints.append(
        "セル内の `|` は `\\|` でエスケープしてください"
        "（バッククォートで囲んでも列区切りとして数えます）。"
    )
    return hints


def _build_recovery_hints(error_msg: str) -> str:
    """Map done-guard error types to specific recovery actions (DX5)."""
    hints: list[str] = []
    legacy_writer = _has_legacy_security_evidence_writer_shape(error_msg)
    error_lines = error_msg.splitlines()
    line_break = any(line.startswith(_LINE_BREAK_HEADLINES) for line in error_lines)
    # 「唯一の回復手順」の抑止は tasklist.md の見出しだけを根拠にする。state.md の行区切りで
    # 抑止すると、tasklist.md の本物の schema 違反の回復手順が黙って消える（Issue #119 / D-28）
    tasklist_line_break = any(line.startswith(_LINE_BREAK_HEADLINE_TASKLIST) for line in error_lines)
    if line_break:
        # 区切り文字で割れた断片が schema 違反になっても、解除手順は文字の削除（impl-gate R21 M-1）
        hints.append(
            "行区切り文字 → 理由に示した行にある見えない文字（U+2028 など）を削除してください。"
            "削除後の tasklist.md / state.md で改めて検査されます。"
        )
    if "未完了タスク" in error_msg:
        hints.append(
            "残タスクあり → Current Task / Pending Tasks のタスクを完了させるか、"
            "不要なら Completed Tasks へ移してください。"
        )
    if "非標準の内容" in error_msg:
        hints.append(
            "非標準コンテンツ → Current Task / Pending Tasks に "
            "「- なし」以外の非タスク行があります。内容を確認して整理してください。"
        )
    if "Verification セクションが存在しません" in error_msg:
        hints.append(
            "Verification 欠落 → tasklist.md に ## Verification セクションを追加し、"
            "各 AC の検証行を記録してください。"
        )
    if "schema 違反行が" in error_msg or _has_no_ac_rows_headline(error_msg):
        hints.extend(_verification_shape_hints(error_msg, legacy_writer or tasklist_line_break))
    if legacy_writer:
        # AC-20（2026-09-10 改訂）: 暫定回避は人間が判断して行う操作。fail / pending の行は
        # 削除も移動もしない。writer 修正までは agent の正規手順では解除できないので、
        # 停止して人間へ報告する。「こうすれば解除される」と読める括弧や開示文書への
        # 参照は置かない
        hints.append(
            "外部 security evidence 行 → `method=security_evidence:*` 行は external "
            "verifier hook が書く行です。agent の手書きは契約違反です。書き直しても "
            "writer が legacy 形式で行を探すため次の scan で再生成されます。"
            "status が `fail` / `pending` の行は削除も移動もせず、原因（スキャンで見つかった"
            "問題）を解消して verifier を再実行してください。"
            "他の違反・未完了を解消したうえで、残るのが legacy 形式の行だけなら、writer 修正までは "
            "agent が取れる正規の手順ではこの block を解除できません。"
            '`<gdd-stop reason="blocked">` で停止し、スキャン結果と次の選択肢を人間へ報告してください'
            "（legacy 行の扱いは `pass` の行も含めて人間が判断します）。"
            "恒久対処: verifier plugin 側 writer の `method=` prefix 付与 + "
            "4 列表形式化（本 PR 対象外）。"
            "暫定回避（副作用あり。人間が判断して行う操作です。agent は自分で設定しないでください）: "
            "人間が verifier plugin の local 設定ファイル（project の `.claude/<plugin 名>.local.md`"
            "または global の `~/.claude/<plugin 名>.local.md`）の frontmatter に "
            "`enabled: false` を置く。副作用: (1) 設定を置いただけでは block は解除されない "
            "(2) この設定は Snyk の Stop ゲートとスキャン状態追跡も止め、global へ置くと"
            "全プロジェクトに効く (3) writer 修正後は設定を戻し、verifier を再実行して"
            "証跡を取り直してから done にする。"
        )
    if "を通常のファイルとして読めないため done を許可しません" in error_msg:
        hints.append(
            "通常のファイルでない状態ファイル → 理由に示した tasklist.md / state.md が FIFO・"
            "ディレクトリ・symlink のループ・指す先の無い symlink になっています。"
            "通常のファイルに置き換えてください。"
        )
    if "fenced code block が重なっています" in error_msg:
        hints.append(
            "節内 fence → 記入例・散文は `## Verification Notes` へ移してください"
            "（そこでは fence を自由に使えます）。"
        )
    if 'fenced code block の中に "## Verification" 見出し' in error_msg:
        hints.append(
            '見出し入り fence → Notes へ移しても解除されません。'
            'fence 内の見出し行を書き換えてください（例: "Verification 節の例:"）。'
        )
    if "未完了/失敗" in error_msg:
        hints.append(
            "Verification 未完了 → pending/fail の検証行があります。"
            "gdd-implementation-gating を再実行して pass にしてください。"
        )
    if any(line.startswith(_ROUTE_LINE_HEADLINES) for line in error_msg.splitlines()):
        hints.append(
            "Route In Progress の行 → state.md に `- Route In Progress: <値>` の形で 1 行に書いてください"
            "（remediation route が完了していれば none）。"
        )
    if any(line.startswith(_STATE_FENCE_UNCLOSED_HEADLINE) for line in error_msg.splitlines()):
        hints.append("state.md の code fence → 閉じ忘れた ``` / ~~~ を閉じてください。")
    if "Route In Progress=" in error_msg:
        hints.append(
            "Route In Progress 残存 → remediation が完了していません。"
            "state.md の Route In Progress=none に更新してください。"
        )
    if not hints:
        hints.append(
            "tasklist.md の全タスクを完了し、Verification を pass にしてから "
            "<gdd-stop reason=\"done\"> を再出力してください。"
        )
    return "\n".join(f"• {h}" for h in hints)


def _build_why_explanations(error_msg: str) -> str:
    """Explain WHY each done-guard rule exists. 教育的な背景説明を生成する。

    AI が次回以降に同じパターンで止まらないよう、ルールの背景理由を伝える。
    「何が悪いか」は error_msg が示すが、「なぜそのルールがあるか」は未提供。
    """
    whys: list[str] = []
    if "未完了タスク" in error_msg or "非標準の内容" in error_msg:
        whys.append(
            "なぜ: done は「全タスク完了」の宣言。残タスクがあるまま done すると"
            "実装漏れが本番に流れます。hook が構造的に防ぐことで、context 圧縮で"
            "tasklist の記憶が失われた場合でも実装漏れを検出できます。"
        )
    if "Verification" in error_msg:
        whys.append(
            "なぜ: テスト通過 ≠ AC 充足。Verification は「どの AC を、どの方法で、"
            "いつ確認したか」の証拠記録です。これがないと「通ったつもり」で done してしまい、"
            "要件と実装の乖離が気付かれないまま残ります。"
        )
    route_line = any(line.startswith(_ROUTE_LINE_HEADLINES) for line in error_msg.splitlines())
    if "Route In Progress=" in error_msg or route_line:
        whys.append(
            "なぜ: Route In Progress は remediation（差し戻し修正）の進行中フラグ。"
            "これが残ったまま done すると、中途半端な修正が未完了のままターミナル状態に入ります。"
            "none にクリアする = remediation が完了して正常フローに戻った、という意味です。"
        )
    if not whys:
        whys.append(
            "なぜ: done は後戻りできないターミナル状態。ここで前提条件を構造的に検証することで、"
            "「通ったつもり」で done してしまうのを防ぎます。"
        )
    return "\n".join(whys)

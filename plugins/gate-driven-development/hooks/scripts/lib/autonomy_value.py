"""state.md の自走上限と `Human Check Status` の evidence が、自走のマージに入る形かを見て、入らない理由を返す。

入る形の正本は `references/post-merge-qa.md` § 入口（行と値の読み方）と手順 2（完全一致）で、読み手は main である。
この module は書き手（main・gate の subagent）に知らせるだけで、allow / deny は変えない。
悪い形を並べず、入る形（行が 1 行・`- 自走上限: <値>` の形・evidence が `human:<値>` と完全一致・値が表の値。承認前の
`pending`・`changes_requested` を除き evidence が `human:` で始まる）を
満たさないときに、欠けた条件を返す。`scripts/lint-approved-direction.py` と steering の書き込み hook が共有する。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from .tasklist_parse import strip_fenced_blocks
except ImportError:  # lint とテストは top-level の module として読む
    _DIR = str(Path(__file__).resolve().parent)
    sys.path.insert(0, _DIR)
    try:
        from tasklist_parse import strip_fenced_blocks
    finally:
        sys.path.remove(_DIR)

# 自走のマージを許す自走上限の値（references/human-check-template.md § 自走上限の置換値）
MERGE_AUTONOMY_LIMITS = ("マージまで", "マージ・デプロイ・QA まで")
# 表の値のうち、`マージ` を含むが自走のマージを許さないもの（マージは 1 操作ごとの承認に残る）
_NON_MERGE_LIMITS = ("PR マージ後検証 / 再学習まで",)

# 先頭の空白・箇条の記号・`**`・バッククォートを除いて（`**` は `[-*+]` の 2 回で読み、括弧の後の繰り返しは括弧があるときだけ。
# 同じ文字を 2 通りに読むと後戻りが増える）、ラベル（括弧の注記を挟んでよい）の後に `:`・`：`・`=` が来る行
_LINE = re.compile(
    r"^\s*(?:[-*+]\s*|`)*(自走上限|Human Check Status)(?:\*\*|`)*"
    r"(?:(?:（[^）]*）|\([^)]*\))(?:\*\*|`)*)?\s*[:：=](.*)$"
)
_CANONICAL_LIMIT = re.compile(r"^\s*- 自走上限: ")
_EVIDENCE = re.compile(r" \| evidence:(.*?)(?: \| |$)")
_QUOTE = 80


def _read(text: str) -> tuple[list[tuple[str, bool]], list[tuple[str, str]]]:
    """コードフェンスの外の、自走上限の（値, `- 自走上限: ` の形か）と、Human Check Status の（status, evidence）を返す。"""
    limits: list[tuple[str, bool]] = []
    statuses: list[tuple[str, str]] = []
    for line in strip_fenced_blocks(text).splitlines():
        found = _LINE.match(line)
        if not found:
            continue
        if found.group(1) == "自走上限":
            limits.append((found.group(2).split(" | ", 1)[0].strip(), bool(_CANONICAL_LIMIT.match(line))))
        else:
            evidence = _EVIDENCE.search(found.group(2))
            statuses.append((found.group(2).split(" | ", 1)[0].strip(), evidence.group(1).strip() if evidence else ""))
    return limits, statuses


def _q(value: str) -> str:
    return value if len(value) <= _QUOTE else value[:_QUOTE] + "…"


def _mentions_merge(value: str) -> bool:
    """自走のマージを指しうる値か。`マージ` を含み、マージを許さない表の値で始まらないもの。"""
    return "マージ" in value and not value.startswith(_NON_MERGE_LIMITS)


# 承認前の status（references/gate-status-schema.md）。このときの evidence は `human:` でなくてよい
_BEFORE_APPROVAL = ("pending", "changes_requested")

# 注記・表の外の値の WARN に共通の、直し方の文
_FIX_SCOPE = (
    "直すのは、本人のターンの承認か事前回答の適用を記録しているこの書き込みの続きだけで、後から見つけた記録は"
    "書き換えず、マージの時点で Merge Approval を 1 問で問います。gate の subagent は evidence を書き換えません"
)


def _value_note(value: str) -> str | None:
    """自走上限か `human:` の evidence の値 1 つについて、表の値に入らない理由を返す。"""
    if value in MERGE_AUTONOMY_LIMITS or value in _NON_MERGE_LIMITS:
        return None
    other = next((m for m in _NON_MERGE_LIMITS if value.startswith(m)), None)
    if other:
        return (
            f"WARN: human-evidence 自走上限の値 `{_q(value)}` は `{other}` に注記が付いた形です。注記は worklog.md に"
            f"移し、値を `{other}` に戻します。この値ではマージは 1 操作ごとの承認のままで、注記で自走のマージには"
            "なりません。" + _FIX_SCOPE
        )
    base = next((m for m in MERGE_AUTONOMY_LIMITS if value.startswith(m)), None)
    if base:
        return (
            f"WARN: human-evidence 自走上限の値 `{_q(value)}` は `{base}` に注記が付いた形で、"
            "自走のマージに入りません（references/post-merge-qa.md の完全一致）。注記が範囲を狭める条件"
            "（PR の限定・前提の PR など）なら値を `PR 作成まで` にし、自走上限の値そのものを本人が選んでいない"
            "（Fable などが代わりに決めた）なら `human:` の承認にしません。どちらか判別できないときも `PR 作成まで` に"
            "します。注記が出所・日付・委任先の記録だけなら、worklog.md に移して値から外します（事前回答を適用した承認なら、"
            "その `事前回答:` の行に。references/human-check-template.md § 事前回答）。" + _FIX_SCOPE
        )
    if "マージ" not in value:
        return None
    return (
        f"WARN: human-evidence 自走上限の値 `{_q(value)}` は § 自走上限の置換値の表の値ではありません。"
        "自走のマージに入りません（references/post-merge-qa.md の完全一致）。本人の言葉を表の値に当てはめます"
        "（references/human-check-template.md § 事前回答 5）。マージ後の確認が read-only なら `マージまで` にします。"
        "デプロイ・QA の書き込みを含むなら、repo に宣言があれば `マージ・デプロイ・QA まで`、宣言が無ければ"
        "`PR 作成まで` にします。範囲を狭める条件がある、本人が値を選んでいないときも"
        "`PR 作成まで` にします。出所・日付は worklog.md に書きます。" + _FIX_SCOPE
    )


def _status_notes(limit: str, status: str, evidence: str) -> list[str]:
    """自走上限がマージの値のときの、`human:` で始まらない evidence の注記を返す（承認前の status は除く）。"""
    if status in _BEFORE_APPROVAL or evidence.startswith("human:"):
        return []
    target = f"`human:{limit}`" if limit in MERGE_AUTONOMY_LIMITS else "自走上限を表の値に直したうえで `human:<直した値>`"
    return [
        f"WARN: human-evidence Human Check Status の evidence `{_q(evidence)}` が `human:` で始まりません。"
        "references/post-merge-qa.md 手順 2 は evidence が `human:<自走上限の値>` と完全一致するときだけ本人の承認と"
        "みなすので、自走のマージに入りません。本人のターンの承認か、§ 事前回答 2 の適用を済ませた記録の続きなら"
        f"{target} にします。それ以外（判断役の承認、後から見つけた記録など）は書き換えません。"
        "gate の subagent は evidence を書き換えません。マージの時点で Merge Approval を 1 問で問います"
    ]


def autonomy_value_notes(text: str) -> list[str]:
    """自走のマージに入らない形を、`WARN: human-evidence` で始まる文で返す。

    自走上限か `human:` の evidence の値が、自走のマージを指しうる値（`マージ` を含み、`PR マージ後検証 / 再学習まで`
    で始まらない）か、注記を付けた `PR マージ後検証 / 再学習まで` のときだけ見る。
    """
    limits, statuses = _read(text)
    evidences = [e for _, e in statuses]
    human = [e for e in evidences if e.startswith("human:")]
    values = list(dict.fromkeys([v for v, _ in limits] + [e.removeprefix("human:").strip() for e in human]))
    if not any(_mentions_merge(v) or _value_note(v) for v in values):
        return []
    notes = [n for n in map(_value_note, values) if n]
    if len(limits) != 1:
        notes.append(
            f"WARN: human-evidence 自走上限の行が {len(limits)} 行あります。自走のマージに入るのは、"
            "`- 自走上限: <値>` の行が 1 行だけのときです（references/post-merge-qa.md § 入口）"
        )
    elif not limits[0][1]:
        notes.append(
            "WARN: human-evidence 自走上限の行が `- 自走上限: <値>` の形ではありません（`**`・バッククォート・"
            "全角コロン・`=`・括弧の注記付きの欄名など）。自走のマージに入るのはこの形のときだけです"
            "（references/post-merge-qa.md § 入口）"
        )
    if len(statuses) != 1:
        notes.append(
            f"WARN: human-evidence Human Check Status の行が {len(statuses)} 行あります。自走のマージに入るのは、"
            "1 行だけのときです（references/post-merge-qa.md § 入口）"
        )
    limit = limits[0][0] if len(limits) == 1 else None
    if limit is not None and _mentions_merge(limit) and len(statuses) == 1:
        notes.extend(_status_notes(limit, *statuses[0]))
    for evidence in dict.fromkeys(human):
        if limit is not None and evidence != f"human:{limit}":
            notes.append(
                f"WARN: human-evidence `{_q(evidence)}` が自走上限 `{_q(limit)}` と一致しません。"
                "references/post-merge-qa.md 手順 2 は evidence が `human:<自走上限の値>` と完全一致するときだけ"
                "本人の承認とみなします"
            )
    return notes


def _current(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return ""


def notes_for_write(targets: list[str], project) -> list[str]:
    """書き込み後の state.md の全文（`project(path)`。作れなければ None）の注記を返す。失敗したら空にする。

    自走上限と Human Check Status の行（値と形）が書き込みの前後で変わらないときは返さない。後から見つけた
    記録は書き換えないので、同じ注記を書き込みのたびに返さない。
    """
    notes: list[str] = []
    try:
        for path in targets:
            if not path.replace("\\", "/").lower().endswith("/state.md"):
                continue
            projected = project(path)
            if isinstance(projected, str) and _read(projected) != _read(_current(path)):
                notes.extend(n for n in autonomy_value_notes(projected) if n not in notes)
    except Exception:  # noqa: BLE001 - 知らせるだけの検査なので、失敗は allow のまま無言にする
        return []
    return notes

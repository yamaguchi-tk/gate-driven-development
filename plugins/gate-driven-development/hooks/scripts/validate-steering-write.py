#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# `lib/transcript.py` は `from lib.constants import` 等を使うため package import が必須で、
# 単体 module 化はできない。単体実行のため `hooks/scripts` を一時的に sys.path へ入れ、
# 他の `lib` パッケージ（`scripts/lib` 等）との衝突を避けるため読んだ直後に外す。
# import 例外時も汚染しないよう try/finally で確実にロールバックする（このスクリプトを
# importlib.util.exec_module() 経由でロードするテストは pytest プロセスを共有するため）。
#
# `sys.path` の操作だけでは足りない: `sys.modules["lib"]` が既に `scripts/lib` を指していると
# import 機構はキャッシュ済み package を使い `ModuleNotFoundError: No module named
# 'lib.transcript'` になる（実測。`tests/_plugin_module_loader.py` 冒頭が同じ問題を記録）。
# そこで import の前後で `lib` / `lib.*` の `sys.modules` エントリを退避・復元する。
# import 済みの `last_user_turn_is_peer` は依存先を module globals に束縛済みで復元後も動く。
# なお、この import block 自体が落ちたときの fail-closed は
# `run-steering-write-hook.sh` の rc guard 側で担保する（独立レビュー R3 #1）。
_SCRIPT_DIR = str(Path(__file__).resolve().parent)


def _is_lib_module(name: str) -> bool:
    return name == "lib" or name.startswith("lib.")


_SAVED_LIB_MODULES = {k: v for k, v in sys.modules.items() if _is_lib_module(k)}
for _name in list(_SAVED_LIB_MODULES):
    del sys.modules[_name]
sys.path.insert(0, _SCRIPT_DIR)
try:
    from lib.transcript import last_user_turn_is_peer  # noqa: E402
    from lib.tasklist_parse import NON_NEWLINE_LINE_BREAKS  # noqa: E402
    from lib.patch_scoping import (  # noqa: E402
        extract_added_lines,
        parse_patch_paths,
        patch_added_lines,
        patch_added_lines_by_path,
        patch_added_lines_by_section,
        patch_inflow_sources,
        patch_text_of,
    )
    from lib.steering_size import (  # noqa: E402
        NEW_STRING_KEYS,
        SizeDecision,
        _evaluate_size_decision,
        size_notice,
    )
    from lib.advisory_lint import allow_response, lint_warning as _lint_warning  # noqa: E402
    from lib.request_diff_approval import (  # noqa: E402
        chunks_add_approval as _rda_chunks_add_approval,
        collect_violations as _request_diff_approval,
        record_allow as _rda_record_allow,
        value_turns_approved as _rda_value_turns_approved,
    )
    from lib.autonomy_value import notes_for_write  # noqa: E402
    from lib.secret_scanning import (  # noqa: E402
        ELLIPSIS_EXCLUDE_SECTIONS,
        find_aws_account_id,
        find_ellipsis,
        find_email,
        find_local_path,
        find_secret_marker,
        find_sensitive_value,
    )
finally:
    if _SCRIPT_DIR in sys.path:
        sys.path.remove(_SCRIPT_DIR)
    for _name in [k for k in list(sys.modules) if _is_lib_module(k)]:
        del sys.modules[_name]
    sys.modules.update(_SAVED_LIB_MODULES)


# ルール正本: references/common-guardrails.md
#   - § 省略記法禁止 (ELLIPSIS_RE, lib/secret_scanning.py)
#   - § .steering artifact の正本性 (LOCAL_PATH_PATTERNS)
# このスクリプトは正本のルールを実行時に enforcement する。
# ルール変更時は正本を先に更新し、このスクリプトの正規表現を追従させる。

ALLOW_RESPONSE = {"continue": True, "suppressOutput": True}

# steering artifact の肥大は gate / route 判断の各ステップを重くする
# （下の上限を大きく超えた steering では、1 ステップが分単位で遅くなった）。
# 上限を超えて増える write は止めずに通知する（`lib/steering_size.py` の `size_notice`。減る write には出さない）。
STEERING_SIZE_WARN_BYTES = {"state.md": 20_000, "tasklist.md": 80_000, "design.md": 60_000}
DENY_PREFIX = "Blocked write to .steering because "
DENY_SUFFIX = (
    "For paths and emails, use relative paths, example@example.com, or a plain word instead; "
    "for other values, follow the Why line."
)
# カテゴリごとの「なぜ」の説明（何が悪いかだけでなく理由を示し、次から同じ形を避けさせる）。
WHY_EXPLANATIONS = {
    "email": (
        "Why: .steering/ は監査証跡として git 履歴に残ります。個人メールがコミットされると、"
        "リポジトリ閲覧者全員に PII が漏洩します。example.com か「（メールアドレス）」のような語を使ってください。"
    ),
    "path": (
        "Why: ローカル絶対パス（/Users/..., /home/...）は他の開発者の環境で解決できません。"
        "相対パスならチーム全員の環境で同じ意味を持ちます。"
    ),
    "ellipsis": (
        "Why: ...省略 / （略） / 中略 は原文の一部を削った記号です。"
        "migration / conversion タスクでは steering に書かれた内容がそのまま実装に流れるため、"
        "省略表現が残ると変換後のファイルで原文情報が欠落します。"
        "全文を展開するか、参照パス（例: 元ファイルの path）で書いてください。"
    ),
    "aws_account_id": (
        "Why: AWS アカウント ID は権限境界やコスト分析の手がかりになります。"
        "アカウントを特定できる 12 桁の実値は <redacted-account-id> などに置き換えてください。"
    ),
    "secret_marker": (
        "Why: 秘密鍵や API token は .steering/ に残すと git 履歴から漏洩します。"
        "実値ではなく secret の種類、保管先、または <redacted> だけを書いてください。"
    ),
    "sensitive_value": (
        "Why: password / token / secret / credential の実値らしき値は監査証跡に残せません。"
        "設定項目名だけを残し、値は <redacted> にしてください。"
    ),
    "state_metadata": (
        "Why: active steering の解決は `state.md` の `Started At` に依存します。"
        "これが無いと同一 worktree の resume 候補を一意に決めにくくなり、"
        "fail-closed な multi-active ambiguity が増えます。"
    ),
    "state_core_fields": (
        "Why: SessionStart / UserPromptSubmit hook は Tier 1 (Core) field が"
        "揃っていない state.md を active steering として解決できず fail-closed します。"
        "欠落したまま作業を続けると、hook が現在の作業を案内できず、"
        "コンパクションの後に作業内容が失われます。1 行ずつで済むので書き込み時点で揃えてください。"
    ),
    "self_review_evidence": (
        "Why: `Pre-PR Self Review` / `Pre-Push Self Review` は push / PR 作成 gate の"
        "入力です。書式が壊れると gate が証跡を読めず fail-closed になります。"
        "key: sha, rounds, consecutive_clean, dry, lanes をすべて含めてください。"
    ),
    "completed_reviewed_by": (
        "Why: 完了タスクの `Reviewed by:` は completion-check Step 2a が読みます。要約や worklog への移動で"
        "落ちると、completion-check で差し戻されます（2026-10-01 の S-0）。行はそのまま残してください。"
        "再オープンは、タスクを `## Current Task` か `## Pending Tasks` へ移してください。完了タスクを意図して"
        "消す・分け直すとき（refactor の abort、gdd-task-breakdown の作り直しなど）は、先に `## Pending Tasks` へ移す書き込みをしてから消してください。"
    ),
    "risk_low_approval": (
        "Why: `risk-low:` の承認は、リスクの段が低のタスクで human check を待たずに進む根拠になります。"
        "request-crosscheck.md の記録を読み違えて書く、または書き込み後の state.md を確かめられない書き込みを通すと、"
        "人が見るべき変更が確認なしに進みます。"
    ),
    "origin_session_rewrite": (
        "Why: `Origin Session` は cross-session 通知の宛先です（write-once）。"
        "書き換えを許すと、内容 allowlist を通った HITL 要約と steering path が"
        "第三者セッションへ送られます。宛先が変わる場合は書き換えず、通知を skip して"
        "`Origin Notification: unavailable (<理由>)` を記録してください。"
        "ApplyPatch で止まったときは Write・Edit で書いてください。どちらも無ければ、shell で書かずにユーザーに頼んでください。"
    ),
}

# Tier 1 (Core) state.md fields — canonical definition: references/state-field-tiers.md
# These must be present in active steering state.md. When any of them is written,
# `Started At` becomes transitively required (see state_requires_started_at).
# Keep in sync with hooks/scripts/lib/detect-steering.sh:gdd_validate_active_state_fields.
STATE_REQUIRED_FIELDS = ("Resume From", "Human Check Status", "Route In Progress")

# 無限ループ対策: 同じ (file, category) で連続 deny し続けると AI が別表記で再試行を
# 繰り返し ping-pong になる。N 回連続で同一 deny が起きたら escape hatch として warning
# 付き allow に降格させ、人間判断に委ねる（「N-1 回は守る / N 回目は通知して通す」）。
# 共通仕様の正本: references/bounce-log-schema.md
#   - hook-level gate は閾値 3（MAX_CONSECUTIVE_DENIES）、skill-level gate は 2
#   - identifier-key は (path, category) の sha1 hash
STATE_DIR = Path(
    os.environ.get("GDD_HOOK_STATE_DIR")
    or (Path.home() / ".claude" / ".gdd-hook-state")
)
MAX_CONSECUTIVE_DENIES = 3
STATE_TTL_SECONDS = 3600  # 1 時間経過した counter はリセット

# 3 回連続 deny での自動降格から除外する category。基準は 2 つで、両方を満たすもの
# だけを入れる: (a) AI が書き方を直せば決定的に解消する（ping-pong リスクが低い）、
# (b) 降格して 1 回通すと結果が回復不能。
#
# - `self_review_evidence`: 書式を直せば解消する。降格しても gate が証跡を読めなく
#   なるだけで回復可能だが、AC-22 が自動 allow 降格を明示的に禁じている
#   （design.md § Design Policy Discussion）。
# - `secret_marker`: 値を `<redacted>` に置換すれば必ず解消する。一方、降格して 1 回通せば
#   平文の credential が git 履歴に着地し取り消せない。実 token を握っているのは AI 自身で、
#   表記だけ変えた再試行では値が残り続け 3 回目に escape hatch へ到達する（実測で確認）。
#
# `email` / `aws_account_id` / `sensitive_value` も (b) を満たすが、降格可否の変更は
# 既存利用者の挙動を変えるため本 category とは別に判断する。
# - `origin_session_rewrite`: `Origin Session` は cross-session 通知の宛先。降格して 1 回通すと
#   以後の HITL 要約が攻撃者指定の宛先へ送られ取り消せない。書き換えをやめれば解消（(a)）。ApplyPatch の
#   deny は書き方では解けない（Write・Edit で書く）が、降格して通すと (b) が残るので降格しない。
# - `steering_line_break`: 行区切り文字を取り除けば解消する（(a)）。降格して 1 回通すと、
#   `collect_peer_turn_state_write_violations`（承認・マージ承認・中止・完了の記録）と
#   `collect_origin_session_rewrite_violations`（`Origin Session` の書き換え）を外した書き込みが着地する（(b)）。
# - `request_diff_approval`: 依頼から外れる点を要件の変更の経路に送れば解消する（(a)）。降格して 1 回通すと、
#   ユーザーが同意していない狭めが承認として記録され、後続の phase がそれを前提に進む（(b)）。
NON_DEMOTABLE_CATEGORIES = {
    "self_review_evidence",
    "secret_marker",
    "peer_turn_state_write",
    "origin_session_rewrite",
    "steering_line_break",
    "risk_low_approval",
    "request_diff_approval",
}


def _state_key(path: str, category: str) -> str:
    # path は tool_input 由来で lone surrogate を含みうる。素の `encode("utf-8")` は
    # `UnicodeEncodeError` を投げ、counter 操作は deny emit の前段にあるため既存 deny が
    # 1 件も走らず fail-open する。`surrogatepass` なら key の一意性も保たれる（H-1）。
    h = hashlib.sha1(f"{normalize_path(path)}::{category}".encode("utf-8", "surrogatepass")).hexdigest()
    return h[:16]


def _state_file(path: str, category: str) -> Path:
    return STATE_DIR / f"{_state_key(path, category)}.json"


def load_deny_count(path: str, category: str) -> int:
    f = _state_file(path, category)
    if not f.exists():
        return 0
    # 壊れた counter state（非 dict / 非数値 / 不正バイト / JSON 不正）は一律 0 回扱い。
    # 例外を top-level guard へ届けると、TTL は読めた後にしか効かないため当該
    # (path, category) が hook の無効化以外で解けない恒久 deny で固まる（独立レビュー R3 #4）。
    try:
        data = json.loads(f.read_text())  # UnicodeDecodeError / JSONDecodeError ⊂ ValueError
        ts = float(data.get("ts", 0))  # 非 dict は AttributeError
        count = int(data.get("count", 0))
    except (OSError, ValueError, TypeError, AttributeError):
        return 0
    if time.time() - ts > STATE_TTL_SECONDS:
        return 0
    return count


def record_deny(path: str, category: str) -> int:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        return 1  # state 書けない環境でも最低 1 回は deny として振る舞う
    count = load_deny_count(path, category) + 1
    f = _state_file(path, category)
    try:
        f.write_text(json.dumps({"count": count, "ts": time.time()}))
    except OSError:
        pass
    return count


def clear_deny(path: str, category: str) -> None:
    f = _state_file(path, category)
    if f.exists():
        try:
            f.unlink()
        except OSError:
            pass


def emit_allow() -> int:
    print(json.dumps(ALLOW_RESPONSE))
    return 0


def emit_allow_with_advisory(advisory: list[str], notice: str = "", context: list[str] | None = None) -> int:
    """allow のまま advisory を systemMessage に、自走上限の注記を additionalContext に載せる（lib/advisory_lint.py）。"""
    print(json.dumps(allow_response(ALLOW_RESPONSE, advisory, notice, context or [])))
    return 0


def _resolve_plugin_root() -> Path:
    """plugin root を env から取り、無ければ本 script の位置から導く。"""
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if env_root and Path(env_root).resolve().is_dir():
        return Path(env_root).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _find_steering_dir(path: Path) -> Path | None:
    """`.steering/<task>/` にあたる祖先ディレクトリを返す。見つからなければ None。"""
    for ancestor in [path.parent] + list(path.parents):
        if ancestor.parent.name == ".steering" and ancestor.is_dir():
            return ancestor
    return None


# size 判定（上限を超えて増える write の通知）は `lib/steering_size.py` に分離。上限表は引数で渡す。


def run_advisory_lints(
    steering_targets: list[str], content_chunks: list[str] | None = None, tool_name: str = ""
) -> list[str]:
    """state.md / requirements.md / tasklist.md / design.md の write に対して advisory lint を走らせる。

    既存 deny ロジックを補完する形で、glob 粒度 / AC ID 整合性などを warning として返す。
    deny には昇格しない（修正路径を奪わないため）。
    """
    plugin_root = _resolve_plugin_root()
    lint_ad = plugin_root / "scripts" / "lint-approved-direction.py"
    lint_ac = plugin_root / "scripts" / "lint-ac.py"
    lint_dup = plugin_root / "scripts" / "lint-requirements-duplication.py"

    warnings: list[str] = []
    seen_steering_dirs: set[str] = set()
    seen_dup_dirs: set[str] = set()

    for path in steering_targets:
        try:
            p = Path(path).resolve()
        except (OSError, ValueError, RuntimeError):
            # NUL 入りパス等。落とすと後の通知ごと失われるので skip のみ。
            continue
        steering_dir = _find_steering_dir(p)
        if steering_dir is None:
            continue

        # Advisory 1: state.md write → run lint-approved-direction on state.md
        name = p.name.lower()  # is_state_md_path と同じく大文字小文字を区別しない
        if name == "state.md" and p.is_file():
            warning = _lint_warning(
                lint_ad, [str(p), "--quiet"] + (["--no-human-evidence"] if tool_name in PROJECTABLE_TOOLS else []),
                f"[approved-direction lint] {p.name}", ("WARN:",)
            )
            if warning:
                warnings.append(warning)

        # Advisory 3: requirements.md or design.md write → AC の欄名の列挙の書き直しを出す
        # （requirements-template.md § 事実は AC に 1 回だけ書く）。Advisory 2 の
        # `continue` より前に置く。
        if name in ("requirements.md", "design.md") and str(steering_dir) not in seen_dup_dirs:
            seen_dup_dirs.add(str(steering_dir))
            warning = _lint_warning(
                lint_dup,
                ["--steering-dir", str(steering_dir)],
                f"[duplication lint] {steering_dir.name}",
                ("WARN:",),
            )
            if warning:
                warnings.append(warning)

        # Advisory 2: requirements.md or tasklist.md write → run lint-ac on the steering dir
        if name in ("requirements.md", "tasklist.md"):
            sd_key = str(steering_dir)
            if sd_key in seen_steering_dirs:
                continue  # already linted this steering dir in this hook invocation
            seen_steering_dirs.add(sd_key)
            warning = _lint_warning(
                lint_ac,
                ["--steering-dir", str(steering_dir), "--quiet"],
                f"[ac lint] {steering_dir.name}",
                ("WARN:", "ERROR:"),
            )
            if warning:
                warnings.append(warning)

    return warnings


def emit_deny(
    reasons: list[tuple[str, str]], suffix: str = DENY_SUFFIX, notice: str | None = None
) -> int:
    """reasons は (category, description) のリスト。category は WHY_EXPLANATIONS のキー。

    `notice` は size の上限超過の通知（`size_notice`）。deny 本文の末尾に付記する。
    """
    descriptions = [desc for _, desc in reasons]
    categories = []
    for cat, _ in reasons:
        if cat not in categories:
            categories.append(cat)
    why_lines = [WHY_EXPLANATIONS[cat] for cat in categories if cat in WHY_EXPLANATIONS]
    message = DENY_PREFIX + "; ".join(descriptions) + ". " + suffix
    if why_lines:
        message += "\n\n" + "\n".join(why_lines)
    if notice:
        message += "\n\n" + notice
    print(
        json.dumps(
            {
                "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny"},
                "systemMessage": message,
            }
        ),
        file=sys.stderr,
    )
    return 2


def emit_allow_with_warning(
    target_paths: list[str],
    reasons: list[tuple[str, str]],
    notice: str | None = None,
) -> int:
    """連続 deny が MAX に達したとき escape hatch として warning 付きで allow する。

    `target_paths` は本文にそのまま載る。size 経路のように生パスを出せない場合は
    呼び出し元が literal（ファイル名）に丸めてから渡す（S-5）。
    `notice` は size の上限超過の通知（`size_notice`）。warning の末尾に付記する。
    """
    descriptions = [desc for _, desc in reasons]
    categories = []
    for cat, _ in reasons:
        if cat not in categories:
            categories.append(cat)
    why_lines = [WHY_EXPLANATIONS[cat] for cat in categories if cat in WHY_EXPLANATIONS]
    escalation = (
        f"⚠ Same deny triggered {MAX_CONSECUTIVE_DENIES} times in a row for "
        f"{', '.join(target_paths)}. Hook is escaping to warning mode to avoid an "
        f"infinite deny↔retry loop. HUMAN REVIEW REQUIRED: verify the content is "
        f"actually safe to persist. Only this write is allowed: the counter for this (path, category) "
        f"is reset to 0, so the next write with the same violation is denied again. "
        f"Original violations: {'; '.join(descriptions)}."
    )
    if why_lines:
        escalation += "\n\n" + "\n".join(why_lines)
    if notice:
        escalation += "\n\n" + notice
    print(
        json.dumps(
            {
                "continue": True,
                "suppressOutput": False,
                "systemMessage": escalation,
            }
        )
    )
    return 0


# patch を path 単位にスコープ化するヘルパは `lib/patch_scoping.py` に分離（冒頭の import 部を参照。
# 1500 行の目安のため）。patch 全体を 1 本の文字列として扱うと、別ファイルへ書いた行を誤認する。


def extract_target_paths(tool_name: str, tool_input: object) -> list[str]:
    paths: list[str] = []

    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "target_file", "target_notebook"):
            value = tool_input.get(key)
            if isinstance(value, str):
                paths.append(value)

    patch_text = patch_text_of(tool_name, tool_input)
    if patch_text is not None:
        paths.extend(parse_patch_paths(patch_text))

    return paths


def extract_content_chunks(tool_name: str, tool_input: object) -> list[str]:
    chunks: list[str] = []

    if isinstance(tool_input, dict):
        for key in NEW_STRING_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str):
                chunks.append(value)

        edits = tool_input.get("edits")
        if isinstance(edits, dict):
            # size 判定側（`lib/steering_size.py`）と受理集合を揃える。dict の `edits` を
            # 落とすと secret / email / path の全 detector を型ゆらぎ 1 つで素通りできた
            # （PR #58 2 巡目 BL-2。Case 54b）。
            edits = [edits]
        if isinstance(edits, list):
            for edit in edits:
                if not isinstance(edit, dict):
                    continue
                for key in NEW_STRING_KEYS:
                    value = edit.get(key)
                    if isinstance(value, str):
                        chunks.append(value)

    patch_text = patch_text_of(tool_name, tool_input)
    if patch_text is not None:
        chunks.append(extract_added_lines(patch_text))

    return [chunk for chunk in chunks if chunk]


# 検出器の表。`(category, finder, describe)` の 3 つ組で 1 種類の違反を表す。
# finder は `(line, in_code_block, in_exclude_section)` を受けて検出値か falsy を返す。
# 引数を使わない finder もシグネチャを揃える（表を 1 本にして分岐を増やさないため）。
# **並び順が reasons の出力順になる**ため、順序を変えない。
DETECTORS: tuple[tuple[str, object, object], ...] = (
    (
        "email",
        lambda line, code, exclude: find_email(line),
        lambda v: f"it contains an email address ({v})",
    ),
    (
        "path",
        lambda line, code, exclude: find_local_path(line),
        lambda v: f"it contains a local absolute path ({v})",
    ),
    (
        "ellipsis",
        lambda line, code, exclude: find_ellipsis(line, exclude),
        lambda v: (
            f"it contains an omission marker ({v}). "
            "Expand to full content or replace with a path reference"
        ),
    ),
    (
        "aws_account_id",
        lambda line, code, exclude: find_aws_account_id(line, code),
        lambda v: "it contains a probable AWS account ID. Replace it with <redacted-account-id>",
    ),
    (
        "secret_marker",
        lambda line, code, exclude: find_secret_marker(line),
        lambda v: "it contains a probable secret marker. Replace the value with <redacted>",
    ),
    (
        "sensitive_value",
        lambda line, code, exclude: find_sensitive_value(line, code),
        lambda v: (
            f"it contains a probable sensitive value for `{v}`. "
            "Replace the value with <redacted>"
        ),
    ),
)


def _advance_section_state(line: str, in_exclude_section: bool):
    """fence の外の 1 行を読んで (除外セクション内か, この行を読み飛ばすか) を返す。見出し行も検出器にかける。"""
    if any(line.startswith(sec) for sec in ELLIPSIS_EXCLUDE_SECTIONS):
        return True, False
    if in_exclude_section and line.startswith(("#", "##", "###", "####")):
        return False, False
    return in_exclude_section, False


def collect_violations(
    chunks: list[str], skip_categories: frozenset[str] = frozenset()
) -> list[tuple[str, str]]:
    """違反を (category, description) のタプルで返す。category は WHY_EXPLANATIONS のキー。

    同一 category は最初の 1 件だけを返す（同じ理由を何度も突き返さないため）。
    検出器の追加・変更は `DETECTORS` の表だけで閉じる。
    """
    reasons: list[tuple[str, str]] = []
    seen_categories: set[str] = set()

    for chunk in chunks:
        # code block は閉じた fence だけ。閉じ忘れの後ろは検査する側に倒し、fence の中の行は節の構造として読まない
        lines, closed, _open_at, _spans = _scan_fences(chunk)
        in_exclude_section = False
        for i, line in enumerate(lines):
            in_code_block = i in closed
            if not in_code_block:
                in_exclude_section, skip = _advance_section_state(line, in_exclude_section)
                if skip:
                    continue
            for category, finder, describe in DETECTORS:
                if category in seen_categories or category in skip_categories:
                    continue
                value = finder(line, in_code_block, in_exclude_section)
                if not value:
                    continue
                reasons.append((category, describe(value)))
                seen_categories.add(category)

    return reasons


# fence の走査は lib/tasklist_parse._scan_fences を共有する。ここで 2 つ目の実装を作らない。
# **top-level module として**読む。`from lib.X import` は `sys.modules["lib"]` を
# hooks 側に固定し、同一プロセスの `scripts/lib`（`lint_base` 等）を解決できなく
# する（実測: ModuleNotFoundError）。読んだ直後に path を戻す。
_LIB_DIR = str(Path(__file__).resolve().parent / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from reviewed_by_guard import lost_reviewed_by  # noqa: E402
    from steering_paths import (  # noqa: E402
        is_state_md_path,
        is_steering_path,
        is_tasklist_md_path,
        normalize_path,
    )
    from state_write_projection import (  # noqa: E402
        PROJECTABLE_TOOLS,
        _edit_triples,
        edit_misses_old_string,
        project_written_text,
    )
    from risk_tier import collect_risk_low_approval_violations  # noqa: E402
    from origin_session_guard import (  # noqa: E402
        _moves_onto_state_md,
        _read_patch_source,
        collect_origin_session_rewrite_violations,
    )
    from tasklist_parse import _scan_fences, strip_fenced_blocks  # noqa: E402
    from state_fields import (  # noqa: E402
        _strip_backticks_for_field_match,
        has_state_field_line,
        state_field_pattern,
        state_field_value,
    )
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)


def has_state_field(text: str, field: str) -> bool:
    """field が値付きで存在するかを判定する。

    2 つの fail-open を塞ぐ:

    - 部分文字列検索 (`f"{field}:" in text`) は本文の散文（例:
      `次のターンでは Next Action: を必ず記録すること`）を field と誤認する
    - prefix の有無だけを見ると値のない `Resume From:` を present と数える。
      read 側 `detect-steering.sh:gdd_validate_active_state_fields` は
      `[[ -z "${_value// /}" ]]` で空値を missing 扱いするので、write 側が
      通すと「書けたのに読み取り側で invalid」の非対称が残る

    判定は値取得そのものに委ねる。存在判定と値取得で規約が割れないのが要点。
    """
    return bool(state_field_value(text, field))


def state_requires_started_at(text: str) -> bool:
    # trigger は「routing field に触ったか」。読み取り規約は充足検査と揃える
    # （部分文字列のままだと散文で trigger され、アンカー済み検査で欠落と判定されて
    # 正常な書き込みを誤 deny する）が、値の有無は問わない
    # （問うと空値への更新が trigger をすり抜けて検査が走らない）。
    return any(has_state_field_line(text, field) for field in STATE_REQUIRED_FIELDS)


def has_started_at(text: str) -> bool:
    return has_state_field(text, "Started At")


# canonical tasklist phase の判定に使う 3 gate。区切り文字は `=` / `:` の両方を受理する
# （canonical: references/state-schema.json § gate_field_delimiter）。
GATE_STATUS_FIELDS = ("Requirements Review Status", "Design Review Status", "Human Check Status")


def is_canonical_tasklist_phase(state_path: Path, combined: str) -> bool:
    """read 側 `detect-steering.sh:gdd_check_3field_gate` と同じ canonical 判定"""
    if not (state_path.parent / "tasklist.md").exists():
        return False
    return all(state_field_value(combined, f) == "approved" for f in GATE_STATUS_FIELDS)


def collect_state_core_field_violations(target_paths: list[str], chunks: list[str]) -> list[tuple[str, str]]:
    """state.md の routing field を触る書き込みで Tier 1 field の充足を検査する。

    判定対象は「既存ファイル内容 + 書き込み chunk」。chunk だけを見ると、
    Edit で 1 field ずつ更新する通常運用では充足が検査される瞬間が来ない。

    既知の制約: 連結は「書き込み後のファイル」ではないので、field の**削除・空値化**を
    表現できない。既存ファイルに旧値が残っていると、その field を空値に更新する Edit は
    連結後の文字列に旧値が残るため通る。正確に見るには payload を適用した結果テキストで
    判定する必要があり、それは別途の設計変更になる。

    canonical: references/state-field-tiers.md § Tier 1
    read 側の対応実装: hooks/scripts/lib/detect-steering.sh:gdd_validate_active_state_fields
    """
    chunk_text = "\n".join(chunks)
    # routing field をまったく含まない書き込み（別セクションの追記など）は対象外
    if not state_requires_started_at(chunk_text):
        return []

    for path in target_paths:
        if not is_state_md_path(path):
            continue
        try:
            # `errors="replace"`: 不正バイトの `UnicodeDecodeError` は直下の
            # `except OSError` に捕まらず検査ごと無効化される（CHANGELOG `#### Fixed`）。
            existing_text = Path(path).read_text(encoding="utf-8", errors="replace")
        # path 側の lone surrogate は OS へ渡す時点で `UnicodeEncodeError`（⊂ `ValueError`）。
        # 「読めない = 既存値なし」に倒す（本ファイル内の path read_text 8 箇所すべて同じ扱い。
        # 例外を外へ出すと後段の既存 deny が走らない / 独立レビュー H-1）。
        except (OSError, ValueError):
            existing_text = ""
        combined = existing_text + "\n" + chunk_text
        missing = [f for f in STATE_REQUIRED_FIELDS if not has_state_field(combined, f)]

        # `Next Action` は conditional field。canonical tasklist phase 以降でだけ必須にする
        # （references/state-field-tiers.md § Tier 1）。保存先は state.md / tasklist.md の
        # どちらでもよい — read 側の decoupling と揃えないと、routing source を持っている
        # task を write 側だけが弾く。別 deny category にはしない: メッセージが 2 本に割れると
        # 1 回の書き込みで直せず MAX_CONSECUTIVE_DENIES の escape hatch を無駄に消費する。
        state_path = Path(path)
        if is_canonical_tasklist_phase(state_path, combined):
            try:
                tl_path = state_path.parent / "tasklist.md"
                tasklist_text = tl_path.read_text(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                tasklist_text = ""
            if not has_state_field(combined, "Next Action") and not has_state_field(
                tasklist_text, "Next Action"
            ):
                missing.append("Next Action")

        if not missing:
            continue
        return [(
            "state_core_fields",
            "it leaves state.md without canonical Tier 1 fields ("
            + ", ".join(f"`{f}`" for f in missing)
            + "). Add them as `<Field>: <value>` lines",
        )]
    return []


SELF_REVIEW_FIELDS = ("Pre-PR Self Review", "Pre-Push Self Review")
# 書式判定の正本は shipped parser 1 本だけ。python 側に必須 key 集合・値ドメインを
# 持たない（持った瞬間に「書けるが読めない証跡」を通す非対称が生まれる）。
SELF_REVIEW_LIB = Path(__file__).resolve().parent / "lib" / "self-review-evidence.sh"
# 1 invocation の**合計**を hook timeout（hooks.json: 10 秒）未満にする。単発値だけ見ると `SELF_REVIEW_FIELDS` 2 本に
# 触れた chunk で 2 倍になり harness の kill が先に来て email / secret deny まで消える（R3 #6 / R4 #3）。3s×2 + advisory lint 2s = 8s。
SELF_REVIEW_PARSE_TIMEOUT = 3

# Task Size の正規化規則の正本は pre-push gate step 9（`run-pre-push-gate-hook.sh`）。
# 既知の 4 値以外・欠落はすべて fail-closed 側の `standard` へ畳む。write / pre-push /
# pre-PR の 3 箇所が同じ規則を使わないと、同じ state.md で受理面が割れる（R4 #1 / #7）。
# 例外: pre-push gate が複数 steering から tip の証跡で選んだときは standard で読む（step 8b）。
GDD_TASK_SIZES = ("trivial", "quick (express)", "quick (standard)", "standard")


def normalize_task_size(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    return value if value in GDD_TASK_SIZES else "standard"


def parse_self_review_line(field: str, text: str, task_size: str = "") -> tuple[bool, str] | None:
    """証跡行の書式判定を shipped parser `gdd_parse_self_review_field` に委譲する。

    戻り値は `(valid, missing_keys)`。parser を起動できなければ `None`。
    `task_size` は正規化済み Task Size で、gate 側と同じ第 3 引数として渡す。
    渡さないと委譲記録形の受理面だけが write 側で広くなり、「write は通るが gate は
    invalid にする」非対称が復活する（R4 #1）。

    Why（判定を 1 本に寄せる）: 同じ書式を python（write 時）と bash（push / PR gate 時）で
    別々に実装すると、必ず判定がズレて「write hook は通すが gate は読めない」証跡が作れる
    （T-19 Attempt 1 の M-1 = 同一入力 12 形中 9 形で不一致）。key の追加・値ドメインの変更を
    片側だけに入れても壊れないよう、python 側は「触ったか」の trigger だけを持ち、
    「正しいか」は gate と同一の関数へ問い合わせる。
    """
    if not SELF_REVIEW_LIB.exists():
        return None
    script = (
        "set -uo pipefail\n"
        f"source {shlex.quote(str(SELF_REVIEW_LIB))}\n"
        'gdd_parse_self_review_field "$1" "$2" "$3"\n'
        "printf '%s\\t%s\\n' \"$GDD_SR_VALID\" \"$GDD_SR_MISSING_KEYS\"\n"
    )
    tmp_path = None
    try:
        # lone surrogate を含む行でも書き切る（`surrogatepass`）。`UnicodeEncodeError` を
        # 出すと本来の deny 理由が guard の固定文 deny に化ける（独立レビュー R2 #2）。
        # `tmp_path` は write の前に確保し、write が落ちても finally で必ず unlink する。
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8", errors="surrogatepass"
        ) as tmp:
            tmp_path = tmp.name
            tmp.write(text + "\n")
        proc = subprocess.run(
            ["bash", "-c", script, "gdd-sr-parse", tmp_path, field, task_size],
            capture_output=True,
            text=True,
            timeout=SELF_REVIEW_PARSE_TIMEOUT,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    lines = [ln for ln in proc.stdout.splitlines() if "\t" in ln]
    if not lines:
        return None
    valid, _, missing = lines[-1].partition("\t")
    return valid.strip() == "true", missing.strip()


def collect_self_review_evidence_violations(
    target_paths: list[str], chunks: list[str]
) -> list[tuple[str, str]]:
    """AC-11 / AC-6: state.md へ書く証跡 field を、gate と同じ判定で検査する。

    対象の絞り込みは隣接する `collect_state_core_field_violations` と同じ
    `is_state_md_path()`。証跡の正本置き場は `GDD_SR_RECOVERY_CORE` が示す
    `<steering-dir>/state.md` で、Tier 3 定義上も state field なので、他の
    steering ファイル（tasklist / design / handoff / worklog）に現れる同名の
    **散文**は検査対象にしない。絞らないと「証跡 field を話題にしている行」を
    deny し、本 category は非降格なので自動回復できない（T-19 Attempt 1 の H-1）。

    検査対象は **chunk 限定**にする。既存ファイル内容と連結すると、既存の正しい行が
    残っている限り Edit で書いた不正値が常に allow される false pass が起きるため
    （design.md § Design Policy Discussion 「証跡 field の検査対象を chunk に限定する」）。

    既知の限界 (1): 行頭を含まない部分 Edit は trigger にかからず無検査で通る
    （chunk 限定方針の内在的な帰結。fail-closed の正本は pre-push / pre-PR gate）。

    既知の限界 (2): 検査対象の `chunk_text` は複数の書き込み単位を `\\n` で連結した
    1 本の文字列だが、書式判定を委譲する shipped parser は同名 field の
    **最初の 1 行しか読まない**（`gdd_extract_doc_field` の awk が最初の一致で `exit`）。
    したがって判定は「連結後の並び順」で決まり、**誤爆と fail-open の両方向**が起きる
    （impl-gate T-21 Attempt 2 M-1' で実測。回帰は
    `tests/test_validate_steering_write.py` の
    `test_self_review_concatenated_chunk_order_decides_verdict` が固定する）:

      - fail-open: 有効な証跡行が先 + state.md の不正行が後 → allow（同じ不正行が
        単独なら deny）
      - 誤爆: 不正行が先 + state.md の有効行が後 → deny

    発火は複数ファイルを 1 度に更新する `ApplyPatch`（advisory L-45）に限らない。
    同名 field 行を 2 本以上含む単一 `Write` や、複数 edit を持つ `MultiEdit` でも
    同じ順序依存が出る（3 形とも実測済み）。

    それでも受容するのは、write hook が早期警告層であり、fail-closed の正本が
    chunk ではなく state.md 本体を読み直す pre-push / pre-PR gate 側にあるため
    （不正行が state.md の当該 field の先頭出現である通常形なら、write hook が
    見逃しても gate 側で block される。これも実測で確認済み）。
    書き込み単位ごとに分割して検査する / 全出現を検査する、といった振る舞いを
    変える修正は design 変更に相当するため、ここでは扱わない。
    """
    chunk_text = "\n".join(chunks)
    # trigger は「その field 行に触ったか」だけを見る。判定（値が正しいか）は parser の
    # 責務で、ここでは持たない。存在判定と充足検査を分ける規約は同ファイルの
    # has_state_field_line / has_state_field と同じ。
    touched = [f for f in SELF_REVIEW_FIELDS if has_state_field_line(chunk_text, f)]
    if not touched:
        return []
    state_paths = [path for path in target_paths if is_state_md_path(path)]
    if not state_paths:
        return []

    # 委譲記録形の受理面は Task Size 依存なので、gate と同じ第 3 引数を渡す（R4 #1）。
    # 取得元は chunk（今回の書き込み）を優先し、無ければ書き込み対象 state.md の既存内容。
    # `state_field_value` は**最初の値付き出現**を返すため、連結順が優先順位になる。
    # 連結せず chunk → existing の順で個別に引くのは、同じ書き込みで `Task Size` を
    # 更新する場合に chunk 側の新値を効かせるため（連結すると既存値が常に勝つ / R5 #2）。
    # 読めない・未知値は `normalize_task_size` が fail-closed 側の `standard` へ畳む。
    # `read_text` は path に lone surrogate / NUL があると `ValueError`（`UnicodeEncodeError`
    # を含む）を投げるため `OSError` と併せて捕捉する。ここで抜けると main() まで伝播して
    # 既存 deny category が 1 件も走らずに fail-open する（PR #52 と同じ規約 / R5 #1）。
    try:
        existing_text = Path(state_paths[0]).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        existing_text = ""
    task_size = normalize_task_size(
        state_field_value(chunk_text, "Task Size")
        or state_field_value(existing_text, "Task Size")
    )

    for field in touched:
        parsed = parse_self_review_line(field, chunk_text, task_size)
        if parsed is None:
            # parser を起動できないのは content の違反ではなく infra error。ここで
            # fail-closed にすると、非降格 category ゆえに state.md への書き込みが
            # 回復不能に固まる（H-1 と同型）。write hook は早期警告であり、
            # fail-closed の正本は pre-push / pre-PR gate 側にある。
            return []
        valid, missing = parsed
        if valid:
            continue
        return [(
            "self_review_evidence",
            f"it writes `{field}` in a form the push / PR gate cannot read "
            f"(invalid or missing: {missing or 'unknown'})",
        )]
    return []


PEER_TURN_STATE_WRITE_PATTERNS = [
    re.compile(r"^(?:-\s+)?Human Check Status\s*[:=]\s*approved", re.MULTILINE),
    re.compile(r"^(?:-\s+)?Merge Approval\s*[:=]", re.MULTILINE),
    re.compile(r"^(?:-\s+)?Next Action\s*[:=]\s*cancelled", re.MULTILINE),
    re.compile(r"^(?:-\s+)?Resume From\s*[:=]\s*(?:cancelled|done)(?![A-Za-z0-9_-])", re.MULTILINE),
]

# 上の chunk 用パターンと同じ 4 つの決定（承認・マージ承認・中止・完了）を **field 値**で表した判定。
# `denied_value` が None のときは「値が変わったこと自体」を見る（`Merge Approval` は
# 値の形が自由なため、`approved` のような固定語で判定できない）。
#
# `paths` は「その field が routing source として実際に読まれるファイル」。read 側
# `hooks/scripts/lib/detect-steering.sh` の実装に合わせる:
#
# - `Human Check Status`: `gdd_check_3field_gate` / `gdd_validate_active_state_fields`
#   がどちらも state.md だけを見る
# - `Merge Approval`: 正本置き場は state.md（`gdd_parse_merge_gate_field`）
# - `Next Action`: `gdd_validate_active_state_fields` が **tasklist.md → state.md** の
#   順に読む。tasklist.md も正本なので、そこで値だけを `cancelled` へ置換する Edit も
#   境界の対象にする（PR #31 レビュー Finding S）
# - `Resume From`: state.md の値（`gdd_value_head` の後）が done・cancelled と完全一致すると、
#   worktree の binding 先が pre-push・merge・pre-PR gate の数え直しから外れる
#   （`gdd_detect_active_steering`）。中止・完了の記録として同じく止める
PEER_TURN_STATE_WRITE_FIELDS = (
    ("Human Check Status", "approved", (is_state_md_path,)),
    ("Merge Approval", None, (is_state_md_path,)),
    ("Next Action", "cancelled", (is_state_md_path, is_tasklist_md_path)),
    ("Resume From", "cancelled", (is_state_md_path,)),
    ("Resume From", "done", (is_state_md_path,)),
)

# gate が field を読む reader（`gdd_extract_doc_field`）。値の比較は python の行規則ではなく
# この reader で読んだ値で行う（python 側の行規則は区切りの前の空白・`\v` などで行を広く
# 受けるので、gate が読まない囮の行を先に足すと、本物の値の置換を見逃していた）。
DETECT_STEERING_LIB = Path(__file__).resolve().parent / "lib" / "detect-steering.sh"
READER_TIMEOUT = 3


def reader_field_values(texts: list[str], fields: list[str]) -> list[list[str]] | None:
    """各テキストの各 field を gate の reader で読んだ生の値を返す。起動・実行に失敗したら `None`。

    `parse_self_review_line` と同じく shipped の reader に委ねるが、失敗したときは呼び出し側が
    止める側に倒す（peer turn の境界なので、判定できない書き込みを通さない）。field ごとの失敗も
    同じく `None` にする。孤立サロゲートを含むテキストも `None` にする（一時ファイルに書くバイトが
    実ファイルのバイトと一致する保証が無く、gate と同じ値を読めない）。
    """
    if not DETECT_STEERING_LIB.exists():
        return None
    if any(re.search("[\ud800-\udfff]", text) for text in texts):
        return None
    script = (
        "set -uo pipefail\n"
        f"source {shlex.quote(str(DETECT_STEERING_LIB))}\n"
        'n="$1"; shift\n'
        'files=("${@:1:$n}"); fields=("${@:$((n + 1))}")\n'
        'for f in "${files[@]}"; do for k in "${fields[@]}"; do\n'
        '  v="$(gdd_extract_doc_field "$f" "$k")" || exit 1\n'
        '  printf "%s\\0" "$v"\n'
        "done; done\n"
        'printf "ok\\0"\n'
    )
    tmp_paths: list[str] = []
    try:
        for text in texts:
            with tempfile.NamedTemporaryFile(
                "w", suffix=".md", delete=False, encoding="utf-8", errors="surrogatepass"
            ) as tmp:
                tmp_paths.append(tmp.name)
                tmp.write(text)
        proc = subprocess.run(
            ["bash", "-c", script, "gdd-reader", str(len(tmp_paths)), *tmp_paths, *fields],
            capture_output=True,
            timeout=READER_TIMEOUT,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    finally:
        for tmp_path in tmp_paths:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    parts = proc.stdout.decode("utf-8", errors="replace").split("\0")
    expected = len(texts) * len(fields)
    if len(parts) != expected + 2 or parts[expected] != "ok":
        return None
    return [parts[i * len(fields):(i + 1) * len(fields)] for i in range(len(texts))]


def reader_heads(value: str) -> set[str]:
    """gate が値を比べる形。`gdd_value_head`（`|` の手前）と、最初の空白か `|` までの 2 つ。"""
    head = value.split("|", 1)[0].strip()
    token = re.split(r"[\s|]", value.lstrip(), maxsplit=1)[0]
    return {head, token}


PEER_TURN_STATE_WRITE_REASON = (
    "peer_turn_state_write",
    "直近の発言は別セッションからのメッセージであり、承認・マージ承認・"
    "中止・完了の記録には使えません。ユーザー本人のターンで再度お伝えください。",
)

PEER_TURN_UNPROJECTABLE_REASON = (
    "peer_turn_state_write",
    "直近の発言は別セッションからのメッセージです。この Edit は、old_string がファイルと完全に一致しないか、"
    "空の new_string で old_string が改行で終わっていないため、書き込み後の値を判定できません"
    "（承認・マージ承認・中止・完了の記録を確かめられないので止めます）。ファイルを読み直して old_string を"
    "完全に一致させ、行を消すときは改行まで含めてください（または全文を Write で書き直してください）。",
)

PEER_TURN_MOVE_UNREADABLE_REASON = (
    "peer_turn_state_write",
    "直近の発言は別セッションからのメッセージです。この ApplyPatch の move の移動元が通常のファイルでないか読めないため、"
    "移動先へ運ばれる承認・マージ承認・中止・完了の記録を確かめられないので止めます。ユーザー本人のターンで書き直してください。",
)

def collect_peer_turn_state_write_violations(
    target_paths: list[str], tool_input: object, chunks: list[str], is_peer_turn: bool, tool_name: str = ""
) -> list[tuple[str, str]]:
    """security boundary: 直近の実会話ターンが cross-session peer 由来のとき、
    人間の意思決定を記録するパターン（承認・マージ承認・中止・完了）の書込みを
    deny する。判定前にバックティックを除去し、gdd_extract_doc_field()
    （hooks/scripts/lib/detect-steering.sh）と同じ受理規則に揃える。

    2 層で見る:

    1. chunk（追加文字列）に field 行そのものが現れる形（`Write` / `ApplyPatch` /
       行ごと差し替える `Edit`）。`ApplyPatch` は、move で流れ込む移動元（`patch_inflow_sources()`）の
       今の内容も見る。移動元が通常のファイルでないか読めなければ止める
    2. 書込み後テキストの field 値（`project_written_text`。`Write` の全文と、`Edit` /
       `MultiEdit` を当てた後のテキスト）。値だけを置換する Edit
       （`old_string="pending"` / `new_string="approved"`）は chunk に field 名が
       出ないため 1 だけでは素通りする（PR #31 レビュー Finding C）。値は python の行規則と、
       gate の reader（`reader_field_values`）の両方で読んで比べ、reader が読めなければ止める。

    `ApplyPatch` は 1 だけで見る（2 の入力を作らない）。行区切り文字で hook と gate の行を
    ずらす形は `collect_line_break_violations` が止める。`Edit` / `MultiEdit` の `old_string` が
    書き込み前のテキストに見つからないときは、射影が「変化なし」に見えても止める（`edit_misses_old_string`）。

    2 では **書込みの前後で値が変わったとき**だけ deny する。既に `approved` が
    記録済みの state.md に対する無関係な Edit まで落とさないため。対象ファイルは
    field ごとに違う（`PEER_TURN_STATE_WRITE_FIELDS` の `paths`）。`Next Action` は
    tasklist.md も read 側の正本なので、そこで値だけを `cancelled` に置換する Edit も
    見る（PR #31 レビュー Finding S）。

    1 は path を絞らない（どの steering ファイルに書いても deny する over-broad 側 =
    fail-closed）。2 の入力は `Write` / `Edit` / `MultiEdit` のときだけ作る
    （`project_written_text()` の tool_name gate。`ApplyPatch` payload に
    無関係な `old_string`/`new_string` を混ぜて非 `None` の無害な projected を
    先に確定させる余地を作らない。PR #31 独立レビュー Finding F-3 と同根）。
    """
    if not is_peer_turn:
        return []
    # ApplyPatch の move は、移動元の今の内容を移動先へ運ぶ（追加行に現れない）。連鎖した move の元も読む
    patch_text = patch_text_of(tool_name, tool_input)
    moved = [_read_patch_source(source) for path in target_paths for source in patch_inflow_sources(patch_text or "", path)]
    if None in moved:
        return [PEER_TURN_MOVE_UNREADABLE_REASON]
    combined_stripped = "\n".join(chunks + moved).replace("`", "")
    for pattern in PEER_TURN_STATE_WRITE_PATTERNS:
        if pattern.search(combined_stripped):
            return [PEER_TURN_STATE_WRITE_REASON]

    for path in target_paths:
        applicable = [
            (field, denied_value)
            for field, denied_value, matchers in PEER_TURN_STATE_WRITE_FIELDS
            if any(matcher(path) for matcher in matchers)
        ]
        if not applicable:
            continue
        if edit_misses_old_string(tool_name, tool_input, path):
            return [PEER_TURN_UNPROJECTABLE_REASON]
        projected = project_written_text(tool_name, tool_input, path)
        if projected is None:
            continue
        try:
            existing = Path(path).read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            existing = ""
        for field, denied_value in applicable:
            before = state_field_value(existing, field)
            after = state_field_value(projected, field)
            if after == before:
                continue
            if denied_value is None or after == denied_value:
                return [PEER_TURN_STATE_WRITE_REASON]
        # gate の reader で読んだ値でも比べる（読めなければ止める）。
        fields = sorted({field for field, _ in applicable})
        values = reader_field_values([existing, projected], fields)
        if values is None:
            return [PEER_TURN_STATE_WRITE_REASON]
        before_values, after_values = values
        for field, denied_value in applicable:
            index = fields.index(field)
            before, after = before_values[index], after_values[index]
            if after == before:
                continue
            if denied_value is None or denied_value in reader_heads(after):
                return [PEER_TURN_STATE_WRITE_REASON]
    return []


STEERING_LINE_BREAK_REASON = (
    "steering_line_break",
    "steering への書き込みの中身（patch・content・old_string・new_string など）に、LF・CRLF 以外の"
    "行区切り文字（U+000B・U+000C・U+2028・単独の CR など）が含まれています。この hook と gate で"
    "行の数え方が変わり、記録の検査を外せるため止めます。その文字を取り除いて書き直してください。",
)
_LONE_CR = re.compile(r"\r(?!\n)")


def _tool_input_strings(value: object):
    """tool_input の中の文字列を、入れ子の dict・list もたどってすべて返す。"""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _tool_input_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _tool_input_strings(item)


def collect_line_break_violations(tool_input: object) -> list[tuple[str, str]]:
    """security boundary: steering への書き込みの中身に LF・CRLF 以外の行区切り文字があれば、ターンを問わず deny する。

    この hook は patch を `str.splitlines()`（`lib/patch_scoping.py`）で割り、既存ファイルを universal
    newlines で読み、field の値を `splitlines()` 系の規則（`lib/tasklist_parse.py`）でも読む。gate の
    reader（awk）は LF だけで割り、`\\v`・`\\f`・単独の `\\r` などは行の中の文字（`- ` の後の空白）
    として読む。この食い違いで、行区切り文字の後ろに置いた記録が peer turn の記録の検査
    （`collect_peer_turn_state_write_violations`）も `Origin Session` の write-once
    （`collect_origin_session_rewrite_violations`）も外れる（独立-1 F1・F8、独立-2 G1・G2）。
    ApplyPatch の偽の `*** Update File:` header の形もあるので、tool_input の文字列をすべて、
    section に割る前の形で見る。集合は done guard（`lib/done_guard.py`）と同じ `NON_NEWLINE_LINE_BREAKS` と
    単独の `\\r`（CRLF は通す）。
    """
    for text in _tool_input_strings(tool_input):
        if _LONE_CR.search(text) or any(ch in NON_NEWLINE_LINE_BREAKS for ch in text):
            return [STEERING_LINE_BREAK_REASON]
    return []


def collect_completed_reviewed_by_violations(
    steering_targets: list[str], tool_name: str, tool_input: object
) -> list[tuple[str, str]]:
    """完了タスクの `Reviewed by` を落とす tasklist.md の書き込み（判定は `lib/reviewed_by_guard.py`）。
    判定中の例外（読めないなど）は止める（降格はできる）。違反が無ければ連続 deny の回数を戻す。"""
    reasons: list[tuple[str, str]] = []
    for path in [p for p in steering_targets if is_tasklist_md_path(p)]:
        try:
            written = project_written_text(tool_name, tool_input, path)
            lost = lost_reviewed_by(Path(path), tool_name, written, _edit_triples(tool_input))
        except Exception as exc:  # noqa: BLE001 - 判定できないときは止める側に倒す
            lost = [f"could not check ({type(exc).__name__})"]
        if not lost:
            clear_deny(path, "completed_reviewed_by")
        else:  # path ごとに 1 件（回数は _record_existing_denies が counter ごとに 1 回だけ進める）
            reasons.append(("completed_reviewed_by", f"{Path(path).name}: " + "; ".join(lost)))
    return reasons


def collect_state_metadata_violations(target_paths: list[str], chunks: list[str]) -> list[tuple[str, str]]:
    chunk_text = "\n".join(chunks)
    if not state_requires_started_at(chunk_text):
        return []

    reasons: list[tuple[str, str]] = []
    for path in target_paths:
        if not is_state_md_path(path):
            continue
        existing_text = ""
        try:
            existing_text = Path(path).read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            existing_text = ""
        if has_started_at(chunk_text) or has_started_at(existing_text):
            continue
        reasons.append((
            "state_metadata",
            "it updates state.md canonical fields without `Started At`. "
            "Add `Started At: <ISO8601>` to the state metadata block",
        ))
        break
    return reasons


def _extract_steering_request(payload: dict) -> tuple[str, object, list[str]]:
    """hook payload から (tool_name, tool_input, steering 配下の target paths) を取り出す。"""
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    target_paths = extract_target_paths(tool_name, tool_input)
    return tool_name, tool_input, [p for p in target_paths if is_steering_path(p)]


def _write_notes(steering_targets: list[str], tool_name: str, tool_input: object) -> list[str]:
    """書き込み後の state.md の自走上限の注記（lib/autonomy_value.py）。知らせるだけなので、例外は空にする。"""
    try:  # 2 つの呼び出し元（早期 allow を含む）をここで守る
        return notes_for_write(steering_targets, lambda path: project_written_text(tool_name, tool_input, path))
    except Exception:  # noqa: BLE001
        return []


def _size_context(size: SizeDecision, notes: list[str]) -> list[str]:
    """additionalContext（agent に届く）に載せる行。size の通知を先頭に置く。"""
    notice = size_notice(size)
    return [notice, *notes] if notice else notes


def _emit_without_violations(
    steering_targets: list[str], content_chunks: list[str], tool_name: str, size: SizeDecision, tool_input: object = None
) -> int:
    """既存 deny category が 1 件も出なかったときの allow（size の超過は止めずに通知する）。"""
    # 違反解消 → counter クリア。
    for path in steering_targets:
        for cat in WHY_EXPLANATIONS.keys():
            clear_deny(path, cat)
    try:
        advisory_warnings = run_advisory_lints(steering_targets, content_chunks, tool_name)
    except Exception:  # noqa: BLE001 - advisory は deny に昇格させない（独立レビュー R3 #7）
        advisory_warnings = []
    notes = _write_notes(steering_targets, tool_name, tool_input)
    return emit_allow_with_advisory(advisory_warnings, size_notice(size), _size_context(size, notes))


def _record_existing_denies(steering_targets: list[str], reasons: list[tuple[str, str]]) -> int:
    """既存 category の連続 deny counter を進め、最大値を返す。counter（`_state_key`）ごとに書き込み 1 回で 1 回だけ
    進める（同じ path を 2 つの key で指す・同じ category の reason が 2 件ある書き込みで、1 回目に降格へ届かない）。"""
    pairs = {_state_key(path, cat): (path, cat) for path in steering_targets for cat, _ in reasons}
    return max((record_deny(path, cat) for path, cat in pairs.values()), default=0)


def _clear_existing_denies(steering_targets: list[str], reasons: list[tuple[str, str]]) -> None:
    """既存 category の counter をクリアする（escape hatch で実際に allow する回だけ）。"""
    for path in steering_targets:
        for cat, _ in reasons:
            clear_deny(path, cat)


def _emit_with_violations(
    steering_targets: list[str], reasons: list[tuple[str, str]], size: SizeDecision
) -> int:
    """既存 deny category が出たときの record / escape hatch / emit（size の超過は理由にせず、本文に通知を付ける）。"""
    max_seen = _record_existing_denies(steering_targets, reasons)
    notice = size_notice(size) or None
    has_non_demotable = any(cat in NON_DEMOTABLE_CATEGORIES for cat, _ in reasons)
    if max_seen >= MAX_CONSECUTIVE_DENIES and not has_non_demotable:
        _clear_existing_denies(steering_targets, reasons)
        _record_request_diff_allows()
        return emit_allow_with_warning(steering_targets, reasons, notice=notice)
    return emit_deny(reasons, notice=notice)


def _payload_is_peer_turn(payload: dict) -> bool:
    """payload の `transcript_path` から peer turn かを判定する（queued で届いた peer の行も読む）。

    非 str（型ゆらぎ）は「未指定」扱い。`TypeError` を top-level guard へ渡すと全
    `.steering` write が恒久 deny になり、自動 escape hatch が無い（独立レビュー R2 #5）。
    """
    raw = payload.get("transcript_path", "")
    if not isinstance(raw, str) or not raw:
        return False
    try:
        return last_user_turn_is_peer(Path(raw), include_queued=True)
    except (OSError, ValueError):
        # 値の lone surrogate / NUL は filename encode で ValueError（`lib/transcript.py`
        # の except OSError では拾えない）。guard に届けると全 write が恒久 deny になるため
        # peer turn 扱い = fail-closed に倒す（独立レビュー R3 #2）。
        return True


_RDA_PENDING: list[tuple[dict, str]] = []  # 承認を通したら記録する (payload, state.md)。書き込み全体を通すときだけ書く


def _record_request_diff_allows() -> None:
    for payload, path in _RDA_PENDING:
        _rda_record_allow(payload, path)


def _collect_request_diff_approval_violations(
    steering_targets: list[str], payload: dict, chunks: list[str], tool_name: str, tool_input: object
) -> list[tuple[str, str]]:
    """state.md を approved にする書き込みを、直前の提示の `依頼との差:` で止める
    （`lib/request_diff_approval.py`）。通したら `_RDA_PENDING` に積み、書き込み全体を通すときに記録する。

    approved に変わるかは、peer turn の検査（`collect_peer_turn_state_write_violations`）と同じ道具で見る。
    Edit の old_string が当たらない書き込みと、gate の reader で読めない書き込みは、変わるものとして扱う。
    """
    status = "Human Check Status"
    approvals: list[str] = []
    for path in (p for p in steering_targets if is_state_md_path(p)):
        try:
            existing = Path(path).read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            existing = ""
        projected = project_written_text(tool_name, tool_input, path)
        if edit_misses_old_string(tool_name, tool_input, path):
            approves = True
        elif projected is None:
            approves = _rda_chunks_add_approval(chunks)
        elif _rda_value_turns_approved(state_field_value(existing, status), state_field_value(projected, status)):
            approves = True
        else:
            values = reader_field_values([existing, projected], [status])
            approves = values is None or (values[1][0] != values[0][0] and "approved" in reader_heads(values[1][0]))
        if approves:
            approvals.append(path)
    violations = _request_diff_approval(approvals, payload)
    if not violations:
        _RDA_PENDING.extend((payload, path) for path in approvals)
    return violations


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return emit_allow()

    tool_name, tool_input, steering_targets = _extract_steering_request(payload)
    if not steering_targets:  # 改行に似た文字で target を見失う形は、parser の割り方に依らず止める
        mentions = any(".steering" in text.lower() for text in _tool_input_strings(tool_input))
        breaks = collect_line_break_violations(tool_input) if mentions else []
        return emit_deny(breaks) if breaks else emit_allow()

    size = _evaluate_size_decision(tool_name, tool_input, steering_targets, STEERING_SIZE_WARN_BYTES)

    content_chunks = extract_content_chunks(tool_name, tool_input)

    is_peer_turn = _payload_is_peer_turn(payload)

    # reviews.md はレビュー指摘の記録先（追記専用）。指摘には「requirements.md に
    # 『...省略』が残っている」のような引用が含まれるため、ellipsis の
    # 表現検査は適用しない（秘匿系検査は維持する）。全 target が reviews.md の
    # 場合だけ緩和し、混在書き込みは安全側で通常検査にする。
    review_log_skip = (
        frozenset({"ellipsis"})
        if steering_targets
        and all(normalize_path(p).endswith("/reviews.md") for p in steering_targets)
        else frozenset()
    )
    patch_text = patch_text_of(tool_name, tool_input)  # fence を別の hunk・別ファイルと対にしない
    per_file = patch_added_lines_by_path(patch_text) + patch_added_lines_by_section(patch_text)
    reasons = collect_violations(content_chunks + per_file, skip_categories=review_log_skip)
    if content_chunks:
        reasons.extend(collect_state_metadata_violations(steering_targets, content_chunks))
        reasons.extend(collect_state_core_field_violations(steering_targets, content_chunks))
        reasons.extend(collect_self_review_evidence_violations(steering_targets, content_chunks))

    # security boundary の 3 検査は content chunk が空でも走らせる。行ごと消す Edit
    # （`new_string=""`）は追加文字列を持たないため、chunk の有無で早期 allow すると
    # `Origin Session` を削除してから別 ID を「初回値」として設定できる
    # （PR #31 レビュー Finding J）。判定は追加文字列ではなく書込み後の値で行う。
    reasons.extend(collect_line_break_violations(tool_input))
    reasons.extend(collect_completed_reviewed_by_violations(steering_targets, tool_name, tool_input))
    reasons.extend(collect_risk_low_approval_violations(steering_targets, content_chunks, tool_name, tool_input))
    if not _moves_onto_state_md(patch_text):  # 止める move では、peer turn の検査に移動元を読ませない
        reasons.extend(collect_peer_turn_state_write_violations(steering_targets, tool_input, content_chunks, is_peer_turn, tool_name))
    reasons.extend(_collect_request_diff_approval_violations(steering_targets, payload, content_chunks, tool_name, tool_input))
    reasons.extend(
        collect_origin_session_rewrite_violations(
            steering_targets, content_chunks, is_peer_turn, tool_input, tool_name
        )
    )
    if not reasons:
        _record_request_diff_allows()
    if not content_chunks and not reasons:  # 行を消すだけの Edit も、自走上限の行を消しうる
        notes = _write_notes(steering_targets, tool_name, tool_input)
        return emit_allow_with_advisory([], size_notice(size), _size_context(size, notes))
    if not reasons:
        return _emit_without_violations(steering_targets, content_chunks, tool_name, size, tool_input)

    return _emit_with_violations(steering_targets, reasons, size)


GUARD_FAILURE_MESSAGE = (
    "Blocked write to .steering: the guard hit an internal error and fails closed. "
    "Retry after checking the payload; to bypass a guard defect, disable GDD hooks via "
    "~/.claude/gdd-hooks-disabled."
)


def _emit_guard_failure(exc: BaseException) -> int:
    """main() の未捕捉例外を deny（exit 2）へ倒す二重防御（正本は wrapper の rc guard。R3 #1・H-2）。
    本文は固定文と例外の型名だけにする（メッセージ・traceback は path / content の生値を含みうる）。"""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny"},
                "systemMessage": f"{GUARD_FAILURE_MESSAGE} (error type: {type(exc).__name__})",
            }
        ),
        file=sys.stderr,
    )
    return 2


# guard 全体の時限（秒）。hook の上限（hooks.json の 10 秒）より前に、既定の動作の SIGALRM でプロセスを
# 終わらせる。harness に kill されると hook は非 block になり、guard が走らずに書き込みが通る。既定の
# 動作なら C の処理（Python 3.12 以前の NFKC など）の途中でも止まり、wrapper が 0・2 以外の終了コードを
# deny に倒す。遅い形を 1 つずつ直す代わりに、ここで形を問わず閉じる。setitimer の無い環境では張れない。
GUARD_TIME_LIMIT_SECONDS = 8


def _arm_time_limit() -> None:
    if hasattr(signal, "setitimer"):
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, GUARD_TIME_LIMIT_SECONDS)


if __name__ == "__main__":
    _arm_time_limit()
    try:
        _rc = main()
    except Exception as exc:  # noqa: BLE001 - fail-closed guard（型を絞ると穴が残る）
        _rc = _emit_guard_failure(exc)
    raise SystemExit(_rc)

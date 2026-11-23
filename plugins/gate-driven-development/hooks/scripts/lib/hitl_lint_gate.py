"""Wire existing HITL quality lints to the human-check-waiting Stop hook.

背景: HITL（`<gdd-stop reason="human-check-waiting">`）向けの品質lintは6本
存在し判定ロジックは正しく動くが、呼び出し手順がどこにも書かれていないため
実運用でほぼ実行されない。このモジュールは
**新しい判定ロジックを一切追加せず**、既存3本を実際に呼び出す配線だけを担う。

v1で配線するのは3本のみ:
  - lint-hitl-display-integrity
  - lint-human-check-language
  - lint-hitl-complexity
残り3本は対象外（判定を変えずに配線するだけ、という制約と両立しないため）:
  - lint-hitl-decision-quality: 自由文の trigger-word 一致で偽陽性が出やすい
    （例: 「実測」の2文字だけで Multiple PR Strategy Options を要求する）。
  - lint-hitl-stage-plan: 「### 段階実装案」セクション自体を要求し、複数段階
    かどうかに関わらず本文中に列挙を求める。配線済みのdisplay-integrity/
    human-check-languageは「段階実装」「段階実装サマリー」という語の存在
    だけを見る（各stop marker直前のタグがすべてstage="none"なら見ない）
    のに対し、stage-planはその節の内容（各段階の粒度・順序）まで判定する。
    判定基準が異質で自由文寄りのため、既存ロジックを変えずに
    一律適用するとlintの適用範囲外の書き方にまで正誤を強制することになる。
  - lint-hitl-outcome-audit: 検査対象がrequirements.mdの別セクションであり、
    human-check-waiting時点の最終HITL本文とは対象アーティファクトが異なる。

挙動は警告だけ（2026-10-14）: lint を通らない HITL も止めず、結果を
.gdd/hitl-lint.log に記録し、`systemMessage` でユーザーに知らせる。それまでは
同じ /gdd-dev の中で 2 回まで差し戻していたが、display-integrity が求める
約 20 の見出しと complexity の 60 行の上限を同時に満たせず、差し戻すたびに
もう片方で落ちて、同じ HITL がユーザーに何回も並んでいた（差し戻しの回数が
HITL の数を上回っていた）。差し戻しの予算（`hitl_lint_blocks`）も
使わなくなったので外した。HITL を欄から描画して照合する仕組みに替えるまでの
つなぎで、lint の判定ロジックは変えない。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from lib.errors import append_hook_error, append_log_record, hitl_lint_log_path

HITL_MARKER = '<gdd-stop reason="human-check-waiting">'

# (report name, script filename) — レポート順。判定ロジックは各scriptの中にあり
# ここでは一切変更しない。
HITL_LINT_SCRIPTS: tuple[tuple[str, str], ...] = (
    ("lint-hitl-display-integrity", "lint-hitl-display-integrity.py"),
    ("lint-human-check-language", "lint-human-check-language.py"),
    ("lint-hitl-complexity", "lint-hitl-complexity.py"),
)

# 条件付き節と Option 軸の lint（2026-09-15、方針メモでユーザー確認）: 新しい判定ロジックは
# まず記録だけで配線する。このリストのスクリプトの exit code 1 は
# hook-errors.log に記録されるだけで、`HITL_LINT_SCRIPTS` と違って
# ユーザーへの警告文にも載せない。
HITL_LINT_WARN_SCRIPTS: tuple[tuple[str, str], ...] = (
    ("lint-hitl-required-fields", "lint-hitl-required-fields.py"),
    ("lint-hitl-decision-fields", "lint-hitl-decision-fields.py"),
)

_SUBPROCESS_TIMEOUT_SECONDS = 3
_TOTAL_BUDGET_SECONDS = 4
_SKIP_ENV_VAR = "GDD_SKIP_HITL_LINT"

def should_score_hitl_text(reason: str, last_output: str) -> bool:
    """human-check-waitingの最終HITL面だけを採点対象にする前段ガード。

    Stop hookにはこのガードを経由せずreason="human-check-waiting"へ到達する
    経路が他に2つある（tool_result側にしかマーカーが無い一致、markerlessな
    state.md fallback）。そのいずれも`last_output`（main assistant text）が
    実際にユーザーへ表示される最終HITLではないため、マーカーが文字列として
    存在するときだけ採点する。

    注意: このガードが通った後、`run_hitl_lints`へ渡すのは`last_output`
    全体（＝そのターンの最終assistantメッセージ全文）であり、HITLの節
    （`## 確認`等）だけを切り出したものではない（独立レビュー2巡目）。
    HITLの前に長い前置き文章が続くターンでは、その分だけ
    lint-hitl-complexityの行数予算に不利に効く。
    """
    return reason == "human-check-waiting" and HITL_MARKER in last_output


def run_hitl_lints(
    plugin_root: Path,
    hitl_text: str,
    *,
    scripts: tuple[tuple[str, str], ...] = HITL_LINT_SCRIPTS,
    deadline: float | None = None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """`scripts`（既定は配線済み3本）をhitl_textに対して実行する。

    `scripts` を明示的に渡すことで、警告文に載せる対象（既定の
    `HITL_LINT_SCRIPTS`）と記録だけの対象（`HITL_LINT_WARN_SCRIPTS`）の
    どちらも同じ subprocess/timeout ロジックで実行できる（判定ロジックの
    実行経路を1本化する。扱いの違いは呼び出し元が持つ）。

    `deadline`（`time.monotonic()` 基準の絶対時刻）を省略すると、この呼び出し
    単独で新しい `_TOTAL_BUDGET_SECONDS` の予算を確保する（既存の呼び出し元・
    テストの挙動を変えない）。呼び出し元が複数回 `run_hitl_lints` を呼ぶ場合
    （`enforce_hitl_lint_gate` の警告パス→記録パス）は、同じ `deadline` を
    明示的に渡すことで合計の subprocess 実行時間を1回分の予算に収める
    （独立レビュー指摘: 呼び出しごとに予算を再計算すると、Stop hook 全体の
    timeout を lint の subprocess 実行だけで消費しうる）。

    Returns:
      failures: (lint名, メッセージ) のリスト。lintが実行でき、かつ内容不良
        (exit code 1) と判定したもの。
      errors: 実行できなかったlintの説明文字列のリスト（script不在・timeout・
        想定外exit code）。fail-open — 内容不良としては扱わない。
    """
    failures: list[tuple[str, str]] = []
    errors: list[str] = []

    # 配線対象が1本も見つからない（＝plugin_rootが未解決）場合、HITLごとに
    # 複数行のエラーを積むとgdd-status/hook-errors.logのノイズになる（独立
    # レビュー finding 12）。よくあるこの状態は1行に集約する。
    missing = [name for name, script in scripts if not (plugin_root / "scripts" / script).exists()]
    if len(missing) == len(scripts):
        errors.append(
            f"no wired HITL lint scripts found under {plugin_root / 'scripts'} "
            "(plugin_root unresolved?)"
        )
        return failures, errors

    fd, tmp_name = tempfile.mkstemp(suffix=".md", prefix="gdd-hitl-lint-")
    tmp_path = Path(tmp_name)
    try:
        os.chmod(tmp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(hitl_text)

        if deadline is None:
            deadline = time.monotonic() + _TOTAL_BUDGET_SECONDS
        for name, script in scripts:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                errors.append(f"{name}: total lint budget exceeded, skipped")
                continue
            script_path = plugin_root / "scripts" / script
            if not script_path.exists():
                errors.append(f"{name}: script not found at {script_path}")
                continue
            try:
                result = subprocess.run(
                    [sys.executable, str(script_path), str(tmp_path)],
                    capture_output=True,
                    text=True,
                    # 個々のscriptにも上限を課すが、Stop hook全体のtimeoutに
                    # 収まるよう、残り予算を超えないところで打ち切る
                    # （独立レビュー2巡目: 3本が最悪ケースでそれぞれ
                    # _SUBPROCESS_TIMEOUT_SECONDS一杯まで使うと合計が
                    # hooks.jsonのStop hook timeout(10秒)の大半を食う）。
                    timeout=min(_SUBPROCESS_TIMEOUT_SECONDS, remaining),
                    check=False,
                )
            except Exception as exc:  # noqa: BLE001 - fail-open by design
                errors.append(f"{name}: {type(exc).__name__}: {exc}")
                continue

            if result.returncode == 0:
                continue
            # 一時ファイルのpathは警告文を出す時点で既に削除済みになる
            # ため、文言に残すと開けないpathへの参照になる（独立レビュー2巡目）。
            combined = (result.stdout + result.stderr).strip().replace(str(tmp_path), "<HITL 本文>")
            if result.returncode == 1:
                failures.append((name, combined))
            else:
                errors.append(f"{name}: unexpected exit code {result.returncode}: {combined}")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001 - best-effort cleanup
            pass

    return failures, errors


def _run_and_log_warn_lints(
    project_root: Path, plugin_root: Path, hitl_text: str, *, deadline: float
) -> None:
    """`HITL_LINT_WARN_SCRIPTS` を実行し、結果は hook-errors.log
    にだけ記録する（警告文には載せない）。

    `deadline` は呼び出し元（`enforce_hitl_lint_gate`）が警告パスと共有する
    単一の予算。ここで新しい予算を確保すると、2 つのパスの合計が Stop hook
    全体の timeout（`hooks.json` で10秒）に近づく（独立レビュー指摘、実害クラス）。

    例外はすべて fail-open（記録して握りつぶす。HITL の pause 自体を妨げない）。
    """
    try:
        findings, errors = run_hitl_lints(
            plugin_root, hitl_text, scripts=HITL_LINT_WARN_SCRIPTS, deadline=deadline
        )
    except Exception as exc:  # noqa: BLE001 - fail-open
        append_hook_error(project_root, "hitl_lint_gate_warn", f"{type(exc).__name__}: {exc}")
        return
    for name, message in findings:
        append_hook_error(project_root, "hitl_lint_gate_warn", f"{name}: {message}")
    for error in errors:
        append_hook_error(project_root, "hitl_lint_gate_warn", error)


def _resolve_plugin_root() -> Path:
    return Path(
        os.environ.get("CLAUDE_PLUGIN_ROOT")
        or os.environ.get("GDD_PLUGIN_ROOT")
        or os.getcwd()
    ).resolve()


_WARNING_DETAIL_LINES = 3


def _warning_message(failures: list[tuple[str, str]]) -> str:
    """ユーザーに見せる警告文。lint ごとに最初の行と、詳細行（`- ` で始まる行）を
    `_WARNING_DETAIL_LINES` 行まで載せ、全文は hitl-lint.log に残す。"""
    lines = [
        "HITL の品質チェック（止めずに知らせるだけ）で、次の lint を通りませんでした。"
        "全文は .gdd/hitl-lint.log にあります。",
    ]
    for name, message in failures:
        head, *rest = message.splitlines() or [""]
        lines.append(f"- {name}: {head}")
        details = [line for line in rest if line.startswith("- ")]
        lines.extend(f"  {line}" for line in details[:_WARNING_DETAIL_LINES])
    return "\n".join(lines)


def enforce_hitl_lint_gate(
    project_root: Path,
    reason: str,
    last_output: str,
    *,
    plugin_root: Path | None = None,
) -> str:
    """try_stop_with_done_guardから呼ばれるエントリポイント。ユーザーに見せる
    警告文を返す（無ければ空文字）。stdout には書かず、停止を止めない。

    内部エラーはすべてfail-open（`append_hook_error`へ記録し、空文字を返す）。
    plugin_root解決（`os.getcwd()`を含む）自体が例外を投げる場合もこのtryに
    含める（独立レビュー finding 10）。
    """
    if os.environ.get(_SKIP_ENV_VAR) == "1":
        return ""
    if not should_score_hitl_text(reason, last_output):
        return ""

    # 警告パス・記録パス共通の単一予算（`run_hitl_lints` のdocstring参照）。
    shared_deadline = time.monotonic() + _TOTAL_BUDGET_SECONDS
    try:
        resolved_plugin_root = plugin_root if plugin_root is not None else _resolve_plugin_root()
        failures, errors = run_hitl_lints(resolved_plugin_root, last_output, deadline=shared_deadline)
    except Exception as exc:  # noqa: BLE001 - fail-open
        append_hook_error(project_root, "hitl_lint_gate", f"{type(exc).__name__}: {exc}")
        return ""

    for error in errors:
        append_hook_error(project_root, "hitl_lint_gate", error)
    _run_and_log_warn_lints(project_root, resolved_plugin_root, last_output, deadline=shared_deadline)

    # 不通過は日常的に出るので、故障の記録（hook-errors.log。gdd-status が末尾 5 件を
    # 診断として見せる）とは分けて書く
    for name, message in failures:
        append_log_record(hitl_lint_log_path(project_root), "hitl_lint_gate", f"{name}: {message}")
    return _warning_message(failures) if failures else ""

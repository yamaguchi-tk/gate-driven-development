"""merge gate hook の signal 消費契約 / config-defaults.md ↔ 定数同期の契約テスト。

`HookSignalConsumptionContractTests` は `gh_command_parse` の parse 結果 key が
hook 側で emit・read・実際に消費されるところまで追跡する（未消費の signal を
静かに無視する fail-open の再発防止）。`ConfigDefaultsMergeGateSyncTests` は
`references/config-defaults.md` の人間向け正本表と `lib/constants.py` の実行時
ミラー定数が乖離しないことを検査する。どちらも個々の gate 判定ロジックではなく
「hook を構成する複数正本が同期しているか」という契約なので同じファイルへ
まとめた（`tests/test_merge_gate_hook.py` 分割）。
"""
from __future__ import annotations

import re
import sys
import unittest

from _merge_gate_support import HOOK_SCRIPT, PLUGIN_ROOT

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.constants import (  # noqa: E402
    MERGE_GATE_APPROVAL_FRESHNESS_MINUTES,
    MERGE_GATE_RECHECK_FRESHNESS_MINUTES,
    MERGE_GATE_REVIEW_WAIT_MINUTES,
)
from lib.gh_command_parse import parse_gh_pr_merge  # noqa: E402


class HookSignalConsumptionContractTests(unittest.TestCase):
    """F-1 の root cause（parser の signal を hook が読まない）を構造で防ぐ。

    `gh_command_parse.HOOK_CONSUMED_SIGNALS` に載る signal は、hook が
    (1) inline python で emit し、(2) read ループで shell 変数へ束ね、
    (3) その変数を **コメント以外の場所で実際に読む** こと。どれか 1 つでも
    欠けたらこのテストが落ちる。parse 結果に新しい key を足したときは、
    consumed / unconsumed のどちらかへ登録するまで落ち続ける。
    """

    @staticmethod
    def _strip_comments(text):
        return "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )

    def setUp(self):
        from lib import gh_command_parse

        self.gcp = gh_command_parse
        self.src = HOOK_SCRIPT.read_text(encoding="utf-8")
        self.code = self._strip_comments(self.src)

    def test_every_parse_result_key_is_classified(self):
        keys = set(parse_gh_pr_merge("gh pr merge 1", "", "/repo").keys())
        classified = set(self.gcp.HOOK_CONSUMED_SIGNALS) | set(self.gcp.HOOK_UNCONSUMED_SIGNALS)
        self.assertEqual(
            keys, classified,
            "parse 結果の key は consumed / unconsumed のどちらかへ明示登録すること: "
            f"未分類={keys - classified} / 実体の無い登録={classified - keys}",
        )

    def test_consumed_signals_are_emitted_and_read_by_the_hook(self):
        mapping = dict(re.findall(r'^\s*([a-z_]+)\)\s*([A-Z_]+)="\$_v"', self.code, re.M))
        for signal in self.gcp.HOOK_CONSUMED_SIGNALS:
            with self.subTest(signal=signal):
                self.assertIn(f'emit("{signal}"', self.code, f"hook が {signal} を emit していない")
                self.assertIn(signal, mapping, f"hook の read ループに {signal} の branch が無い")
                var = mapping[signal]
                reads = re.findall(r"\$\{?" + var + r"\b", self.code)
                self.assertGreaterEqual(
                    len(reads), 1,
                    f"{signal} -> ${var} が代入されるだけで一度も読まれていない"
                    "（gate #11 F-1 と同じ fail-open の形）",
                )

    def test_unconsumed_signals_carry_a_reason(self):
        for signal, reason in self.gcp.HOOK_UNCONSUMED_SIGNALS.items():
            with self.subTest(signal=signal):
                self.assertTrue(reason.strip(), f"{signal} を消費しない理由が空")

    def test_failures_and_observed_are_appended_in_lockstep(self):
        lines = self.code.splitlines()
        failure_lines = [i for i, ln in enumerate(lines) if 'FAILURES+=("' in ln]
        self.assertGreater(len(failure_lines), 0)
        for i in failure_lines:
            with self.subTest(line=lines[i].strip()):
                window = "\n".join(lines[i:i + 3])
                self.assertIn(
                    'OBSERVED+=("', window,
                    "FAILURES への追加は観測値・key 名の追加と対で行うこと"
                    "（design.md § reason code カタログ の観測値 / key 列）",
                )
        self.assertEqual(
            self.code.count('FAILURES+=("'), self.code.count('OBSERVED+=("'),
        )

# --- md↔code 同期テスト（design.md:475 が要求）--------------------------------
#
# `references/config-defaults.md` の `## Merge Gate` 見出し直下の最初の表が
# 人間向け正本、`lib/constants.py` の 3 定数が実行時ミラー。ここが乖離すると
# hook は正本と違う値で動くのに doc は古い値を主張し続ける。見出し / 表が
# 消えた場合もテストを red にする（silent skip を避ける）。

CONFIG_DEFAULTS_PATH = PLUGIN_ROOT / "references" / "config-defaults.md"

def _extract_merge_gate_defaults(text: str) -> dict[str, int]:
    lines = text.splitlines()
    try:
        heading_index = lines.index("## Merge Gate")
    except ValueError:
        raise AssertionError("`## Merge Gate` 見出しが見つからない") from None

    # 見出し直下の最初の表だけを見る: 空行や散文を挟んだ次の表は対象外。
    table_rows: list[str] = []
    for line in lines[heading_index + 1:]:
        if line.startswith("|"):
            table_rows.append(line)
        elif table_rows:
            break
    if len(table_rows) < 3:
        raise AssertionError("`## Merge Gate` 直下に既定値の表が見つからない")

    defaults: dict[str, int] = {}
    for row in table_rows[2:]:  # header row + separator row をスキップ
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        name, default = cells[0], cells[1]
        defaults[name] = int(default)
    return defaults

class ConfigDefaultsMergeGateSyncTests(unittest.TestCase):
    def test_table_values_match_constants_and_literal_expectations(self):
        defaults = _extract_merge_gate_defaults(CONFIG_DEFAULTS_PATH.read_text(encoding="utf-8"))

        self.assertEqual(defaults.get("Merge Gate Review Wait"), MERGE_GATE_REVIEW_WAIT_MINUTES)
        self.assertEqual(defaults.get("Merge Gate Recheck Freshness"), MERGE_GATE_RECHECK_FRESHNESS_MINUTES)
        self.assertEqual(defaults.get("Merge Gate Approval Freshness"), MERGE_GATE_APPROVAL_FRESHNESS_MINUTES)

        # design.md § 既定値の正本: literal 期待値そのものも固定する（定数側が
        # 静かにずれても、表の値と一致しているだけでは検出できないため）。
        self.assertEqual(defaults.get("Merge Gate Review Wait"), 40)
        self.assertEqual(defaults.get("Merge Gate Recheck Freshness"), 10)
        self.assertEqual(defaults.get("Merge Gate Approval Freshness"), 120)

        # design.md § 既定値の不変条件: 承認鮮度は待機値より大きくなければ、
        # 正規手順の待機がそのまま承認を失効させてしまう。
        self.assertGreater(
            defaults["Merge Gate Approval Freshness"], defaults["Merge Gate Review Wait"],
        )

    def test_missing_heading_fails_instead_of_silently_skipping(self):
        with self.assertRaises(AssertionError):
            _extract_merge_gate_defaults("# no merge gate heading here\n")

    def test_missing_table_after_heading_fails(self):
        with self.assertRaises(AssertionError):
            _extract_merge_gate_defaults("## Merge Gate\n\nno table here, just prose.\n")

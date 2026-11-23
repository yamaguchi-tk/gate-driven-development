"""hook 横断の block reason 復旧要素 contract（T-15 remediation）。

design.md § block reason に必ず含める 3 要素 は「全 block reason」に掛かる規定だが、
T-14 時点の機械検査は pre-push gate hook 1 本だけを読んでいた。結果として
T-15 が pre-PR gate へ足した 2 code は肯定側（3 要素が在る）・否定側（実パス / slug が
出ない）のどちらの検査にも掛からず、記録先も key 一覧も正本パスも持たない reason が
全 suite を素通りした（T-15 Attempt 1 の M-1）。

本 module は検査対象を **glob で発見** し、hook ごとの fixture provider を登録制に
することで、hook が増えても自動で対象に入る形にする。ファイル名・件数の literal は
持たない。
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

import _block_reason_support as support

# design.md § reason code カタログ（確定版）で「出す key: —」の行（gate 自体の
# 故障 — state.md を読めない/HEAD を解決できない/git repo でない/コマンドを解析
# できない/対象 PR を決められない）は、そもそも state.md のどの field が欠けて
# いるかという情報を持たない。
# したがって共通復旧要素（記録先 <steering-dir>/state.md・必要 key 一覧・正本パス）
# は要求できない。
#
# ただし **無検査にはしない**（gate #11 F-4）。design.md § block reason の復旧要素は
# 「kill-switch の明示は code 14 以降に限る。これらは policy 違反ではなく gate 側の
# 故障であり、出口を示さないと人間は hook 本体を編集する」と定めているので、
# この family（下の `_GATE_FAILURE_CODES` が正本）には共通復旧要素の
# **代わりに kill-switch 文言**を要求する。
# 例外集合でテストを緑にする（invariant を満たす代わりに検査を外す）方向は取らない。
_GATE_FAILURE_CODES = frozenset(
    {"state-unreadable", "head-unresolvable", "repo-root-unresolvable",
     # `parse-error` = コマンド解析が完走しない（python3 不在 / 不正 JSON /
     # import 失敗）、または tokenizer がクォート解析に失敗して縮退した（AC-19）。
     # state.md のどの field が欠けているかを持たない gate 側の故障。
     "parse-error",
     "pr-url-unrecorded", "steering-ambiguous",
     # AC-13/AC-14: untrusted 由来 root で起動根拠が無い経路。同じ性質。
     "untrusted-root-unverified"}
    # NOTE: `pr-target-unresolvable` はここに入れない。同じ code が 2 つの family
    # で使われており（gate 故障系 = root != 実行先 / 解決不能、policy 違反系 =
    # state.md の PR URL 欠落を含む全件列挙）、code 単位の分類ができない。gate 故障
    # 系の instance が kill-switch を案内することは
    # `test_merge_gate_hook_block_reason_quality.py` の専用テストで固定する。
)
# kill-switch 文言も復旧要素と同じく shell 側の正本定数から抽出する（provider が
# 値そのものを返す自己参照検査に退化させないため）。hook が増えたらここへ足す。
_KILL_SWITCH_CONSTANT_NAMES = ("GDD_MG_KILL_SWITCH_HINT",)
_KILL_SWITCH_HINTS = tuple(
    support._extract_shell_constant(name) for name in _KILL_SWITCH_CONSTANT_NAMES
)


class HookBlockReasonRecoveryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.derived = support.reason_codes_by_hook()
        self.providers = support.registered_providers()

    def test_every_reason_code_emitting_hook_has_registered_fixtures(self) -> None:
        """reason code を出す hook に fixture provider が無ければ落とす（fail-closed）。

        新しい gate hook が block reason を出し始めたとき、この test が最初に落ちる。
        「検査対象へ追加する」操作を provider の登録 1 つに集約し、対象一覧という
        第 2 の正本を作らないための入口。
        """
        uncovered = sorted(hook.name for hook in self.derived if hook not in self.providers)
        self.assertEqual(
            uncovered,
            [],
            f"block reason の復旧要素検査に掛かっていない hook: {uncovered}",
        )

    def test_generation_is_driven_by_glob_discovery_only(self) -> None:
        """AC-8(a)(b) の検出点。

        (1) 集合一致: 生成された per-hook メソッドの `_gdd_hook` 集合が
        `reason_codes_by_hook()` の key 集合と一致する（変異 (b)・
        誤生成があれば不一致になる）。`_gdd_hook` は生成時点の即値代入
        のため、late-binding 退行（factory を外して loop 内 `def` に
        戻す変異）はこの集合一致だけでは検出できない。late-binding は
        各生成メソッド本体の自己整合性チェック（`own._gdd_hook is hook`）
        が検出する。
        (2) literal 不在: 発見された hook の `name` / `stem` が本モジュール
        自身のソースに literal として現れない（変異 (a) の唯一の検出点）。
        """
        generated_hooks = {
            getattr(HookBlockReasonRecoveryContractTests, name)._gdd_hook
            for name in dir(HookBlockReasonRecoveryContractTests)
            if getattr(
                getattr(HookBlockReasonRecoveryContractTests, name, None),
                "_gdd_hook",
                None,
            )
            is not None
        }
        self.assertEqual(generated_hooks, set(self.derived))

        module_source = Path(__file__).read_text(encoding="utf-8")
        for hook in self.derived:
            self.assertNotIn(hook.name, module_source, f"hook 名 literal が残存: {hook.name}")
            self.assertNotIn(hook.stem, module_source, f"hook stem literal が残存: {hook.stem}")


def _make_recovery_test(hook: "Path", codes: "frozenset[str]"):
    def test(self: "HookBlockReasonRecoveryContractTests") -> None:
        # ADR-2 の late-binding 退行検出は `_gdd_hook` の集合一致だけでは不十分
        # （`_gdd_hook` は生成時点の即値代入のため、factory を外して late-binding
        # 形に戻しても per-iteration の正しい値のまま残ってしまう）。ここで自分
        # 自身の `_gdd_hook` と本体が実際に使う `hook` の同一性を実行時に突き合わせ、
        # late-binding 形（body の `hook` が全メソッドで最終値になる）を検出する。
        own = getattr(type(self), self._testMethodName)
        self.assertIs(own._gdd_hook, hook, "生成メソッドのクロージャ束縛が退行している（late-binding）")

        provider = self.providers.get(hook)
        if provider is None:
            self.skipTest(
                f"{hook.name}: provider 未登録"
                "（fail-closed は test_every_reason_code_emitting_hook_has_registered_fixtures が担当）"
            )
        samples = provider()
        observed = {sample.code for sample in samples}
        self.assertEqual(
            observed,
            set(codes),
            f"{hook.name}: fixture 未到達の reason code={set(codes) - observed} / "
            f"実装に無い label={observed - set(codes)}",
        )
        for sample in samples:
            with self.subTest(hook=hook.name, code=sample.code):
                if sample.code in _GATE_FAILURE_CODES:
                    self.assertTrue(
                        any(hint in sample.reason for hint in _KILL_SWITCH_HINTS),
                        f"{hook.name} / {sample.code}: gate 故障系なのに kill-switch の"
                        f"出口が案内されていない / reason={sample.reason}",
                    )
                else:
                    self.assertEqual(
                        support.missing_recovery_elements(sample.reason),
                        [],
                        f"{hook.name} / {sample.code}: 復旧要素が欠落 / reason={sample.reason}",
                    )
                self.assertTrue(
                    sample.forbidden,
                    f"{hook.name} / {sample.code}: forbidden token 一覧が空（空洞化 guard）",
                )
                for token in sample.forbidden:
                    self.assertNotIn(
                        token,
                        sample.reason,
                        f"{hook.name} / {sample.code}: 実パス・slug が漏れている",
                    )

    test._gdd_hook = hook  # ADR-2: late-binding 退行を集合比較で検出するための属性
    return test


support.import_provider_modules()
for _hint in _KILL_SWITCH_HINTS:
    if not _hint:
        raise AssertionError("kill-switch 定数の抽出値が空文字（空洞化 guard 1/3）")
for _element in support.RECOVERY_ELEMENTS:
    if not _element:
        raise AssertionError("復旧要素定数の抽出値が空文字（空洞化 guard 2/3）")
for _hook, _codes in sorted(support.reason_codes_by_hook().items()):
    _slug = re.sub(r"[^0-9a-zA-Z]", "_", _hook.stem)
    setattr(
        HookBlockReasonRecoveryContractTests,
        f"test_block_reason_recovery__{_slug}",
        _make_recovery_test(_hook, _codes),
    )


if __name__ == "__main__":
    unittest.main()

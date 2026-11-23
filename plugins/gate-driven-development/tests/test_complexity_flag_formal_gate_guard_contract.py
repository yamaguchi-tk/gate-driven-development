"""PR #89 セルフレビュー HIGH 指摘: `--complexity` による formal gate 降格の fail-open。

実測根拠（PR #89 review discussion_r4021487916）: `scripts/resolve-gdd-model.py` の
`classify_tier()` は `complexity in legacy_complexity_map` を最優先で評価し即 return する。
`phase` が `FORMAL_GATE_PHASES`（`gdd-implementation-gating` 等）であっても、
`--complexity leaf` / `light` / `heavy` を渡すと phase 既定の `formal_gate` tier を
無視して軽い tier（`leaf_task` / `light_task` / `general_heavy`）へ黙って降格できた。
`FORMAL_GATE_PHASES` は `scripts/resolve-gdd-model.py` と `scripts/run-gdd-worker.py`
（`fallback_action()` が参照）の両方に同内容で 2 重定義されており（独立レビュー
round 4 指摘：「別モジュールの定数」という先の版の記述は誤りだった）、`classify_tier()`
はどちらも参照せず phase 名から formal gate かどうかを判定する経路を持たない
（`classify_tier()` は `PHASE_TO_TIER` の tier 値だけを見る）。

`CHANGELOG-archive-3.md:277` に同型の問題（`--phase gdd-direction-checker --complexity
heavy` で phase 固定判定を迂回できた）を一度直した記録があるが、その修正は Fable 撤去で
`gdd-direction-checker` ごと削除され、他の formal gate phase 全般には一般化されて
いなかった（今回は再発）。

Opus advisory（2026-09-16）による調査で、実際に `--complexity leaf/light/heavy` を
渡している実装・skill・reference・test は 0 件と判明した（`remediation_loop` のみが
実使用）。そのため「controller が渡してよいのは `remediation_loop` のみ」という
`references/subagent-dispatch.md` の散文の禁止を、argparse の `choices` から
`leaf` / `light` / `heavy` を削除する機械的な制約に置き換える（YAGNI・不要な分岐を
増やさない）。

`--phase` に基づく text signal 経由の `leaf_task` 降格（`LEAF_HINTS` 一致による、
`--complexity` を使わない別経路）も同型の fail-open だった（独立レビュー round 3
High/blocking 指摘）。`tests/checks/hooks.sh:262,300` が formal gate phase 内でも
テキストシグナルで軽量化する既存動作を期待値として固定していたため当初は対象外・
既知の限界として開示するに留めていたが、ユーザー確認のうえ本 PR で修正し hooks.sh
の期待値も更新した（`test_formal_gate_phase_text_signal_does_not_downgrade_to_leaf_task`
参照）。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _plugin_module_loader import load_plugin_module

from _paths import PLUGIN_ROOT as ROOT
RESOLVER = ROOT / "scripts" / "resolve-gdd-model.py"
WORKER = ROOT / "scripts" / "run-gdd-worker.py"

# formal gate の 1 つを代表として使う。`FORMAL_GATE_PHASES` の全件走査は
# test_remediation_loop_model_routing_contract.py 側の責務と重複させない。
FORMAL_GATE_PHASE = "gdd-implementation-gating"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class ComplexityFlagFormalGateGuardTests(unittest.TestCase):
    def test_resolver_cli_rejects_leaf_light_heavy(self) -> None:
        # fail-open ケース 1: block すべき入力（formal gate を軽量 tier へ落とす
        # 明示指定）が allow になっていないこと。argparse レベルで拒否され、
        # exit code が非 0 であること。
        for complexity in ("leaf", "light", "heavy"):
            with self.subTest(complexity=complexity):
                result = subprocess.run(
                    [
                        sys.executable, str(RESOLVER),
                        "--runtime", "claude_code",
                        "--phase", FORMAL_GATE_PHASE,
                        "--complexity", complexity,
                        "--json",
                    ],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout)
                # 拒否された場合に軽量 tier の値が出力に紛れ込んでいないこと
                # （非 0 終了しつつ stdout に結果が漏れる回帰を防ぐ）。独立レビュー
                # round 4 指摘: argparse の error は stderr へ出て stdout は構造上
                # 常に空になるため、tier 文字列個別の assertNotIn は落ちようがない。
                # stdout が空であること自体を検査する（この不変が崩れたら検知する）。
                self.assertEqual(result.stdout, "")

    def test_worker_runner_cli_rejects_leaf_light_heavy(self) -> None:
        # 入口（run-gdd-worker.py）からも同じ拒否が効くこと。dry-run でも
        # command が組み立てられない（= worker が起動しない）ことを確認する。
        for complexity in ("leaf", "light", "heavy"):
            with self.subTest(complexity=complexity):
                result = subprocess.run(
                    [
                        sys.executable, str(WORKER),
                        "--runtime", "codex",
                        "--phase", FORMAL_GATE_PHASE,
                        "--complexity", complexity,
                        "--text", "t",
                        "--dry-run",
                    ],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout)
                # 独立レビュー round 4 指摘: argparse の error は stderr へ出るため
                # stdout は構造上常に空（tier 文字列個別の assertNotIn は落ちようがない）。
                self.assertEqual(result.stdout, "")

    def test_formal_gate_phase_text_signal_does_not_downgrade_to_leaf_task(self) -> None:
        # 独立レビュー round 3 High/blocking 指摘（F1）: `--complexity` を使わずとも、
        # `classify_tier()` の `leaf_task:bounded_leaf_task` 分岐（LEAF_HINTS の
        # テキスト一致、`if phase:` の phase 既定判定より前で return する）により
        # formal gate phase を黙って `leaf_task` へ降格できた。同型 fail-open として
        # ユーザー判断によりこの PR で修正する（`tests/checks/hooks.sh:262,300` の
        # 期待値も本 PR で更新。「classify routing candidates」は LEAF_HINTS の
        # "classify" / "routing" に一致する）。
        result = subprocess.run(
            [
                sys.executable, str(RESOLVER),
                "--runtime", "cursor",
                "--phase", "gdd-requirements-gating",
                "--text", "classify routing candidates",
                "--json",
            ],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tier"], "formal_gate")
        # 独立レビュー round 4 指摘: list membership の assertNotIn("leaf_task", reasons)
        # は実際の要素が "leaf_task:bounded_leaf_task"（完全一致しない文字列）のため
        # 常に真になり判別力が無かった。完全一致で検査する。
        self.assertNotIn("leaf_task:bounded_leaf_task", payload["reasons"])

    def test_general_heavy_phases_text_signal_does_not_downgrade_to_leaf_task(self) -> None:
        # 独立レビュー round 4 指摘（F4）: floor の集合
        # `{"formal_gate", "general_heavy", "general_heavy_risk"}` のうち
        # formal_gate しかテストされていなかった。残り 2 tier も pin する。
        for phase, expected_tier, expected_reason in (
            ("gdd-systematic-debugging", "general_heavy", "phase_default:general_heavy:gdd-systematic-debugging"),
            ("gdd-pr-review", "general_heavy_risk", "phase_default:general_heavy_risk:gdd-pr-review"),
        ):
            with self.subTest(phase=phase):
                result = subprocess.run(
                    [
                        sys.executable, str(RESOLVER),
                        "--runtime", "cursor",
                        "--phase", phase,
                        "--text", "classify routing candidates",
                        "--json",
                    ],
                    capture_output=True, text=True, check=True,
                )
                payload = json.loads(result.stdout)
                self.assertEqual(payload["tier"], expected_tier)
                self.assertIn(expected_reason, payload["reasons"])
                self.assertNotIn("leaf_task:bounded_leaf_task", payload["reasons"])

    def test_unknown_phase_string_does_not_fall_through_to_leaf_task(self) -> None:
        # 独立レビュー round 4 High/blocking 指摘（F2）: `phase_tier =
        # PHASE_TO_TIER.get(phase or "", "light_task")` は `--phase` が未知・
        # 表記ゆれ（大文字小文字・タイポ等）の場合 permissive な既定
        # （light_task）へ倒れ、floor が一切効かなかった。ユーザー判断により
        # 閉じた部分集合（`phase` が非空かつ `PHASE_TO_TIER` に無い値）のみ
        # 修正する：未知 phase は leaf_task 分岐を素通りさせない。
        # 独立レビュー round 5 指摘（F-3）: `leaf_task` と `light_task` は
        # 全 runtime で model 自体は同一（`TIER_TO_MODEL` 参照）のため、tier
        # ラベルだけの検査では floor の実効性（reasoning effort の引き上げ）を
        # 判別できない。`effort` も検査して回帰を検知できるようにする。
        result = subprocess.run(
            [
                sys.executable, str(RESOLVER),
                "--runtime", "cursor",
                "--phase", "gdd-requirements-gating-typo",
                "--text", "classify routing candidates",
                "--json",
            ],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertNotEqual(payload["tier"], "leaf_task")
        self.assertNotIn("leaf_task:bounded_leaf_task", payload["reasons"])
        # leaf_task の effort（"low"）ではなく light_task の effort（"medium"）が
        # 適用されていること（model は leaf_task と同一のため、floor の効果を
        # 判別できる唯一のフィールドが effort）。
        self.assertEqual(payload["effort"], "medium")

    def test_resolver_phase_argument_is_normalized_like_other_readers(self) -> None:
        # 独立レビュー round 6 High/blocking 指摘（H-1）: `hooks/scripts/gdd_stop_hook.py
        # ::_detect_phase()` と `run-gdd-worker.py::main()` には round 4/5 で
        # `.strip().lower()` 正規化を足したが、`resolve-gdd-model.py::main()` 自身は
        # `--phase` をそのまま `classify_tier()` へ渡しており、changelog が「3 実装
        # 全てに対称適用した」と主張していたのに実際には適用されていなかった
        # （`phase in PHASE_TO_TIER` の完全一致 lookup が表記ゆれで外れ、floor は
        # `leaf_task` への降格は防ぐが `formal_gate` -> `light_task` の降格は
        # 素通りしていた）。`--phase` と `--state-file` の両チャネルで正規化する。
        for extra_args in (
            ["--phase", "GDD-Implementation-Gating"],
            ["--phase", " gdd-implementation-gating "],
        ):
            with self.subTest(extra_args=extra_args):
                result = subprocess.run(
                    [
                        sys.executable, str(RESOLVER),
                        "--runtime", "claude_code",
                        *extra_args,
                        "--json",
                    ],
                    capture_output=True, text=True, check=True,
                )
                payload = json.loads(result.stdout)
                self.assertEqual(payload["tier"], "formal_gate")
                self.assertEqual(payload["model"], "opus")

    def test_resolver_state_file_detected_phase_is_normalized(self) -> None:
        # 独立レビュー round 6 指摘（H-1）: `--phase` 未指定時に state file の
        # frontmatter `detected_phase` から読む経路（`run-with-plugin.sh` が
        # `--state-file` のみを渡す本番導線）も同じ非正規化の fail-open を踏む。
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.md"
            state_file.write_text(
                "---\ndetected_phase: GDD-Implementation-Gating\n---\nbody\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable, str(RESOLVER),
                    "--runtime", "claude_code",
                    "--state-file", str(state_file),
                    "--json",
                ],
                capture_output=True, text=True, check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["tier"], "formal_gate")
            self.assertEqual(payload["model"], "opus")

    def test_resolver_state_file_frontmatter_value_of_three_hyphens_does_not_lose_detected_phase(
        self,
    ) -> None:
        # 独立レビュー round 10 High/blocking 指摘（H-1）: `lib/state_io.py::parse_state()`
        # は round 9 で frontmatter 終端を「内容が厳密に `---` である行」でのみ判定する
        # よう line-exact 化したが、同じ state file フォーマットを読む
        # `resolve-gdd-model.py::extract_frontmatter_value()`/`read_text_from_state()`
        # は旧来の部分文字列一致 `text.split("---\n", 2)` のまま残っており、値が
        # ちょうど `"---"` になる frontmatter 行（`detected_phase` より前にある別の
        # key。例えば `resume_from_baseline` は `.steering` の自由文から入るため
        # `"---"` で終わり得る）があると、その行を終端と誤認してそれより後ろの
        # `detected_phase` を丸ごと読み落とし、`--phase` 未指定・`--state-file` のみの
        # 本番導線（`run-with-plugin.sh`）で formal gate phase が `light_task` へ
        # 黙って降格していた（round 9 H-1 と同じバグ・同じ入力を読む別実装。
        # `state_io.py::parse_state()` と対称の line-exact 判定にする）。
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "state.md"
            state_file.write_text(
                "---\n"
                "active: true\n"
                "resume_from_baseline: ---\n"
                "detected_phase: gdd-refactor-planning\n"
                "---\n"
                "body\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable, str(RESOLVER),
                    "--runtime", "claude_code",
                    "--state-file", str(state_file),
                    "--json",
                ],
                capture_output=True, text=True, check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["phase"], "gdd-refactor-planning")
            self.assertEqual(payload["tier"], "general_heavy")
            self.assertEqual(payload["model"], "opus")

    def test_leaf_task_text_signal_still_applies_without_formal_gate_phase(self) -> None:
        # fail-open ケース 3 の裏側（過剰拒否の回帰防止）: formal gate 以外の phase・
        # phase 未指定では、従来どおり LEAF_HINTS によるテキスト一致で leaf_task へ
        # 分類されること（`gdd-status` は leaf_task tier。phase 未指定は
        # 既存の `tests/checks/hooks.sh` ケースと同型）。
        result = subprocess.run(
            [
                sys.executable, str(RESOLVER),
                "--runtime", "cursor",
                "--text", "classify routing candidates",
                "--json",
            ],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tier"], "leaf_task")
        self.assertIn("leaf_task:bounded_leaf_task", payload["reasons"])

    def test_resolver_cli_still_accepts_remediation_loop(self) -> None:
        # fail-open ケース 3: 判定できない／過剰拒否で正当な入力まで通らなくなる
        # 退行が無いこと（本体の回帰防止。remediation_loop は唯一の実使用値）。
        result = subprocess.run(
            [
                sys.executable, str(RESOLVER),
                "--runtime", "cursor",
                "--phase", FORMAL_GATE_PHASE,
                "--complexity", "remediation_loop",
                "--json",
            ],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tier"], "remediation_loop")
        self.assertEqual(payload["model"], "grok-4.6")

    def test_formal_gate_phase_without_complexity_is_unaffected(self) -> None:
        # fail-open ケース 3 の裏側: 通常経路（--complexity 未指定）が
        # この修正で壊れていないこと。
        result = subprocess.run(
            [
                sys.executable, str(RESOLVER),
                "--runtime", "claude_code",
                "--phase", FORMAL_GATE_PHASE,
                "--json",
            ],
            capture_output=True, text=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tier"], "formal_gate")

    def test_skill_md_leaf_priority_limitation_matches_heavy_or_above_phases(self) -> None:
        # 独立レビュー round 5 指摘（F-4）: round 4 の F1 で `skills/gdd-model-routing/
        # SKILL.md` に足した「`detected_phase` が formal gate / 一般 heavy 系なら
        # leaf を優先しない」という floor の限定句（phase 接尾辞の列挙）が、実装側の
        # `HEAVY_OR_ABOVE_TIERS` 相当 phase 集合と一致することを検査していなかった。
        # `PHASE_TO_TIER` に heavy 系 phase が追加・改名されても SKILL.md の散文が
        # 追随せず黙って古くなる退行を検知する。
        resolver = load_plugin_module("scripts/resolve-gdd-model.py")
        skill = read("skills/gdd-model-routing/SKILL.md")
        anchor = "`detected_phase` が入っていても、`leaf_task` が明確なら leaf を優先してよい。"
        self.assertIn(anchor, skill)
        bullet_start = skill.index(anchor)
        bullet_end = skill.index("\n", bullet_start)
        bullet = skill[bullet_start:bullet_end]

        match = re.search(
            r"formal gate（([^）]+)）または一般 heavy 系（([^）]+)）",
            bullet,
        )
        self.assertIsNotNone(match, bullet)
        suffixes = [s.strip() for group in match.groups() for s in group.split("/")]
        enumerated_phases = {f"gdd-{suffix}" for suffix in suffixes}

        heavy_or_above_phases = {
            phase
            for phase, tier in resolver.PHASE_TO_TIER.items()
            if tier in resolver.HEAVY_OR_ABOVE_TIERS
        }
        self.assertEqual(enumerated_phases, heavy_or_above_phases)

    def test_formal_gate_phases_definitions_stay_in_sync(self) -> None:
        # 独立レビュー round 4 指摘（F7）: `FORMAL_GATE_PHASES` は
        # resolve-gdd-model.py と run-gdd-worker.py に同内容で 2 重定義されており、
        # かつ resolve-gdd-model.py の `PHASE_TO_TIER` で tier="formal_gate" の
        # phase 集合とも一致している必要がある（floor の集合が実質 3 箇所に
        # 分散しているため、片方だけ更新される退行を検知する）。
        resolver = load_plugin_module("scripts/resolve-gdd-model.py")
        worker = load_plugin_module("scripts/run-gdd-worker.py")
        from_phase_to_tier = {
            phase for phase, tier in resolver.PHASE_TO_TIER.items() if tier == "formal_gate"
        }
        self.assertEqual(set(resolver.FORMAL_GATE_PHASES), from_phase_to_tier)
        self.assertEqual(set(worker.FORMAL_GATE_PHASES), from_phase_to_tier)


if __name__ == "__main__":
    unittest.main()

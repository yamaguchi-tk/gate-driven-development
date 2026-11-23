"""P0 contract tests for meta-level GDD feedback loops."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _validate_plugin_reader import read_validate_plugin_and_checks


from _paths import PLUGIN_ROOT


def read(path: str) -> str:
    return (PLUGIN_ROOT / path).read_text(encoding="utf-8")


class P0MetaFeedbackContractTests(unittest.TestCase):
    def _write_decision_ready_hitl(
        self,
        path: Path,
        *,
        judgment: str = "既存方式を拡張する方針でよいか。",
        extra_sections: list[str] | None = None,
    ) -> None:
        sections = [
            "## 確認",
            "",
            "### どこまで自走するのか",
            "- はい。判断ポイントと自走範囲が合っていれば、このまま進めます。",
            "",
            "### 30秒判断",
            "**整理した要件**: GDDのHITL表示を、承認者が判断できる文章に直します。",
            "**実装する方法・内容**: 既存テンプレートとlintを更新し、新しい大きな仕組みは増やしません。",
            "**検証する方法・内容**: contract testとlintで、悪いHITLが落ちることを確認します。",
            "**どこまで自走するのか**: 実装、テスト、PR作成まで。本番反映やmergeは別承認です。",
            f"**判断ポイント**: {judgment}",
            "**段階実装サマリー**: 単一段階。今回のPRで完結します。",
            "",
            "### OKで進む範囲",
            "- HITLテンプレートとlintの更新。",
            "",
            "### OKでも許可されないこと",
            "- merge、deploy、本番相当write。",
            "",
            "### 人間が今やること",
            "- 表示内容と自走範囲が期待どおりか確認してOKする。",
            "",
            "### OK 後に残る作業",
            "- design-gating、TDD、実装、検証、PR作成。",
            "",
            "### PR検証後の次の導線",
            "- PRがmergeされたらローカル整理を案内し、次段階があれば同じチャットで「次に進んで」と言える状態にします。",
            "",
            "### 人間に戻す条件",
            "- scope、AC、security、architecture、自走上限が変わる場合。",
        ]
        if extra_sections:
            sections.extend(["", *extra_sections])
        path.write_text("\n".join(sections), encoding="utf-8")

    def test_runtime_budget_linter_measures_skill_and_template_runtime_surface(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-runtime-budget.py"
        context_budget = read("references/context-budget.md")
        validate = read_validate_plugin_and_checks()

        for token in [
            "SKILL body line budget",
            "Runtime template budget",
            "express runtime profile",
            "standard runtime profile",
            "estimated runtime tokens",
        ]:
            self.assertIn(token, context_budget + validate)

        # このテストは linter の「出力内容」（どの profile / ファイルを計測して
        # 報告するか）を検証するもので、budget の gate ではない。したがって全上限は
        # 意図的に緩く置き、この項目では落ちないようにする。
        # **不変条件**: ここの値は実 gate（tests/checks/skill-body-budget.sh と
        # tests/checks/lint-scripts-functional.sh の 6 引数）より必ず大きく保つこと。
        # 実 gate 側を引き上げたときにここが取り残されると、gate ではないテストが
        # 先に落ちて「budget 超過」に見える（以前の task で実際に発生。承認ポイント A で
        # express tokens を 33468 -> 33801 に上げた際、ここは 33600 のまま残っていた）。
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(PLUGIN_ROOT),
                "--max-skill-body-lines",
                "650",
                "--max-total-skill-body-lines",
                "7500",
                "--max-express-template-lines",
                "200",
                "--max-standard-template-lines",
                "850",
                "--max-express-estimated-tokens",
                "34500",
                "--max-standard-estimated-tokens",
                "57900",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Runtime Budget", result.stdout)
        self.assertIn("express runtime profile", result.stdout)
        self.assertIn("standard runtime profile", result.stdout)
        self.assertIn("skills/gdd-using-skills/SKILL.md", result.stdout)
        self.assertIn("commands/gdd-dev.md", result.stdout)

    def test_runtime_budget_linter_rejects_over_budget_skill_body(self) -> None:
        # Token budgets are intentionally set high (99999) so this test fails
        # only on --max-skill-body-lines (set to 10), not on token limits.
        script = PLUGIN_ROOT / "scripts" / "lint-runtime-budget.py"

        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(PLUGIN_ROOT),
                "--max-skill-body-lines",
                "10",
                "--max-total-skill-body-lines",
                "7500",
                "--max-express-template-lines",
                "200",
                "--max-standard-template-lines",
                "850",
                "--max-express-estimated-tokens",
                "99999",
                "--max-standard-estimated-tokens",
                "99999",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("SKILL body line budget", result.stdout)
        self.assertIn("gdd-completion-check/SKILL.md", result.stdout)

    def test_plain_language_linter_rejects_unexplained_internal_terms(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-human-check-language.py"
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-hitl.md"
            bad.write_text(
                "次に必要な判断は holdout を human-confirm して executable にすることです。\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("説明なしの内部用語", result.stdout)
        self.assertIn("holdout", result.stdout)
        self.assertIn("human-confirm", result.stdout)
        self.assertIn("executable", result.stdout)

    def test_plain_language_linter_allows_explained_internal_terms(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-human-check-language.py"
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good-hitl.md"
            good.write_text(
                "\n".join(
                    [
                        "評価用に取り分けたサンプル（holdout）を確認します。",
                        "人が内容を確認済みにする（human-confirm）作業です。",
                        "自動テストやコマンドで実行できる状態（executable）にします。",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(good)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)

    def test_plain_language_linter_requires_non_engineer_decision_brief_for_final_hitl(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-human-check-language.py"
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-final-hitl.md"
            bad.write_text(
                "\n".join(
                    [
                        "## 確認",
                        "",
                        "次に必要な判断は、既存の評価サンプルを確認済みにして、自動テストで使える状態にすることです。",
                        "",
                        "<gdd-stop reason=\"human-check-waiting\">",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("判断ポイント", result.stdout)
        self.assertIn("整理した要件", result.stdout)
        self.assertIn("実装する方法・内容", result.stdout)

    def test_plain_language_linter_allows_final_hitl_with_non_engineer_decision_brief(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-human-check-language.py"
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good-final-hitl.md"
            good.write_text(
                "\n".join(
                    [
                        "## 確認",
                        "",
                        "### 30秒判断（まず見るところ）",
                        "**整理した要件**: 通知先の設定を既存の仕組みで直します。",
                        "**実装する方法・内容**: 既存設定ファイルを更新し、新しい仕組みは増やしません。",
                        "**検証する方法・内容**: 設定の読み込みテストとlintで確認します。",
                        "**どこまで自走するのか**: 実装とPR作成まで。本番反映やmergeは別承認です。",
                        "**判断ポイント**: 通知先の変更範囲が期待どおりか。",
                        "**段階実装サマリー**: 単一段階: 今回のPRで完結。",
                        "",
                        "<gdd-stop reason=\"human-check-waiting\">",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(good)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)

    def test_plain_language_linter_is_part_of_plugin_validation(self) -> None:
        validate = read_validate_plugin_and_checks()

        self.assertIn("scripts/lint-human-check-language.py", validate)
        self.assertIn("BLOCK: human-check-language-lint", validate)

    def test_hitl_outcome_audit_linter_rejects_mismatch_or_unverified(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-outcome-audit.py"
        with tempfile.TemporaryDirectory() as tmp:
            requirements = Path(tmp) / "requirements.md"
            requirements.write_text(
                "\n".join(
                    [
                        "## HITL Outcome Audit",
                        "",
                        "| Approved Direction の欄 | 最終成果物で見るもの | 結果 | Evidence / notes |",
                        "|---|---|---|---|",
                        "| 何を作るか | diff | match | ok |",
                        "| どう作るか | stack | mismatch | stack changed silently |",
                        "| 確認すること | tests | unverified | evidence missing |",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(requirements)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("HITL Outcome Audit", result.stdout)
        self.assertIn("mismatch", result.stdout)
        self.assertIn("unverified", result.stdout)
        self.assertIn("completion を通さない", result.stdout)

    def test_hitl_outcome_audit_linter_allows_match_and_na(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-outcome-audit.py"
        with tempfile.TemporaryDirectory() as tmp:
            requirements = Path(tmp) / "requirements.md"
            requirements.write_text(
                "\n".join(
                    [
                        "## HITL Outcome Audit",
                        "",
                        "| Approved Direction の欄 | 最終成果物で見るもの | 結果 | Evidence / notes |",
                        "|---|---|---|---|",
                        "| 何を作るか | diff | match | ok |",
                        "| 確認しないこと | unsupported scope | N/A | not applicable with rationale |",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(requirements)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)

    def test_hitl_complexity_linter_rejects_over_budget_sample(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-complexity.py"
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "too-long-hitl.md"
            sample.write_text(
                "\n".join(
                    [
                        "## 確認",
                        "### 30秒判断",
                        "承認ポイント:",
                        "**1. Scope**",
                        "**2. Stack**",
                        "**3. Test**",
                        "**4. Runtime**",
                        "**5. Review**",
                        "**6. Deploy**",
                    ]
                    + [f"detail line {i}" for i in range(1, 18)]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    str(sample),
                    "--max-lines",
                    "12",
                    "--max-approval-points",
                    "5",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("GDD Complexity Budget", result.stdout)
        self.assertIn("HITL行数", result.stdout)
        self.assertIn("承認ポイント数", result.stdout)

    def test_hitl_decision_quality_linter_rejects_option_b_without_sibling_options(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-option-hitl.md"
            self._write_decision_ready_hitl(
                bad,
                judgment="Scope は Option B でよいか。",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Option label is undefined", result.stdout)
        self.assertIn("Option A / B / C", result.stdout)
        self.assertIn("選択肢の説明", result.stdout)

    def test_hitl_decision_quality_linter_allows_defined_option_set(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good-option-hitl.md"
            self._write_decision_ready_hitl(
                good,
                judgment="AIの仮決定は Option B です。A/B/Cの違いを確認してください。",
                extra_sections=[
                    "### 選択肢の説明",
                    "| 選択肢 | 何をする案か | 良い点 | 弱い点 / やらないこと | AIの仮決定 |",
                    "|---|---|---|---|---|",
                    "| Option A | 個別の文面だけを直す案 | 早い | 再発防止が弱い | 不採用 |",
                    "| Option B | テンプレートとlintを合わせて直す案 | 再発防止しやすい | 少し重い | 採用 |",
                    "| Option C | 評価基盤まで大きく作る案 | 保証が強い | 今回には重すぎる | 不採用 |",
                ],
            )

            result = subprocess.run(
                [sys.executable, str(script), str(good)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def _compact_layout_hitl(self, scope_block: str, deny_block: str) -> str:
        return "\n".join(
            [
                "## 確認",
                "",
                "### 何を作るか（整理した要件）",
                "承認範囲の欄が空のまま表示されないようにします。",
                "",
                "### どう作るか（実装する方法・内容）",
                "lint の欄抽出を、その欄の行だけに閉じます。",
                "",
                "### どう確かめるか（検証する方法・内容）",
                "compact の bullet 形と見出し形の HITL を lint にかけて終了コードを見ます。",
                "",
                "### どこまで自走するか（どこまで自走するのか）",
                scope_block,
                deny_block,
                "- 人間に戻す条件: scope、AC、security、architecture が変わる場合。",
                "",
                "### 判断ポイント",
                "1. 空欄検出を有効にするか — 変更前: 発火しない / 変更後: 発火する。",
                "",
                "### 段階実装（段階実装サマリー）",
                "単一段階。今回で完結します。",
                "",
                "### 現在地",
                "| 項目 | 内容 |",
                "|---|---|",
                "| 人間が今やること | 判断ポイントが意図どおりか確認して OK と返す |",
                "| OK 後に残る作業 | 実装、テスト、gate 再通過 |",
            ]
        )

    def test_hitl_decision_linter_detects_empty_approval_scope_in_both_layouts(self) -> None:
        """正本 compact は承認範囲を bullet で書く。見出し形だけでなく bullet 形でも空欄を落とす。"""
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        bullet_deny = "- OKでも許可されないこと: merge、deploy、本番相当 write、外部投稿。"
        heading_deny = "### OKでも許可されないこと\nmerge、deploy、本番相当 write、外部投稿。"
        cases = {
            "bullet-filled": ("- OKで進む範囲: 実装、テスト、review 収束まで AI に任せます。", bullet_deny),
            "bullet-nested": ("- OKで進む範囲:\n  - 実装とテストの追加。\n  - review 収束まで AI に任せます。", bullet_deny),
            "bullet-empty": ("- OKで進む範囲:", bullet_deny),
            "bullet-placeholder": ("- OKで進む範囲: 未定", bullet_deny),
            "heading-filled": ("### OKで進む範囲\n実装、テスト、review 収束まで AI に任せます。", heading_deny),
            "heading-empty": ("### OKで進む範囲", heading_deny),
        }
        results = {}
        with tempfile.TemporaryDirectory() as tmp:
            for name, (scope_block, deny_block) in cases.items():
                sample = Path(tmp) / f"{name}.md"
                sample.write_text(self._compact_layout_hitl(scope_block, deny_block), encoding="utf-8")
                results[name] = subprocess.run(
                    [sys.executable, str(script), str(sample)],
                    text=True,
                    capture_output=True,
                    check=False,
                )

        for name in ("bullet-filled", "bullet-nested", "heading-filled"):
            result = results[name]
            self.assertEqual(result.returncode, 0, f"{name}: {result.stdout}{result.stderr}")
        for name in ("bullet-empty", "bullet-placeholder", "heading-empty"):
            result = results[name]
            self.assertEqual(result.returncode, 1, f"{name}: {result.stdout}{result.stderr}")
            self.assertIn("decision section is empty or placeholder: OKで進む範囲", result.stdout, name)

    def test_hitl_decision_quality_linter_rejects_option_set_without_tradeoffs(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-option-tradeoffs-hitl.md"
            self._write_decision_ready_hitl(
                bad,
                judgment="AIの仮決定は Option B です。A/B/Cの違いを確認してください。",
                extra_sections=[
                    "### 選択肢の説明",
                    "| 選択肢 | 何をする案か |",
                    "|---|---|",
                    "| Option A | 個別の文面だけを直す案 |",
                    "| Option B | テンプレートとlintを合わせて直す案 |",
                    "| Option C | 評価基盤まで大きく作る案 |",
                ],
            )

            result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("missing option explanation detail", result.stdout)
        self.assertIn("良い点", result.stdout)
        self.assertIn("弱い点", result.stdout)
        self.assertIn("AIの仮決定", result.stdout)

    def test_hitl_decision_quality_linter_rejects_multi_pr_without_strategy_options(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-multi-pr-hitl.md"
            self._write_decision_ready_hitl(
                bad,
                judgment="複数PRで進める方針でよいか。",
                extra_sections=[
                    "### 段階実装案",
                    "| Stage | この段階でやること | このPR/後続 | 完了確認 |",
                    "|---|---|---|---|",
                    "| S-1 | テンプレート更新 | current-pr | contract test |",
                    "| S-2 | eval更新 | follow-up-pr | scenario test |",
                ],
            )

            result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("missing Multiple PR Strategy Options", result.stdout)
        self.assertIn("単一PR", result.stdout)
        self.assertIn("複数PR", result.stdout)

    def test_hitl_decision_quality_linter_rejects_post_merge_verification_without_strategy_options(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad-post-merge-hitl.md"
            self._write_decision_ready_hitl(
                bad,
                judgment="post-merge verification まで進める方針でよいか。",
                extra_sections=[
                    "### 段階実装案",
                    "| Stage | この段階でやること | このPR/後続 | 完了確認 |",
                    "|---|---|---|---|",
                    "| S-1 | テンプレート更新 | current-pr | contract test |",
                    "| S-2 | merge後検証 | post-merge verification | scenario test |",
                ],
            )

            result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("missing Multiple PR Strategy Options", result.stdout)

    def test_hitl_decision_quality_linter_allows_multi_pr_with_strategy_options(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good-multi-pr-hitl.md"
            self._write_decision_ready_hitl(
                good,
                judgment="AIの仮決定は複数PR案です。PRの分け方を確認してください。",
                extra_sections=[
                    "### Multiple PR Strategy Options",
                    "| 選択肢 | 何をする案か | 良い点 | 弱い点 / やらないこと | AIの仮決定 |",
                    "|---|---|---|---|---|",
                    "| 単一PR | 全部を1つのPRで実装する | レビュー対象が一度で済む | PRが大きくなる | 不採用 |",
                    "| 複数PR | 安定した単位でPRを分ける | レビューと戻しがしやすい | 追跡が必要 | 採用 |",
                    "| 後続PR着手前に再承認 | 後続PRはマージ後に再確認して始める | 混線しにくい | 少し遅い | 採用 |",
                    "",
                    "### 段階実装案",
                    "| Stage | この段階でやること | このPR/後続 | 後続の追跡先 | 完了確認 |",
                    "|---|---|---|---|---|",
                    "| S-1 | テンプレート更新 | current-pr | なし | contract test |",
                    "| S-2 | eval更新 | follow-up-pr | Planned Follow-up Stage Lane | scenario test |",
                ],
            )

            result = subprocess.run(
                [sys.executable, str(script), str(good)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_new_p0_meta_lints_are_part_of_plugin_validation(self) -> None:
        validate = read_validate_plugin_and_checks()

        for token in [
            "references/workflow-incident-review.md",
            "scripts/lint-resume-integrity.py",
            "scripts/lint-hitl-outcome-audit.py",
            "scripts/lint-hitl-complexity.py",
            "scripts/lint-hitl-display-integrity.py",
            "scripts/lint-human-check-language.py",
            "scripts/lint-pr-review-followup-state.py",
            "BLOCK: resume-integrity-lint",
            "BLOCK: hitl-outcome-audit-lint",
            "BLOCK: hitl-complexity-lint",
            "BLOCK: hitl-display-integrity-lint",
            "BLOCK: human-check-language-lint",
            "BLOCK: pr-review-followup-state-lint",
        ]:
            self.assertIn(token, validate)

    def test_resume_integrity_linter_rejects_mixed_task_branch_and_worktree(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260601-example-review-task"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "## Gate Status",
                        "- Task ID: 20260601-example-review-task",
                        "- Active Worktree Path: /tmp/repo",
                        "- Active Branch: codex/20260605-example-dns-task",
                        "- Resume From: gdd-subagent-driven-implementation",
                        "- Next Action: gdd-subagent-driven-implementation",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), "--steering-dir", str(steering), "--branch", "codex/20260605-example-dns-task"],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Resume Integrity", result.stdout)
        self.assertIn("branch/task mismatch", result.stdout)

    def test_resume_integrity_linter_allows_matching_task_branch_and_worktree(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260605-example-hardening-task"
            steering.mkdir(parents=True)
            (steering / "tasklist.md").write_text("## Current Task\n- T-1\n", encoding="utf-8")
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "## Gate Status",
                        "- Task ID: 20260605-example-hardening-task",
                        f"- Active Worktree Path: {repo}",
                        "- Active Branch: codex/20260605-example-hardening-task",
                        "- Resume From: gdd-subagent-driven-implementation",
                        "- Next Action: gdd-subagent-driven-implementation",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--steering-dir",
                    str(steering),
                    "--branch",
                    "codex/20260605-example-hardening-task",
                    "--worktree-path",
                    str(repo),
                    "--quiet",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_resume_integrity_linter_allows_express_resume_from_before_tasklist_exists(self) -> None:
        # 独立-15 finding 9: build_like 判定が Resume From も見ていたため、express の
        # 承認直後〜tasklist.md 作成前の crash recovery window（Resume From=
        # gdd-test-driven-development、tasklist.md 未作成が正常。state-machine.md:424）を
        # 「build resume requires tasklist.md」と誤検知していた。独立-27 finding 3:
        # 実装（lint-resume-integrity.py の build_like）は Next Action と Resume From の
        # 両方で判定しており、Task Size=quick (express) かつ Resume From=
        # gdd-test-driven-development の組み合わせ（この crash recovery window）だけを
        # Resume From 側の判定から除外する（Resume From 側の block 自体は
        # test_resume_integrity_linter_blocks_stale_resume_from_without_tasklist と
        # test_resume_integrity_linter_blocks_stray_gdd_tdd_resume_from_outside_express_task_size
        # が固定する）。
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260621-express-crash-recovery"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "---",
                        "Task Size: quick (express)",
                        "---",
                        "",
                        "## Gate Status",
                        "- Task ID: 20260621-express-crash-recovery",
                        f"- Active Worktree Path: {repo}",
                        "- Active Branch: codex/20260621-express-crash-recovery",
                        "- Resume From: gdd-test-driven-development",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--steering-dir",
                    str(steering),
                    "--branch",
                    "codex/20260621-express-crash-recovery",
                    "--worktree-path",
                    str(repo),
                    "--quiet",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_resume_integrity_linter_blocks_build_resume_without_tasklist(self) -> None:
        # 独立-16 finding 4: build_like が block する側（tasklist.md 無しで build 系
        # Next Action）を固定するテストが 1 本も無く、判定ブロックを丸ごと削除しても
        # 全テストが緑のまま通っていた（等価変異の生存）。finding 5: build_like の
        # token 集合が state-machine.md § active steering の決定規則 1. build candidate
        # の Next Action 集合（gdd-systematic-debugging・gdd-refactor-planning を含む
        # 6 値）と揃っておらず、この 2 値では誤検知しないまま通っていた。6 値すべてで
        # rc=1・エラーメッセージを固定する。
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        build_next_actions = (
            "gdd-test-driven-development",
            "gdd-subagent-driven-implementation",
            "gdd-implementation-gating",
            "gdd-systematic-debugging",
            "gdd-refactor-planning",
            "gdd-completion-check",
        )
        for next_action in build_next_actions:
            with self.subTest(next_action=next_action), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                steering = repo / ".steering" / "20260621-no-tasklist"
                steering.mkdir(parents=True)
                (steering / "state.md").write_text(
                    "\n".join(
                        [
                            "## Gate Status",
                            "- Task ID: 20260621-no-tasklist",
                            f"- Active Worktree Path: {repo}",
                            "- Active Branch: codex/20260621-no-tasklist",
                            f"- Next Action: {next_action}",
                        ]
                    ),
                    encoding="utf-8",
                )

                result = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        "--steering-dir",
                        str(steering),
                        "--branch",
                        "codex/20260621-no-tasklist",
                        "--worktree-path",
                        str(repo),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("build resume requires tasklist.md", result.stdout + result.stderr)

    def test_resume_integrity_linter_blocks_stale_resume_from_without_tasklist(self) -> None:
        # 独立-18 finding 2: build_like の判定から Resume From を丸ごと外したため、
        # 閉じたかった入力（express の crash recovery window: Resume From=
        # gdd-test-driven-development・tasklist.md 未作成）以外の Resume From（例:
        # gdd-implementation-gating・tasklist.md 未作成という壊れた state）もこの
        # fail-closed lint を素通りするようになっていた。Next Action が無く Resume From
        # だけが build 系トークンを持つ場合も block する。
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        stale_resume_froms = (
            "gdd-subagent-driven-implementation",
            "gdd-implementation-gating",
            "gdd-systematic-debugging",
            "gdd-refactor-planning",
            "gdd-completion-check",
        )
        for resume_from in stale_resume_froms:
            with self.subTest(resume_from=resume_from), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                steering = repo / ".steering" / "20260621-stale-resume-from"
                steering.mkdir(parents=True)
                (steering / "state.md").write_text(
                    "\n".join(
                        [
                            "## Gate Status",
                            "- Task ID: 20260621-stale-resume-from",
                            f"- Active Worktree Path: {repo}",
                            "- Active Branch: codex/20260621-stale-resume-from",
                            f"- Resume From: {resume_from}",
                        ]
                    ),
                    encoding="utf-8",
                )

                result = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        "--steering-dir",
                        str(steering),
                        "--branch",
                        "codex/20260621-stale-resume-from",
                        "--worktree-path",
                        str(repo),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("build resume requires tasklist.md", result.stdout + result.stderr)

    def test_resume_integrity_linter_allows_express_resume_from_with_pipe_tail_annotation(self) -> None:
        # 独立-19 finding 2: normalize_slug() が pipe 区切りの注記（updated_by 等。
        # references/state-machine.md:323-325 が定める汎用 state field 書式）ごと潰すため、
        # 除外条件の完全一致比較 normalize_slug(resume_from) != "gdd-test-driven-development"
        # が成立せず、express の crash recovery window（tasklist.md 未作成が正常）に pipe
        # 付き注記が付いただけで誤って block していた。Resume From は先頭セグメント
        # （pipe より前）だけを比較に使う。
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260621-express-pipe-tail"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "---",
                        "Task Size: quick (express)",
                        "---",
                        "",
                        "## Gate Status",
                        "- Task ID: 20260621-express-pipe-tail",
                        f"- Active Worktree Path: {repo}",
                        "- Active Branch: codex/20260621-express-pipe-tail",
                        "- Resume From: gdd-test-driven-development | updated_by: gdd-dev | updated_at: 2026-09-22T10:00:00+09:00",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--steering-dir",
                    str(steering),
                    "--branch",
                    "codex/20260621-express-pipe-tail",
                    "--worktree-path",
                    str(repo),
                    "--quiet",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_resume_integrity_linter_blocks_stray_gdd_tdd_resume_from_outside_express_task_size(self) -> None:
        # 独立-19 finding 3: express 除外が Task Size を条件にしていなかったため、Task Size が
        # express 以外（standard・quick (express → standard) 等）でも Resume From=
        # gdd-test-driven-development・tasklist.md 未作成という壊れた state がこの
        # fail-closed lint を素通りしていた（差分のコメントは「express の窓だけを除外する」と
        # 宣言していたが、実装は Task Size を見ずに値 1 つだけで除外しており宣言より広く
        # 開いていた）。除外は Task Size=quick (express) かつ Resume From=
        # gdd-test-driven-development の組み合わせだけに絞る。
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        non_express_task_sizes = (
            "standard",
            "quick (standard)",
            "quick (express → standard)",
        )
        for task_size in non_express_task_sizes:
            with self.subTest(task_size=task_size), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                steering = repo / ".steering" / "20260621-non-express-stray-resume-from"
                steering.mkdir(parents=True)
                (steering / "state.md").write_text(
                    "\n".join(
                        [
                            "---",
                            f"Task Size: {task_size}",
                            "---",
                            "",
                            "## Gate Status",
                            "- Task ID: 20260621-non-express-stray-resume-from",
                            f"- Active Worktree Path: {repo}",
                            "- Active Branch: codex/20260621-non-express-stray-resume-from",
                            "- Resume From: gdd-test-driven-development",
                        ]
                    ),
                    encoding="utf-8",
                )

                result = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        "--steering-dir",
                        str(steering),
                        "--branch",
                        "codex/20260621-non-express-stray-resume-from",
                        "--worktree-path",
                        str(repo),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("build resume requires tasklist.md", result.stdout + result.stderr)

    def test_resume_integrity_linter_pipe_tail_annotation_does_not_break_terminal_or_next_action_reads(
        self,
    ) -> None:
        # 独立-20 finding 2: 独立-19 の pipe 先頭セグメント切り出しは Resume From・Task Size
        # の 2 読み取りにしか適用されず、is_terminal() の Resume From・Next Action 読み取りと
        # build_like の Next Action 読み取りは pipe 尾部を含んだまま比較していた。
        # `Next Action: done | updated_by: ... | updated_at: ...` を default branch で
        # lint すると、terminal 判定が外れて "non-terminal steering on default branch" を
        # 誤検出し、かつ "completion-check" の部分一致で build_like も誤って True になる
        # （tasklist.md が無ければ "build resume requires tasklist.md" も誤検出）。
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260621-pipe-tail-next-action"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "## Gate Status",
                        "- Task ID: 20260621-pipe-tail-next-action",
                        f"- Active Worktree Path: {repo}",
                        "- Active Branch: main",
                        "- Resume From: done",
                        "- Next Action: done | updated_by: gdd-completion-check | updated_at: 2026-09-22T10:00:00+09:00",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--steering-dir",
                    str(steering),
                    "--branch",
                    "main",
                    "--worktree-path",
                    str(repo),
                    "--quiet",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_resume_integrity_linter_blocks_when_task_size_is_missing_even_with_express_resume_from(
        self,
    ) -> None:
        # 独立-20 finding 3: express 除外は Task Size=quick (express) との AND 条件になった。
        # Task Size が欠落した state.md（`extract_field` は空文字を返す）では
        # is_express_crash_recovery_window=False になり、fail-closed の block 方向を維持する
        # （`references/state-field-tiers.md` の Lightweight Template は正規の express
        # state.md に必ず Task Size frontmatter を持たせるため、この経路は非正規の state.md
        # だけが通る）。この挙動を固定する。
        script = PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260621-missing-task-size"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "## Gate Status",
                        "- Task ID: 20260621-missing-task-size",
                        f"- Active Worktree Path: {repo}",
                        "- Active Branch: codex/20260621-missing-task-size",
                        "- Resume From: gdd-test-driven-development",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--steering-dir",
                    str(steering),
                    "--branch",
                    "codex/20260621-missing-task-size",
                    "--worktree-path",
                    str(repo),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("build resume requires tasklist.md", result.stdout + result.stderr)

    def test_continuity_linter_pipe_tail_annotation_on_next_action_does_not_trigger_false_build_like(
        self,
    ) -> None:
        # 独立-21 finding 2: lint-resume-integrity.py 側だけ `field_head()` で pipe 先頭
        # セグメントを切り出すようにした結果、同じ state.md を読む別実装
        # scripts/lint-state-tasklist-continuity.py の action_is_build_like() は
        # pipe 尾部を含む全文で部分一致するため、`Next Action` の実際の値が build-like
        # でなくても `updated_by: gdd-test-driven-development` のような注記に含まれる
        # トークンで誤って build-like と判定してしまう。この Next Action 側の非対称は
        # この diff が新たに作ったもの（Resume From 側の非対称は base から存在した）。
        script = PLUGIN_ROOT / "scripts" / "lint-state-tasklist-continuity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260621-pipe-tail-next-action-continuity"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "## Gate Status",
                        "- Task ID: 20260621-pipe-tail-next-action-continuity",
                        "- Next Action: human-check-waiting | updated_by: gdd-test-driven-development | updated_at: 2026-09-22T10:00:00+09:00",
                        "- Resume From: gdd-design-gating",
                    ]
                ),
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "## Review Status\nNext Action=gdd-design-gating\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), "--steering-dir", str(steering), "--quiet"],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_continuity_linter_still_blocks_build_like_next_action_with_pipe_tail_annotation(
        self,
    ) -> None:
        # 独立-22 finding 3（独立-21 finding 2 の block 側回帰）: field_head() 追加で
        # pipe 尾部を無視するようにした結果、head セグメント自体が build-like な値
        # （`gdd-implementation-gating` 等）のケースまで一緒に見逃していないかを固定する。
        # 先頭セグメントが build-like なら、pipe 尾部の有無に関わらず `## Current Task`
        # 欠落時に block し続ける。
        script = PLUGIN_ROOT / "scripts" / "lint-state-tasklist-continuity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260621-pipe-tail-still-blocks"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "## Gate Status",
                        "- Task ID: 20260621-pipe-tail-still-blocks",
                        "- Next Action: gdd-implementation-gating | updated_by: gdd-test-driven-development | updated_at: 2026-09-22T10:00:00+09:00",
                        "- Resume From: gdd-design-gating",
                    ]
                ),
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "## Review Status\nNext Action=gdd-design-gating\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), "--steering-dir", str(steering)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            "build-like resume requires tasklist.md Current Task",
            result.stdout + result.stderr,
        )

    def test_continuity_linter_empty_head_with_build_token_only_in_pipe_tail_is_not_build_like(
        self,
    ) -> None:
        # 独立-22 finding 3 / 独立-23 finding 6: `field_head()` は先頭セグメントだけを見る
        # 設計であり、pipe 尾部（`updated_by:` 等の注記）に build token が含まれるだけでは
        # build-like と判定しない。`Next Action` の値そのものが空（コロン直後が pipe）で、
        # `Resume From` も build-like でない場合、`## Current Task` が無くても block しない。
        # `references/state-machine.md` § state field のフォーマット検証は、先頭セグメントが
        # 空文字列の値を不正値・fail-closed 対象と定めており、この lint（読み取り時）は
        # その規定どおりには block していない。書き込み時に不正値を防ぐのは
        # `hooks/scripts/validate-steering-write.py` 側の役割だが、本 diff の範囲では
        # そちらがこの具体的な形（空 head + pipe 尾部）を確実に防ぐことまでは確認していない。
        # このテストは「意図した正しい設計」としてではなく、現状の挙動を固定するために書く
        # （既知の未解消ギャップとして PR 本文の限界に列挙する）。
        script = PLUGIN_ROOT / "scripts" / "lint-state-tasklist-continuity.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            steering = repo / ".steering" / "20260621-empty-head-build-token-in-tail"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "\n".join(
                    [
                        "## Gate Status",
                        "- Task ID: 20260621-empty-head-build-token-in-tail",
                        "- Next Action:  | updated_by: gdd-implementation-gating",
                        "- Resume From: gdd-design-gating",
                    ]
                ),
                encoding="utf-8",
            )
            (steering / "tasklist.md").write_text(
                "## Review Status\nNext Action=gdd-design-gating\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), "--steering-dir", str(steering), "--quiet"],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pr_review_followup_linter_rejects_clean_before_post_fix_refresh(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-pr-review-followup-state.py"
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.md"
            state.write_text(
                "\n".join(
                    [
                        "PR Review Follow-up Status: clean",
                        "PR Review Follow-up Attempts: 2",
                        "PR URL: https://github.com/example/repo/pull/123",
                        "Fresh PR Review Evidence: gh pr view 123 at 2026-06-07T12:00:00+09:00",
                        "Fresh PR Checks Evidence: gh pr checks 123 at 2026-06-07T12:00:00+09:00 pass",
                        "",
                        "PR Review Follow-up:",
                        "- PR URL: https://github.com/example/repo/pull/123",
                        "- Iteration: 2",
                        "- Collected findings: 0",
                        "- Valid actionable findings: 0",
                        "- Idempotency keys processed: human:thread-1:src/app.py:42:missing-test",
                        "- Fixed findings: thread-1",
                        "- Invalid / out-of-scope: none",
                        "- CI failure: none",
                        "- Verification: pytest tests/test_app.py PASS",
                        "- Push: abc1234",
                        "- Re-review request: sent",
                        "- Next: actionable finding 0件",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(state)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("post-fix fresh review evidence", result.stdout)
        self.assertIn("post-fix fresh checks evidence", result.stdout)

    def test_pr_review_followup_linter_rejects_clean_with_pending_checks(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-pr-review-followup-state.py"
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "state.md"
            state.write_text(
                "\n".join(
                    [
                        "PR Review Follow-up Status: clean",
                        "PR Review Follow-up Attempts: 2",
                        "PR URL: https://github.com/example/repo/pull/123",
                        "Fresh PR Review Evidence: gh pr view 123 at 2026-06-07T12:10:00+09:00",
                        "Fresh PR Checks Evidence: gh pr checks 123 at 2026-06-07T12:10:00+09:00 pending",
                        "",
                        "PR Review Follow-up:",
                        "- PR URL: https://github.com/example/repo/pull/123",
                        "- Iteration: 2",
                        "- Collected findings: 0",
                        "- Valid actionable findings: 0",
                        "- Idempotency keys processed: none",
                        "- Fixed findings: none",
                        "- Invalid / out-of-scope: none",
                        "- CI failure: none",
                        "- Verification: pytest tests/test_app.py PASS",
                        "- Push: not_needed",
                        "- Re-review request: not_needed",
                        "- Next: actionable finding 0件",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(script), str(state)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("fresh checks evidence is not pass/neutral/skipped", result.stdout)


if __name__ == "__main__":
    unittest.main()

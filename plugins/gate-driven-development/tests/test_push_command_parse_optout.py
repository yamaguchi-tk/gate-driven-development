"""`push_command_parse` の opt-out の受理面・副作用の無い push の除外・CLI entrypoint の opt-out 境界の単体テスト。

`test_push_command_parse.py` から分けた。

確かめる本体は `hooks/scripts/lib/push_command_parse.py`・`hooks/scripts/lib/git_command_parse.py`
（`tokenize` などは `git_command_parse` の定義を `push_command_parse` が再公開している）。
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from _paths import PLUGIN_ROOT
from _timing_budget import hang_guard_seconds

PRE_PUSH_HANG_GUARD = hang_guard_seconds("run-pre-push-gate-hook.sh")
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

import push_command_parse as pcp  # noqa: E402


class FindOptoutTests(unittest.TestCase):
    """opt-out 受理面の機械判定（AC-4、design.md § opt-out 受理面の機械定義）。

    肯定側・否定側を対で固定する。CRLF の対は T-1 Carry Forward advisory A-3 の
    判断（T-2 で選択: 行継続の処理〔今は `shell_lexer.normalize`〕は `\\r\\n` を
    行継続にせず実 bash に合わせる = 過大受理を避ける側）をそのまま固定する。
    """

    def test_accepts_command_start_prefix(self) -> None:
        tokens = pcp.tokenize("GDD_SKIP_PRE_PUSH_GATE=1 git push origin main")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertTrue(result["accepted"])
        self.assertEqual(result["via"], "command-prefix")

    def test_accepts_env_wrapped_prefix(self) -> None:
        tokens = pcp.tokenize("env GDD_SKIP_PRE_PUSH_GATE=1 git push origin main")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertTrue(result["accepted"])

    def test_rejects_echo_prefix(self) -> None:
        tokens = pcp.tokenize("echo GDD_SKIP_PRE_PUSH_GATE=1 git push")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertFalse(result["accepted"])

    def test_rejects_assignment_not_adjoining_push(self) -> None:
        tokens = pcp.tokenize(
            "GDD_SKIP_PRE_PUSH_GATE=1 git rev-parse HEAD && git push origin HEAD"
        )
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertFalse(result["accepted"])

    def test_rejects_bash_c_expansion(self) -> None:
        # 境界値は tokenize_with_boundary から取る（shlex.split 再計算は禁止。
        # T-1 remediation 1 / F-2 対応）
        tokens, raw_count = pcp.tokenize_with_boundary(
            "bash -c 'GDD_SKIP_PRE_PUSH_GATE=1 git push'"
        )
        result = pcp.find_optout(tokens, original_token_count=raw_count)
        self.assertFalse(result["accepted"])

    def test_accepts_line_continuation_prefix(self) -> None:
        # design.md § opt-out 受理面の機械定義: 「行継続を挟んだ同形」は受理される。
        # `\` + LF（真の行継続）は除去され token を残さないため同一コマンド扱い。
        tokens = pcp.tokenize("GDD_SKIP_PRE_PUSH_GATE=1 \\\ngit push origin main")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertTrue(result["accepted"])

    def test_accepts_prefix_at_start_of_line_after_newline(self) -> None:
        # design.md § opt-out 受理面の機械定義 item 1: 改行 token の直後も
        # 「コマンド先頭」。実 bash でも 2 行目は var 付きの push として走る。
        tokens = pcp.tokenize("cd .\nGDD_SKIP_PRE_PUSH_GATE=1 git push origin main")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertTrue(result["accepted"])
        self.assertEqual(result["via"], "command-prefix")

    def test_rejects_raw_newline_between_assignment_and_push(self) -> None:
        # design.md § opt-out 受理面の機械定義 item 2 の明示拒否ケース（生 LF 版）。
        # 改行はコマンドの切れ目なので、代入列は別コマンドに波及しない。
        tokens = pcp.tokenize("GDD_SKIP_PRE_PUSH_GATE=1 env\ngit push origin main")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertFalse(result["accepted"])

    def test_rejects_crlf_line_continuation(self) -> None:
        # Attempt 5 advisory A-3 の実測ケースそのもの: `\` + CRLF は CR だけを
        # エスケープし、LF はコマンド区切りとして残る（実 bash: env 非継承）。
        # `env` と `git push` は別コマンドになるため受理されてはならない。
        tokens = pcp.tokenize(
            "GDD_SKIP_PRE_PUSH_GATE=1 env \\\r\ngit push origin main"
        )
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertFalse(result["accepted"])

    def test_rejects_brace_group_prefix_with_default_separators(self) -> None:
        # 既定値（run-pre-push-gate-hook.sh と共有）は不変であることを固定する。
        # `{` はブロック gate の受理面には含まれない。
        tokens = pcp.tokenize("{ GDD_SKIP_PRE_PUSH_GATE=1 git push origin main; }")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertFalse(result["accepted"])

    def test_accepts_brace_group_prefix_with_widened_separators(self) -> None:
        # PR #88 人間レビュー round 5 指摘 Medium: round 4 で push 検出だけ
        # `{` を command-start に含めた結果、nudge hook 内で「push とは判定
        # するのに opt-out は無視する」非対称が生まれていた。呼び出し側が
        # `PUSH_DETECTION_COMMAND_START_SEPARATORS` を明示すれば同じ
        # brace group 内の opt-out も受理できることを固定する。
        tokens = pcp.tokenize("{ GDD_SKIP_PRE_PUSH_GATE=1 git push origin main; }")
        result = pcp.find_optout(
            tokens,
            original_token_count=len(tokens),
            separators=pcp.PUSH_DETECTION_COMMAND_START_SEPARATORS,
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["via"], "command-prefix")

    def test_accepts_case_arm_prefix_with_widened_separators(self) -> None:
        tokens = pcp.tokenize(
            "case x in a) GDD_SKIP_PRE_PUSH_GATE=1 git push origin main;; esac"
        )
        result = pcp.find_optout(
            tokens,
            original_token_count=len(tokens),
            separators=pcp.PUSH_DETECTION_COMMAND_START_SEPARATORS,
        )
        self.assertTrue(result["accepted"])

    def test_rejects_optout_disguised_by_unenumerated_glued_redirect(self) -> None:
        # PR #88 人間レビュー round 6 指摘 High: 実 bash では `>|` は
        # noclobber 上書き付きの redirect 演算子で、`>|GDD_SKIP_PRE_PUSH_GATE=1`
        # は環境変数を立てず、ファイル名 `GDD_SKIP_PRE_PUSH_GATE=1` へ
        # 出力を逃がすだけ（実行される `git push` に opt-out は効かない）。
        # 是正前は `>|` が `_TWO_CHAR_OPERATORS` に無いため `>`+`|` に
        # 割れ、末尾の `|` が既定の区切り集合に一致してしまい、pre-push gate
        # （run-pre-push-gate-hook.sh、既定の `_COMMAND_START_SEPARATORS`）
        # が実際には立っていない opt-out を受理していた。`find_optout` は
        # `token_ends_with_separator` の glued 再解釈を使わず `token in
        # separators` の完全一致に留めることで、この過検出（fail-open）を
        # 防ぐ。
        tokens = pcp.tokenize(">|GDD_SKIP_PRE_PUSH_GATE=1 git push origin main")
        result = pcp.find_optout(tokens, original_token_count=len(tokens))
        self.assertFalse(result["accepted"])


class PushHasSideEffectExcludedFlagTests(unittest.TestCase):
    """実際に remote へ副作用を及ぼさない（or push 完了と無関係な）push 相当
    コマンドを検出する（PR #88 人間レビュー指摘 High-2 の付随修正）。

    `git push -h`（実 git、2026-09-15 計測）: `-d/--delete` `-n/--dry-run`
    `-h/--help` を確認済み。
    """

    def test_plain_push_has_no_excluded_flag(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertFalse(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_dry_run_short_flag_is_excluded(self) -> None:
        tokens = pcp.tokenize("git push -n origin main")
        _, git_index = pcp.is_git_push(tokens)
        self.assertTrue(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_dry_run_long_flag_is_excluded(self) -> None:
        tokens = pcp.tokenize("git push --dry-run origin main")
        _, git_index = pcp.is_git_push(tokens)
        self.assertTrue(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_delete_short_flag_is_excluded(self) -> None:
        tokens = pcp.tokenize("git push -d origin old-branch")
        _, git_index = pcp.is_git_push(tokens)
        self.assertTrue(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_delete_long_flag_is_excluded(self) -> None:
        tokens = pcp.tokenize("git push --delete origin old-branch")
        _, git_index = pcp.is_git_push(tokens)
        self.assertTrue(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_help_short_flag_is_excluded(self) -> None:
        tokens = pcp.tokenize("git push -h")
        _, git_index = pcp.is_git_push(tokens)
        self.assertTrue(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_help_long_flag_is_excluded(self) -> None:
        tokens = pcp.tokenize("git push --help")
        _, git_index = pcp.is_git_push(tokens)
        self.assertTrue(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_no_dry_run_negation_is_not_excluded(self) -> None:
        # `--no-dry-run` は dry-run を明示的に無効化する（実 push）。文字列
        # 部分一致ではなく token 完全一致で見るため誤って除外してはならない。
        tokens = pcp.tokenize("git push --no-dry-run origin main")
        _, git_index = pcp.is_git_push(tokens)
        self.assertFalse(pcp.push_has_side_effect_excluded_flag(tokens, git_index))

    def test_unrelated_flag_is_not_excluded(self) -> None:
        tokens = pcp.tokenize("git push --force origin main")
        _, git_index = pcp.is_git_push(tokens)
        self.assertFalse(pcp.push_has_side_effect_excluded_flag(tokens, git_index))


class MainEntrypointOptoutBoundaryTests(unittest.TestCase):
    """CLI entrypoint（`_main`）の opt-out 境界を固定する（tasklist T-4 Step 3、A-11 の反映）。

    impl-gate advisory A-11: T-4 計画の `_main` draft は
    `find_optout(tokens, original_token_count=len(tokens))` を呼んでおり、
    `len(tokens)` は nested shell 展開 **後** の長さになるため、展開由来 token の
    `git_index` は常にこの境界未満になってしまい design.md § opt-out 受理面の
    機械定義 item 4（`bash -c`/`eval` 由来 token は受理しない）が CLI 経由では
    機能しなくなる（fail-open）。境界値は `tokenize_with_boundary` の第 2 戻り値
    （展開 **前** の原文 token 数）から取らなければならない。`find_optout` 自体の
    単体契約は T-2 で確定済みのため、ここでは CLI 配線（`_main`）が正しい境界を
    渡していることだけを固定する。
    """

    _SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "push_command_parse.py"

    def _run_cli(self, command: str) -> dict:
        payload = json.dumps(
            {"command": command, "payload_cwd": "", "process_cwd": "/tmp"}
        )
        completed = subprocess.run(
            [sys.executable, str(self._SCRIPT)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=PRE_PUSH_HANG_GUARD,
        )
        self.assertEqual(
            completed.returncode, 0, msg=f"stderr={completed.stderr!r}"
        )
        return json.loads(completed.stdout)

    def test_bash_c_optout_rejected_via_cli(self) -> None:
        # design.md 111-122 行の明示例: 展開由来なので拒否されなければならない。
        # ただしこの形は**境界判定に到達する前**にコマンド先頭判定で落ちる
        # （展開由来の代入 token の直前が quoted command string token になるため）。
        # 境界そのものの判別は test_expanded_optout_after_inner_separator_* が担う
        result = self._run_cli("bash -c 'GDD_SKIP_PRE_PUSH_GATE=1 git push'")
        self.assertFalse(result["optout"]["accepted"])

    def test_expanded_optout_after_inner_separator_rejected_via_cli(self) -> None:
        """境界値を `len(tokens)` に取り違えたときだけ受理される形を固定する。

        nested command string の**内側に区切り token がある**と、展開由来の代入列は
        「区切り直後 = コマンド先頭」を満たしてしまう。したがって最後の砦は
        `find_optout` の `original_token_count`（展開**前**の原文 token 数）だけになる。
        `len(tokens)`（展開**後**の長さ）を渡すと展開由来 `git_index` が常に境界未満に
        なり、以下はいずれも `accepted: true / via: command-prefix` に転ぶ（fail-open）。
        """
        for command in (
            "bash -c 'true; GDD_SKIP_PRE_PUSH_GATE=1 git push'",
            "bash -c 'cd /repo/a && GDD_SKIP_PRE_PUSH_GATE=1 git push origin main'",
            "eval 'true; GDD_SKIP_PRE_PUSH_GATE=1 git push'",
        ):
            with self.subTest(command=command):
                result = self._run_cli(command)
                self.assertTrue(result["is_push"])
                self.assertFalse(result["optout"]["accepted"])
                self.assertIsNone(result["optout"]["via"])

    def test_plain_prefix_optout_accepted_via_cli(self) -> None:
        # 正の対照ケース: 修正が正常系（境界内の prefix）を壊していないことを確認
        result = self._run_cli("GDD_SKIP_PRE_PUSH_GATE=1 git push origin main")
        self.assertTrue(result["optout"]["accepted"])
        self.assertEqual(result["optout"]["via"], "command-prefix")


if __name__ == "__main__":
    unittest.main()

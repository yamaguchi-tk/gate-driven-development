"""merge gate hook の shell 引数解析 / 独立レビュー severity / steering 解決の回帰群。

`gate #14`/`#15`/`#16` で見つかった fail-open（リダイレクト位置引数誤読・
入れ子 shell 越しの実行未検出・severity 判定の変異生存・done steering 複数件時の
正本決定漏れ）を、実 hook subprocess 経由で固定する。`test_merge_gate_hook_gate_activation.py`
（正規経路の活性化）とは対象が「壊れやすい境界条件の回帰」である点で異なるため
別ファイルへ分けた（`tests/test_merge_gate_hook.py` 分割）。
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _merge_gate_input_classes import once_per_input_class
from _merge_gate_support import (
    _approval_line,
    _head_sha,
    _init_repo,
    _init_repo_with_commit_date,
    _run_hook,
    _valid_evidence_lines,
    _write_evidence_state,
    _write_state,
    _write_two_done_steerings,
)


class RedirectionAndNestedShellHookRegressionTests(unittest.TestCase):
    """gate #14 M-1 / M-3 を hook 実起動で固定する。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)
        # どのテストも state を書くのは最初の起動の前の 1 回だけなので、hook に同じ入力が渡る行は 1 回だけ起動する
        self._hook = once_per_input_class(
            lambda payload: _run_hook(payload, self.repo, self.home), self.repo)

    def _run(self, command):
        return self._hook({"tool_input": {"command": command}})

    def test_redirections_do_not_cause_a_false_block(self):
        # M-1: 全証跡が valid なら、リダイレクトが付いても allow のまま。
        # `pr-target-unresolvable` は policy code なので kill-switch の出口を
        # 案内せず、誤って不足として通知すると案内どおりでは抜けられない恒久ループになる。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        for command in (
            "gh pr merge 7 </dev/null",
            "gh pr merge 7 > /tmp/gdd-merge-gate-test.log",
            "gh pr merge 7 2>&1",
            "gh pr merge 7 | tee /dev/null",
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_nested_shell_invocation_still_reaches_the_gate(self):
        # M-3: `bash -c` / `eval` は agent が普通に使う idiom。証跡が無ければ不足として通知する。
        _write_state(self.repo, active=True, extra_lines=[])
        for command in (
            "bash -c 'gh pr merge 7'",
            'sh -c "gh pr merge 7"',
            "eval 'gh pr merge 7'",
            "$(echo gh) pr merge 7",
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout, f"{command} が素通りした")
                self.assertIn("approval-missing", result.stdout)

    def test_prose_mentioning_the_command_is_not_blocked(self):
        # 過検出の否定側（本 PR 自身の commit / CHANGELOG 更新を通知しない）。
        _write_state(self.repo, active=True, extra_lines=[])
        result = self._run('git commit -m "gh pr merge の block 条件を追加"')
        self.assertNotIn('"hookEventName"', result.stdout)

    # --- gate #15 H-1: 演算子を挟んでも対象 PR を取り違えない（hook 実起動） -----
    #
    # 旧実装は最初の演算子で走査を打ち切り、後続の位置引数が見えないまま
    # 「引数省略形」と誤認していた。hook は引数省略形を `state.md` の PR を
    # 対象とみなすため、**別 PR / ブランチ名指定のマージが、記録済みの別 PR 向け
    # 承認で allow** された。全証跡 valid（PR #7 向け）の repo で実測する。
    def test_operator_forms_do_not_inherit_another_prs_approval(self):
        _write_state(self.repo, active=True, extra_lines=_valid_evidence_lines(self.head))
        for command, code in (
            ("gh pr merge </dev/null other-branch", "pr-target-unresolvable"),
            ("gh pr merge 2>&1 999", "approval-pr-mismatch"),
            ("gh pr merge >/tmp/gdd-merge-gate-test.log 999", "approval-pr-mismatch"),
            ("gh pr merge 7 && gh pr merge 999", "pr-target-unresolvable"),
            ("gh pr merge 7; gh pr merge other-branch", "pr-target-unresolvable"),
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout, f"{command} が素通りした")
                self.assertIn(code, result.stdout)

    def test_operator_forms_match_the_plain_form_verdict(self):
        # `active: false`（merge 時の既定状態）でも、演算子の有無で判定が変わらない
        # ことを等価性で固定する（design 5c の「別 PR 指定は素通り」境界を含む）。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        for command, baseline in (
            ("gh pr merge 2>&1 999", "gh pr merge 999"),
            ("gh pr merge >/tmp/gdd-merge-gate-test.log 999", "gh pr merge 999"),
            ("gh pr merge </dev/null other-branch", "gh pr merge other-branch"),
        ):
            with self.subTest(command=command):
                self.assertEqual(self._run(command).stdout, self._run(baseline).stdout)

    def test_chained_merges_block_even_with_an_inactive_marker(self):
        # 1 本目が承認済みでも、2 本目（未承認の PR）を道連れに allow しない。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        for command in (
            "gh pr merge 7 && gh pr merge 999",
            "gh pr merge 7; gh pr merge other-branch",
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn("pr-target-unresolvable", result.stdout, f"{command} が素通りした")

    def test_single_merge_with_operators_still_allows(self):
        # 過検出の否定側: merge が 1 本なら連結・リダイレクトが付いても allow。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        for command in (
            "git fetch --all && gh pr merge 7",
            "gh pr merge 7 && echo merged",
            "gh pr merge 2>&1 7",
        ):
            with self.subTest(command=command):
                self.assertNotIn('"hookEventName": "PreToolUse"', self._run(command).stdout)

    # --- gate #16 M-A: interpreter へ食わせる heredoc 本文は「データ」ではない ---
    #
    # heredoc 本文の除去は pre-PR gate から引き継いだ過検出緩和（`git commit -F -
    # <<MSG … MSG` の散文を誤って通知しない）だが、heredoc は **コマンドを実行する
    # 経路でもある**。introducer 行が shell interpreter なら本文はそのまま実行される
    # ので、緩和したままだと `bash <<EOF … gh pr merge … EOF` が gate を丸ごと素通り
    # する。実行形（interpreter への入力）とデータ形を introducer 行で分ける。
    def test_interpreter_heredoc_body_still_reaches_the_gate(self):
        _write_state(self.repo, active=True, extra_lines=[])
        for command in (
            "bash <<'EOF'\ngh pr merge 7 --squash\nEOF",
            "bash -s <<EOF\ngh pr merge 7 --squash\nEOF",
            "sh <<'SH'\ngh pr merge 7\nSH",
            "bash <<-EOF\ngh pr merge 7\nEOF",
            # pipeline 内の interpreter（`<<` の所有コマンドは cat だが、本文は
            # そのまま bash へ流れる）。所有 pipeline 単位の判定でも落とさない。
            "cat <<'EOF' | bash\ngh pr merge 7\nEOF",
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout, f"{command} が素通りした")
                self.assertIn("approval-missing", result.stdout)

    def test_data_heredoc_body_is_still_relaxed(self):
        # 過検出の否定側（pre-PR gate 由来の緩和を維持する）: interpreter でない
        # コマンドへ **データとして** 渡す heredoc 本文は command word ではない。
        #
        # gate #17 M-1: 判定範囲が「行全体」だと、制御演算子で区切られた **別
        # コマンド** の interpreter が後続のデータ heredoc を実行形へ格上げし、
        # この repo の日常操作（`bash tests/validate-plugin.sh && git commit -m
        # "$(cat <<'EOF' … )"`）が `pr-target-unresolvable` として通知された。
        # 単独形だけを並べていると、この回帰を素通りさせる。
        _write_state(self.repo, active=True, extra_lines=[])
        for command in (
            "git commit -F - <<MSG\ngh pr merge の block 条件を追加\nMSG",
            "cat <<'EOF' > /tmp/gdd-merge-gate-test.md\ngh pr merge 7 を説明する行\nEOF",
            # 別 segment の interpreter（`&&` の左辺）に引きずられない。
            "bash tests/validate-plugin.sh && git commit -m \"$(cat <<'EOF'\n"
            "fix(gdd): merge gate の gh pr merge 検出漏れを修正\nEOF\n)\"",
            "git add -A && bash tests/validate-plugin.sh"
            " && git commit -F - <<MSG\ngh pr merge を修正\nMSG",
            # interpreter の **クォートされた引数の中** で開く heredoc。所有者は
            # 入れ子 script 側の `git commit` であって、外側の bash ではない。
            "bash -lc 'git commit -F - <<MSG\nfix: gh pr merge を修正\nMSG'",
        ):
            with self.subTest(command=command):
                self.assertNotIn('"hookEventName"', self._run(command).stdout)

    # --- gate #15 M-3: interpreter のフラグ列越しでも gate に到達する ------------
    def test_nested_shell_flag_forms_still_reach_the_gate(self):
        _write_state(self.repo, active=True, extra_lines=[])
        for command in (
            "bash --norc -c 'gh pr merge 7'",
            "bash -euo pipefail -c 'gh pr merge 7'",
            "bash --noprofile --norc -c 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout, f"{command} が素通りした")
                self.assertIn("approval-missing", result.stdout)

ACME_7 = "https://github.com/acme/widgets/pull/7"
# state.md に書かれうる、正準形でない PR URL（番号の形の merge は、どれも照合して不足として通知する）
NON_CANONICAL_PR_URLS = {
    "angle": "<{url}>",
    "pipe_note": "{url} | updated_by: main-session",
    "md_link": "[#7]({url})",
    "files_suffix": "{url}/files",
    "zero_pad": "{url_zero_pad}",
}


def _non_canonical(form: str, url: str = ACME_7) -> str:
    return NON_CANONICAL_PR_URLS[form].format(url=url, url_zero_pad=url.replace("/pull/7", "/pull/007"))


class NonCanonicalPrUrlTargetTests(unittest.TestCase):
    """対象 PR の照合: URL と番号が両方見える merge と、正準形でない PR URL の別 repo の同じ番号。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)

    def _run(self, command):
        return _run_hook({"tool_input": {"command": command}}, self.repo, self.home)

    def test_number_is_still_matched_when_a_url_is_also_given(self):
        """不足を通知すべき入力: URL と番号の両方が位置引数に見える merge（`<URL#8> 7`）は、対象を決められないので不足として通知する。"""
        _write_state(self.repo, active=False)
        result = self._run("gh pr merge https://github.com/acme/widgets/pull/8 7")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_other_repo_with_the_same_number_is_stopped_like_the_number_form(self):
        """受理集合の対称性: 別の repo の同じ番号は、URL の形でも番号の形（`-R`）と同じく不足として通知する。"""
        _write_state(self.repo, active=False, pr_url=_non_canonical("angle", "https://github.com/other/thing/pull/7"))
        for command in (f"gh pr merge {ACME_7}", "gh pr merge -R acme/widgets 7"):
            with self.subTest(command=command):
                self.assertIn('"hookEventName": "PreToolUse"', self._run(command).stdout)
        shutil.rmtree(self.repo / ".steering")
        _write_state(self.repo, active=False, pr_url=_non_canonical("angle"))
        for command in ("gh pr merge https://github.com/other/thing/pull/7", "gh pr merge -R other/thing 7"):
            with self.subTest(command=command):
                self.assertIn('"hookEventName": "PreToolUse"', self._run(command).stdout)

class IndependentReviewSeverityRegressionTests(unittest.TestCase):
    """gate #14 M-2: AC-4 の severity 判定に回帰テストを持たせる。

    `high != 0 || medium != 0` のどちらの項を削っても既存 suite は全緑のままだった
    （変異が 2 種とも SURVIVED）。high / medium それぞれの単独発火と、両方 0 の
    通過扱い（常に通知する変異の kill）を実挙動で固定する。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        # 待機 40 分の経過を作るため HEAD の committer date を 45 分前に置く
        # （`Last Review Push At.at >= HEAD committer date` の制約を満たすため）。
        old45 = (datetime.now(timezone.utc) - timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.repo = _init_repo_with_commit_date(self.tmp, old45)
        self.head = _head_sha(self.repo)
        self.old41 = (datetime.now(timezone.utc) - timedelta(minutes=41)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    def _run(self, high, medium):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _write_evidence_state(self.repo, [
            _approval_line(7, self.head),
            f"- Pre-Merge Review Recheck: {self.head} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head} | at: {self.old41}",
            f"- Bot Review Received: {self.head} | received: no | at: {self.old41}",
            f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer"
            f" | context: diff-only | high: {high} | medium: {medium} | at: {self.old41}",
        ])
        return _run_hook({"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home)

    def test_high_findings_block(self):
        result = self._run(high=2, medium=0)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("independent-review-missing", result.stdout)
        self.assertIn("high 2 件", result.stdout)

    def test_medium_findings_without_disposition_block_with_new_reason_code(self):
        # medium 単独（blocking 0）は independent-review-missing ではなく
        # medium-disposition-missing として通知する（design.md § D5-2 の 4 行目）。
        result = self._run(high=0, medium=3)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("medium-disposition-missing", result.stdout)
        self.assertNotIn("independent-review-missing", result.stdout)

    def test_high_and_medium_both_zero_allows(self):
        # AC-4: Low のみ残存（= high/medium 0 件）は通知の理由にならない。
        result = self._run(high=0, medium=0)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

class SteeringResolutionRegressionTests(unittest.TestCase):
    """gate #14 M-4 / gate #15 M-1: AC-6 の 3 条件外で gate が消える経路の扱い。

    - done steering 2 件（`multiple`）: 正本 state.md が決まらない。gate #15 M-1
      以降は **gate 対象判定の後** に倒す（対象 PR を記録した steering が一意なら
      それを正本に採用。無ければ「PR URL 不一致」と同じ素通り面。`active: true`
      または候補 2 件以上 / 対象不明なら AC-10 に従い不足として通知）
    - `.claude/gdd-dev.local.md` 不在: GDD セッションマーカーそのものの不在
      → AC-6(a) の素通り面として **意図的に** allow（requirements / design に明記）
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)

    def _run(self, command="gh pr merge 7"):
        return _run_hook({"tool_input": {"command": command}}, self.repo, self.home)

    def test_two_done_steerings_block_when_the_session_is_active(self):
        # `active: true` は marker 単独で gate 対象。正本が決まらないので不足として通知する。
        _write_two_done_steerings(self.repo, active=True)
        result = self._run()
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("steering-ambiguous", result.stdout)
        self.assertIn("gdd-hooks-disabled", result.stdout)

    def test_two_done_steerings_do_not_leak_the_slug(self):
        slugs = _write_two_done_steerings(self.repo, active=True)
        result = self._run()
        for slug in slugs:
            self.assertNotIn(slug, result.stdout)

    def test_two_done_steerings_pass_through_under_kill_switch(self):
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        _write_two_done_steerings(self.repo, active=True)
        result = self._run()
        self.assertNotIn('"hookEventName"', result.stdout)

    # --- gate #15 M-1: `multiple` が gate 対象判定より前で全件を不足として通知していた回帰 ---

    def test_target_pr_selects_the_matching_steering_as_canonical(self):
        # 対象 PR (#1) を記録した steering がちょうど 1 件 → それを正本にして
        # 通常の証跡検査へ進む（`steering-ambiguous` にはしない）。
        _write_two_done_steerings(self.repo)
        result = self._run("gh pr merge 1")
        self.assertNotIn("steering-ambiguous", result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_unrelated_pr_number_passes_through(self):
        # 記録済みのどの PR とも一致しない → 単一 steering 時の「PR URL 不一致」
        # と同じ素通り面。ここを不足の通知にすると done steering 2 件の checkout の
        # **全マージ**で通知が出て、復旧が kill-switch か手動整理しか無くなる。
        _write_two_done_steerings(self.repo)
        result = self._run("gh pr merge 999")
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_unrelated_repo_pr_url_passes_through(self):
        # 別 repo の無関係な PR。GDD と無関係なマージまで巻き込まない。
        _write_two_done_steerings(self.repo)
        result = self._run("gh pr merge https://github.com/other/thing/pull/999")
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_omitted_args_still_block_when_target_is_unknown(self):
        # 対象を決める材料がコマンドにも steering にも無い → AC-10 で fail-closed。
        _write_two_done_steerings(self.repo)
        result = self._run("gh pr merge")
        self.assertIn("steering-ambiguous", result.stdout)

    def test_same_pr_recorded_twice_still_blocks(self):
        # 同じ PR を 2 件の steering が記録 → 一意に選べないので不足として通知する。
        _write_two_done_steerings(self.repo)
        second = self.repo / ".steering" / "20260102-followup" / "state.md"
        second.write_text(
            "## Gate Status\n- Resume From: done\n- Next Action: done\n"
            "- PR URL: https://github.com/acme/widgets/pull/1\n"
        )
        result = self._run("gh pr merge 1")
        self.assertIn("steering-ambiguous", result.stdout)

    def test_single_done_steering_still_resolves(self):
        # 統制群: 1 件なら従来どおり解決して証跡検査へ進む。
        _write_state(self.repo, active=False, extra_lines=[])
        result = self._run()
        self.assertIn("approval-missing", result.stdout)

    # --- gate #16 H-A: `multiple` × `PR URL` 未記録が素通りへ潰れていた回帰 -----
    #
    # `_mg_match_steering_by_target` は `PR URL` を持たない候補を **黙って** 落として
    # いたため、`_MG_MATCH_STATUS=none` が「対象は別 PR（素通り面）」と「判定材料が
    # 無い（AC-10 の不足を通知する面）」の両方に潰れていた。単一 steering 経路は同じ状況を
    # `pr-url-unrecorded` で不足として通知しているので、**steering 件数だけで fail-closed が
    # 反転**していた。3 条件（done 2 件 / URL 記録し忘れ / `active: false`）はいずれも
    # 既定状態で、攻撃者入力ではなく記録し忘れで成立する。

    UNRECORDED = ("20260102-followup",)

    def test_unrecorded_pr_url_among_multiple_steerings_blocks(self):
        _write_two_done_steerings(self.repo, unrecorded=self.UNRECORDED)
        for command in (
            "gh pr merge 23",
            "gh pr merge https://github.com/acme/widgets/pull/23",
            "gh pr merge --admin 23",
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout, f"{command} が素通りした")
                self.assertIn("pr-url-unrecorded", result.stdout)
                self.assertIn("不足 key: PR URL", result.stdout)
                self.assertIn("gdd-hooks-disabled", result.stdout)

    def test_omitted_args_with_an_unrecorded_url_still_blocks(self):
        # 対象を決める材料がコマンド側にも無い形は従来どおり `steering-ambiguous`
        # （「対象を明示するか steering を 1 件に整理」が正しい次の 1 アクション）。
        # どちらの code でも fail-closed であることは変わらない。
        _write_two_done_steerings(self.repo, unrecorded=self.UNRECORDED)
        result = self._run("gh pr merge")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("steering-ambiguous", result.stdout)

    def test_unrecorded_pr_url_verdict_matches_the_single_steering_path(self):
        # fail-closed の等価性: 同一証跡欠落なら steering 件数で判定を変えない。
        _write_two_done_steerings(self.repo, unrecorded=self.UNRECORDED)
        multiple = self._run("gh pr merge 23")
        shutil.rmtree(self.repo / ".steering")
        _write_state(self.repo, active=False, pr_url=None)
        single = self._run("gh pr merge 23")
        self.assertIn("pr-url-unrecorded", single.stdout)
        self.assertIn("pr-url-unrecorded", multiple.stdout)

    def test_unrecorded_pr_url_does_not_leak_the_slug(self):
        slugs = _write_two_done_steerings(self.repo, unrecorded=self.UNRECORDED)
        result = self._run("gh pr merge 23")
        for slug in slugs:
            self.assertNotIn(slug, result.stdout)

    def test_unrecorded_pr_url_passes_through_under_kill_switch(self):
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        _write_two_done_steerings(self.repo, unrecorded=self.UNRECORDED)
        result = self._run("gh pr merge 23")
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_matching_steering_still_wins_over_an_unrecorded_sibling(self):
        # 過検出の否定側: 対象 PR (#1) を記録した steering が一意に決まるなら、
        # 隣に URL 未記録の steering があっても従来どおりそれを正本にする。
        _write_two_done_steerings(self.repo, unrecorded=self.UNRECORDED)
        result = self._run("gh pr merge 1")
        self.assertNotIn("pr-url-unrecorded", result.stdout)
        self.assertNotIn("steering-ambiguous", result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_all_urls_recorded_still_passes_through(self):
        # 素通り面は「全候補が URL 記録済みで、どれとも一致しない」ときだけ残す。
        _write_two_done_steerings(self.repo)
        result = self._run("gh pr merge 999")
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_missing_local_state_marker_passes_through(self):
        # AC-6(a) の素通り面（gate #14 M-4 で「明記して閉じる」と判断した側）。
        # `.steering/` に PR URL があってもマーカーが無ければ非 GDD セッション。
        # 判断根拠: マーカーを通知の条件にすると steering を持ち込んだだけの repo の
        # 正当な merge を全件不足として通知し、requirements § リスクの誤爆による迂回を招く。
        steering = self.repo / ".steering" / "20260101-demo"
        steering.mkdir(parents=True, exist_ok=True)
        (steering / "state.md").write_text(
            "## Gate Status\n- Resume From: done\n- Next Action: done\n"
            "- PR URL: https://github.com/acme/widgets/pull/7\n"
        )
        self.assertFalse((self.repo / ".claude" / "gdd-dev.local.md").exists())
        result = self._run()
        self.assertNotIn('"hookEventName"', result.stdout)

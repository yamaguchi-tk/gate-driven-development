"""merge gate hook プロセス起動 / 対象 PR 解決 / gate 活性化の契約テスト。

`run-merge-gate-hook.sh` を実 subprocess として起動し、kill-switch・
GDD セッションマーカー不在・対象 PR の 3 組解決・`active:`/`branch` 引数の
組み合わせで gate が正しく活性化する（＝評価対象になる）ことを検査する。
証跡（Merge Approval 以降のフィールド）そのものの通過 / 不足の通知の判定は
`test_merge_gate_hook_evidence_gate.py` 側が持つ（`tests/test_merge_gate_hook.py`
分割）。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    _head_sha,
    _init_bare_repo,
    _init_named_repo,
    _init_repo,
    _new_full_evidence_repo,
    _new_marker_only_repo,
    _new_repo_with_marker_and_pr,
    _run_hook,
    _valid_evidence_lines,
    _write_marker_only,
    _write_state,
    _write_two_done_steerings,
)


class HookProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)

    def test_non_merge_command_passes_through(self):
        payload = {"tool_input": {"command": "ls -la"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_kill_switch_bypasses_and_logs(self):
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        _write_marker_only(self.repo, active=True, session_id="test-session")
        payload = {"tool_input": {"command": "gh pr merge 1"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)
        log = self.home / ".claude" / ".gdd-hook-state" / "merge-gate-suppressed.log"
        self.assertTrue(log.exists())
        self.assertIn("kill-switch-bypass", log.read_text())

    def test_kill_switch_bypasses_when_root_unresolvable(self):
        # A-3 (Task A advisory / gate #12): kill-switch は実装上 git root の
        # 確定より前に評価される（design.md § 主要フロー step 4。root を解決
        # できない非 git ディレクトリでも kill-switch が効くようにするための
        # 意図的な順序）。この順序を root 解決 -> kill-switch へ戻すと、
        # 非 git ディレクトリでは repo-root-unresolvable で不足として通知されてしまい
        # 本テストは red になる。
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        non_repo = self.tmp / "not-a-repo"
        non_repo.mkdir()
        payload = {"tool_input": {"command": "gh pr merge 1"}}
        result = _run_hook(payload, non_repo, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    # --- gate #13 F-B1 回帰: suppression ログに絶対パスを残さない -------------
    #
    # `_mg_log_suppressed` は当初 `root: <絶対パス>` を平文で追記していた。
    # references/self-review-lanes.md § merge gate 証跡 / design.md § hook 所有ログ /
    # adr.md の秘匿契約はいずれも「repo 識別子は絶対パス全体の sha1 先頭 8 桁。
    # 絶対パス・repo 名・worktree slug は残さない」を要求する。同居する
    # `pre-push-optout.log`（`gdd_sr_log_event`）の hash + `chmod 600` と同水準に
    # そろっていることを、到達経路 2 本ともで実測して固定する。
    SUPPRESSION_LOG_REL = (".claude", ".gdd-hook-state", "merge-gate-suppressed.log")

    def _assert_suppression_log_is_private(self, event):
        log = self.home.joinpath(*self.SUPPRESSION_LOG_REL)
        self.assertTrue(log.exists(), f"{event} で suppression ログが作られること")
        text = log.read_text()
        self.assertIn(event, text)

        # 1. 絶対パスの痕跡が 1 文字も残らない（logical / physical 双方で確認）。
        for path in {str(self.repo), os.path.realpath(self.repo),
                     str(self.tmp), os.path.realpath(self.tmp)}:
            self.assertNotIn(path, text, f"絶対パス {path} がログに残っている")
        self.assertNotIn("/", text, "path separator がログに残っている（= 非可逆化されていない）")
        self.assertNotIn(self.tmp.name, text, "tmp ディレクトリ名がログに残っている")

        # 2. repo 識別子は sha1 先頭 8 桁の形（`gdd_sr_log_event` と同形の key 名）。
        for line in text.splitlines():
            self.assertRegex(
                line,
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \| event: [a-z-]+ \| repo: [0-9a-f]{8}$",
            )

        # 3. `pre-push-optout.log` と同じ 0600。
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)

    def test_kill_switch_suppression_log_hides_absolute_path(self):
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        _write_marker_only(self.repo, active=True, session_id="test-session")
        result = _run_hook({"tool_input": {"command": "gh pr merge 1"}}, self.repo, self.home)
        self.assertEqual(result.returncode, 0)
        self._assert_suppression_log_is_private("kill-switch-bypass")

    def test_unresolved_steering_suppression_log_hides_absolute_path(self):
        # kill-switch なし・steering 未解決（`.steering/` を作らない）の到達経路。
        # ここでの PROJECT_ROOT は git rev-parse --show-toplevel 済みの絶対パス。
        _write_marker_only(self.repo, active=True, session_id="test-session")
        result = _run_hook({"tool_input": {"command": "gh pr merge 1"}}, self.repo, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)
        self._assert_suppression_log_is_private("unresolved-steering-on-merge")

    def test_non_gdd_session_passes_through(self):
        payload = {"tool_input": {"command": "gh pr merge 1"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_unowned_marker_with_no_steering_passes_through(self):
        # AC-1: 別セッションが残した active marker（C-1）+ `.steering/` に
        # done/blocked 候補が 1 件も無い repo は不足として通知されない。経路 A が
        # 降格し、steering 未解決の既存素通り面へ合流する。実 incident と同型
        # （`active: true` + 別 session_id + task steering 無し）。
        _write_marker_only(self.repo, active=True, session_id="other-session")
        payload = {"tool_input": {"command": "gh pr merge 1"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)
        self.assertNotIn("session-mismatch", result.stdout)
        log = self.home / ".claude" / ".gdd-hook-state" / "merge-gate-suppressed.log"
        lines = log.read_text().splitlines()
        self.assertEqual(
            len(lines), 2,
            f"降格 1 行 + unresolved-steering-on-merge 1 行のちょうど 2 行のはず: {lines}",
        )
        self.assertIn("unowned-active-marker-demoted", lines[0])
        self.assertIn("unresolved-steering-on-merge", lines[1])
        self._assert_suppression_log_is_private("unowned-active-marker-demoted")

    def test_unowned_marker_with_recorded_pr_reaches_evidence_gate(self):
        # AC-2: 別セッション marker + 対象 PR URL を記録した steering がある
        # 場合は証跡検査へ進む。承認証跡が無ければ approval-missing として通知し、
        # session-mismatch では通知しない（経路 B の検査撤去の直接確認）。
        _write_state(self.repo, active=True, session_id="other-session")
        payload = {"tool_input": {"command": "gh pr merge 7"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)
        self.assertNotIn("session-mismatch", result.stdout)

class TargetResolutionRegressionTests(unittest.TestCase):
    """F-1: 対象 PR の 3 組解決が repo 決定要因を実際に消費すること。

    統制群（同一 repo・同一番号）は allow のまま、repo を差し替える 7 形が
    すべて `pr-target-unresolvable` として通知することを実挙動で確認する。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin",
             "https://github.com/acme/widgets.git"], check=True,
        )
        _write_state(self.repo, active=True, extra_lines=_valid_evidence_lines(self.head))

    def _run(self, command, extra_env=None):
        return _run_hook(
            {"tool_input": {"command": command}}, self.repo, self.home, extra_env=extra_env,
        )

    def test_control_same_repo_number_allows(self):
        result = self._run("gh pr merge 7")
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_repo_decision_inputs_block_when_they_point_elsewhere(self):
        cases = [
            ("gh pr merge -R org/otherrepo 7", None),
            ("gh --repo org/otherrepo pr merge 7", None),
            ("gh pr merge --repo=org/otherrepo 7", None),
            ("gh pr merge https://github.com/evil/other/pull/7", None),
            ("gh pr merge my-feature-branch", None),
            ("GH_REPO=org/otherrepo gh pr merge 7", None),
            ("gh pr merge 7", {"GH_REPO": "org/otherrepo"}),
            ("gh pr merge 7", {"GH_HOST": "ghe.example.com"}),
        ]
        for command, env in cases:
            with self.subTest(command=command, env=env):
                result = self._run(command, extra_env=env)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_gh_repo_set_default_pointing_elsewhere_blocks(self):
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "remote.origin.gh-resolved",
             "other/repo"], check=True,
        )
        result = self._run("gh pr merge 7")
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_gh_repo_set_default_base_marker_still_allows(self):
        # `gh repo set-default` が origin 自身を既定にした場合の値（誤爆させない）。
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "remote.origin.gh-resolved",
             "base"], check=True,
        )
        result = self._run("gh pr merge 7")
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_matching_repo_flag_still_allows(self):
        result = self._run("gh pr merge -R acme/widgets 7")
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

class GateActivationRegressionTests(unittest.TestCase):
    """F-2: 引数省略 `gh pr merge` × `active: false` で gate が発火すること。

    design 5c が「AC-2 が不足として通知したい #1032 の主経路」と名指しした最頻形 × 最頻状態。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)

    def _run(self, command):
        return _run_hook({"tool_input": {"command": command}}, self.repo, self.home)

    def test_omitted_args_with_inactive_marker_blocks(self):
        _write_state(self.repo, active=False, extra_lines=[])
        result = self._run("gh pr merge")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_number_arg_with_inactive_marker_blocks(self):
        # 統制群（gate #11 時点でも不足として通知していた形）。
        _write_state(self.repo, active=False, extra_lines=[])
        result = self._run("gh pr merge 7")
        self.assertIn("approval-missing", result.stdout)

    def test_omitted_args_with_active_marker_blocks(self):
        _write_state(self.repo, active=True, extra_lines=[])
        result = self._run("gh pr merge")
        self.assertIn("approval-missing", result.stdout)

    def test_omitted_args_with_full_evidence_allows(self):
        # 発火させた結果として過剰な通知になっていないこと（肯定側）。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        result = self._run("gh pr merge")
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_unrelated_pr_number_with_inactive_marker_passes_through(self):
        # design 5c の境界は維持する: 非 active かつ steering の PR でもない対象は
        # gate 対象にしない（引数省略だけが「state.md の PR を対象」に化ける）。
        _write_state(self.repo, active=False, extra_lines=[])
        result = self._run("gh pr merge 999")
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_missing_pr_url_with_inactive_marker_blocks(self):
        # RF-1 / AC-10: `active: false`（`done` 後の最頻状態）で `PR URL` が
        # **未記録**の経路は、AC-6 の 3 条件（steering 不在 / kill-switch / 非該当
        # コマンド）のいずれでもない。gate 対象外ではなく「判定材料が欠けている」
        # 状態なので不足の通知に倒す。block reason は不足材料と回復手段を両方出す。
        _write_state(self.repo, active=False, pr_url=None)
        result = self._run("gh pr merge 7")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-url-unrecorded", result.stdout)
        self.assertIn("不足 key: PR URL", result.stdout)
        self.assertIn("使わないステアリングの終え方", result.stdout)
        self.assertIn("<steering-dir>/state.md", result.stdout)
        self.assertIn("gdd-hooks-disabled", result.stdout)

    def test_missing_pr_url_with_omitted_args_blocks(self):
        _write_state(self.repo, active=False, pr_url=None)
        result = self._run("gh pr merge")
        self.assertIn("pr-url-unrecorded", result.stdout)

    def test_missing_pr_url_passes_through_under_kill_switch(self):
        # 誤爆（stale な `.steering/` が残る repo の正当な merge）の逃がし口は
        # 既存 kill-switch 1 本に閉じる（current task 判定などの分岐は足さない）。
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        _write_state(self.repo, active=False, pr_url=None)
        result = self._run("gh pr merge 7")
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_match_head_commit_flag_value_is_not_read_as_a_target(self):
        # RF-3: `--match-head-commit <sha>` は正当な merge オプション。値の消費が
        # 壊れると sha が位置引数（ブランチ名）として読まれ `unresolvable=true`
        # → `pr-target-unresolvable` の過剰な通知になる。正常系を 1 本固定する。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        result = self._run(f"gh pr merge 7 --match-head-commit {self.head}")
        self.assertNotIn('"hookEventName"', result.stdout)

class BranchArgumentGateActivationRegressionTests(unittest.TestCase):
    """gate #14 H-1: 位置引数がブランチ名でも gate 対象から落ちないこと。

    `gh pr merge [<number> | <url> | <branch>]` はブランチ名が一級の呼び出し形。
    旧実装は `unresolvable == true` を gate 対象判定から除外していたため、
    `active: false`（merge 時の既定状態）と組むと AC-1 / AC-2 / AC-3 が
    **単一入力**で同時に迂回された（証跡ゼロでも allow）。
    """

    BRANCH = "my-feature-branch"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin",
             "https://github.com/acme/widgets.git"], check=True,
        )

    def _run(self, command):
        return _run_hook({"tool_input": {"command": command}}, self.repo, self.home)

    def _commands(self):
        return (
            f"gh pr merge {self.BRANCH}",
            f"gh pr merge --admin {self.BRANCH}",
            f"gh pr merge -R acme/widgets {self.BRANCH}",
            f"bash -c 'gh pr merge {self.BRANCH}'",
        )

    def test_branch_arg_with_inactive_marker_blocks(self):
        # 証跡は**全部揃っている**状態で流す。gate が発火していれば
        # 「対象を決められない」ことだけが理由で不足の通知になる。素通りしたら
        # それは gate 対象判定から落ちた（= H-1 の fail-open）ということ。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        for command in self._commands():
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_branch_arg_without_evidence_blocks_with_active_marker(self):
        # 統制群: `active: true` 側の挙動は本 remediation で変えない。
        _write_state(self.repo, active=True, extra_lines=[])
        result = self._run(f"gh pr merge {self.BRANCH}")
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_branch_name_never_appears_in_the_block_reason(self):
        # design.md § Sensitive Data / Masking Policy: ブランチ名は禁止 token。
        _write_state(self.repo, active=False, extra_lines=_valid_evidence_lines(self.head))
        result = self._run(f"gh pr merge {self.BRANCH}")
        self.assertNotIn(self.BRANCH, result.stdout)

    def test_branch_arg_passes_through_under_kill_switch(self):
        (self.home / ".claude" / "gdd-hooks-disabled").touch()
        _write_state(self.repo, active=False, extra_lines=[])
        result = self._run(f"gh pr merge {self.BRANCH}")
        self.assertNotIn('"hookEventName"', result.stdout)


class DemotionEquivalenceTests(unittest.TestCase):
    """AC-6a/AC-6b/AC-6c: 降格後の判定が 3 marker 状態（C-1 / C-2 / active:false）で
    一致し、marker 不在の通過集合を超えないことを絶対期待値で固定する
    （design.md § 判定表。ADR-3: 同値ではなく絶対値の pin で経路 B 消し忘れを検出する）。
    """

    MARKERS = (
        ("C-1", True, "other-session-uuid"),
        ("C-2", True, None),
        ("active:false", False, "other-session-uuid"),
    )

    def _new_fixtures(self):
        tmp = Path(tempfile.mkdtemp())
        home = tmp / "home"
        (home / ".claude").mkdir(parents=True)
        repo = _init_repo(tmp)
        return repo, home

    def test_no_steering_candidates_passes_through(self):
        # 判定表 (i)
        for label, active, session_id in self.MARKERS:
            with self.subTest(marker=label):
                repo, home = self._new_fixtures()
                _write_marker_only(repo, active=active, session_id=session_id)
                result = _run_hook({"tool_input": {"command": "gh pr merge 1"}}, repo, home)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn('"hookEventName"', result.stdout)

    def test_single_steering_pr_url_unrecorded_blocks(self):
        # 判定表 (ii)
        for label, active, session_id in self.MARKERS:
            with self.subTest(marker=label):
                repo, home = self._new_fixtures()
                _write_state(repo, active=active, session_id=session_id, pr_url=None)
                result = _run_hook({"tool_input": {"command": "gh pr merge 7"}}, repo, home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-url-unrecorded", result.stdout)

    def test_single_steering_pr_url_matches_insufficient_evidence_blocks(self):
        # 判定表 (iii) = AC-2 の核心。経路 B 撤去の固定（絶対値 pin。ADR-3）。
        for label, active, session_id in self.MARKERS:
            with self.subTest(marker=label):
                repo, home = self._new_fixtures()
                _write_state(repo, active=active, session_id=session_id)
                result = _run_hook({"tool_input": {"command": "gh pr merge 7"}}, repo, home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("approval-missing", result.stdout)
                self.assertNotIn("session-mismatch", result.stdout)

    def test_single_steering_pr_url_points_elsewhere_passes_through(self):
        # 判定表 (iv)。PR 番号を明示的に渡す — 省略すると `:383-390` により
        # 無条件一致になり偽 GREEN になる（design.md 脚注）。保護面 1
        # （`:402` 経路）の縮小をここで固定する。
        for label, active, session_id in self.MARKERS:
            with self.subTest(marker=label):
                repo, home = self._new_fixtures()
                _write_state(repo, active=active, session_id=session_id)
                result = _run_hook({"tool_input": {"command": "gh pr merge 999"}}, repo, home)
                self.assertNotIn('"hookEventName"', result.stdout)

    def test_multiple_steering_no_target_match_passes_through(self):
        # 判定表 (v) = 保護面 2 の縮小（`:349` の multiple 経路。今日は
        # `active:true` marker で `steering-ambiguous` として通知していた入力が
        # 降格後は素通りになる。design.md AC-6c 面 2）。
        for label, active, session_id in self.MARKERS:
            with self.subTest(marker=label):
                repo, home = self._new_fixtures()
                _write_two_done_steerings(repo, active=active, session_id=session_id)
                result = _run_hook({"tool_input": {"command": "gh pr merge 999"}}, repo, home)
                self.assertNotIn('"hookEventName"', result.stdout)

    def test_multiple_steering_one_pr_url_unrecorded_blocks(self):
        # 判定表 (vi)
        for label, active, session_id in self.MARKERS:
            with self.subTest(marker=label):
                repo, home = self._new_fixtures()
                _write_two_done_steerings(
                    repo, active=active, session_id=session_id,
                    unrecorded=("20260102-followup",),
                )
                result = _run_hook({"tool_input": {"command": "gh pr merge 999"}}, repo, home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-url-unrecorded", result.stdout)

    def test_demoted_pass_through_set_is_subset_of_marker_absent(self):
        # AC-6b: 降格ケース（C-1/C-2）の通過集合が marker 不在（無条件 exit 0、
        # 全入力通過）の通過集合を超えない。(ii) は marker 不在なら素通り
        # だが、降格ケースでは不足の通知が残ることを直接示す（真部分集合の証拠）。
        for label, active, session_id in (
            ("C-1", True, "other-session-uuid"), ("C-2", True, None),
        ):
            with self.subTest(marker=label):
                repo, home = self._new_fixtures()
                _write_state(repo, active=active, session_id=session_id, pr_url=None)
                result = _run_hook({"tool_input": {"command": "gh pr merge 7"}}, repo, home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)


class SuppressionLogFailureContainmentTests(unittest.TestCase):
    """design.md § ログ呼び出しの failure containment / adr.md ADR-1:
    `_mg_log_suppressed` の依存コマンドが失敗しても、降格ケースは証跡検査へ
    到達し不足の通知を返す（hook が無出力で落ちない = 新しい fail-open にならない）。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)

    def test_shasum_failure_still_reaches_evidence_gate(self):
        _write_state(self.repo, active=True, session_id="other-session-uuid")
        shim_dir = self.tmp / "bin"
        shim_dir.mkdir()
        for name in ("shasum", "sha1sum"):
            shim = shim_dir / name
            shim.write_text("#!/bin/sh\nexit 1\n")
            shim.chmod(0o755)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            extra_env={"PATH": f"{shim_dir}:{os.environ['PATH']}"},
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_unset_home_still_reaches_evidence_gate(self):
        # `HOME` も `GDD_HOOK_STATE_DIR` も無い環境。`_mg_log_suppressed` の
        # `local _state_dir="${GDD_HOOK_STATE_DIR:-${HOME}/.claude/.gdd-hook-state}"`
        # が `set -u` で即死する経路で、`|| true` では捕まえられない
        # （bash は `||` の左辺の関数呼び出しの中では errexit を抑止するが、
        # `set -u` の未定義変数エラーは抑止しない）。この 1 面が subshell ガードの
        # 唯一の load-bearing な守備範囲であり、ここを固定しないと subshell を
        # 外す mutation が生き残る。
        _write_state(self.repo, active=True, session_id="other-session-uuid")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            drop_env=("HOME", "GDD_HOOK_STATE_DIR"),
        )
        self.assertEqual(
            result.returncode, 0,
            f"hook が非 0 で落ちている（無出力素通り）: stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)


class RootCandidateResolutionTests(unittest.TestCase):
    """AC-1/AC-2/AC-11/AC-12/AC-16/AC-17: root 候補ループ（3 段）の契約。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)

    # --- AC-1: 非 git cwd + `cd <repo>` で root を解決する -------------------
    def test_cd_target_resolves_root_from_non_git_cwd(self):
        repo = _new_repo_with_marker_and_pr(self.tmp, "target-repo")
        non_repo = self.tmp / "not-a-repo"
        non_repo.mkdir()
        for sep in ("&&", ";"):
            with self.subTest(sep=sep):
                command = f"cd {repo} {sep} gh pr merge 7"
                result = _run_hook({"tool_input": {"command": command}}, non_repo, self.home)
                self.assertNotIn("repo-root-unresolvable", result.stdout)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("approval-missing", result.stdout)

    def test_cd_target_followed_by_other_commands_still_resolves(self):
        # AC-5 の hook レベル確認。
        repo = _new_repo_with_marker_and_pr(self.tmp, "target-repo-2")
        non_repo = self.tmp / "not-a-repo-2"
        non_repo.mkdir()
        command = f"cd {repo} && git fetch && gh pr merge 7"
        result = _run_hook({"tool_input": {"command": command}}, non_repo, self.home)
        self.assertNotIn("repo-root-unresolvable", result.stdout)
        self.assertIn("approval-missing", result.stdout)

    # --- AC-2: 候補順（marker を持つ候補のうちプロセス cwd が最優先） ----------
    def test_process_cwd_with_marker_wins_over_untrusted_candidates(self):
        # impl-gate Round 2 IG-10: 旧 fixture は A / B / C の 3 repo すべてに同じ
        # PR（pull/7）の steering を置いていたため、root が A・B・C のどれに
        # 決まっても同じ approval-missing になり、候補順を判別できなかった
        # （候補順を反転させる mutation でも PASS した）。
        # 判別できる形: A（プロセス cwd）と untrusted 候補 1 つだけを置き、
        # どちらも marker + pull/7 の steering（承認なし）を持たせる。
        #   root = A（正しい候補順）: untrusted 候補の toplevel が root と異なる
        #     ので AC-18（marker 検査直後の toplevel 比較）が pr-target-unresolvable
        #     で即不足として通知し、steering 検査（approval-missing）には到達しない。
        #   root = untrusted 側（候補順が反転した mutation）: 実行先 == root で
        #     AC-18 は発火せず、その repo の steering が approval-missing を返す。
        # したがって「pr-target-unresolvable が出て approval-missing が出ない」を
        # 肯定 / 否定の両側で assert すると候補順の反転を検出できる。
        # 無出力 exit 0（marker 不在の素通り）とも区別できる（通知の出力を要求）。
        repo_a = _new_repo_with_marker_and_pr(self.tmp, "repo-a")
        repo_b = _new_repo_with_marker_and_pr(self.tmp, "repo-b")
        repo_c = _new_repo_with_marker_and_pr(self.tmp, "repo-c")
        cases = (
            ("payload cwd", {"command": "gh pr merge 7", "cwd": str(repo_b)}),
            ("cd_target", {"command": f"cd {repo_c} && gh pr merge 7"}),
        )
        for label, tool_input in cases:
            with self.subTest(candidate=label):
                result = _run_hook({"tool_input": tool_input}, repo_a, self.home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)
                self.assertNotIn("approval-missing", result.stdout)

    # --- AC-2 (impl-gate Round 1 IG-8 修正): marker を持つ候補を優先 ---------
    def test_untrusted_candidate_with_marker_is_used_when_trusted_candidate_lacks_marker(self):
        # IG-8 再現形。旧実装は trusted 候補（プロセス cwd）が marker 無しでも
        # git repo として解決した時点で候補ループを break し、marker + PR URL を
        # 持つ untrusted 候補（payload cwd）を一度も評価しないまま step 5 の
        # marker 検査で無出力 exit 0 に抜けていた（main では同じ入力が
        # approval-missing として通知していた = fail-open 回帰）。
        # 修正後は trusted 候補が marker を持たない場合は break せず、marker を
        # 持つ untrusted 候補（payload cwd）を採用して通常の証跡検査へ進む。
        trusted_no_marker = self.tmp / "trusted-no-marker"
        trusted_no_marker.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=trusted_no_marker, check=True)
        untrusted_with_marker = _new_repo_with_marker_and_pr(self.tmp, "untrusted-with-marker", pr=7)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(untrusted_with_marker)}},
            trusted_no_marker, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_harness_payload_cwd_under_process_cwd_git_root_needs_no_marker(self):
        # ADR-6: A-1 の harness 例外は候補順で吸収される。プロセス cwd
        # （trusted）が第 1 候補として評価され、marker 検査でも同じ git root
        # （payload cwd は同一 repo の sub dir で toplevel が一致）を指すため、
        # marker 優先ルール（IG-8 修正後の AC-2）が入っても payload cwd 専用の
        # 分岐は生まれない。両候補とも marker が無いので、全候補 marker 不在の
        # 従来フォールバック（AC-6(a)）でプロセス cwd 由来 root に決まり、
        # 誤爆しないことを exit 0 で固定する。
        repo = self.tmp / "harness-repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        sub = repo / "sub"
        sub.mkdir()
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 1", "cwd": str(sub)}}, repo, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    # --- AC-11: untrusted 候補は marker 必須 ---------------------------------
    # marker の無い untrusted 候補は root に採用しない。ただし全候補と各祖先に
    # marker が無く実行先が確定できる merge は GDD の対象外として通す（旧仕様は
    # `repo-root-unresolvable` として通知していた。Renovate 自動マージを妨げた事象を
    # 受けて期待値を反転。不足として通知する側の契約は test_merge_gate_hook_non_gdd_merge.py）。
    def test_cd_target_without_marker_passes_as_outside_gdd(self):
        repo = self.tmp / "no-marker-repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        non_repo = self.tmp / "not-a-repo-3"
        non_repo.mkdir()
        command = f"cd {repo} && gh pr merge 1"
        result = _run_hook({"tool_input": {"command": command}}, non_repo, self.home)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    def test_payload_cwd_without_marker_passes_when_process_cwd_is_not_git(self):
        repo = self.tmp / "no-marker-repo-2"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        non_repo = self.tmp / "not-a-repo-4"
        non_repo.mkdir()
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 1", "cwd": str(repo)}}, non_repo, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    # --- AC-12: 候補が非ディレクトリ / git 失敗でも hook が無出力で落ちない ---
    def test_non_directory_cd_target_does_not_crash_the_hook(self):
        non_repo = self.tmp / "not-a-repo-5"
        non_repo.mkdir()
        result = _run_hook(
            {"tool_input": {"command": "cd /no/such/dir && gh pr merge 1"}}, non_repo, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("repo-root-unresolvable", result.stdout)

    # --- AC-16: root 確定後の chdir が維持されている -------------------------
    def test_steering_resolution_operates_inside_the_resolved_cd_target_root(self):
        # chdir を落とすと gdd_pre_push_resolve_steering がプロセス cwd を見て
        # 無出力 exit 0 になる（AC-16 の規定）。steering 由来の block reason が
        # 出ることで、実際に cd_target 配下で解決していることを固定する。
        repo = _new_repo_with_marker_and_pr(self.tmp, "chdir-check-repo")
        non_repo = self.tmp / "not-a-repo-6"
        non_repo.mkdir()
        command = f"cd {repo} && gh pr merge 7"
        result = _run_hook({"tool_input": {"command": command}}, non_repo, self.home)
        self.assertIn("approval-missing", result.stdout)

    # --- AC-17: payload cwd が非 git ディレクトリのとき root はプロセス cwd 由来で
    # 確定するが、解決できない実行先 signal は無視せず不足として通知（IG-13 (a‴)） ---------
    def test_non_git_payload_cwd_blocks_as_pr_target_unresolvable_not_repo_root_unresolvable(self):
        # 変更前（main）は候補全滅扱いで `repo-root-unresolvable`。IG-13 remediation 前の
        # HEAD は「解決できない payload cwd = 無い」とみなし `approval-missing` まで進んで
        # いたが、同じ「無い」扱いが CDPATH / 相対パス等の正規化差ごとに無検査 exit 0 を
        # 生んだため（IG-8 / IG-9 / IG-12 / IG-13）、raw で非空なのに toplevel へ解決
        # できない untrusted 実行先は `pr-target-unresolvable` として通知する（人間承認済み
        # 案 (a‴)。AC-17 / AC-18 の意味変更）。root 自体はプロセス cwd 由来で決まるので
        # `repo-root-unresolvable` にはならない。
        repo = _new_repo_with_marker_and_pr(self.tmp, "process-cwd-repo")
        non_git_dir = self.tmp / "payload-non-git"
        non_git_dir.mkdir()
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(non_git_dir)}}, repo, self.home,
        )
        self.assertNotIn("repo-root-unresolvable", result.stdout)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)


class RootVsExecutionTargetMismatchTests(unittest.TestCase):
    """AC-18: root ≠ `gh` の実行先を既存 `pr-target-unresolvable` へ倒す。

    到達位置は step 5 の marker 検査の直後（steering 解決より前）。impl-gate
    Round 2 IG-9: trusted 候補（プロセス cwd）が marker を持つと候補ループは
    候補 1 で確定するため、marker + 対象 PR の steering を持つ payload cwd は
    評価されない。旧位置（対象 PR 解決の後）では steering 未解決 / 別 PR の
    無検査 exit 0 が先に効き、main（payload cwd を root にしていた）が
    approval-missing として通知していた入力が HEAD で無出力 exit 0 になっていた。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)

    def _git_repo(self, name):
        return _init_bare_repo(self.tmp, name)

    def _committed_repo(self, name):
        return _init_named_repo(self.tmp, name)

    def _full_evidence_repo(self, name):
        return _new_full_evidence_repo(self.tmp, name)

    def _repo_with_marker_and_pr(self, name, pr):
        return _new_repo_with_marker_and_pr(self.tmp, name, pr)

    # --- IG-9 再現形（main では approval-missing の通知 / 旧 HEAD では無出力 exit 0）
    def test_payload_cwd_with_target_pr_steering_blocks_when_trusted_root_has_no_steering(self):
        repo_a = self._committed_repo("trusted-marker-only")
        _write_marker_only(repo_a, active=False)
        repo_b = self._repo_with_marker_and_pr("payload-with-target-pr", pr=7)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(repo_b)}}, repo_a, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_payload_cwd_with_target_pr_steering_blocks_when_trusted_root_records_another_pr(self):
        repo_a = self._repo_with_marker_and_pr("trusted-other-pr", pr=9)
        repo_b = self._repo_with_marker_and_pr("payload-with-target-pr-2", pr=7)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(repo_b)}}, repo_a, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    # --- AC-18 本体（root に全証跡があっても実行先が別 repo なら不足の通知） --------
    def test_cd_target_pointing_at_a_different_repo_blocks_as_pr_target_unresolvable(self):
        repo_a = self._full_evidence_repo("target-a")
        repo_b = self._git_repo("target-b")
        result = _run_hook(
            {"tool_input": {"command": f"cd {repo_b} && gh pr merge 7"}}, repo_a, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_payload_cwd_pointing_at_a_different_repo_blocks_symmetrically(self):
        repo_a = self._full_evidence_repo("target-a-payload")
        repo_b = self._git_repo("target-b-payload")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(repo_b)}}, repo_a, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    # --- 誤爆しない側（同一 toplevel / 非 GDD セッション / AC-4 不採用形） -------
    def test_cd_target_pointing_at_a_subdirectory_of_root_does_not_block(self):
        repo_a = self._full_evidence_repo("target-a-sub")
        sub = repo_a / "sub"
        sub.mkdir()
        result = _run_hook(
            {"tool_input": {"command": f"cd {sub} && gh pr merge 7"}}, repo_a, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_payload_cwd_pointing_at_a_subdirectory_of_root_does_not_block(self):
        repo_a = self._full_evidence_repo("target-a-payload-sub")
        sub = repo_a / "sub"
        sub.mkdir()
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(sub)}}, repo_a, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_no_marker_anywhere_keeps_passing_through_even_if_payload_cwd_points_elsewhere(self):
        # AC-6(a): 全候補が marker を持たない非 GDD セッションは従来どおり素通り。
        # AC-18 は marker 検査の**後**に置くので、非 GDD の repo の merge を
        # 新たに通知することはない（誤爆面を増やさない側の固定）。
        repo_a = self._git_repo("no-marker-a")
        repo_b = self._git_repo("no-marker-b")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(repo_b)}}, repo_a, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)

    # --- (a) 拡張（impl-gate T-8/T-9 F-1 / F-3、人間承認 2026-09-08T08:32:20+09:00）
    # 旧 fixture `test_ac4_rejected_chdir_form_is_not_caught_by_ac18` は「AC-4 で
    # 不採用になる chdir 形は AC-18 の比較対象が無く allow」を限界の明示として
    # 固定していた。承認案 (a)(1) により意味が変わり、走査範囲に chdir intent が
    # あるのに AC-4 で不採用にした形は「解決できない実行先」として
    # `pr-target-unresolvable` へ倒す。fixture は F-1 が指摘した実害形そのもの
    # （root = 全証跡を持つ repo A、実シェルは repo B で `gh` を走らせる）で、
    # 修正前は 3 版（origin/main / pre-T-8 / T-8）とも ALLOW だった。
    def test_ac4_rejected_chdir_forms_block_as_pr_target_unresolvable(self):
        a = self._full_evidence_repo("target-a-intent")
        b = self._git_repo("target-b-intent")
        commands = (
            f"builtin cd {b} && gh pr merge 7",
            f"cd {a} && cd {b} && gh pr merge 7",
            f"cd {a} && echo x#y ; cd {b}\ngh pr merge 7",
            f"cd -- {b} && gh pr merge 7",
            f"cd -P {b} && gh pr merge 7",
            f"cd {a} && CD=cd && $CD {b} && gh pr merge 7",
            f"cd {a} && env --chdir={b} gh pr merge 7",
            f"env --chdir={b} gh pr merge 7",
            f"pushd {b} && gh pr merge 7",
            f"cd {a} && bash -c 'cd {b} && gh pr merge 7'",
            f"eval 'cd {b} && gh pr merge 7'",
            f"(cd {b} && gh pr merge 7)",
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, a, self.home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_env_options_with_separate_argument_before_chdir_still_block(self):
        # `env -C <B>` 単独は不足として通知されるのに、`-u X` を
        # 挟むだけで intent が落ちて ALLOW になっていた（同一 guard 内の非対称）。
        # fixture はこの欠陥の実害形そのもの（root = 全証跡を持つ repo A、実シェルは
        # repo B で `gh` を走らせる）。
        a = self._full_evidence_repo("target-a-env-u")
        b = self._git_repo("target-b-env-u")
        for command in (
            f"env -u X -C {b} gh pr merge 7",
            f"env -u X --chdir={b} gh pr merge 7",
            f"/usr/bin/env -u X -C {b} gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, a, self.home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_bundled_env_short_options_before_chdir_still_block(self):
        # `env` の短オプションは束ねて書ける。macOS 実測で `env -iC <B> pwd` /
        # `env -iC<B> pwd` / `env -vC <B> pwd` はいずれも `<B>` へ chdir するが、
        # 非束ね形 `env -i -C <B>` だけが不足として通知される非対称が残っていた
        # （束ね形は intent が落ち、root = repo A の証跡で allow に抜ける）。
        a = self._full_evidence_repo("target-a-env-bundle")
        b = self._git_repo("target-b-env-bundle")
        for command in (
            f"env -iC {b} gh pr merge 7",
            f"env -iC{b} gh pr merge 7",
            f"env -vC {b} gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, a, self.home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    def test_env_without_chdir_option_still_allows(self):
        # 誤爆しない側: chdir しない `env`（環境変数の設定 / `-u` / `-i` 単独）は
        # intent を立てず、root = 実行先のまま allow を維持する。
        a = self._full_evidence_repo("target-a-env-allow")
        for command in (
            "env GH_TOKEN=x gh pr merge 7",
            "env -u X gh pr merge 7",
            "env -i gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, a, self.home)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_adopted_cd_target_into_root_itself_still_allows(self):
        # 誤爆しない側: AC-4 / AC-5 の正当形（`cd <root> && ... && gh pr merge`）は
        # intent があっても cd_target が採用され AC-18 の一致枝に入る。
        a = self._full_evidence_repo("target-a-intent-allow")
        for command in (
            f"cd {a} && gh pr merge 7",
            f"cd {a} && git fetch && gh pr merge 7",
            f"cd {a}; gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, a, self.home)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    # --- IG-12 再現形（impl-gate Round 3）: payload cwd が**相対パス** ----------
    # 候補ループは `cd "$PROJECT_ROOT"` 前（プロセス cwd 基準）、AC-18 は `cd` 後
    # （PROJECT_ROOT 基準）で同じ文字列を解決していたため、proc cwd = `P/x`
    # （P に marker）/ `P/x/y` = marker + 対象 PR steering の入れ子 repo /
    # `cwd: "y"` で AC-18 が比較対象（`P/y` = 不在）を失い無検査 exit 0 に抜けた。
    # main（be2e907）は抽出直後に `cd && pwd` で絶対化していたため
    # approval-missing として通知していた。承認済み案 (a): 抽出直後に 1 回だけ
    # 絶対化し、AC-18 は候補ループで解決した toplevel を再利用する。
    def _nested_repo_with_marker_and_pr(self, parent, name, pr):
        return _new_repo_with_marker_and_pr(parent, name, pr, commit=False)

    def test_relative_payload_cwd_into_nested_repo_blocks_when_trusted_root_has_no_steering(self):
        repo_p = self._committed_repo("rel-parent")
        _write_marker_only(repo_p, active=False)
        proc_cwd = repo_p / "x"
        proc_cwd.mkdir()
        self._nested_repo_with_marker_and_pr(proc_cwd, "y", pr=7)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": "y"}}, proc_cwd, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_relative_payload_cwd_into_nested_repo_blocks_when_trusted_root_records_another_pr(self):
        repo_p = self._repo_with_marker_and_pr("rel-parent-other-pr", pr=9)
        proc_cwd = repo_p / "x"
        proc_cwd.mkdir()
        self._nested_repo_with_marker_and_pr(proc_cwd, "y", pr=7)
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": "y"}}, proc_cwd, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_relative_payload_cwd_resolves_against_process_cwd_and_does_not_block_inside_root(self):
        # 誤爆しない側: 相対 cwd はプロセス cwd 基準で絶対化され、root 配下の
        # subdirectory なら AC-18 は一致とみなす（絶対パス形 `..._subdirectory_of_root`
        # と同じ結果）。絶対化の基準を取り違える mutation を落とす固定。
        repo_a = self._full_evidence_repo("rel-inside-root")
        (repo_a / "sub").mkdir()
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": "sub"}}, repo_a, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    # --- IG-13 再現形（impl-gate Round 4）: hook env の CDPATH -------------------
    # hook が Claude Code プロセスから継承する `CDPATH` が非空（`.` だけでも）だと、
    # bash の `cd` は相対パスを解決したあと絶対パスを stdout に印字するため
    # `$(cd "$PAYLOAD_CWD" && pwd)` が 2 行になり、payload cwd 候補が `-d` 判定で
    # 脱落 → AC-18 が比較対象を失い IG-12 形が無検査 exit 0 に抜けた（HEAD 0117be2）。
    # 承認済み案 (a‴)(1): `PROCESS_CWD` 取得直後に `unset CDPATH`。
    def test_relative_payload_cwd_into_nested_repo_blocks_even_when_cdpath_is_set(self):
        repo_p = self._committed_repo("rel-parent-cdpath")
        _write_marker_only(repo_p, active=False)
        proc_cwd = repo_p / "x"
        proc_cwd.mkdir()
        self._nested_repo_with_marker_and_pr(proc_cwd, "y", pr=7)
        for cdpath in (".", f".:{proc_cwd}"):
            with self.subTest(CDPATH=cdpath):
                result = _run_hook(
                    {"tool_input": {"command": "gh pr merge 7", "cwd": "y"}}, proc_cwd, self.home,
                    extra_env={"CDPATH": cdpath},
                )
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)

    # --- (a‴)(2): 解決できない untrusted 実行先 signal は「無い」とみなさず不足として通知 ---
    # 4 回連続の fail-open（IG-8 / IG-9 / IG-12 / IG-13）に共通する根本原因は、
    # untrusted 入力の正規化が 1 つ崩れるたびに「解決できない = 無い」扱いで
    # untrusted 候補が評価されないまま無検査 exit 0 へ抜けること。raw で非空なのに
    # toplevel へ解決できない payload cwd / cd_target は `pr-target-unresolvable` で
    # 不足として通知する（AC-12 の「hook を落とさない」は維持し、通過扱いではなく不足の通知へ倒す）。
    # 旧挙動: A（marker のみ）は steering 未解決で無出力 exit 0（C2 形）。
    def test_unresolvable_payload_cwd_blocks_as_pr_target_unresolvable(self):
        repo_a = self._committed_repo("trusted-marker-only-unresolvable-cwd")
        _write_marker_only(repo_a, active=False)
        non_git_dir = self.tmp / "payload-non-git-dir"
        non_git_dir.mkdir()
        for label, cwd in (("missing", str(self.tmp / "no-such-dir")), ("non-git", str(non_git_dir))):
            with self.subTest(payload_cwd=label):
                result = _run_hook(
                    {"tool_input": {"command": "gh pr merge 7", "cwd": cwd}}, repo_a, self.home,
                )
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("pr-target-unresolvable", result.stdout)
                self.assertNotIn("repo-root-unresolvable", result.stdout)

    def test_unresolvable_cd_target_blocks_as_pr_target_unresolvable(self):
        # cd_target 側の対称形（C7 形）。AC-4 は絶対パスであれば存在確認をしないので、
        # 不在 dir が cd_target として届く。旧挙動は payload cwd 側と同じ無出力 exit 0。
        repo_a = self._committed_repo("trusted-marker-only-unresolvable-cd")
        _write_marker_only(repo_a, active=False)
        result = _run_hook(
            {"tool_input": {"command": f"cd {self.tmp}/no-such-cd-dir && gh pr merge 7"}},
            repo_a, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)
        self.assertNotIn("repo-root-unresolvable", result.stdout)

    def test_unresolvable_payload_cwd_does_not_block_outside_gdd_session(self):
        # 誤爆しない側（AC-6(a) 維持）: marker がどこにも無い非 GDD セッションでは
        # marker 検査の exit 0 が (a‴) の通知より先に効く。非 GDD の repo の merge を
        # 新たに通知しない固定。
        repo_a = self._committed_repo("no-marker-unresolvable-cwd")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(self.tmp / "no-such-dir")}},
            repo_a, self.home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)


class CdTargetEvasionHookLevelTests(unittest.TestCase):
    """design.md § テスト『迂回 subTest』: 迂回形はすべて root 候補にならず不足として通知する。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.non_repo = self.tmp / "not-a-repo"
        self.non_repo.mkdir()

    def _decoy(self, name):
        return _new_marker_only_repo(self.tmp, name)

    def test_evasion_forms_never_resolve_a_root_and_stay_blocked(self):
        a = self._decoy("decoy-a")
        b = self._decoy("decoy-b")
        commands = (
            f"cd {a} && bash -c 'cd {b} && gh pr merge 7'",
            f"eval 'cd {b} && gh pr merge 7'",
            f"cd {a} && pushd {b} && gh pr merge 7",
            f"cd {a} && (cd {b} && gh pr merge 7)",
            f"(cd {a} && gh pr merge 7)",
            "cd ~/repo && gh pr merge 7",
            f"cd -- {a} && gh pr merge 7",
            f"cd -P {a} && gh pr merge 7",
            f"cd {a} && CD=cd && $CD {b} && gh pr merge 7",
            f"cd {a} && bash -c 'cd$IFS{b}; gh pr merge 7'",
            f"cd {a} && env --chdir={b} gh pr merge 7",
            f"pushd {a} && gh pr merge 7",
            # T-8 (completion-check Round2 H-1): 語中 `#` が既定の shlex
            # commenters により行末までコメント扱いされていた頃は、実際には
            # 2 つ目の `cd` が存在するのに 1 つ目の `cd`（decoy-a）だけが見え、
            # cd_target がその 1 つに単独確定して decoy-a の marker 経由で
            # root が誤って解決していた（`untrusted-root-unverified` を返し、
            # 他の迂回形と揃って `repo-root-unresolvable` にならなかった）。
            f"cd {a} && echo x#y ; cd {b}\ngh pr merge 7",
        )
        for command in commands:
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, self.non_repo, self.home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("repo-root-unresolvable", result.stdout)


class WordStartCommentHookLevelTests(unittest.TestCase):
    """impl-gate T-8/T-9 F-2（承認案 (a)(2)）: `#` の扱いを bash 準拠にする。

    語頭の `#` はコメント（行末コメント付きの正当な merge を通知しない）、
    語中の `#` は token の一部（T-8 が塞いだ main の gate 全面素通りを開け直さない）。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)

    def test_trailing_comment_after_merge_does_not_block(self):
        # F-2 の 4 形: origin/main `ALLOW(exit0-silent)` → T-8 `pr-target-unresolvable`
        # に反転していた新規 false-positive。復旧文（root 内で実行 / `cd` / `-R`）が
        # 原因に対応しない通知だったため、allow へ戻す。
        a = _new_full_evidence_repo(self.tmp, "comment-allow")
        for command in (
            "gh pr merge 7 # squash after CI",
            "gh pr merge 7 --squash # ok",
            "gh pr merge 7 #",
            f"cd {a} && gh pr merge 7 # done",
        ):
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, a, self.home)
                self.assertEqual(result.returncode, 0)
                self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_hash_inside_word_still_activates_the_gate(self):
        # T-8 の実価値: main は `is_merge=false` で gate 自体が起動せず無検査 ALLOW
        # だった 3 形。marker + 対象 PR steering あり・承認証跡なしの repo では
        # `approval-missing` で通知されること（= gate が起動していること）を固定。
        repo = _new_repo_with_marker_and_pr(self.tmp, "hash-in-word", pr=7)
        for command in (
            "echo x#y && gh pr merge 7",
            "echo x#y ; gh pr merge 7",
            "bash -c 'echo a#b && gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = _run_hook({"tool_input": {"command": command}}, repo, self.home)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("approval-missing", result.stdout)


class RepoRootUnresolvableWordingTests(unittest.TestCase):
    """AC-3/AC-7: 全滅時の通知文言が訂正後の 3 断片を含む。"""

    def test_repo_root_unresolvable_wording_matches_the_corrected_recovery_fragments(self):
        tmp = Path(tempfile.mkdtemp())
        home = tmp / "home"
        (home / ".claude").mkdir(parents=True)
        non_repo = tmp / "non-repo"
        non_repo.mkdir()
        # 実行先を確定できない形（実在しない cd 先）。非 git cwd の素の merge は
        # GDD の対象外として通るようになったので、不足の通知が残る入力で文言を見る。
        result = _run_hook(
            {"tool_input": {"command": f"cd {tmp}/no-such-dir && gh pr merge 1"}}, non_repo, home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("repo-root-unresolvable", result.stdout)
        self.assertIn("cd ", result.stdout)
        self.assertIn("&& gh pr merge", result.stdout)
        self.assertIn("repo 内のディレクトリ", result.stdout)

    def test_repo_flag_merge_outside_gdd_passes_from_non_git_cwd(self):
        # 旧 AC-3（`-R owner/repo` が付いていても素通りしない）の反転。cwd が marker の
        # 無い git repo なら同じコマンドは従来から exit 0 で、非 git cwd だけが不足として通知される
        # 非対称だった。非 git cwd から -R で GDD 管理下の PR を merge する形が無検査に
        # なる点は、git cwd と同じ限界として CHANGELOG に明記している。
        tmp = Path(tempfile.mkdtemp())
        home = tmp / "home"
        (home / ".claude").mkdir(parents=True)
        non_repo = tmp / "non-repo-2"
        non_repo.mkdir()
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge -R acme/widgets 7"}}, non_repo, home,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('"hookEventName"', result.stdout)


class PrTargetUnresolvableWordingTests(unittest.TestCase):
    """AC-18（advisory-1、impl-gate Round 4 IG-13 (a‴) により T-3 で必須化）:

    `pr-target-unresolvable` の 1 文目（旧文言: `URL か -R owner/repo <番号> で
    対象を明示してください`）は「root ≠ 実行先」および「実行先が解決できない」
    形の復旧手順として不適合（URL / `-R` を足しても復旧しない。復旧は
    「root の repo 内のディレクトリで実行する」または「実在する repo を `cd` に
    指定する」）。(a‴) でこの 2 事象が同じ reason code に合流したため、訂正後の
    文言は両方の case で同一の復旧フラグメントを案内すること。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)

    def _git_repo(self, name):
        return _init_bare_repo(self.tmp, name)

    def _full_evidence_repo(self, name):
        return _new_full_evidence_repo(self.tmp, name)

    def test_pr_target_unresolvable_wording_guides_recovery_for_root_vs_execution_target_mismatch(self):
        # AC-18 本体形: root A に全証跡があるが `cd` 先が別 repo B。
        repo_a = self._full_evidence_repo("target-a-wording")
        repo_b = self._git_repo("target-b-wording")
        result = _run_hook(
            {"tool_input": {"command": f"cd {repo_b} && gh pr merge 7"}}, repo_a, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)
        self.assertIn("root の repo 内のディレクトリで実行する", result.stdout)
        self.assertIn("実在する repo を cd に指定する", result.stdout)

    def test_pr_target_unresolvable_wording_also_applies_to_the_unresolvable_target_case(self):
        # AC-18 (a‴) 形: `cd` 先の signal は届いたが解決できない（不在 dir）。
        repo_a = self._full_evidence_repo("target-a-wording-unresolvable")
        result = _run_hook(
            {"tool_input": {"command": f"cd {self.tmp}/no-such-cd-dir-wording && gh pr merge 7"}},
            repo_a, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)
        self.assertIn("root の repo 内のディレクトリで実行する", result.stdout)
        self.assertIn("実在する repo を cd に指定する", result.stdout)


class TokenizerDegradationBlockTests(unittest.TestCase):
    """shlex が縮退した解析結果で allow を返さないこと。

    縮退した token 列は演算子と密着した token を割らないので、`;gh` が token `gh`
    にならず `is_merge` が落ちる。merge 検出も chdir 語彙も同時に数え落とすため、
    「merge ではない」と断定できない。解析未完走（`parse-error`）と同じ family
    へ倒す（独立レビュー 3 巡目 high）。
    """

    # bash では valid だが shlex が ValueError を投げる形（ANSI-C quoting）。
    _DEGRADING_PREFIX = "x=$'\\'' ;"

    def test_degraded_merge_command_blocks_instead_of_passing_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_repo_with_marker_and_pr(parent, "root")
            result = _run_hook(
                {"tool_input": {"command": self._DEGRADING_PREFIX + "gh pr merge 7"}},
                root,
                parent / "home",
            )
            self.assertEqual(result.stdout.strip() != "", True, "無出力素通りは不可")
            self.assertIn("parse-error", result.stdout)

    def test_degraded_command_hiding_a_second_cd_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_repo_with_marker_and_pr(parent, "root")
            other = _new_marker_only_repo(parent, "other")
            command = f"{self._DEGRADING_PREFIX}cd {other} ;gh pr merge 7"
            result = _run_hook(
                {"tool_input": {"command": command}}, root, parent / "home"
            )
            self.assertIn("parse-error", result.stdout)

    def test_unparsable_merge_outside_jurisdiction_still_blocks(self):
        # 解析が完走しない family（python3 不在 / import 失敗 / 不正 JSON）では
        # `is_merge` が false のまま残る。root 未解決時の管轄外通過をこの family まで
        # 広げると、本物の `gh pr merge -R owner/repo 7` が非 git ディレクトリで
        # 無出力素通りになる（origin/main は不足として通知していた）。
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "nongit"
            outside.mkdir()
            stub = Path(tmp) / "stub"
            stub.mkdir()
            fake = stub / "python3"
            fake.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            fake.chmod(0o755)
            result = _run_hook(
                {"tool_input": {"command": "gh pr merge -R owner/repo 7"}},
                outside,
                Path(tmp) / "home",
                extra_env={"PATH": f"{stub}:{os.environ.get('PATH', '')}"},
            )
            self.assertIn("repo-root-unresolvable", result.stdout)

    def test_degraded_non_merge_command_outside_jurisdiction_passes(self):
        # 縮退のせいで merge 判定が付かないまま root も解決できない場合、GDD
        # セッションかどうかも決められない。ここで不足として通知すると、非 git ディレクトリ
        # で実行した merge でもないコマンドを無関係な理由で通知することになる。
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "nongit"
            outside.mkdir()
            result = _run_hook(
                {"tool_input": {"command": "echo it's fine merge"}},
                outside,
                Path(tmp) / "home",
            )
            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.returncode, 0)

    def test_non_merge_command_is_not_blocked_by_degradation(self):
        # 過剰な通知を避ける側。step 1 の粗いフィルタが見るのは **payload 全体**
        # の `merge` 部分文字列なので（`run-merge-gate-hook.sh` step 1）、payload の
        # どこにも `merge` が無いことを先に assert する。この前提を書かないと
        # 「payload に cwd を足したら通らなくなる」形の空虚なテストになる
        # （PR review M-2）。
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_repo_with_marker_and_pr(parent, "root")
            payload = {"tool_input": {"command": self._DEGRADING_PREFIX + "echo hi"}}
            self.assertNotIn("merge", json.dumps(payload))
            result = _run_hook(payload, root, parent / "home")
            self.assertEqual(result.stdout.strip(), "")
            self.assertEqual(result.returncode, 0)

    def test_non_merge_degraded_command_blocks_when_payload_carries_merge(self):
        """AC-19 § 限界（誤爆面）の regression fixture。

        step 1 のフィルタは payload 全体を見るため、`merge` を含む worktree パスが
        `tool_input.cwd` に載る環境では、`merge` を含まないコマンドでも縮退すれば
        不足として通知される。fail-closed 方向のみだが、開示した挙動なので実測で固定する
        （PR review M-2）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_repo_with_marker_and_pr(parent, "merge-gate-root")
            self.assertIn("merge", str(root))
            result = _run_hook(
                {"tool_input": {"command": self._DEGRADING_PREFIX + "echo hi",
                                "cwd": str(root)}},
                root, parent / "home",
            )
            self.assertIn("parse-error", result.stdout)


class PayloadCwdWithCdTargetTests(unittest.TestCase):
    """AC-2: root 確定後も残り候補の toplevel を解決し続けること。

    `tool_input.cwd` を送る runtime の PreToolUse payload では（Claude Code の Bash は送らず、
    最上位に `cwd` を持つ。test_gates_toplevel_cwd.py）、
    「payload cwd あり × cd_target あり × root は候補 0 で確定」が本 PR の主目的形
    になる。候補ループの `continue` を IG-8 以前の `break` へ戻す退行は、この
    組み合わせでのみ観測できる: 候補 0 で打ち切ると `_MG_CAND_ROOT[1]` / `[2]` が
    空のまま残り、AC-18 が「実行先 signal は非空なのに解決できない」と判定して
    主目的形を `pr-target-unresolvable` へ倒す（PR review M-3。既存 fixture は
    すべて `tool_input.cwd` を省いており、候補 1 が `-n` チェックで先に continue
    するためこの行に到達しなかった）。
    """

    def test_payload_cwd_and_cd_target_under_root_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_full_evidence_repo(parent, "root")
            sub = root / "sub"
            sub.mkdir()
            result = _run_hook(
                {"tool_input": {"command": f"cd {sub} && gh pr merge 7",
                                "cwd": str(root)}},
                root, parent / "home",
            )
            self.assertEqual(result.stdout.strip(), "", "主目的形が block されている")
            self.assertEqual(result.returncode, 0)

    def test_cd_target_outside_root_still_blocks_with_payload_cwd(self):
        # 上のテストが「何でも allow」で通っていないことの対向 assert。
        # 同じ payload 形（cwd あり）で `cd` 先だけ別 repo にすると不足として通知される。
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_full_evidence_repo(parent, "root")
            other = _new_marker_only_repo(parent, "other")
            result = _run_hook(
                {"tool_input": {"command": f"cd {other} && gh pr merge 7",
                                "cwd": str(root)}},
                root, parent / "home",
            )
            self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
            self.assertIn("pr-target-unresolvable", result.stdout)


class UntrustedRootBlockTests(unittest.TestCase):
    """AC-13/AC-14: untrusted 由来 root で gate 起動根拠が無い経路を不足の通知へ倒す。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.non_repo = self.tmp / "not-a-repo"
        self.non_repo.mkdir()

    def _marker_repo(self, name):
        return _new_marker_only_repo(self.tmp, name)

    def test_three_ungated_exit_paths_block_for_cd_target_origin(self):
        # (1) steering が found でない（`.steering/` を作らない）。
        repo1 = self._marker_repo("untrusted-1")
        result1 = _run_hook(
            {"tool_input": {"command": f"cd {repo1} && gh pr merge 7"}}, self.non_repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result1.stdout)
        self.assertIn("untrusted-root-unverified", result1.stdout)

        # (2) `multiple` かつ対象 PR を記録した steering が無い。
        repo2 = self._marker_repo("untrusted-2")
        _write_two_done_steerings(repo2, active=False)
        result2 = _run_hook(
            {"tool_input": {"command": f"cd {repo2} && gh pr merge 999"}}, self.non_repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result2.stdout)
        self.assertIn("untrusted-root-unverified", result2.stdout)

        # (3) steering の PR URL が別 PR を指す。
        repo3 = self._marker_repo("untrusted-3")
        _write_state(repo3, active=False, pr_url="https://github.com/acme/widgets/pull/1")
        result3 = _run_hook(
            {"tool_input": {"command": f"cd {repo3} && gh pr merge 999"}}, self.non_repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result3.stdout)
        self.assertIn("untrusted-root-unverified", result3.stdout)

    def test_payload_cwd_origin_hits_the_same_block(self):
        # A-1 の帰結: payload cwd（プロセス cwd の git root 配下でない）も同じ扱い。
        repo = self._marker_repo("untrusted-payload")
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7", "cwd": str(repo)}}, self.non_repo, self.home,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("untrusted-root-unverified", result.stdout)

    def test_trusted_process_cwd_origin_keeps_existing_exit_zero_for_the_same_states(self):
        # 非対称固定: 同じ状態でも **プロセス cwd** 由来なら従来どおり exit 0。
        repo1 = self.tmp / "trusted-1"
        repo1.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo1, check=True)
        (repo1 / ".claude").mkdir(parents=True)
        (repo1 / ".claude" / "gdd-dev.local.md").write_text("active: false\n")
        result1 = _run_hook({"tool_input": {"command": "gh pr merge 7"}}, repo1, self.home)
        self.assertEqual(result1.returncode, 0)
        self.assertNotIn('"hookEventName"', result1.stdout)

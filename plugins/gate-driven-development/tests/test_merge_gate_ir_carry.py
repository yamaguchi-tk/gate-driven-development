"""merge gate（`gh pr merge`）の `received: no` 経路が Independent Review Carry を読むこと。

レビュー済みの tip に default branch を merge しただけの HEAD では、旧 sha の
`Independent Review` を引き継いで、bot の待機の免除と独立レビューの要求を満たす
（条件の正本: references/self-review-lanes.md § Independent Review の引き継ぎ）。
hook の入口（run-merge-gate-hook.sh）から走らせる。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _git_fixture import init_repo
from _merge_gate_support import _approval_line, _run_hook, _write_evidence_state

GUIDE = "既定ブランチを取り込むだけのマージコミットなら Independent Review Carry 行で引き継げる"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _iso(minutes_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


class MergeGateIrCarryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        init_repo(self.repo, branch="main")
        _git(self.repo, "switch", "-q", "-c", "feature")
        (self.repo / "README.md").write_text("test\n- feature\n", encoding="utf-8")
        _git(self.repo, "commit", "-q", "-am", "feature index")
        self.reviewed = _git(self.repo, "rev-parse", "HEAD")
        _git(self.repo, "switch", "-q", "main")
        (self.repo / "README.md").write_text("test\n- main\n", encoding="utf-8")
        (self.repo / "main.txt").write_text("main\n", encoding="utf-8")
        _git(self.repo, "add", "README.md", "main.txt")
        _git(self.repo, "commit", "-q", "-m", "main moves")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "main")
        _git(self.repo, "switch", "-q", "feature")

    def _merge(self, resolution="test\n- feature\n- main\n", extra=None, minutes_ago=0):
        subprocess.run(
            ["git", "-C", str(self.repo), "merge", "-q", "--no-ff", "--no-commit", "main"],
            capture_output=True, text=True, check=False,
        )
        (self.repo / "README.md").write_text(resolution, encoding="utf-8")
        for name, body in (extra or {}).items():
            (self.repo / name).write_text(body, encoding="utf-8")
        _git(self.repo, "add", "-A")
        # 待機（40 分）の経過後を作るときは、merge commit の日付を過去にする
        # （Last Review Push At は HEAD の committer date 以降でなければならない）
        when = _iso(minutes_ago)
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-q", "--no-edit", "--date", when],
            check=True, capture_output=True,
            env={**os.environ, "GIT_COMMITTER_DATE": when},
        )
        return _git(self.repo, "rev-parse", "HEAD")

    def _run(self, head, *, carry=True, push_minutes_ago=0, medium=0, high=0, disposition_sha=None):
        push_at = _iso(push_minutes_ago)
        lines = [
            _approval_line(7, head),
            f"- Pre-Merge Review Recheck: {head} | new_blocking: 0 | at: {_iso()}",
            f"- Last Review Push At: {head} | at: {push_at}",
            f"- Bot Review Received: {head} | received: no | at: {push_at}",
            f"- Independent Review: {self.reviewed} | reviewer: light-lane-independent-reviewer "
            f"| context: diff-only | high: {high} | medium: {medium} | blocking: 0 | at: {_iso()}",
        ]
        if carry:
            lines.append(
                f"- Independent Review Carry: {head} | from: {self.reviewed} "
                f"| verified: diff-equal | at: {_iso()}"
            )
        if disposition_sha:
            lines.append(
                f"- Medium Disposition: {disposition_sha} | count: {medium} | recorded: accepted | note: 受容済み "
                f"| at: {_iso()}"
            )
        _write_evidence_state(self.repo, lines)
        payload = {"tool_input": {"command": "gh pr merge 7"}}
        # hook は bash の SECONDS で持ち時間を測る。混んだマシンで前段にかかる分を差し引く
        return _run_hook(payload, self.repo, self.home, extra_env={"SECONDS": "-120"}, timeout=30)

    def assert_allowed(self, result):
        # 落ちた hook も無出力で操作を通すので、終了コードと出力の空を見る
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "", result.stdout)

    def test_carry_skips_bot_wait(self):
        head = self._merge()
        self.assert_allowed(self._run(head))

    def test_without_carry_line_still_waits(self):
        head = self._merge()
        result = self._run(head, carry=False)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def test_carry_with_separator_left_still_waits(self):
        # 区切りの ======= を残した解消は引き継がない
        head = self._merge(resolution="test\n- feature\n=======\n- main\n")
        result = self._run(head)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def test_carry_for_other_sha_still_waits(self):
        self._merge()
        (self.repo / "later.txt").write_text("later\n", encoding="utf-8")
        _git(self.repo, "add", "later.txt")
        _git(self.repo, "commit", "-q", "-m", "after merge")
        later = _git(self.repo, "rev-parse", "HEAD")
        # merge の後に commit を積んだ HEAD は、第 1 親が from でないので引き継がない
        result = self._run(later)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def test_carry_with_high_still_waits(self):
        head = self._merge()
        result = self._run(head, high=1)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def test_carry_reason_is_shown_when_not_carried(self):
        # 引き継ぎを試して引き継げないときは、その理由と引き継ぎの案内を 通知の文に出す
        head = self._merge(extra={"added.txt": "not reviewed\n"})
        result = self._run(head)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        # 待つ場面の判定（lib/autonomy_pushback.py）は、通知文の先頭行のこの部分を読む
        self.assertIn("不足条件: review-wait-not-elapsed。", result.stdout.splitlines()[0])
        reason = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("review-wait-not-elapsed", reason)
        self.assertIn("Independent Review Carry: 引き継げない理由 衝突していないファイルが git の自動 merge の結果と違う", reason)
        self.assertIn(GUIDE, reason)

    def test_carry_reason_without_carry_line(self):
        head = self._merge()
        reason = json.loads(self._run(head, carry=False).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("review-wait-not-elapsed", reason)
        self.assertIn("Independent Review Carry: 引き継げない理由 Independent Review Carry が無い", reason)
        self.assertIn(GUIDE, reason)

    def test_carry_satisfies_independent_review_after_wait(self):
        # 待機の経過後は、引き継いだ独立レビューが独立レビューの要求を満たす
        head = self._merge(minutes_ago=60)
        self.assert_allowed(self._run(head, push_minutes_ago=41))

    def test_after_wait_without_carry_requires_independent_review(self):
        head = self._merge(minutes_ago=60)
        result = self._run(head, push_minutes_ago=41, carry=False)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("independent-review-missing", result.stdout)

    def test_after_wait_not_carried_requires_independent_review_with_reason(self):
        head = self._merge(extra={"added.txt": "not reviewed\n"}, minutes_ago=60)
        reason = json.loads(self._run(head, push_minutes_ago=41).stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("independent-review-missing", reason)
        self.assertIn("Independent Review Carry: 引き継げない理由", reason)
        self.assertIn(GUIDE, reason)

    def test_after_wait_with_high_still_requires_independent_review(self):
        # 引き継ぎの判定を呼ばない経路（high > 0）でも、hook は落ちずに不足として通知する
        head = self._merge(minutes_ago=60)
        result = self._run(head, push_minutes_ago=41, high=1)
        self.assertIn("independent-review-missing", result.stdout)
        # 引き継ぎを試せない場面（high > 0）には案内を出さない
        self.assertNotIn(GUIDE, result.stdout)

    def test_carry_with_medium_requires_disposition_at_head(self):
        head = self._merge()
        missing = self._run(head, medium=1)
        self.assertIn("medium-disposition-missing", missing.stdout)
        stale = self._run(head, medium=1, disposition_sha=self.reviewed)
        self.assertIn("medium-disposition-missing", stale.stdout)
        self.assert_allowed(self._run(head, medium=1, disposition_sha=head))


if __name__ == "__main__":
    unittest.main()

"""review-followup nudge hook: コマンドに UTF-8 で書けない文字があっても、解析結果を最後まで書き出す。

hook の python は解析結果を key ごとに stdout へ出す。push 先の branch に high surrogate（`\\ud800`）があると、
UTF-8 mode の surrogateescape でも書けずに UnicodeEncodeError になり、後に出す `root` が出ないまま終わって
いた（gh に問い合わせずに抜けていた）。merge gate・pre-push gate と同じ形で書く。branch 名は `\\uXXXX` に
置き換わるので実在の branch には当たらず、提案の有無は変わらない。
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _review_followup_nudge_support import _write_stub_gh, ReviewFollowupNudgeFixtureMixin


class ReviewFollowupNudgeEmitEncodingTests(ReviewFollowupNudgeFixtureMixin, unittest.TestCase):
    def test_unencodable_branch_keeps_push_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            args = Path(tmp) / "args.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter, args_file=args)
            result = self._run_hook(
                repo,
                "git push origin feature-\ud800",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            # root が届けば、push 先の branch（書けない文字は `\\uXXXX` に置き換わる）を gh に問い合わせる。
            self.assertTrue(counter.exists(), result.stdout + result.stderr)
            self.assertEqual(args.read_text(encoding="utf-8").strip(), "feature-\\ud800")

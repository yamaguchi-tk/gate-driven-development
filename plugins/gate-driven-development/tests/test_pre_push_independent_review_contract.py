"""Contract tests for pre-push gate step 13b — 独立レビュー証跡（2026-09-06）。

`standard` の push 前は「内部整合レーン 1 周 ＋ 独立レビュー 1 回」に置き換わった
（正本: `references/self-review-lanes.md` § リスク比例発火表 /
`references/independent-review.md`）。3 レーン自己周回は reviewer recall 実測で
確定欠陥を 1 件も拾えず `approved` を出したため、接地・敵対レーンの検出
責務を独立レビューへ移し、hook 側は `Independent Review` 行（sha 一致・`high: 0`）
だけを機械検査する。

fixture は `test_pre_push_gate_contract.py` の helper を **関数として借用**する
（継承すると親 class の全 test が本 module でも再実行されるため）。block reason の
allow-list / reason code 閉包検査は provider 登録の都合で親 module 側にある。
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import test_pre_push_gate_contract as _parent


class PrePushIndependentReviewContractTests(unittest.TestCase):
    # 借用元は class body 内でだけ解決する。module 名前空間に TestCase の別名を置くと
    # pytest が親 class を本 module でも収集し、親 test が二重実行される（実際に起きた）。
    _Base = _parent.PrePushGateContractTests

    _init_repo = _Base._init_repo
    _write_local_state = _Base._write_local_state
    _run_hook = _Base._run_hook
    _head_sha = _Base._head_sha
    _commit_extra = _Base._commit_extra
    _evidence_line = _Base._evidence_line
    _independent_review_line = _Base._independent_review_line
    _write_steering = _Base._write_steering

    def test_consecutive_clean_one_with_dry_yes_passes(self) -> None:
        """「2 連続」要件の撤廃側。内部整合レーン 1 周が clean（`consecutive_clean: 1`）
        で、`Independent Review` 行が揃っていれば standard でも通す。閾値を 2 へ戻す
        変異はここで KILL される（0 が不足として通知する側は親 module の step 12 test）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            head = self._head_sha(repo)
            self._write_steering(
                repo,
                task_size="standard",
                evidence=self._evidence_line(sha=head, dry="yes", consecutive_clean="1"),
            )

            result = self._run_hook(
                repo,
                "git push -u origin main",
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_step13b_standard_requires_independent_review_evidence(self) -> None:
        """standard は `Independent Review` 行（sha 一致・`high: 0`）を要求する。

        3 レーン自己周回は reviewer recall 実測で確定欠陥を 1 件も拾わず
        `approved` を出したため、接地・敵対の検出責務を独立レビューへ移した。
        欠落 / sha 不一致 / high>0 / blocking>0 の 4 分岐と正常系を 1 本で固定する。
        `blocking` は merge gate と受理集合を揃えるための分岐（独立レビュー #6 /
        2026-09-06。`high: 0 | blocking: 2` が push gate だけ素通りしていた）。
        """
        cases = (
            ("missing", "independent-review-missing"),
            ("stale", "independent-review-stale"),
            ("high", "independent-review-high"),
            ("blocking", "independent-review-high"),
            ("ok", None),
        )
        for kind, expected_code in cases:
            with self.subTest(case=kind), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                stale = self._head_sha(repo)
                head = self._commit_extra(repo, "feature.py")
                kwargs: dict[str, object] = {}
                if kind == "missing":
                    kwargs["auto_independent_review"] = False
                elif kind == "stale":
                    kwargs["independent_review"] = self._independent_review_line(sha=stale)
                elif kind == "high":
                    kwargs["independent_review"] = self._independent_review_line(
                        sha=head, high="2"
                    )
                elif kind == "blocking":
                    kwargs["independent_review"] = self._independent_review_line(
                        sha=head, high="0", blocking="2"
                    )
                self._write_steering(
                    repo,
                    task_size="standard",
                    evidence=self._evidence_line(sha=head, dry="yes", consecutive_clean="1"),
                    **kwargs,  # type: ignore[arg-type]
                )

                result = self._run_hook(
                    repo,
                    "git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                if expected_code is None:
                    self.assertEqual(result.stdout, "")
                else:
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse", result.stdout)
                    self.assertIn(expected_code, payload["hookSpecificOutput"]["additionalContext"])

    def test_step13b_exempt_task_sizes_pass_without_independent_review(self) -> None:
        """`quick (standard)` / `quick (express)` / `trivial` は step 13b を免除する
        （発火表と同じ境界。standard だけが独立レビューを要求する）。"""
        for task_size in ("quick (standard)", "quick (express)", "trivial"):
            with self.subTest(task_size=task_size), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                head = self._head_sha(repo)
                self._write_steering(
                    repo,
                    task_size=task_size,
                    evidence=self._evidence_line(sha=head, dry="no", consecutive_clean="0"),
                    auto_independent_review=False,
                )

                result = self._run_hook(
                    repo,
                    "git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()

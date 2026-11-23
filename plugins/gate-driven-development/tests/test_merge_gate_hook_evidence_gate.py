"""merge gate hook の承認判定（AC-2）/ 証跡ゲート（AC-1, AC-3）の契約テスト。

`Merge Approval` フィールド（PR 番号・HEAD SHA・鮮度）による承認判定と、
`Pre-Merge Review Recheck` / `Last Review Push At` / `Bot Review Received` /
`Independent Review` の証跡 4 点による通過 / 不足の通知の確定を、実 hook subprocess
経由で検査する。gate が「評価対象になるかどうか」（活性化）は
`test_merge_gate_hook_gate_activation.py` 側の関心事（`tests/test_merge_gate_hook.py`
分割）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _merge_gate_support import (
    _approval_line,
    _head_sha,
    _init_repo,
    _init_repo_with_commit_date,
    _run_hook,
    _write_evidence_state,
    _write_local_state,
)


class ApprovalJudgmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)

    def _run(self, approval_lines, command="gh pr merge 7", payload_extra=None):
        _write_local_state(self.repo, extra_lines=approval_lines)
        payload = {"tool_input": {"command": command}}
        payload.update(payload_extra or {})
        return _run_hook(payload, self.repo, self.home)

    def test_missing_merge_approval_blocks(self):
        result = self._run([])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_tab_newline_in_repo_flag_cannot_forge_is_merge_via_emit_channel(self):
        # A-1 (Task A advisory / gate #12): parse 結果は `\t` 区切り・改行終端の
        # プレーンテキストチャネルで hook 本体へ渡される。sanitize が無いと、
        # attacker が制御できる `-R` の値に `\t`/`\n` を混ぜることで emit() の
        # 出力に偽の追加行（`is_merge\tfalse`）を注入でき、後段の read ループが
        # 既に読んだ `is_merge=true` を無検査で false に上書きする（通知も
        # suppression ログも残らず gate ごと素通りする）。emit() が `\t`/`\n` を
        # 潰していれば注入は成立せず、証跡不足のまま通常どおり不足として通知される。
        result = self._run([], command='gh pr merge -R "a\nis_merge\tfalse" 7')
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout,
                       "is_merge の偽装が成立し、gate が無検査のまま素通りした")

    def test_malformed_pr_url_blocks_with_pr_target_unresolvable(self):
        # design.md § 対象 PR の 3 組解決: state.md の PR URL 不在/不正 →不足の通知。
        # active: true マーカーで gate 対象は成立させたうえで PR URL 自体を壊す。
        _write_local_state(
            self.repo, pr_url="not-a-url", extra_lines=[_approval_line(7, self.head)],
        )
        result = _run_hook({"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_pr_number_mismatch_blocks(self):
        result = self._run([_approval_line(7, self.head)], command="gh pr merge 999")
        self.assertIn("approval-pr-mismatch", result.stdout)

    def test_head_sha_mismatch_blocks(self):
        result = self._run([_approval_line(7, "0" * 40)])
        self.assertIn("approval-sha-mismatch", result.stdout)

    def test_stale_approval_blocks(self):
        result = self._run([_approval_line(7, self.head, minutes_ago=121)])
        self.assertIn("approval-stale", result.stdout)

    def test_fresh_matching_approval_passes_step7(self):
        # 120 分ちょうどの厳密な境界一致は使わない: このテストは full hook
        # subprocess（git init 込み）を経由するため、Python 側でタイムスタンプを
        # 計算してから bash 側の `date -u +%s` が実行されるまでの起動オーバーヘッド
        # （実行のたびに 120 分丁度を超えたり超えなかったりして flaky 化した）を境界一致に
        # 巻き込んでしまう。境界そのもの（120 分ちょうど = 通過 / 1 秒超過 = 不足の通知）は
        # オーバーヘッドの無い `gdd_mg_within_minutes` 直接呼び出しの契約テスト
        # （`test_within_minutes_at_exact_boundary_is_within` /
        # `test_within_minutes_one_second_over_boundary_is_not_within`）で別途固定済み。
        # ここでは「明確に鮮度内の承認なら step 7 で approval- 系 failure が出ない」
        # ことだけを見るため、境界から十分離れた値を使う。
        result = self._run([_approval_line(7, self.head, minutes_ago=1)])
        self.assertNotIn("approval-", result.stdout)

    def test_second_run_with_same_approval_is_not_blocked(self):
        # one-shot 廃止（ADR-14）の帰結を肯定側で固定する。同一 head SHA・
        # 鮮度内なら同じ Merge Approval 行で 2 回目も不足として通知されない
        # （design.md § Honest Limitations「厳密な one-shot は保証しない」）。
        # Step Group A3（証跡ゲート）は Merge Approval だけでなく
        # Pre-Merge Review Recheck / Last Review Push At / Bot Review Received も
        # 必須にするため、ここで allow を主張するには 4 field 全てを揃える必要がある
        # （欠けたまま不足の通知が無いことを主張すると常に
        # recheck-missing/review-push-missing/bot-review-flag-missing で失敗する）。
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines = [
            _approval_line(7, self.head),
            f"- Pre-Merge Review Recheck: {self.head} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head} | at: {now_iso}",
            f"- Bot Review Received: {self.head} | received: yes | at: {now_iso}",
        ]
        first = self._run(lines)
        self.assertNotIn('"hookEventName": "PreToolUse"', first.stdout)
        second = self._run(lines)
        self.assertNotIn('"hookEventName": "PreToolUse"', second.stdout)

    def test_missing_transcript_path_does_not_change_verdict(self):
        # hook が transcript に再依存する変異を KILL する
        lines = [_approval_line(7, self.head)]
        with_tp = self._run(lines, payload_extra={"transcript_path": "/nonexistent.jsonl"})
        without_tp = self._run(lines)
        self.assertEqual(
            '"hookEventName": "PreToolUse"' in with_tp.stdout,
            '"hookEventName": "PreToolUse"' in without_tp.stdout,
        )

class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head_sha = subprocess.run(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    def _run(self, extra_lines, extra_env=None):
        # 承認は state.md の Merge Approval 行で与える（ADR-14。transcript fixture は作らない）
        _write_evidence_state(
            self.repo,
            [_approval_line(7, self.head_sha)] + list(extra_lines),
        )
        payload = {"tool_input": {"command": "gh pr merge 7"}}
        return _run_hook(payload, self.repo, self.home, extra_env=extra_env)

    def _backdate_head_commit(self, minutes_ago):
        # `Last Review Push At` は merge-gate-evidence.sh 側で
        # `at >= HEAD の committer date` を要求する（push は commit の後に起きる、
        # という制約）。setUp の _init_repo は実時刻でコミットするため、そのままでは
        # 「review push が待機時間（40 分）以上前」という fixture を作れない
        # （at が HEAD committer date より前になり review-push-missing に化ける）。
        # ここで HEAD の committer date 自体を過去へ付け替え、self.head_sha を
        # amend 後の SHA で更新する。
        old_iso = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        env = dict(os.environ)
        env["GIT_COMMITTER_DATE"] = old_iso
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "--amend", "--no-edit", "--date", old_iso],
            check=True, env=env, capture_output=True, text=True,
        )
        self.head_sha = _head_sha(self.repo)

    def test_missing_recheck_blocks(self):
        result = self._run([])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("recheck-missing", result.stdout)

    # --- A-13: Independent Review 以外の4フィールドも Merge Approval と同じ
    # 3分岐（missing / unparsable / malformed）へ揃える。field 完全欠落は
    # 従来通り field 専用 code（recheck-missing 等）、必須 key 欠落は
    # evidence-unparsable、値ドメイン違反は evidence-malformed に分岐する。

    def test_recheck_present_but_missing_new_blocking_key_blocks_with_evidence_unparsable(self):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | at: {now_iso}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-unparsable", result.stdout)
        self.assertNotIn("recheck-missing", result.stdout)

    def test_recheck_non_numeric_new_blocking_blocks_with_evidence_malformed(self):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: abc | at: {now_iso}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-malformed", result.stdout)
        self.assertNotIn("recheck-missing", result.stdout)

    def test_review_push_present_but_missing_at_key_blocks_with_evidence_unparsable(self):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-unparsable", result.stdout)
        self.assertNotIn("review-push-missing", result.stdout)

    def test_review_push_at_before_head_commit_blocks_with_evidence_malformed(self):
        # merge-gate-evidence.sh の Last Review Push At 制約（at >= HEAD committer
        # date）。_init_repo は「今」でコミットするため、明確に過去の at は違反する。
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: 2020-01-01T00:00:00Z",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-malformed", result.stdout)
        self.assertNotIn("review-push-missing", result.stdout)

    def test_bot_review_present_but_missing_received_key_blocks_with_evidence_unparsable(self):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {now_iso}",
            f"- Bot Review Received: {self.head_sha} | at: {now_iso}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-unparsable", result.stdout)
        self.assertNotIn("bot-review-flag-missing", result.stdout)

    def test_bot_review_invalid_received_domain_blocks_with_evidence_malformed(self):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {now_iso}",
            f"- Bot Review Received: {self.head_sha} | received: maybe | at: {now_iso}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-malformed", result.stdout)
        self.assertNotIn("bot-review-flag-missing", result.stdout)

    def test_independent_review_present_but_missing_reviewer_key_blocks_with_evidence_unparsable(self):
        # 待機（40 分）経過後の独立レビュー fallback 経路で、Independent Review
        # 行自体は存在するが必須 key（reviewer）が欠落しているケース。
        self._backdate_head_commit(minutes_ago=60)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        old_iso = (datetime.now(timezone.utc) - timedelta(minutes=41)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {old_iso}",
            f"- Bot Review Received: {self.head_sha} | received: no | at: {old_iso}",
            f"- Independent Review: {self.head_sha} | context: diff-only | high: 0 | medium: 0 | at: {old_iso}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-unparsable", result.stdout)
        self.assertNotIn("independent-review-missing", result.stdout)

    def test_recheck_sha_mismatch_blocks(self):
        result = self._run([
            "- Pre-Merge Review Recheck: 0000000 | new_blocking: 0 | at: 2026-01-01T00:00:00Z",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("recheck-sha-mismatch", result.stdout)

    def test_recheck_new_blocking_nonzero_blocks(self):
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 2 | at: 2026-01-01T00:00:00Z",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("recheck-blocking", result.stdout)

    def test_bot_received_yes_skips_independent_review(self):
        # recheck 鮮度（10 分）判定は実行時の実時刻基準（merge-gate-evidence.sh の
        # `date -u +%s`）。固定した過去日時（旧: 2026-01-01T00:00:00Z）は実時刻から
        # 見て常に鮮度切れになり recheck-stale で誤爆する。動的な「今」を使う。
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {now_iso}",
            f"- Bot Review Received: {self.head_sha} | received: yes | at: {now_iso}",
        ])
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_bot_received_no_wait_not_elapsed_blocks(self):
        """Independent Review が**無い**状態で待機未経過なら不足として通知（待機免除の対象外）。

        待機免除（`test_bot_received_no_clean_independent_review_skips_wait`）は
        Independent Review が HEAD で high 0 / blocking 0 のときだけ効く。この
        fixture は Independent Review 行を置かないので、従来どおり
        `review-wait-not-elapsed` になる（挙動は不変）。
        """
        # 同上: recheck 鮮度は実時刻基準のため動的な「今」を使う。
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {now_iso}",
            f"- Bot Review Received: {self.head_sha} | received: no | at: {now_iso}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def _run_wait_not_elapsed_with_ir(self, ir_line):
        # 待機未経過（push は「今」= 経過 0 分）で received: no。Independent Review
        # の内容だけを差し替えて、待機免除の成立条件を切り分ける。
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {now_iso}",
            f"- Bot Review Received: {self.head_sha} | received: no | at: {now_iso}",
            ir_line.format(now_iso=now_iso),
        ])

    def test_bot_received_no_clean_independent_review_skips_wait(self):
        # 待機の目的は bot レビューの着弾待ちなので、独立レビューが HEAD で
        # high 0 / blocking 0 なら経過 0 分でも待たせない（待機経過後に要求される
        # のは同じ Independent Review であり、待つ意味が無い）。
        result = self._run_wait_not_elapsed_with_ir(
            f"- Independent Review: {self.head_sha} | reviewer: gdd-completion-reviewer "
            "| context: diff-only | high: 0 | medium: 0 | blocking: 0 | at: {now_iso}"
        )
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_bot_received_no_stale_independent_review_still_waits(self):
        # 別 sha の独立レビューは HEAD を保証しないので待機を免除しない。
        result = self._run_wait_not_elapsed_with_ir(
            "- Independent Review: 0000000 | reviewer: gdd-completion-reviewer "
            "| context: diff-only | high: 0 | medium: 0 | blocking: 0 | at: {now_iso}"
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def test_bot_received_no_high_finding_independent_review_still_waits(self):
        # high>0 は独立レビューが通っていない状態。待機を免除しない
        # （independent-review-missing へ先行させず、従来どおり待機を出す）。
        result = self._run_wait_not_elapsed_with_ir(
            f"- Independent Review: {self.head_sha} | reviewer: gdd-completion-reviewer "
            "| context: diff-only | high: 1 | medium: 0 | blocking: 0 | at: {now_iso}"
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-wait-not-elapsed", result.stdout)

    def test_wait_elapsed_without_independent_review_blocks(self):
        # recheck 鮮度（10 分）と review push の待機経過（40 分）は相反する窓なので
        # 同一 timestamp を使い回さない: recheck は実時刻基準で鮮度内、review push は
        # 40 分超過させる。review push を過去に置くには HEAD の committer date も
        # それより前に付け替える必要がある（merge-gate-evidence.sh が
        # `Last Review Push At.at >= HEAD committer date` を要求するため）。
        self._backdate_head_commit(minutes_ago=60)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        old_iso = (datetime.now(timezone.utc) - timedelta(minutes=41)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {old_iso}",
            f"- Bot Review Received: {self.head_sha} | received: no | at: {old_iso}",
        ])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("independent-review-missing", result.stdout)

    def test_wait_elapsed_with_clean_independent_review_allows(self):
        # 同上: recheck は鮮度内（実時刻基準）、review push は 40 分超過させて
        # 独立レビュー fallback 経路に入れる。HEAD committer date もそれより前に
        # 付け替える。
        self._backdate_head_commit(minutes_ago=60)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        old_iso = (datetime.now(timezone.utc) - timedelta(minutes=41)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        result = self._run([
            f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            f"- Last Review Push At: {self.head_sha} | at: {old_iso}",
            f"- Bot Review Received: {self.head_sha} | received: no | at: {old_iso}",
            f"- Independent Review: {self.head_sha} | reviewer: gdd-completion-reviewer | context: diff-only | high: 0 | medium: 0 | at: {old_iso}",
        ])
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_head_committer_date_unresolvable_blocks_review_push(self):
        # T-3 gate #9 advisory A-1 の pin: git log 失敗（committer date 取得不能）を
        # fake git シムで再現する。空文字を merge-gate-evidence.sh へ渡して
        # 制約検査ごと skip させず、review-push-missing で不足として通知すること。
        fake_bin = self.tmp / "fake-bin"
        fake_bin.mkdir()
        real_git = shutil.which("git")
        fake_git = fake_bin / "git"
        fake_git.write_text(
            "#!/usr/bin/env bash\n"
            'if [[ "$1" == "log" ]]; then exit 1; fi\n'
            f'exec "{real_git}" "$@"\n'
        )
        fake_git.chmod(0o755)
        now_iso = "2026-01-01T00:00:00Z"
        result = self._run(
            [
                f"- Pre-Merge Review Recheck: {self.head_sha} | new_blocking: 0 | at: {now_iso}",
            ],
            extra_env={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("review-push-missing", result.stdout)


class BlockingCategoryJudgmentTests(unittest.TestCase):
    """design.md § テスト方針 1/2/3/3b（AC-3/AC-4/AC-5）を fixture 化する。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        old45 = (datetime.now(timezone.utc) - timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.repo = _init_repo_with_commit_date(self.tmp, old45)
        self.head = _head_sha(self.repo)
        self.old41 = (datetime.now(timezone.utc) - timedelta(minutes=41)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    def _base_lines(self):
        return [
            _approval_line(7, self.head),
            f"- Pre-Merge Review Recheck: {self.head} | new_blocking: 0 | at: "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            f"- Last Review Push At: {self.head} | at: {self.old41}",
            f"- Bot Review Received: {self.head} | received: no | at: {self.old41}",
        ]

    def _run_with_ir(self, ir_line, extra=()):
        _write_evidence_state(self.repo, self._base_lines() + [ir_line] + list(extra))
        return _run_hook({"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home)

    def test_case_a_high0_medium3_blocking0_with_disposition_allows(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 3 | blocking: 0 | at: {self.old41}")
        disp = (f"- Medium Disposition: {self.head} | count: 3 | recorded: accepted "
                f"| note: 受容済み | at: {self.old41}")
        result = self._run_with_ir(ir, extra=[disp])
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_case_b_high0_medium1_blocking1_blocks(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 1 | blocking: 1 | at: {self.old41}")
        result = self._run_with_ir(ir)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("independent-review-missing", result.stdout)

    def test_case_c_high1_medium0_blocking0_blocks(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 1 | medium: 0 | blocking: 0 | at: {self.old41}")
        result = self._run_with_ir(ir)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("independent-review-missing", result.stdout)

    def test_medium_disposition_unresolvable_sha_blocks(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 2 | blocking: 0 | at: {self.old41}")
        disp = ("- Medium Disposition: 0000000 | count: 2 | recorded: accepted "
                f"| note: old | at: {self.old41}")
        result = self._run_with_ir(ir, extra=[disp])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("medium-disposition-missing", result.stdout)

    def test_medium_disposition_resolvable_but_stale_sha_blocks(self):
        # M-7: `0000000`（unresolvable）だけでなく、実在するが HEAD ではない
        # 古い commit の sha でも不足として通知することを確認する（存在検査だけでなく
        # HEAD 一致検査そのものを固定する。退行注入で SURVIVED だった箇所）。
        old_head = self.head
        (self.repo / "f2.txt").write_text("y")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-q", "-m", "second"],
            check=True,
            env={**os.environ, "GIT_AUTHOR_DATE": self.old41, "GIT_COMMITTER_DATE": self.old41},
        )
        self.head = _head_sha(self.repo)
        self.assertNotEqual(old_head, self.head)
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 2 | blocking: 0 | at: {self.old41}")
        disp = (f"- Medium Disposition: {old_head} | count: 2 | recorded: accepted "
                f"| note: stale but resolvable | at: {self.old41}")
        result = self._run_with_ir(ir, extra=[disp])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("medium-disposition-missing", result.stdout)

    def test_medium_disposition_count_mismatch_blocks(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 3 | blocking: 0 | at: {self.old41}")
        disp = (f"- Medium Disposition: {self.head} | count: 1 | recorded: accepted "
                f"| note: 不一致 | at: {self.old41}")
        result = self._run_with_ir(ir, extra=[disp])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("medium-disposition-missing", result.stdout)

    # --- Medium Disposition も Merge Approval と同じ3分岐（missing / unparsable /
    # malformed）へ揃える。field 完全欠落は従来通り medium-disposition-missing、
    # 必須 key 欠落は evidence-unparsable、値ドメイン違反は evidence-malformed。

    def test_medium_disposition_present_but_missing_count_key_blocks_with_evidence_unparsable(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 2 | blocking: 0 | at: {self.old41}")
        disp = (f"- Medium Disposition: {self.head} | recorded: accepted "
                f"| note: 受容済み | at: {self.old41}")
        result = self._run_with_ir(ir, extra=[disp])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-unparsable", result.stdout)
        self.assertIn("不足 key: Medium Disposition", result.stdout)
        self.assertNotIn("medium-disposition-missing", result.stdout)

    def test_medium_disposition_non_numeric_count_blocks_with_evidence_malformed(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 2 | blocking: 0 | at: {self.old41}")
        disp = (f"- Medium Disposition: {self.head} | count: abc | recorded: accepted "
                f"| note: 受容済み | at: {self.old41}")
        result = self._run_with_ir(ir, extra=[disp])
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-malformed", result.stdout)
        self.assertIn("不正 key: Medium Disposition", result.stdout)
        self.assertNotIn("medium-disposition-missing", result.stdout)

    def test_legacy_blocking_key_absent_high1_blocks(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 1 | medium: 0 | at: {self.old41}")
        result = self._run_with_ir(ir)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_legacy_blocking_key_absent_high0_medium0_allows(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 0 | at: {self.old41}")
        result = self._run_with_ir(ir)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_legacy_blocking_key_absent_logs_suppression(self):
        # M-6: 旧書式（`blocking` key 欠落）を寛容側の既定で通した経路は
        # design.md § D5 / self-review-lanes.md:132 が唯一の可視化と明記する
        # suppression ログを残す（gate 判定の通過 / 不足の通知を問わず記録する）。
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 0 | at: {self.old41}")
        self._run_with_ir(ir)
        log = self.home / ".claude" / ".gdd-hook-state" / "merge-gate-suppressed.log"
        self.assertTrue(log.exists())
        self.assertIn("legacy-evidence-no-blocking-field", log.read_text())

    def test_blocking_key_present_does_not_log_legacy_suppression(self):
        # 境界テスト: `blocking` key がある通常経路では旧書式ログを残さない
        # （M-6 修正が過剰発火しないことの確認）。
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 0 | blocking: 0 | at: {self.old41}")
        self._run_with_ir(ir)
        log = self.home / ".claude" / ".gdd-hook-state" / "merge-gate-suppressed.log"
        if log.exists():
            self.assertNotIn("legacy-evidence-no-blocking-field", log.read_text())

    def test_near_miss_key_blockin_is_malformed(self):
        ir = (f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
              f"| context: diff-only | high: 0 | medium: 1 | blockin: 1 | at: {self.old41}")
        result = self._run_with_ir(ir)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("evidence-malformed", result.stdout)


class LegacyEvidenceLogFailureContainmentTests(unittest.TestCase):
    """`legacy-evidence-no-blocking-field` のログ呼び出しが死んでも証跡検査へ到達する。

    design.md § ログ呼び出しの failure containment / adr.md ADR-1 の同型ケース。
    `test_merge_gate_hook_gate_activation.py` の `SuppressionLogFailureContainmentTests`
    が `unowned-active-marker-demoted`（活性化経路）を固定しているのに対し、
    こちらは証跡経路の呼び出しを固定する。両者は「記録後も処理を続ける」2 箇所で、
    ここで即死すると hook が無出力で終わり、PreToolUse の契約上「通知を返さなかった」
    = 素通りになる。

    `_mg_log_suppressed` の死に方は 2 通り: `HOME` 未設定（`set -u`）と、
    `shasum` / `sha1sum` 双方の失敗（`_repo_id="$(... | shasum ...)"` が `pipefail`
    で非 0）。後者は `|| true` だけでも捕まる（bash は `||` の左辺の関数呼び出しの
    中では errexit を抑止する）が、前者は捕まらない。subshell が load-bearing なのは
    `HOME` 側であり、両方を測らないと subshell を外す mutation が生き残る。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        old45 = (datetime.now(timezone.utc) - timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.repo = _init_repo_with_commit_date(self.tmp, old45)
        self.head = _head_sha(self.repo)
        self.old41 = (datetime.now(timezone.utc) - timedelta(minutes=41)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        # 旧書式（`blocking` key 欠落）× `high: 1` = 監査記録を残したうえで
        # `independent-review-missing` を返すべき証跡。ログ記録が死んでも
        # この不足の通知が出ることが、containment の観測点になる。
        _write_evidence_state(self.repo, [
            _approval_line(7, self.head),
            f"- Pre-Merge Review Recheck: {self.head} | new_blocking: 0 | at: "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            f"- Last Review Push At: {self.head} | at: {self.old41}",
            f"- Bot Review Received: {self.head} | received: no | at: {self.old41}",
            f"- Independent Review: {self.head} | reviewer: gdd-completion-reviewer "
            f"| context: diff-only | high: 1 | medium: 0 | at: {self.old41}",
        ])

    def _assert_reached_evidence_gate(self, result):
        self.assertEqual(
            result.returncode, 0,
            f"hook が非 0 で落ちている（無出力素通り）: stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("independent-review-missing", result.stdout)

    def test_shasum_failure_still_reaches_evidence_gate(self):
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
        self._assert_reached_evidence_gate(result)

    def test_unset_home_still_reaches_evidence_gate(self):
        # `HOME` も `GDD_HOOK_STATE_DIR` も無い環境。`_mg_log_suppressed` の
        # `local _state_dir="${GDD_HOOK_STATE_DIR:-${HOME}/.claude/.gdd-hook-state}"`
        # が `set -u` で即死する経路で、`|| true` では捕まえられない。
        result = _run_hook(
            {"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home,
            drop_env=("HOME", "GDD_HOOK_STATE_DIR"),
        )
        self._assert_reached_evidence_gate(result)

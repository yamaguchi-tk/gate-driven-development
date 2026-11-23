"""merge gate hook が出す block reason の品質（F-3/F-4）と復旧要素の契約テスト。

`_merge_gate_block_reason_samples()` は design.md § reason code カタログの全 code を
実 hook subprocess 経由で到達させる fixture provider で、
`_block_reason_support.register_block_reason_provider()` へ登録することで
hook 横断の復旧要素検査（`test_hook_block_reason_recovery_contract.py`）からも
再利用される。reason 文言そのものの品質（アクション句・観測値・kill-switch 案内・
masking allowlist）を検査するのがこのファイルの責務（`tests/test_merge_gate_hook.py`
分割）。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _block_reason_support import (
    BlockReasonSample,
    _extract_shell_constant,
    register_block_reason_provider,
)
from _merge_gate_support import (
    HOOK_SCRIPT,
    LIB_DIR,
    _approval_line,
    _head_sha,
    _init_named_repo,
    _init_repo,
    _init_repo_with_commit_date,
    _new_full_evidence_repo,
    _new_marker_only_repo,
    _run_hook,
    _write_evidence_state,
    _write_local_state,
    _write_state,
    _write_two_done_steerings,
)


def _merge_gate_block_reason_samples() -> list:
    """hook 横断 contract 用の fixture provider。

    design.md § reason code カタログ「fixture provider は上表の全 code について
    到達可能な sample を返す」に従い、全 code を個別に踏む（RF-1 remediation で
    `pr-url-unrecorded` を追加）。`FAILURES` 配列 +
    `${FAILURES[0]}` 展開で動的に組み立てる code は
    `_block_reason_support.reason_codes_by_hook()` 側の `FAILURES\\+=\\(...\\)` 抽出
    （Step Group A5 で追加）と対になっている。
    """
    samples: list[BlockReasonSample] = []

    def _sample(code, tool_command, repo, home, forbidden_extra=(), extra_env=None):
        result = _run_hook({"tool_input": {"command": tool_command}}, repo, home, extra_env=extra_env)
        samples.append(BlockReasonSample(
            code=code, reason=result.stdout,
            forbidden=(str(repo),) + forbidden_extra,
        ))

    # --- gate 到達前の構造的失敗（kill-switch を出口として案内する family） ---

    # repo-root-unresolvable: hook プロセスの cwd が git repo ですらなく、実行先
    # （cd 先）も確定できない（実在しない）。
    tmp = Path(tempfile.mkdtemp())
    home = tmp / "home"
    (home / ".claude").mkdir(parents=True)
    non_repo = tmp / "non-repo"
    non_repo.mkdir()
    _sample("repo-root-unresolvable", f"cd {tmp}/no-such-dir && gh pr merge 1", non_repo, home)

    # head-unresolvable: git repo だが commit が 1 つも無いため HEAD を解決できない。
    tmp2 = Path(tempfile.mkdtemp())
    home2 = tmp2 / "home"
    (home2 / ".claude").mkdir(parents=True)
    empty_repo = tmp2 / "repo"
    empty_repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=empty_repo, check=True)
    _write_local_state(empty_repo)
    _sample("head-unresolvable", "gh pr merge 7", empty_repo, home2, ("20260101-demo",))

    # state-unreadable: steering は解決されるが state.md の読み取り権限が無い。
    tmp4 = Path(tempfile.mkdtemp())
    home4 = tmp4 / "home"
    (home4 / ".claude").mkdir(parents=True)
    repo4 = _init_repo(tmp4)
    state_path4 = _write_local_state(repo4)
    state_path4.chmod(0o000)
    try:
        _sample("state-unreadable", "gh pr merge 7", repo4, home4, ("20260101-demo",))
    finally:
        state_path4.chmod(0o644)

    # parse-error: `gh pr merge` と分かった後にコマンド解析が完走できない
    # （python3 が動かない環境）。判定材料が無いので fail-closed（AC-10）。
    tmp4a = Path(tempfile.mkdtemp())
    home4a = tmp4a / "home"
    (home4a / ".claude").mkdir(parents=True)
    repo4a = _init_repo(tmp4a)
    _write_local_state(repo4a)
    shim_dir4a = tmp4a / "bin"
    shim_dir4a.mkdir()
    (shim_dir4a / "python3").write_text("#!/bin/sh\nexit 127\n")
    (shim_dir4a / "python3").chmod(0o755)
    _sample("parse-error", "gh pr merge 7", repo4a, home4a, ("20260101-demo",),
            extra_env={"PATH": f"{shim_dir4a}:{os.environ['PATH']}"})

    # pr-url-unrecorded: steering は解決でき state.md も読めるが `PR URL` が無い
    # （RF-1 / AC-10。`active: false` は `done` 後の最頻状態）。
    tmp4b = Path(tempfile.mkdtemp())
    home4b = tmp4b / "home"
    (home4b / ".claude").mkdir(parents=True)
    repo4b = _init_repo(tmp4b)
    _write_state(repo4b, active=False, pr_url=None)
    _sample("pr-url-unrecorded", "gh pr merge 7", repo4b, home4b, ("20260101-demo",))

    # steering-ambiguous: done 済み steering が 2 件あり正本を決められない
    # （gate #14 M-4 / AC-10）。gate #15 M-1 以降、この code は「gate 対象では
    # あるが正本が決まらない」形でだけ出る（`active: true` × 対象 PR 不一致）。
    tmp4c = Path(tempfile.mkdtemp())
    home4c = tmp4c / "home"
    (home4c / ".claude").mkdir(parents=True)
    repo4c = _init_repo(tmp4c)
    _write_two_done_steerings(repo4c, active=True)
    _sample("steering-ambiguous", "gh pr merge 7", repo4c, home4c,
            ("20260101-demo", "20260102-followup"))

    # --- 対象 PR の 3 組解決（1 code） ---

    # pr-target-unresolvable: state.md の PR URL 自体が書式不正。
    tmp5 = Path(tempfile.mkdtemp())
    home5 = tmp5 / "home"
    (home5 / ".claude").mkdir(parents=True)
    repo5 = _init_repo(tmp5)
    _write_local_state(repo5, pr_url="not-a-url")
    _sample("pr-target-unresolvable", "gh pr merge 7", repo5, home5, ("20260101-demo",))

    # --- 承認判定（4 code） ---

    def _approval_repo():
        t = Path(tempfile.mkdtemp())
        h = t / "home"
        (h / ".claude").mkdir(parents=True)
        r = _init_repo(t)
        return h, r, _head_sha(r)

    # approval-missing: Merge Approval 行が無い。
    home6, repo6, head6 = _approval_repo()
    _write_local_state(repo6)
    _sample("approval-missing", "gh pr merge 7", repo6, home6, ("20260101-demo",))

    # approval-pr-mismatch: 承認 PR 番号とマージ対象 PR 番号が食い違う。
    home7, repo7, head7 = _approval_repo()
    _write_local_state(repo7, extra_lines=[_approval_line(7, head7)])
    _sample("approval-pr-mismatch", "gh pr merge 999", repo7, home7, ("20260101-demo",))

    # approval-sha-mismatch: 承認後に 1 commit 積んで HEAD が動いた形状。
    home8, repo8, head8 = _approval_repo()
    _write_local_state(repo8, extra_lines=[_approval_line(7, "0" * 40)])
    _sample("approval-sha-mismatch", "gh pr merge 7", repo8, home8, ("20260101-demo",))

    # approval-stale: 承認鮮度上限（120 分）を超過。
    home9, repo9, head9 = _approval_repo()
    _write_local_state(repo9, extra_lines=[_approval_line(7, head9, minutes_ago=121)])
    _sample("approval-stale", "gh pr merge 7", repo9, home9, ("20260101-demo",))

    # --- 証跡検査（9 code） ---

    def _evidence_repo(extra_lines):
        t = Path(tempfile.mkdtemp())
        h = t / "home"
        (h / ".claude").mkdir(parents=True)
        r = _init_repo(t)
        head = _head_sha(r)
        _write_evidence_state(r, [_approval_line(7, head)] + list(extra_lines))
        return h, r, head

    # recheck-missing: Pre-Merge Review Recheck 行が無い。
    home10, repo10, head10 = _evidence_repo([])
    _sample("recheck-missing", "gh pr merge 7", repo10, home10, ("20260101-demo",))

    # recheck-sha-mismatch: recheck sha が HEAD と食い違う。
    home11, repo11, head11 = _evidence_repo([
        "- Pre-Merge Review Recheck: 0000000 | new_blocking: 0 | at: 2026-01-01T00:00:00Z",
    ])
    _sample("recheck-sha-mismatch", "gh pr merge 7", repo11, home11, ("20260101-demo",))

    def _new_repo(commit_date_iso=None):
        t = Path(tempfile.mkdtemp())
        h = t / "home"
        (h / ".claude").mkdir(parents=True)
        r = _init_repo(t) if commit_date_iso is None else _init_repo_with_commit_date(t, commit_date_iso)
        return h, r, _head_sha(r)

    def _fresh_recheck_line(sha):
        at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return f"- Pre-Merge Review Recheck: {sha} | new_blocking: 0 | at: {at}"

    # recheck-blocking: new_blocking が 0 でない（recheck 自体は sha 一致・新鮮）。
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    home12, repo12, head12 = _new_repo()
    _write_evidence_state(repo12, [
        _approval_line(7, head12),
        f"- Pre-Merge Review Recheck: {head12} | new_blocking: 2 | at: {now_iso}",
    ])
    _sample("recheck-blocking", "gh pr merge 7", repo12, home12, ("20260101-demo",))

    # recheck-stale: recheck.at が鮮度上限（10 分）を超過。
    old15 = (datetime.now(timezone.utc) - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
    home13, repo13, head13 = _new_repo()
    _write_evidence_state(repo13, [
        _approval_line(7, head13),
        f"- Pre-Merge Review Recheck: {head13} | new_blocking: 0 | at: {old15}",
    ])
    _sample("recheck-stale", "gh pr merge 7", repo13, home13, ("20260101-demo",))

    # review-push-missing: recheck は新鮮・有効だが Last Review Push At が無い。
    home14, repo14, head14 = _new_repo()
    _write_evidence_state(repo14, [_approval_line(7, head14), _fresh_recheck_line(head14)])
    _sample("review-push-missing", "gh pr merge 7", repo14, home14, ("20260101-demo",))

    # bot-review-flag-missing: recheck + push は揃うが Bot Review Received が無い。
    home15, repo15, head15 = _new_repo()
    now_iso15 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_evidence_state(repo15, [
        _approval_line(7, head15),
        _fresh_recheck_line(head15),
        f"- Last Review Push At: {head15} | at: {now_iso15}",
    ])
    _sample("bot-review-flag-missing", "gh pr merge 7", repo15, home15, ("20260101-demo",))

    # review-wait-not-elapsed: push 直後（経過 0 分）で received: no。
    # Independent Review は置かない（HEAD で high 0 の独立レビューがあると
    # 待機が免除され、この code へ到達しない）。
    home16, repo16, head16 = _new_repo()
    now_iso16 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_evidence_state(repo16, [
        _approval_line(7, head16),
        _fresh_recheck_line(head16),
        f"- Last Review Push At: {head16} | at: {now_iso16}",
        f"- Bot Review Received: {head16} | received: no | at: {now_iso16}",
    ])
    _sample("review-wait-not-elapsed", "gh pr merge 7", repo16, home16, ("20260101-demo",))

    # independent-review-missing: 待機（40 分）は経過済みだが独立レビューが無い。
    # HEAD 自体を 45 分前へ backdate し、recheck は「今」新鮮、push は「41 分前」
    # （HEAD backdate より後 = A-1 pin を満たす）にすることで、鮮度 10 分と
    # 待機 40 分という相反する 2 つの窓を単一シナリオで両立させる。
    old45 = (datetime.now(timezone.utc) - timedelta(minutes=45)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old41 = (datetime.now(timezone.utc) - timedelta(minutes=41)).strftime("%Y-%m-%dT%H:%M:%SZ")
    home17, repo17, head17 = _new_repo(commit_date_iso=old45)
    _write_evidence_state(repo17, [
        _approval_line(7, head17),
        _fresh_recheck_line(head17),
        f"- Last Review Push At: {head17} | at: {old41}",
        f"- Bot Review Received: {head17} | received: no | at: {old41}",
    ])
    _sample("independent-review-missing", "gh pr merge 7", repo17, home17, ("20260101-demo",))

    # medium-disposition-missing: high 0 / blocking 0 / medium >0 だが
    # Medium Disposition が未記録。
    home17a, repo17a, head17a = _new_repo(commit_date_iso=old45)
    _write_evidence_state(repo17a, [
        _approval_line(7, head17a),
        _fresh_recheck_line(head17a),
        f"- Last Review Push At: {head17a} | at: {old41}",
        f"- Bot Review Received: {head17a} | received: no | at: {old41}",
        f"- Independent Review: {head17a} | reviewer: gdd-completion-reviewer "
        f"| context: diff-only | high: 0 | medium: 2 | blocking: 0 | at: {old41}",
    ])
    _sample("medium-disposition-missing", "gh pr merge 7", repo17a, home17a, ("20260101-demo",))

    # evidence-unparsable: Merge Approval に必須 key（evidence）が無い。
    home18, repo18, head18 = _new_repo()
    at18 = datetime.now(timezone.utc).isoformat()
    _write_local_state(repo18, extra_lines=[
        f"- Merge Approval: PR #7 / head {head18} | approved_at: {at18}",
    ])
    _sample("evidence-unparsable", "gh pr merge 7", repo18, home18, ("20260101-demo",))

    # evidence-malformed: Merge Approval の先頭 segment が書式違反。
    home19, repo19, _head19 = _new_repo()
    at19 = datetime.now(timezone.utc).isoformat()
    _write_local_state(repo19, extra_lines=[
        f"- Merge Approval: PR #abc / head xyz | evidence: x | approved_at: {at19}",
    ])
    _sample("evidence-malformed", "gh pr merge 7", repo19, home19, ("20260101-demo",))

    # untrusted-root-unverified: marker あり・steering 無しの repo を
    # `cd <repo> && gh pr merge 7` で指す形（AC-13/AC-14）。
    tmp20 = Path(tempfile.mkdtemp())
    home20 = tmp20 / "home"
    (home20 / ".claude").mkdir(parents=True)
    non_repo20 = tmp20 / "not-a-repo"
    non_repo20.mkdir()
    untrusted_repo20 = _init_named_repo(tmp20, "untrusted-repo")
    (untrusted_repo20 / ".claude").mkdir(parents=True)
    (untrusted_repo20 / ".claude" / "gdd-dev.local.md").write_text("active: false\n")
    _sample(
        "untrusted-root-unverified",
        f"cd {untrusted_repo20} && gh pr merge 7",
        non_repo20, home20,
        forbidden_extra=(str(untrusted_repo20), "20260101-demo"),
    )

    return samples

register_block_reason_provider(HOOK_SCRIPT, _merge_gate_block_reason_samples)

class MergeGateRecoveryElementRegressionTests(unittest.TestCase):
    def test_gdd_mg_recovery_core_literal_break_is_detected(self):
        literal = _extract_shell_constant("GDD_MG_RECOVERY_CORE")
        self.assertIn("self-review-lanes.md", literal)

GATE_FAILURE_CODES = frozenset(
    {"state-unreadable", "head-unresolvable", "repo-root-unresolvable",
     # コマンド解析が完走しない（python3 不在 / 不正 JSON / import 失敗）。gate 側の
     # 故障なので、出口として kill-switch を案内する family に入れる。
     "parse-error",
     # RF-1: gate 対象かどうかを判定できない状態。誤爆の逃がし口が kill-switch
     # 1 本である以上、reason にその出口を書く（policy 違反の family ではない）。
     "pr-url-unrecorded",
     # gate #14 M-4: steering の正本が決まらない（done 候補 2 件以上）。同上。
     "steering-ambiguous",
     # AC-13/AC-14: untrusted 由来 root で gate 起動根拠が無い経路。同上。
     "untrusted-root-unverified"}
)

class PrTargetMismatchKillSwitchHintTests(unittest.TestCase):
    """`pr-target-unresolvable` の gate 故障系 instance が kill-switch を案内するか。

    同じ code が 2 つの family で使われる（gate 故障系 = root != 実行先 / 解決不能、
    policy 違反系 = state.md の PR URL 欠落を含む全件列挙）ため、
    `test_hook_block_reason_recovery_contract.py` の code 単位の family 表では
    分類できない。gate 故障系の instance だけをここで固定する。

    この経路は「復旧手順が原理的に実行不能な環境」（プロセス cwd も payload cwd も
    非 git）でも発火しうるので、唯一の出口である kill-switch を落とすと人間は
    hook 本体を編集するしかなくなる（独立レビュー 2 巡目 medium）。
    """

    def test_root_vs_execution_target_mismatch_carries_the_kill_switch_hint(self):
        hint = _extract_shell_constant("GDD_MG_KILL_SWITCH_HINT")
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_full_evidence_repo(parent, "root")
            other = _new_marker_only_repo(parent, "other")
            result = _run_hook(
                {"tool_input": {"command": f"cd {other} && gh pr merge 7"}},
                root,
                parent / "home",
            )
            reason = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("pr-target-unresolvable", reason)
            self.assertIn(hint, reason)


class BlockReasonQualityTests(unittest.TestCase):
    """F-3 / F-4: reason code 別のアクション・観測値・kill-switch の contract。"""

    @classmethod
    def setUpClass(cls):
        cls.samples = _merge_gate_block_reason_samples()
        cls.reasons = {}
        for sample in cls.samples:
            # hook が不足の通知を返さなかった sample を「JSON として壊れている」で
            # 落とすと、どの code がなぜ落ちたかが出力に残らない（setUpClass の
            # 例外は全 test を ERROR にするだけで、sample 識別子も hook の
            # stdout/stderr も失われる）。実測: 実装へ mutation を当てたとき
            # 7 ERROR だけが出て原因の特定に別途 1 周期を要した。
            try:
                payload = json.loads(sample.reason)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"code={sample.code!r} の hook 出力が JSON ではない: {exc}\n"
                    f"raw={sample.reason!r}"
                ) from exc
            cls.reasons[sample.code] = payload["hookSpecificOutput"]["additionalContext"]
        cls.kill_switch_hint = _extract_shell_constant("GDD_MG_KILL_SWITCH_HINT")
        cls.recovery_core = _extract_shell_constant("GDD_MG_RECOVERY_CORE")

    def _action_clause(self, code):
        reason = self.reasons[code]
        head = reason.split("）: ", 1)[1]
        return head.split("。", 1)[0]

    def test_every_code_has_a_distinct_action_clause(self):
        # F-3: policy 系 13 code が 1 文へ潰れていた（code 15 と 16 の区別が消えた）。
        clauses = {code: self._action_clause(code) for code in self.reasons}
        self.assertEqual(
            len(set(clauses.values())), len(clauses),
            f"reason code ごとに異なるアクションを出すこと: {clauses}",
        )

    def test_action_precedes_recovery_elements(self):
        # design.md § Delivery Channel Rendering Check の語順原則。
        for code, reason in sorted(self.reasons.items()):
            with self.subTest(code=code):
                clause = self._action_clause(code)
                # 命令形（動詞）で終わること = 末尾切り詰めで最初に失うのが
                # アクションにならない語順であることの機械検査。
                self.assertIn(
                    "ください", clause,
                    f"{code}: 先頭が命令形のアクション句になっていない / clause={clause}",
                )
                tail = self.kill_switch_hint if code in GATE_FAILURE_CODES else self.recovery_core
                self.assertIn(tail, reason)
                self.assertLess(reason.index(clause), reason.index(tail))

    def test_gate_failure_codes_offer_the_kill_switch(self):
        # F-4: gate 側の故障 4 code にこそ出口を示す（design.md § block reason の復旧要素）。
        for code in sorted(GATE_FAILURE_CODES):
            with self.subTest(code=code):
                self.assertIn(self.kill_switch_hint, self.reasons[code])

    def test_policy_codes_do_not_mention_the_kill_switch(self):
        # 「kill-switch の明示は code 14 以降に限る」（policy 違反には書かない）。
        for code, reason in sorted(self.reasons.items()):
            if code in GATE_FAILURE_CODES:
                continue
            with self.subTest(code=code):
                self.assertNotIn("gdd-hooks-disabled", reason)

    def test_kill_switch_hint_names_the_file_the_hook_actually_checks(self):
        # hint が実装と乖離しないよう、lib/kill-switch.sh の実体と突き合わせる。
        kill_switch_src = (LIB_DIR / "kill-switch.sh").read_text(encoding="utf-8")
        self.assertIn("gdd-hooks-disabled", kill_switch_src)
        self.assertIn("gdd-hooks-disabled", self.kill_switch_hint)

    def test_observed_values_are_emitted_per_code(self):
        # AC-1: 観測値（SHA / 経過時間 / 件数 / key 名）を reason に出す。
        expectations = {
            "approval-missing": ["key: Merge Approval"],
            "approval-pr-mismatch": ["承認宛 PR #7", "実行対象 PR #999"],
            "approval-sha-mismatch": ["承認 sha 0000000", "HEAD "],
            "approval-stale": ["経過 ", "上限 120 分"],
            "pr-target-unresolvable": ["key: PR URL"],
            "pr-url-unrecorded": ["不足 key: PR URL"],
            "recheck-missing": ["key: Pre-Merge Review Recheck"],
            "recheck-sha-mismatch": ["証跡 sha 0000000"],
            "recheck-stale": ["上限 10 分"],
            "recheck-blocking": ["new_blocking 2 件"],
            "review-push-missing": ["key: Last Review Push At"],
            "bot-review-flag-missing": ["key: Bot Review Received"],
            "review-wait-not-elapsed": ["待機上限 40 分", "残り "],
            "independent-review-missing": ["key: Independent Review"],
            "medium-disposition-missing": ["medium 2 件", "key: Medium Disposition"],
            "evidence-unparsable": ["不足 key: Merge Approval"],
            "evidence-malformed": ["不正 key: Merge Approval"],
            "untrusted-root-unverified": ["起動根拠: steering 未解決"],
        }
        for code, tokens in sorted(expectations.items()):
            with self.subTest(code=code):
                for token in tokens:
                    self.assertIn(token, self.reasons[code])

    def test_masking_allowlist_holds_for_every_reason(self):
        # design.md § Sensitive Data / Masking Policy: 絶対パス・slug・repo 名・
        # ブランチ名を出さない（observation を足したことで漏れていないこと）。
        for code, reason in sorted(self.reasons.items()):
            with self.subTest(code=code):
                self.assertNotIn("/private/", reason)
                self.assertNotIn("/tmp/", reason)
                self.assertNotIn("20260101-demo", reason)
                self.assertNotIn("acme/widgets", reason)

class AdminFlagReasonTests(unittest.TestCase):
    """design.md § コマンド検出の設計: `--admin` は 1 文足す。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        _write_state(self.repo, active=True, extra_lines=[])

    def test_admin_merge_reason_warns_about_branch_protection(self):
        result = _run_hook({"tool_input": {"command": "gh pr merge --admin 7"}}, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("--admin", result.stdout)
        self.assertIn("branch protection", result.stdout)

    def test_non_admin_merge_reason_omits_the_note(self):
        result = _run_hook({"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertNotIn("branch protection", result.stdout)

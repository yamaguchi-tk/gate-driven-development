"""merge gate の承認語彙述語 / state.md 証跡フィールドの parser 契約テスト。

`is_merge_approval()` は 2026-09-02 の方式転換（ADR-14）後、hook ではなく
GDD main session が `state.md` の `Merge Approval` を記録してよいかを判定する
述語として使う。語彙・全文アンカー・否定除外の規律は方式転換後も不変。

`gdd_parse_merge_gate_field`（`merge-gate-evidence.sh`）は state.md の各証跡
フィールド（`Merge Approval` / `Pre-Merge Review Recheck` / `Bot Review Received` /
`Last Review Push At` / `Independent Review` / `PR URL`）を共通の generic 語彙
（missing / unparsable / malformed）へ正規化する 1 関数。値ドメイン検査の細部が
ここに集まるため、コマンドラインパース（`GhCommandParseTests`）とは別ファイルへ
分けた（`tests/test_merge_gate_hook.py` 分割）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _merge_gate_support import HANG_GUARD, LIB_DIR, PLUGIN_ROOT

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.constants import (  # noqa: E402
    MERGE_GATE_APPROVAL_FRESHNESS_MINUTES,
    MERGE_GATE_REVIEW_WAIT_MINUTES,
    is_merge_approval,
)


class MergeApprovalPredicateTests(unittest.TestCase):
    # design.md § 承認語彙の述語 が要求する閉じた語彙（肯定側）
    POSITIVE_CASES = [
        "マージして", "マージしていい", "マージして良い", "マージお願い",
        "マージ実行", "merge して", "merge して良い", "merge it", "merge this",
    ]

    def test_closed_vocabulary_all_approve(self):
        for text in self.POSITIVE_CASES:
            with self.subTest(text=text):
                self.assertTrue(is_merge_approval(text))

    def test_non_approval_prose_is_rejected(self):
        for text in [
            "レビュー指摘に対応して",
            "push して再レビュー依頼して",
            "Continue the active `/gdd-dev` run.",
            "Stop hook feedback: ...",
        ]:
            with self.subTest(text=text):
                self.assertFalse(is_merge_approval(text))

    def test_past_tense_report_is_not_approval(self):
        # MANUAL_MERGE_RE（lib/post_merge_continuation.py の過去形報告）との取り違え回帰
        for text in ["マージした", "merged"]:
            with self.subTest(text=text):
                self.assertFalse(is_merge_approval(text))

    def test_negation_suffix_forms_are_rejected(self):
        for text in [
            "マージしてしまった", "マージしておいた", "マージしてある",
            "マージしてはいけません", "マージしては駄目", "マージしてないよね",
        ]:
            with self.subTest(text=text):
                self.assertFalse(is_merge_approval(text))

    def test_negation_word_sentences_are_rejected(self):
        for text in [
            "まだマージしないで", "Do not merge this until CI passes",
            "マージしていいか、まず私に聞いてから",
        ]:
            with self.subTest(text=text):
                self.assertFalse(is_merge_approval(text))

    def test_fullwidth_space_variant_is_rejected(self):
        self.assertFalse(is_merge_approval("マージ　して"))

    def test_existing_distributed_lines_are_not_approval(self):
        # design.md § 承認語彙の述語: `マージして再学習まで` を含む既存 10 行は
        # 全文アンカーにより非承認と判定されることを固定する（肯定側ケース）
        for text in [
            "post-PR 操作がすでに明示承認済み: マージして再学習までを worklog に残す",
            "`マージして再学習まで` などの明示承認済みの post-PR scope を worklog に残す",
        ]:
            with self.subTest(text=text):
                self.assertFalse(is_merge_approval(text))

import subprocess


def _run_mg_parse(
    field_line: str,
    field_name: str,
    head_committer_date: str = "2026-01-01T00:00:00Z",
    env: dict | None = None,
) -> dict:
    # 本番 hook（run-merge-gate-hook.sh:2）と同じ shell option で走らせる。これが無いと
    # 「`set -e` 起因の即死・無音 skip」（H-1 / Round 16 SR-M1 のクラス）を parser
    # 契約テストが構造的に検出できない（Round 16 SR-M2）。
    script = f"""
set -euo pipefail
source '{LIB_DIR}/merge-gate-evidence.sh'
STATE_FILE="$(mktemp)"
printf -- '- {field_name}: %s\\n' "$1" > "$STATE_FILE"
gdd_parse_merge_gate_field "$STATE_FILE" "{field_name}" "$2"
printf 'valid=%s\\nsha=%s\\nreason=%s\\napproval_pr=%s\\napproved_at=%s\\n' \\
  "$GDD_MG_VALID" "$GDD_MG_SHA" "$GDD_MG_REASON" "${{GDD_MG_APPROVAL_PR:-}}" "${{GDD_MG_APPROVED_AT:-}}"
printf 'pr_owner=%s\\npr_repo=%s\\npr_number=%s\\n' \\
  "${{GDD_MG_PR_OWNER:-}}" "${{GDD_MG_PR_REPO:-}}" "${{GDD_MG_PR_NUMBER:-}}"
printf 'blocking=%s\\ndisposition_count=%s\\ndisposition_recorded=%s\\ndisposition_note=%s\\n' \\
  "${{GDD_MG_BLOCKING:-}}" "${{GDD_MG_DISPOSITION_COUNT:-}}" "${{GDD_MG_DISPOSITION_RECORDED:-}}" "${{GDD_MG_DISPOSITION_NOTE:-}}"
"""
    proc = subprocess.run(
        ["bash", "-c", script, "_", field_line, head_committer_date],
        capture_output=True, text=True, timeout=HANG_GUARD, env=env,
    )
    out = dict(line.split("=", 1) for line in proc.stdout.strip().splitlines() if "=" in line)
    return out


def _run_mg_within_minutes(iso: str, limit_minutes: int, now_epoch: int | None = None) -> bool:
    script = f"""
source '{LIB_DIR}/merge-gate-evidence.sh'
gdd_mg_within_minutes "$1" "$2"
"""
    env = None
    shim_dir = None
    if now_epoch is not None:
        # gdd_mg_within_minutes は now を `date -u +%s` から読む。実時計のままだと
        # 「境界ちょうど」を渡した瞬間から subprocess 起動までの経過で境界を越え、
        # 判定が実行時間に依存して flaky になる。now だけを固定するため PATH 先頭に
        # date シムを置く（ISO→epoch 変換は python3 側なのでシムの影響を受けない）。
        shim_dir = tempfile.mkdtemp()
        shim = Path(shim_dir) / "date"
        shim.write_text(f'#!/bin/sh\necho {now_epoch}\n')
        shim.chmod(0o755)
        env = {**os.environ, "PATH": f"{shim_dir}:{os.environ['PATH']}"}
    try:
        proc = subprocess.run(
            ["bash", "-c", script, "_", iso, str(limit_minutes)],
            capture_output=True, text=True, timeout=HANG_GUARD, env=env,
        )
        return proc.returncode == 0
    finally:
        if shim_dir is not None:
            shutil.rmtree(shim_dir, ignore_errors=True)

class MergeGateEvidenceParserTests(unittest.TestCase):
    def test_valid_recheck_evidence(self):
        out = _run_mg_parse(
            "abc1234 | new_blocking: 0 | at: 2026-01-01T00:05:00Z",
            "Pre-Merge Review Recheck",
        )
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["sha"], "abc1234")

    def test_non_numeric_new_blocking_is_malformed(self):
        out = _run_mg_parse(
            "abc1234 | new_blocking: abc | at: 2026-01-01T00:05:00Z",
            "Pre-Merge Review Recheck",
        )
        self.assertEqual(out["valid"], "false")

    def test_naive_timestamp_is_invalid(self):
        out = _run_mg_parse(
            "abc1234 | new_blocking: 0 | at: 2026-01-01T00:05:00",
            "Pre-Merge Review Recheck",
        )
        self.assertEqual(out["valid"], "false")

    def test_received_must_be_yes_or_no(self):
        out = _run_mg_parse(
            "abc1234 | received: maybe | at: 2026-01-01T00:05:00Z",
            "Bot Review Received",
        )
        self.assertEqual(out["valid"], "false")

    def test_last_review_push_at_before_committer_date_is_invalid(self):
        out = _run_mg_parse(
            "abc1234 | at: 2025-01-01T00:00:00Z",
            "Last Review Push At",
            head_committer_date="2026-01-01T00:00:00Z",
        )
        self.assertEqual(out["valid"], "false")

    def test_merge_approval_valid_line_decomposes_into_pr_sha_approved_at(self):
        out = _run_mg_parse(
            "PR #7 / head abc1234 | evidence: ユーザーが「マージして」と指示 | approved_at: 2026-01-01T00:05:00Z",
            "Merge Approval",
        )
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["approval_pr"], "7")
        self.assertEqual(out["sha"], "abc1234")
        self.assertEqual(out["approved_at"], "2026-01-01T00:05:00Z")

    def test_merge_approval_leading_segment_without_hash_is_malformed(self):
        out = _run_mg_parse(
            "PR 7 / head abc1234 | evidence: x | approved_at: 2026-01-01T00:05:00Z",
            "Merge Approval",
        )
        self.assertEqual(out["valid"], "false")

    def test_merge_approval_leading_zero_pr_number_is_malformed(self):
        out = _run_mg_parse(
            "PR #07 / head abc1234 | evidence: x | approved_at: 2026-01-01T00:05:00Z",
            "Merge Approval",
        )
        self.assertEqual(out["valid"], "false")

    def test_merge_approval_non_hex_sha_is_malformed(self):
        out = _run_mg_parse(
            "PR #7 / head zzz | evidence: x | approved_at: 2026-01-01T00:05:00Z",
            "Merge Approval",
        )
        self.assertEqual(out["valid"], "false")

    def test_merge_approval_empty_evidence_is_unparsable(self):
        out = _run_mg_parse(
            "PR #7 / head abc1234 | evidence: | approved_at: 2026-01-01T00:05:00Z",
            "Merge Approval",
        )
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "unparsable")

    def test_merge_approval_naive_approved_at_is_malformed(self):
        out = _run_mg_parse(
            "PR #7 / head abc1234 | evidence: x | approved_at: 2026-01-01T00:05:00",
            "Merge Approval",
        )
        self.assertEqual(out["valid"], "false")

    def test_merge_approval_future_approved_at_is_malformed(self):
        from datetime import datetime, timedelta, timezone
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        out = _run_mg_parse(
            f"PR #7 / head abc1234 | evidence: x | approved_at: {future}",
            "Merge Approval",
        )
        self.assertEqual(out["valid"], "false")

    def test_field_entirely_absent_reason_is_missing(self):
        script = f"""
source '{LIB_DIR}/merge-gate-evidence.sh'
STATE_FILE="$(mktemp)"
printf -- '- Other Field: x\\n' > "$STATE_FILE"
gdd_parse_merge_gate_field "$STATE_FILE" "Merge Approval" ""
printf 'valid=%s\\nreason=%s\\n' "$GDD_MG_VALID" "$GDD_MG_REASON"
"""
        proc = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=HANG_GUARD,
        )
        out = dict(line.split("=", 1) for line in proc.stdout.strip().splitlines() if "=" in line)
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "missing")

    def test_duplicate_merge_approval_lines_use_first_value(self):
        script = f"""
source '{LIB_DIR}/merge-gate-evidence.sh'
STATE_FILE="$(mktemp)"
printf -- '- Merge Approval: PR #7 / head abc1234 | evidence: first | approved_at: 2026-01-01T00:05:00Z\\n' > "$STATE_FILE"
printf -- '- Merge Approval: PR #9 / head def5678 | evidence: second | approved_at: 2026-01-01T00:06:00Z\\n' >> "$STATE_FILE"
gdd_parse_merge_gate_field "$STATE_FILE" "Merge Approval" ""
printf 'approval_pr=%s\\n' "$GDD_MG_APPROVAL_PR"
"""
        proc = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=HANG_GUARD,
        )
        out = dict(line.split("=", 1) for line in proc.stdout.strip().splitlines() if "=" in line)
        self.assertEqual(out["approval_pr"], "7")

    def test_within_minutes_at_exact_boundary_is_within(self):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        iso = (now - timedelta(minutes=120)).isoformat()
        self.assertTrue(_run_mg_within_minutes(iso, 120, now_epoch=int(now.timestamp())))

    def test_within_minutes_one_second_over_boundary_is_not_within(self):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        iso = (now - timedelta(minutes=120, seconds=1)).isoformat()
        self.assertFalse(_run_mg_within_minutes(iso, 120, now_epoch=int(now.timestamp())))

    # --- F-1: Independent Review の reviewer / context 値ドメイン（impl-gate #8） ---
    # design.md § 値ドメイン:「reviewer: 空白を含まない非空 token / context: diff-only」

    def test_independent_review_valid_line(self):
        out = _run_mg_parse(
            "abc1234 | reviewer: gdd-implementation-reviewer | context: diff-only"
            " | high: 0 | medium: 0 | at: 2026-01-01T00:05:00Z",
            "Independent Review",
        )
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["sha"], "abc1234")

    def test_independent_review_without_reviewer_key_is_unparsable(self):
        out = _run_mg_parse(
            "abc1234 | context: diff-only | high: 0 | medium: 0 | at: 2026-01-01T00:05:00Z",
            "Independent Review",
        )
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "unparsable")

    def test_independent_review_reviewer_with_space_is_malformed(self):
        out = _run_mg_parse(
            "abc1234 | reviewer: 自作 チェックリスト | context: diff-only"
            " | high: 0 | medium: 0 | at: 2026-01-01T00:05:00Z",
            "Independent Review",
        )
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "malformed")

    def test_independent_review_without_context_key_is_unparsable(self):
        out = _run_mg_parse(
            "abc1234 | reviewer: gdd-implementation-reviewer"
            " | high: 0 | medium: 0 | at: 2026-01-01T00:05:00Z",
            "Independent Review",
        )
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "unparsable")

    def test_independent_review_non_diff_only_context_is_malformed(self):
        # 「実装文脈から切り離した独立レビュー」の標識が無い証跡で AC-3 の
        # 待機解除を通さない（self-review / implementation-aware は不可）
        for ctx in ["self-review", "implementation-aware"]:
            with self.subTest(context=ctx):
                out = _run_mg_parse(
                    f"abc1234 | reviewer: gdd-implementation-reviewer | context: {ctx}"
                    " | high: 0 | medium: 0 | at: 2026-01-01T00:05:00Z",
                    "Independent Review",
                )
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "malformed")

    # --- F-2: PR URL の完全一致（impl-gate #8） ---
    # design.md § 値ドメイン:「https://github.com/<owner>/<repo>/pull/<number> に完全一致」

    def test_pr_url_valid_line_decomposes_owner_repo_number(self):
        out = _run_mg_parse("https://github.com/acme/widgets/pull/42", "PR URL")
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["pr_owner"], "acme")
        self.assertEqual(out["pr_repo"], "widgets")
        self.assertEqual(out["pr_number"], "42")

    def test_pr_url_non_exact_matches_are_malformed(self):
        # shell glob 実装では 4 形すべてが valid=true になっていた（impl-gate #8 F-2）。
        # `.../pull/42/files` はブラウザからのコピペで最頻の形
        for url in [
            "https://github.com/acme/widgets/pull/42/files",
            "https://github.com/acme/widgets/pull/42abc",
            "https://github.com/a/b/c/d/pull/7",
            "https://github.com/acme widgets/x/pull/7",
            "https://github.com/acme/widgets/pull/07",
            "https://github.com/acme/widgets/pull/",
            "http://github.com/acme/widgets/pull/42",
        ]:
            with self.subTest(url=url):
                out = _run_mg_parse(url, "PR URL")
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "malformed")
                self.assertEqual(out["pr_number"], "")

    # --- F-3: GDD_MG_REASON の generic 語彙（impl-gate #8） ---
    # tasklist T-3 Stage Output Contract:「missing / unparsable / malformed の 3 値」
    # （field 不在 / 必須 key 欠落 / 値ドメイン違反）。state.md 自体が読めない場合の
    # `state-unreadable` のみ field 層の外側にある例外。

    GENERIC_REASON_VOCABULARY = {"missing", "unparsable", "malformed"}

    def test_missing_required_key_is_unparsable(self):
        # 必須 key 欠落は design code 15 evidence-unparsable（「不足 key 名を出す」）
        # へマップされる必要があり、malformed（code 16）に化けてはいけない
        for field, line in [
            ("Pre-Merge Review Recheck", "abc1234 | at: 2026-01-01T00:05:00Z"),
            ("Bot Review Received", "abc1234 | at: 2026-01-01T00:05:00Z"),
            ("Merge Approval", "PR #7 / head abc1234 | evidence: x"),
            ("Last Review Push At", "abc1234"),
            (
                "Independent Review",
                "abc1234 | reviewer: r | context: diff-only | medium: 0 | at: 2026-01-01T00:05:00Z",
            ),
        ]:
            with self.subTest(field=field):
                out = _run_mg_parse(line, field)
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "unparsable")

    def test_value_domain_violations_are_malformed(self):
        for field, line in [
            ("Pre-Merge Review Recheck", "abc1234 | new_blocking: abc | at: 2026-01-01T00:05:00Z"),
            ("Pre-Merge Review Recheck", "abc1234 | new_blocking: 00 | at: 2026-01-01T00:05:00Z"),
            ("Bot Review Received", "abc1234 | received: maybe | at: 2026-01-01T00:05:00Z"),
            ("Pre-Merge Review Recheck", "zzz | new_blocking: 0 | at: 2026-01-01T00:05:00Z"),
            ("Pre-Merge Review Recheck", "abc1234 | new_blocking: 0 | at: 2026-01-01T00:05:00"),
        ]:
            with self.subTest(field=field, line=line):
                out = _run_mg_parse(line, field)
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "malformed")

    def test_reason_never_leaks_final_reason_codes(self):
        # `evidence-malformed` / `state-unreadable` は design § reason code
        # カタログの最終 code。generic 層に混入させない（T-12/T-13 が case でマップする）
        for field, line in [
            ("Independent Review", "abc1234 | high: 0 | medium: 0 | at: 2026-01-01T00:05:00Z"),
            ("Bot Review Received", "abc1234 | received: maybe | at: 2026-01-01T00:05:00Z"),
            ("Last Review Push At", "abc1234 | at: 2025-01-01T00:00:00Z"),
            ("PR URL", "https://github.com/acme/widgets/pull/42/files"),
            ("Pre-Merge Review Recheck", "zzz | new_blocking: 0 | at: 2026-01-01T00:05:00Z"),
        ]:
            with self.subTest(field=field, line=line):
                out = _run_mg_parse(line, field)
                self.assertEqual(out["valid"], "false")
                self.assertIn(out["reason"], self.GENERIC_REASON_VOCABULARY)

    def test_state_unreadable_is_the_only_non_generic_reason(self):
        script = f"""
source '{LIB_DIR}/merge-gate-evidence.sh'
gdd_parse_merge_gate_field "/nonexistent/state.md" "Merge Approval" ""
printf 'valid=%s\\nreason=%s\\n' "$GDD_MG_VALID" "$GDD_MG_REASON"
"""
        proc = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=HANG_GUARD,
        )
        out = dict(line.split("=", 1) for line in proc.stdout.strip().splitlines() if "=" in line)
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "state-unreadable")

    # --- advisory-1: 出力グローバルの先頭リセット（姉妹関数と同じ規律） ---

    def test_output_globals_are_reset_between_calls(self):
        # T-3 advisory A-11: blocking / Medium Disposition の 4 グローバルも
        # 他 field 群と同じく次呼び出しでリセットされることを pin する
        # （run-merge-gate-hook.sh は同一プロセスで複数 field を連続 parse するため）。
        script = f"""
source '{LIB_DIR}/merge-gate-evidence.sh'
STATE_FILE="$(mktemp)"
printf -- '- Independent Review: abc1234 | reviewer: r | context: diff-only | high: 3 | medium: 5 | blocking: 2 | at: 2026-01-01T00:05:00Z\\n' > "$STATE_FILE"
printf -- '- Medium Disposition: abc1234 | count: 5 | recorded: accepted | note: x | at: 2026-01-01T00:05:00Z\\n' >> "$STATE_FILE"
printf -- '- Bot Review Received: abc1234 | received: maybe | at: 2026-01-01T00:06:00Z\\n' >> "$STATE_FILE"
gdd_parse_merge_gate_field "$STATE_FILE" "Independent Review" ""
gdd_parse_merge_gate_field "$STATE_FILE" "Medium Disposition" ""
gdd_parse_merge_gate_field "$STATE_FILE" "Bot Review Received" ""
printf 'high=%s\\nmedium=%s\\nat=%s\\nblocking=%s\\ndisposition_count=%s\\ndisposition_recorded=%s\\ndisposition_note=%s\\n' \\
  "$GDD_MG_HIGH" "$GDD_MG_MEDIUM" "$GDD_MG_AT" "$GDD_MG_BLOCKING" \\
  "$GDD_MG_DISPOSITION_COUNT" "$GDD_MG_DISPOSITION_RECORDED" "$GDD_MG_DISPOSITION_NOTE"
"""
        proc = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=HANG_GUARD,
        )
        out = dict(line.split("=", 1) for line in proc.stdout.strip().splitlines() if "=" in line)
        self.assertEqual(out["high"], "")
        self.assertEqual(out["medium"], "")
        self.assertEqual(out["at"], "")
        self.assertEqual(out["blocking"], "")
        self.assertEqual(out["disposition_count"], "")
        self.assertEqual(out["disposition_recorded"], "")
        self.assertEqual(out["disposition_note"], "")

    # --- advisory-2: HEAD committer date が変換不能なら不足の通知側（fail-closed） ---

    def test_unparseable_head_committer_date_blocks(self):
        out = _run_mg_parse(
            "abc1234 | at: 2026-01-01T00:05:00Z",
            "Last Review Push At",
            head_committer_date="not-a-timestamp",
        )
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "malformed")

    def test_approval_freshness_exceeds_review_wait(self):
        # design.md § 条件C の不変条件: Approval Freshness > Review Wait。
        from lib.constants import (
            MERGE_GATE_APPROVAL_FRESHNESS_MINUTES,
            MERGE_GATE_REVIEW_WAIT_MINUTES,
        )
        self.assertGreater(
            MERGE_GATE_APPROVAL_FRESHNESS_MINUTES, MERGE_GATE_REVIEW_WAIT_MINUTES
        )

    # --- blocking key と Medium Disposition の parser 拡張 ---

    def test_independent_review_blocking_key_is_parsed(self):
        out = _run_mg_parse(
            "abc1234 | reviewer: gdd-completion-reviewer | context: diff-only "
            "| high: 0 | medium: 3 | blocking: 1 | at: 2026-01-01T00:05:00Z",
            "Independent Review",
        )
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["blocking"], "1")

    def test_independent_review_missing_blocking_key_defaults_to_zero_with_reason(self):
        out = _run_mg_parse(
            "abc1234 | reviewer: gdd-completion-reviewer | context: diff-only "
            "| high: 0 | medium: 3 | at: 2026-01-01T00:05:00Z",
            "Independent Review",
        )
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["blocking"], "0")
        self.assertEqual(out["reason"], "legacy-no-blocking-field")

    # Round 8 H-1/M-1 実測分を含む near-miss 形。抽出が英数字・`_`/`-`/`*`/空白を
    # 許容するため、コロン前空白・強調記法・末尾数字のいずれも「欠落」ではなく
    # malformed として不足を通知する。`block-ing` / `b_l_o_c_k_i_n` は正規化（`-`/`_` 除去）
    # が寄与しないと検出できない変種（Round 16 IR-M1: 除去を全廃した mutation が
    # 既存 5 変種では SURVIVED した）。
    NEAR_MISS_BLOCKING_KEYS = (
        "Blocking: 1",
        "blockin: 1",
        "blocking : 1",
        "**blocking**: 1",
        "blocking2: 1",
        "block-ing: 1",
        "b_l_o_c_k_i_n: 1",
        # T-3-R2 M-6（Round 17 advisory）: 接頭辞判定の閾値はちょうど 6 文字
        # （`"${#_norm}" -ge 6`）。既存の最短 near-miss 例 `blockin` は 7 文字で、
        # 境界のちょうど 6 文字を pin するケースが無かった（`-ge 6` を `-ge 7` に
        # 変える mutation が既存 7 変種では SURVIVED した）。
        "blocki: 1",
        # T-3-R4（completion-check Round 20 H-1）: `_gdd_sr_lookup` は `:` と `=`
        # の両方を key 区切りとして受理する（`gate_field_delimiter` 契約）が、
        # near-miss walk は `:` しか見ていなかったため `=` 区切りの near-miss key
        # が無音で `legacy-no-blocking-field` へ倒れていた（実パーサで実測）。
        "Blocking= 1",
        "blockin= 1",
        "BLOCKING=1",
        # 独立レビュー CONFIRMED（誤検知修正の副作用で fail-open 化しかけた）:
        # 複数語だが「blocking」が候補の先頭語である言い換え typo。近傍語判定を
        # 「候補の先頭が blocking で始まるか」というアンカー付き判定にしたことで、
        # 末尾に無関係語が続く形（`blocking count` 等）は維持しつつ、先頭に
        # 無関係語が来る自由文（`mentions blocking key`）だけを除外している。
        "blocking count: 1",
        "Blocking Count: 1",
        "block ing: 1",
    )

    def _independent_review_line_with(self, segment: str) -> str:
        return (
            f"abc1234 | reviewer: gdd-completion-reviewer | context: diff-only "
            f"| high: 0 | medium: 3 | {segment} | at: 2026-01-01T00:05:00Z"
        )

    def test_independent_review_near_miss_blocking_key_is_malformed(self):
        for near_miss in self.NEAR_MISS_BLOCKING_KEYS:
            with self.subTest(key=near_miss):
                out = _run_mg_parse(self._independent_review_line_with(near_miss), "Independent Review")
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "malformed")

    def test_independent_review_equals_in_free_text_value_is_not_a_false_positive(self):
        # T-3-R4: H-1 の修正（`=` を `:` へ正規化）が、`=` を含む自由文の値
        # （クエリ文字列等）まで near-miss として誤爆させないことを固定する。
        note = "note: see PR https://x/y?a=1&b=2"
        out = _run_mg_parse(self._independent_review_line_with(note), "Independent Review")
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["reason"], "legacy-no-blocking-field")
        self.assertEqual(out["blocking"], "0")

    def test_independent_review_note_word_before_unrelated_key_is_not_a_false_positive(self):
        # 実測: 旧書式（`blocking` key 欠落）で note の自由文中に「blocking」という
        # 語が現れ、句読点を挟まず直後に無関係な `key:` が続くと、near-miss walk が
        # 空白区切りの複数語（"mentions blocking key"）を連結して `blockingkey` を
        # 作り、「blocking key の typo」と誤認して malformed にしていた
        # （句読点を挟むと `test_independent_review_equals_in_free_text_value_is_not_a_false_positive`
        # の通り正しく通る）。判定はコロン直前の1語に限定しなければならない。
        note = "note: mentions blocking key: unrelated"
        out = _run_mg_parse(self._independent_review_line_with(note), "Independent Review")
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["reason"], "legacy-no-blocking-field")
        self.assertEqual(out["blocking"], "0")

    def test_independent_review_near_miss_detection_needs_no_external_command(self):
        # Round 16 SR-M1: near-miss 検出は fail-closed 判定の本体であり、`grep`/`tr`
        # が失敗しても（`for` list の command substitution では `set -e` が発火しない
        # ため）無音で `legacy-no-blocking-field` へ倒れてはならない。両コマンドを
        # exit 127 にする PATH シム下でも malformed を維持することを pin する。
        shim_dir = tempfile.mkdtemp()
        try:
            for name in ("grep", "tr"):
                shim = Path(shim_dir) / name
                shim.write_text("#!/bin/sh\nexit 127\n")
                shim.chmod(0o755)
            env = {**os.environ, "PATH": f"{shim_dir}:{os.environ['PATH']}"}
            for near_miss in self.NEAR_MISS_BLOCKING_KEYS:
                with self.subTest(key=near_miss):
                    out = _run_mg_parse(
                        self._independent_review_line_with(near_miss), "Independent Review", env=env,
                    )
                    self.assertEqual(out.get("valid"), "false", out)
                    self.assertEqual(out.get("reason"), "malformed", out)
        finally:
            shutil.rmtree(shim_dir, ignore_errors=True)

    def test_independent_review_nocasematch_is_restored_after_the_call(self):
        # Round 16 SR-M2/IR-M2: `nocasematch` の復元（`eval "$_saved_nocasematch"`）を
        # 落とすと呼び出し元の `[[ ]]`/`case` がすべて大小文字非依存になり、他の判定
        # （`context: diff-only` の完全一致等）が緩む。legacy 経路（`blocking` 欠落）と
        # near-miss 経路（ループ途中 break）の両方で off に戻ることを pin する。
        for segment in ("note: legacy", "Blocking: 1"):
            with self.subTest(segment=segment):
                script = f"""
set -euo pipefail
source '{LIB_DIR}/merge-gate-evidence.sh'
STATE_FILE="$(mktemp)"
printf -- '- Independent Review: %s\\n' "$1" > "$STATE_FILE"
gdd_parse_merge_gate_field "$STATE_FILE" "Independent Review" "2026-01-01T00:00:00Z"
shopt nocasematch || echo RESTORED-OFF
"""
                proc = subprocess.run(
                    ["bash", "-c", script, "_", self._independent_review_line_with(segment)],
                    capture_output=True, text=True, timeout=HANG_GUARD,
                )
                self.assertIn("RESTORED-OFF", proc.stdout, f"rc={proc.returncode} err={proc.stderr}")

    def test_medium_disposition_fields_are_parsed(self):
        out = _run_mg_parse(
            "abc1234 | count: 1 | recorded: accepted | note: 判断済み | at: 2026-01-01T00:05:00Z",
            "Medium Disposition",
        )
        # count の Independent Review との一致検査は hook 側（T-4）が行うため、
        # ここでは parser がフィールドを正しく取り出せることだけを検証する。
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["disposition_count"], "1")
        self.assertEqual(out["disposition_recorded"], "accepted")
        self.assertEqual(out["disposition_note"], "判断済み")

    def test_medium_disposition_placeholder_recorded_is_malformed(self):
        out = _run_mg_parse(
            "abc1234 | count: 3 | recorded: <follow-up PR URL> | note: <1 行> | at: 2026-01-01T00:05:00Z",
            "Medium Disposition",
        )
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "malformed")

    def test_medium_disposition_single_end_placeholder_is_malformed(self):
        # Round 8 H-1 実測分: 正本テンプレート（self-review-lanes.md）
        # 「<follow-up PR URL / issue 参照 | accepted>」を `|` で segment 分割すると
        # 閉じ `>` を失った片端形が残る。両端一致 '<'*'>' はこれを見逃していた。
        out = _run_mg_parse(
            "abc1234 | count: 3 | recorded: <follow-up PR URL / issue 参照 "
            "| note: 正常な備考 | at: 2026-01-01T00:05:00Z",
            "Medium Disposition",
        )
        self.assertEqual(out["valid"], "false")
        self.assertEqual(out["reason"], "malformed")

    def test_medium_disposition_non_placeholder_value_with_angle_char_is_valid(self):
        # 片端一致への強化が正常値まで誤爆させないことの境界テスト（`<`/`>` を
        # 含まない通常値は valid のまま）。
        out = _run_mg_parse(
            "abc1234 | count: 2 | recorded: https://github.com/acme/widgets/issues/9 "
            "| note: 対応済み | at: 2026-01-01T00:05:00Z",
            "Medium Disposition",
        )
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["disposition_recorded"], "https://github.com/acme/widgets/issues/9")

    # --- 単独形の退行注入 KILL テスト ---
    # 既存 test_medium_disposition_placeholder_recorded_is_malformed は recorded /
    # note を同時にプレースホルダにしており、先に評価される recorded の case で
    # return するため note の case には到達しない（相互マスク）。以下 3 本は各検査を
    # 単独で踏み、検査削除の変異を個別に KILL する。

    def test_medium_disposition_placeholder_note_alone_is_malformed(self):
        # recorded は正常値。note だけをプレースホルダにして note の case を単独で踏む。
        for note in ("<1 行>", "<1 行"):
            with self.subTest(note=note):
                out = _run_mg_parse(
                    f"abc1234 | count: 3 | recorded: accepted | note: {note} | at: 2026-01-01T00:05:00Z",
                    "Medium Disposition",
                )
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "malformed")

    def test_medium_disposition_non_uint_count_is_malformed(self):
        # count の値ドメイン（uint、先頭ゼロ不可）。他 key はすべて正常値。
        for count in ("x", "00", "-1", "1.5"):
            with self.subTest(count=count):
                out = _run_mg_parse(
                    f"abc1234 | count: {count} | recorded: accepted | note: 判断済み | at: 2026-01-01T00:05:00Z",
                    "Medium Disposition",
                )
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "malformed")

    def test_independent_review_non_uint_blocking_is_malformed(self):
        # blocking の値ドメイン（uint、先頭ゼロ不可）。key は存在するため
        # legacy-no-blocking-field 経路には入らず、値検査だけで malformed になる。
        for blocking in ("x", "00", "-1", "1.5"):
            with self.subTest(blocking=blocking):
                out = _run_mg_parse(
                    f"abc1234 | reviewer: gdd-completion-reviewer | context: diff-only "
                    f"| high: 0 | medium: 3 | blocking: {blocking} | at: 2026-01-01T00:05:00Z",
                    "Independent Review",
                )
                self.assertEqual(out["valid"], "false")
                self.assertEqual(out["reason"], "malformed")


class AutonomyMergeApprovalTemplateTests(unittest.TestCase):
    """post-merge-qa.md 手順 2 が書かせる自走の `Merge Approval` の形を、merge gate の parser が受け付けるか。

    文書のひな形を読んで値を入れ、parser に通す（ひな形が parser の必須 key を落とすと落ちる）。
    """

    TEMPLATE_PREFIX = "Merge Approval: PR #<n> / head <sha> | evidence: post-pr-autonomy:"

    def _template(self) -> str:
        text = (PLUGIN_ROOT / "references" / "post-merge-qa.md").read_text(encoding="utf-8")
        found = [
            seg for seg in text.split("`")
            if seg.startswith(self.TEMPLATE_PREFIX)
        ]
        self.assertEqual(len(found), 1, "post-merge-qa.md に自走の Merge Approval のひな形が 1 つだけある")
        return found[0]

    def test_template_is_accepted_by_the_parser(self):
        line = (
            self._template()
            .replace("<n>", "7")
            .replace("<sha>", "abc1234")
            .replace("<自走上限の値>", "マージ・デプロイ・QA まで")
            .replace("<ISO 8601>", "2026-01-01T00:05:00Z")
        )
        self.assertNotIn("<", line)
        out = _run_mg_parse(line.removeprefix("Merge Approval: "), "Merge Approval")
        self.assertEqual(out["valid"], "true")
        self.assertEqual(out["approval_pr"], "7")
        self.assertEqual(out["sha"], "abc1234")
        self.assertEqual(out["approved_at"], "2026-01-01T00:05:00Z")
